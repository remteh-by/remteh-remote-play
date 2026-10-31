#import <Foundation/Foundation.h>
#include <assert.h>
#include <dlfcn.h>
#include <stdio.h>
#include <string.h>

int avcodec_receive_frame(void *context,void *frame) {(void)context;(void)frame;return -1;}

int main(void) {
    @autoreleasepool {
        int (*validate)(const char *,size_t)=dlsym(RTLD_DEFAULT,"deckivo_validate_input_request");
        assert(validate);
        NSDictionary *valid=@{@"schema":@1,@"revision":@"0123456789abcdef0123456789abcdef",
            @"keyboard":@"13:23,1:24,0:25,2:26",@"mouse":@"0:22,1:21,2:8,3:1,4:2",
            @"sensitivity":@0.025,@"invert_y":@(NO)};
        NSData *data=[NSJSONSerialization dataWithJSONObject:valid options:0 error:NULL];
        assert(validate(data.bytes,data.length));
        NSMutableDictionary *camera=valid.mutableCopy;
        camera[@"camera"]=@{@"mouse_raw_input":@(YES),@"mouse_smoothing_ms":@8,@"mouse_deadzone":@.12,@"mouse_response_curve":@1.6};
        data=[NSJSONSerialization dataWithJSONObject:camera options:0 error:NULL];assert(validate(data.bytes,data.length));
        for(NSArray *invalid in @[@[@"mouse_smoothing_ms",@17],@[@"mouse_smoothing_ms",@(YES)],@[@"mouse_deadzone",@.4],@[@"mouse_response_curve",@0],@[@"mouse_raw_input",@1]]){
            NSMutableDictionary *profile=[camera[@"camera"] mutableCopy];profile[invalid[0]]=invalid[1];camera[@"camera"]=profile;
            data=[NSJSONSerialization dataWithJSONObject:camera options:0 error:NULL];assert(!validate(data.bytes,data.length));
            camera[@"camera"]=@{@"mouse_raw_input":@(YES),@"mouse_smoothing_ms":@8,@"mouse_deadzone":@.12,@"mouse_response_curve":@1.6};
        }
        NSArray *invalid=@[@[@"schema",@2],@[@"schema",@(YES)],@[@"sensitivity",@(YES)],
            @[@"sensitivity",@0.00001],@[@"sensitivity",@1],@[@"invert_y",@"false"],
            @[@"keyboard",@"53:0"],@[@"keyboard",@"13:23,"],@[@"mouse",@"5:1"],
            @[@"keyboard",@"13:35"],@[@"mouse",@[]],@[@"revision",@"invalid revision"]];
        for(NSArray *change in invalid){
            NSMutableDictionary *value=valid.mutableCopy;value[change[0]]=change[1];
            data=[NSJSONSerialization dataWithJSONObject:value options:0 error:NULL];
            assert(!validate(data.bytes,data.length));
        }
        NSMutableDictionary *unbound=valid.mutableCopy;unbound[@"keyboard"]=@"";unbound[@"mouse"]=@"";
        data=[NSJSONSerialization dataWithJSONObject:unbound options:0 error:NULL];
        assert(validate(data.bytes,data.length));
        assert(!validate("[]",2));assert(!validate("{",1));assert(!validate(NULL,0));
        char large[17000];memset(large,' ',sizeof(large));assert(!validate(large,sizeof(large)));
        puts("PASS: production runtime input parser; valid/unbound profiles; malformed, boolean, reserved-key and oversized requests rejected");
    }
    return 0;
}
