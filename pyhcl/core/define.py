"""Module's define statement object abstract class

Filename: define.py
Author: SunnyChen
"""
from __future__ import annotations

import copy
import sys
from typing import Union, List
from pyhcl.core import rawdata
from pyhcl.core.resources import HasInfo, InstanceId
from pyhcl.firrtl import ir

# TODO(SunnyChen): Use frame to track the definition's class
# Not a good implementation, considering to fix in the future


# def extend_map(opra: Define, oprb: Define):
#     """Use inspect module to get the class name, then extend the syntax_map"""
#     # TODO(SunnyChen): Just back to the previous frame, not good
#     # Get class's name
#     current_frame = list(filter(lambda x: not x is None, [opra.define_frame, oprb.define_frame]))[0]
#     if opra.define_frame is Node:
#         opra.define_frame = current_frame
#     elif oprb.define_frame is None:
#         oprb.define_frame = current_frame
#     class_name = current_frame.f_code.co_name
#     # Extend syntax tree
#     if syntax_map.get(class_name, None) is None:
#         syntax_map.setdefault(class_name, [])
#     for i in rawdata.local_sytax_tree:
#         syntax_map[class_name].append(i)
#     rawdata.local_sytax_tree.clear()


def get_width(value: Union[int, str]) -> int:
    """Get literal value's width"""
    if isinstance(value, str):
        # should be "hxxx"
        num_str = value[1:]
        value = int(num_str, 16)

    width = 0
    while value != 0:
        value = int(value / 2)
        width = width + 1
    return width


def U(value: Union[int, str], width: int = 0) -> Define:
    """Construct a UInt literal value from a integer or string"""
    if width == 0:
        _width = get_width(value)
    else:
        _width = width
    litexp = ir.LitUInt(ir.Gender.male, ir.UInt(_width), True, value)
    # rawdata.local_sytax_tree.append(litexp)
    ret = Define(rawdata.UInt(_width))
    ret._data._ir_exp = litexp
    return copy.deepcopy(ret)


def S(value: Union[int, str], width: int = 0) -> Define:
    """Construct a UInt literal value from a intelitsintger or string"""
    if width == 0:
        _width = get_width(value)
    else:
        _width = width
    litexp = ir.LitSInt(ir.Gender.male, ir.SInt(_width), True, value)
    # rawdata.local_sytax_tree.append(litexp)
    ret = Define(rawdata.SInt(_width))
    ret._data._ir_exp = litexp
    return copy.deepcopy(ret)


def stop(clk: Define, halt: Define, exit_code: int):
    """Stop statement"""
    # Check halt and clk type
    if not isinstance(clk._data, rawdata.Clock) or not isinstance(halt._data, rawdata.UInt):
        if halt._data._ir_exp.type.width != 0:
            raise TypeError("Stop statement's clock signal must be clock type, halt signal must be 1 bit UInt")

    # Construct a stop statement
    sourceinfo = HasInfo(sys._getframe(1))._sourceinfo
    stop_node = ir.Stop(sourceinfo, clk._data._ir_exp, halt._data._ir_exp, exit_code)
    rawdata.local_sytax_tree.append(stop_node)


def printf(clk: Define, con: Define, printstr, *variables):
    """Printf statement"""
    # Check con and clk type
    if not isinstance(clk._data, rawdata.Clock) or not isinstance(con._data, rawdata.UInt):
        if con._data._ir_exp.type.width != 0:
            raise TypeError("Stop statement's clock signal must be clock type, halt signal must be 1 bit UInt")

    # Construct a printf statement
    sourceinfo = HasInfo(sys._getframe(1))._sourceinfo
    exp_list = [k._data._ir_exp for k in variables]
    printf_node = ir.Printf(sourceinfo, clk._data._ir_exp, con._data._ir_exp, printstr, exp_list)
    rawdata.local_sytax_tree.append(printf_node)


def skip():
    """Skip statement"""
    # Construct skip statement
    sourceinfo = HasInfo(sys._getframe(1))._sourceinfo
    skip_node = ir.Skip(sourceinfo)
    rawdata.local_sytax_tree.append(skip_node)


