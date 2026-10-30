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

    /* The production focus policy must recover from minimize/restore without
     * replaying held inputs or undoing an explicit Esc/F8 release. */
    DkMacInput focus_input;dk_mac_init(&focus_input,.025,false,1.);
    DkMacCapture capture={0};DkMacFocus focused={true,true,true,false,false};
    assert(dk_mac_capture_eligible(true,focused));
    assert(!dk_mac_capture_wants_resume(&capture,true)); /* never enabled */
    for(unsigned cycle=0;cycle<500;cycle++){
        dk_mac_capture_begin(&capture);
        assert(dk_mac_key(&focus_input,13,true));focus_input.mouse[0]=true;
        dk_mac_motion(&focus_input,30,20,10.);
        assert(dk_mac_capture_end(&capture,&focus_input,10.01,true));
        assert(!capture.active&&capture.resume_on_focus);
        /* App resign + window resign can describe the same focus loss. */
        assert(!dk_mac_capture_end(&capture,&focus_input,10.02,true));
        assert(capture.resume_on_focus);
        dk_mac_sample(&focus_input,10.03,&buttons,axes);
        assert(!buttons&&!axes[0]&&!axes[1]&&!axes[2]&&!axes[3]&&axes[4]==INT16_MIN&&axes[5]==INT16_MIN);
        for(unsigned mask=0;mask<32;mask++){
            DkMacFocus focus={(mask&1)!=0,(mask&2)!=0,(mask&4)!=0,(mask&8)!=0,(mask&16)!=0};
            bool eligible=dk_mac_capture_eligible(true,focus);
            assert(eligible==(mask==7));
            assert(dk_mac_capture_wants_resume(&capture,eligible)==eligible);
            assert(!dk_mac_capture_eligible(false,focus));
        }
        assert(dk_mac_capture_wants_resume(&capture,dk_mac_capture_eligible(true,focused)));
        dk_mac_capture_begin(&capture);assert(capture.active&&!capture.resume_on_focus);
        dk_mac_sample(&focus_input,10.04,&buttons,axes);
        assert(!buttons&&!axes[1]&&axes[5]==INT16_MIN); /* no ghost W/click */
        dk_mac_key(&focus_input,13,true);dk_mac_sample(&focus_input,10.05,&buttons,axes);
        assert(axes[1]==-32767); /* fresh input works after resume */
        assert(dk_mac_capture_end(&capture,&focus_input,10.06,false));
        assert(!dk_mac_capture_wants_resume(&capture,true)); /* End stream */
        dk_mac_capture_end(&capture,&focus_input,10.07,true);
        assert(!dk_mac_capture_wants_resume(&capture,true)); /* later focus change */
        dk_mac_capture_begin(&capture); /* explicit F8 can start again */
        dk_mac_capture_end(&capture,&focus_input,10.08,true);
        dk_mac_capture_end(&capture,&focus_input,10.09,false);
        assert(!dk_mac_capture_wants_resume(&capture,true)); /* cancel pending resume */
        /* Esc/F8 used to expose the minimize button must not permanently turn
         * off input after the next minimize/return cycle. */
        dk_mac_capture_begin(&capture);
        dk_mac_capture_end(&capture,&focus_input,10.1,false);
        dk_mac_capture_ungrab(&capture);
        assert(!dk_mac_capture_wants_resume(&capture,true)); /* cursor remains free now */
        dk_mac_capture_end(&capture,&focus_input,10.2,true);
        assert(dk_mac_capture_wants_resume(&capture,true)); /* return re-enters */
        dk_mac_capture_begin(&capture);
        dk_mac_capture_end(&capture,&focus_input,10.3,false);
        assert(!capture.active&&!capture.resume_on_focus&&!capture.rearm_on_focus_loss);
    }
    DkMacRect screen={0,0,1440,900},large={0,0,2880,1800};
    DkMacRect restored=dk_mac_restore_frame(large,screen);
    assert(restored.width==1440&&restored.height==900); /* points, not Retina pixels */
    restored=dk_mac_restore_frame((DkMacRect){800,800,600,400},screen);
    assert(restored.x==800&&restored.y==500&&restored.width==600&&restored.height==400);
    restored=dk_mac_restore_frame((DkMacRect){0,0,1470,923},(DkMacRect){0,0,1470,956});
    assert(restored.x==0&&restored.y==0&&restored.width==1470&&restored.height==923); /* Mac safe area */
    restored=dk_mac_restore_frame((DkMacRect){-1900,20,800,600},(DkMacRect){-1920,0,1920,1080});
    assert(restored.x==-1900&&restored.y==20&&restored.width==800&&restored.height==600);
    restored=dk_mac_restore_frame((DkMacRect){NAN,INFINITY,NAN,INFINITY},screen);
    assert(restored.x==0&&restored.y==0&&restored.width==1440&&restored.height==900);

    puts("PASS: WASD/mouse mappings; 500 focus cycles x32 states; Esc->minimize->restore; stop cancels resume; logical-point window restore, Retina sizes and negative-screen origins");
    return 0;
}
