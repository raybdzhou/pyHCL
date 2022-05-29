from pyhcl.firrtl.ir import *
from typing import List, Dict
from dataclasses import dataclass
from pyhcl.firrtl.passes.utils import flatten, flip
from pyhcl.exceptions import PyHCLException

@dataclass
class ReplaceSubindex:
    c: Circuit

    def run(self) -> Circuit:
        modules: List[Module] = []

        def replace_subindex(e: Exp) -> Exp:
            return e

        def replace_subindex_e(e: Exp) -> Exp:
            if isinstance(e, RefSubindex):
                return replace_subindex(e)
            elif isinstance(e, ValidIf):
                return ValidIf(e.gender, e.type, e.passive_type, replace_subindex_e(e.con), replace_subindex_e(e.vad))
            elif isinstance(e, Mux):
                return Mux(e.gender, e.type, e.passive_type, replace_subindex_e(e.con), replace_subindex_e(e.true_exp),
                replace_subindex_e(e.false_exp))
            elif isinstance(e, Op):
                return Op(e.gender, e.type, e.passive_type, e.name, [replace_subindex_e(operand) for operand in e.operands],
                e.parameters)
            else:
                return e

        def replace_subindex_s(s: DefStat) -> DefStat:
            if isinstance(s, DefReg):
                return DefReg(s.sourceinfo, s.name, s.instanceid, replace_subindex_e(s.clk), s.type)
            elif isinstance(s, DefRegReset):
                return DefRegReset(s.sourceinfo, s.name, s.instanceid,
                replace_subindex_e(s.clk), replace_subindex_e(s.reset_signal), replace_subindex_e(s.reset_value))
            elif isinstance(s, DefNode):
                return DefNode(s.sourceinfo, s.name, s.instanceid, replace_subindex_e(s.node_exp))
            elif isinstance(s, RefMemPort):
                return RefMemPort(s.sourceinfo, s.name, s.instanceid, replace_subindex_e(s.clk), s.refmem,
                replace_subindex_e(s.addr), s.read_or_write, s.infer)
            elif isinstance(s, Connect):
                return Connect(s.sourceinfo, replace_subindex_e(s.lexp), replace_subindex_e(s.rexp))
            elif isinstance(s, When):
                return When(s.sourceinfo, WhenBegin(s.whenbegin.sourceinfo, replace_subindex_e(s.whenbegin.con)),
                s.whenend, s.has_else, replace_subindex_s(s.elsebegin), s.elseend, [replace_subindex_e(sx) for sx in s.stats])
            elif isinstance(s, ElseBegin):
                return ElseBegin(s.sourceinfo, [replace_subindex_s(sx) for sx in s.stats])
            else:
                return s

        def replace_subindex_m(m: Module) -> Module:
            stats = list(map(lambda stat: replace_subindex_s(stat), m.stats))
            return Module(m.sourceinfo, m.name, m.instanceid, m.ports, stats)

        for m in self.c.modules:
            modules.append(replace_subindex_m(m))
        return Circuit(self.c.sourceinfo, self.c.name, self.c.instanceid, modules)