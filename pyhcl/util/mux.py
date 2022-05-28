"""Mux function definition file

Include basic mux function and complex muxlookup function

Filename: mux.py
Author: SunnyChen
"""
import sys

from pyhcl.core import rawdata
from pyhcl.core.define import Define
from pyhcl.core.resources import HasInfo, InstanceId
from pyhcl.firrtl import ir
from pyhcl.util import utils_func


def Mux(condition: Define, true_define: Define, false_define: Define):
    """Built-in basic mux function

    [WARNING]: Temporary only support ground type
    """
    # Construct Mux expression
    mux_exp = ir.Mux(ir.Gender.male, ir.Type(), True, condition._data._ir_exp,
                     true_define._data._ir_exp, false_define._data._ir_exp)

    # Construct internal node
    sourceinfo = HasInfo(sys._getframe(1))._sourceinfo
    _id = InstanceId()
    node = ir.DefNode(sourceinfo, "_T_" + str(_id.id), _id, mux_exp)

    # Create node reference
    node_ref = ir.RefId(ir.Gender.male, node.node_exp.type, True, node)
    raw_data = rawdata.Bits(sys._getframe(1))
    raw_data._ir_exp = node_ref
    def_node = Define(raw_data)

    rawdata.local_sytax_tree.append(node)

    return def_node


def MuxLookUp(key: Define, default: Define, dictionary: dict):
    """Built-in advanced mux function

    Args:
        key: Indicate the key value of the dict
        default: Default case value
        dictionary: Map the key value to the case value
    """
    stack = []
    sourceinfo = HasInfo(sys._getframe(1))._sourceinfo

    # Append all statements
    # for k, v in dictionary.items():
    #     iexp = v._data._ir_exp
    #     utils_func.search_def(iexp, stack)
    #
    # rawdata.local_sytax_tree.extend(stack)
    # stack.clear()

    # Recursively append mux statements
    prv_node_ref = default._data._ir_exp
    search_list = []
    for k, v in dictionary.items():
        # eq(key, k)
        search_list.append(k)

    search_list = search_list[::-1]

    for k in search_list:
        v = dictionary[k]
        con_node_ref = (key == k)._data._ir_exp
        # eq_op = ir.Op(ir.Gender.male, ir.UInt(1), True, "eq", [key._data._ir_exp, k._data._ir_exp], [])
        # _id = InstanceId()
        # eq_node = ir.DefNode(sourceinfo, "_T_" + str(_id.id), _id, eq_op)
        # con_node_ref = ir.RefId(ir.Gender.male, eq_node.node_exp.type, True, eq_node)

        # mux(con, current, prv)
        mux_op = ir.Mux(ir.Gender.male, ir.Type(), True, con_node_ref, v._data._ir_exp, prv_node_ref)
        _id = InstanceId()
        mux_node = ir.DefNode(sourceinfo, "_T_" + str(_id.id), _id, mux_op)
        prv_node_ref = ir.RefId(ir.Gender.male, mux_node.node_exp.type, True, mux_node)

        rawdata.local_sytax_tree.append(mux_node)

    # Return definition
    raw_data = rawdata.Bits(sys._getframe(1))
    raw_data._ir_exp = prv_node_ref
    def_node = Define(raw_data)

    return def_node
