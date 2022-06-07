"""Builder of the framework

Filename: builder.py
Author  : SunnyChen
"""
from __future__ import annotations

import os
from typing import List

from pyhcl.core.bundle import Bundle
from pyhcl.core.ports import Port
from pyhcl.core.rawmodule import Module, modules_list
from pyhcl.firrtl import ir
from pyhcl.firrtl.passes.auto_inferring import AutoInferring
from pyhcl.firrtl.passes.expand_aggregate import ExpandAggregate
from pyhcl.firrtl.passes.expand_sequential import ExpandSequential
from pyhcl.firrtl.passes.namespace import Namespace
from pyhcl.firrtl.passes.remove_access import RemoveAccess
from pyhcl.firrtl.passes.replace_subaccess import ReplaceSubaccess
from pyhcl.firrtl.passes.verilog_optimize import VerilogOptimize

syntax_tree = []
# If a self-define module override a var from base class
# Throw a warning
# override_warning = False


def auto_name(l: List):
    """Auto construct internal nodes' name"""
    for i in range(0, len(l)):
        if isinstance(l[i], ir.Definition):
            l[i].name = "_T_" + str(l[i].instanceid.id)


# def construct_io(io_obj):
#     # Append fields
#     # Get ports
#     for k in io_obj.__dict__:
#         if not k.startswith("_") and not k.startswith("__"):
#             port = io_obj.__dict__[k]
#             if isinstance(port, Bundle):
#                 construct_io(port)
#             else:
#                 node = port._define_node
#                 node.name = k
#                 if isinstance(port, Input):
#                     field = ir.Field(node.sourceinfo, node.name, node.instanceid, True, node.type)
#                 elif isinstance(port, Output):
#                     field = ir.Field(node.sourceinfo, node.name, node.instanceid, False, node.type)
#                 io_obj._agg_type.fields.append(field)
#
#                 # # change _define_node ref
#                 # old_exp = port._data._ir_exp
#                 # port._data._ir_exp = ir.RefSubfield(old_exp.gender, old_exp.type, old_exp.passive_type,
#                 #                                     io_obj._define_node, field)
#                 port._data._ir_exp.ref_arg = io_obj._define_node
#                 port._data._ir_exp.ref_field = field


def build_syntax_tree(module):
    """Build the syntax tree from current module class"""
    # Get Module's clock and reset first
    clk = module.clock
    rst = module.reset

    # # build IO
    # obj_list = []
    # for k in module.__dict__:
    #     if not k.startswith("_") and not k.startswith("__"):
    #         obj_list.append(module.__dict__[k])
    # io_obj_list = list(filter(lambda x: isinstance(x, Bundle), obj_list))
    # if len(io_obj_list) > 1 or len(io_obj_list) <= 0:
    #     print("[WARNING]: module's IO invalid")
    # io_obj = io_obj_list[0]

    for k in module.__dict__:
        if not k.startswith("__") and not k.startswith("_"):
            # New class value or Overwrite a base class's value
            # Fill name space
            obj = module.__dict__[k]
            node = obj._define_node
            node.name = k

            # # If it is a module
            # if isinstance(obj, Module):
            #     build_syntax_tree(obj, circuit)
            #     circuit.modules.append(obj._define_node)
            #     # Inst module
            #     instmodule = ir.InstModule(None, k, InstanceId(), obj._define_node)
            #     module._define_node.stats.append(instmodule)

            # If it is a register, fill the clk attr
            if isinstance(node, ir.DefReg) or isinstance(node, ir.DefRegReset):
                node.clk = clk._data._ir_exp
                if isinstance(node, ir.DefRegReset):
                    node.reset_signal = rst._data._ir_exp

            # Attach current definition to module
            # TODO(SunnyChen): If a submodule? a Bundle?
            if isinstance(obj, Port) or isinstance(obj, Bundle) and isinstance(obj._define_node, ir.Port):
                module._define_node.ports.append(node)
            elif not isinstance(obj, Module):
                module._define_node.stats.append(node)
            syntax_tree.append(node)

    # temp_output = Output(io_obj)
    # io_obj._define_node = temp_output._define_node
    # io_obj._data = temp_output._data
    #
    # construct_io(io_obj)

    # Push command statements now
    # auto_name(local_sytax_tree)
    # If a memory port ref exit, attach clock to the port definition
    # for i in list(filter(lambda x: isinstance(x, ir.RefMemPort), local_sytax_tree)):
    #     i.clk = clk._data._ir_exp
    # module._define_node.stats.extend(local_sytax_tree)
    # local_sytax_tree.clear()


