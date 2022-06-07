from dataclasses import dataclass
from typing import Dict, List
from pyhcl.firrtl.ir import *
from pyhcl.firrtl.passes.namespace import Namespace

@dataclass
class AutoInferring:
    c: Circuit
    max_width: int = 0

    def run(self, namespace: Namespace):
        modules: List[Module] = []

        def auto_inferring_t(t: Type) -> Type:
            if isinstance(t, UInt):
                if t.width == 0:
                    return UInt(self.max_width)
                else:
                    self.max_width = self.max_width if self.max_width > t.width else t.width
                    return t
            elif isinstance(t, SInt):
                if t.width == 0:
                    return SInt(self.max_width)
                else:
                    self.max_width = self.max_width if self.max_width > t.width else t.width
                    return t
            elif isinstance(t, (Clock, AsyncReset)):
                return t
            elif isinstance(t, Vector):
                return Vector(t.width, t.size, auto_inferring_t(t.type))
            elif isinstance(t, Bundle):
                return Bundle(t.width, t.size, [Field(fx.sourceinfo, fx.name, fx.instanceid, fx.is_flip, auto_inferring_t(fx.type)) for fx in t.fields])
            else:
                return t

        def auto_inferring_e(e: Exp, inferring_map: Dict[str, Type]) -> Exp:
            if isinstance(e, Mux):
                return Mux(e.gender, e.type, e.passive_type, auto_inferring_e(e.con, inferring_map), auto_inferring_e(e.true_exp, inferring_map),
                auto_inferring_e(e.false_exp, inferring_map))
            elif isinstance(e, ValidIf):
                return ValidIf(e.gender, e.type, e.passive_type, auto_inferring_e(e.con, inferring_map), auto_inferring_e(e.vad, inferring_map))
            elif isinstance(e, Op):
                return Op(e.gender, e.type, e.passive_type, e.name, [auto_inferring_e(operand, inferring_map) for operand in e.operands], e.parameters)
            elif isinstance(e, LitUInt):
                if isinstance(e.type, UInt) is False or e.type.width < get_width(e.initial):
                    return LitUInt(e.gender, UInt(get_width(e.initial)), e.passive_type, e.initial)
                else:
                    return e
            elif isinstance(e, LitSInt):
                if isinstance(e.type, UInt) is False or e.type.width < get_width(e.initial) + 1:
                    return LitSInt(e.gender, UInt(get_width(e.initial) + 1), e.passive_type, e.initial)
                else:
                    return e
            elif isinstance(e, RefId):
                type = e.type
                if isinstance(e.ref_arg, Ref) is False:
                    type = inferring_map[e.emit()]
                return RefId(e.gender, type, e.passive_type, auto_inferring_e(e.ref_arg, inferring_map))
            elif isinstance(e, RefSubfield):
                type = e.type
                if isinstance(e.ref_arg, Ref) is False:
                    type = inferring_map[e.emit()]
                return RefSubfield(e.gender, type, e.passive_type, auto_inferring_e(e.ref_arg, inferring_map), e.ref_field)
            elif isinstance(e, RefSubindex):
                type = e.type
                if isinstance(e.ref_arg, Ref) is False:
                    type = inferring_map[e.emit()]
                return RefSubindex(e.gender, type, e.passive_type, auto_inferring_e(e.ref_arg, inferring_map), e.index)
            elif isinstance(e, RefSubaccess):
                type = e.type
                if isinstance(e.ref_arg, Ref) is False:
                    type = inferring_map[e.emit()]
                return RefSubaccess(e.gender, type, e.passive_type, auto_inferring_e(e.ref_arg, inferring_map), e.index_exp)
            else:
                return e

        def auto_inferring_s(s: Union[DefStat, CmdStat], inferring_map: Dict[str, Type]) -> Union[DefStat, CmdStat]:
            if isinstance(s, When):
                return When(s.sourceinfo, WhenBegin(s.whenbegin.sourceinfo, auto_inferring_e(s.whenbegin.con, inferring_map)), s.whenend,
                s.has_else, auto_inferring_s(s.elsebegin, inferring_map), s.elseend, [auto_inferring_s(sx, inferring_map) for sx in s.stats])
            elif isinstance(s, ElseBegin):
                return ElseBegin(s.sourceinfo, [auto_inferring_s(sx, inferring_map) for sx in s.stats])
            elif isinstance(s, DefReg):
                clk = auto_inferring_e(s.clk, inferring_map)
                return DefReg(s.sourceinfo, s.name, s.instanceid, clk, s.type)
            elif isinstance(s, DefRegReset):
                clk = auto_inferring_e(s.clk, inferring_map)
                reset_signal = auto_inferring_e(s.reset_signal, inferring_map)
                reset_value = auto_inferring_e(s.reset_value, inferring_map)
                type = auto_inferring_t(s.type)
                inferring_map[s.name] = type
                return DefRegReset(s.sourceinfo, s.name, s.instanceid, clk, type, reset_signal, reset_value)
            elif isinstance(s, DefWire):
                inferring_map[s.name] = auto_inferring_t(s.type)
                return s
            elif isinstance(s, DefMem):
                inferring_map[s.name] = auto_inferring_t(s.type)
                return s
            elif isinstance(s, DefNode):
                node_exp = auto_inferring_e(s.node_exp, inferring_map)
                inferring_map[s.name] = node_exp.type
                return DefNode(s.sourceinfo, s.name, s.instanceid, node_exp)
            elif isinstance(s, RefMemPort):
                clk = auto_inferring_e(s.clk, inferring_map)
                addr = auto_inferring_e(s.addr, inferring_map)
                return RefMemPort(s.sourceinfo, s.name, s.instanceid, clk, s.refmem, addr, s.read_or_write, s.infer)
            elif isinstance(s, Connect):
                return Connect(s.sourceinfo, auto_inferring_e(s.lexp, inferring_map), auto_inferring_e(s.rexp, inferring_map), s.is_block)
            else:
                return s
            

        def auto_inferring_m(m: Module, inferring_map: Dict[str, Type]) -> Module:
            stats: List[DefStat] = []
            for p in m.ports:
                inferring_map[p.name] = auto_inferring_t(p.type)
            for s in m.stats:
                stats.append(auto_inferring_s(s, inferring_map))
            return Module(m.sourceinfo, m.name, m.instanceid, m.ports, stats)

        for m in self.c.modules:
            inferring_map: Dict[str, Type] = {}
            modules.append(auto_inferring_m(m, inferring_map))
        return Circuit(self.c.sourceinfo, self.c.name, self.c.instanceid, modules)