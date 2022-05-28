"""ListLookup util for PyHCL

Filename: listlookup.py
Author: SunnyChen
"""
import sys
from typing import List
from pyhcl.core.define import Define
from pyhcl.core.resources import HasInfo, InstanceId
from pyhcl.util import utils_func
from pyhcl.core import rawdata
from pyhcl.firrtl import ir


def ListLookup(addr: Define, default: List, dictionary: dict) -> List:
    """Built-in ListLookup function

    ListLookup is useful in generating control signals

    Args:
        addr: Indicate the address of the list
        default: Default list case
        dictionary: Map the address to the list

    Return:
        A control signal list
    """
    stack = []
    ret_list = []
    equal_map = {}
    sourceinfo = HasInfo(sys._getframe(1))._sourceinfo

    # Append all statements in the list
    # for i in default:
    #     iexp = i._data._ir_exp
    #     utils_func.search_def(iexp, stack)
    #
    # rawdata.local_sytax_tree.extend(stack)
    # stack.clear()
    #
    # for k, v in dictionary.items():
    #     # v is a list
    #     for i in v:
    #         iexp = i._data._ir_exp
    #         utils_func.search_def(iexp, stack)
    #
    # rawdata.local_sytax_tree.extend(stack)
    # stack.clear()

    # Append equal test statements
    for k, v in dictionary.items():
        con_node_ref = (addr == k)._data._ir_exp
        equal_map[k] = con_node_ref

    # Construct the return list
    for i in range(0, len(default)):
        prv_node_ref = default[i]._data._ir_exp
        search_list = []
        for k, v in dictionary.items():
            search_list.append(k)

        search_list = search_list[::-1]
        for k in search_list:
            v = dictionary[k]
            mux_op = ir.Mux(ir.Gender.male, ir.Type(), True, equal_map[k], v[i]._data._ir_exp, prv_node_ref)
            _id = InstanceId()
            mux_node = ir.DefNode(sourceinfo, "_T_" + str(_id.id), _id, mux_op)
            prv_node_ref = ir.RefId(ir.Gender.male, mux_node.node_exp.type, True, mux_node)

            rawdata.local_sytax_tree.append(mux_node)

        raw_data = rawdata.Bits(sys._getframe(1))
        raw_data._ir_exp = prv_node_ref
        def_node = Define(raw_data)

        ret_list.append(def_node)

    return ret_list
