"""When statements for PyHCL

Filename: when.py
Author: SunnyChen
"""
import sys

from pyhcl.core.define import Define
from pyhcl.core import rawdata
from pyhcl.firrtl import ir
from pyhcl.core.resources import HasInfo
from pyhcl.util import utils_func

# Trace when statements
when_list = []

# Track if other statements between when/elsewhen and elsewhen/otherwise statements
track_index = 0


class WhenMarks:
    def __init__(self, when_node, elsewhen: bool = False):
        self.when_node = when_node
        self.elsewhen = elsewhen


class When(object):
    def __init__(self, con: Define):
        self.con = con
        self.whenbegin_node = None
        self.when_node = None
        self.sourceinfo = None
        self.prv_index = 0

    def __enter__(self):
        self.sourceinfo = HasInfo(sys._getframe(1))._sourceinfo

        # Create a new when ir node
        self.when_node = ir.When(self.sourceinfo)

        # Add trace
        when_list.append(WhenMarks(self.when_node))
        self.whenbegin_node = ir.WhenBegin(self.sourceinfo, self.con._data._ir_exp)
        self.prv_index = len(rawdata.local_sytax_tree)

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.when_node.stats.extend(rawdata.local_sytax_tree[self.prv_index:])
        del rawdata.local_sytax_tree[self.prv_index:]

        whenend_node = ir.WhenEnd(self.sourceinfo)

        self.when_node.whenbegin = self.whenbegin_node
        self.when_node.whenend = whenend_node
        self.when_node.elsebegin = ir.ElseBegin(self.sourceinfo)
        self.when_node.elseend = ir.ElseEnd(self.sourceinfo)

        rawdata.local_sytax_tree.append(self.when_node)

        global track_index
        track_index = len(rawdata.local_sytax_tree)


# def when(con):
#     """When statement function, use nest function and class"""
#     # No need to use parameters in wrapper function
#     def decorator(func):
#         # Deal with the condition
#         # When statement condition must be logical expression or Bool type
#         # Temporary do not perform type checking
#         # Construct WhenBegin ir node
#         sourceinfo = HasInfo(sys._getframe(1))._sourceinfo
#
#         # Create a new when ir node
#         when_node = ir.When(sourceinfo)
#
#         # Add trace
#         when_list.append(WhenMarks(when_node))
#         whenbegin_node = ir.WhenBegin(sourceinfo, con._data._ir_exp)
#         prv_index = len(rawdata.local_sytax_tree)
#
#         func()
#
#         when_node.stats.extend(rawdata.local_sytax_tree[prv_index:])
#         del rawdata.local_sytax_tree[prv_index:]
#
#         whenend_node = ir.WhenEnd(sourceinfo)
#
#         when_node.whenbegin = whenbegin_node
#         when_node.whenend = whenend_node
#         when_node.elsebegin = ir.ElseBegin(sourceinfo)
#         when_node.elseend = ir.ElseEnd(sourceinfo)
#
#         rawdata.local_sytax_tree.append(when_node)
#
#         global track_index
#         track_index = len(rawdata.local_sytax_tree)
#
#     return decorator


class Elsewhen(object):
    def __init__(self, con: Define):
        self.con = con
        self.sourceinfo = None
        self.whenbegin_node = None
        self.when_node = None
        self.prv_index = 0

    def __enter__(self):
        global track_index
        condition_stack = []
        self.sourceinfo = HasInfo(sys._getframe(1))._sourceinfo

        # Construct outer else statement
        else_node = ir.ElseBegin(self.sourceinfo)

        # Condition statements must append to the else node
        utils_func.search_def(self.con._data._ir_exp, condition_stack)
        else_node.stats.extend(condition_stack)
        condition_stack.clear()
        else_node.stats.extend(rawdata.local_sytax_tree[track_index:])
        del rawdata.local_sytax_tree[track_index:]

        elseend_node = ir.ElseEnd(self.sourceinfo)

        # Search when list from the tail to the beginning
        for i in range(len(when_list) - 1, -1, -1):
            if not when_list[i].elsewhen:
                when_list[i].elsewhen = True
                when_list[i].when_node.has_else = True
                when_list[i].when_node.elsebegin = else_node
                when_list[i].when_node.elseend = elseend_node
                break

        # Construct a new when statement
        self.when_node = ir.When(self.sourceinfo)
        when_list.append(WhenMarks(self.when_node))
        self.whenbegin_node = ir.WhenBegin(self.sourceinfo, self.con._data._ir_exp)

        else_node.stats.append(self.when_node)

        self.prv_index = len(rawdata.local_sytax_tree)

    def __exit__(self, exc_type, exc_val, exc_tb):
        global track_index
        self.when_node.stats.extend(rawdata.local_sytax_tree[self.prv_index:])
        del rawdata.local_sytax_tree[self.prv_index:]

        whenend_node = ir.WhenEnd(self.sourceinfo)

        self.when_node.whenbegin = self.whenbegin_node
        self.when_node.whenend = whenend_node
        self.when_node.elsebegin = ir.ElseBegin(self.sourceinfo)
        self.when_node.elseend = ir.ElseEnd(self.sourceinfo)

        track_index = len(rawdata.local_sytax_tree)


