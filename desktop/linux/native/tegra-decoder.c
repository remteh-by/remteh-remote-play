/* SPDX-License-Identifier: GPL-3.0-or-later
 * Per-process adapter for Switchroot FFmpeg. No system library is replaced.
 * Chiaki 2.2 opens its decoder before receiving SPS; nvv4l2 needs dimensions.
 * The launcher supplies the negotiated resolution preset explicitly.
 */
#define _GNU_SOURCE
#include <libavcodec/avcodec.h>
#include <dlfcn.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <time.h>
#include <unistd.h>
#include <dirent.h>
#include <sys/ioctl.h>
#include <linux/input.h>
#include <limits.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <stdatomic.h>

static void *current_controller;
static int control_fd = -1;
static int control_attempted;
static char control_path[sizeof(((struct sockaddr_un *)0)->sun_path)];
static _Atomic int exclusive_capture;
static _Atomic unsigned long decoded_frames;
static char decoder_name[64];
static double first_frame_time, last_sample_time;
static unsigned long last_sample_frames;

static double monotonic_seconds(void)
{
    struct timespec t;
    clock_gettime(CLOCK_MONOTONIC, &t);
    return t.tv_sec + t.tv_nsec / 1000000000.0;
}

static void close_control(void)
{
    if (control_fd >= 0) close(control_fd);
    if (control_path[0]) unlink(control_path);
}

static void init_control(void)
{
    if (control_attempted) return;
    control_attempted = 1;
    const char *path = getenv("DECKIVO_CONTROL");
    if (!path || strlen(path) >= sizeof(control_path)) return;
    struct sockaddr_un addr = { .sun_family = AF_UNIX };
    strcpy(addr.sun_path, path);
    /* The launcher supplies a path in its mode-0700 configuration directory.
     * Never listen on TCP, accept shell commands, or touch another user's path. */
    struct stat info;
    if (!lstat(path, &info)) {
        if (!S_ISSOCK(info.st_mode) || info.st_uid != geteuid()) return;
        unlink(path);
    }
    control_fd = socket(AF_UNIX, SOCK_DGRAM | SOCK_NONBLOCK | SOCK_CLOEXEC, 0);
    if (control_fd < 0) return;
    if (bind(control_fd, (struct sockaddr *)&addr, sizeof(addr))) {
        close(control_fd); control_fd = -1; return;
    }
    chmod(path, 0600);
    strcpy(control_path, path);
    atexit(close_control);
}

/* Chiaki polls SDL on its Qt GUI timer. Calling quit from this hook stays on
 * the GUI thread and lets the normal stack destructors stop the PS5 session.
 * No SIGTERM/SIGKILL and no synthetic keyboard events are used. */
int SDL_PollEvent(void *event)
{
    static int (*next)(void *);
    static double chord_since;
    static int quitting;
    if (!next) next = dlsym(RTLD_NEXT, "SDL_PollEvent");
    init_control();
    char command[16];
    int stop = control_fd >= 0 && recv(control_fd, command, sizeof(command), MSG_DONTWAIT) == 4
               && !memcmp(command, "stop", 4);
    const char *chord = getenv("DECKIVO_DISCONNECT_CHORD");
    if (current_controller && chord && !strcmp(chord, "1")) {
        unsigned char (*get_button)(void *, int) = dlsym(RTLD_NEXT, "SDL_GameControllerGetButton");
        if (get_button && get_button(current_controller, 4) && get_button(current_controller, 6)) {
            if (!chord_since) chord_since = monotonic_seconds();
            if (monotonic_seconds() - chord_since >= 1.5) stop = 1;
        } else chord_since = 0;
    }
    if (stop && !quitting) {
        void (*quit)(void) = dlsym(RTLD_DEFAULT, "_ZN16QCoreApplication4quitEv");
        if (quit) {
            quitting = 1;
            fprintf(stderr, "[Deckivo] Graceful disconnect requested\n");
            quit();
        }
    }
    return next(event);
}

void SDL_GameControllerClose(void *controller)
{
    static void (*next)(void *);
    if (!next) next = dlsym(RTLD_NEXT, "SDL_GameControllerClose");
    if (current_controller == controller) current_controller = NULL;
    next(controller);
}

/* Use SDL's existing evdev file descriptor so only this client receives the
 * controller while streaming. The kernel releases the grab when it closes.
 * Never open/grab keyboards, touchscreens, or arbitrary input devices. */
