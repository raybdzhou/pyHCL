"""IO ports for modules

Filename: ports.py
Author: SunnyChen
"""
from __future__ import annotations

import copy

from pyhcl.core import define
from pyhcl.core import rawdata
from pyhcl.core.resources import InstanceId
from pyhcl.firrtl import ir


class Port(define.Define):
    """Define module's ports <<Abstract>>

    It must take a data type (such as UInt, SInt, Clock) to construct a valid module port
    """
    def __init__(self, _data: rawdata.Data, dir: ir.Dir):
        raw_data = copy.deepcopy(_data)
        super().__init__(raw_data)
        # Normal port
        # Construct Port object
        sourceinfo = _data._sourceinfo
        _id = InstanceId()
        port = ir.Port(sourceinfo, "_T_" + str(_id.id), _id, dir, _data._ir_exp.type)
        # builder.syntax_tree.append(port)

        # Update _data ref
        self._data._ir_exp = ir.RefId(ir.Gender.male, port.type, True, port)

        self._define_node = port


class Input(Port):
    """Define Input port"""
    def __init__(self, _data: rawdata.Data):
        """Inits a Input port"""
        raw_data = copy.deepcopy(_data)
        super().__init__(raw_data, ir.Dir.Input)
        if isinstance(_data, rawdata.Element):
            self._data._ir_exp.gender = ir.Gender.male    # Input port: male
        elif isinstance(_data, rawdata.Record):
            pass


class Output(Port):
    """Define Output port"""
    def __init__(self, _data: rawdata.Data):
        """Inits a Input port"""
        raw_data = copy.deepcopy(_data)
        super().__init__(raw_data, ir.Dir.Output)
        if isinstance(_data, rawdata.Element):
            self._data._ir_exp.gender = ir.Gender.female  # Input port: female
        elif isinstance(_data, rawdata.Record):
            pass
