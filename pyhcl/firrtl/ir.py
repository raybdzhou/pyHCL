"""The IR of the framework, which organized as a AST

Filename: ir.py
Author: SunnyChen
"""
from __future__ import annotations
from dataclasses import dataclass
from dataclasses import field
from typing import Optional, List, Union
from pyhcl.core.resources import InstanceId, SourceInfo
from pyhcl.exceptions import EquivalentError
from enum import Enum
import abc

# Primitive operations, index 0 is arg's number, index 1 is parameters' number
PrimOp = {
    "add": [2, 0], "sub": [2, 0], "mul": [2, 0], "div": [2, 0], "rem": [2, 0],
    "lt": [2, 0], "leq": [2, 0], "gt": [2, 0], "geq": [2, 0], "eq": [2, 0],
    "neq": [2, 0], "pad": [1, 1], "asUInt": [1, 0], "asSInt": [1, 0],
    "asClock": [1, 0], "shl": [1, 1], "shr": [1, 1], "dshl": [2, 0],
    "dshr": [2, 0], "cvt": [1, 0], "neg": [1, 0], "not": [1, 0], "and": [2, 0],
    "or": [2, 0], "xor": [2, 0], "andr": [1, 0], "orr": [1, 0], "xorr": [1, 0],
    "cat": [2, 0], "bits": [1, 2], "head": [1, 1], "tail": [1, 1]
}

# Primitive operations in verilog
v_PrimOp = {
    "add": "+", "sub": "-", "mul": "*", "div": "/", "rem": "%", "lt": "<", "leq": "<=",
    "gt": ">", "geq": ">=", "eq": "==", "neq": "!=", "pad": "", "asUInt": "", "asSInt": "",
    "asClock": "", "shl": "<<", "shr": ">>", "dshl": "","dshr": "", "cvt": "", "neg": "-",
    "not": "~", "and": "&", "or": "|", "xor": "^", "andr": "", "orr": "", "xorr": "","cat": "",
    "bits": "", "head": "", "tail": ""
}

# emit level
emit_level = 0


# IR direction enum class
class Dir(Enum):
    Input = 0
    Output = 1


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


# TODO(SunnyChen): Do some check here?
# 1. like conditional signal must be 1 bit unsigned integer
# 2. FIRRTL internal rules


@dataclass
class BaseArg(metaclass=abc.ABCMeta):
    """Basic AST object class, an abstract class

    Attributes:
        sourceinfo: SourceInfo object, indicate the source info form python source file
    """

    sourceinfo: SourceInfo = None

    def add(self, basearg):
        """Method which could add BaseArg objects in current object"""
        pass

    def remove(self, basearg):
        """Method which could remove a BaseArg object from current object"""
        pass

    @abc.abstractmethod
    def emit(self) -> str:
        """The emit method should be implemented in all BaseArg objects

        Returns:
            A FIRRTL source code string
        """
        pass

    @abc.abstractmethod
    def emit_verilog(self) -> str:
        """The emit_verilog method should be implemented in all BaseArg objects
        
        Returns:
            A Verilog source code string
        
        """
        pass

    @classmethod
    def __subclasshook__(cls, subclass):
        """Overwrite __subclasshook__()

        Interface: emit() method
        """
        if cls is BaseArg:
            attr = set(dir(subclass))
            if "emit" in attr:
                return True
            else:
                return False
        else:
            return NotImplemented


@dataclass
class Definition(BaseArg):
    """Definition abstract class

    All define statements inherit from this class

    Attributes:
        sourceinfo: Definition AST object source code sourceinfo
        name: Definition AST object name
        instanceid: Core instance id
    """

    name: str = ""
    instanceid: InstanceId = None

    def emit(self) -> str:
        pass

    def emit_verilog(self) -> str:
        pass


class Gender(Enum):
    """Gender class for expression"""
    undefined = 0
    male = 1
    female = 2
    bi_gender = 3


@dataclass
class Type(object):
    """FIRRTL AST object type, abstract class Type

    Attributes:
        width: An integer number indicate current type object width
    """
    width: int = 0

    def flow_check(self, rtype) -> bool:
        """Check self.type <= rtype width, this only check the width,
        not include type check
        """
        pass

    def emit(self) -> str:
        pass

    def emit_verilog(self) -> str:
        pass


@dataclass
class Exp(object):
    """Abstract AST expression object

    Attributes:
        gender: Expression's FIRRTL gender
        type: Expression's type
        passive_type: True if the expression is passive type, otherwise false
    """
    gender: Gender = Gender.undefined
    type: Type = None
    passive_type: bool = True

    def emit(self) -> str:
        pass

    def emit_verilog(self) -> str:
        pass

    @classmethod
    def equivalent_check(cls, lexp, rexp) -> bool:
        """Check the equivalent of two expression

        Args:
            lexp, rexp: two expression to be checked

        Returns:
            True if both expression is equivalent, otherwise false
        """
        # One of the exp is ground type, but other is not, TypeError
        if rexp.type.__class__.__name__ == "Type":
            return True

        type_mismatch_case1 = isinstance(lexp.type, AggType) and not isinstance(rexp.type, AggType)
        type_mismatch_case2 = not isinstance(lexp.type, AggType) and isinstance(rexp.type, AggType)
        if type_mismatch_case1 or type_mismatch_case2:
            return False

        # Ground type
        lexp_is_ground_type = not isinstance(lexp.type, AggType) and isinstance(lexp.type, Type)
        rexp_is_ground_type = not isinstance(rexp.type, AggType) and isinstance(rexp.type, Type)
        if lexp_is_ground_type and rexp_is_ground_type:
            # All ground type equivalent to own type
            if lexp.type.__class__.__name__ != rexp.type.__class__.__name__:
                return False
            else:
                return True
        else:
            # Agg type
            if lexp.type.__class__.__name__ == "Vector" and rexp.type.__class__.__name__ == "Vector":
                # Vector
                if lexp.type.size == rexp.type.size and lexp.type.type.__class__.__name__ == rexp.type.type.__class__.__name__:
                    return True
                else:
                    return False
            elif lexp.type.__class__.__name__ == "Bundle" and rexp.type.__class__.__name__ == "Bundle":
                # Bundle
                if len(lexp.type.fields) == len(rexp.type.fields):
                    for i in range(0, len(lexp.type.fields)):
                        if lexp.type.fields[i].is_flip != rexp.type.fields[i].is_flip or lexp.type.fields[i].type.__class__.__name__ != rexp.type.fields[i].type.__class__.__name__:
                            return False
                    return True
                else:
                    return False
            else:
                return False