# def push_cmdstat(toplv_class, toplv_node):
#     if syntax_map.get(toplv_class.__name__, None) is None:
#         return
#     cmd_list = syntax_map[toplv_class.__name__]
#     auto_name(cmd_list)
#     toplv_node.stats.extend(cmd_list)
#     for i in cmd_list:
#         if isinstance(i, ir.Definition):
#             toplv_node.instanceid.add_child(i.instanceid.id)
#             i.instanceid.add_parent(toplv_node.instanceid.id)


def elaborate(module) -> ir.Circuit:
    """Elaborate the module's definition.
    The module must be the top level module.
    """
    # Timer
    # print("[%f] Start elaborate" % 0)
    # start = time.time()

    # Get all attributes of current module
    attr_list = list(filter(lambda x: not x.startswith("__") and not x.startswith("_") and not x == "stat",
                     list(module.__dir__())))
    # build_map = dict.fromkeys(attr_list, False)

    # First construct top level circuit and module
    toplv_node = module._define_node
    toplv_node.name = module.__class__.__name__
    circuit = ir.Circuit(toplv_node.sourceinfo, module.__class__.__name__, toplv_node.instanceid)

    # toplv_class = module.__class__

    # Construct clock and reset signal first
    # User should not define their own clock and reset signal
    # Module.clock.define_node.name = "clock"
    # Module.reset.define_node.name = "reset"
    # toplv_node.ports.extend([Module.clock.define_node, Module.reset.define_node])
    # build_map["clock"] = True
    # build_map["reset"] = True

    # From the top level module to construct all the components
    # Append definition first
    # build_syntax_tree(module)

    # Search till the base Module class
    # Statements must generate from base class to current class
    # base_cls = toplv_class
    # search_list = list(filter(lambda x: x != HasInfo and x != object and x != toplv_class, base_cls.__mro__))
    # for i in search_list:
    #     build_syntax_tree(i, toplv_node, build_map)
    #     push_cmdstat(i, toplv_node)
    # while base_cls != Module:
    #     base_cls = base_cls.__bases__[0]
    #     build_syntax_tree(base_cls, toplv_node, build_map)
    #
    #     if base_cls != Module:
    #         push_cmdstat(base_cls, toplv_node)

    # Push command statements
    # push_cmdstat(toplv_class, toplv_node)

    # for i in syntax_tree:
    #     print(i, end='\n')

    # Attach
    for i in modules_list:
        circuit.modules.append(i)
        circuit.instanceid.add_child(i.instanceid.id)
        i.instanceid.add_parent(circuit.instanceid.id)

    # Attach top level module
    circuit.modules.append(module._define_node)
    circuit.instanceid.add_child(module._define_node.instanceid.id)
    module._define_node.instanceid.add_parent(circuit.instanceid.id)

    # Print elaboration time
    # elapsed = time.time() - start
    # print("[%f] Done elaboration" % elapsed)

    return circuit


def emit(circuit: ir.Circuit, filename: str):
    """From syntax tree to emit FIRRTL code"""
    # From circuit, if the first element is not a circuit, raise a Error
    s = circuit.emit()

    if not os.path.exists('.fir'):
        os.mkdir('.fir')
    f = os.path.join('.fir', filename)
    with open(f, "w+") as fir_file:
        fir_file.write(s)
    
    return f

def emit_verilog(circuit: ir.Circuit, filename: str):
    """From syntax tree to emit Verilog code"""
    # From circuit, if the first element is not a circuit, raise a Error
    namespace = Namespace()
    circuit = AutoInferring(circuit).run(namespace)
    circuit = ExpandAggregate(circuit).run(namespace)
    circuit = ReplaceSubaccess(circuit).run(namespace)
    circuit = RemoveAccess(circuit).run(namespace)
    circuit = VerilogOptimize(circuit).run(namespace)
    circuit = ExpandSequential(circuit).run(namespace)
    s = circuit.emit_verilog()

    if not os.path.exists('.v'):
        os.mkdir('.v')
    f = os.path.join('.v', filename)
    with open(f, "w+") as fir_file:
        fir_file.write(s)
    
    return f


def dumpverilog(fir_file, vfile):
    """Dump FIRRTL source code to verilog
    Use built-in firrtl compiler
    """
    os.system("firrtl -i %s -o %s -X verilog" % (fir_file, vfile))
