/* SPDX-License-Identifier: GPL-3.0-or-later
 * Deckivo's own per-process SDL2 input bridge. No global HID or input hooks.
 * ABI: SDL_VirtualJoystickDesc v1, SDL >= 2.24 (wiki.libsdl.org/SDL2).
 * Only a private, mode-0600 local socket accepts fixed-size state packets.
 */
#define _GNU_SOURCE
#include <stdint.h>
#include <stdlib.h>
#include <string.h>
#include <stdio.h>
#include <dlfcn.h>
#include <unistd.h>
#include <sys/socket.h>
#include <sys/un.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <time.h>
#include <pthread.h>
#include <stdatomic.h>
#ifdef __APPLE__
#include <dispatch/dispatch.h>
#include <objc/runtime.h>
#include <objc/message.h>
extern int SDL_NumJoysticks(void);
extern int SDL_PollEvent(void *);
extern int avcodec_receive_frame(void *,void *);
/* The adapter belongs to this executable, never to Qt helper subprocesses. */
static void init_owned_stop(void);
extern void deckivo_macos_input_start(void);
extern void deckivo_macos_capture(void *);
extern void deckivo_macos_release(void *);
extern void deckivo_macos_activate(void *);
extern void deckivo_macos_close(void *);
__attribute__((constructor)) static void isolate_adapter(void) { unsetenv("DYLD_INSERT_LIBRARIES");init_owned_stop();deckivo_macos_input_start(); }
#endif

