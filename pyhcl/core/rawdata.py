"""PyHCL data type definition classes

Filename: rawdata.py
Author  : SunnyChen
"""
from __future__ import annotations
import sys
import copy
from enum import Enum
from typing import Union, List
from pyhcl.core.resources import HasInfo, InstanceId
from pyhcl.firrtl import ir

local_sytax_tree = []


class Direction(Enum):
    """PyHCL frontend direction enum class"""
    Undefined = 0
    Input = 1
    Output = 2


class Data(HasInfo):
    """Abstract data class

    Attributes:
        _sourceinfo: object's source code information
        _ir_exp: object's IR exp
    """
    def __init__(self, frame=None):
        """Inits a Data object"""
        super().__init__(frame)
        self._ir_exp: ir.Exp = None

    def width_unknown(self) -> bool:
        """If current object didn't define width, return True"""
        return self._ir_exp.type.width == 0

    def __invert__(self):
        pass

    def __neg__(self):
        pass

    def __and__(self, other):
        pass

    def __or__(self, other):
        pass

    def __xor__(self, other):
        pass

    def andr(self):
        pass

    def orr(self):
        pass

    def xorr(self):
        pass

    def __eq__(self, other):
        pass

    def __ne__(self, other):
        pass

    def __lshift__(self, other):
        pass

    def __rshift__(self, other):
        pass

    def __add__(self, other):
        pass

    def __sub__(self, other):
        pass

    def __mul__(self, other):
        pass

    def __truediv__(self, other):
        pass

    def __mod__(self, other):
        pass

    def __lt__(self, other):
        pass

    def __le__(self, other):
        pass

    def __gt__(self, other):
        pass

    def __ge__(self, other):
        pass

    def pad(self, other: int):
        pass

    def asuint(self):
        pass

    def assint(self):
        pass

    def asclock(self):
        pass

    def cvt(self):
        pass

    def __neg__(self):
        pass

    def __getitem__(self, item: Union[int, slice, Element]):
        pass

    def head(self, n: int):
        pass

    def tail(self, n: int):
        pass

    def __imatmul__(self, other):
        """Overload '@=' operator as connect"""
        pass


class Element(Data):
    """Abstract element class

    Attributes:
        sourceinfo: object's source code information
        _ir_exp: object's IR exp object
    """
    def __init__(self, frame=None):
        """Inits a Element object"""
        super().__init__(frame)

    # def width_unknown(self) -> bool:
    #     """If current object didn't define width, return True"""
    #     return self._ir_exp.type.width == 0


class Aggregate(Data):
    """Aggregate type of the data
    Vector - Directly inherit Aggregate
    Bundle - Aggregate -> Record -> Bundle
    """
    pass


class Vec(Aggregate):
    """Vector type of the data
    Inherit from Class Aggregate
    """

    def __init__(self, size: int, vtype: Element):
        """Inits a Vec type class

        [WARNING]: Temporary Vec only support ground type
        """
        raw_vtype = copy.deepcopy(vtype)
        super().__init__(sys._getframe(1))
        # Construct a Vector type
        self._ir_exp = ir.Ref()
        # Modify size and type in definition
        self._ir_exp.type = ir.Vector(0, size, raw_vtype._ir_exp.type)


class Record(Aggregate):
    """Abstract class Record for Bundle class

    Attributes:
        _sourceinfo: Source information
        _ir_exp: Object's IR exp
        agg_type: Bundle's aggregate type
    """
    def __init__(self, frame):
        """Bundle needs fields"""
        super().__init__(frame)
        self._agg_type = ir.Bundle(0, 0)
        self._ir_exp = ir.Exp(ir.Gender.undefined, self._agg_type, False)


