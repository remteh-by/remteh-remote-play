"""Focused keyboard/mouse → standard gamepad; never observes global input."""
import math
import socket
import struct
import time

_sequence_tick=0

DEFAULT_KEYS={'W':'ly-','S':'ly+','A':'lx-','D':'lx+','Space':'cross','C':'circle','R':'square','F':'triangle','Q':'l1','E':'r1','Ctrl':'l3','Alt':'r3','Return':'options','1':'share','Tab':'touchpad','F2':'ps','Up':'up','Down':'down','Left':'left','Right':'right'}
SDL_BUTTONS={'cross':0,'circle':1,'square':2,'triangle':3,'share':4,'ps':5,'options':6,'l3':7,'r3':8,'l1':9,'r1':10,'up':11,'down':12,'left':13,'right':14,'touchpad':20}


class InputState:
    def __init__(self,sensitivity=.025,invert_y=False,mapping=None):
        self.sensitivity=max(.001,min(.2,float(sensitivity))) if isinstance(sensitivity,(int,float)) and math.isfinite(sensitivity) else .025
        self.invert_y=bool(invert_y)
        self.mapping=DEFAULT_KEYS.copy()
        if isinstance(mapping,dict):
            self.mapping.update({key:value for key,value in mapping.items() if key in DEFAULT_KEYS and value in set(DEFAULT_KEYS.values())})
        self.sequence=0
        self.reset()

    def reset(self):
        self.keys=set();self.mouse_buttons=set();self.mouse=(0.,0.);self.moved_at=0.

    def key(self,name,down):
        if name not in self.mapping:return False
        self.keys.add(name) if down else self.keys.discard(name)
        return True

    def move(self,dx,dy,at=None):
        if not all(isinstance(v,(int,float)) and math.isfinite(v) for v in (dx,dy)):return
        self.mouse=(max(-1.,min(1.,dx*self.sensitivity)),max(-1.,min(1.,dy*self.sensitivity*(-1 if self.invert_y else 1))))
        self.moved_at=time.monotonic() if at is None else at

    def packet(self,at=None):
        at=time.monotonic() if at is None else at
        actions={self.mapping[key] for key in self.keys}
        buttons=sum(1<<index for name,index in SDL_BUTTONS.items() if name in actions)
        if 'middle' in self.mouse_buttons:buttons|=1<<SDL_BUTTONS['r3']
        x=int('lx+' in actions)-int('lx-' in actions);y=int('ly+' in actions)-int('ly-' in actions)
        scale=max(1.,math.hypot(x,y));x/=scale;y/=scale
        rx,ry=self.mouse if at-self.moved_at<.08 else (0.,0.)
        axes=[round(v*32767) for v in (x,y,rx,ry)]+[32767 if key in self.mouse_buttons else -32768 for key in ('right','left')]
        global _sequence_tick
        _sequence_tick=max(int(time.monotonic()*1000),_sequence_tick+1)
        self.sequence=_sequence_tick&0xffffffff
        return struct.pack('<4sII6h',b'DKI1',self.sequence,buttons,*axes)


class InputTransport:
    def __init__(self,path):
        self.path=str(path)
        self.socket=socket.socket(socket.AF_UNIX,socket.SOCK_DGRAM)
        self.socket.setblocking(False)

    def send(self,packet):
        try:self.socket.sendto(packet,self.path);return True
        except OSError:return False

    def close(self):self.socket.close()