@dataclass
class Circuit(Definition):
    """Top level module Circuit definition AST class

    Attributes:
        name: Object's name
        sourceinfo: Object's source code info
        instanceid: Object's instance core id
        modules: Modules in current circuit
    """

    modules: List[Definition] = field(default_factory=list, compare=False)

    def add(self, module: Definition):
        """Add a module in current circuit

        Args:
            module: Module to be added, must be a object

        Raises:
            TypeError: Module to be added is not a Module object
            ValueError: The module to be added is in the list already
        """
        if not isinstance(module, Module):
            raise TypeError("Not a module instance")
        elif module in self.modules:
            raise ValueError("The module is already in the list")
        else:
            self.modules.append(module)
            self.instanceid.add_child(module.instanceid.id)
            module.instanceid.add_parent(self.instanceid.id)

    def remove(self, module: Definition):
        """Remove a module in current circuit

        Args:
            module: Module to be removed, must be a object

        Raises:
            TypeError: Module to be removed is not a Module object
            ValueError: The module to be remove is not in the list
        """
        if not isinstance(module, Module):
            raise TypeError("Not a module instance")
        else:
            self.modules.remove(module)

        self.instanceid.remove_child(module.instanceid.id)
        module.instanceid.remove_parent(self.instanceid.id)

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current circuit

        Returns:
            The FIRRTL code string
        """
        # Using a table to record the result, do not use "+" operator to increase execution time
        global emit_level
        cat_table: List[str] = []
        if not self.sourceinfo is None:
            cat_table.append("circuit {} : {}\n".format(self.name, self.sourceinfo.emit()))
        else:
            cat_table.append("circuit {} :\n".format(self.name))

        emit_level = emit_level + 1
        for m in self.modules:
            cat_table.append("  "*emit_level + m.emit() + "\n")
        emit_level = emit_level - 1

        return "".join(cat_table)
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current circuit

        Returns:
            The Verilog code string
        """
        global emit_level
        cat_table: List[str] = []
        for m in self.modules:
            cat_table.append(m.emit_verilog() + '\n')
        return "".join(cat_table)


@dataclass
class Module(Definition):
    """Module AST object class

    Attributes:
        name: Object's name
        sourceinfo: Object's source code information
        id: Object's core id
        ports: Module's ports list
        stats: Module's statements list
    """

    ports: List[Definition] = field(default_factory=list, compare=False)
    stats: List[BaseArg] = field(default_factory=list, compare=False)

    def add(self, basearg):
        """Add a port or statement in list

        Args:
            basearg: Port or Statement object

        Raise:
            TypeError: Item to be add is not a port neither a statement
        """
        if isinstance(basearg, Port):
            self.ports.append(basearg)
            self.instanceid.child_id.append(basearg.instanceid.id)
            basearg.instanceid.parent_id.append(self.instanceid.id)
        elif isinstance(basearg, DefStat):
            self.stats.append(basearg)
            self.instanceid.child_id.append(basearg.instanceid.id)
            basearg.instanceid.parent_id.append(self.instanceid.id)
        elif isinstance(basearg, CmdStat):
            self.stats.append(basearg)
        else:
            raise TypeError("Item to be add is not a port neither a statement")

    def remove(self, basearg):
        """Remove a port or statement in list

        Args:
            basearg: Port or Statement object to be removed

        Raise:
            TypeError: Item to be removed is not a port neither a statement
            ValueError: Item to be removed is not in the list
        """
        if isinstance(basearg, Port):
            self.ports.remove(basearg)
        elif isinstance(basearg, DefStat) or isinstance(basearg, CmdStat):
            self.stats.remove(basearg)
        else:
            raise TypeError("Item to be removed is not a port neither a statement")

        self.instanceid.child_id.remove(basearg.instanceid.id)
        basearg.instanceid.parent_id.remove(self.instanceid.id)

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current module

        Returns:
            The FIRRTL code string
        """
        global emit_level
        cat_table: List[str] = []
        if self.sourceinfo is None:
            cat_table.append("module {} : \n".format(self.name))
        else:
            cat_table.append("module {} : {}\n".format(self.name, self.sourceinfo.emit()))

        emit_level = emit_level + 1
        # Generate ports define
        for p in self.ports:
            cat_table.append("  "*emit_level + p.emit())
        cat_table.append("\n")

        # Generate statements define
        for s in self.stats:
            cat_table.append("  "*emit_level + s.emit())
        cat_table.append("\n")
        emit_level = emit_level - 1

        return "".join(cat_table)
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current module

        Returns:
            The Verilog code string
        """
        global emit_level
        port_declares: List[str] = []
        stat_declares: List[str] = []
        cat_table: List[str] = []

        emit_level = emit_level + 1
        for p in self.ports:
            port_declares.append("\n" + "\t"*emit_level + p.emit_verilog())
        emit_level = emit_level - 1

        emit_level = emit_level + 1
        for s in self.stats:
            stat_declares.append("\n" + "\t"*emit_level + s.emit_verilog())
        emit_level = emit_level - 1

        if self.sourceinfo is None:
            cat_table.append(f"module {self.name}({''.join(port_declares)}\n);\n{''.join(stat_declares)}\nendmodule")
        else:
            cat_table.append(f"module {self.name}(\t{self.sourceinfo.emit_verilog()}{''.join(port_declares)}\n);\n{''.join(stat_declares)}\nendmodule")

        return "".join(cat_table)


