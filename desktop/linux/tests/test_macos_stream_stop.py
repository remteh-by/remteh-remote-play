"""Run the stop watchdog against real owned children and local Unix sockets."""
import os
from pathlib import Path
import select
import signal
import socket
import subprocess
import sys
import tempfile
import threading
import time
import unittest

sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from macos_supervisor import supervise_engine


@unittest.skipUnless(os.name=='posix','Unix subprocess and socket lifecycle')
class MacStreamStopTests(unittest.TestCase):
    def setUp(self):
        self.temp=tempfile.TemporaryDirectory(prefix='dk-stop-',dir='/tmp')
        self.addCleanup(self.temp.cleanup)
        self.root=Path(self.temp.name)
        self.control=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
        self.control.bind(str(self.root/'control'))
        self.addCleanup(self.control.close)
        self.adapter=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
        self.adapter.bind(str(self.root/'adapter'))
        self.adapter.setblocking(False)
        self.addCleanup(self.adapter.close)
        self.sender=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
        self.sender.settimeout(.05)
        self.addCleanup(self.sender.close)

    def child(self,ignore_term=False,duration=30):
        source=('import signal,time\n'
                f'signal.signal(signal.SIGTERM,signal.SIG_IGN)\n' if ignore_term else 'import time\n')
        source+=f'print("ready",flush=True)\ntime.sleep({duration!r})\n'
        child=subprocess.Popen([sys.executable,'-u','-c',source],stdout=subprocess.PIPE,stderr=subprocess.DEVNULL)
        def cleanup():
            if child.poll() is None:child.kill()
            child.wait(timeout=3)
            child.stdout.close()
        self.addCleanup(cleanup)
        self.assertTrue(select.select([child.stdout],[],[],3)[0],'Owned child did not start')
        self.assertEqual(child.stdout.readline(),b'ready\n')
        return child

    def send(self,value):
        self.sender.sendto(value,str(self.root/'control'))

    def test_repeated_end_stream_cannot_extend_a_hung_child_deadline(self):
        child=self.child(ignore_term=True)
        self.send(b'stop')
        done=threading.Event()
        def repeat():
            while not done.wait(.015):
                try:self.send(b'stop')
                except (OSError,TimeoutError):pass
        thread=threading.Thread(target=repeat)
        thread.start()
        started=time.monotonic()
        try:code=supervise_engine(child,self.control,self.root/'adapter',.15,.05)
        finally:done.set();thread.join(timeout=2)
        self.assertEqual(code,-signal.SIGKILL)
        self.assertLess(time.monotonic()-started,2)
        self.assertEqual(self.adapter.recv(32),b'quit')
        self.assertFalse(thread.is_alive())

    def test_native_window_close_is_bounded_without_sending_a_second_quit(self):
        child=self.child()
        self.send(b'closing')
        code=supervise_engine(child,self.control,self.root/'adapter',.05,.2)
        self.assertEqual(code,-signal.SIGTERM)
        with self.assertRaises(BlockingIOError):self.adapter.recv(32)

    def test_unknown_control_packet_does_not_stop_a_healthy_child(self):
        child=self.child(duration=.25)
        self.send(b'garbage')
        self.assertEqual(supervise_engine(child,self.control,self.root/'adapter',.01,.01),0)
        with self.assertRaises(BlockingIOError):self.adapter.recv(32)


if __name__=='__main__':unittest.main()
