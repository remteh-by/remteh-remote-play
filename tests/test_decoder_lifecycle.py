"""Compile the actual video decoder against a deterministic fake MediaCodec.

Exercises pthread concurrency, detach/recreate and teardown without an EOS input
buffer. This is a lifecycle regression test, not a real video decoding test.
"""
from pathlib import Path
import subprocess
import tempfile

ROOT = Path(__file__).resolve().parents[1]
COMMON = r'''
#pragma once
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>
#include <sys/types.h>
#include <pthread.h>
typedef void JNIEnv;
typedef void *jobject;
typedef int ChiakiLog;
typedef int ChiakiCodec;
typedef int ChiakiErrorCode;
typedef pthread_mutex_t ChiakiMutex;
typedef pthread_t ChiakiThread;
#define CHIAKI_ERR_SUCCESS 0
#define CHIAKI_LOGE(...) ((void)0)
#define CHIAKI_LOGI(...) ((void)0)
static inline int chiaki_mutex_init(ChiakiMutex *m, bool recursive) { (void)recursive; return pthread_mutex_init(m, 0); }
static inline int chiaki_mutex_lock(ChiakiMutex *m) { return pthread_mutex_lock(m); }
static inline int chiaki_mutex_unlock(ChiakiMutex *m) { return pthread_mutex_unlock(m); }
static inline int chiaki_mutex_fini(ChiakiMutex *m) { return pthread_mutex_destroy(m); }
static inline int chiaki_thread_create(ChiakiThread *t, void *(*fn)(void *), void *ctx) { return pthread_create(t, 0, fn, ctx); }
static inline int chiaki_thread_join(ChiakiThread *t, void **result) { return pthread_join(*t, result); }
static inline bool chiaki_codec_is_h265(int c) { return c != 0; }
typedef struct ANativeWindow { int unused; } ANativeWindow;
typedef struct AMediaCodec { int unused; } AMediaCodec;
typedef struct AMediaFormat { int unused; } AMediaFormat;
typedef int media_status_t;
typedef struct { uint32_t flags; int32_t size; } AMediaCodecBufferInfo;
#define AMEDIA_OK 0
#define AMEDIACODEC_BUFFER_FLAG_END_OF_STREAM 4
#define AMEDIAFORMAT_KEY_MIME "mime"
#define AMEDIAFORMAT_KEY_WIDTH "width"
#define AMEDIAFORMAT_KEY_HEIGHT "height"
ANativeWindow *ANativeWindow_fromSurface(JNIEnv *, jobject);
void ANativeWindow_release(ANativeWindow *);
AMediaCodec *AMediaCodec_createDecoderByType(const char *);
AMediaFormat *AMediaFormat_new(void);
void AMediaFormat_delete(AMediaFormat *);
void AMediaFormat_setString(AMediaFormat *, const char *, const char *);
void AMediaFormat_setInt32(AMediaFormat *, const char *, int32_t);
media_status_t AMediaCodec_configure(AMediaCodec *, AMediaFormat *, ANativeWindow *, void *, uint32_t);
media_status_t AMediaCodec_start(AMediaCodec *);
media_status_t AMediaCodec_stop(AMediaCodec *);
media_status_t AMediaCodec_delete(AMediaCodec *);
media_status_t AMediaCodec_setOutputSurface(AMediaCodec *, ANativeWindow *);
ssize_t AMediaCodec_dequeueInputBuffer(AMediaCodec *, int64_t);
uint8_t *AMediaCodec_getInputBuffer(AMediaCodec *, size_t, size_t *);
media_status_t AMediaCodec_queueInputBuffer(AMediaCodec *, size_t, size_t, size_t, uint64_t, uint32_t);
ssize_t AMediaCodec_dequeueOutputBuffer(AMediaCodec *, AMediaCodecBufferInfo *, int64_t);
media_status_t AMediaCodec_releaseOutputBuffer(AMediaCodec *, size_t, bool);
'''
HARNESS = r'''
#include "video-decoder.h"
#include <assert.h>
#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
static int windows, codecs;
ANativeWindow *ANativeWindow_fromSurface(JNIEnv *env, jobject surface) { (void)env; assert(surface); ++windows; return calloc(1,sizeof(ANativeWindow)); }
void ANativeWindow_release(ANativeWindow *w) { assert(w); --windows; free(w); }
AMediaCodec *AMediaCodec_createDecoderByType(const char *s) { (void)s; ++codecs; return calloc(1,sizeof(AMediaCodec)); }
AMediaFormat *AMediaFormat_new(void) { return calloc(1,sizeof(AMediaFormat)); }
void AMediaFormat_delete(AMediaFormat *f) { free(f); }
void AMediaFormat_setString(AMediaFormat *f,const char *k,const char *v) { (void)f;(void)k;(void)v; }
void AMediaFormat_setInt32(AMediaFormat *f,const char *k,int32_t v) { (void)f;(void)k;(void)v; }
media_status_t AMediaCodec_configure(AMediaCodec *c, AMediaFormat *f, ANativeWindow *w,void *p,uint32_t x) { (void)c;(void)f;(void)w;(void)p;(void)x; return 0; }
media_status_t AMediaCodec_start(AMediaCodec *c) { (void)c; return 0; }
media_status_t AMediaCodec_stop(AMediaCodec *c) { (void)c; return 0; }
media_status_t AMediaCodec_delete(AMediaCodec *c) { --codecs; free(c); return 0; }
media_status_t AMediaCodec_setOutputSurface(AMediaCodec *c,ANativeWindow *w) { (void)c;(void)w; return 0; }
ssize_t AMediaCodec_dequeueInputBuffer(AMediaCodec *c,int64_t t) { (void)c;(void)t; return -1; }
uint8_t *AMediaCodec_getInputBuffer(AMediaCodec *c,size_t i,size_t *s) { (void)c;(void)i;*s=0;return 0; }
media_status_t AMediaCodec_queueInputBuffer(AMediaCodec *c,size_t i,size_t o,size_t s,uint64_t t,uint32_t f) { (void)c;(void)i;(void)o;(void)s;(void)t;(void)f;return 0; }
ssize_t AMediaCodec_dequeueOutputBuffer(AMediaCodec *c,AMediaCodecBufferInfo *i,int64_t t) { (void)c;(void)i; assert(t>0 && t<=10000); usleep(1000); return -1; }
media_status_t AMediaCodec_releaseOutputBuffer(AMediaCodec *c,size_t i,bool r) { (void)c;(void)i;(void)r;return 0; }
int main(void) {
    alarm(10); // Deadlocks fail instead of hanging the test runner.
    AndroidChiakiVideoDecoder d;
    assert(!android_chiaki_video_decoder_init(&d,0,1280,720,0));
    android_chiaki_video_decoder_set_surface(&d,0,0); // Empty detach must unlock.
    for(int i=0;i<100;i++) {
        android_chiaki_video_decoder_set_surface(&d,0,(void *)1);
        assert(codecs==1 && windows==1);
        android_chiaki_video_decoder_set_surface(&d,0,(void *)2); // Surface replacement.
        assert(windows==1);
        usleep(1000);
        android_chiaki_video_decoder_set_surface(&d,0,0); // Never any EOS input buffer.
        assert(!d.codec && !d.window && !d.output_thread_started);
        assert(codecs==0 && windows==0);
        assert(!android_chiaki_video_decoder_video_sample((uint8_t *)"x",1,0,false,&d));
    }
    android_chiaki_video_decoder_set_surface(&d,0,(void *)1);
    android_chiaki_video_decoder_fini(&d);
    assert(codecs==0 && windows==0);
    puts("PASS: 100 create/swap/detach cycles, empty detach, no-EOS shutdown, active fini; zero leaked fake windows/codecs");
}
'''

with tempfile.TemporaryDirectory(prefix="remteh-decoder-test-") as temp:
    base = Path(temp)
    (base / "common.h").write_text(COMMON)
    for header in ("jni.h", "chiaki/log.h", "chiaki/thread.h", "android/native_window_jni.h", "media/NdkMediaCodec.h", "media/NdkMediaFormat.h"):
        path = base / header
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text('#include "common.h"\n')
    (base / "harness.c").write_text(HARNESS)
    cpp = ROOT / "android/app/src/main/cpp"
    binary = base / "test-decoder"
    subprocess.run(["clang", "-std=c11", "-D_DEFAULT_SOURCE", "-D__ANDROID_API__=26", "-fsanitize=address,undefined", "-g", "-pthread", "-I" + str(base), "-I" + str(cpp), str(cpp / "video-decoder.c"), str(base / "harness.c"), "-o", str(binary)], check=True)
    subprocess.run([str(binary)], check=True, timeout=12)
