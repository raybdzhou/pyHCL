"""Bundle for PyHCL

Filename: bundle.py
Author: SunnyChen
"""
from __future__ import annotations

import copy
import sys

from pyhcl.core.define import Define
from pyhcl.core import rawdata
from pyhcl.core.memory import Mem
from pyhcl.core.ports import Port, Input, Output
from pyhcl.core.reg import Reg, RegInit
from pyhcl.core.resources import InstanceId, HasInfo
from pyhcl.core.wire import Wire
from pyhcl.firrtl import ir
from pyhcl.firrtl.ir import Vector


def Field(_data: rawdata.Data):
    """Wrap a data type to a definition"""
    return Define(_data)


# def update_ref_arg(bundle, refmemport):
#     """For bundle type to recursively update their fields' ref_arg"""
#     for k in bundle.__dict__:
#         if not k.startswith("_") and not k.startswith("__"):
#             obj = bundle.__dict__[k]
#             if not isinstance(obj, Bundle):
#                 # Not bundle, ground field
#                 obj._data._ir_exp.ref_arg = ir.RefId(ir.Gender.bi_gender, obj._data._ir_exp.type,
#                                                      obj._data._ir_exp.passive_type, refmemport)
#             # else:
#             #     update_ref_arg(obj, refmemport)