class Bits(Element):
    """Abstract bits class

    This class need to overwrite operators.

    Attributes:
        sourceinfo: object's source code information
        _ir_exp: object's IR exp object
    """
    def __init__(self, frame=None):
        """Inits a Bits object"""
        super().__init__(frame)

    def to_uint(self):
        """Convert current SInt object to UInt object"""
        ret = UInt(self._ir_exp.type.width)
        if isinstance(self._ir_exp, ir.LitInt):
            if isinstance(self._ir_exp, ir.LitSInt):
                ret._ir_exp = ir.LitUInt(self._ir_exp.gender, ir.UInt(self._ir_exp.type.width),
                                        self._ir_exp.passive_type, self._ir_exp.initial)
        else:
            ret._ir_exp = self._ir_exp
            ret._ir_exp.type = ir.UInt(self._ir_exp.type.width)
        ret._ir_exp.type = ir.UInt(self._ir_exp.type.width)
        ret._sourceinfo = self._sourceinfo
        return ret

    def to_sint(self):
        """Convert current UInt object to SInt object"""
        ret = SInt(self._ir_exp.type.width)
        if isinstance(self._ir_exp, ir.LitInt):
            if isinstance(self._ir_exp, ir.LitUInt):
                ret._ir_exp = ir.LitSInt(self._ir_exp.gender, ir.SInt(self._ir_exp.type.width),
                                        self._ir_exp.passive_type, self._ir_exp.initial)
        else:
            ret._ir_exp = self._ir_exp
            ret._ir_exp.type = ir.UInt(self._ir_exp.type.width)
        ret._ir_exp.type = ir.UInt(self._ir_exp.type.width)
        ret._sourceinfo = self._sourceinfo
        return ret

    def to_clock(self):
        """Convert current UInt/SInt object to Clock object"""
        if isinstance(self, Clock):
            return self

        ret = Clock()
        ret._ir_exp = self._ir_exp
        ret._ir_exp.type = ir.Clock(1)
        ret._sourceinfo = self._sourceinfo
        return ret

    def push_node(self, op: ir.Op) -> ir.RefId:
        """Create a node for the operator and push it to syntax tree
        Return the reference of the node
        """
        # Construct node
        _sourceinfo = HasInfo(sys._getframe(3))._sourceinfo
        _id = InstanceId()
        node = ir.DefNode(_sourceinfo, "_T_" + str(_id.id), _id, op)

        local_sytax_tree.append(node)
        node_ref = ir.RefId(ir.Gender.male, node.node_exp.type, True, node)
        return node_ref

    def __invert__(self):
        """Overload operator '~'"""
        # Construct IR Op object
        neg_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "not", [self._ir_exp], [])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(neg_op)
        return ret

    def __and__(self, other):
        """Overload operator '&'"""
        # Construct IR Op object
        and_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "and", [self._ir_exp, other._ir_exp], [])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(and_op)
        if self.width_unknown() or other.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            ret._ir_exp.type.width = max(self._ir_exp.type.width, other._ir_exp.type.width)
        return ret

    def __or__(self, other):
        """Overload operator '|'"""
        # Construct IR Op object
        or_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "or", [self._ir_exp, other._ir_exp], [])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(or_op)
        if self.width_unknown() or other.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            ret._ir_exp.type.width = max(self._ir_exp.type.width, other._ir_exp.type.width)
        return ret

    def __xor__(self, other):
        """Overload operator '^'"""
        # Construct IR Op object
        xor_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "xor", [self._ir_exp, other._ir_exp], [])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(xor_op)
        if self.width_unknown() or other.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            ret._ir_exp.type.width = max(self._ir_exp.type.width, other._ir_exp.type.width)
        return ret

    def andr(self):
        """Bitwise and operation"""
        # Construct IR Op object
        andr_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "andr", [self._ir_exp], [])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(andr_op)
        return ret

    def orr(self):
        """Bitwise or operation"""
        # Construct IR Op object
        orr_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "orr", [self._ir_exp], [])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(orr_op)
        return ret

    def xorr(self):
        """Bitwise xor operation"""
        # Construct IR Op object
        xorr_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "xorr", [self._ir_exp], [])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(xorr_op)
        return ret

    def __eq__(self, other):
        """Overload operator '=='"""
        # Construct IR Op object
        eq_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "eq", [self._ir_exp, other._ir_exp], [])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(eq_op)
        if self.width_unknown() or other.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            ret._ir_exp.type.width = 1
        return ret

    def __ne__(self, other):
        """Overload operator '!='"""
        # Construct IR Op object
        neq_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "neq", [self._ir_exp, other._ir_exp], [])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(neq_op)
        if self.width_unknown() or other.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            ret._ir_exp.type.width = 1
        return ret

    def __lshift__(self, other):
        """Overload operator '<<'"""
        # shl or dshl
        if isinstance(other, int):
            # shl
            if isinstance(self, UInt):
                shl_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "shl", [self._ir_exp], [other])
                ret = self.to_uint()
            else:
                shl_op = ir.Op(ir.Gender.male, ir.SInt(self._ir_exp.type.width), True, "shl", [self._ir_exp], [other])
                ret = self.to_sint()
            ret._ir_exp = self.push_node(shl_op)
            if ret.width_unknown():
                ret._ir_exp.type.width = 0
            else:
                ret._ir_exp.type.width += other
        else:
            if isinstance(self, UInt):
                shl_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "dshl",
                               [self._ir_exp, other._ir_exp], [])
                ret = self.to_uint()
            else:
                shl_op = ir.Op(ir.Gender.male, ir.SInt(self._ir_exp.type.width), True, "dshl",
                               [self._ir_exp, other._ir_exp], [])
                ret = self.to_sint()
            ret._ir_exp = self.push_node(shl_op)
            ret._ir_exp.type.width = 0
        return ret

    def __rshift__(self, other):
        """Overload operator '>>'"""
        # shr or dshr
        if isinstance(other, int):
            # shr
            if isinstance(self, UInt):
                shr_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "shr", [self._ir_exp], [other])
                ret = self.to_uint()
            else:
                shr_op = ir.Op(ir.Gender.male, ir.SInt(self._ir_exp.type.width), True, "shr", [self._ir_exp], [other])
                ret = self.to_sint()
            ret._ir_exp = self.push_node(shr_op)
            if not ret.width_unknown():
                ret._ir_exp.type.width = max(1, self._ir_exp.type.width - other)
        else:
            if isinstance(self, UInt):
                shr_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "dshr",
                               [self._ir_exp, other._ir_exp], [])
                ret = self.to_uint()
            else:
                shr_op = ir.Op(ir.Gender.male, ir.SInt(self._ir_exp.type.width), True, "dshr",
                               [self._ir_exp, other._ir_exp], [])
                ret = self.to_sint()
            ret._ir_exp = self.push_node(shr_op)
            ret._ir_exp.type.width = 0
        return ret

    def __add__(self, other):
        """Overload operator '+'"""
        if isinstance(self, SInt) or isinstance(other, SInt):
            ret = self.to_sint()
            add_op = ir.Op(ir.Gender.male, ir.SInt(self._ir_exp.type.width), True, "add",
                           [self._ir_exp, other._ir_exp], [])
        else:
            ret = self.to_uint()
            add_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "add",
                           [self._ir_exp, other._ir_exp], [])
        ret._ir_exp = self.push_node(add_op)
        # four cases
        if self.width_unknown() or other.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            both_uint = isinstance(self, UInt) and isinstance(other, UInt)
            both_sint = isinstance(self, SInt) and isinstance(other, SInt)
            if both_uint or both_sint:
                ret._ir_exp.type.width = max(self._ir_exp.type.width, other._ir_exp.type.width) + 1
            elif isinstance(self, SInt) and isinstance(other, UInt):
                ret._ir_exp.type.width = max(self._ir_exp.type.width - 1, other._ir_exp.type.width) + 2
            elif isinstance(self, UInt) and isinstance(other, SInt):
                ret._ir_exp.type.width = max(self._ir_exp.type.width, other._ir_exp.type.width - 1) + 2
        return ret

    def __sub__(self, other):
        """Overload operator '-'"""
        sub_op = ir.Op(ir.Gender.male, ir.SInt(self._ir_exp.type.width), True, "sub", [self._ir_exp, other._ir_exp], [])
        ret = self.to_sint()
        ret._ir_exp = self.push_node(sub_op)
        # four cases
        if self.width_unknown() or other.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            both_uint = isinstance(self, UInt) and isinstance(other, UInt)
            both_sint = isinstance(self, SInt) and isinstance(other, SInt)
            if both_uint or both_sint:
                ret._ir_exp.type.width = max(self._ir_exp.type.width, other._ir_exp.type.width) + 1
            elif isinstance(self, SInt) and isinstance(other, UInt):
                ret._ir_exp.type.width = max(self._ir_exp.type.width - 1, other._ir_exp.type.width) + 2
            elif isinstance(self, UInt) and isinstance(other, SInt):
                ret._ir_exp.type.width = max(self._ir_exp.type.width, other._ir_exp.type.width - 1) + 2
        return ret

    def __mul__(self, other):
        """Overload operator '*'"""
        if isinstance(self, SInt) or isinstance(other, SInt):
            ret = self.to_sint()
            mul_op = ir.Op(ir.Gender.male, ir.SInt(self._ir_exp.type.width), True, "mul", [self._ir_exp, other._ir_exp],
                           [])
        else:
            ret = self.to_uint()
            mul_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "mul", [self._ir_exp, other._ir_exp],
                           [])
        ret._ir_exp = self.push_node(mul_op)
        if self.width_unknown() or other.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            ret._ir_exp.type.width += other._ir_exp.type.width
        return ret

    def __truediv__(self, other):
        """Overload operator '/'"""
        if isinstance(self, SInt) or isinstance(other, SInt):
            ret = self.to_sint()
            div_op = ir.Op(ir.Gender.male, ir.SInt(self._ir_exp.type.width), True, "div", [self._ir_exp, other._ir_exp],
                           [])
        else:
            ret = self.to_uint()
            div_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "div", [self._ir_exp, other._ir_exp],
                           [])
        ret._ir_exp = self.push_node(div_op)
        if self.width_unknown() or other.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            if isinstance(other, SInt):
                ret._ir_exp.type.width += 1
        return ret

    def __mod__(self, other):
        """Overload operator '%'"""
        if isinstance(self, UInt):
            ret = self.to_uint()
            mod_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "rem", [self._ir_exp, other._ir_exp],
                           [])
        else:
            ret = self.to_sint()
            mod_op = ir.Op(ir.Gender.male, ir.SInt(self._ir_exp.type.width), True, "rem", [self._ir_exp, other._ir_exp],
                           [])
        ret._ir_exp = self.push_node(mod_op)
        if self.width_unknown() or other.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            if isinstance(self, SInt) and isinstance(other, UInt):
                ret._ir_exp.type.width = min(self._ir_exp.type.width, other._ir_exp.type.width - 1)
            else:
                ret._ir_exp.type.width = min(self._ir_exp.type.width, other._ir_exp.type.width)
        return ret

    def __lt__(self, other):
        """Overload operator '<'"""
        lt_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "lt", [self._ir_exp, other._ir_exp], [])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(lt_op)
        if self.width_unknown() or other.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            ret._ir_exp.type.width = 1
        return ret

    def __le__(self, other):
        """Overload operator '<='"""
        leq_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "leq", [self._ir_exp, other._ir_exp], [])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(leq_op)
        if self.width_unknown() or other.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            ret._ir_exp.type.width = 1
        return ret

    def __gt__(self, other):
        """Overload operator '>'"""
        gt_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "gt", [self._ir_exp, other._ir_exp], [])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(gt_op)
        if self.width_unknown() or other.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            ret._ir_exp.type.width = 1
        return ret

    def __ge__(self, other):
        """Overload operator '>='"""
        geq_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "geq", [self._ir_exp, other._ir_exp], [])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(geq_op)
        if self.width_unknown() or other.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            ret._ir_exp.type.width = 1
        return ret

    def pad(self, other: int):
        """FIRRTL pad operator"""
        if isinstance(self, UInt):
            pad_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "pad", [self._ir_exp], [other])
            ret = self.to_uint()
        else:
            pad_op = ir.Op(ir.Gender.male, ir.SInt(self._ir_exp.type.width), True, "pad", [self._ir_exp], [other])
            ret = self.to_sint()
        ret._ir_exp = self.push_node(pad_op)
        if not ret.width_unknown():
            ret._ir_exp.type.width = max(self._ir_exp.type.width, other)
        return ret

    def asuint(self):
        """FIRRTL asUInt operator"""
        asuint_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "asUInt", [self._ir_exp], [])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(asuint_op)
        return ret

    def assint(self):
        """FIRRTL asSInt operator"""
        assint_op = ir.Op(ir.Gender.male, ir.SInt(self._ir_exp.type.width), True, "asSInt", [self._ir_exp], [])
        ret = self.to_sint()
        ret._ir_exp = self.push_node(assint_op)
        return ret

    def asclock(self):
        """FIRRTL asClock operator"""
        asclock_op = ir.Op(ir.Gender.male, ir.Clock(1), True, "asClock", [self._ir_exp], [])
        ret = self.to_clock()
        ret._ir_exp = self.push_node(asclock_op)
        return ret

    def cvt(self):
        """FIRRTL cvt operator"""
        cvt_op = ir.Op(ir.Gender.male, ir.SInt(self._ir_exp.type.width), True, "cvt", [self._ir_exp], [])
        ret = self.to_sint()
        ret._ir_exp = self.push_node(cvt_op)
        if self.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            if isinstance(self, UInt):
                ret._ir_exp.type.width = self._ir_exp.type.width + 1
        return ret

    def __neg__(self):
        """Overload operator '-'"""
        neg_op = ir.Op(ir.Gender.male, ir.SInt(self._ir_exp.type.width), True, "neg", [self._ir_exp], [])
        ret = self.to_sint()
        ret._ir_exp = self.push_node(neg_op)
        return ret

    def __getitem__(self, item: Union[int, slice]):
        """Overload operator '[]'"""
        if isinstance(item, int):
            # extract one bit
            bits_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "bits", [self._ir_exp], [item, item])
            ret = self.to_uint()
            ret._ir_exp = self.push_node(bits_op)
            if self.width_unknown():
                ret._ir_exp.type.width = 0
            else:
                ret._ir_exp.type.width = 1
        elif isinstance(item, slice):
            # extract some bits
            bits_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "bits", [self._ir_exp], [item.start, item.stop])
            ret = self.to_uint()
            ret._ir_exp = self.push_node(bits_op)
            if self.width_unknown():
                ret._ir_exp.type.width = 0
            else:
                ret._ir_exp.type.width = item.start - item.stop + 1
        else:
            raise TypeError("__getitem__(): index should be int or slice")
        return ret

    def head(self, n: int):
        """FIRRTL operator head"""
        if self._ir_exp.type.width != 0 and n > self._ir_exp.type.width:
            raise ValueError("head(): Width is too large")
        head_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "head", [self._ir_exp], [n])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(head_op)
        if self.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            ret._ir_exp.type.width = n
        return ret

    def tail(self, n: int):
        """FIRRTL operator tail"""
        if self._ir_exp.type.width != 0 and n >= self._ir_exp.type.width:
            raise ValueError("tail(): Width is too large")
        tail_op = ir.Op(ir.Gender.male, ir.UInt(self._ir_exp.type.width), True, "tail", [self._ir_exp], [n])
        ret = self.to_uint()
        ret._ir_exp = self.push_node(tail_op)
        if self.width_unknown():
            ret._ir_exp.type.width = 0
        else:
            ret._ir_exp.type.width -= n
        return ret

    def __imatmul__(self, other: Data):
        """Overload '@=' as connect"""
        sourceinfo = HasInfo(sys._getframe(2))._sourceinfo
        lexp = self._ir_exp
        rexp = other._ir_exp
        trace = lexp
        while hasattr(trace, "ref_arg"):
            trace = trace.ref_arg
            if isinstance(trace, ir.RefMemPort):
                trace.read_or_write = False
                # lexp = copy.deepcopy(self._ir_exp)
        # trace = rexp
        # while hasattr(trace, "ref_arg"):
        #     trace = trace.ref_arg
        #     if isinstance(trace, ir.RefMemPort):
        #         # rexp = copy.deepcopy(other._ir_exp)
        connect = ir.Connect(sourceinfo, lexp, rexp)
        local_sytax_tree.append(connect)
        return self