def validif(condition: Define, input_def: Define):
    """Conditional valid statement"""
    if not isinstance(condition._data, rawdata.UInt) and condition._data._ir_exp.type.width != 1:
        if not input_def._data._ir_exp.passive_type:
            raise TypeError("validif statement's condition data type must be 1 bit UInt")

    # Construct ValidIf expression
    validif_exp = ir.ValidIf(ir.Gender.male, input_def._data._ir_exp.type, True,
                             condition._data._ir_exp, input_def._data._ir_exp)

    sourceinfo = HasInfo(sys._getframe(1))._sourceinfo
    _id = InstanceId()
    node = ir.DefNode(sourceinfo, "_T_" + str(_id.id), _id, validif_exp)

    # Create node reference
    node_ref = ir.RefId(ir.Gender.male, node.node_exp.type, True, node)
    raw_data = rawdata.Bits(sys._getframe(1))
    raw_data._ir_exp = node_ref
    def_node = Define(raw_data)

    rawdata.local_sytax_tree.append(node)

    return def_node


def type_check(data_list: List[rawdata.Data]):
    """Check if the data type is ground type(Element)
    If not, raise TypeError
    """
    if len(list(filter(lambda x: not isinstance(x, rawdata.Element), data_list))) != 0:
        raise TypeError("The operand's data type must be ground type")


