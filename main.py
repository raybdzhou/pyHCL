from __future__ import annotations
from pyhcl import *

class FullAdderIO(Bundle):
    def __init__(self):
        super().__init__()
        self.a = Input(Bool())
        self.b = Input(Bool())
        self.cin = Input(Bool())
        self.sum = Output(Bool())
        self.cout = Output(Bool())
        

class FullAdder(Module):
    def __init__(self):
        super().__init__()
        self.io = FullAdderIO().IO()

        self.io.sum @= self.io.a ^ self.io.b & self.io.cin
        self.io.cout @= self.io.a & self.io.b | self.io.b & self.io.cin | self.io.a & self.io.cin

if __name__ == "__main__":
    builder.emit_verilog(builder.elaborate(FullAdder().gen()), "FullAdder.v")
