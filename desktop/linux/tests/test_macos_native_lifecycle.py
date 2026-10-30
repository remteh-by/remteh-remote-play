"""Exercise production native code and the actual SDL audio interposition."""
from pathlib import Path
import os
import shutil
import subprocess
import sys
import tempfile
import unittest


@unittest.skipUnless(sys.platform=='darwin','macOS native adapter')
class MacNativeLifecycleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        compiler=shutil.which('clang')
        cls.sdl=Path(os.environ.get('DECKIVO_TEST_SDL_PREFIX','/opt/homebrew/opt/sdl2'))
        if not compiler or not (cls.sdl/'include/SDL2/SDL.h').exists():
            if os.environ.get('DECKIVO_REQUIRE_MAC_NATIVE_TESTS')=='1':
                raise RuntimeError('Required Mac native tests need clang and SDL2 at DECKIVO_TEST_SDL_PREFIX')
            raise unittest.SkipTest('The Mac builder clang/SDL2 dependencies are required')
        cls.temp=tempfile.TemporaryDirectory(prefix='dk-native-')
        cls.addClassCleanup(cls.temp.cleanup)
        cls.work=Path(cls.temp.name)
        root=Path(__file__).resolve().parents[2]
        def run(args):return subprocess.run([str(x) for x in args],capture_output=True,text=True,check=True,timeout=60)
        cls.run_compile=staticmethod(run)
        common=[compiler,'-Wall','-Wextra','-Werror','-O1','-mmacosx-version-min=13.0']
        run(common+['-fsanitize=address,undefined',root/'macos/test-input-state.c','-o',cls.work/'test-state'])
        run(common+['-c',root/'linux/native/kbm-bridge.c','-o',cls.work/'bridge.o'])
        run(common+['-fobjc-arc','-c',root/'macos/native-input.m','-o',cls.work/'mac.o'])
        cls.adapter=cls.work/'adapter.dylib'
        run([compiler,'-dynamiclib','-undefined','dynamic_lookup','-framework','Cocoa','-framework','ApplicationServices',cls.work/'bridge.o',cls.work/'mac.o','-o',cls.adapter])
        run(common+['-I'+str(cls.sdl/'include/SDL2'),root/'macos/test-audio-minimize.c',
                    '-L'+str(cls.sdl/'lib'),'-lSDL2','-Wl,-rpath,'+str(cls.sdl/'lib'),'-Wl,-export_dynamic','-o',cls.work/'test-audio'])
        run(common+['-fobjc-arc',root/'macos/test-input-runtime.m','-framework','Foundation',
                    '-L'+str(cls.sdl/'lib'),'-lSDL2','-Wl,-rpath,'+str(cls.sdl/'lib'),'-Wl,-export_dynamic','-o',cls.work/'test-runtime'])

    def test_focus_input_and_retina_window_policy_under_sanitizers(self):
        result=self.run_compile([self.work/'test-state'])
        self.assertIn('PASS:',result.stdout)
        print(result.stdout.strip())

    def test_live_input_request_parser_rejects_partial_or_invalid_profiles(self):
        environment={k:v for k,v in os.environ.items() if not k.startswith(('DECKIVO_','DYLD_'))}
        environment.update(DYLD_INSERT_LIBRARIES=str(self.adapter),SDL_AUDIODRIVER='dummy',DECKIVO_KBM='0')
        result=subprocess.run([str(self.work/'test-runtime')],env=environment,capture_output=True,text=True,check=True,timeout=30)
        self.assertIn('PASS:',result.stdout)
        print(result.stdout.strip())

    def test_minimized_audio_is_dropped_and_resume_has_no_backlog(self):
        environment={k:v for k,v in os.environ.items() if not k.startswith(('DECKIVO_','DYLD_'))}
        environment.update(DYLD_INSERT_LIBRARIES=str(self.adapter),SDL_AUDIODRIVER='dummy',DECKIVO_KBM='0')
        result=subprocess.run([str(self.work/'test-audio')],env=environment,capture_output=True,text=True,check=True,timeout=30)
        self.assertIn('PASS:',result.stdout)
        print(result.stdout.strip())


if __name__=='__main__':unittest.main()