typedef struct {
    uint16_t version,type,naxes,nbuttons,nhats,vendor_id,product_id,padding;
    uint32_t button_mask,axis_mask;
    const char *name;
    void *userdata;
    void (*Update)(void *);
    void (*SetPlayerIndex)(void *,int);
    int (*Rumble)(void *,uint16_t,uint16_t);
    int (*RumbleTriggers)(void *,uint16_t,uint16_t);
    int (*SetLED)(void *,uint8_t,uint8_t,uint8_t);
    int (*SendEffect)(void *,const void *,int);
} DkVirtualDesc;
static int input_fd=-1,device_index=-1,attempted,virtual_attempted,quitting;
static void *joystick;
static char input_path[sizeof(((struct sockaddr_un *)0)->sun_path)];
static double received_at;
static uint32_t last_sequence;
static int sequence_seen;
static __thread int updating;
static int (*set_axis)(void *,int,int16_t);
static int (*set_button)(void *,int,uint8_t);
static int (*next_poll)(void *);
static int (*next_num)(void);
static double now(void) {struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec/1e9;}
static uint32_t u32(const unsigned char *p) {return (uint32_t)p[0]|(uint32_t)p[1]<<8|(uint32_t)p[2]<<16|(uint32_t)p[3]<<24;}
static int16_t i16(const unsigned char *p) {return (int16_t)((unsigned)p[0]|(unsigned)p[1]<<8);}
static void neutral(void) {
    if(!joystick||!set_axis||!set_button)return;
    for(int i=0;i<6;i++)set_axis(joystick,i,i>=4?INT16_MIN:0);
    for(int i=0;i<21;i++)set_button(joystick,i,0);
}
#ifdef __APPLE__
void deckivo_notify_closing(void) {
    const char *path=getenv("DECKIVO_SUPERVISOR_SOCKET");
    if(!path||!path[0]||strlen(path)>=sizeof(((struct sockaddr_un *)0)->sun_path))return;
    int fd=socket(AF_UNIX,SOCK_DGRAM,0);if(fd<0)return;
    struct sockaddr_un address={0};address.sun_family=AF_UNIX;strcpy(address.sun_path,path);
    (void)sendto(fd,"closing",7,MSG_DONTWAIT,(struct sockaddr *)&address,sizeof(address));close(fd);
}
static void quit_main(void *unused) {
    (void)unused;deckivo_macos_release(NULL);neutral();
    fprintf(stderr,"[Deckivo] user-ended stream\n");
    deckivo_notify_closing();
    /* The engine's window close event stops its session before Qt exits.
     * NSApplication terminate skips that event and can block session join. */
    deckivo_macos_close(NULL);
}
#endif
#ifdef __APPLE__
void deckivo_request_quit(void) {dispatch_async_f(dispatch_get_main_queue(),NULL,quit_main);}
static dispatch_source_t stop_source;
static int stop_fd=-1,stop_requested;
static char stop_path[sizeof(((struct sockaddr_un *)0)->sun_path)];
static void stop_cleanup(void) {
    if(stop_source)dispatch_source_cancel(stop_source);
    if(stop_fd>=0){close(stop_fd);stop_fd=-1;}
    if(stop_path[0])unlink(stop_path);
}
static void stop_read(void *unused) {
    (void)unused;char data[8];
    if(recv(stop_fd,data,sizeof(data),MSG_DONTWAIT)!=4)return;
    if(!memcmp(data,"quit",4)&&!stop_requested){stop_requested=1;dispatch_async_f(dispatch_get_main_queue(),NULL,quit_main);}
    else if(!memcmp(data,"grab",4))dispatch_async_f(dispatch_get_main_queue(),NULL,deckivo_macos_capture);
    else if(!memcmp(data,"drop",4))dispatch_async_f(dispatch_get_main_queue(),NULL,deckivo_macos_release);
}
static void init_owned_stop(void) {
    const char *path=getenv("DECKIVO_STOP_SOCKET");
    if(!path||!path[0]||strlen(path)>=sizeof(stop_path))return;
    struct stat info;if(lstat(path,&info)==0)return;
    stop_fd=socket(AF_UNIX,SOCK_DGRAM,0);if(stop_fd<0)return;
    struct sockaddr_un address={0};address.sun_family=AF_UNIX;strcpy(address.sun_path,path);
    if(bind(stop_fd,(struct sockaddr *)&address,sizeof(address))<0){close(stop_fd);stop_fd=-1;return;}
    chmod(path,0600);strcpy(stop_path,path);atexit(stop_cleanup);
    stop_source=dispatch_source_create(DISPATCH_SOURCE_TYPE_READ,(uintptr_t)stop_fd,0,dispatch_get_global_queue(DISPATCH_QUEUE_PRIORITY_DEFAULT,0));
    if(!stop_source){stop_cleanup();return;}
    dispatch_source_set_event_handler_f(stop_source,stop_read);dispatch_resume(stop_source);
    fprintf(stderr,"[Deckivo] owned engine control ready\n");
}
#endif
static void update_input(void *unused) {
    (void)unused;
    if(input_fd<0)return;
    unsigned char packet[32];ssize_t length;int count=0;
    while(count++<64&&(length=recv(input_fd,packet,sizeof(packet),MSG_DONTWAIT))>0) {
        if(length==4&&!memcmp(packet,"quit",4)) {
            if(!quitting){quitting=1;neutral();
#ifdef __APPLE__
                dispatch_async_f(dispatch_get_main_queue(),NULL,quit_main);
#else
                void (*quit)(void)=dlsym(RTLD_DEFAULT,"_ZN16QCoreApplication4quitEv");if(quit)quit();
#endif
            }continue;
        }
        if(length!=24||memcmp(packet,"DKI1",4)||!joystick)continue;
        uint32_t sequence=u32(packet+4),buttons=u32(packet+8);
        if(buttons&~0x1fffffu)continue;
        if(sequence_seen&&(int32_t)(sequence-last_sequence)<=0)continue;
        last_sequence=sequence;sequence_seen=1;received_at=now();
        for(int i=0;i<6;i++)set_axis(joystick,i,i16(packet+12+i*2));
        for(int i=0;i<21;i++)set_button(joystick,i,(buttons>>i)&1);
    }
    if(joystick&&received_at&&now()-received_at>.25){neutral();received_at=0;}
}
static void cleanup(void) {if(input_fd>=0)close(input_fd);if(input_path[0])unlink(input_path);}
static void initialize(void) {
    if(updating)return;
    const char *path=getenv("DECKIVO_INPUT_SOCKET");
    if(!path||!path[0]||strlen(path)>=sizeof(input_path))return;
    if(!attempted){
        attempted=1;
        struct stat info;
        if(lstat(path,&info)==0){
            const char *owned=getenv("DECKIVO_OWNED_STREAM");
            if(owned&&!strcmp(owned,"1")&&S_ISSOCK(info.st_mode)&&info.st_uid==geteuid()){if(unlink(path)<0)return;}
            else{fprintf(stderr,"[Deckivo] input socket already exists; refusing reuse\n");return;}
        }
        input_fd=socket(AF_UNIX,SOCK_DGRAM,0);if(input_fd<0)return;
        struct sockaddr_un address={0};address.sun_family=AF_UNIX;strcpy(address.sun_path,path);
        if(bind(input_fd,(struct sockaddr *)&address,sizeof(address))<0){close(input_fd);input_fd=-1;return;}
        chmod(path,0600);strcpy(input_path,path);atexit(cleanup);
    }
    if(input_fd<0||virtual_attempted)return;
    const char *enabled=getenv("DECKIVO_KBM");
    if(!enabled||strcmp(enabled,"1"))return;
    uint32_t (*was_init)(uint32_t)=dlsym(RTLD_DEFAULT,"SDL_WasInit");
    int (*attach)(const DkVirtualDesc *)=dlsym(RTLD_DEFAULT,"SDL_JoystickAttachVirtualEx");
    void *(*open_joystick)(int)=dlsym(RTLD_DEFAULT,"SDL_JoystickOpen");
    set_axis=dlsym(RTLD_DEFAULT,"SDL_JoystickSetVirtualAxis");set_button=dlsym(RTLD_DEFAULT,"SDL_JoystickSetVirtualButton");
    if(!was_init||!(was_init(0x200)&0x200))return;
    virtual_attempted=1;
    if(!attach||!open_joystick||!set_axis||!set_button){
        fprintf(stderr,"[Deckivo] SDL virtual input unavailable\n");return;
    }
    DkVirtualDesc desc={0};desc.version=1;desc.type=1;desc.naxes=6;desc.nbuttons=21;
    desc.axis_mask=0x3f;desc.button_mask=0x1fffff;desc.name="Deckivo Keyboard & Mouse";desc.Update=update_input;
    updating=1;device_index=attach(&desc);if(device_index>=0)joystick=open_joystick(device_index);updating=0;
    if(joystick){neutral();fprintf(stderr,"[Deckivo] keyboard/mouse virtual controller ready\n");}
}
int deckivo_ensure_controller(void) {
    uint32_t (*was_init)(uint32_t)=dlsym(RTLD_DEFAULT,"SDL_WasInit");
    int (*init)(uint32_t)=dlsym(RTLD_DEFAULT,"SDL_InitSubSystem");
    if(!was_init||!init)return 0;
    if(!(was_init(0x200)&0x200)&&init(0x2200)<0)return 0;
    initialize();return joystick!=NULL;
}
unsigned deckivo_controller_status(void) {
    uint32_t (*was_init)(uint32_t)=dlsym(RTLD_DEFAULT,"SDL_WasInit");
    if(!joystick||!was_init||!(was_init(0x200)&0x200))return 0;
    int (*attached)(void *)=dlsym(RTLD_DEFAULT,"SDL_JoystickGetAttached");
    int32_t (*instance)(void *)=dlsym(RTLD_DEFAULT,"SDL_JoystickInstanceID");
    void *(*controller)(int32_t)=dlsym(RTLD_DEFAULT,"SDL_GameControllerFromInstanceID");
    unsigned status=1;
    if(attached&&attached(joystick))status|=2;
    if(instance&&controller&&controller(instance(joystick)))status|=4;
    return status;
}
void deckivo_set_controller(uint32_t buttons,const int16_t axes[6]) {
    uint32_t (*was_init)(uint32_t)=dlsym(RTLD_DEFAULT,"SDL_WasInit");
    if(!joystick||!set_axis||!set_button||!was_init||!(was_init(0x200)&0x200))return;
    for(int i=0;i<6;i++)set_axis(joystick,i,axes[i]);
    for(int i=0;i<21;i++)set_button(joystick,i,(buttons>>i)&1);
}
void deckivo_pump_controller(void) {uint32_t (*was_init)(uint32_t)=dlsym(RTLD_DEFAULT,"SDL_WasInit");void (*update)(void)=dlsym(RTLD_DEFAULT,"SDL_JoystickUpdate");if(update&&was_init&&(was_init(0x200)&0x200))update();}
static int dk_num(void) {
#ifdef __APPLE__
    if(!next_num)next_num=SDL_NumJoysticks;
#else
    if(!next_num)next_num=dlsym(RTLD_NEXT,"SDL_NumJoysticks");
#endif
    if(!updating)initialize();
    return next_num?next_num():0;
}
static int dk_poll(void *event) {
#ifdef __APPLE__
    if(!next_poll)next_poll=SDL_PollEvent;
#else
    if(!next_poll)next_poll=dlsym(RTLD_NEXT,"SDL_PollEvent");
#endif
    initialize();update_input(NULL);
    return next_poll?next_poll(event):0;
}
#ifdef __APPLE__
extern int SDL_NumJoysticks(void);extern int SDL_PollEvent(void *);
#define INTERPOSE(new,old) __attribute__((used)) static struct {const void *replacement,*original;} interpose_##old __attribute__((section("__DATA,__interpose")))={(const void *)&new,(const void *)&old}
INTERPOSE(dk_num,SDL_NumJoysticks);INTERPOSE(dk_poll,SDL_PollEvent);
/* Keep draining decoded audio while the owned window is minimized/hidden.
 * Dropping queue submissions avoids a stale audio backlog on return and does
 * not alter the system volume, microphone capture or the owner's audio level. */