class Define(object):
    """All define statement object's based class <<abstract>>"""
    def __init__(self, _data: rawdata.Data):
        """Inits a Define object"""
        # If the data type is a ground type
        self._data = _data
        self._define_node = ir.Definition()

    # Overloaded operators
    # These operators can only effect the element data type
    def to_bool(self):
        """Construct a bit operation and return a mirror copy"""
        # If use this function on a vector, raise error
        if isinstance(self._data, rawdata.Vec) or isinstance(self._data, rawdata.Record):
            raise TypeError("Can't convert a aggregate type to Bool")

        ret = copy.deepcopy(self.__getitem__(0))
        return ret

    def __hash__(self):
        # Make Define objects hashable
        # Hash their memory address
        return hash(id(self))

    def __invert__(self):
        # type_check([self._data])
        node = Node(~self._data)
        return node

    def __neg__(self):
        # type_check([self._data])
        node = Node(-self._data)
        return node

    def __and__(self, other: Define):
        # type_check([self._data, other._data])
        node = Node(self._data & other._data)
        return node

    def __or__(self, other: Define):
        # type_check([self._data, other._data])
        node = Node(self._data | other._data)
        return node

    def __xor__(self, other: Define):
        # type_check([self._data, other._data])
        node = Node(self._data ^ other._data)
        return node

    def andr(self):
        # type_check([self._data])
        node = Node(self._data.andr())
        return node

    def orr(self):
        # type_check([self._data])
        node = Node(self._data.orr())
        return node

    def xorr(self):
        # type_check([self._data])
        node = Node(self._data.xorr())
        return node

    def __eq__(self, other):
        # type_check([self._data, other._data])
        if isinstance(other, Define):
            node = Node(self._data == other._data)
            return node
        else:
            # BitPat: operand == bitpat
            sourceinfo = HasInfo(sys._getframe(1))._sourceinfo

            # Convert bitpat.mask and bitpat.cmp to "hxx" style
            mask_str = 'h0' + str(hex(int(other.mask[1:], 2)))[2:]
            cmp_str = 'h0' + (hex(int(other.cmp[1:], 2)))[2:]

            # Extract the valid bits from the pattern: and(operand, bitpat.mask)
            and_op = ir.Op(ir.Gender.male, ir.Type(), True, "and", [self._data._ir_exp, U(mask_str)._data._ir_exp], [])
            _id = InstanceId()
            and_node = ir.DefNode(sourceinfo, "_T_" + str(_id.id), _id, and_op)
            and_node_ref = ir.RefId(ir.Gender.male, and_node.node_exp.type, True, and_node)

            # Equal test
            _id = InstanceId()
            eq_op = ir.Op(ir.Gender.male, ir.UInt(1), True, "eq", [and_node_ref, U(cmp_str)._data._ir_exp], [])
            eq_node = ir.DefNode(sourceinfo, "_T_" + str(_id.id), _id, eq_op)
            eq_node_ref = ir.RefId(ir.Gender.male, eq_node.node_exp.type, True, eq_node)

            rawdata.local_sytax_tree.extend([and_node, eq_node])

            raw_data = rawdata.Bits(sys._getframe(1))
            raw_data._ir_exp = eq_node_ref
            def_node = Define(raw_data)

            return def_node

    def __ne__(self, other):
        # type_check([self._data, other._data])
        if isinstance(other, Define):
            node = Node(self._data != other._data)
            return node
        else:
            # BitPat: operand == bitpat
            sourceinfo = HasInfo(sys._getframe(1))._sourceinfo

            # Convert bitpat.mask and bitpat.cmp to "hxx" style
            mask_str = 'h0' + str(hex(int(other.mask[1:], 2)))[2:]
            cmp_str = 'h0' + (hex(int(other.cmp[1:], 2)))[2:]

            # Extract the valid bits from the pattern: and(operand, bitpat.mask)
            and_op = ir.Op(ir.Gender.male, ir.Type(), True, "and", [self._data._ir_exp, U(mask_str)._data._ir_exp], [])
            _id = InstanceId()
            and_node = ir.DefNode(sourceinfo, "_T_" + str(_id.id), _id, and_op)
            and_node_ref = ir.RefId(ir.Gender.male, and_node.node_exp.type, True, and_node)

            # Not equal test
            _id = InstanceId()
            neq_op = ir.Op(ir.Gender.male, ir.UInt(1), True, "neq", [and_node_ref, U(cmp_str)._data._ir_exp], [])
            neq_node = ir.DefNode(sourceinfo, "_T_" + str(_id.id), _id, neq_op)
            neq_node_ref = ir.RefId(ir.Gender.male, neq_node.node_exp.type, True, neq_node)

            rawdata.local_sytax_tree.extend([and_node, neq_node])

            raw_data = rawdata.Bits(sys._getframe(1))
            raw_data._ir_exp = neq_node_ref
            def_node = Define(raw_data)

            return def_node

    def __lshift__(self, other: Union[Define, int]):
        # type_check([self._data, other._data])
        if isinstance(other, Define):
            node = Node(self._data << other._data)
        else:
            node = Node(self._data << other)
        return node

    def __rshift__(self, other: Union[Define, int]):
        # type_check([self._data, other._data])
        if isinstance(other, Define):
            node = Node(self._data >> other._data)
        else:
            node = Node(self._data >> other)
        return node

    def __add__(self, other: Define):
        # type_check([self._data, other._data])
        node = Node(self._data + other._data)
        # extend_map(self, other)
        return node

    def __sub__(self, other: Define):
        # type_check([self._data, other._data])
        node = Node(self._data - other._data)
        return node

    def __mul__(self, other: Define):
        # type_check([self._data, other._data])
        node = Node(self._data * other._data)
        # extend_map(self, other)
        return node

    def __truediv__(self, other: Define):
        # type_check([self._data, other._data])
        node = Node(self._data / other._data)
        return node

    def __mod__(self, other: Define):
        # type_check([self._data, other._data])
        node = Node(self._data % other._data)
        return node

    def __lt__(self, other: Define):
        # type_check([self._data, other._data])
        node = Node(self._data < other._data)
        return node

    def __le__(self, other: Define):
        # type_check([self._data, other._data])
        node = Node(self._data <= other._data)
        return node

    def __gt__(self, other: Define):
        # type_check([self._data, other._data])
        node = Node(self._data > other._data)
        return node

    def __ge__(self, other: Define):
        # type_check([self._data, other._data])
        node = Node(self._data >= other._data)
        return node

    def pad(self, n: int):
        # type_check([self._data])
        node = Node(self._data.pad(n))
        return node

    def asuint(self):
        # type_check([self._data])
        node = Node(self._data.asuint())
        return node

    def assint(self):
        # type_check([self._data])
        node = Node(self._data.assint())
        return node

    def asclock(self):
        # type_check([self._data])
        node = Node(self._data.asclock())
        return node

    def cvt(self):
        # type_check([self._data])
        node = Node(self._data.cvt())
        return node

    def __getitem__(self, item: Union[int, slice, Define]):
        # type_check([self._data])
        # Check the definition's datatype
        if not isinstance(self._data, rawdata.Vec):
            # Normal bitwise operation
            if isinstance(item, Define):
                raise TypeError("Bitwise operation can only be int or slice")

            node = Node(self._data.__getitem__(item))
            return node
        else:
            # Vec type
            # Temporary only support int
            if isinstance(item, slice):
                raise TypeError("Vec item index do not support slice")

            # Create a deep copy mirror of current Vec type Definition
            # Vec temporary support UInt and SInt
            if isinstance(self._data._ir_exp.type.type, ir.UInt):
                mirror_data = rawdata.UInt(self._data._ir_exp.type.type.width)
            elif isinstance(self._data._ir_exp.type.type, ir.SInt):
                mirror_data = rawdata.SInt(self._data._ir_exp.type.type.width)
            else:
                mirror_data = None

            # If is int, use subindex.
            # If is Definition, use subaccess
            if isinstance(item, int):
                mirror_data._ir_exp = ir.RefSubindex(ir.Gender.bi_gender, mirror_data._ir_exp.type,
                                                     mirror_data._ir_exp.passive_type, self._define_node, item)
            elif isinstance(item, Define):
                mirror_data._ir_exp = ir.RefSubaccess(ir.Gender.bi_gender, mirror_data._ir_exp.type,
                                                     mirror_data._ir_exp.passive_type, self._define_node,
                                                      item._data._ir_exp)
            if isinstance(self._data._ir_exp, ir.RefSubfield):
                # Reference, get deep copy of self
                raw_self = copy.deepcopy(self)
                exp = self._data._ir_exp
                temp_ir_exp = raw_self._data._ir_exp
                if isinstance(self._data._ir_exp.type.type, ir.UInt):
                    raw_self._data = rawdata.UInt(raw_self._data._ir_exp.type.type.width)
                elif isinstance(self._data._ir_exp.type.type, ir.SInt):
                    raw_self._data = rawdata.SInt(raw_self._data._ir_exp.type.type.width)
                # raw_self._data._ir_exp = temp_ir_exp

                # Get rid of field
                self._data._ir_exp.ref_field = None

                raw_self._data._ir_exp = ir.RefSubfield(self._data._ir_exp.gender, ir.UInt(temp_ir_exp.type.type.width),
                                                        temp_ir_exp.passive_type, self._data._ir_exp,
                                                        mirror_data._ir_exp)
                return raw_self
            return Define(mirror_data)

    def head(self, n: int):
        # type_check([self._data])
        node = Node(self._data.head(n))
        return node

    def tail(self, n: int):
        # type_check([self._data])
        node = Node(self._data.tail(n))
        return node

    def __imatmul__(self, other):
        # Seems like not a good idea to check type in connection
        # type_check([self._data, other._data])

        # If the left side is a reference to a memory port,
        # must be writing to the memory
        if isinstance(self._data._ir_exp, ir.RefId):
            if isinstance(self._data._ir_exp.ref_arg, ir.RefMemPort):
                self._data._ir_exp.ref_arg.read_or_write = False
        self._data @= other._data
        # extend_map(self, other)
        return self

    def __setitem__(self, key, value):
        """Virtually override, no use"""
        pass

    def invalid(self):
        """Generate an invalid statement"""
        # Construct a IsInvalid
        sourceinfo = HasInfo(sys._getframe(1))._sourceinfo
        invalid_node = ir.IsInvalid(sourceinfo, self._data._ir_exp)
        rawdata.local_sytax_tree.append(invalid_node)


class Node(Define):
    """Internal node class"""

    def __init__(self, _data: rawdata.Data):
        """Inits a node class"""
        # A node must be a internal definition, not define by the user
        # raw_data = copy.deepcopy(_data)
        super().__init__(_data)
        self._define_node = _data._ir_exp
