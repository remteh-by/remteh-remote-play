/* Tests the same input state used by the macOS event monitor. */
#include "input-state.h"
#include <assert.h>
#include <stdio.h>

int main(void) {
    DkMacInput s,a,b;uint32_t buttons;int16_t axes[6],first[6],second[6];
    dk_mac_init(&s,.025,false,1.);
    const unsigned keys[]={13,0,1,2};
    const int16_t movement[][2]={{0,-32767},{-32767,0},{0,32767},{32767,0}};
    for(unsigned i=0;i<4;i++){
        dk_mac_reset(&s,1.);assert(dk_mac_key(&s,keys[i],true));dk_mac_sample(&s,1.02,&buttons,axes);
        assert(axes[0]==movement[i][0]&&axes[1]==movement[i][1]&&buttons==0);
        dk_mac_key(&s,keys[i],false);dk_mac_sample(&s,1.04,&buttons,axes);assert(axes[0]==0&&axes[1]==0);
    }
    dk_mac_key(&s,13,true);dk_mac_key(&s,2,true);dk_mac_sample(&s,1.06,&buttons,axes);
    assert(axes[0]>0&&axes[1]<0&&hypot(axes[0],axes[1])<=32768);
    dk_mac_key(&s,1,true);dk_mac_key(&s,0,true);dk_mac_sample(&s,1.08,&buttons,axes);assert(axes[0]==0&&axes[1]==0);

    dk_mac_init(&a,.025,false,1.);dk_mac_init(&b,.025,false,1.);
    dk_mac_motion(&a,8,-4,1.005);
    for(int i=0;i<8;i++)dk_mac_motion(&b,1,-.5,1.001+i*.001);
    dk_mac_sample(&a,1.+1./60.,&buttons,first);dk_mac_sample(&b,1.+1./60.,&buttons,second);
    assert(!memcmp(first,second,sizeof(first)));assert(first[2]>0&&first[3]<0);
    dk_mac_sample(&a,1.+2./60.,&buttons,axes);assert(axes[2]==0&&axes[3]==0); /* no camera tail */
    dk_mac_init(&b,.025,false,1.);dk_mac_motion(&b,4,-2,1.004);dk_mac_sample(&b,1.+1./120.,&buttons,second);
    assert(!memcmp(first,second,sizeof(first))); /* same mouse speed, different timer rate */
    dk_mac_motion(&b,NAN,INFINITY,1.03);dk_mac_sample(&b,1.04,&buttons,axes);assert(axes[2]==0&&axes[3]==0);
    dk_mac_motion(&b,100,100,1.05);dk_mac_sample(&b,2.,&buttons,axes);assert(axes[2]==0&&axes[3]==0);
    dk_mac_init(&b,.025,true,1.);dk_mac_motion(&b,2,-3,1.01);dk_mac_sample(&b,1.02,&buttons,axes);assert(axes[2]>0&&axes[3]>0);
    dk_mac_motion(&b,1e10,1e10,1.03);dk_mac_sample(&b,1.04,&buttons,axes);assert(hypot(axes[2],axes[3])<=32768);

    dk_mac_reset(&s,2.);s.mouse[0]=true;dk_mac_sample(&s,2.02,&buttons,axes);assert(axes[5]==32767&&axes[4]==-32768);
    s.mouse[0]=false;s.mouse[1]=true;dk_mac_sample(&s,2.04,&buttons,axes);assert(axes[4]==32767&&axes[5]==-32768);
    dk_mac_key(&s,56,true);dk_mac_key(&s,59,true);dk_mac_key(&s,58,true);s.mouse[2]=true;
    dk_mac_key(&s,49,true);dk_mac_key(&s,15,true);dk_mac_key(&s,14,true);dk_mac_key(&s,15,false);
    dk_mac_sample(&s,2.06,&buttons,axes);assert((buttons&0x187)==0x187); /* cross,circle,square,L3,R3 */
    dk_mac_reset(&s,2.08);dk_mac_sample(&s,2.1,&buttons,axes);
    assert(buttons==0&&axes[0]==0&&axes[1]==0&&axes[2]==0&&axes[3]==0&&axes[4]==-32768&&axes[5]==-32768);
    assert(!dk_mac_key(&s,300,true));
    /* Side buttons, modifiers, shared actions, and arbitrary physical remapping. */
    s.mouse[3]=s.mouse[4]=true;dk_mac_sample(&s,2.12,&buttons,axes);assert(buttons==6);
    dk_mac_reset(&s,3.);
    assert(dk_mac_bindings(&s,"6:23,7:0,59:9,12:1",false));
    assert(!dk_mac_key(&s,13,true)); /* W is unbound */
    assert(dk_mac_key(&s,6,true));dk_mac_sample(&s,3.02,&buttons,axes);assert(axes[1]==-32767);
    dk_mac_key(&s,6,false);dk_mac_key(&s,62,true);dk_mac_key(&s,12,true);
    dk_mac_sample(&s,3.04,&buttons,axes);assert(buttons==((1u<<9)|(1u<<1))); /* Ctrl+Q are normal actions */
    dk_mac_reset(&s,3.06);assert(s.key_bindings[6]==23); /* reset preserves custom map */
    assert(dk_mac_bindings(&s,"0:0,1:20,2:27,3:21,4:22",true));
    for(unsigned i=0;i<5;i++){
        dk_mac_reset(&s,4.);s.mouse[i]=true;dk_mac_sample(&s,4.02,&buttons,axes);
        if(i==0)assert(buttons==1);
        if(i==1)assert(buttons==(1u<<20));
        if(i==2)assert(axes[3]==-32767);
        if(i==3)assert(axes[4]==32767);
        if(i==4)assert(axes[5]==32767);
        s.mouse[i]=false;dk_mac_sample(&s,4.04,&buttons,axes);assert(!buttons&&axes[3]==0&&axes[4]==INT16_MIN&&axes[5]==INT16_MIN);
    }
    int8_t saved[128];memcpy(saved,s.key_bindings,128);
    const char *invalid[]={"128:0","-1:0","6:31","6:15","6:9999999999999999999999","6:1,","6:no","53:0","100:0","103:0","54:0","55:0","57:0","63:0"};
    for(unsigned i=0;i<sizeof(invalid)/sizeof(invalid[0]);i++){
        assert(!dk_mac_bindings(&s,invalid[i],false));assert(!memcmp(saved,s.key_bindings,128));
    }
    assert(!dk_mac_bindings(&s,"5:1",true));
    assert(dk_mac_bindings(&s,"60:2,61:1,62:0",false));
    assert(s.key_bindings[56]==2&&s.key_bindings[58]==1&&s.key_bindings[59]==0);
    assert(dk_mac_bindings(&s,"",false));assert(!dk_mac_key(&s,56,true));
    assert(dk_mac_bindings(&s,NULL,true));assert(s.mouse_bindings[4]==22);
    assert(dk_mac_bindings(&s,"",true));assert(s.mouse_bindings[4]==-1);

    puts("PASS: WASD directions/releases, diagonal/opposite keys, mouse polling/timer rates, no tail, stale/nonfinite motion, inversion, triggers, common controls, shared bindings, reset, custom keyboard mappings, all five mouse buttons, reserved keys, malformed configuration");
    return 0;
}
