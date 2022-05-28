"""Some utils function that may use in PyHCL core or util components

Filename: utils_func.py
Author: SunnyChen
"""
from pyhcl.firrtl import ir
from pyhcl.core import rawdata


def search_def(iexp, stack):
    """Search the definition chain of the node

    Usage:
        - When/Elsewhen statements - Constructing condition
        - MuxLookup Utils - Constructing dict statements
    """
    try:
        temp_stack = []
        if isinstance(iexp, ir.Ref):
            if isinstance(iexp.ref_arg, ir.Definition):
                # if iexp.ref_arg in rawdata.local_sytax_tree:
                #     temp_stack.append(iexp.ref_arg)
                #     # Remove from the local syntax tree
                #     rawdata.local_sytax_tree.remove(iexp.ref_arg)
                ref = iexp.ref_arg
                if isinstance(ref, ir.DefNode):
                    for i in ref.node_exp.operands:
                            search_def(i, stack)
        stack.extend(temp_stack[::-1])
    except Exception:
        print(iexp.ref_arg.emit())
