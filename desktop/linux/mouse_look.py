"""Bounded mouse-camera options; independent of bindings and device identity."""
import math

DEFAULTS = {'mouse_raw_input': True, 'mouse_smoothing_ms': 8.0,
            'mouse_deadzone': 0.0, 'mouse_response_curve': 1.0}
RANGES = {'mouse_smoothing_ms': (0., 16.), 'mouse_deadzone': (0., .35),
          'mouse_response_curve': (.5, 3.)}


def settings(value,strict=False):
    result=DEFAULTS.copy()
    if not isinstance(value,dict):
        if strict:raise ValueError('Invalid mouse camera options')
        return result
    for key in DEFAULTS:
        if key not in value:continue
        item=value[key]
        valid=type(item) is bool if key=='mouse_raw_input' else (
            type(item) in (int,float) and math.isfinite(item) and RANGES[key][0]<=item<=RANGES[key][1])
        if not valid:
            if strict:raise ValueError('Invalid mouse camera option: '+key)
            continue
        result[key]=item if type(item) is bool else float(item)
    return result
