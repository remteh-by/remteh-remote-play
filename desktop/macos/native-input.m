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
#include <unistd.h>
#include "input-state.h"

extern int deckivo_ensure_controller(void);
extern void deckivo_set_controller(uint32_t,const int16_t[6]);
extern void deckivo_pump_controller(void);
extern void deckivo_request_quit(void);
extern void deckivo_notify_closing(void);
extern void deckivo_set_audio_hidden(int);
extern unsigned deckivo_controller_status(void);
static BOOL enabled,relative_mouse,ignore_initial_motion,previous_mouse_events;
static DkMacCapture capture_state;
static DkMacInput input;
static NSWindow *capture_window,*stream_window;
static NSPanel *capture_badge;
static id local_monitor,resign_observer,window_observer,termination_observer,close_observer,mini_observer,restore_observer;
static dispatch_source_t input_timer;
static const char *capture_reason="not_started";
static unsigned long key_events,accepted_keys,mouse_events,accepted_mouse,action_samples;
static NSRect remembered_frame;
static BOOL have_frame,restore_pending,remembered_fullscreen,audio_hidden;
static NSUInteger geometry_generation;
static double seconds(void){struct timespec t;clock_gettime(CLOCK_MONOTONIC,&t);return t.tv_sec+t.tv_nsec/1e9;}

