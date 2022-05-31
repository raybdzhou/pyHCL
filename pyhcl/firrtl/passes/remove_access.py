from pyhcl.firrtl.ir import *
from typing import List, Dict
from dataclasses import dataclass
from pyhcl.firrtl.passes.utils import flatten, flip
from pyhcl.exceptions import PyHCLException

@dataclass
class RemoveAccess:
    c: Circuit

    def run(self) -> Circuit:
        modules: List[Module] = []

        def gen_def(defin: Definition, type: Type = None, dir: Dir = None, name: str = None):
            if isinstance(defin, Circuit):
                return Circuit(defin.sourceinfo, name, defin.instanceid, defin.modules)
            elif isinstance(defin, Module):
                return Module(defin.sourceinfo, name, defin.instanceid, defin.ports, defin.stats)
            elif isinstance(defin, Port):
                return Port(defin.sourceinfo, name, defin.instanceid, defin.direction, type)
            elif isinstance(defin, Field):
                return Field(defin.sourceinfo, name, defin.instanceid, defin.is_flip, type)
            elif isinstance(defin, DefWire):
                return DefWire(defin.sourceinfo, name, defin.instanceid, type)
            elif isinstance(defin, DefReg):
                return DefReg(defin.sourceinfo, name, defin.instanceid, defin.clk, type)
            elif isinstance(defin, DefRegReset):
                return DefRegReset(defin.sourceinfo, name, defin.instanceid, defin.clk, type,
                defin.reset_signal, defin.reset_value)
            elif isinstance(defin, DefMem):
                return DefMem(defin.sourceinfo, name, defin.instanceid, type, defin.size)
            elif isinstance(defin, DefNode):
                return DefNode(defin.sourceinfo, name, defin.instanceid, defin.node_exp)
            elif isinstance(defin, InstModule):
                return InstModule(defin.sourceinfo, name, defin.instanceid, defin.module)
            elif isinstance(defin, RefMemPort):
                return RefMemPort(defin.sourceinfo, name, defin.instanceid, defin.clk, defin.refmem, 
                defin.addr, defin.read_or_write, defin.infer)
            elif isinstance(defin, RefId):
                return RefId(defin.gender, type, defin.passive_type, gen_def(defin.ref_arg, type, dir, name))
            else:
                return defin

        def remove_access(e: Exp, type: Type = None, name: str = None) -> Exp:
            if isinstance(e, RefId):
                return gen_def(e, type, None, name)
            elif isinstance(e, RefSubindex):
                return remove_access(e.ref_arg, e.type, f"{e.ref_arg.name}_{e.index}")
            elif isinstance(e, RefSubfield):
                if isinstance(e.ref_field, Field):
                    name = f"{e.ref_arg.emit_verilog()}_{e.ref_field.name}"
                elif e.ref_field is None:
                    name = f"{e.ref_arg.emit_verilog()}"
                else:
                    name = f"{e.ref_arg.emit_verilog()}_{e.ref_field.emit_verilog()}"
                return remove_access(e.ref_arg, e.type, name)
            elif isinstance(e, RefSubaccess):
                ...
            else:
                return e

        def remove_access_e(e: Exp) -> Exp:
            if isinstance(e, (RefSubindex, RefSubfield)):
                return remove_access(e)
            elif isinstance(e, ValidIf):
                return ValidIf(e.gender, e.type, e.passive_type, remove_access_e(e.con), remove_access_e(e.vad))
            elif isinstance(e, Mux):
                return Mux(e.gender, e.type, e.passive_type, remove_access_e(e.con), remove_access_e(e.true_exp),
                remove_access_e(e.false_exp))
            elif isinstance(e, Op):
                return Op(e.gender, e.type, e.passive_type, e.name, [remove_access_e(operand) for operand in e.operands],
                e.parameters)
            else:
                return e

        def remove_access_s(s: DefStat) -> DefStat:
            if isinstance(s, DefReg):
                return DefReg(s.sourceinfo, s.name, s.instanceid, remove_access_e(s.clk), s.type)
            elif isinstance(s, DefRegReset):
                return DefRegReset(s.sourceinfo, s.name, s.instanceid,
                remove_access_e(s.clk), remove_access_e(s.reset_signal), remove_access_e(s.reset_value))
            elif isinstance(s, DefNode):
                return DefNode(s.sourceinfo, s.name, s.instanceid, remove_access_e(s.node_exp))
            elif isinstance(s, RefMemPort):
                return RefMemPort(s.sourceinfo, s.name, s.instanceid, remove_access_e(s.clk), s.refmem,
                remove_access_e(s.addr), s.read_or_write, s.infer)
            elif isinstance(s, Connect):
                return Connect(s.sourceinfo, remove_access_e(s.lexp), remove_access_e(s.rexp))
            elif isinstance(s, When):
                return When(s.sourceinfo, WhenBegin(s.whenbegin.sourceinfo, remove_access_e(s.whenbegin.con)),
                s.whenend, s.has_else, remove_access_s(s.elsebegin), s.elseend, [remove_access_s(sx) for sx in s.stats])
            elif isinstance(s, ElseBegin):
                return ElseBegin(s.sourceinfo, [remove_access_s(sx) for sx in s.stats])
            else:
                return s

        def remove_access_m(m: Module) -> Module:
            stats = list(map(lambda stat: remove_access_s(stat), m.stats))
            return Module(m.sourceinfo, m.name, m.instanceid, m.ports, stats)

        for m in self.c.modules:
            modules.append(remove_access_m(m))
        return Circuit(self.c.sourceinfo, self.c.name, self.c.instanceid, modules)