/* Exercise the production resampler, not a second implementation of it. */
#include "input-state.h"
#include <stdlib.h>
#define CHECK(value) do { if(!(value)){ fprintf(stderr,"CHECK failed at line %d: %s\n",__LINE__,#value);exit(1); } } while(0)
#include <stdio.h>

static double steady(double report_hz,double phase,double smoothing) {
    DkMacInput s;dk_mac_init(&s,.01,false,1.);
    CHECK(dk_mac_mouse_options(&s,smoothing,0,1));
    double next=1.+phase,sum=0,squares=0;unsigned count=0;
    uint32_t buttons;int16_t axes[6];
    for(unsigned n=1;n<=500;n++){
        double now=1.+n*.004;
        while(next<=now){dk_mac_motion(&s,400./report_hz,0,next);next+=1./report_hz;}
        dk_mac_sample(&s,now,&buttons,axes);
        if(n>60){double value=axes[2]/32767.;sum+=value;squares+=value*value;count++;}
    }
    double mean=sum/count,variation=sqrt(fmax(0,squares/count-mean*mean))/mean;
    CHECK(fabs(mean-400*.01/60)<.001);
    return variation;
}
int main(void) {
    for(unsigned hz=125;hz<=1000;hz*=2){
        for(unsigned phase=0;phase<8;phase++){
            double variation=steady(hz,.0003+phase*.0005,8);
            CHECK(variation<.035);
        }
    }
    double old=steady(125,.001,0),filtered=steady(125,.001,8);
    CHECK(old>.9&&filtered<.035);
    printf("PASS: 125/250/500/1000 Hz x8 phases, steady velocity; 125 Hz CV %.3f -> %.3f at 250 Hz output\n",old,filtered);
    DkMacInput s;uint32_t buttons;int16_t axes[6];
    dk_mac_init(&s,.01,false,1.);CHECK(dk_mac_mouse_options(&s,8,0,1));
    dk_mac_motion(&s,6,0,1.001);
    double distance=0;
    for(unsigned n=1;n<=10;n++){
        dk_mac_sample(&s,1.+n*.004,&buttons,axes);distance+=axes[2]/32767.*60*.004/.01;
        if(n>=4)CHECK(axes[2]==0); /* finite window; no exponential camera tail */
    }
    CHECK(fabs(distance-6)<.002);
    dk_mac_motion(&s,40,0,1.045);dk_mac_sample(&s,1.048,&buttons,axes);CHECK(axes[2]>0);
    dk_mac_motion(&s,-1,0,1.049);dk_mac_sample(&s,1.052,&buttons,axes);CHECK(axes[2]<0);
    dk_mac_reset(&s,2.);dk_mac_sample(&s,2.004,&buttons,axes);CHECK(axes[2]==0);
    CHECK(dk_mac_mouse_options(&s,0,.12,2));
    dk_mac_motion(&s,.001,0,2.005);dk_mac_sample(&s,2.008,&buttons,axes);
    CHECK(axes[2]>32767*.12&&axes[3]==0);
    dk_mac_sample(&s,2.012,&buttons,axes);CHECK(axes[2]==0); /* anti-deadzone never drifts */
    dk_mac_motion(&s,100000,100000,2.013);dk_mac_sample(&s,2.016,&buttons,axes);
    CHECK(hypot(axes[2],axes[3])<=32768);
    double original=s.deadzone;CHECK(!dk_mac_mouse_options(&s,17,0,1));CHECK(s.deadzone==original);
    CHECK(!dk_mac_mouse_options(&s,NAN,0,1));CHECK(!dk_mac_mouse_options(&s,8,.36,1));CHECK(!dk_mac_mouse_options(&s,8,0,0));
    puts("PASS: conserved displacement, bounded stop, immediate reversal, neutral on reset, radial curve/deadzone and invalid options");
}
