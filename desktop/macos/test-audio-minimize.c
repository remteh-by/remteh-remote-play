/* Run with the production adapter inserted and SDL_AUDIODRIVER=dummy. */
#include <SDL.h>
#include <assert.h>
#include <dlfcn.h>
#include <stdint.h>
#include <stdio.h>

/* Satisfy the adapter's unrelated video interposition without a decoder. */
int avcodec_receive_frame(void *context,void *frame) {(void)context;(void)frame;return -1;}

int main(void) {
    void (*hidden)(int)=dlsym(RTLD_DEFAULT,"deckivo_set_audio_hidden");
    assert(hidden);
    assert(SDL_Init(SDL_INIT_AUDIO)==0);
    SDL_AudioSpec desired={0};desired.freq=48000;desired.format=AUDIO_S16SYS;
    desired.channels=2;desired.samples=480;
    SDL_AudioDeviceID device=SDL_OpenAudioDevice(NULL,0,&desired,NULL,0);
    assert(device); /* remains paused for deterministic queue inspection */
    int16_t samples[960];for(unsigned i=0;i<960;i++)samples[i]=(int16_t)i;
    assert(SDL_QueueAudio(device,samples,sizeof(samples))==0);
    assert(SDL_GetQueuedAudioSize(device)==sizeof(samples));
    SDL_ClearQueuedAudio(device);
    for(unsigned cycle=0;cycle<500;cycle++){
        hidden(1);
        assert(SDL_QueueAudio(device,samples,sizeof(samples))==0);
        assert(SDL_GetQueuedAudioSize(device)==0); /* no minimized backlog */
        hidden(0);
        assert(SDL_QueueAudio(device,samples,sizeof(samples))==0);
        assert(SDL_GetQueuedAudioSize(device)==sizeof(samples));
        SDL_ClearQueuedAudio(device);
    }
    for(unsigned i=0;i<960;i++)assert(samples[i]==(int16_t)i);
    SDL_CloseAudioDevice(device);SDL_Quit();
    puts("PASS: production SDL queue interposition, 500 mute/unmute cycles, no hidden backlog, input buffer unchanged");
    return 0;
}
