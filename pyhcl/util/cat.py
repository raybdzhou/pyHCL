"""PyHCL utils cat

Filename: cat.py
Author: SunnyChen
"""
import sys

from pyhcl.core import rawdata
from pyhcl.core.define import Define
from pyhcl.core.resources import HasInfo, InstanceId
from pyhcl.firrtl import ir


def Cat(*cat_list):
    """Built-in cat function

    [WARNING]: Temporary only support ground type
    """
    clist = cat_list
    clist_len = len(clist)
    # print(clist_len)

    # Construct Cat Expression
    if clist_len == 0:
        raise ValueError("No element in cat list")
    elif clist_len == 1:
        return cat_list[0]
    elif clist_len >= 2:
        cat_index = 0
        prv_node = None
        last_node = None
        while cat_index < clist_len - 1:
            # Construct Cat expression
            if prv_node is None:
                cat_op = ir.Op(ir.Gender.male, ir.Type(), True, "cat",
                               [clist[cat_index]._data._ir_exp, clist[cat_index+1]._data._ir_exp], [])
            else:
                cat_op = ir.Op(ir.Gender.male, ir.Type(), True, "cat",
                               [prv_node, clist[cat_index + 1]._data._ir_exp], [])

            # Construct internal node
            sourceinfo = HasInfo(sys._getframe(1))._sourceinfo
            _id = InstanceId()
            node = ir.DefNode(sourceinfo, "_T_" + str(_id.id), _id, cat_op)
            inter_node_ref = ir.RefId(ir.Gender.male, node.node_exp.type, True, node)

            prv_node = inter_node_ref
            rawdata.local_sytax_tree.append(node)

            if cat_index == clist_len - 2:
                last_node = node

            cat_index += 1

        # Create node reference
        node_ref = ir.RefId(ir.Gender.male, last_node.node_exp.type, True, last_node)
        raw_data = rawdata.Bits(sys._getframe(1))
        raw_data._ir_exp = node_ref
        def_node = Define(raw_data)

        return def_node

