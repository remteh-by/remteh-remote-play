// SPDX-License-Identifier: LicenseRef-AGPL-3.0-only-OpenSSL

#include "video-decoder.h"

#include <jni.h>

#include <android/native_window_jni.h>
#include <media/NdkMediaCodec.h>
#include <media/NdkMediaFormat.h>

#include <string.h>
#include <time.h>

#define INPUT_BUFFER_TIMEOUT_MS 10

static void *android_chiaki_video_decoder_output_thread_func(void *user);

ChiakiErrorCode
android_chiaki_video_decoder_init(AndroidChiakiVideoDecoder *decoder,
                                  ChiakiLog *log, int32_t target_width,
                                  int32_t target_height, ChiakiCodec codec) {
  decoder->log = log;
  decoder->codec = NULL;
  decoder->timestamp_cur = 0;
  decoder->target_width = target_width;
  decoder->target_height = target_height;
  decoder->target_codec = codec;
  decoder->window = NULL;
  atomic_init(&decoder->shutdown_output, false);
  atomic_init(&decoder->input_buffers,0);atomic_init(&decoder->decoded_frames,0);
  atomic_init(&decoder->surface_submissions,0);atomic_init(&decoder->receiver_lost_frames,0);
  atomic_init(&decoder->first_output_ns,0);
  decoder->output_thread_started = false;
  return chiaki_mutex_init(&decoder->codec_mutex, false);
}

/* Caller owns codec_mutex. The output thread never takes it and has a bounded
 * dequeue timeout, so joining cannot deadlock with surface teardown. */
static void kill_decoder_locked(AndroidChiakiVideoDecoder *decoder) {
  atomic_store(&decoder->shutdown_output, true);
  if (decoder->output_thread_started) {
    chiaki_thread_join(&decoder->output_thread, NULL);
    decoder->output_thread_started = false;
  }
  if (decoder->codec) {
    AMediaCodec_stop(decoder->codec);
    AMediaCodec_delete(decoder->codec);
    decoder->codec = NULL;
  }
  if (decoder->window) {
    ANativeWindow_release(decoder->window);
    decoder->window = NULL;
  }
  atomic_store(&decoder->shutdown_output, false);
}

void android_chiaki_video_decoder_fini(AndroidChiakiVideoDecoder *decoder) {
  chiaki_mutex_lock(&decoder->codec_mutex);
  kill_decoder_locked(decoder);
  chiaki_mutex_unlock(&decoder->codec_mutex);
  chiaki_mutex_fini(&decoder->codec_mutex);
}

void android_chiaki_video_decoder_set_surface(
    AndroidChiakiVideoDecoder *decoder, JNIEnv *env, jobject surface) {
  chiaki_mutex_lock(&decoder->codec_mutex);

  if (!surface) {
    kill_decoder_locked(decoder);
    goto beach;
  }

  if (decoder->codec) {
#if __ANDROID_API__ >= 23
    CHIAKI_LOGI(decoder->log,
                "Video decoder already initialized, swapping surface");
    ANativeWindow *new_window =
        surface ? ANativeWindow_fromSurface(env, surface) : NULL;
    if (!new_window) goto beach;
    if (AMediaCodec_setOutputSurface(decoder->codec, new_window) != AMEDIA_OK) {
      ANativeWindow_release(new_window);
      goto beach;
    }
    ANativeWindow_release(decoder->window);
    decoder->window = new_window;
#else
    CHIAKI_LOGE(decoder->log, "Video Decoder already initialized");
#endif
    goto beach;
  }

  decoder->window = ANativeWindow_fromSurface(env, surface);
  if (!decoder->window) goto beach;

  const char *mime =
      chiaki_codec_is_h265(decoder->target_codec) ? "video/hevc" : "video/avc";
  CHIAKI_LOGI(decoder->log, "Initializing decoder with mime %s", mime);

  decoder->codec = AMediaCodec_createDecoderByType(mime);
  if (!decoder->codec) {
    CHIAKI_LOGE(decoder->log, "Failed to create AMediaCodec for mime type %s",
                mime);
    goto error_surface;
  }

  AMediaFormat *format = AMediaFormat_new();
  AMediaFormat_setString(format, AMEDIAFORMAT_KEY_MIME, mime);
  AMediaFormat_setInt32(format, AMEDIAFORMAT_KEY_WIDTH, decoder->target_width);
  AMediaFormat_setInt32(format, AMEDIAFORMAT_KEY_HEIGHT,
                        decoder->target_height);

  media_status_t r =
      AMediaCodec_configure(decoder->codec, format, decoder->window, NULL, 0);
  if (r != AMEDIA_OK) {
    CHIAKI_LOGE(decoder->log, "AMediaCodec_configure() failed: %d", (int)r);
    AMediaFormat_delete(format);
    goto error_codec;
  }

  r = AMediaCodec_start(decoder->codec);
  AMediaFormat_delete(format);
  if (r != AMEDIA_OK) {
    CHIAKI_LOGE(decoder->log, "AMediaCodec_start() failed: %d", (int)r);
    goto error_codec;
  }

  ChiakiErrorCode err = chiaki_thread_create(
      &decoder->output_thread, android_chiaki_video_decoder_output_thread_func,
      decoder);
  if (err != CHIAKI_ERR_SUCCESS) {
    CHIAKI_LOGE(decoder->log, "Failed to create output thread for AMediaCodec");
    AMediaCodec_stop(decoder->codec);
    goto error_codec;
  }
  decoder->output_thread_started = true;

  goto beach;

error_codec:
  AMediaCodec_delete(decoder->codec);
  decoder->codec = NULL;

error_surface:
  ANativeWindow_release(decoder->window);
  decoder->window = NULL;

beach:
  chiaki_mutex_unlock(&decoder->codec_mutex);
}