@dataclass
class Port(Definition):
    """Port AST object class

    Attributes:
        name: Object's name
        sourceinfo: Object's source code information
        id: Object's core id
        direction: Port's direction
        type: Port's type
    """
    direction: Dir = Dir.Input
    type: Type = None

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current port

        Returns:
            The FIRRTL code string
        """
        if self.direction == Dir.Input:
            dir_str = "input"
        else:
            dir_str = "output"
        if self.sourceinfo is None:
            return "{} {} : {}\n".format(dir_str, self.name, self.type.emit())
        else:
            return "{} {} : {} {}\n".format(dir_str, self.name, self.type.emit(), self.sourceinfo.emit_verilog())
    
    def emit_verilog(self) -> str:
        """Generate and return the FIRRTL code of current port

        Returns:
            The FIRRTL code string
        """
        if self.direction == Dir.Input:
            dir_str = "input"
        else:
            dir_str = "output"
        if self.sourceinfo is None:
            return f"{dir_str}\t{self.type.emit_verilog()}{self.name};"
        else:
            return f"{dir_str}\t{self.type.emit_verilog()}{self.name};\t{self.sourceinfo.emit_verilog()}"


@dataclass
class Field(Definition):
    """Field AST object class

    Attributes:
        name: Object's name
        sourceinfo: Object's source code information
        id: Object's core id
        is_flip: Is current field flip
        type: Field's type
    """

    is_flip: bool = False
    type: Type = None

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current field

        Returns:
            The FIRRTL code string
        """
        if self.is_flip:
            return "flip {} : {}".format(self.name, self.type.emit())
        else:
            return "{} : {}".format(self.name, self.type.emit())
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current field

        Returns:
            The Verilog code string
        """
        pass


@dataclass
class DefStat(Definition):
    """Abstract AST class represent all definition statement"""
    name: str = ""
    instanceid: InstanceId = None
    sourceinfo: SourceInfo = None

    def emit(self) -> str:
        pass

    def emit_verilog(self) -> str:
        pass


@dataclass
class DefWire(DefStat):
    """AST class represent a wire definition

    Attributes:
        name: Object's name
        sourceinfo: Object's source code information
        id: Object's core id
        type: Wire's type
    """
    type: Type = None

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current wire definition

        Returns:
            The FIRRTL code string
        """
        if self.sourceinfo is None:
            return "wire {} : {}\n".format(self.name, self.type.emit())
        else:
            return "wire {} : {} {}\n".format(self.name, self.type.emit(), self.sourceinfo.emit())
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current wire definition

        Returns:
            The Verilog code string
        """
        if self.sourceinfo is None:
            return f"wire\t{self.type.emit_verilog()}{self.name};"
        else:
            return f"wire\t{self.type.emit_verilog()}{self.name};\t{self.sourceinfo.emit_verilog()}"


@dataclass
class DefReg(DefStat):
    """AST class represent a register definition, without reset operation

    Attributes:
        name: Object's name
        sourceinfo: Object's source code information
        id: Object's core id
        type: Register's type
        clk: Register's update clock
    """
    clk: Exp = None
    type: Type = None

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current register definition,
        without reset operation

        Returns:
            The FIRRTL code string
        """
        if self.sourceinfo is None:
            return "reg {} : {}, {}\n".format(self.name, self.type.emit(), self.clk.emit())
        else:
            return "reg {} : {}, {} {}\n".format(self.name, self.type.emit(), self.clk.emit(), self.sourceinfo.emit())
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current register definition

        Returns:
            The Verilog code string
        """
        if self.sourceinfo is None:
            return f"reg\t{self.type.emit_verilog()}{self.name};"
        else:
            return f"reg\t{self.type.emit_verilog()}{self.name};\t{self.sourceinfo.emit_verilog()}"


@dataclass
class DefRegReset(DefStat):
    """AST class represent a register definition, with reset operation

    When the reset_signal is true, then the register will set to reset_value

    Attributes:
        name: Object's name
        sourceinfo: Object's source code information
        id: Object's core id
        type: Register's type
        clk: Register's update clock
        reset_signal: Register's reset signal
        reset_value: Register's reset value
    """
    clk: Exp = None
    type: Type = None
    reset_signal: Exp = None
    reset_value: Exp = None

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current register definition,
        with reset operation

        Returns:
            The FIRRTL code string
        """
        if self.sourceinfo is None:
            return "reg %s : %s, %s with: (reset => (%s, %s))\n" % (self.name, self.type.emit(), self.clk.emit(),
                                                                      self.reset_signal.emit(), self.reset_value.emit())
        else:
            return "reg %s : %s, %s with: (reset => (%s, %s)) %s\n" % (self.name, self.type.emit(), self.clk.emit(),
                                                                         self.reset_signal.emit(), self.reset_value.emit(),
                                                                         self.sourceinfo.emit())
    

    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current register definition

        Returns:
            The Verilog code string
        """
        if self.sourceinfo is None:
            return f"reg\t{self.type.emit_verilog()}{self.name};"
        else:
            return f"reg\t{self.type.emit_verilog()}{self.name};\t{self.sourceinfo.emit_verilog()}"


@dataclass
class DefMem(DefStat):
    """AST class represent a memory definition, could be synchronous or asynchronous

    Attributes:
        name: Object's name
        sourceinfo: Object's source co.ir_expde information
        id: Object's core id
        type: Memory's type
        size: Memory's size
        sync: Synchronous read memory or not
    """
    type: Type = None
    size: int = 0
    sync: bool = False

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current memory definition

        Returns:
            The FIRRTL code string
        """
        cat_table = []
        if self.sync:
            cat_table.append("smem ")
        else:
            cat_table.append("cmem ")
        if self.sourceinfo is None:
            cat_table.append("{} : {}\n".format(self.name, self.type.emit()))
        else:
            cat_table.append("{} : {} {}\n".format(self.name, self.type.emit(), self.sourceinfo.emit()))

        return "".join(cat_table)
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current memory definition

        Returns:
            The Verilog code string
        """
        if self.sourceinfo is None:
            return f"reg\t{self.type.emit_verilog()}{self.name}\t[0:{self.size-1}];"
        else:
            return f"reg\t{self.type.emit_verilog()}{self.name}\t[0:{self.size-1}];\t{self.sourceinfo.emit_verilog()}"


@dataclass
class DefNode(DefStat):
    """AST class represent a node definition

    Attributes:
        name: Object's name
        sourceinfo: Object's source code information
        id: Object's core id
        node_exp: Expression of the node
    """
    node_exp: Exp = None

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current node definition

        Returns:
            The FIRRTL code string
        """
        if self.sourceinfo is None:
            return "node {} = {}\n".format(self.name, self.node_exp.emit())
        else:
            return "node {} = {} {}\n".format(self.name, self.node_exp.emit(), self.sourceinfo.emit())
    

    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current node definition

        Returns:
            The Verilog code string
        """
        if self.sourceinfo is None:
            return f"wire\t{self.node_exp.type.emit_verilog()}{self.name} = {self.node_exp.emit_verilog()};"
        else:
            return f"wire\t{self.node_exp.type.emit_verilog()}{self.name} = {self.node_exp.emit_verilog()};\t{self.sourceinfo.emit_verilog()}"


@dataclass
class InstModule(DefStat):
    """AST class represent a module instance definition

    Attributes:
        name: Object's name
        sourceinfo: Object's source code information
        id: Object's core id
        module: The referenced module
    """
    module: Module = None

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current node definition

        Returns:
            The FIRRTL code string
        """
        if self.sourceinfo is None:
            return "inst {} of {}\n".format(self.name, self.module.name)
        else:
            return "inst {} of {} {}\n".format(self.name, self.module.name, self.sourceinfo.emit())
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of instance definition

        Returns:
            The Verilog code string
        """
        port_decs: List[str] = []
        inst_ports: List[str] = []
        global emit_level
        emit_level = emit_level + 1
        for p in self.module.ports:
            port_decs.append(f"wire\t{p.type.emit_verilog()}\t{self.name}_{p.name}")
            inst_ports.append("\n" + "\t" * emit_level + f".{p.name}({self.name}_{p.name}),")
        port_dec = '\n'.join(port_decs)
        if self.sourceinfo is None:
            return f"{port_dec}\n{self.module.name}\t{self.name}({''.join(inst_ports)});"
        else:
            return f"{port_dec}\n{self.module.name}\t{self.name}(\t{self.sourceinfo.emit_verilog()}{''.join(inst_ports)});"


@dataclass
class RefMemPort(DefStat):
    """AST class represent a reference of memory port statement

    Attributes:
        name: Object's name - this may required from global name pool
        sourceinfo: Object's source code information
        id: Object's core id
        clk: Clock signal
        refmem: Refer memory
        addr: Address expression
        read_or_write: Read memroy or write memory
                       True if read, otherwise write
        infer: Infer or not (Aggregate Type use)
    """
    clk: Exp = None
    refmem: DefMem = None
    addr: Exp = None
    read_or_write: bool = True
    infer: bool = False

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current reference of memory port statement

        Returns:
            The FIRRTL code string
        """
        cat_table = []
        if self.infer:
            cat_table.append("infer mport ")
        else:
            if self.read_or_write:
                cat_table.append("read mport ")
            else:
                cat_table.append("write mport ")
        cat_table.append("{} = {}[{}], {}".format(self.name, self.refmem.name, self.addr.emit(), self.clk.emit()))

        if self.sourceinfo is None:
            cat_table.append("\n")
        else:
            cat_table.append(" %s\n" % self.sourceinfo.emit())

        return "".join(cat_table)
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current memory port statement

        Returns:
            The Verilog code string
        """
        memportdeclares = ""
        memportdeclares += f"wire {self.refmem.type.emit_verilog()}{self.refmem.name}_{self.name}_data;\n"
        memportdeclares += f"wire [{get_width(self.refmem.size)-1}:0] {self.refmem.name}_{self.name}_addr;\n"
        memportdeclares += f"wire {self.refmem.name}_{self.name}_en;\n"
        memportdeclares += f"assign {self.refmem.name}_{self.name}_addr = {self.addr.emit_verilog()};\n"
        memportdeclares += f"assign {self.refmem.name}_{self.name}_en = 1\'h1;\n"
        if self.read_or_write is False:
            memportdeclares += f'wire {self.refmem.name}_{self.name}_mask;\n'
        return memportdeclares




@dataclass
class CmdStat(BaseArg):
    """AST abstract class represent command statements"""
    sourceinfo: SourceInfo = None

    def emit(self) -> str:
        pass

    def emit_verilog(self) -> str:
        pass


@dataclass(init=False)
class Connect(CmdStat):
    """AST class represent a connect operation

    Attributes:
        sourceinfo: Object's source code information
        lexp: Left-hand side expression being connected
        rexp: Right-hand side expression
    """
    lexp: Exp = None
    rexp: Exp = None

    def __init__(self, sourceinfo: SourceInfo = None, lexp: Exp = None, rexp: Exp = None):
        """Inits a connect object

        Args:
            lexp: Left-hand side expression being connected
            rexp: Right-hand expression being connected

        Raises:
            TypeError: If one of the args is not a Exp object
            EquivalentError: If two expression is not equivalent
            ValueError: If two expressions' gender are not match
        """
        if not isinstance(lexp, Exp) or not isinstance(rexp, Exp):
            raise TypeError("One of the args is not a Exp object")

        # if not Exp.equivalent_check(lexp, rexp):
        #     raise EquivalentError("Expression going to connect is not equivalent", lexp, rexp)

        # if not lexp.type.flow_check(rexp.type):
        #     raise FlowCheckError("Expression not pass flow check", lexp, rexp)

        # Check expression's gender
        # lexp_gender_check = lexp.gender == Gender.female or lexp.gender == Gender.bi_gender
        # rexp_gender_check = rexp.gender == Gender.male or rexp.gender == Gender.bi_gender or rexp.passive_type
        # if not lexp_gender_check or not rexp_gender_check:
        #     raise ValueError("Two expressions gender are not match")

        self.lexp = lexp
        self.rexp = rexp
        self.sourceinfo = sourceinfo

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current connect statement

        Returns:
            The FIRRTL code string
        """
        if self.sourceinfo is None:
            return "{} <= {}\n".format(self.lexp.emit(), self.rexp.emit())
        else:
            return "{} <= {} {}\n".format(self.lexp.emit(), self.rexp.emit(), self.sourceinfo.emit())
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current statement

        Returns:
            The Verilog code string
        """
        if self.sourceinfo is None:
            return f"assign\t{self.lexp.emit_verilog()} = {self.rexp.emit_verilog()};"
        else:
            return f"assign\t{self.lexp.emit_verilog()} = {self.rexp.emit_verilog()};\t{self.sourceinfo.emit_verilog()}"


@dataclass
class IsInvalid(CmdStat):
    """AST class represent a isinvalid expression

    Attributes:
        sourceinfo: Object's source code information
        invad_exp: The expression to define invalid
    """
    invad_exp: Exp = None

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current isinvalid statement

        Returns:
            The FIRRTL code string
        """
        if self.sourceinfo is None:
            return "%s is invalid\n" % self.invad_exp.emit()
        else:
            return "%s is invalid %s\n" % (self.invad_exp.emit(), self.sourceinfo.emit())
    
    def emit_verilog(self) -> str:
        pass


