from dataclasses import dataclass
from typing import List, Dict
from pyhcl.firrtl.ir import *
from pyhcl.firrtl.passes.namespace import Namespace
from pyhcl.exceptions import PyHCLException, PyHCLExceptions

class Error:
    def __init__(self):
        self.errors: List[PyHCLException] = []

    def append(self, pe: PyHCLException):
        self.errors.append(pe)
    
    def trigger(self):
        if len(self.errors) == 0:
            return
        elif len(self.errors) == 1:
            raise self.errors.pop()
        else:
            self.append(f'{len(self.errors)} errors detected!')
            raise PyHCLExceptions(self.errors)

class ModuleGraph:
    nodes: Dict[str, set] = {}
    
    def add(self, parent: str, child: str) -> List[str]:
        if parent not in self.nodes.keys():
            self.nodes[parent] = set()
        self.nodes[parent].add(child)
        return self.path_exists(child, parent, [child, parent])
    
    def path_exists(self, child: str, parent: str, path: List[str] = None) -> List[str]:
        cx = self.nodes[child] if child in self.nodes.keys() else None
        if cx is not None:
            if parent in cx:
                return [parent] + path
            else:
                for cxx in cx:
                    new_path = self.path_exists(cxx, parent, [cxx] + path)
                    if len(new_path) > 0:
                        return new_path
        return None

class ScopeView:
    def __init__(self, moduleNS: set, scopes: List[set]):
        self.moduleNS = moduleNS
        self.scopes = scopes
    
    def declare(self, name: str):
        self.moduleNS.add(name)
        self.scopes[0].add(name)
    
    # ensures that the name cannot be used again, but prevent references to this name
    def add_to_namespace(self, name: str):
        self.moduleNS.add(name)

    def expand_m_port_visibility(self, port: RefMemPort):
        mem_in_scopes = False
        def expand_m_port(scope: set, mp: RefMemPort):
            if mp.refmem.name in scope:
                scope.add(mp.name)
            return scope
        self.scopes = list(map(lambda scope: expand_m_port(scope, port), self.scopes))
        for sx in self.scopes:
            if port.refmem.name in sx:
                mem_in_scopes = True
        if mem_in_scopes is False:
            self.scopes[0].add(port.name)

    
    def legal_decl(self, name: str) -> bool:
        return name in self.moduleNS

    def legal_ref(self, name: str) -> bool:
        for s in self.scopes:
            if name in s:
                return True
        return False
    
    def get_ref(self):
        for s in self.scopes:
            print(s)

    def child_scope(self):
        return ScopeView(self.moduleNS, [set()])


def scope_view():
    return ScopeView(set(), [set()])