# def elsewhen(con):
#     """elsewhen statement function"""
#     def decorator(func):
#         global track_index
#         condition_stack = []
#         sourceinfo = HasInfo(sys._getframe(1))._sourceinfo
#
#         # Construct outer else statement
#         else_node = ir.ElseBegin(sourceinfo)
#
#         # Condition statements must append to the else node
#         utils_func.search_def(con._data._ir_exp, condition_stack)
#         else_node.stats.extend(condition_stack)
#         condition_stack.clear()
#         # else_node.stats.extend(rawdata.local_sytax_tree[track_index:])
#         # del rawdata.local_sytax_tree[track_index:]
#
#         elseend_node = ir.ElseEnd(sourceinfo)
#
#         # Search when list from the tail to the beginning
#         for i in range(len(when_list) - 1, -1, -1):
#             if not when_list[i].elsewhen:
#                 when_list[i].elsewhen = True
#                 when_list[i].when_node.has_else = True
#                 when_list[i].when_node.elsebegin = else_node
#                 when_list[i].when_node.elseend = elseend_node
#                 break
#
#         # Construct a new when statement
#         when_node = ir.When(sourceinfo)
#         when_list.append(WhenMarks(when_node))
#         whenbegin_node = ir.WhenBegin(sourceinfo, con._data._ir_exp)
#
#         else_node.stats.append(when_node)
#
#         prv_index = len(rawdata.local_sytax_tree)
#
#         func()
#
#         when_node.stats.extend(rawdata.local_sytax_tree[prv_index:])
#         del rawdata.local_sytax_tree[prv_index:]
#
#         whenend_node = ir.WhenEnd(sourceinfo)
#
#         when_node.whenbegin = whenbegin_node
#         when_node.whenend = whenend_node
#         when_node.elsebegin = ir.ElseBegin(sourceinfo)
#         when_node.elseend = ir.ElseEnd(sourceinfo)
#
#         track_index = len(rawdata.local_sytax_tree)
#
#     return decorator


class Otherwise(object):
    def __init__(self):
        self.sourceinfo = None
        self.else_node = None
        self.prv_index = 0

    def __enter__(self):
        global track_index
        self.sourceinfo = HasInfo(sys._getframe(1))._sourceinfo

        # Construct outer else statement
        self.else_node = ir.ElseBegin(self.sourceinfo)

        # Condition statements must append to the else node
        self.else_node.stats.extend(rawdata.local_sytax_tree[track_index:])
        del rawdata.local_sytax_tree[track_index:]

        elseend_node = ir.ElseEnd(self.sourceinfo)

        # Search when list from the tail to the beginning
        for i in range(len(when_list) - 1, -1, -1):
            if not when_list[i].elsewhen:
                when_list[i].elsewhen = True
                when_list[i].when_node.has_else = True
                when_list[i].when_node.elsebegin = self.else_node
                when_list[i].when_node.elseend = elseend_node
                break

        self.prv_index = len(rawdata.local_sytax_tree)

    def __exit__(self, exc_type, exc_val, exc_tb):
        global track_index
        self.else_node.stats.extend(rawdata.local_sytax_tree[self.prv_index:])
        del rawdata.local_sytax_tree[self.prv_index:]

        track_index = len(rawdata.local_sytax_tree)


# def otherwise():
#     """Otherwise statement function
#
#     The otherwise actually append to the else statement's when node
#     """
#     def decorator(func):
#         global track_index
#         sourceinfo = HasInfo(sys._getframe(1))._sourceinfo
#
#         # Construct outer else statement
#         else_node = ir.ElseBegin(sourceinfo)
#
#         # Condition statements must append to the else node
#         else_node.stats.extend(rawdata.local_sytax_tree[track_index:])
#         del rawdata.local_sytax_tree[track_index:]
#
#         elseend_node = ir.ElseEnd(sourceinfo)
#
#         # Search when list from the tail to the beginning
#         for i in range(len(when_list) - 1, -1, -1):
#             if not when_list[i].elsewhen:
#                 when_list[i].elsewhen = True
#                 when_list[i].when_node.has_else = True
#                 when_list[i].when_node.elsebegin = else_node
#                 when_list[i].when_node.elseend = elseend_node
#                 break
#
#         prv_index = len(rawdata.local_sytax_tree)
#
#         func()
#
#         else_node.stats.extend(rawdata.local_sytax_tree[prv_index:])
#         del rawdata.local_sytax_tree[prv_index:]
#
#         track_index = len(rawdata.local_sytax_tree)
#
#     return decorator


# class when(object):
#     def __init__(self, con):
#         sourceinfo = HasInfo(sys._getframe(1))._sourceinfo
#         whenbegin_node = ir.WhenBegin(sourceinfo, con._data._ir_exp)
#
#     def begin(self, *exp):
#         print(exp)
#         pass
