"""Register define class

Filename: reg.py
Author: SunnyChen
"""
import copy
import sys
from typing import Union
from pyhcl.core import define, rawdata
from pyhcl.core.resources import InstanceId, HasInfo
from pyhcl.firrtl import ir


class Reg(define.Define):
    """Register class, without initialized"""
    def __init__(self, _data: rawdata.Data):
        """Inits a Register without initial

        Remember to set clk -> builder.
        [WARNING]: Data type can only be the ground type
        """
        raw_data = copy.deepcopy(_data)
        super().__init__(raw_data)
        # Construct a Reg object
        sourceinfo = raw_data._sourceinfo
        _id = InstanceId()
        reg = ir.DefReg(sourceinfo, "_T_" + str(_id.id), _id, None, raw_data._ir_exp.type)

        # Update _data ref
        self._data._ir_exp = ir.RefId(ir.Gender.bi_gender, reg.type, True, reg)

        self._define_node = reg


class RegInit(define.Define):
    """Register class with initial value"""
    def __init__(self, value: Union[int, define.Define], _data: rawdata = None, clk = None, rst = None):
        """Inits a Register with initial value

        Remember to set clk and reset -> builder.

        Args:
            value: initial value
            _data: Register's type
        """
        real_clk = None if clk is None else clk._data._ir_exp
        real_rst = None if rst is None else rst._data._ir_exp

        if _data is None:
            raw_data = copy.deepcopy(value._data)
        else:
            raw_data = copy.deepcopy(_data)
        super().__init__(raw_data)
        sourceinfo = raw_data._sourceinfo
        _id = InstanceId()

        if isinstance(value, int):
            reginit = ir.DefRegReset(sourceinfo, "_T_" + str(_id.id), _id, real_clk, raw_data._ir_exp.type, real_rst,
                                     define.U(value)._data._ir_exp)
        else:
            # Define
            reginit = ir.DefRegReset(sourceinfo, "_T_" + str(_id.id), _id, real_clk, value._data._ir_exp.type, real_rst,
                                     value._data._ir_exp)

        # Update _data ref
        self._data._ir_exp = ir.RefId(ir.Gender.bi_gender, reginit.type, True, reginit)

        self._define_node = reginit