bool android_chiaki_video_decoder_video_sample(uint8_t *buf, size_t buf_size,
                                               int32_t frames_lost,
                                               bool frame_recovered,
                                               void *user) {
  (void)frame_recovered; // unused
  bool r = true;
  AndroidChiakiVideoDecoder *decoder = user;
  if(frames_lost>0)atomic_fetch_add(&decoder->receiver_lost_frames,(unsigned long long)frames_lost);
  chiaki_mutex_lock(&decoder->codec_mutex);

  if (!decoder->codec) {
    CHIAKI_LOGE(decoder->log,
                "Received video data, but decoder is not initialized!");
    r = false;
    goto beach;
  }

  while (buf_size > 0) {
    ssize_t codec_buf_index = AMediaCodec_dequeueInputBuffer(
        decoder->codec, INPUT_BUFFER_TIMEOUT_MS * 1000);
    if (codec_buf_index < 0) {
      CHIAKI_LOGE(decoder->log, "Failed to get input buffer");
      r = false;
      goto beach;
    }

    size_t codec_buf_size;
    uint8_t *codec_buf = AMediaCodec_getInputBuffer(
        decoder->codec, (size_t)codec_buf_index, &codec_buf_size);
    if (!codec_buf || !codec_buf_size) { r = false; goto beach; }
    size_t codec_sample_size = buf_size;
    if (codec_sample_size > codec_buf_size) {
      // CHIAKI_LOGD(decoder->log, "Sample is bigger than buffer, splitting");
      codec_sample_size = codec_buf_size;
    }
    memcpy(codec_buf, buf, codec_sample_size);
    media_status_t r = AMediaCodec_queueInputBuffer(
        decoder->codec, (size_t)codec_buf_index, 0, codec_sample_size,
        decoder->timestamp_cur++,
        0); // timestamp just raised by 1 for maximum realtime
    if (r != AMEDIA_OK) {
      CHIAKI_LOGE(decoder->log, "AMediaCodec_queueInputBuffer() failed: %d",
                  (int)r);
    } else atomic_fetch_add(&decoder->input_buffers,1);
    buf += codec_sample_size;
    buf_size -= codec_sample_size;
  }

beach:
  chiaki_mutex_unlock(&decoder->codec_mutex);
  return r;
}

static void *android_chiaki_video_decoder_output_thread_func(void *user) {
  AndroidChiakiVideoDecoder *decoder = user;

  while (!atomic_load(&decoder->shutdown_output)) {
    AMediaCodecBufferInfo info;
    ssize_t status = AMediaCodec_dequeueOutputBuffer(decoder->codec, &info, 10000);
    if (status >= 0) {
      if(info.size!=0){
        atomic_fetch_add(&decoder->decoded_frames,1);
        if(atomic_load(&decoder->first_output_ns)==0){
          struct timespec at;clock_gettime(CLOCK_MONOTONIC,&at);
          atomic_store(&decoder->first_output_ns,(unsigned long long)at.tv_sec*1000000000ULL+at.tv_nsec);
        }
      }
      media_status_t released=AMediaCodec_releaseOutputBuffer(decoder->codec,(size_t)status,info.size!=0);
      if(info.size!=0 && released==AMEDIA_OK)atomic_fetch_add(&decoder->surface_submissions,1);
      if (info.flags & AMEDIACODEC_BUFFER_FLAG_END_OF_STREAM) {
        CHIAKI_LOGI(decoder->log, "AMediaCodec reported EOS");
        break;
      }
    } else {
      bool shutdown = atomic_load(&decoder->shutdown_output);
      if (shutdown) {
        CHIAKI_LOGI(decoder->log, "Video Decoder Output Thread detected "
                                  "shutdown after reported error");
        break;
      }
    }
  }

  CHIAKI_LOGI(decoder->log, "Video Decoder Output Thread exiting");

  return NULL;
}