class Bundle(Define):
    """Bundle define data class"""
    def __init__(self):
        """Inits a Bundle object
        **Call at last**
        """
        super().__init__(rawdata.Record(sys._getframe(1)))

    def update_subfield(self, refsubfield):
        for k in self.__dict__:
            if not k.startswith("_") and not k.startswith("__"):
                obj = self.__dict__[k]
                gender = obj._data._ir_exp.gender
                refsubfield.gender = gender
                obj._data._ir_exp.ref_arg = refsubfield
                if isinstance(obj, Bundle):
                    obj.update_subfield(obj._data._ir_exp)

    def append_bundle(self, type_cls):
        for k in self.__dict__:
            if not k.startswith("_") and not k.startswith("__"):
                obj = self.__dict__[k]

                node = obj._define_node
                node.name = k
                # Update port's reference
                exp = obj._data._ir_exp

                # Construct port's field
                if isinstance(obj, Input):
                    if not hasattr(obj, "_flip"):
                        field = ir.Field(node.sourceinfo, k, node.instanceid, True, node.type)
                    else:
                        field = ir.Field(node.sourceinfo, k, node.instanceid, False, node.type)
                    subfield = ir.RefSubfield(ir.Gender.male, exp.type, exp.passive_type, self._data._ir_exp,
                                              field)
                elif isinstance(obj, Output):
                    if not hasattr(obj, "_flip"):
                        field = ir.Field(node.sourceinfo, k, node.instanceid, False, node.type)
                    else:
                        field = ir.Field(node.sourceinfo, k, node.instanceid, True, node.type)
                    subfield = ir.RefSubfield(ir.Gender.female, exp.type, exp.passive_type, self._data._ir_exp,
                                              field)
                else:
                    if not hasattr(obj, "_flip"):
                        field = ir.Field(obj._data._sourceinfo, k, InstanceId(), False, obj._data._ir_exp.type)
                    else:
                        field = ir.Field(obj._data._sourceinfo, k, InstanceId(), True, obj._data._ir_exp.type)
                    # ref = ir.RefId(ir.Gender.bi_gender, self._data.type, self._data.passive_type,
                    #                self._define_node)
                    subfield = ir.RefSubfield(ir.Gender.bi_gender, exp.type, exp.passive_type, self._data._ir_exp,
                                              field)

                obj._data._ir_exp = subfield

                # If is a bundle, update the subfield
                if isinstance(obj, Bundle):
                    if type_cls.__name__ == "Reg":
                        obj.Reg(True)
                    elif type_cls.__name__ == "Port":
                        obj.IO(True)
                    elif type_cls.__name__ == "Wire":
                        obj.Wire(True)
                    elif type_cls.__name__ == "Mem":
                        obj.Mem(128, True)
                    obj.update_subfield(subfield)
                if not isinstance(obj, Bundle):
                    if isinstance(self._define_node.type, Vector):
                        self._define_node.type.type.fields.append(field)
                    else:
                        self._define_node.type.fields.append(field)
                else:
                    field.type = obj._define_node.type
                    if isinstance(self._define_node.type, Vector):
                        self._define_node.type.type.fields.append(field)
                    else:
                        self._define_node.type.fields.append(field)
                    pass

    def IO(self, flag=False):
        """From bundle to construct a IO object
        First construct a Output port

        Args:
            flag: Indicate call from user's code or inner constructor
        """
        if not flag:
            if not hasattr(self, "_flip"):
                self._define_node = Output(self._data)._define_node
            else:
                self._define_node = Input(self._data)._define_node
            self._data._ir_exp = ir.RefId(ir.Gender.bi_gender, self._data._ir_exp.type, self._data._ir_exp.passive_type,
                                          self._define_node)
            pass
        else:
            self._define_node = Output(rawdata.Record(sys._getframe(1)))._define_node
        # Append to bundle
        # for k in self.__dict__:
        #     if not k.startswith("_") and not k.startswith("__"):
        #         obj = self.__dict__[k]
        #         node = obj._define_node
        #         node.name = k
        #         # Update port's reference
        #         exp = obj._data._ir_exp
        #
        #         # Construct port's field
        #         if isinstance(obj, Input):
        #             field = ir.Field(node.sourceinfo, k, node.instanceid, True, node.type)
        #         else:
        #             field = ir.Field(node.sourceinfo, k, node.instanceid, False, node.type)
        #         subfield = ir.RefSubfield(exp.gender, exp.type, exp.passive_type, self._data._ir_exp, field)
        #         obj._data._ir_exp = subfield
        #
        #         # If is a bundle, update the subfield
        #         if isinstance(obj, Bundle):
        #             obj.update_subfield(subfield)
        #         self._define_node.type.fields.append(field)
        self.append_bundle(Port)
        return self

    # TODO(SunnyChen): Bundle to other type definition
    def Reg(self, flag=False):
        """From Bundle to construct Register (without reset value)
        RegInit cannot use in Bundle, must be a ground type
        """
        if not flag:
            self._define_node = Reg(self._data)._define_node
            self._data._ir_exp = ir.RefId(ir.Gender.bi_gender, self._data._ir_exp.type, self._data._ir_exp.passive_type,
                                          self._define_node)
        else:
            self._define_node = Reg(rawdata.Record(sys._getframe(1)))._define_node
        # Append to Bundle
        self.append_bundle(Reg)
        return self

    def Wire(self, flag=False):
        """From Bundle to construct Wire"""
        if not flag:
            self._define_node = Wire(self._data)._define_node
            self._data._ir_exp = ir.RefId(ir.Gender.bi_gender, self._data._ir_exp.type, self._data._ir_exp.passive_type,
                                          self._define_node)
        else:
            self._define_node = Wire(rawdata.Record(sys._getframe(1)))._define_node
        # Append to Bundle
        self.append_bundle(Wire)
        return self

    def Mem(self, size: int, flag=False):
        """From Bundle to construct Mem"""
        self._define_node = Mem(size, self._data)._define_node
        if flag:
            self._define_node.type = ir.Bundle()
        # Append to Bundle
        self.append_bundle(Mem)
        return self

    def __getitem__(self, item: Define):
        """Override Define class __getitem__() method

        Args:
            item: core's UInt or SInt type definition(ref)
        """
        # Construct RefMemPort Definition
        # Push to local syntax tree
        _sourceinfo = HasInfo(sys._getframe(1))._sourceinfo
        _id = InstanceId()
        refmemport = ir.RefMemPort(_sourceinfo, "_T_" + str(_id.id), _id, None, self._define_node, item._data._ir_exp, True, True)
        rawdata.local_sytax_tree.append(refmemport)

        # Temporary change all field's ref
        for k in self.__dict__:
            if not k.startswith("_") and not k.startswith("__"):
                obj = self.__dict__[k]
                # Not bundle, ground field
                obj._data._ir_exp.ref_arg = ir.RefId(ir.Gender.bi_gender, obj._data._ir_exp.type,
                                                     obj._data._ir_exp.passive_type, refmemport)

        return copy.deepcopy(self)

    def __setitem__(self, key, value):
        pass

    def flip(self):
        """Mark as flip"""
        self._flip = True
        return self

    def __matmul__(self, other):
        for i in self.__dict__:
            if not i.startswith("_") and not i.startswith("__"):
                for k in other.__dict__:
                    if not k.startswith("_") and not k.startswith("__"):
                        if i == k:
                            if i == "clock" or i == "reset":
                                continue

                            self_object = self.__dict__[i]
                            other_object = other.__dict__[k]
                            if isinstance(self_object, Input) and isinstance(other_object, Output):
                                self_object @= other_object
                            elif isinstance(self_object, Output) and isinstance(other_object, Input):
                                other_object @= self_object
    
    def decoupled(self, name, type):
        self.__dict__[name+"_valid"] = Output(rawdata.UInt(1))
        self.__dict__[name+"_ready"] = Input(rawdata.UInt(1))
        self.__dict__[name] = Output(type)