@dataclass
class Stop(CmdStat):
    """AST class represent a stop expression

    Attributes:
        sourceinfo: Object's source code information
        clk: Clock signal
        con: Condition expression
        exit_code: Exit code
    """
    clk: Exp = None
    con: Exp = None
    exit_code: int = 0

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current stop statement

        Returns:
            The FIRRTL code string
        """
        if self.sourceinfo is None:
            return "stop({}, {}, {})\n".format(self.clk.emit(), self.con.emit(), self.exit_code)
        else:
            return "stop({}, {}, {}) {}\n".format(self.clk.emit(), self.con.emit(), self.exit_code, self.sourceinfo.emit())
    
    def emit_verilog(self) -> str:
        pass


@dataclass
class Skip(CmdStat):
    """AST class represent a skip expression

    Attributes:
        sourceinfo: Object's source code information
    """

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current stop statement

        Returns:
            The FIRRTL code string
        """
        if self.sourceinfo is None:
            return "skip\n"
        else:
            return "skip %s\n" % self.sourceinfo.emit()
    
    def emit_verilog(self) -> str:
        pass


@dataclass
class Printf(CmdStat):
    """AST class represent a printf statement

    Attributes:
        sourceinfo: Object's source code information
        clk: Clock signal
        con: Condition expression
        printstr: Format print string
        vars: Print variables list
    """
    clk: Exp = None
    con: Exp = None
    printstr: str = ""
    vars: List[Exp] = field(default_factory=list, compare=False)

    def emit(self) -> str:
        """Genereate and return the FIRRTL code of current printf statement

        Return:
            The FIRRTL code string
        """
        cat_table = []
        cat_table.append("printf({}, {}, \"{}\", ".format(self.clk.emit(), self.con.emit(), self.printstr))

        for i in range(0, len(self.vars)-1):
            cat_table.append("%s, " % self.vars[i].emit())
        cat_table.append("%s)" % self.vars[len(self.vars)-1].emit())

        if self.sourceinfo is None:
            cat_table.append("\n")
        else:
            cat_table.append(" %s\n" % self.sourceinfo.emit())

        return "".join(cat_table)
    
    def emit_verilog(self) -> str:
        pass