@dataclass
class CheckForms:
    c: Circuit
    errors: Error = Error()

    def run(self, namespace: Namespace):
        modulesNS: List[str] = []
        def has_flip(t: Type):
            if isinstance(t, Bundle):
                for fx in t.fields:
                    if fx.is_flip:
                        return True
                    has_flip(fx.type)
            elif isinstance(t, Vector):
                return has_flip(t.type)
            else:
                return False
        
        def check_name(sourceinfo: SourceInfo, names: ScopeView, referenced: bool, s: Union[DefStat, CmdStat]):
            if referenced is False:
                return
            if len(s.name) == 0:
                assert referenced is False, 'A statement with an empty name cannot be used as a reference!'
            else:
                if names.legal_decl(s.name) is True:
                    self.errors.append(PyHCLException(f"{sourceinfo.emit()} Reference {s.name} does not have a unique name."))
                if referenced:
                    names.declare(s.name)
                else:
                    names.add_to_namespace(s.name)
        
        def check_instance(sourceinfo: SourceInfo, child: str, parent: str):
            if child not in modulesNS:
                self.errors.append(PyHCLException(f"{sourceinfo.emit()} Module {parent} is not defined."))
            childToParent = ModuleGraph().add(parent, child)
            if childToParent is not None and len(childToParent) > 0:
                self.errors.append(PyHCLException(f"{sourceinfo.emit()} Has instance loop {'->'.join(childToParent)}."))
        
        def check_valid_loc(sourceinfo: SourceInfo, e: Exp):
            if isinstance(e, (LitUInt, LitSInt, Op)):
                self.errors.append(f"{sourceinfo.emit()} Invalid connect to an expression that is not a reference or a WritePort.")
        
        def valid_sub_exp(sourceinfo: SourceInfo, e: Exp):
            if not isinstance(e, (Ref, Mux, ValidIf)):
                self.errors.append(PyHCLException(f"{sourceinfo.emit()} Invalid access to non-reference."))

        def check_forms_w(sourceinfo: SourceInfo, w: int):
            if w < 0:
                self.errors.append(PyHCLException(f"{sourceinfo.emit()} Width cannot be negative."))

        def check_forms_t(sourceinfo: SourceInfo, t: Type):
            if isinstance(t, Vector) and t.size < 0:
                self.errors.append(PyHCLException(f"{sourceinfo.emit()} Vector type size cannot be negative."))
                check_forms_t(t.type)
            elif isinstance(t, Bundle):
                for fx in t.fields:
                    check_forms_t(fx.sourceinfo, fx.type)
            else:
                check_forms_w(sourceinfo, t.width)
        
        def check_forms_e(sourceinfo: SourceInfo, names: ScopeView, e: Exp):
            if isinstance(e, Ref):
                if isinstance(e, RefSubaccess):
                    valid_sub_exp(sourceinfo, e.ref_arg)
                if isinstance(e, (RefSubindex, RefSubaccess, RefSubfield)):
                    check_forms_e(sourceinfo, names, e.ref_arg)
                else:
                    if not names.legal_ref(e.ref_arg.name):
                        self.errors.append(PyHCLException(f"{sourceinfo.emit()} Reference {e.ref_arg.name} is not declared."))
            elif isinstance(e, LitUInt):
                if e.initial < 0:
                    self.errors.append(PyHCLException(f"{sourceinfo.emit()} UIntLiteral cannot be negative."))
            elif isinstance(e, ValidIf):
                check_forms_e(sourceinfo, names, e.con)
                check_forms_e(sourceinfo, names, e.vad)
            elif isinstance(e, Mux):
                check_forms_e(sourceinfo, names, e.con)
                check_forms_e(sourceinfo, names, e.true_exp)
                check_forms_e(sourceinfo, names, e.false_exp)
            elif isinstance(e, Op):
                for operand in e.operands:
                    check_forms_e(sourceinfo, names, operand)
            else:
                ...
        
        def check_forms_s(names: ScopeView, s: Union[DefStat, CmdStat]):
            referenced = True if isinstance(s, (DefWire, DefReg, DefRegReset, InstModule, DefMem, DefNode)) else False
            check_name(s.sourceinfo, names, referenced, s)
            if isinstance(s, When):
                for sx in s.stats:
                    check_forms_s(names, sx)
                check_forms_s(names, s.elsebegin)
            elif isinstance(s, ElseBegin):
                for sx in s.stats:
                    check_forms_s(names, sx)
            elif isinstance(s, (DefReg, DefRegReset)):
                check_forms_e(s.sourceinfo, names, s.clk)
                if isinstance(s, DefRegReset):
                    check_forms_e(s.sourceinfo, names, s.reset_signal)
                    check_forms_e(s.sourceinfo, names, s.reset_value)
                if has_flip(s.type):
                    self.errors.append(PyHCLException(f"{s.sourceinfo.emit()}  Register {s.name} cannot be a bundle type with flips."))
            elif isinstance(s, DefMem):
                if has_flip(s.type):
                    self.errors.append(PyHCLException(f"{s.sourceinfo.emit()}  Memory {s.name} cannot be a bundle type with flips."))
                if s.size < 0:
                    self.errors.append(PyHCLException(f"{s.sourceinfo.emit()} Memory size cannot be negative or zero."))
            elif isinstance(s, InstModule):
                check_instance(s.sourceinfo, s.name, s.module.name)
            elif isinstance(s, Connect):
                check_valid_loc(s.sourceinfo, s.lexp)
                check_forms_e(s.sourceinfo, names, s.lexp)
                check_forms_e(s.sourceinfo, names, s.rexp)
            elif isinstance(s, RefMemPort):
                check_forms_e(s.sourceinfo, names, s.clk)
                check_forms_e(s.sourceinfo, names, s.addr)
                names.expand_m_port_visibility(s)
            elif isinstance(s, DefNode):
                check_forms_e(s.sourceinfo, names, s.node_exp)
            else:
                ...

        def check_forms_p(names: ScopeView, p: Port):
            if names.legal_decl(p.name):
                self.errors.append(PyHCLException(f"{p.sourceinfo.emit()} Reference {p.name} does not have a unique name."))
            names.declare(p.name)
            check_forms_t(p.sourceinfo, p.type)

        def check_forms_m(m: Module):
            names = scope_view()
            for p in m.ports:
                check_forms_p(names, p)
            for s in m.stats:
                check_forms_s(names, s)
        
        for m in self.c.modules:
            if m.name not in modulesNS:
                modulesNS.append(m.name)
                check_forms_m(m)
            else:
                self.errors.append(f"{m.sourceinfo.emit} Repeat definition of module {m.name}")
        self.errors.trigger()
        return self.c
