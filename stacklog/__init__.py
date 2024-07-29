# -*- coding: utf-8 -*-
"""Top-level package for stacklog."""

__author__ = "Micah Smith"
__email__ = "micahjsmith@gmail.com"
__version__ = "2.0.0"

import time
import types
from collections import defaultdict
from functools import wraps
from inspect import getfullargspec
from typing import Any, Callable, TypeVar

from ._time_formatters import format_time
from .compat import Dict, List, ParamSpec, StrEnum, Tuple, Union

__all__ = (
    "stacklog",
    "stacktime",
)


SUCCESS = "DONE"
FAILURE = "FAILURE"


# type if an exception is currently being handled
SysExcInfoCurrentExc = Tuple[type, BaseException, types.TracebackType]
# type if there is no current exception
SysExcInfoNoCurrentExc = Tuple[None, None, None]
SysExcInfo = Union[SysExcInfoCurrentExc, SysExcInfoNoCurrentExc]

# type for a `condition` handler
StacklogConditionMatchFn = Union[
    Callable[[Union[type, None]], bool],
    Callable[[Union[type, None], Union[BaseException, None]], bool],
    Callable[
        [
            Union[type, None],
            Union[BaseException, None],
            Union[types.TracebackType, None],
        ],
        bool,
    ],
]

# the logging method
StacklogMethodFn = Callable[[str], Any]

# a callback for any of the signals
StacklogCallbackFn = Callable[["stacklog"], None]

P_CALL = ParamSpec("P_CALL")
T_CALL = TypeVar("T_CALL")


def getnargs(func: object) -> int:
    return len(getfullargspec(func).args)


class Event(StrEnum):
    ENTER = "enter"
    BEGIN = "begin"
    EXIT = "exit"
    SUCCESS = "success"
    FAILURE = "failure"


class stacklog:
    """Stack log messages

    Example usage::

       with stacklog(logging.info, 'Running long function'):
           run_long_function()

       with stacklog(logging.info, 'Running error-prone function'):
           raise Exception

       with stacklog(logging.info, 'Skipping not implemented',
                     conditions=[(NotImplementedError, 'SKIPPED')]):
           raise NotImplementedError

    This produces logging output::

        INFO:root:Running long function...
        INFO:root:Running long function...DONE
        INFO:root:Running error-prone function...
        INFO:root:Running error-prone function...FAILURE
        INFO:root:Skipping not implemented...
        INFO:root:Skipping not implemented...SKIPPED

    Args:
        method: log callable
        message: log message
        *args: right-most args to log method
        conditions (List[Tuple]): list of tuples of exceptions or tuple of
            exceptions to catch and log conditions, such as
            ``[(NotImplementedError, 'SKIPPED')]``.
        **kwargs: kwargs to log method
    """

    __callbacks: Dict[Event, List[StacklogCallbackFn]]
    __conditions: List[Tuple[StacklogConditionMatchFn, StacklogCallbackFn]]
    __condition_index: Union[int, None]

    def __init__(
        self,
        method: StacklogMethodFn,
        message: str,
        *args,  # type: ignore
        conditions: Union[List[Tuple[type, str]], None] = None,
        **kwargs  # type: ignore
    ):
        if conditions is None:
            conditions = []
        self.method = method
        self.message = str(message)
        self.args = args  # type: ignore
        self.kwargs = kwargs  # type: ignore

        self.__callbacks = defaultdict(list)
        self.__conditions = []
        self.__condition_index = None

        # default behavior
        self.on_begin(begin)
        self.on_success(succeed)
        self.on_failure(fail)

        for exc_type, suffix in conditions:
            self.on_condition(match_condition(exc_type), log_condition(suffix))

    def log(self, suffix: str = "") -> None:
        """Log a message with given suffix"""
        self.method(self.message + "..." + suffix, *self.args, **self.kwargs)  # type: ignore

    def on_begin(self, func: StacklogCallbackFn) -> None:
        """Add callback for beginning of block

        The function ``func`` takes one argument, the stacklog instance.
        """
        self.__on(Event.BEGIN, func)

    def on_success(self, func: StacklogCallbackFn) -> None:
        """Add callback for successful execution

        The function ``func`` takes one argument, the stacklog instance.
        """
        self.__on(Event.SUCCESS, func)

    def on_failure(self, func: StacklogCallbackFn):
        """Add callback for failed execution

        The function ``func`` takes one argument, the stacklog instance.
        """
        self.__on(Event.FAILURE, func)

    def on_condition(self, match: StacklogConditionMatchFn, func: StacklogCallbackFn):
        """Add callback for failed execution

        The first function `match` takes up to three arguments,
        exc_type (``type``), exc_val (``BaseException``), and exc_tb
        (``types.TracebackType``). This is the same tuple of values as returned
        by ``sys.exc_info()`` and allows the client to determine whether to
        respond to this exception or not. This function should return a ``bool``
        and have no side effects.

        The second function ``func`` takes the stacklog instance as the first
        argument and the exception info triple as the remaining arguments.

        Both methods can optionally receive fewer arguments by simply
        declaring fewer arguments in their signatures. They will be called
        with the first arguments they declare.

        See also:
        - https://docs.python.org/3/library/sys.html#sys.exc_info
        """
        self.__conditions.insert(0, (match, func))

    def on_enter(self, func: StacklogCallbackFn):
        """Append callback for entering block

        The function ``func`` takes one argument, the stacklog instance. This
        callback is intended for initializing resources that will be used
        after the block has been executed.
        """
        self.__on(Event.ENTER, func, clear=False)

    def on_exit(self, func: StacklogCallbackFn):
        """Append callback for exiting block

        The function ``func`` takes one argument, the stacklog instance. This
        callback is intended for resolving or processing resources.
        """
        self.__on(Event.EXIT, func, clear=False)

    def __on(self, event: Event, func: StacklogCallbackFn, clear: bool = True):
        if clear:
            self.__callbacks[event].clear()
        self.__callbacks[event].append(func)

    def __signal(self, event: Event):
        if event in self.__callbacks:
            for func in self.__callbacks[event]:
                call_with_args(func, self)

    def __matches_exception(self, *sys_exc_info: SysExcInfo):
        exc_type, exc_val, exc_tb = sys_exc_info
        for i, (match, _) in enumerate(self.__conditions):
            if call_with_args(match, exc_type, exc_val, exc_tb):  # type: ignore
                self.__condition_index = i
                return True
        return False

    def __handle_exception(self, *sys_exc_info: SysExcInfo):
        exc_type, exc_val, exc_tb = sys_exc_info
        if self.__condition_index is not None:
            func = self.__conditions[self.__condition_index][1]
            call_with_args(func, self, exc_type, exc_val, exc_tb)

    def __call__(self, func: Callable[P_CALL, T_CALL]) -> Callable[P_CALL, T_CALL]:
        @wraps(func)
        def wrapper(*args: P_CALL.args, **kwargs: P_CALL.kwargs):
            with self:
                return func(*args, **kwargs)

        return wrapper

    def __enter__(self):
        self.__signal(Event.ENTER)
        self.__signal(Event.BEGIN)
        return self

    def __exit__(self, *sys_exc_info: SysExcInfo):
        exc_type, exc_val, exc_tb = sys_exc_info
        self.__signal(Event.EXIT)

        if exc_type is None:  # type: ignore
            self.__signal(Event.SUCCESS)
        elif self.__matches_exception(exc_type, exc_val, exc_tb):
            self.__handle_exception(exc_type, exc_val, exc_tb)
        else:
            self.__signal(Event.FAILURE)

        return False