@dataclass
class WhenBegin(CmdStat):
    """AST class represent a when statement begin

    Attributes:
        sourceinfo: Object's source code information
        con: When statement conditional expression
    """
    con: Exp = None

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current when begin statement

        Return:
            The FIRRTL code string
        """
        if self.sourceinfo is None:
            return "when %s :\n" % self.con.emit()
        else:
            return "when %s : %s\n" % (self.con.emit(), self.sourceinfo.emit())
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current when begin statement

        Returns:
            The Verilog code string
        """
        if self.sourceinfo is None:
            return f"if ({self.con.emit_verilog()}) begin"
        else:
            return f"if ({self.con.emit_verilog()}) begin\t{self.sourceinfo.emit_verilog()}"
        


@dataclass
class WhenEnd(CmdStat):
    """AST class represent a when statement end

    Attributes:
        sourceinfo: Object's source code information
    """

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current when end statement

        Return:
            The FIRRTL code string
        """
        global emit_level
        if self.sourceinfo is None:
            return "  "*emit_level + "skip\n"
        else:
            return "  "*emit_level + "skip %s\n" % self.sourceinfo.emit()
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current when end statement

        Returns:
            The Verilog code string
        """
        return "end"


@dataclass
class ElseBegin(CmdStat):
    """AST class represent a else begin statement

    Attributes:
        sourceinfo: Object's source code information
        stats: Else statments list
    """
    stats: List[BaseArg] = field(default_factory=list, compare=False)

    def add(self, basearg):
        """Add a statement to else statements list"""
        self.stats.append(basearg)

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current else begin statement

        Return:
            The FIRRTL code string
        """
        global emit_level
        cat_table = []
        if self.sourceinfo is None:
            cat_table.append("  "*emit_level + "else : \n")
        else:
            cat_table.append("  "*emit_level + "else : %s\n" % self.sourceinfo.emit())

        emit_level = emit_level + 1
        for s in self.stats:
            cat_table.append("  "*emit_level + s.emit())

        return "".join(cat_table)
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current else begin statement

        Returns:
            The Verilog code string
        """
        global emit_level
        cat_table: List[str] = []
        if self.sourceinfo is None:
            cat_table.append("else begin")
        else:
            cat_table.append(f"else begin\t{self.sourceinfo.emit_verilog()}")
        
        emit_level = emit_level + 1
        for s in self.stats:
            cat_table.append("\t"*emit_level + s.emit_verilog())

        return "\n".join(cat_table)

