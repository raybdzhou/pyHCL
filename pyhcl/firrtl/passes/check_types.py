from typing import List, Dict
from dataclasses import dataclass
from pyhcl.firrtl.ir import *
from pyhcl.firrtl.passes.namespace import Namespace
from pyhcl.exceptions import PyHCLException

class Error:
    def __init__(self):
        self.errors: List[PyHCLException] = []

    def append(self, pe: PyHCLException):
        self.errors.append(pe)
    
    def trigger(self):
        if len(self.errors) == 0:
            return
        elif len(self.errors) == 1:
            raise self.errors.pop()
        else:
            print(self.errors)
            self.append(f'{len(self.errors)} errors detected!')
            raise PyHCLException(self.errors)

@dataclass
class CheckTypes:
    c: Circuit
    errors: Error = Error()

    def run(self, namespace: Namespace):
        def check_types_w(t: Type, sourceinfo: SourceInfo):
            if isinstance(t, (UInt, SInt)):
                if t.width <= 0:
                    self.errors.append(PyHCLException(f"[{sourceinfo.emit()}] Illegal bit-width statement"))
            elif isinstance(t, Vector):
                if t.size < 0:
                    self.errors.append(PyHCLException(f"[{sourceinfo.emit()}] Illegal size statement"))
                check_types_w(t.type, sourceinfo)
            elif isinstance(t, Bundle):
                for f in t.fields:
                    check_types_w(f.type, sourceinfo)
            else:
                ...
        
        def check_types_e(e: Exp, sourceinfo: SourceInfo):
            if isinstance(e, Mux):
                if not isinstance(e.con.type, UInt) or e.con.type.width != 1:
                    self.errors.append(PyHCLException(f"[{sourceinfo.emit()}] Illegal type/bit-width in {e.con}"))
                check_types_e(e.true_exp, sourceinfo)
                check_types_e(e.false_exp, sourceinfo)
            elif isinstance(e, ValidIf):
                if not isinstance(e.con.type, UInt) or e.con.type.width != 1:
                    self.errors.append(PyHCLException(f"[{sourceinfo.emit()}] Illegal type/bit-width in {e.con}"))
                check_types_e(e.vad, sourceinfo)
            elif isinstance(e, Op):
                for operand in e.operands:
                    check_types_e(operand, sourceinfo)
            elif isinstance(e, LitUInt):
                if get_width(e.initial) > e.type.width:
                    self.errors.append(f"[{sourceinfo.emit()}] Bit-width less than the width of the value")
            elif isinstance(e, LitSInt):
                if get_width(e.initial) + 1 > e.type.width:
                    self.errors.append(f"[{sourceinfo.emit()}] Bit-width less than the width of the value")
            elif isinstance(e, Ref):
                if isinstance(e.ref_arg, DefNode):
                    if type(e.type) != type(e.ref_arg.node_exp.type) or e.type.width < e.ref_arg.node_exp.type.width:
                        self.errors.append(f"[{sourceinfo.emit()}] Illegal type/bit-width")
                elif isinstance(e, RefMemPort):
                    ...
                elif isinstance(e, Ref):
                    if isinstance(e.ref_arg.type, Bundle) and isinstance(e, RefSubfield):
                        for fx in e.ref_arg.type.fields:
                            if fx.name == e.ref_field.name:
                                if type(e.type) != type(fx.type) or e.type.width < fx.type.width:
                                    self.errors.append(f"[{sourceinfo.emit()}] Illegal type/bit-width")
                    elif isinstance(e.ref_arg.type, Vector) and isinstance(e, (RefSubaccess, RefSubindex)):
                        check_types_w(e.ref_arg.type, sourceinfo)
                        if type(e.type) != type(e.ref_arg.type.type) or e.type.width < e.ref_arg.type.type.width:
                            self.errors.append(f"[{sourceinfo.emit()}] Illegal type/bit-width")
                    else:
                        if type(e.type) != type(e.ref_arg.type) or e.type.width < e.ref_arg.type.width:
                            self.errors.append(f"[{sourceinfo.emit()}] Illegal type/bit-width")
                    check_types_e(e.ref_arg, sourceinfo)
                else:
                    ...
            else:
                ...

        def check_types_s(s: Union[DefStat, CmdStat]):
            if isinstance(s, When):
                check_types_s(s.whenbegin)
                check_types_s(s.elsebegin)
                for sx in s.stats:
                    check_types_s(sx)
            elif isinstance(s, WhenBegin):
                check_types_e(s.con, s.sourceinfo)
            elif isinstance(s, ElseBegin):
                for sx in s.stats:
                    check_types_s(sx)
            elif isinstance(s, DefWire):
                check_types_w(s.type, s.sourceinfo)
            elif isinstance(s, DefReg):
                if not isinstance(s.clk, Clock):
                    self.errors.append(PyHCLException(f"[{s.sourceinfo.emit()}] Illegal clk type"))
                check_types_w(s.type, s.sourceinfo)
            elif isinstance(s, DefRegReset):
                if not isinstance(s.clk.type, Clock):
                    self.errors.append(PyHCLException(f"[{s.sourceinfo.emit()}] Illegal clk type"))
                if not isinstance(s.reset_signal.type, AsyncReset):
                    self.errors.append(PyHCLException(f"[{s.sourceinfo.emit()}] Illegal reset signal type"))
                if not type(s.reset_value.type) == type(s.type) or s.reset_value.type.width > s.type.width:
                    self.errors.append(PyHCLException(f"[{s.sourceinfo.emit()}] Reset value type/width should be {s.type}, not {s.reset_value.type}"))
                check_types_w(s.type, s.sourceinfo)
            elif isinstance(s, DefMem):
                check_types_w(s.type)
            elif isinstance(s, RefMemPort):
                if not isinstance(s.clk.type, Clock):
                    self.errors.append(PyHCLException(f"[{s.sourceinfo.emit()}] Illegal clk type"))
                check_types_e(s.addr, s.sourceinfo)
            elif isinstance(s, DefNode):
                check_types_e(s.node_exp, s.sourceinfo)
            elif isinstance(s, Connect):
                if not type(s.lexp.type) == type(s.rexp.type) and s.lexp.type.width < s.rexp.type.width:
                    self.errors.append(f"[{s.sourceinfo.emit()}] Illegal connect since right expression's type/width should be {s.lexp.type}, not {s.rexp.type}")
                check_types_e(s.lexp, s.sourceinfo)
                check_types_e(s.rexp, s.sourceinfo)
            else:
                ...

        def check_types_p(p: Port):
            if isinstance(p.type, (UInt, SInt, Clock, AsyncReset, Vector, Bundle)):
                check_types_w(p.type, p.sourceinfo)
            else:
                self.errors.append(PyHCLException(f"[{p.sourceinfo.emit()}] {p.type} is unknown type."))

        def check_types_m(m: Module):
            for p in m.ports:
                check_types_p(p)
            
            for s in m.stats:
                check_types_s(s)   
        
        for m in self.c.modules:
            check_types_m(m)
        
        self.errors.trigger()
        return self.c