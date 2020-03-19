# -*- coding: utf-8 -*-

"""Top-level package for stacklog."""

__author__ = 'Micah Smith'
__email__ = 'micahjsmith@gmail.com'
__version__ = '1.1.0'

import time
from collections import defaultdict
from functools import wraps

from ._time_formatters import format_time
from .compat import clearlist, getnargs

__all__ = (
    'stacklog',
    'stacktime',
)


SUCCESS = 'DONE'
FAILURE = 'FAILURE'


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

    def __init__(self, method, message, *args, **kwargs):
        self.method = method
        self.message = str(message)
        self.args = args
        conditions = kwargs.pop('conditions', [])  # py2 compat
        self.kwargs = kwargs

        self.__callbacks = defaultdict(list)
        self.__conditions = []
        self.__condition_index = None

        # default behavior
        self.on_begin(begin)
        self.on_success(succeed)
        self.on_failure(fail)

        for exc_type, suffix in conditions:
            self.on_condition(
                match_condition(exc_type),
                log_condition(suffix)
            )

    def log(self, suffix=''):
        """Log a message with given suffix"""
        self.method(self.message + '...' + suffix, *self.args, **self.kwargs)

    def on_begin(self, func):
        """Add callback for beginning of block

        The function ``func`` takes one argument, the stacklog instance.
        """
        self.__on(Event.BEGIN, func)

    def on_success(self, func):
        """Add callback for successful execution

        The function ``func`` takes one argument, the stacklog instance.
        """
        self.__on(Event.SUCCESS, func)

    def on_failure(self, func):
        """Add callback for failed execution

        The function ``func`` takes one argument, the stacklog instance.
        """
        self.__on(Event.FAILURE, func)

    def on_condition(self, match, func):
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

    def on_enter(self, func):
        """Append callback for entering block

        The function ``func`` takes one argument, the stacklog instance. This
        callback is intended for initializing resources that will be used
        after the block has been executed.
        """
        self.__on(Event.ENTER, func, clear=False)

    def on_exit(self, func):
        """Append callback for exiting block

        The function ``func`` takes one argument, the stacklog instance. This
        callback is intended for resolving or processing resources.
        """
        self.__on(Event.EXIT, func, clear=False)

    def __on(self, event, func, clear=True):
        if clear:
            clearlist(self.__callbacks[event])
        self.__callbacks[event].append(func)

    def __signal(self, condition):
        if condition in self.__callbacks:
            for func in self.__callbacks[condition]:
                call_with_args(func, self)

    def __matches_exception(self, exc_type, exc_val, exc_tb):
        for i, (match, _) in enumerate(self.__conditions):
            if call_with_args(match, exc_type, exc_val, exc_tb):
                self.__condition_index = i
                return True
        return False

    def __handle_exception(self, exc_type, exc_val, exc_tb):
        func = self.__conditions[self.__condition_index][1]
        call_with_args(func, self, exc_type, exc_val, exc_tb)

    def __call__(self, func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return wrapper

    def __enter__(self):
        self.__signal(Event.ENTER)
        self.__signal(Event.BEGIN)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__signal(Event.EXIT)

        if exc_type is None:
            self.__signal(Event.SUCCESS)
        elif self.__matches_exception(exc_type, exc_val, exc_tb):
            self.__handle_exception(exc_type, exc_val, exc_tb)
        else:
            self.__signal(Event.FAILURE)

        return False


def call_with_args(func, *args):
    """Call a function with the number of args that it requires"""
    nargs = getnargs(func)
    return func(*args[:nargs])


class Event:
    ENTER = 'enter'
    BEGIN = 'begin'
    EXIT = 'exit'
    SUCCESS = 'success'
    FAILURE = 'failure'


def begin(stacklogger):
    """Log the default begin message"""
    return stacklogger.log()


def succeed(stacklogger):
    """Log the default success message"""
    return stacklogger.log(suffix=SUCCESS)


def fail(stacklogger):
    """Log the default failure message"""
    return stacklogger.log(suffix=FAILURE)


def match_condition(exc_type):
    """Return a function that matches subclasses of ``exc_type``"""
    return lambda _exc_type: issubclass(exc_type, _exc_type)


def log_condition(suffix):
    """Return a function that logs the given suffix."""
    return lambda stacklogger: stacklogger.log(suffix=suffix)


# ---- custom stackloggers ------

def stacktime(*args, **kwargs):
    """Stack log messages with timing information

    The same arguments apply as to stacklog, with one additional kwarg.

    Args:
        unit (str): one of 'auto', 'ns', 'mks', 'ms', 's'.
    """
    unit = kwargs.pop('unit', 'auto')  # py2 compat
    stacklogger = stacklog(*args, **kwargs)

    start = None
    duration = None

    def on_enter():
        global start
        start = time.time()

    def on_exit():
        global duration, start
        duration = format_time(unit, (time.time() - start))

    def on_success(s):
        global duration
        suffix = SUCCESS + ' in ' + duration
        s.log(suffix=suffix)

    stacklogger.on_enter(on_enter)
    stacklogger.on_exit(on_exit)
    stacklogger.on_success(on_success)

    return stacklogger
