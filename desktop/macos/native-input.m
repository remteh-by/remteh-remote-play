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
#include "input-state.h"

extern int deckivo_ensure_controller(void);
extern void deckivo_set_controller(uint32_t,const int16_t[6]);
extern void deckivo_pump_controller(void);
extern void deckivo_request_quit(void);
extern void deckivo_notify_closing(void);
static BOOL enabled,capturing,relative_mouse,ignore_initial_motion,previous_mouse_events;
static DkMacInput input;
static NSWindow *capture_window,*stream_window;
static NSPanel *capture_badge;
static id local_monitor,resign_observer,window_observer,termination_observer,close_observer;
static dispatch_source_t input_timer;
static double seconds(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec/1e9;}

void deckivo_macos_release(void *unused) {
    (void)unused;
    if(capturing)fprintf(stderr,"[Deckivo] WASD mouse capture released\n");
    if(relative_mouse){CGAssociateMouseAndMouseCursorPosition(true);relative_mouse=NO;}
    if(capturing)[NSCursor unhide];
    if(capture_window)capture_window.acceptsMouseMovedEvents=previous_mouse_events;
    capturing=NO;ignore_initial_motion=NO;dk_mac_reset(&input,seconds());
    if(capture_badge){
        [capture_badge.parentWindow removeChildWindow:capture_badge];
        [capture_badge orderOut:nil];[capture_badge close];capture_badge=nil;
    }
    capture_window=nil;
    const int16_t axes[6]={0,0,0,0,INT16_MIN,INT16_MIN};deckivo_set_controller(0,axes);deckivo_pump_controller();
}
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
void deckivo_macos_activate(void *unused) {
    (void)unused;
    [NSApp activateIgnoringOtherApps:YES];
    NSWindow *window=NSApp.keyWindow;
    if([window isKindOfClass:NSPanel.class])window=nil;
    if(!window)for(NSWindow *candidate in NSApp.windows)if(candidate.visible&&!candidate.miniaturized&&![candidate isKindOfClass:NSPanel.class]){window=candidate;break;}
    if(window)stream_window=window;
    [window makeKeyAndOrderFront:nil];
}
#pragma clang diagnostic pop
static void center_pointer(void) {
    NSRect frame=capture_window.frame;
    CGFloat top=NSMaxY(NSScreen.screens.firstObject.frame);
    CGWarpMouseCursorPosition(CGPointMake(NSMidX(frame),top-NSMidY(frame)));
}
static void show_capture_badge(NSString *text) {
    /* Qt owns the streaming contentView and its OpenGL backing layer. Adding
     * AppKit subviews there can replace/obscure the drawable while audio and
     * decoding continue. Keep our transient hint in its own non-key window. */
    NSRect parent_frame=capture_window.frame;
    CGFloat width=fmin(470,fmax(100,NSWidth(parent_frame)-36));
    capture_badge=[[NSPanel alloc] initWithContentRect:NSMakeRect(NSMinX(parent_frame)+18,NSMaxY(parent_frame)-76,width,28)
        styleMask:NSWindowStyleMaskBorderless|NSWindowStyleMaskNonactivatingPanel
        backing:NSBackingStoreBuffered defer:NO];
    capture_badge.releasedWhenClosed=NO;capture_badge.opaque=NO;
    capture_badge.backgroundColor=NSColor.clearColor;capture_badge.hasShadow=NO;
    capture_badge.ignoresMouseEvents=YES;capture_badge.hidesOnDeactivate=NO;
    capture_badge.collectionBehavior=NSWindowCollectionBehaviorFullScreenAuxiliary|NSWindowCollectionBehaviorTransient|NSWindowCollectionBehaviorIgnoresCycle;
    NSTextField *label=[NSTextField labelWithString:text];
    label.frame=NSMakeRect(0,0,width,28);label.autoresizingMask=NSViewWidthSizable|NSViewHeightSizable;
    label.font=[NSFont systemFontOfSize:12 weight:NSFontWeightMedium];
    label.textColor=[NSColor colorWithCalibratedRed:.855 green:.976 blue:.459 alpha:1];
    label.drawsBackground=YES;label.backgroundColor=[NSColor colorWithCalibratedRed:.063 green:.071 blue:.086 alpha:.9];
    label.alignment=NSTextAlignmentCenter;
    [capture_badge.contentView addSubview:label];
    [capture_window addChildWindow:capture_badge ordered:NSWindowAbove];
    [capture_badge orderFront:nil];
    NSPanel *shown=capture_badge;
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,3*NSEC_PER_SEC),dispatch_get_main_queue(),^{
        if(capture_badge==shown){
            [shown.parentWindow removeChildWindow:shown];[shown orderOut:nil];[shown close];capture_badge=nil;
        }
    });
}
static void begin_capture(void) {
    if(!enabled||!NSApp.active||NSApp.modalWindow||!deckivo_ensure_controller())return;
    deckivo_macos_release(NULL);
    capture_window=NSApp.keyWindow;
    if(!capture_window)return;
    previous_mouse_events=capture_window.acceptsMouseMovedEvents;
    capture_window.acceptsMouseMovedEvents=YES;
    center_pointer();
    if(CGAssociateMouseAndMouseCursorPosition(false)!=kCGErrorSuccess){
        capture_window.acceptsMouseMovedEvents=previous_mouse_events;capture_window=nil;
        fprintf(stderr,"[Deckivo] relative mouse capture unavailable\n");return;
    }
    relative_mouse=YES;capturing=YES;ignore_initial_motion=YES;[NSCursor hide];
    fprintf(stderr,"[Deckivo] WASD mouse capture active (relative)\n");
    NSString *language=NSProcessInfo.processInfo.environment[@"DECKIVO_INPUT_LANG"];
    BOOL ru=[language hasPrefix:@"ru"]||([language isEqualToString:@"auto"]&&[NSLocale.preferredLanguages.firstObject hasPrefix:@"ru"]);
    show_capture_badge(ru?@"DECKIVO · Клавиатура + мышь · Esc — отпустить · F8 — захват":@"DECKIVO · Keyboard + mouse · Esc releases · F8 captures");
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
static void input_tick(void *unused) {
    (void)unused;if(!NSApp||!deckivo_ensure_controller())return;
    if(capturing&&(!NSApp.active||!capture_window.keyWindow||NSApp.modalWindow))deckivo_macos_release(NULL);
    int16_t axes[6]={0,0,0,0,INT16_MIN,INT16_MIN};uint32_t buttons=0;
    if(capturing)dk_mac_sample(&input,seconds(),&buttons,axes);
    deckivo_set_controller(buttons,axes);deckivo_pump_controller();
}
void deckivo_macos_input_start(void) {
    /* Observe the owned streaming window even in controller-only mode. A
     * non-key hint panel closing must never end the Remote Play session. */
    dispatch_async(dispatch_get_main_queue(),^{
        close_observer=[NSNotificationCenter.defaultCenter addObserverForName:NSWindowWillCloseNotification object:nil queue:nil usingBlock:^(NSNotification *note){
            NSWindow *window=note.object;
            if(!stream_window||window!=stream_window||[window isKindOfClass:NSPanel.class])return;
            fprintf(stderr,"[Deckivo] user-ended stream (native window closed)\n");
            deckivo_notify_closing();
        }];
    });
    const char *flag=getenv("DECKIVO_KBM");enabled=flag&&!strcmp(flag,"1");if(!enabled)return;
    const char *value=getenv("DECKIVO_MOUSE_SENSITIVITY"),*inverted=getenv("DECKIVO_MOUSE_INVERT_Y");
    dk_mac_init(&input,value?strtod(value,NULL):.025,inverted&&!strcmp(inverted,"1"),seconds());
    bool keys_valid=dk_mac_bindings(&input,getenv("DECKIVO_KEY_BINDINGS"),false);
    bool mouse_valid=dk_mac_bindings(&input,getenv("DECKIVO_MOUSE_BINDINGS"),true);
    if(!keys_valid||!mouse_valid)
        fprintf(stderr,"[Deckivo] invalid input mapping; retained safe defaults for that device\n");
    dispatch_async(dispatch_get_main_queue(),^{
        NSEventMask mask=NSEventMaskKeyDown|NSEventMaskKeyUp|NSEventMaskFlagsChanged|NSEventMaskMouseMoved|NSEventMaskLeftMouseDragged|NSEventMaskRightMouseDragged|NSEventMaskOtherMouseDragged|NSEventMaskLeftMouseDown|NSEventMaskLeftMouseUp|NSEventMaskRightMouseDown|NSEventMaskRightMouseUp|NSEventMaskOtherMouseDown|NSEventMaskOtherMouseUp;
        local_monitor=[NSEvent addLocalMonitorForEventsMatchingMask:mask handler:^NSEvent *(NSEvent *event){
            /* Route Cmd+Q through the same orderly session close as the dashboard. */
            if(event.type==NSEventTypeKeyDown&&event.keyCode==12&&(event.modifierFlags&NSEventModifierFlagCommand)&&!event.ARepeat){deckivo_macos_release(NULL);deckivo_request_quit();return nil;}
            if(event.type==NSEventTypeKeyDown&&event.keyCode==100&&!event.ARepeat){if(capturing)deckivo_macos_release(NULL);else deckivo_macos_capture(NULL);return nil;}
            if(!capturing)return event;
            if(!NSApp.active||NSApp.modalWindow){deckivo_macos_release(NULL);return event;}
            if(event.window&&event.window!=capture_window){deckivo_macos_release(NULL);return event;}
            if(event.type==NSEventTypeKeyDown&&event.keyCode==53){deckivo_macos_release(NULL);return nil;}
            /* Process key releases even when Cmd is held; shortcuts cannot leave W stuck. */
            if(event.type==NSEventTypeKeyUp)dk_mac_key(&input,event.keyCode,false);
            if(event.modifierFlags&NSEventModifierFlagCommand){dk_mac_reset(&input,seconds());return event;}
            if(event.type==NSEventTypeFlagsChanged){dk_mac_key(&input,56,(event.modifierFlags&NSEventModifierFlagShift)!=0);dk_mac_key(&input,59,(event.modifierFlags&NSEventModifierFlagControl)!=0);dk_mac_key(&input,58,(event.modifierFlags&NSEventModifierFlagOption)!=0);return nil;}
            if(event.type==NSEventTypeKeyDown||event.type==NSEventTypeKeyUp){
                dk_mac_key(&input,event.keyCode,event.type==NSEventTypeKeyDown);
                /* F11 remains the engine's fullscreen shortcut. Other keys belong to this mode. */
                return event.keyCode==103?event:nil;
            }
            switch(event.type){
                case NSEventTypeMouseMoved:case NSEventTypeLeftMouseDragged:case NSEventTypeRightMouseDragged:case NSEventTypeOtherMouseDragged:
                    if(ignore_initial_motion){ignore_initial_motion=NO;return nil;}
                    dk_mac_motion(&input,event.deltaX,event.deltaY,seconds());return nil;
                case NSEventTypeLeftMouseDown:input.mouse[0]=true;return nil;case NSEventTypeLeftMouseUp:input.mouse[0]=false;return nil;
                case NSEventTypeRightMouseDown:input.mouse[1]=true;return nil;case NSEventTypeRightMouseUp:input.mouse[1]=false;return nil;
                case NSEventTypeOtherMouseDown:if(event.buttonNumber>=2&&event.buttonNumber<=4){input.mouse[event.buttonNumber]=true;return nil;}return event;
                case NSEventTypeOtherMouseUp:if(event.buttonNumber>=2&&event.buttonNumber<=4){input.mouse[event.buttonNumber]=false;return nil;}return event;
                default:return event;
            }
        }];
        resign_observer=[NSNotificationCenter.defaultCenter addObserverForName:NSApplicationDidResignActiveNotification object:NSApp queue:nil usingBlock:^(NSNotification *note){(void)note;deckivo_macos_release(NULL);}];
        window_observer=[NSNotificationCenter.defaultCenter addObserverForName:NSWindowDidResignKeyNotification object:nil queue:nil usingBlock:^(NSNotification *note){if(note.object==capture_window)deckivo_macos_release(NULL);}];
        termination_observer=[NSNotificationCenter.defaultCenter addObserverForName:NSApplicationWillTerminateNotification object:NSApp queue:nil usingBlock:^(NSNotification *note){(void)note;deckivo_macos_release(NULL);}];
        input_timer=dispatch_source_create(DISPATCH_SOURCE_TYPE_TIMER,0,0,dispatch_get_main_queue());
        dispatch_source_set_timer(input_timer,DISPATCH_TIME_NOW,16*NSEC_PER_MSEC,2*NSEC_PER_MSEC);dispatch_source_set_event_handler_f(input_timer,input_tick);dispatch_resume(input_timer);
    });
}
