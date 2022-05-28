"""RawModule definition class

Filename: rawmodule.py
Author  : SunnyChen
"""
from __future__ import annotations

import copy
import sys
import time

from pyhcl.core import ports
from pyhcl.core import rawdata
from pyhcl.core.bundle import Bundle
from pyhcl.core.define import Define, Node
from pyhcl.core.ports import Port
from pyhcl.core.resources import InstanceId, HasInfo
from pyhcl.firrtl import ir


modules_list = []

def inherit(*basecls):
    """Must excute when define your own module and inherit form self-define module

    Attributes:
        *basecls: classes to be inherited
    """
    # Search the inherit chain
    # Could inherit multi classes
    pass


# class IO(Bundle):
#     """Module's IO, must be implemented"""
#     def __init__(self):
#         super().__init__()
#         self._data = rawdata.Data(sys._getframe(1))
#         self._define_node = ir.Definition()
#
#     def fix(self):
#         """Fix the ports ref"""
#         for k in self.__dict__:
#             if not k.startswith("_") and not k.startswith("__"):
#                 obj = self.__dict__[k]
#                 exp = obj._data._ir_exp
#                 obj._data._ir_exp = ir.RefSubfield(exp.gender, exp.type, exp.passive_type, None, None)
#
#         return self


# def IO(bundle):
#     """Wrap the bundle object"""
#     # Monkey Patch
#
#     # Fix fields' references
#     for k in bundle.__dict__:
#         if not k.startswith("_") and not k.startswith("__"):
#             obj = bundle.__dict__[k]
#             exp = obj._data._ir_exp
#             obj._data._ir_exp = ir.RefSubfield(exp.gender, exp.type, exp.passive_type, None, None)
#
#     return bundle


def update_submodule(submodule: Module, upper_node):
    """Update submodule's ref"""
    for k in submodule.__dict__:
        if not k.startswith("_") and not k.startswith("__"):
            obj = submodule.__dict__[k]
            if not isinstance(obj, Module):
                if isinstance(obj, Bundle):
                    exp = obj._data._ir_exp
                    refmodule = ir.RefId(ir.Gender.undefined, None, False, upper_node)
                    refsubfield = ir.RefSubfield(exp.gender, exp.type, exp.passive_type, refmodule, exp)
                    obj._data._ir_exp = refsubfield
                    obj.update_subfield(refsubfield)
                elif isinstance(obj, Port):
                    exp = obj._data._ir_exp
                    refmodule = ir.RefId(ir.Gender.undefined, None, False, upper_node)
                    refsubfield = ir.RefSubfield(exp.gender, exp.type, exp.passive_type, refmodule, exp)
                    obj._data._ir_exp = refsubfield
                pass


class Module(HasInfo):
    """Abstract Class for module definition

    The definition statements must be the class variables, all command statements must write
    in stat method

    Attributes:
        define_node: Module's define node
    """

    def __init__(self):
        """Inits a module"""
        # Construct Module node
        super().__init__(sys._getframe(1))
        self.clock = ports.Input(rawdata.Clock())
        self.reset = ports.Input(rawdata.UInt(1))
        _id = InstanceId()
        self._define_node = ir.Module(self._sourceinfo, "_T_" + str(_id.id), _id)

    def gen(self):
        """Construct submodule
        If init a module inside a module, must indicate the upper module's node
        """

        self.build_syntax_tree()

        for i in list(filter(lambda x: isinstance(x, ir.RefMemPort), rawdata.local_sytax_tree)):
            i.clk = self.clock._data._ir_exp
        self._define_node.stats.extend(rawdata.local_sytax_tree)
        rawdata.local_sytax_tree.clear()

        # update_submodule(self, self._define_node)

        # modules_list.append(self._define_node)

        return self

    def build_syntax_tree(self):
        """Build the syntax tree from current module class"""
        # Get Module's clock and reset first
        clk = self.clock
        rst = self.reset
        # # build IO
        # obj_list = []
        # for k in module.__dict__:
        #     if not k.startswith("_") and not k.startswith("__"):
        #         obj_list.append(module.__dict__[k])
        # io_obj_list = list(filter(lambda x: isinstance(x, Bundle), obj_list))
        # if len(io_obj_list) > 1 or len(io_obj_list) <= 0:
        #     print("[WARNING]: module's IO invalid")
        # io_obj = io_obj_list[0]

        for k in self.__dict__:
            if not k.startswith("__") and not k.startswith("_"):
                # New class value or Overwrite a base class's value
                # Fill name space
                obj = self.__dict__[k]
                node = obj._define_node
                node.name = k

                # If it is a module
                if isinstance(obj, Module):
                    new_node = copy.deepcopy(node)
                    new_node.name = obj.__class__.__name__
                    instmodule = ir.InstModule(None, k, InstanceId(), new_node)
                    self._define_node.stats.append(instmodule)

                    modules_list.append(new_node)

                    update_submodule(obj, obj._define_node)

                    clk_connect = ir.Connect(HasInfo(sys._getframe(1))._sourceinfo, obj.clock._data._ir_exp,
                               self.clock._data._ir_exp)
                    rst_connect = ir.Connect(HasInfo(sys._getframe(1))._sourceinfo, obj.reset._data._ir_exp,
                               self.reset._data._ir_exp)
                    self._define_node.stats.extend([clk_connect, rst_connect])

                    # Update submodule's ref
                    # update_submodule(obj, self._define_node)

                # If it is a register, fill the clk attr
                if isinstance(node, ir.DefReg) or isinstance(node, ir.DefRegReset):
                    if node.clk is None:
                        node.clk = clk._data._ir_exp
                    if isinstance(node, ir.DefRegReset):
                        if node.reset_signal is None:
                            node.reset_signal = rst._data._ir_exp

                # Attach current definition to module
                # TODO(SunnyChen): If a submodule? a Bundle?
                if isinstance(obj, Port) or isinstance(obj, Bundle) and isinstance(obj._define_node, ir.Port):
                    self._define_node.ports.append(node)
                elif not isinstance(obj, Module) and not isinstance(obj, Node):
                    self._define_node.stats.append(node)

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