static _Atomic int minimized_audio;
void deckivo_set_audio_hidden(int hidden) {atomic_store(&minimized_audio,hidden!=0);}
extern int SDL_QueueAudio(uint32_t,const void *,uint32_t);
static int dk_queue_audio(uint32_t device,const void *data,uint32_t length) {
    if(atomic_load(&minimized_audio))return 0;
    return SDL_QueueAudio(device,data,length);
}
INTERPOSE(dk_queue_audio,SDL_QueueAudio);
/* Count successful video decode calls without depending on an AVFrame layout. */
static unsigned long frames;static double first_frame;
static int dk_receive(void *context,void *frame) {
    static int (*next)(void *,void *);if(!next)next=avcodec_receive_frame;
    int result=next?next(context,frame):-1;
    if(result==0){frames++;if(!first_frame){first_frame=now();dispatch_async_f(dispatch_get_main_queue(),NULL,deckivo_macos_activate);}
        const char *path=getenv("DECKIVO_METRICS");
        if(path&&(frames==1||frames%30==0)){
            char temporary[1024];if(snprintf(temporary,sizeof(temporary),"%s.new",path)<(int)sizeof(temporary)){
                FILE *file=fopen(temporary,"w");
                if(file){double elapsed=now()-first_frame;fprintf(file,"{\"pid\":%d,\"frames\":%lu,\"elapsed_ms\":%lu,\"decoder\":\"macos_engine\"}",getpid(),frames,(unsigned long)(elapsed*1000));fclose(file);chmod(temporary,0600);rename(temporary,path);}
            }
        }
    }return result;
}
extern int avcodec_receive_frame(void *,void *);INTERPOSE(dk_receive,avcodec_receive_frame);
#else
int SDL_NumJoysticks(void){return dk_num();}int SDL_PollEvent(void *event){return dk_poll(event);}
#endif
