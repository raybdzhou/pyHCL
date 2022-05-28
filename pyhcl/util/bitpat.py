"""PyHCL bitpat class

Filename: bitpat.py
Author: SunnyChen
"""
from pyhcl.core.define import U


class BitPat(object):
    """A BitPat class is use to identify specify value.
    BitPat often use in control logic such as main control unit
    We also provide a method to convert a BitPat object to a UInt literal value

    A BitPat only support '==' and '!=' operation
    A BitPat object must be *RIGHT-SIDE* expression

    Attributes:
        pattern: Represent the bit string of the BitPat
        mask: Use in compare operation as a mask bit string
    """
    def __init__(self, pattern: str):
        """Construct a BitPat object

        Args:
            pattern: Bit pattern, starts with 'b' indicates the pattern is binary format
        """
        self.pattern = pattern

        # Extract the bit pattern form string
        # Construct mask and comparable string
        mask_cat_table = ['b']
        cmp_cat_table = ['b']
        for s in self.pattern[1:]:
            mask_cat_table.append('1' if s != '?' else '0')
            cmp_cat_table.append(s if s == '1' else '0')
        self.mask = "".join(mask_cat_table)
        self.cmp = "".join(cmp_cat_table)

    def bitpattouint(self):
        """Convert current BitPat object to a literal UInt value"""
        value = int(self.cmp[1:], 2)
        return U(value)