static void end_capture(BOOL temporary) {
    BOOL was_active=dk_mac_capture_end(&capture_state,&input,seconds(),temporary);
    capture_reason=temporary?"focus_lost":"dashboard_or_stop";
    if(was_active)fprintf(stderr,temporary?"[Deckivo] WASD mouse capture suspended (focus lost)\n":"[Deckivo] WASD mouse capture released\n");
    if(relative_mouse){CGAssociateMouseAndMouseCursorPosition(true);relative_mouse=NO;}
    if(was_active)[NSCursor unhide];
    if(capture_window)capture_window.acceptsMouseMovedEvents=previous_mouse_events;
    ignore_initial_motion=NO;
    if(capture_badge){
        [capture_badge.parentWindow removeChildWindow:capture_badge];
        [capture_badge orderOut:nil];[capture_badge close];capture_badge=nil;
    }
    capture_window=nil;
    const int16_t axes[6]={0,0,0,0,INT16_MIN,INT16_MIN};deckivo_set_controller(0,axes);deckivo_pump_controller();
}
void deckivo_macos_release(void *unused) {
    (void)unused;end_capture(NO);
}
static void user_ungrab(const char *reason) {
    end_capture(NO);dk_mac_capture_ungrab(&capture_state);capture_reason=reason;
}
static BOOL video_window_candidate(NSWindow *window) {
    if(!window||[window isKindOfClass:NSPanel.class]||!window.visible||window.miniaturized||window.level!=NSNormalWindowLevel)return NO;
    if(NSWidth(window.frame)<200||NSHeight(window.frame)<100)return NO;
    return !stream_window||window==stream_window||window.class==stream_window.class;
}
static void refresh_stream_window(void) {
    if(NSApp.modalWindow)return;
    NSWindow *candidate=NSApp.keyWindow;
    if(!video_window_candidate(candidate))return;
    if(candidate!=stream_window){
        if(capture_state.active)end_capture(YES);
        stream_window=candidate;
        fprintf(stderr,"[Deckivo] owned stream window selected\n");
    }
}
static BOOL stream_has_focus(void) {
    DkMacFocus focus={NSApp.active,stream_window.keyWindow,stream_window.visible,stream_window.miniaturized,NSApp.modalWindow!=nil};
    return dk_mac_capture_eligible(enabled,focus);
}
#pragma clang diagnostic push
#pragma clang diagnostic ignored "-Wdeprecated-declarations"
void deckivo_macos_activate(void *unused) {
    (void)unused;
    [NSApp activateIgnoringOtherApps:YES];
    refresh_stream_window();NSWindow *window=stream_window;
    if(!window)for(NSWindow *candidate in NSApp.windows)if(video_window_candidate(candidate)){window=candidate;stream_window=window;break;}
    if(window.miniaturized)[window deminiaturize:nil];
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
    if(!stream_has_focus()||!deckivo_ensure_controller())return;
    BOOL resumed=capture_state.resume_on_focus;
    deckivo_macos_release(NULL);
    capture_window=stream_window;
    if(!capture_window)return;
    previous_mouse_events=capture_window.acceptsMouseMovedEvents;
    capture_window.acceptsMouseMovedEvents=YES;
    center_pointer();
    if(CGAssociateMouseAndMouseCursorPosition(false)!=kCGErrorSuccess){
        capture_window.acceptsMouseMovedEvents=previous_mouse_events;capture_window=nil;
        fprintf(stderr,"[Deckivo] relative mouse capture unavailable\n");return;
    }
    relative_mouse=YES;dk_mac_capture_begin(&capture_state);ignore_initial_motion=YES;[NSCursor hide];
    capture_reason=resumed?"focus_return":"capture_requested";
    fprintf(stderr,resumed?"[Deckivo] WASD mouse capture restored after focus return\n":"[Deckivo] WASD mouse capture active (relative)\n");
    NSString *language=NSProcessInfo.processInfo.environment[@"DECKIVO_INPUT_LANG"];
    BOOL ru=[language hasPrefix:@"ru"]||([language isEqualToString:@"auto"]&&[NSLocale.preferredLanguages.firstObject hasPrefix:@"ru"]);
    show_capture_badge(ru?@"DECKIVO · Клавиатура + мышь · Esc — отпустить · F8 — захват":@"DECKIVO · Keyboard + mouse · Esc releases · F8 captures");
}
void deckivo_macos_close(void *unused) {
    (void)unused;
    NSWindow *window=stream_window;
    if(!window)for(NSWindow *candidate in NSApp.windows)if(video_window_candidate(candidate)){window=candidate;break;}
    if(window)[window performClose:nil];
}
void deckivo_macos_capture(void *unused) {
    (void)unused;if(!enabled)return;
    deckivo_macos_activate(NULL);
    dispatch_after(dispatch_time(DISPATCH_TIME_NOW,150*NSEC_PER_MSEC),dispatch_get_main_queue(),^{begin_capture();});
}
static void remember_window_frame(void) {
    if(!stream_window||stream_window.miniaturized||!stream_window.visible||restore_pending)return;
    NSRect frame=stream_window.frame;NSScreen *screen=stream_window.screen;
    if(NSWidth(frame)<=0||NSHeight(frame)<=0||!screen)return;
    remembered_frame=frame;have_frame=YES;
    remembered_fullscreen=(stream_window.styleMask&NSWindowStyleMaskFullScreen)!=0||
        (fabs(NSWidth(frame)-NSWidth(screen.frame))<2&&fabs(NSHeight(frame)-NSHeight(screen.frame))<2);
}
static void restore_window_frame(NSWindow *window,NSUInteger generation) {
    if(generation!=geometry_generation||window!=stream_window||window.miniaturized)return;
    NSScreen *screen=window.screen?:NSScreen.screens.firstObject;
    if(have_frame&&screen){
        NSRect bounds=remembered_fullscreen?screen.frame:screen.visibleFrame;
        DkMacRect saved={remembered_frame.origin.x,remembered_frame.origin.y,remembered_frame.size.width,remembered_frame.size.height};
        DkMacRect limit={bounds.origin.x,bounds.origin.y,bounds.size.width,bounds.size.height};
        DkMacRect restored=dk_mac_restore_frame(saved,limit,remembered_fullscreen);
        NSRect frame=NSMakeRect(restored.x,restored.y,restored.width,restored.height);
        if(!NSEqualRects(window.frame,frame))[window setFrame:frame display:YES animate:NO];
        fprintf(stderr,"[Deckivo] restored stream window frame in logical points\n");
    }
    restore_pending=NO;geometry_generation++;
    if(enabled){capture_state.resume_on_focus=YES;capture_state.rearm_on_focus_loss=YES;}
}
static void publish_input_status(void) {
    static double last_write;double now=seconds();if(now-last_write<1)return;last_write=now;
    const char *base=getenv("DECKIVO_METRICS");if(!base||!base[0])return;
    NSString *path=[[NSString stringWithUTF8String:base] stringByAppendingString:@".input"];
    if(!path)return;
    unsigned controller=deckivo_controller_status();
    NSRect frame=stream_window?stream_window.frame:NSZeroRect;NSScreen *screen=stream_window.screen;
    NSRect screen_frame=screen?screen.frame:NSZeroRect;
    NSDictionary *status=@{@"schema":@1,@"pid":@(getpid()),@"active":@(capture_state.active),
        @"resume_pending":@(capture_state.resume_on_focus),@"rearm_on_focus_loss":@(capture_state.rearm_on_focus_loss),
        @"reason":[NSString stringWithUTF8String:capture_reason],@"enabled":@(enabled),
        @"app_active":@(NSApp.active),@"app_hidden":@(NSApp.hidden),@"window_key":@(stream_window.keyWindow),
        @"window_visible":@(stream_window.visible),@"window_minimized":@(stream_window.miniaturized),
        @"modal":@(NSApp.modalWindow!=nil),@"target_window":@(stream_window.windowNumber),@"key_window":@(NSApp.keyWindow.windowNumber),
        @"frame_width_points":@(NSWidth(frame)),@"frame_height_points":@(NSHeight(frame)),
        @"backing_scale":@(stream_window.backingScaleFactor),@"screen_width_points":@(NSWidth(screen_frame)),@"screen_height_points":@(NSHeight(screen_frame)),
        @"audio_hidden":@(audio_hidden),@"keys_seen":@(key_events),@"keys_accepted":@(accepted_keys),
        @"mouse_seen":@(mouse_events),@"mouse_accepted":@(accepted_mouse),@"samples_with_actions":@(action_samples),
        @"controller_ready":@((controller&1)!=0),@"controller_attached":@((controller&2)!=0),@"controller_open":@((controller&4)!=0)};
    NSData *data=[NSJSONSerialization dataWithJSONObject:status options:0 error:NULL];
    if(data&&[data writeToFile:path options:NSDataWritingAtomic error:NULL])
        [NSFileManager.defaultManager setAttributes:@{NSFilePosixPermissions:@0600} ofItemAtPath:path error:NULL];
}
static void input_tick(void *unused) {
    (void)unused;if(!NSApp)return;
    refresh_stream_window();remember_window_frame();
    BOOL hidden=NSApp.hidden||!NSApp.active||stream_window.miniaturized;
    if(hidden!=audio_hidden){
        audio_hidden=hidden;deckivo_set_audio_hidden(hidden);
        fprintf(stderr,hidden?"[Deckivo] audio muted while stream is minimized/hidden\n":"[Deckivo] audio restored\n");
    }
    publish_input_status();
    if(!enabled)return;
    BOOL focused=stream_has_focus();
    if(!focused&&(capture_state.active||capture_state.rearm_on_focus_loss)&&!capture_state.resume_on_focus)end_capture(YES);
    if(!deckivo_ensure_controller())return;
    if(dk_mac_capture_wants_resume(&capture_state,focused))begin_capture();
    int16_t axes[6]={0,0,0,0,INT16_MIN,INT16_MIN};uint32_t buttons=0;
    if(capture_state.active)dk_mac_sample(&input,seconds(),&buttons,axes);
    if(buttons||axes[0]||axes[1]||axes[2]||axes[3]||axes[4]!=INT16_MIN||axes[5]!=INT16_MIN)action_samples++;
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
        mini_observer=[NSNotificationCenter.defaultCenter addObserverForName:NSWindowWillMiniaturizeNotification object:nil queue:nil usingBlock:^(NSNotification *note){
            if(note.object!=stream_window)return;
            remember_window_frame();restore_pending=YES;geometry_generation++;
            end_capture(YES);capture_reason="minimized";
            audio_hidden=YES;deckivo_set_audio_hidden(1);
            fprintf(stderr,"[Deckivo] stream minimized; audio muted and frame saved\n");
        }];
        restore_observer=[NSNotificationCenter.defaultCenter addObserverForName:NSWindowDidDeminiaturizeNotification object:nil queue:nil usingBlock:^(NSNotification *note){
            if(note.object!=stream_window)return;
            NSWindow *window=note.object;NSUInteger generation=geometry_generation;
            dispatch_after(dispatch_time(DISPATCH_TIME_NOW,200*NSEC_PER_MSEC),dispatch_get_main_queue(),^{restore_window_frame(window,generation);});
        }];
        input_timer=dispatch_source_create(DISPATCH_SOURCE_TYPE_TIMER,0,0,dispatch_get_main_queue());
        dispatch_source_set_timer(input_timer,DISPATCH_TIME_NOW,16*NSEC_PER_MSEC,2*NSEC_PER_MSEC);dispatch_source_set_event_handler_f(input_timer,input_tick);dispatch_resume(input_timer);
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
            if(event.type==NSEventTypeKeyDown||event.type==NSEventTypeKeyUp)key_events++;
            else if(event.type!=NSEventTypeFlagsChanged)mouse_events++;
            /* Route Cmd+Q through the same orderly session close as the dashboard. */
            if(event.type==NSEventTypeKeyDown&&event.keyCode==12&&(event.modifierFlags&NSEventModifierFlagCommand)&&!event.ARepeat){deckivo_macos_release(NULL);deckivo_request_quit();return nil;}
            if(event.type==NSEventTypeKeyDown&&event.keyCode==100&&!event.ARepeat){if(capture_state.active)user_ungrab("user_f8");else deckivo_macos_capture(NULL);return nil;}
            if(event.type==NSEventTypeKeyDown&&event.keyCode==53&&stream_has_focus()){user_ungrab("user_escape");return nil;}
            if(!capture_state.active){
                /* A content click re-enters input without forwarding an accidental
                 * double click to the upstream fullscreen/zoom shortcut. */
                if(event.type==NSEventTypeLeftMouseDown&&event.window==stream_window&&stream_has_focus()){
                    NSView *view=stream_window.contentView;
                    if(NSPointInRect([view convertPoint:event.locationInWindow fromView:nil],view.bounds)){begin_capture();return nil;}
                }
                return event;
            }
            if(!stream_has_focus()){end_capture(YES);return event;}
            if(event.window&&event.window!=capture_window){end_capture(YES);return event;}
            /* Process key releases even when Cmd is held; shortcuts cannot leave W stuck. */
            if(event.type==NSEventTypeKeyUp)dk_mac_key(&input,event.keyCode,false);
            if(event.modifierFlags&NSEventModifierFlagCommand){dk_mac_reset(&input,seconds());return event;}
            if(event.type==NSEventTypeFlagsChanged){dk_mac_key(&input,56,(event.modifierFlags&NSEventModifierFlagShift)!=0);dk_mac_key(&input,59,(event.modifierFlags&NSEventModifierFlagControl)!=0);dk_mac_key(&input,58,(event.modifierFlags&NSEventModifierFlagOption)!=0);return nil;}
            if(event.type==NSEventTypeKeyDown||event.type==NSEventTypeKeyUp){
                if(dk_mac_key(&input,event.keyCode,event.type==NSEventTypeKeyDown))accepted_keys++;
                /* F11 remains the engine's fullscreen shortcut. Other keys belong to this mode. */
                return event.keyCode==103?event:nil;
            }
            switch(event.type){
                case NSEventTypeMouseMoved:case NSEventTypeLeftMouseDragged:case NSEventTypeRightMouseDragged:case NSEventTypeOtherMouseDragged:
                    accepted_mouse++;
                    if(ignore_initial_motion){ignore_initial_motion=NO;return nil;}
                    dk_mac_motion(&input,event.deltaX,event.deltaY,seconds());return nil;
                case NSEventTypeLeftMouseDown:accepted_mouse++;input.mouse[0]=true;return nil;case NSEventTypeLeftMouseUp:accepted_mouse++;input.mouse[0]=false;return nil;
                case NSEventTypeRightMouseDown:accepted_mouse++;input.mouse[1]=true;return nil;case NSEventTypeRightMouseUp:accepted_mouse++;input.mouse[1]=false;return nil;
                case NSEventTypeOtherMouseDown:if(event.buttonNumber>=2&&event.buttonNumber<=4){accepted_mouse++;input.mouse[event.buttonNumber]=true;return nil;}return event;
                case NSEventTypeOtherMouseUp:if(event.buttonNumber>=2&&event.buttonNumber<=4){accepted_mouse++;input.mouse[event.buttonNumber]=false;return nil;}return event;
                default:return event;
            }
        }];
        resign_observer=[NSNotificationCenter.defaultCenter addObserverForName:NSApplicationDidResignActiveNotification object:NSApp queue:nil usingBlock:^(NSNotification *note){(void)note;end_capture(YES);}];
        window_observer=[NSNotificationCenter.defaultCenter addObserverForName:NSWindowDidResignKeyNotification object:nil queue:nil usingBlock:^(NSNotification *note){if(note.object==capture_window)end_capture(YES);}];
        termination_observer=[NSNotificationCenter.defaultCenter addObserverForName:NSApplicationWillTerminateNotification object:NSApp queue:nil usingBlock:^(NSNotification *note){(void)note;deckivo_macos_release(NULL);}];
    });
}
