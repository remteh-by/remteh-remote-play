"""Local, bounded support reminder policy; no session telemetry is uploaded."""
import math

LATER_SECONDS=14*24*60*60


def state(value):
    if not isinstance(value,dict):value={}
    shows=value.get('shows',0);next_at=value.get('next_at',0)
    if type(shows) is not int:shows=0
    if type(next_at) not in (int,float) or not math.isfinite(next_at):next_at=0
    return {'eligible':value.get('eligible') is True,'disabled':value.get('disabled') is True,
        'shows':max(0,min(3,shows)),'next_at':max(0,next_at)}



def complete(value,seconds,clean):
    result=state(value)
    result['eligible']=bool(clean and seconds>=600)
    return result


def due(value,now):
    result=state(value)
    return result['eligible'] and not result['disabled'] and result['shows']<3 and now>=result['next_at']


def shown(value):
    result=state(value);result['eligible']=False;result['shows']=min(3,result['shows']+1);return result


def consume(value,now,allowed=True):
    result=state(value)
    show=allowed and due(result,now)
    result['eligible']=False
    return result,show


def action(value,choice,now):
    result=state(value)
    result['eligible']=False
    if choice=='later':result['next_at']=now+LATER_SECONDS
    else:result['disabled']=True
    return result
