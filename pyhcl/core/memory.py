"""PyHCL Memory define class
Include asynchronous memory and synchronous memory

Filename: memory.py
Author: SunnyChen
"""
import copy
import sys

from pyhcl.core.define import Define
from pyhcl.core.rawdata import Data, Vec, local_sytax_tree, Bits
from pyhcl.core.resources import InstanceId, HasInfo
from pyhcl.firrtl.ir import DefMem, Gender, RefId, RefMemPort, RefSubaccess, Connect, UInt, SInt


class Mem(Define):
    """PyHCL asynchronous memory class
    Memory class need Vector type
    """

    def __init__(self, size: int, element: Data):
        """Inits a Mem object
        [WARNING]: Data type can only be the ground type
        If want to use a bundle, use bundle's method to construct a
        memory from a bundle
        """
        raw_element = copy.deepcopy(element)
        # Construct a Vector type
        vector_type: Vec = Vec(size, element)
        vector_type._ir_exp.type.size = size
        # First type means the ir_exp's type, since the data is a
        # aggregate data, so second type means the aggregate data's
        # element type
        vector_type._ir_exp.type.type = raw_element._ir_exp.type
        super().__init__(vector_type)

        # Construct a Memory object
        sourceinfo = raw_element._sourceinfo
        _id = InstanceId()
        mem = DefMem(sourceinfo, "_T_" + str(_id.id), _id, vector_type._ir_exp.type, size, False)

        # Update element ref
        self._data._ir_exp = RefId(Gender.male, mem.type, True, mem)

        self._define_node = mem

    def __getitem__(self, item: Define):
        """Override Define's __getitem__() method
        Appear on the rexp -> read()
        Appear on the lexp -> write()
        """
        return self.read(item)

    def read(self, addr):
        """Built-in memory read method

        Remember to apply clock
        [WARNING]: If the memory's element type is aggregate, DO NOT USE

        Args:
            addr: Literal or other definition object, type must be UInt or SInt
        """
        # Construct a Memory Ref Definition
        # This definition must push to the local syntax tree
        exp = self._data._ir_exp
        _sourceinfo = HasInfo(sys._getframe(1))._sourceinfo
        _id = InstanceId()
        refmemport = RefMemPort(_sourceinfo, "_T_" + str(_id.id), _id, None, self._define_node, addr._data._ir_exp, True)
        local_sytax_tree.append(refmemport)

        ref = RefId(Gender.bi_gender, exp.type.type, exp.passive_type, refmemport)
        temp_data = Bits(sys._getframe())

        temp_data._ir_exp = ref
        temp_def = Define(temp_data)

        return temp_def

    def write(self, addr, value: Define):
        """Built-in memory write method

        Remember to apply clock
        [WARNING]: If the memory's element type is aggregate, DO NOT USE

        Args:
            addr: Literal or other definition object, type must be UInt or SInt
            value: The value to be write
        """
        # Construct memory port reference
        exp = self._data._ir_exp
        _sourceinfo = HasInfo(sys._getframe(1))._sourceinfo
        _id = InstanceId()
        refmemport = RefMemPort(_sourceinfo, "_T_" + str(_id.id), _id, None, self._define_node, addr._data._ir_exp, False)
        local_sytax_tree.append(refmemport)

        # Write the memory
        port_ref = RefId(Gender.bi_gender, exp.type.type, exp.passive_type, refmemport)
        connect = Connect(_sourceinfo, port_ref, value._data._ir_exp)
        local_sytax_tree.append(connect)

    def __setitem__(self, key, value):
        """Virtually override __setitem__ method, no use"""
        pass