P_CALL_WITH_ARGS = ParamSpec("P_CALL_WITH_ARGS")
T_CALL_WITH_ARGS = TypeVar("T_CALL_WITH_ARGS")


def call_with_args(
    func: Callable[P_CALL_WITH_ARGS, T_CALL_WITH_ARGS], *args  # type: ignore
) -> T_CALL_WITH_ARGS:
    """Call a function with the number of args that it requires"""
    nargs = getnargs(func)
    funcargs = args[:nargs]  # type: ignore
    return func(*funcargs)  # type: ignore


def begin(stacklogger: stacklog) -> None:
    """Log the default begin message"""
    stacklogger.log()


def succeed(stacklogger: stacklog) -> None:
    """Log the default success message"""
    stacklogger.log(suffix=SUCCESS)


def fail(stacklogger: stacklog) -> None:
    """Log the default failure message"""
    stacklogger.log(suffix=FAILURE)


def match_condition(exc_type: type) -> Callable[[Union[type, None]], bool]:
    """Return a function that matches subclasses of ``exc_type``"""

    def func(_exc_type: Union[type, None]):
        if _exc_type is None:
            return False
        return issubclass(_exc_type, exc_type)

    return func


def log_condition(suffix: str) -> StacklogCallbackFn:
    """Return a function that logs the given suffix."""

    def func(stacklogger: stacklog) -> None:
        stacklogger.log(suffix=suffix)

    return func


# ---- custom stackloggers ------


class stacktime(stacklog):
    """Stack log messages with timing information

    The same arguments apply as to stacklog, with one additional kwarg.

    Args:
        unit (str):
            one of 'auto', 'ns', 'mks', 'ms', 's', 'min'. Defaults to 'auto'.

    Example usage::

       >>> with stacktime(print, 'Running some code', unit='ms'):
       ...     time.sleep(1e-2)
       ...
       Running some code...
       Running some code...DONE in 11.11 ms

    """

    def __init__(
        self, method: StacklogMethodFn, message: str, unit: str = "auto", **kwargs  # type: ignore
    ):
        super().__init__(method, message, **kwargs)  # type: ignore

        self.unit = unit

        self.start: Union[float, None] = None
        self.end: Union[float, None] = None

        def handle_enter(_s: stacklog):
            self.start = time.time()

        def handle_exit(_s: stacklog):
            if self.start:
                self.end = time.time()

        def handle_success(_s: stacklog):
            if self.start is not None and self.end is not None:
                duration = self.__format_time(self.end - self.start)
                suffix = SUCCESS + " in " + duration
            else:
                suffix = SUCCESS
            _s.log(suffix=suffix)

        self.on_enter(handle_enter)
        self.on_exit(handle_exit)
        self.on_success(handle_success)

    def __format_time(self, secs: float) -> str:
        return format_time(self.unit, secs)

    @property
    def elapsed_seconds(self) -> float:
        now = time.time()
        if self.start is None:
            return 0
        elif self.end is None:
            return now - self.start
        else:
            return self.end - self.start

    @property
    def elapsed(self) -> str:
        return self.__format_time(self.elapsed_seconds)
