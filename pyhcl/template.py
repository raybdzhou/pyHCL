from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from typing import Deque, Union

tree: Deque = deque()


def when(exp):
    t: Deque = deque()
    tree.append(t)
    t.append(exp)

    def w(*exp):
        for i in exp:
            t.append(i)

        return Else()

    class Else:
        def elsewhen(self, ex):
            t.append(ex)
            return w

        def otherwise(self, *e):
            for i in e:
                t.append(i)
            return t

    return w


def temp(exp):
    print(exp)
    return exp





@dataclass
class Node:
    n: str
    exp: Add

@dataclass
class Add:
    l: Ipt
    r: Ipt

@dataclass
class Conn:
    l: Opt
    r: Node

@dataclass
class Ipt:
    u: Ut
    ref: str = None

    def __add__(self, other: Union[Ipt, Opt]) -> Node:
        add = Add(self, other)
        node = Node('N_1', add)
        tree.append(node)
        return node

@dataclass
class Ut:
    w: int

@dataclass
class Opt:
    u: Ut
    ref: str = None

    def __lshift__(self, other: Node):
        conn = Conn(self, other)
        tree.append(conn)
        return self


class A:
    a = Ipt(Ut(32))
    b = Ipt(Ut(32))
    c = Opt(Ut(32))

    def stmt(self):
        A.c << A.a + A.b



@dataclass()
class Module:
    name: str
    tree: Deque

@dataclass
class Circuit:
    name: str
    module: Module


def run(module):
    for k in module.__dict__:
        if not k.startswith('__') and not k == 'stmt':
            v = module.__dict__[k]
            v.ref = k
            tree.appendleft((k, v))
    module().stmt()

    m = Module(module.__name__, tree)
    c = Circuit(m.name, m)
    print(c)