class UInt(Bits):
    """PyHCL UInt data class"""
    def __init__(self, width=0):
        """Inits a UInt object"""
        # TODO(SunnyChen): Temporary search frame stack 1 depth
        super().__init__(sys._getframe(1))
        # If inits a UInt object, it must be referred to a definition object
        # Such as Input(UInt(8)), Wire(UInt(8)) or Reg(UInt(8))
        self._ir_exp = ir.Ref()
        self._ir_exp.type = ir.UInt(width)


class SInt(Bits):
    """PyHCL SInt data class"""
    def __init__(self, width=0):
        """Inits a SInt object"""
        # TODO(SunnyChen): Temporary search frame stack 1 depth
        super().__init__(sys._getframe(1))
        self._ir_exp = ir.Ref()
        self._ir_exp.type = ir.SInt(width)


class Bool(UInt):
    """PyHCL Bool data class"""
    def __init__(self):
        """Inits a bool object"""
        super().__init__(1)

    @classmethod
    def asbool(cls, value: Union[int, str]):
        """Construct a Bool from a integer or string"""
        litexp = ir.LitUInt(ir.Gender.male, ir.UInt(1), True, value)
        ret = Bool()
        ret._ir_exp = litexp
        return ret


class Clock(Element):
    """PyHCL Clock data class"""
    def __init__(self):
        """Inits a clock object"""
        super().__init__(sys._getframe(1))
        self._ir_exp = ir.Ref()
        self._ir_exp.type = ir.Clock(1)


class AsyncReset(Element):
    """PyHCL AsyncReset data class"""
    def __init__(self):
        super().__init__(sys._getframe(1))
        self._ir_exp = ir.Ref()
        self._ir_exp.type = ir.AsyncReset(1)
