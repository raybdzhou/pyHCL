from platform import node
from pyhcl.firrtl.ir import *
from typing import List, Dict
from dataclasses import dataclass

@dataclass
class VerilogOptimize:
    c: Circuit

    def run(self):
        modules: List[Module] = []

        def auto_gen_node(s):
            return isinstance(s, DefNode) and s.name.startswith("_T")
        
        def get_name(e: Exp) -> str:
            if isinstance(e, (RefSubindex, RefSubfield, RefSubaccess)):
                return get_name(e.ref_arg)
            elif isinstance(e, RefId):
                return e.emit_verilog()

        def verilog_optimize_e(expr: Exp, node_map: Dict[str, DefStat], filter_nodes: set) -> Exp:
            if isinstance(expr, (LitUInt, LitSInt)):
                return expr
            elif isinstance(expr, RefId):
                en = get_name(expr)
                if en in node_map:
                    filter_nodes.add(en)
                    return verilog_optimize_e(node_map[en].node_exp, node_map, filter_nodes)
                else:
                    return expr
            elif isinstance(expr, (RefSubfield, RefSubindex, RefSubaccess)):
                return expr
            elif isinstance(expr, Mux):
                return Mux(
                    expr.gender,
                    expr.type,
                    expr.passive_type,
                    verilog_optimize_e(expr.con, node_map, filter_nodes),
                    verilog_optimize_e(expr.true_exp, node_map, filter_nodes),
                    verilog_optimize_e(expr.false_exp, node_map, filter_nodes))
            elif isinstance(expr, ValidIf):
                return ValidIf(
                    expr.gender,
                    expr.type,
                    expr.passive_type,
                    verilog_optimize_e(expr.cond, node_map, filter_nodes),
                    verilog_optimize_e(expr.value, node_map, filter_nodes))
            elif isinstance(expr, Op):
                operands = list(map(lambda operand: verilog_optimize_e(operand, node_map, filter_nodes), expr.operands))
                return Op(expr.gender, expr.type, expr.passive_type, expr.name, operands, expr.parameters)
            else:
                return expr

        def verilog_optimize_s(stat: Union[DefStat, List[DefStat]], node_map: Dict[str, DefStat], filter_nodes: set) -> Union[DefStat, List[DefStat]]:
            if isinstance(stat, list):
                node_map = {**node_map ,**{s.name: s for s in stat if auto_gen_node(s)}}
                cat_stats = []
                for s in stat:
                    if isinstance(s, Connect):
                        cat_stats.append(Connect(s.sourceinfo, verilog_optimize_e(s.lexp, node_map, filter_nodes), verilog_optimize_e(s.rexp, node_map, filter_nodes)))
                    elif isinstance(s, DefNode):
                        cat_stats.append(DefNode(s.sourceinfo, s.name, s.instanceid, verilog_optimize_e(s.node_exp, node_map, filter_nodes)))
                    elif isinstance(s, When):
                        cat_stats.append(When(s.sourceinfo, verilog_optimize_s(s.whenbegin, node_map, filter_nodes), s.whenend, s.has_else,
                        verilog_optimize_s(s.elsebegin, node_map, filter_nodes), s.elseend,  verilog_optimize_s(s.stats, node_map, filter_nodes)))
                    else:
                        cat_stats.append(s)
                cat_stats = [s for s in cat_stats if not (isinstance(s, DefNode) and s.name in filter_nodes)]
                return cat_stats
            elif isinstance(stat, WhenBegin):
                return WhenBegin(stat.sourceinfo, verilog_optimize_e(stat.con, node_map, filter_nodes))
            elif isinstance(stat, ElseBegin):
                return ElseBegin(stat.sourceinfo, verilog_optimize_s(stat.stats, node_map, filter_nodes))
            else:
                return stat


        def verilog_optimize_m(m: Module) -> Module:
            node_map: Dict[str, DefNode] = {}
            filter_nodes: set = set()
            return Module(m.sourceinfo, m.name, m.instanceid, m.ports, verilog_optimize_s(m.stats, node_map, filter_nodes))        

        for m in self.c.modules:
            modules.append(verilog_optimize_m(m))
        return Circuit(self.c.sourceinfo, self.c.name, self.c.instanceid, modules)