# added in py39 (generic aliases) and py310 (| syntax)
from typing import Dict, List, Tuple, Union

# Added in py310
try:
    from typing import ParamSpec
except ImportError:
    from typing_extensions import ParamSpec

# Added in py310
try:
    from enum import StrEnum
except ImportError:
    from enum import Enum

    # From https://github.com/python/cpython/blob/3.12/Lib/enum.py
    class ReprEnum(Enum):
        """
        Only changes the repr(), leaving str() and format() to the mixed-in type.
        """

    class StrEnum(str, ReprEnum):
        """
        Enum where members are also (and must be) strings
        """

        def __new__(cls, *values):
            "values must already be of type `str`"
            if len(values) > 3:
                raise TypeError("too many arguments for str(): %r" % (values,))
            if len(values) == 1:
                # it must be a string
                if not isinstance(values[0], str):
                    raise TypeError("%r is not a string" % (values[0],))
            if len(values) >= 2:
                # check that encoding argument is a string
                if not isinstance(values[1], str):
                    raise TypeError("encoding must be a string, not %r" % (values[1],))
            if len(values) == 3:
                # check that errors argument is a string
                if not isinstance(values[2], str):
                    raise TypeError("errors must be a string, not %r" % (values[2]))
            value = str(*values)
            member = str.__new__(cls, value)
            member._value_ = value
            return member

        @staticmethod
        def _generate_next_value_(name, start, count, last_values):
            """
            Return the lower-cased version of the member name.
            """
            return name.lower()


__all__ = (
    "Dict",
    "List",
    "ParamSpec",
    "StrEnum",
    "Tuple",
    "Union",
)
