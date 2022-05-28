"""PyHCL's own exception definition

Not fully implemented.

Filename: exceptions.py
Author: SunnyChen
"""


class PyHCLException(Exception):
    """PyHCL based exception class

    Attributes:
        msg: Exception information
    """

    def __init__(self, msg: str = ""):
        """Inits a PyHCL Exception object

        Args:
            msg: Exception's message
        """
        super().__init__(self)
        self.msg = msg


class EquivalentError(PyHCLException):
    """PyHCL error, indicate two expression going to connect is not equivalent

    Attributes:
        msg: Exception information
        lexp: Left-hand expression
        rexp: Right-hand expression
    """
    def __init__(self, msg: str = "", lexp=None, rexp=None):
        """Inits a EquivalentError object

        Args:
            msg: Exception information
            lexp: Left-hand expression
            rexp: Right-hand expression
        """
        super().__init__(msg)
        self.lexp = lexp
        self.rexp = rexp


class FlowCheckError(PyHCLException):
    """PyHCL error, indicate two expression going to connect flow check fail
EquivalentError
    Attributes:
        msg: Exception information
        lexp: Left-hand expression
        rexp: Right-hand expression
    """
    def __init__(self, msg: str = "", lexp=None, rexp=None):
        """Inits a FlowCheckError object

        Args:
            msg: Exception information
            lexp: Left-hand expression
            rexp: Right-hand expression
        """
        super().__init__(msg)
        self.lexp = lexp
        self.rexp = rexp
