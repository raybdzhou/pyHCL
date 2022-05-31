"""Build resources

Filename: resources.py
Author: SunnyChen
"""
import inspect
from dataclasses import dataclass, field
from typing import List

global_id: int = 0


@dataclass
class SourceInfo(object):
    """Generated FIRRTL source code info object

    Notes: This class using dataclasses
    Attributes:
        filename: Indicate which python source file generate current FIRRTL object
        line: Indicate which line generate current FIRRTL object
        col: Indicate which column generate current FIRRTL object
        info: Source code info string
    """

    filename: str
    line: int
    info: str = field(compare=False, default="")

    def emit(self) -> str:
        """Generate current FIRRTL source info

        Returns:
            A source information string
        """
        self.info = "@[{}:{}]".format(self.filename, self.line)
        return self.info
    
    def emit_verilog(self) -> str:
        """Generate current Verilog source info

        Returns:
            A source information string
        """
        self.info = f"// {self.filename}:{self.line}"
        return self.info


class HasInfo(object):
    """A PyHCL object which has source info"""
    _sourceinfo: SourceInfo = None

    def __init__(self, frame):
        """Generate source code info, init HasInfo object

        The frame information is from a factory or something else?
        """
        split_list = frame.f_code.co_filename.split('/')
        filename = split_list[len(split_list) - 1]
        lineno = frame.f_lineno
        self._sourceinfo = SourceInfo(filename, lineno)


@dataclass(init=False)
class InstanceId(object):
    """Core id class, track all AST objects

    Attributes:
        id: object id
        parent_id: parent definition id list
        child_id: child definition id list
    """

    id: int
    parent_id: List[int] = field(default_factory=list, compare=False)
    child_id: List[int] = field(default_factory=list, compare=False)

    def __init__(self):
        """Inits a InstanceId object"""
        global global_id
        self.id = global_id
        global_id += 1
        self.parent_id: List[int] = []
        self.child_id: List[int] = []

    def add_parent(self, parent: int):
        """Append a parent in parent_list

        Args:
            parent: Parent's id

        Raises:
            ValueError: If the parent to be added is already in the list
        """
        if parent in self.parent_id:
            raise ValueError("Duplicate parent id", parent)
        self.parent_id.append(parent)

    def add_child(self, child: int):
        """Append a child in child_list

        Args:
            child: Child's id

        Raises:
            ValueError: If the child to be added is already in the list
        """
        if child in self.child_id:
            raise ValueError("Duplicate child id", child)
        self.child_id.append(child)

    def remove_parent(self, parent: int):
        """Remove a parent from parent_list

        Args:
            parent: Parent's id

        Raises:
            ValueError: The parent id is not in list
        """
        self.parent_id.remove(parent)

    def remove_child(self, child: int):
        """Remove a child from child_list

        Args:
            child: Child's id

        Raises:
            ValueError: The child id is not in list
        """
        self.parent_id.remove(child)
