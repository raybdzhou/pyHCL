from pyhcl.firrtl.ir import *
from typing import List, Dict
from dataclasses import dataclass
from pyhcl.firrtl.passes.namespace import Namespace

@dataclass
class ExpandSequential:
    c: Circuit

    def run(self, namespace: Namespace):
        modules: List[Module] = []
        blocks: List[CmdStat] = []
        block_map: Dict[str, List[CmdStat]] = {}
        clock_map: Dict[str, Exp] = {}

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

        def expand_sequential_s(stat: CmdStat, stats: List[DefStat], reg_map: Dict[str, DefStat]) -> CmdStat:
            if isinstance(stat, When):
                com_stats: List[DefStat] = []
                seq_stats_map: Dict[str, List[DefStat]] = {}
                for s in stat.stats:
                    if isinstance(s, Connect) and get_ref_name(s.lexp) in reg_map:
                        reg = reg_map[get_ref_name(s.lexp)]
                        if reg.clk.emit_verilog() not in clock_map:
                            clock_map[reg.clk.emit_verilog()] = reg.clk
                        if reg.clk.emit_verilog() not in seq_stats_map:
                            seq_stats_map[reg.clk.emit_verilog()] = []
                        seq_stats_map[reg.clk.emit_verilog()].append(Connect(s.sourceinfo, s.lexp, s.rexp, False))
                    elif isinstance(s, Connect) and get_ref_name(s.lexp) not in reg_map:
                        com_stats.append(s)
                    elif isinstance(s, When):
                        seq_when_map, com_when = expand_sequential_s(s, stats, reg_map)
                        for k in seq_when_map:
                            if k not in seq_stats_map:
                                seq_stats_map[k] = []
                            seq_stats_map[k].append(seq_when_map[k])
                        com_stats.append(com_when)
                    else:
                        stats.append(s)
                seq_else_map, com_else = expand_sequential_s(stat.elsebegin, stats, reg_map)
                for k in seq_stats_map:
                    if k not in seq_else_map:
                        seq_else_map[k] = None
                return {k: When(stat.sourceinfo, stat.whenbegin, stat.whenend, stat.has_else, seq_else_map[k], stat.elseend, v) for k, v in seq_stats_map.items()}, \
                    When(stat.sourceinfo, stat.whenbegin, stat.has_else, stat.has_else, com_else, stat.elseend, com_stats)
            elif isinstance(stat, ElseBegin):
                com_stats: List[DefStat] = []
                seq_stats_map: Dict[str, List[DefStat]] = {}
                for s in stat.stats:
                    if isinstance(s, Connect) and get_ref_name(s.lexp) in reg_map:
                        reg = reg_map[get_ref_name(s.lexp)]
                        if reg.clk.emit_verilog() not in clock_map:
                            clock_map[reg.clk.emit_verilog()] = reg.clk
                        if reg.clk.emit_verilog() not in seq_stats_map:
                            seq_stats_map[reg.clk.emit_verilog()] = []
                        seq_stats_map[reg.clk.emit_verilog()].append(Connect(s.sourceinfo, s.lexp, s.rexp, False))
                    elif isinstance(s, Connect) and get_ref_name(s.lexp) not in reg_map:
                        com_stats.append(s)
                    elif isinstance(s, When):
                        seq_when_map, com_when = expand_sequential_s(s, stats, reg_map)
                        for k in seq_when_map:
                            if k not in seq_stats_map:
                                seq_stats_map[k] = []
                            seq_stats_map[k].append(seq_when_map[k])
                        com_stats.append(com_when)
                    else:
                        stats.append(s)
                return {k: ElseBegin(stat.sourceinfo, v) for k, v in seq_stats_map.items()}, ElseBegin(stat.sourceinfo, com_stats)
            else:
                return {}, stat

        def expand_sequential(stats: List[DefStat]) -> List[DefStat]:
            reg_map: Dict[str, DefStat] = {s.name: s for s in stats if isinstance(s, (DefReg, DefRegReset))}
            mem_map: Dict[str, DefStat] = {s.name: s for s in stats if isinstance(s, RefMemPort)}
            new_stats: List[DefStat] = []
            for stat in stats:
                if isinstance(stat, When):
                    seq_map, com = expand_sequential_s(stat, new_stats, reg_map)
                    if len(com.stats) > 0:
                        new_stats.append(com)
                    for k in seq_map:
                        if k not in block_map:
                            block_map[k] = []
                        if len(seq_map[k].stats) > 0:
                            block_map[k].append(seq_map[k])
                else:
                    new_stats.append(stat)
            reset_map: Dict[str, List[DefStat]] = {}
            reset_sign_map: Dict[str, List[Exp]] = {}
            for reg_name in reg_map:
                reg = reg_map[reg_name]
                if isinstance(reg, DefRegReset):
                    if reg.clk.emit_verilog() not in reset_map:
                        reset_map[reg.clk.emit_verilog()] = []
                    reset_map[reg.clk.emit_verilog()].append(Connect(None, RefId(Gender.undefined, reg.type, True, reg), reg.reset_value, False))
                    if reg.clk.emit_verilog() not in reset_sign_map:
                        reset_sign_map[reg.clk.emit_verilog()] = []
                    reset_sign_map[reg.clk.emit_verilog()].append(reg.reset_signal)
            for k in reset_map:
                if len(reset_map[k]) > 0:
                    for rs in reset_sign_map[k]:
                        block_map[k].append(When(None, WhenBegin(None, rs), WhenEnd(), False, None, None, reset_map[k]))
            for k in mem_map:
                sig = Op(Gender.male, UInt(1), True, "and", [RefId(Gender.undefined, UInt(1), True, DefWire(None, f"{mem_map[k].refmem.name}_{k}_en", None, UInt(1))),
                RefId(Gender.undefined, UInt(1), True, DefWire(None, f"{mem_map[k].refmem.name}_{k}_mask"))], [])
                con = Connect(None, RefSubaccess(Gender.undefined, mem_map[k].refmem.type, True, mem_map[k].refmem, RefId(Gender.undefined, 
                mem_map[k].addr.type, True, DefWire(None, f"{mem_map[k].refmem.name}_{k}_addr", None, mem_map[k].addr.type))), RefId(Gender.undefined, 
                mem_map[k].refmem.type, True, DefWire(None, f"{mem_map[k].refmem.name}_{k}_data", None, mem_map[k].refmem.type)), False)
                if mem_map[k].read_or_write is False:
                    if mem_map[k].clk.emit_verilog()  not in block_map:
                        block_map[mem_map[k].clk.emit_verilog()] = []
                    if mem_map[k].clk.emit_verilog() not in clock_map:
                        clock_map[mem_map[k].clk.emit_verilog()] = mem_map[k].clk
                    block_map[mem_map[k].clk.emit_verilog()].append(When(None, WhenBegin(None, sig), WhenEnd(), False, None, None, [con]))
            for k in block_map:
                new_stats.append(AlwaysBlock(None, block_map[k], clock_map[k]))
            return new_stats

        def expand_sequential_m(m: Module) -> Module:
            return Module(m.sourceinfo, m.name, m.instanceid, m.ports, expand_sequential(m.stats))

        for m in self.c.modules:
            modules.append(expand_sequential_m(m))
        return Circuit(self.c.sourceinfo, self.c.name, self.c.instanceid, modules)