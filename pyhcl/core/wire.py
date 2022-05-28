"""Wire define class

Filename: wire.py
Author: SunnyChen
"""
import copy

from pyhcl.core.define import Define
from pyhcl.core.rawdata import Data
from pyhcl.core.resources import InstanceId
from pyhcl.firrtl.ir import DefWire, RefId, Gender


class Wire(Define):
    """Wire define class

    [WARNING]: Data type can only be the ground type
    """
    def __init__(self, _data: Data):
        """Inits a Wire"""
        raw_data = copy.deepcopy(_data)
        super().__init__(raw_data)
        # Construct a Wire object
        sourceinfo = raw_data._sourceinfo
        _id = InstanceId()
        wire = DefWire(sourceinfo, "_T_" + str(_id.id), _id, raw_data._ir_exp.type)

        # Update _data ref
        self._data._ir_exp = RefId(Gender.bi_gender, wire.type, True, wire)

        self._define_node = wire
