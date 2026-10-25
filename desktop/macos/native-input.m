/* SPDX-License-Identifier: GPL-3.0-or-later
 * Focused input in the owned streaming window. No global event monitor or tap.
 */
#import <Cocoa/Cocoa.h>
#import <ApplicationServices/ApplicationServices.h>
#include <math.h>
#include <stdint.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

extern int deckivo_ensure_controller(void);
extern void deckivo_set_controller(uint32_t,const int16_t[6]);
extern void deckivo_pump_controller(void);
extern void deckivo_request_quit(void);
static BOOL enabled,capturing,keys[256],left_mouse,right_mouse,middle_mouse,control_key,option_key;
static double sensitivity=.025,mouse_x,mouse_y,moved_at;
static BOOL invert_y;
static NSWindow *capture_window;
static NSTextField *badge;
static id local_monitor,resign_observer,window_observer;
static dispatch_source_t input_timer;
static double seconds(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec/1e9;}

void deckivo_macos_release(void *unused) {
    (void)unused;
    if(capturing)[NSCursor unhide];
    capturing=NO;memset(keys,0,sizeof(keys));left_mouse=right_mouse=middle_mouse=control_key=option_key=NO;mouse_x=mouse_y=0;moved_at=0;
    [badge removeFromSuperview];badge=nil;capture_window=nil;
    const int16_t axes[6]={0,0,0,0,INT16_MIN,INT16_MIN};deckivo_set_controller(0,axes);deckivo_pump_controller();
}
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
void deckivo_macos_activate(void *unused) {
    (void)unused;
    [NSApp activateIgnoringOtherApps:YES];
    NSWindow *window=NSApp.keyWindow;
    if(!window)for(NSWindow *candidate in NSApp.windows)if(candidate.visible&&!candidate.miniaturized&&![candidate isKindOfClass:NSPanel.class]){window=candidate;break;}
    [window makeKeyAndOrderFront:nil];
}
#pragma clang diagnostic pop
static void center_pointer(void) {
    NSRect frame=capture_window.frame;
    CGFloat top=NSMaxY(NSScreen.screens.firstObject.frame);
    CGWarpMouseCursorPosition(CGPointMake(NSMidX(frame),top-NSMidY(frame)));
}
static void begin_capture(void) {
    if(!enabled||!NSApp.active||NSApp.modalWindow||!deckivo_ensure_controller())return;
    deckivo_macos_release(NULL);
    capture_window=NSApp.keyWindow;
    if(!capture_window)return;
    capturing=YES;[NSCursor hide];center_pointer();
    NSString *language=NSProcessInfo.processInfo.environment[@"DECKIVO_INPUT_LANG"];
    BOOL ru=[language hasPrefix:@"ru"]||([language isEqualToString:@"auto"]&&[NSLocale.preferredLanguages.firstObject hasPrefix:@"ru"]);
    badge=[NSTextField labelWithString:ru?@"DECKIVO · WASD + мышь · Esc — отпустить · F8 — захват":@"DECKIVO · WASD + mouse · Esc releases · F8 captures"];
    badge.font=[NSFont systemFontOfSize:12 weight:NSFontWeightMedium];badge.textColor=[NSColor colorWithCalibratedRed:.855 green:.976 blue:.459 alpha:1];badge.drawsBackground=YES;badge.backgroundColor=[NSColor colorWithCalibratedRed:.063 green:.071 blue:.086 alpha:.9];badge.alignment=NSTextAlignmentCenter;
    NSView *view=capture_window.contentView;badge.frame=NSMakeRect(18,NSHeight(view.bounds)-48,470,28);badge.autoresizingMask=NSViewMinYMargin|NSViewMaxXMargin;[view addSubview:badge];
}
void deckivo_macos_close(void *unused) {
    (void)unused;
    NSWindow *window=NSApp.keyWindow;
    if(!window)for(NSWindow *candidate in NSApp.windows)if(candidate.visible&&![candidate isKindOfClass:NSPanel.class]){window=candidate;break;}
    if(window)[window performClose:nil];
}
void deckivo_macos_capture(void *unused) {
    (void)unused;if(!enabled)return;
    deckivo_macos_activate(NULL);
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,150*NSEC_PER_MSEC),dispatch_get_main_queue(),^{begin_capture();});
}
static int button_for_key(unsigned short key) {
    switch(key){case 49:return 0;case 8:return 1;case 15:return 2;case 3:return 3;case 18:return 4;case 120:return 5;case 36:return 6;case 12:return 9;case 14:return 10;case 126:return 11;case 125:return 12;case 123:return 13;case 124:return 14;case 48:return 20;default:return -1;}
}
static BOOL movement_key(unsigned short key){return key==13||key==1||key==0||key==2;}
static void input_tick(void *unused) {
    (void)unused;if(!NSApp||!deckivo_ensure_controller())return;
    int16_t axes[6]={0,0,0,0,INT16_MIN,INT16_MIN};uint32_t buttons=0;
    if(capturing&&NSApp.active&&!NSApp.modalWindow){
        double x=(keys[2]?1:0)-(keys[0]?1:0),y=(keys[1]?1:0)-(keys[13]?1:0),scale=fmax(1.,hypot(x,y));
        axes[0]=(int16_t)lrint(x/scale*32767);axes[1]=(int16_t)lrint(y/scale*32767);
        if(moved_at&&seconds()-moved_at<.08){axes[2]=(int16_t)lrint(mouse_x*32767);axes[3]=(int16_t)lrint(mouse_y*32767);}
        axes[4]=right_mouse?INT16_MAX:INT16_MIN;axes[5]=left_mouse?INT16_MAX:INT16_MIN;
        for(unsigned short i=0;i<256;i++)if(keys[i]){int b=button_for_key(i);if(b>=0)buttons|=1u<<b;}
        if(control_key)buttons|=1u<<7;if(option_key||middle_mouse)buttons|=1u<<8;
    }
    deckivo_set_controller(buttons,axes);deckivo_pump_controller();
}
void deckivo_macos_input_start(void) {
    const char *flag=getenv("DECKIVO_KBM");enabled=flag&&!strcmp(flag,"1");if(!enabled)return;
    const char *value=getenv("DECKIVO_MOUSE_SENSITIVITY");double requested=value?strtod(value,NULL):.025;
    if(isfinite(requested))sensitivity=fmax(.001,fmin(.2,requested));
    const char *inverted=getenv("DECKIVO_MOUSE_INVERT_Y");invert_y=inverted&&!strcmp(inverted,"1");
    dispatch_async(dispatch_get_main_queue(),^{
        NSEventMask mask=NSEventMaskKeyDown|NSEventMaskKeyUp|NSEventMaskFlagsChanged|NSEventMaskMouseMoved|NSEventMaskLeftMouseDragged|NSEventMaskRightMouseDragged|NSEventMaskOtherMouseDragged|NSEventMaskLeftMouseDown|NSEventMaskLeftMouseUp|NSEventMaskRightMouseDown|NSEventMaskRightMouseUp|NSEventMaskOtherMouseDown|NSEventMaskOtherMouseUp;
        local_monitor=[NSEvent addLocalMonitorForEventsMatchingMask:mask handler:^NSEvent *(NSEvent *event){
            if(event.type==NSEventTypeKeyDown&&event.keyCode==100&&!event.ARepeat){if(capturing)deckivo_macos_release(NULL);else deckivo_macos_capture(NULL);return nil;}
            if(!capturing||!NSApp.active||NSApp.modalWindow)return event;
            if(event.window&&event.window!=capture_window){deckivo_macos_release(NULL);return event;}
            if(event.type==NSEventTypeKeyDown&&event.keyCode==53){deckivo_macos_release(NULL);return nil;}
            if(event.modifierFlags&NSEventModifierFlagCommand)return event;
            if(event.type==NSEventTypeKeyDown&&event.keyCode==12&&(event.modifierFlags&NSEventModifierFlagControl)){deckivo_macos_release(NULL);deckivo_request_quit();return nil;}
            if(event.type==NSEventTypeFlagsChanged){control_key=(event.modifierFlags&NSEventModifierFlagControl)!=0;option_key=(event.modifierFlags&NSEventModifierFlagOption)!=0;return event;}
            if(event.type==NSEventTypeKeyDown||event.type==NSEventTypeKeyUp){
                unsigned short key=event.keyCode;
                if(key<256&&(movement_key(key)||button_for_key(key)>=0)){keys[key]=event.type==NSEventTypeKeyDown;return nil;}
                return event;
            }
            switch(event.type){
                case NSEventTypeMouseMoved:case NSEventTypeLeftMouseDragged:case NSEventTypeRightMouseDragged:case NSEventTypeOtherMouseDragged:
                    if(isfinite(event.deltaX)&&isfinite(event.deltaY)&&(event.deltaX||event.deltaY)){mouse_x=fmax(-1.,fmin(1.,event.deltaX*sensitivity));mouse_y=fmax(-1.,fmin(1.,event.deltaY*sensitivity*(invert_y?-1:1)));moved_at=seconds();center_pointer();}return nil;
                case NSEventTypeLeftMouseDown:left_mouse=YES;return nil;case NSEventTypeLeftMouseUp:left_mouse=NO;return nil;
                case NSEventTypeRightMouseDown:right_mouse=YES;return nil;case NSEventTypeRightMouseUp:right_mouse=NO;return nil;
                case NSEventTypeOtherMouseDown:if(event.buttonNumber==2){middle_mouse=YES;return nil;}return event;
                case NSEventTypeOtherMouseUp:if(event.buttonNumber==2){middle_mouse=NO;return nil;}return event;
                default:return event;
            }
        }];
        resign_observer=[NSNotificationCenter.defaultCenter addObserverForName:NSApplicationDidResignActiveNotification object:NSApp queue:nil usingBlock:^(NSNotification *note){(void)note;deckivo_macos_release(NULL);}];
        window_observer=[NSNotificationCenter.defaultCenter addObserverForName:NSWindowDidResignKeyNotification object:nil queue:nil usingBlock:^(NSNotification *note){if(note.object==capture_window)deckivo_macos_release(NULL);}];
        input_timer=dispatch_source_create(DISPATCH_SOURCE_TYPE_TIMER,0,0,dispatch_get_main_queue());
        dispatch_source_set_timer(input_timer,DISPATCH_TIME_NOW,16*NSEC_PER_MSEC,2*NSEC_PER_MSEC);dispatch_source_set_event_handler_f(input_timer,input_tick);dispatch_resume(input_timer);
    });
}
