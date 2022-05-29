from pyhcl.core.when import Elsewhen
from pyhcl.firrtl.ir import *
from typing import List, Dict
from dataclasses import dataclass
from pyhcl.firrtl.passes.utils import flatten, flip
from pyhcl.exceptions import PyHCLException

@dataclass
class ExpandAggregate:
    c: Circuit

    def run(self):
        modules: List[Module] = []

        def expand_aggregate_t(t: AggType, d: Dir = None, n: str = None):
            if isinstance(t, Vector):
                type_decs = []
                for i in range(t.size):
                    type_decs.extend(expand_aggregate_t(t.type, d, f"{n}_{i}"))
                return type_decs
            elif isinstance(t, Bundle):
                type_decs = []
                for f in t.fields:
                    type_decs.extend(expand_aggregate_t(f.type, flip(d) if f.is_flip else d, f"{n}_{f.name}"))
                return type_decs
            else:
                return [(t, d, n)]

        def expand_aggregate_p(p: Port):
            port_decs: List[Port] = []
            if isinstance(p.type, (UInt, SInt, Clock, AsyncReset)):
                port_decs.append(p)
            elif isinstance(p.type, (Vector, Bundle)):
                port_decs.extend(list(map(lambda type_dec: Port(p.sourceinfo,
                type_dec[2], p.instanceid, type_dec[1], type_dec[0]), expand_aggregate_t(p.type, p.direction))))
            else:
                raise PyHCLException(f"{p.type.__class__.__name__} is unidentified type!")
            return port_decs

        def expand_aggregate_e(e: Exp):
            exp_decs: List[Exp] = []
            names: List[str] = []
            if isinstance(e, ValidIf):
                if isinstance(e.type, (UInt, SInt, Clock, AsyncReset)):
                    exp_decs.append(e)
                elif isinstance(e.type, (Vector, Bundle)):
                    vads = list(map(lambda x: RefId(e.vad.gender, x[0], e.vad.passive_type, Definition(None, x[2]))),
                    expand_aggregate_t(e.vad.type, None, e.vad.emit_verilog()))
                    exp_decs.extend(list(map(lambda vad: ValidIf(e.gender, vad.type, e.passive_type, e.con, vad)), vads))
                    names.extend(list(map(lambda vad: vad.emit_verilog().replace(e.vad.emit_verilog(), ""), vads)))
                else:
                    raise PyHCLException(f"{e.type.__class__.__name__} is unidentified type!")
            elif isinstance(e, Mux):
                if isinstance(e.type, (UInt, SInt, Clock, AsyncReset)):
                    exp_decs.append(e)
                elif isinstance(e.type, (Bundle, Vector)):
                    true_exps = list(map(lambda x: RefId(e.true_exp.gender, x[0], e.true_exp.passive_type, Definition(None, x[2]))),
                    expand_aggregate_t(e.true_exp.type, None, e.true_exp.emit_verilog()))
                    false_exps = list(map(lambda x: RefId(e.false_exp.gender, x[0], e.false_exp.passive_type, Definition(None, x[2]))),
                    expand_aggregate_t(e.false_exp.type, None, e.false_exp.emit_verilog()))
                    exps = zip(true_exps, false_exps)
                    exp_decs.extend(list(map(lambda exp: Mux(e.gender, exp[0].type, e.passive_type, e.con, exp[0], exp[1])), exps))
                    names.extend(list(map(lambda true_exp: true_exp.emit_verilog().replace(e.true_exp.emit_verilog(), ""), true_exps)))
                else:
                    raise PyHCLException(f"{e.type.__class__.__name__} is unidentified type!")
            else:
                exp_decs.append(e)
            return exp_decs, names

        def expand_aggregate_s(s: DefStat):
            stat_decs: List[DefStat] = []
            if isinstance(s, DefWire):
                if isinstance(s.type, (UInt, SInt, Clock, AsyncReset)):
                    stat_decs.append(s)
                elif isinstance(s.type, (Vector, Bundle)):
                    stat_decs.extend(list(map(lambda stat_dec: DefWire(s.sourceinfo,
                    stat_dec[2], s.instanceid, stat_dec[0]), expand_aggregate_t(s.type, None, s.name))))
                else:
                    raise PyHCLException(f"{s.type.__class__.__name__} is unidentified type!")
                return stat_decs
            elif isinstance(s, DefReg):
                if isinstance(s.type, (UInt, SInt, Clock, AsyncReset)):
                    stat_decs.append(s)
                elif isinstance(s.type, (Vector, Bundle)):
                    stat_decs.extend(list(map(lambda stat_dec: DefReg(s.sourceinfo,
                    stat_dec[2], s.instanceid, s.clk, stat_dec[0]), expand_aggregate_t(s.type, None, s.name))))
                else:
                    raise PyHCLException(f"{s.type.__class__.__name__} is unidentified type!")
                return stat_decs
            elif isinstance(s, DefRegReset):
                if isinstance(s.type, (UInt, SInt, Clock, AsyncReset)):
                    stat_decs.append(s)
                elif isinstance(s.type, (Vector, Bundle)):
                    stat_decs.extend(list(map(lambda stat_dec: DefRegReset(s.sourceinfo,
                    stat_dec[2], s.instanceid, s.clk, stat_dec[0], s.reset_signal, s.reset_value), expand_aggregate_t(s.type, None, s.name))))
                else:
                    raise PyHCLException(f"{s.type.__class__.__name__} is unidentified type!")
                return stat_decs
            elif isinstance(s, DefMem):
                return s
            elif isinstance(s, DefNode):
                if isinstance(s.node_exp.type, (Bundle, Vector)):
                    exp_decs, names = expand_aggregate_e(s.node_exp)
                    xs = zip(exp_decs, names)
                    stat_decs.extend(list(map(lambda x: DefNode(s.sourceinfo, f"{s.name}{x[1]}", s.instanceid, x[0]), expand_aggregate_e(s.node_exp), xs)))
                else:
                    stat_decs.append(s)
                return stat_decs
            elif isinstance(s, RefMemPort):
                return s
            elif isinstance(s, When):
                stats: List[DefStat] = []
                for stat in s.stats:
                    stats.extend(flatten(expand_aggregate_s(stat)))
                
                return When(s.sourceinfo, s.whenbegin, s.whenend, s.has_else,
                expand_aggregate_s(s.elsebegin) if s.has_else else s.elsebegin, s.elseend, stats)
            elif isinstance(s, ElseBegin):
                stats: List[DefStat] = []
                for stat in s.stats:
                    stats.extend(flatten(expand_aggregate_s(stat)))
                
                return ElseBegin(s.sourceinfo, stats)
            else:
                return s

        def expand_aggregate_m(m: Module):
            ports = list(map(lambda p: expand_aggregate_p(p), m.ports))
            stats = list(map(lambda s: expand_aggregate_s(s), m.stats))
            return Module(m.sourceinfo, m.name, m.instanceid, flatten(ports), flatten(stats))

        for m in self.c.modules:
            modules.append(expand_aggregate_m(m))
        return Circuit(self.c.sourceinfo, self.c.name, self.c.instanceid, modules)

