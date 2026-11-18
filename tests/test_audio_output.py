"""Exercise the real Android audio output with a deterministic Oboe substitute.

This covers stream failures, callback data and ownership. It does not measure
the latency of Android, a Bluetooth codec or headphones.
"""
from pathlib import Path
import subprocess
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
OBOE = r'''
#pragma once
#include <algorithm>
#include <cassert>
#include <cstdint>
#include <memory>
#include <set>
namespace oboe {
enum class Result { OK, ErrorUnavailable };
enum class AudioApi { AAudio, OpenSLES };
enum class AudioFormat { I16, Float };
enum class PerformanceMode { LowLatency };
enum class SharingMode { Exclusive };
enum class Usage { Media, Game };
enum class ContentType { Music };
enum class DataCallbackResult { Continue, Stop };
inline bool failOpen=false, failStart=false;
inline int starts=0, closes=0, tunes=0, tuners=0, bufferChanges=0, nextId=0;
inline int burst=192;
inline AudioApi api=AudioApi::AAudio;
inline Usage usage=Usage::Media;
inline std::set<int> active;
class AudioStream;
class AudioStreamCallback {
public:
    virtual ~AudioStreamCallback()=default;
    virtual DataCallbackResult onAudioReady(AudioStream *,void *,int32_t)=0;
    virtual void onErrorBeforeClose(AudioStream *,Result)=0;
    virtual void onErrorAfterClose(AudioStream *,Result)=0;
};
class AudioStream {
public:
    int id=++nextId, channels=2, rate=48000, framesPerBurst=burst, bufferSize=1920;
    AudioApi audioApi=api;
    AudioFormat format=AudioFormat::I16;
    AudioStreamCallback *callback=nullptr;
    AudioStream() { active.insert(id); }
    Result start() {
        ++starts;
        if(failStart) return Result::ErrorUnavailable;
        // A real stream may enter its callback before start() returns.
        int16_t data[2]={-1,-1};
        assert(callback->onAudioReady(this,data,1)==DataCallbackResult::Continue);
        assert(data[0]==0 && data[1]==0);
        return Result::OK;
    }
    AudioFormat getFormat() const { return format; }
    int32_t getBytesPerFrame() const { return channels*sizeof(int16_t); }
    AudioApi getAudioApi() const { return audioApi; }
    int32_t getFramesPerBurst() const { return framesPerBurst; }
    int32_t getBufferSizeInFrames() const { return bufferSize; }
    int32_t getBufferCapacityInFrames() const { return 4096; }
    int32_t setBufferSizeInFrames(int32_t n) { ++bufferChanges; bufferSize=std::min(n,4096); return bufferSize; }
};
struct StreamDeleter {
    void operator()(AudioStream *stream) const {
        if(stream) { active.erase(stream->id); ++closes; delete stream; }
    }
};
using ManagedStream=std::unique_ptr<AudioStream,StreamDeleter>;
class LatencyTuner {
    int streamId;
public:
    explicit LatencyTuner(AudioStream &s):streamId(s.id) { assert(active.count(streamId)); ++tuners; }
    ~LatencyTuner() { assert(!active.count(streamId)); --tuners; }
    Result tune() { assert(active.count(streamId)); ++tunes; return Result::OK; }
};
class AudioStreamBuilder {
    int channels=2, rate=48000;
    AudioStreamCallback *callback=nullptr;
public:
    AudioStreamBuilder *setPerformanceMode(PerformanceMode) { return this; }
    AudioStreamBuilder *setSharingMode(SharingMode) { return this; }
    AudioStreamBuilder *setUsage(Usage u) { usage=u; return this; }
    AudioStreamBuilder *setContentType(ContentType) { return this; }
    AudioStreamBuilder *setFormat(AudioFormat) { return this; }
    AudioStreamBuilder *setChannelCount(int c) { channels=c; return this; }
    AudioStreamBuilder *setSampleRate(int r) { rate=r; return this; }
    AudioStreamBuilder *setCallback(AudioStreamCallback *c) { callback=c; return this; }
    Result openManagedStream(ManagedStream &stream) {
        if(failOpen) return Result::ErrorUnavailable;
        stream.reset(new AudioStream());
        stream->channels=channels; stream->rate=rate; stream->callback=callback;
        return Result::OK;
    }
};
inline const char *convertToText(Result) { return "fake Oboe result"; }
}
'''
HARNESS = r'''
#include "audio-output.cpp"
#include <cstdio>
int main(int argc,char **argv) {
    assert(argc==2);
    auto output=static_cast<AudioOutput *>(android_chiaki_audio_output_new(nullptr));
    if(std::string(argv[1])=="fail-open") {
        oboe::failOpen=true;
        android_chiaki_audio_output_settings(2,48000,output);
        assert(!output->stream && oboe::starts==0 && oboe::tuners==0);
    } else {
        android_chiaki_audio_output_settings(2,48000,output);
        assert(output->stream && oboe::starts==1 && oboe::tuners==1 && oboe::tunes==1);
        assert(oboe::usage==oboe::Usage::Game);
        assert(output->stream->getBufferSizeInFrames()==2*oboe::burst);
        int16_t pcm[512]; std::fill_n(pcm,512,1234);
        android_chiaki_audio_output_frame(pcm,512,output);
        int16_t delivered[1024]; std::fill_n(delivered,1024,-1);
        auto stream=output->stream.get();
        assert(stream->callback->onAudioReady(stream,delivered,512)==oboe::DataCallbackResult::Continue);
        for(int i=0;i<1024;++i) assert(delivered[i]==(i<512?1234:0));
        assert(oboe::tunes==2);
        stream->format=oboe::AudioFormat::Float;
        assert(stream->callback->onAudioReady(stream,delivered,512)==oboe::DataCallbackResult::Stop);
        // Replacing the device closes callbacks before replacing the tuner.
        oboe::api=oboe::AudioApi::OpenSLES; oboe::burst=0;
        int changes=oboe::bufferChanges;
        android_chiaki_audio_output_settings(2,44100,output);
        assert(output->stream->rate==44100 && oboe::tuners==0 && oboe::closes==1);
        assert(oboe::bufferChanges==changes);
        // A later failed open must not start the previously opened device.
        oboe::failOpen=true;
        int starts=oboe::starts;
        android_chiaki_audio_output_settings(2,48000,output);
        assert(!output->stream && oboe::starts==starts && oboe::active.empty());
        oboe::failOpen=false; oboe::api=oboe::AudioApi::AAudio; oboe::burst=192; oboe::failStart=true;
        android_chiaki_audio_output_settings(2,48000,output);
        assert(!output->stream && oboe::active.empty() && oboe::tuners==0);
        oboe::failStart=false;
        android_chiaki_audio_output_settings(2,48000,output);
        assert(output->stream && oboe::tuners==1);
    }
    android_chiaki_audio_output_free(output);
    android_chiaki_audio_output_free(nullptr);
    assert(oboe::active.empty() && oboe::tuners==0);
    puts("PASS: real audio output stream lifecycle and PCM callback; no fake stream/tuner leaks");
}
'''


class AudioOutputTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp = tempfile.TemporaryDirectory(prefix="deckivo-audio-test-")
        cls.addClassCleanup(cls.temp.cleanup)
        base = Path(cls.temp.name)
        headers = {
            "chiaki/log.h": "#pragma once\n#include <stddef.h>\ntypedef int ChiakiLog;\n"
                "#define CHIAKI_LOGE(...) ((void)0)\n#define CHIAKI_LOGI(...) ((void)0)\n"
                "#define CHIAKI_LOGW(...) ((void)0)\n#define CHIAKI_LOGV(...) ((void)0)\n",
            "chiaki/thread.h": "#pragma once\n",
            "android/log.h": "#pragma once\n",
            "oboe/Oboe.h": OBOE,
        }
        for name, content in headers.items():
            path = base/name
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content)
        (base/"harness.cpp").write_text('#include <string>\n'+HARNESS)
        cls.binary = base/"test-audio"
        cpp = ROOT/"android/app/src/main/cpp"
        subprocess.run(["clang++", "-std=c++17", "-fsanitize=address,undefined", "-g",
                        "-I"+str(base), "-I"+str(cpp), str(base/"harness.cpp"),
                        "-o", str(cls.binary)], check=True, capture_output=True, text=True)

    def run_scenario(self, scenario):
        result = subprocess.run([str(self.binary), scenario], capture_output=True, text=True, timeout=10)
        self.assertEqual(result.returncode, 0, result.stdout+result.stderr)

    def test_failed_open_does_not_dereference_a_null_stream(self):
        self.run_scenario("fail-open")

    def test_callback_tuning_failure_and_replacement_ownership(self):
        self.run_scenario("lifecycle")


if __name__ == "__main__":
    unittest.main()
