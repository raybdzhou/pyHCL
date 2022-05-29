# flatten: Expand nested list
from pyhcl.firrtl.ir import *
def flatten(v: list):
    vx: list = []
    for _ in v:
        if isinstance(_, list):
            vx.extend(flatten(_))
        else:
            vx.append(_)
    return vx

def flip(d: Dir):
    if d == Dir.Input:
        return Dir.Output
    elif d == Dir.Output:
        return Dir.Input
    else:
        return d