/* SPDX-License-Identifier: GPL-3.0-or-later
 * Physical Mac key positions and per-tick mouse deltas, shared with the tests.
 * Actions 0..14 / 20: SDL buttons; 21/22: L2/R2; 23..30: stick directions.
 */
#ifndef DECKIVO_MAC_INPUT_STATE_H
#define DECKIVO_MAC_INPUT_STATE_H
#include <stdbool.h>
#include <stdint.h>
#include <string.h>
#include <math.h>
#include <stdlib.h>
#include <errno.h>

typedef struct {
    bool keys[128], mouse[5], invert_y;
    int8_t key_bindings[128], mouse_bindings[5];
    double dx, dy, sensitivity, last_tick, last_motion;
} DkMacInput;

static inline unsigned dk_mac_canonical_key(unsigned key) {
    return key==60?56:key==61?58:key==62?59:key;
}
static inline bool dk_mac_reserved_key(unsigned key) {
    return key==53||key==100||key==103||key==54||key==55||key==57||key==63;
}
static inline bool dk_mac_valid_action(long action) {
    return action==-1||(action>=0&&action<=14)||(action>=20&&action<=30);
}
static inline void dk_mac_reset(DkMacInput *s, double now) {
    memset(s->keys,0,sizeof(s->keys));memset(s->mouse,0,sizeof(s->mouse));
    s->dx=s->dy=s->last_motion=0;s->last_tick=now;
}
static inline void dk_mac_init(DkMacInput *s,double sensitivity,bool invert,double now) {
    memset(s,0,sizeof(*s));s->sensitivity=isfinite(sensitivity)?fmax(.001,fmin(.2,sensitivity)):.025;
    s->invert_y=invert;s->last_tick=now;
    memset(s->key_bindings,-1,sizeof(s->key_bindings));
    const unsigned keys[]={13,1,0,2,49,8,59,56,58,15,14,3,18,12,5,126,125,123,124,36,48,120,99};
    const int8_t actions[]={23,24,25,26,0,1,1,7,8,2,2,3,3,9,10,11,12,13,14,6,20,5,4};
    for(unsigned i=0;i<sizeof(keys)/sizeof(keys[0]);i++)s->key_bindings[keys[i]]=actions[i];
    const int8_t mouse[]={22,21,8,1,2};memcpy(s->mouse_bindings,mouse,sizeof(mouse));
}
/* Parse the bounded, normalized launch config. A malformed value leaves defaults intact.
 * Empty text intentionally unbinds all inputs of this type; NULL keeps defaults. */
static inline bool dk_mac_bindings(DkMacInput *s,const char *text,bool mouse) {
    if(!text)return true;
    if(strlen(text)>2048)return false;
    int8_t parsed[128];memset(parsed,-1,sizeof(parsed));
    const char *p=text;
    while(*p){
        char *end;errno=0;long key=strtol(p,&end,10);
        if(end==p||errno||*end!=':'||key<0||key>=(mouse?5:128))return false;
        p=end+1;errno=0;long action=strtol(p,&end,10);
        if(end==p||errno||!dk_mac_valid_action(action)||(*end!=','&&*end!='\0'))return false;
        if(!mouse){key=dk_mac_canonical_key((unsigned)key);if(dk_mac_reserved_key((unsigned)key))return false;}
        parsed[key]=(int8_t)action;
        p=*end?end+1:end;
        if(*end&&!*p)return false;
    }
    memcpy(mouse?s->mouse_bindings:s->key_bindings,parsed,mouse?5:128);return true;
}
static inline bool dk_mac_key(DkMacInput *s,unsigned key,bool down) {
    key=dk_mac_canonical_key(key);
    if(key>=128||dk_mac_reserved_key(key)||s->key_bindings[key]<0)return false;
    s->keys[key]=down;return true;
}
static inline void dk_mac_motion(DkMacInput *s,double dx,double dy,double now) {
    if(!isfinite(dx)||!isfinite(dy)||!isfinite(now))return;
    s->dx=fmax(-4000.,fmin(4000.,s->dx+dx));s->dy=fmax(-4000.,fmin(4000.,s->dy+dy));s->last_motion=now;
}
static inline void dk_mac_sample(DkMacInput *s,double now,uint32_t *buttons,int16_t axes[6]) {
    bool active[31]={0};
    for(unsigned i=0;i<128;i++)if(s->keys[i]&&s->key_bindings[i]>=0)active[(unsigned)s->key_bindings[i]]=true;
    for(unsigned i=0;i<5;i++)if(s->mouse[i]&&s->mouse_bindings[i]>=0)active[(unsigned)s->mouse_bindings[i]]=true;
    double x=(active[26]?1.:0.)-(active[25]?1.:0.);
    double y=(active[24]?1.:0.)-(active[23]?1.:0.);
    double scale=fmax(1.,hypot(x,y));
    axes[0]=(int16_t)lrint(x/scale*32767.);axes[1]=(int16_t)lrint(y/scale*32767.);
    double elapsed=now-s->last_tick;
    double dt=isfinite(elapsed)&&elapsed>0?fmax(.004,fmin(.05,elapsed)):1./60.;
    double rx=(active[30]?1.:0.)-(active[29]?1.:0.);
    double ry=(active[28]?1.:0.)-(active[27]?1.:0.);
    if(now>=s->last_motion&&now-s->last_motion<.08){
        rx+=s->dx*s->sensitivity/(60.*dt);ry+=s->dy*s->sensitivity/(60.*dt)*(s->invert_y?-1.:1.);
    }
    /* Consume every event once: no last-event overwrite or 80 ms camera tail. */
    s->dx=s->dy=0;s->last_tick=now;
    scale=fmax(1.,hypot(rx,ry));
    axes[2]=(int16_t)lrint(rx/scale*32767.);axes[3]=(int16_t)lrint(ry/scale*32767.);
    axes[4]=active[21]?INT16_MAX:INT16_MIN;axes[5]=active[22]?INT16_MAX:INT16_MIN;
    *buttons=0;
    for(unsigned i=0;i<=20;i++)if(active[i])*buttons|=1u<<i;
}
#endif