void *SDL_GameControllerOpen(int index)
{
    static void *(*next)(int);
    if (!next) next = dlsym(RTLD_NEXT, "SDL_GameControllerOpen");
    void *controller = next(index);
    if (controller) current_controller = controller;
    const char *(*path_for_index)(int) = dlsym(RTLD_NEXT, "SDL_JoystickPathForIndex");
    const char *path = controller && path_for_index ? path_for_index(index) : NULL;
    if (!path || strncmp(path, "/dev/input/event", 16)) return controller;
    DIR *directory = opendir("/proc/self/fd");
    if (!directory) return controller;
    struct dirent *entry;
    while ((entry = readdir(directory))) {
        char link[PATH_MAX], target[PATH_MAX];
        int fd = atoi(entry->d_name);
        if (fd <= 2) continue;
        snprintf(link, sizeof(link), "/proc/self/fd/%d", fd);
        ssize_t length = readlink(link, target, sizeof(target) - 1);
        if (length <= 0) continue;
        target[length] = 0;
        if (!strcmp(path, target)) {
            int result = ioctl(fd, EVIOCGRAB, 1);
            exclusive_capture = result == 0;
            fprintf(stderr, "[Deckivo] Controller capture=%s\n", result ? "unavailable" : "exclusive");
            break;
        }
    }
    closedir(directory);
    return controller;
}

unsigned char SDL_GameControllerGetButton(void *controller, int button)
{
    static unsigned char (*next)(void *, int);
    if (!next) next = dlsym(RTLD_NEXT, "SDL_GameControllerGetButton");
    /* Switch Capture / G8+ screenshot button acts as the PS touchpad click. */
    if (button == 20 && next(controller, 15)) return 1;
    return next(controller, button);
}

const AVCodec *avcodec_find_decoder(enum AVCodecID id)
{
    static const AVCodec *(*next)(enum AVCodecID);
    if (!next) next = dlsym(RTLD_NEXT, "avcodec_find_decoder");
    const char *mode = getenv("DECKIVO_DECODER_MODE");
    if (mode && !strcmp(mode, "software") &&
            (id == AV_CODEC_ID_H264 || id == AV_CODEC_ID_HEVC)) {
        const AVCodec *(*by_name)(const char *) = dlsym(RTLD_NEXT, "avcodec_find_decoder_by_name");
        return by_name(id == AV_CODEC_ID_H264 ? "h264" : "hevc");
    }
    return next(id);
}

int avcodec_open2(AVCodecContext *context, const AVCodec *codec, AVDictionary **options)
{
    static int (*next)(AVCodecContext *, const AVCodec *, AVDictionary **);
    if (!next) next = dlsym(RTLD_NEXT, "avcodec_open2");
    if (codec && strstr(codec->name, "_nvv4l2")) {
        const char *w = getenv("DECKIVO_VIDEO_WIDTH"), *h = getenv("DECKIVO_VIDEO_HEIGHT");
        int width = w ? atoi(w) : 0, height = h ? atoi(h) : 0;
        if ((width == 1280 && height == 720) || (width == 960 && height == 540)
                || (width == 640 && height == 360) || (width == 1920 && height == 1080)) {
            context->width = context->coded_width = width;
            context->height = context->coded_height = height;
            context->pix_fmt = AV_PIX_FMT_YUV420P;
        }
    }
    int result = next(context, codec, options);
    if (codec && codec->type == AVMEDIA_TYPE_VIDEO)
    {
        snprintf(decoder_name, sizeof(decoder_name), "%s", codec->name);
        fprintf(stderr, "[Deckivo] Decoder %s: %dx%d, open=%d\n", codec->name,
                context->width, context->height, result);
    }
    return result;
}

int avcodec_receive_frame(AVCodecContext *context, AVFrame *frame)
{
    static int (*next)(AVCodecContext *, AVFrame *);
    if (!next) next = dlsym(RTLD_NEXT, "avcodec_receive_frame");
    int result = next(context, frame);
    if (!result && context->codec_type == AVMEDIA_TYPE_VIDEO) {
        unsigned long frames = atomic_fetch_add(&decoded_frames, 1) + 1;
        double now = monotonic_seconds();
        if (!first_frame_time) first_frame_time = last_sample_time = now;
        if (frames == 1 || now - last_sample_time >= 1.0) {
            const char *path = getenv("DECKIVO_METRICS");
            char tmp[PATH_MAX];
            if (path && snprintf(tmp, sizeof(tmp), "%s.%ld.tmp", path, (long)getpid()) < (int)sizeof(tmp)) {
                int fd = open(tmp, O_WRONLY | O_CREAT | O_TRUNC | O_CLOEXEC | O_NOFOLLOW, 0600);
                if (fd >= 0) {
                    double fps = frames == 1 ? 0 : (frames - last_sample_frames) / (now - last_sample_time);
                    dprintf(fd, "{\"pid\":%ld,\"frames\":%lu,\"width\":%d,\"height\":%d,"
                        "\"elapsed_ms\":%lu,\"decode_fps\":%.1f,\"decoder\":\"%s\",\"exclusive\":%s}\n",
                        (long)getpid(), frames, frame->width, frame->height,
                        (unsigned long)((now - first_frame_time) * 1000), fps,
                        decoder_name, exclusive_capture ? "true" : "false");
                    close(fd);
                    if (rename(tmp, path)) unlink(tmp);
                }
            }
            last_sample_time = now;
            last_sample_frames = frames;
        }
        if (frames == 1 || frames % 600 == 0)
            fprintf(stderr, "[Deckivo] Decoded frames=%lu, %dx%d, pixel_format=%d\n",
                    frames, frame->width, frame->height, frame->format);
    }
    return result;
}
