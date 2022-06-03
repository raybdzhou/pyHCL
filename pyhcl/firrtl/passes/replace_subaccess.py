from pyhcl.firrtl.ir import *
from typing import List, Dict
from dataclasses import dataclass
from pyhcl.firrtl.passes.namespace import Namespace
from pyhcl.firrtl.passes.utils import get_width

@dataclass
class ReplaceSubaccess:
    c: Circuit

    def run(self, namespace: Namespace):
        modules: List[Module] = []

        def get_ref_name(e: Definition) -> str:
            if isinstance(e, RefSubaccess):
                return get_ref_name(e.ref_arg)
            elif isinstance(e, RefSubfield):
                return get_ref_name(e.ref_arg)
            elif isinstance(e, RefSubindex):
                return get_ref_name(e.ref_arg)
            elif isinstance(e, RefId):
                return get_ref_name(e.ref_arg)
            else:
                return e.name

        def has_access(e: Exp) -> bool:
            if isinstance(e, RefSubaccess):
                return True
            elif isinstance(e, (RefSubfield, RefSubindex)):
                return has_access(e.ref_arg)
            else:
                return False

        def replace_subaccess(e: Exp):
            cons: List[Exp] = []
            exps: List[Exp] = []
            if isinstance(e, RefSubaccess):
                xcons, xexps = replace_subaccess(e.ref_arg)
                if len(cons) == 0 and len(xexps) == 0:
                    if isinstance(e.ref_arg.type, Vector):
                        for i in range(e.ref_arg.type.size):
                            cons.append(Op(Gender.male, UInt(1), True, "eq", [e.index_exp, LitUInt(Gender.undefined, UInt(get_width(e.ref_arg.type.size)), True, i)], []))
                            exps.append(RefSubindex(e.gender, e.type, e.passive_type, e.ref_arg, i))
                    else:
                        exps.append(e)
                else:
                    if isinstance(e.ref_arg.type, Vector):
                        for i in range(e.ref_arg.type.size):
                            for xcon in xcons:
                                cons.append(Op(Gender.male, UInt(1), True, "and", [xcon, Op(Gender.male, UInt(1), True, "eq",
                                [e.index_exp, LitUInt(Gender.undefined, UInt(get_width(e.ref_arg.type.size)), True, i)], [])], []))
                            for xexp in xexps:
                                exps.append(RefSubindex(e.gender, e.type, e.passive_type, xexp, i))
                    else:
                        cons, exps = xcons, xexps
            elif isinstance(e, RefSubfield):
                xcons, xexps = replace_subaccess(e.ref_arg)
                cons = xcons
                for xexp in xexps:
                    exps.append(RefSubfield(e.gender, e.type, e.passive_type, xexp, e.ref_field))
            elif isinstance(e, RefSubindex):
                xcons, xexps = replace_subaccess(e.ref_arg)
                cons = xcons
                for xexp in xexps:
                    exps.append(RefSubindex(e.gender, e.type, e.passive_type, xexp, e.index))
            
            return cons, exps

        def replace_subaccess_e(e: Exp, stats: List[Exp], sourceinfo: SourceInfo, is_sink: bool = False, source: Exp = None) -> Exp:
            if isinstance(e, ValidIf):
                return ValidIf(e.gender, e.type, e.passive_type, replace_subaccess_e(e.con, stats, sourceinfo),
                replace_subaccess_e(e.vad, stats, sourceinfo))
            elif isinstance(e, Mux):
                return Mux(e.gender, e.type, e.passive_type, replace_subaccess_e(e.con, stats, sourceinfo),
                replace_subaccess_e(e.true_exp, stats, sourceinfo), replace_subaccess_e(e.false_exp, stats, sourceinfo))
            elif isinstance(e, Op):
                return Op(e.gender, e.type, e.passive_type, e.name, [replace_subaccess_e(operand, stats, sourceinfo) for operand in e.operands],
                e.parameters)
            elif isinstance(e, (RefSubaccess, RefSubfield, RefSubindex)) and has_access(e):
                if is_sink:
                    cons, exps = replace_subaccess(e)
                    gen_nodes: Dict[str, DefNode] = {}
                    connects: Dict[str, Connect] = {}
                    new_stats: List[Exp] = []
                    e_name = get_ref_name(e)
                    for stat in stats:
                        if isinstance(stat, Connect) and get_ref_name(stat.lexp) == e_name:
                            connects[e.emit_verilog()] = stat.rexp
                        else:
                            new_stats.append(stat)
                    stats = new_stats
                    for i in range(len(cons)):
                        stats.append(Connect(sourceinfo, exps[i], Mux(Gender.male, e.type, True, cons[i], source, connects[exps[i].emit_verilog()])))
                    return
                else:
                    cons, exps = replace_subaccess(e)
                    gen_nodes: Dict[str, DefNode] = {}
                    for i in range(len(cons)):
                        if i == 0:
                            name = namespace.auto_get_name()
                            gen_node = DefNode(sourceinfo, name, None,
                            ValidIf(Gender.male, e.type, True, cons[i], exps[i]))
                            stats.append(gen_node)
                            gen_nodes[name] = gen_node
                        else:
                            last_node = gen_nodes[namespace.last_name()]
                            name = namespace.auto_get_name()
                            gen_node = DefNode(sourceinfo, name, None,
                            Mux(Gender.male, e.type, True, cons[i], exps[i], 
                            RefId(Gender.undefined, last_node.node_exp.type, True, last_node)))
                            stats.append(gen_node)
                            gen_nodes[name] = gen_node
                    return RefId(e.gender, e.type, e.passive_type, gen_nodes[namespace.last_name()])
            else:
                return e

        def replace_subaccess_s(s: DefStat, stats: List[DefStat]):
            if isinstance(s, When):
                stats.append(When(s.sourceinfo, s.whenbegin, s.whenend,
                s.has_else, replace_subaccess_s(s.elsebegin), s.elseend,
                [replace_subaccess_s(sx, stats) for sx in s.stats]))
            elif isinstance(s, ElseBegin):
                stats.append(ElseBegin(s.sourceinfo, [replace_subaccess_s(sx, stats) for sx in s.stats]))
            elif isinstance(s, DefNode):
                stats.append(DefNode(s.sourceinfo, s.name, s.instanceid, replace_subaccess_e(s.node_exp, stats, s.sourceinfo)))
            elif isinstance(s, DefRegReset):
                stats.append(DefRegReset(s.sourceinfo, s.name, s.instanceid, s.clk, s.type, s.reset_signal,
                replace_subaccess_e(s.reset_value, stats, s.sourceinfo)))
            elif isinstance(s, Connect):
                rexp = replace_subaccess_e(s.rexp, stats, s.sourceinfo)
                lexp = replace_subaccess_e(s.lexp, stats, s.sourceinfo, True, rexp)
                if lexp is not None:
                    stats.append(Connect(s.sourceinfo, lexp, rexp))
            else:
                stats.append(s)

        def replace_subaccess_m(m: Module) -> Module:
            stats: List[DefStat] = []
            for stat in m.stats:
                replace_subaccess_s(stat, stats)
            return Module(m.sourceinfo, m.name, m.instanceid, m.ports, stats)

        for m in self.c.modules:
            modules.append(replace_subaccess_m(m))
        return Circuit(self.c.sourceinfo, self.c.name, self.c.instanceid, modules)