@dataclass
class ElseEnd(CmdStat):
    """AST class represent a else end statement

    Attributes:
        sourceinfo: Object's source code information
    """

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current else end statement

        Return:
            The FIRRTL code string
        """
        global emit_level
        if self.sourceinfo is None:
            return "  "*emit_level + "skip\n"
        else:
            return "  "*emit_level + "skip %s\n" % self.sourceinfo.emit()
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current else end statement

        Returns:
            The Verilog code string
        """
        return "end"


@dataclass
class When(CmdStat):
    """AST class represent a when statement

    Attributes:
        sourceinfo: Object's source code information
        whenbegin: When statement begin
        whenend: When statement end
        has_else: Has else branch or not
        elsebegin: Else statement begin
        elseend: Else statement end
        stats: When statements
    """
    whenbegin: WhenBegin = None
    whenend: WhenEnd = None
    has_else: bool = False
    elsebegin: ElseBegin = None
    elseend: ElseEnd = None
    stats: List[BaseArg] = field(default_factory=list, compare=False)

    def add(self, BaseArg):
        """Add a statement to when statements list"""
        self.stats.append(BaseArg)

    def emit(self) -> str:
        """Genereate and return the FIRRTL code of current when statement

        Return:
            The FIRRTL code string
        """
        global emit_level
        cat_table = []
        cat_table.append(self.whenbegin.emit())

        emit_level = emit_level + 1
        for s in self.stats:
            cat_table.append("  "*emit_level + s.emit())
        cat_table.append(self.whenend.emit())
        emit_level = emit_level - 1

        if self.has_else:
            cat_table.append(self.elsebegin.emit())
            cat_table.append(self.elseend.emit())
            emit_level = emit_level - 1

        return "".join(cat_table)
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current when statement

        Returns:
            The Verilog code string
        """
        global emit_level
        cat_table: List[str] = []
        cat_table.append(self.whenbegin.emit_verilog())

        emit_level = emit_level + 1
        for s in self.stats:
            cat_table.append("\t"*emit_level + s.emit_verilog())
        cat_table.append(self.whenend.emit_verilog())
        emit_level = emit_level - 1

        if self.has_else:
            cat_table.append(self.elsebegin.emit_verilog())
            cat_table.append(self.elseend.emit_verilog())
            emit_level = emit_level - 1

        return "\n".join(cat_table)


@dataclass
class UInt(Type):
    """Unsigned integer type

    Attributes:
        width: An integer number indicate current type object width
    """
    def flow_check(self, rtype) -> bool:
        if self.width == 0 or rtype.width == 0:
            # if not define, throw to FIRRTL
            return True
        else:
            if self.width < rtype.width:
                return False
            else:
                return True

    def emit(self) -> str:
        """Return FIRRTL source code string"""
        if self.width == 0:
            return "UInt"
        else:
            return "UInt<{}>".format(self.width)
    
    def emit_verilog(self) -> str:
        """Return Verilog source code string"""
        if self.width <= 1:
            return ""
        else:
            return f"[{self.width-1}:0]\t"


@dataclass
class SInt(Type):
    """Signed integer type

    Attributes:
        width: An integer number indicate current type object width
    """
    def flow_check(self, rtype) -> bool:
        if self.width == 0 or rtype.width == 0:
            # if not define, throw to FIRRTL
            return True
        else:
            if self.width < rtype.width:
                return False
            else:
                return True

    def emit(self) -> str:
        """Return FIRRTL source code string"""
        if self.width == 0:
            return "SInt"
        else:
            return "SInt<{}>".format(self.width)
    
    def emit_verilog(self) -> str:
        """Return Verilog source code string"""
        if self.width <= 1:
            return ""
        else:
            return f"[{self.width-1}:0]\t"


@dataclass
class Clock(Type):
    """Clock type"""
    def flow_check(self, rtype) -> bool:
        # No use
        return True

    def emit(self) -> str:
        """Return FIRRTL source code string"""
        return "Clock"
    
    def emit_verilog(self) -> str:
        """Return Verilog source code string"""
        return ""


@dataclass
class AsyncReset(Type):
    """AsyncReset type"""
    def flow_check(self, rtype) -> bool:
        # No use
        return True

    def emit(self) -> str:
        """Return FIRRTL source code string"""
        return "AsyncReset"
    
    def emit_verilog(self) -> str:
        """Return Verilog source code string"""
        return ""


@dataclass
class AggType(Type):
    """Aggregate type abstract class

    Attributes:
        width: An integer number indicate current type object with (no use here)
        size: Type size
    """
    size: int = 0

    def emit(self) -> str:
        pass

    def emit_verilog(self) -> str:
        pass


@dataclass
class Vector(AggType):
    """Vector type

    Attributes:
        width: An integer number indicate current type object with (no use here)
        size: Type size
        type: Vector's elements' type
    """
    type: Type = None

    def flow_check(self, rtype) -> bool:
        return self.type.flow_check(rtype.type)

    def emit(self) -> str:
        """Return FIRRTL source code string"""
        return "{}[{}]".format(self.type.emit(), self.size)
    
    def emit_verilog(self) -> str:
        pass


@dataclass
class Bundle(AggType):
    """Bundle type

    Attributes:
        width: An integer number indicate current type object with (no use here)
        size: Type size (no use here)
        fields: Fields list
    """
    fields: List[Field] = field(default_factory=list, compare=False)

    def flow_check(self, rtype) -> bool:
        if len(self.fields) != len(rtype.fields):
            return False
        else:
            for i in range(0, len(self.fields)):
                if not self.fields[i].type.flow_check(rtype.fields[i].type):
                    return False
            return True

    def add(self, _field: Field):
        """Add a field to current bundle

        Args:
            _field: The field to be added
        """
        self.fields.append(_field)

    def remove(self, _field: Field):
        """Remove a field from current bundle

        Args:
            _field: The field to be removed

        Raises:
            ValueError: The field is not in the current list
        """
        self.fields.remove(_field)

    def emit(self) -> str:
        """Return FIRRTL source code string"""
        cat_table = []
        cat_table.append("{")
        for i in range(0, len(self.fields)-1):
            cat_table.append(self.fields[i].emit() + ", ")
        cat_table.append(self.fields[len(self.fields)-1].emit() + "}")

        return "".join(cat_table)
    
    def emit_verilog(self) -> str:
        pass


@dataclass
class LitInt(Exp):
    """AST abstract class represent a literal integer

    Attributes:
        gender: Expression's FIRRTL gender
        type: Expression's type
        passive_type: True if the expression is passive type, otherwise false
        initial: Initial value, could be int or str
        width: Optional, Integer's width
    """
    initial: Union[int, str] = None
    gender: Gender = Gender.male
    passive_type: bool = True

    def emit(self) -> str:
        pass

    def emit_verilog(self) -> str:
        pass


@dataclass
class LitUInt(LitInt):
    """AST class represent a unsigned literal integer

    Attributes:
        gender: Expression's FIRRTL gender
        type: Expression's type
        passive_type: True if the expression is passive type, otherwise false
        initial: Initial value, could be int or str
        width: Optional, Integer's width
    """
    type: UInt = UInt(0)

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current unsigned literal integer

        Returns:
            The FIRRTL code string
        """
        if self.type.width == 0:
            return "UInt({})".format(self.initial)
        else:
            if isinstance(self.initial, int):
                return "UInt<{}>({})".format(self.type.width, self.initial)
            else:
                return "UInt<{}>(\"{}\")".format(self.type.width, self.initial)
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current unsigned literal integer

        Returns:
            The Verilog code string
        """
        if self.type.width == 0:
            return self.initial
        else:
            if isinstance(self.initial, int):
                return f"{self.type.width}\'d{self.initial}"
            else:
                return f"{self.type.width}\'{self.initial}"



@dataclass
class LitSInt(LitInt):
    """AST class represent a unsigned literal integer

    Attributes:
        gender: Expression's FIRRTL gender
        type: Expression's type
        passive_type: True if the expression is passive type, otherwise false
        initial: Initial value, could be int or str
        width: Optional, Integer's width
    """
    type: SInt = SInt(0)

    def emit(self) -> str:
        """Generate and return the FIRRTL code of current unsigned literal integer

        Returns:
            The FIRRTL code string
        """
        if self.type.width == 0:
            return "SInt({})".format(self.initial)
        else:
            if isinstance(self.initial, int):
                return "SInt<{}>({})".format(self.type.width, self.initial)
            else:
                return "SInt<{}>(\"{}\")".format(self.type.width, self.initial)
    
    def emit_verilog(self) -> str:
        """Generate and return the Verilog code of current unsigned literal integer

        Returns:
            The Verilog code string
        """
        if self.type.width == 0:
            return self.initial
        else:
            if isinstance(self.initial, int):
                return f"-{self.type.width}\'d{-self.initial}" if self.initial < 0 else f"{self.type.width}\'d{self.initial}"
            else:
                return f"-{self.type.width}\'{self.initial[1:]}" if self.initial[0] == "-" else f"{self.type.width}\'{self.initial}"


@dataclass
class ValidIf(Exp):
    """AST class represent a validif expression

    Attributes:
        gender: Expression's FIRRTL gender
        type: Expression's type
        passive_type: True if the expression is passive type, otherwise false
        con: Conditional expression
        vad: Valid expression
    """
    gender: Gender = Gender.male
    passive_type: bool = True
    con: Exp = None
    vad: Exp = None

    def emit(self) -> str:
        """Return FIRRTL source code string"""
        return "validif({}, {})".format(self.con.emit(), self.vad.emit())
    
    def emit_verilog(self) -> str:
        """Return FIRRTL source code string"""
        return f"{self.con.emit_verilog()} ? {self.vad.emit_verilog()} : Z"


@dataclass
class Mux(Exp):
    """AST class represent a mux expression

    Attributes:
        gender: Expression's FIRRTL gender
        type: Expression's type
        passive_type: True if the expression is passive type, otherwise false
        con: Conditional expression
        true_exp: True expression
        false_exp: False expression
    """
    gender: Gender = Gender.male
    passive_type: bool = True
    con: Exp = None
    true_exp: Exp = None
    false_exp: Exp = None

    def emit(self) -> str:
        """Return FIRRTL source code string"""
        return "mux({}, {}, {})".format(self.con.emit(), self.true_exp.emit(), self.false_exp.emit())
    

    def emit_verilog(self) -> str:
        """Return Verilog source code string"""
        return f"{self.con.emit_verilog()} ? {self.true_exp.emit_verilog()} : {self.false_exp.emit_verilog()}"


@dataclass
class Op(Exp):
    """AST class represent a operation expression

    Attributes:
        gender: Expression's FIRRTL gender
        type: Expression's type
        passive_type: True if the expression is passive type, otherwise false
        name: Operation's name, must be one of the Primop
        operands: Operation's operands
        parameters: Operation's parameters
    """
    gender: Gender = Gender.male
    passive_type: bool = True
    name: str = ""
    operands: List[Exp] = field(default_factory=list, compare=False)
    parameters: List[int] = field(default_factory=list, compare=False)

    def __init__(self, gender: Gender = Gender.male, type: Type = None, passive_type: bool = True, name: str = "",
                 operands: List[Exp] = None, parameters: List[int] = None):
        """Inits a Op object, Would raise TypeError, ValueError"""
        # Type check
        if operands is None:
            self.operands: List[Exp] = []
        elif not isinstance(operands, list):
            raise TypeError("Operands list not a list object")
        else:
            self.operands = operands
        if parameters is None:
            self.parameters: List[int] = []
        elif not isinstance(parameters, list):
            raise TypeError("Parameters list not a list object")
        else:
            self.parameters = parameters

        # Op legal check
        if not name in PrimOp:
            raise ValueError("Not a primitive operation")
        elif len(operands) != PrimOp[name][0] or len(parameters) != PrimOp[name][1]:
            raise ValueError("Operands list or parameters list size not match current operation")

        self.gender = gender
        self.type = type
        self.passive_type = passive_type
        self.name = name

    def emit(self) -> str:
        """Return FIRRTL source code string"""
        cat_table = []
        cat_table.append("%s(" % self.name)

        if len(self.parameters) == 0:
            for i in range(0, len(self.operands)-1):
                cat_table.append("%s, " % self.operands[i].emit())
            cat_table.append("%s)" % self.operands[len(self.operands)-1].emit())
        else:
            for o in self.operands:
                cat_table.append("%s, " % o.emit())
            for i in range(0, len(self.parameters)-1):
                cat_table.append("{}, ".format(self.parameters[i]))
            cat_table.append("{})".format(self.parameters[len(self.parameters)-1]))

        return "".join(cat_table)
    
    def emit_verilog(self) -> str:
        """Return FIRRTL source code string"""

        if len(self.parameters) == 0:
            return f" {v_PrimOp[self.name]} ".join([operand.emit_verilog() for operand in self.operands])
        else:
            operands = [operand.emit_verilog() for operand in self.operands]
            parameters = [parameter for parameter in self.parameters]
            return f" {v_PrimOp[self.name]} ".join(operands + parameters)



@dataclass
class Ref(Exp):
    """AST abstract class represent a reference id

    Attributes:
        gender: Expression's FIRRTL gender
        type: Expression's type
        passive_type: True if the expression is passive type, otherwise false
        ref_arg: Arg being refered
    """
    ref_arg: Definition = None

    def emit(self) -> str:
        pass

    def emit_verilog(self) -> str:
        pass


@dataclass
class RefId(Ref):
    """AST class represent a reference of a definition

    Attributes:
        gender: Expression's FIRRTL gender
        type: Expression's type
        passive_type: True if the expression is passive type, otherwise false
        ref_arg: Arg being refered
    """

    def emit(self) -> str:
        """Return FIRRTL source code string"""
        if isinstance(self.ref_arg, Definition):
            return "%s" % self.ref_arg.name
        else:
            return "%s" % self.ref_arg.emit()
        
    def emit_verilog(self) -> str:
        """Return Verilog source code string"""
        if isinstance(self.ref_arg, Definition):
            return self.ref_arg.name
        else:
            return self.ref_arg.emit_verilog()


@dataclass
class RefSubfield(Ref):
    """AST class represent a reference of a bundle's field

    Attributes:
        gender: Expression's FIRRTL gender
        type: Expression's type
        passive_type: True if the expression is passive type, otherwise false
        ref_arg: Bundle being refered
        ref_field: Field being refered
    """
    ref_arg = None
    ref_field: Union[Field, Ref] = None

    def emit(self) -> str:
        """Return FIRRTL source code string"""
        if isinstance(self.ref_field, Field):
            return "{}.{}".format(self.ref_arg.emit(), self.ref_field.name)
        elif self.ref_field is None:
            return "{}".format(self.ref_arg.emit())
        else:
            return "{}.{}".format(self.ref_arg.emit(), self.ref_field.emit())
    
    def emit_verilog(self) -> str:
        """Return FIRRTL source code string"""
        # if isinstance(self.ref_field, Field):
        #     return f"{self.ref_arg.emit_verilog()}_{self.ref_field.name}"
        # elif self.ref_field is None:
        #     return f"{self.ref_arg.emit_verilog()}"
        # else:
        #     return f"{self.ref_arg.emit_verilog()}_{self.ref_field.emit_verilog()}"
        pass


@dataclass
class RefSubindex(Ref):
    """AST class represent a reference of a vector's index

    Attributes:
        gender: Expression's FIRRTL gender
        type: Expression's type
        passive_type: True if the expression is passive type, otherwise false
        ref_arg: Vector being refered
        index: Vector's index
    """
    ref_arg: Definition = None
    index: int = 0

    def emit(self) -> str:
        """Return FIRRTL source code string"""
        return "{}[{}]".format(self.ref_arg.name, self.index)
    
    def emit_verilog(self) -> str:
        """Return FIRRTL source code string"""
        if isinstance(self.ref_arg, Ref):
            return f"{self.ref_arg.emit_verilog()}_{self.index}"
        return f"{self.ref_arg.name}_{self.index}"


@dataclass
class RefSubaccess(Ref):
    """AST class represent a reference of a vector's index, using expression

    Attributes:
        gender: Expression's FIRRTL gender
        type: Expression's type
        passive_type: True if the expression is passive type, otherwise false
        ref_arg: Vector being refered
        index_exp: Vector's index expression
    """
    ref_arg: Definition = None
    index_exp: Exp = None

    def emit(self) -> str:
        """Return FIRRTL source code string"""
        return "{}[{}]".format(self.ref_arg.name, self.index_exp.emit())
    
    def emit_verilog(self) -> str:
        pass
