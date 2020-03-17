# -*- coding: utf-8 -*-

"""Top-level package for stacklog."""

__author__ = 'Micah Smith'
__email__ = 'micahjsmith@gmail.com'
__version__ = '1.0.0'

import time
from collections import defaultdict
from functools import wraps
from inspect import getfullargspec

from ._vendored import time_formatters

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
        self.method(self.message + '...' + suffix, *self.args, **self.kwargs)

    def on_begin(self, func):
        self.__on(Event.BEGIN, func)

    def on_success(self, func):
        self.__on(Event.SUCCESS, func)

    def on_failure(self, func):
        self.__on(Event.FAILURE, func)

    def on_condition(self, match, func):
        self.__conditions.insert(0, (match, func))

    def on_enter(self, func):
        self.__on(Event.ENTER, func, clear=False)

    def on_exit(self, func):
        self.__on(Event.EXIT, func, clear=False)

    def __on(self, event, func, clear=True):
        if clear:
            self.__callbacks[event].clear()
        self.__callbacks[event].append(func)

    def __signal(self, condition):
        if condition in self.__callbacks:
            for func in self.__callbacks[condition]:
                func(self)

    def __call_with_args(self, func, *args):
        nargs = len(getfullargspec(func).args)
        return func(*args[:nargs])

    def __matches_exception(self, exc_type, exc_val, exc_tb):
        for i, (match, _) in enumerate(self.__conditions):
            if self.__call_with_args(match, exc_type, exc_val, exc_tb):
                self.__condition_index = i
                return True
        return False

    def __handle_exception(self, exc_type, exc_val, exc_tb):
        func = self.__conditions[self.__condition_index][1]
        self.__call_with_args(func, self, exc_type, exc_val, exc_tb)

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


class Event:
    ENTER = 'enter'
    BEGIN = 'begin'
    EXIT = 'exit'
    SUCCESS = 'success'
    FAILURE = 'failure'


def begin(stacklogger):
    return stacklogger.log()


def succeed(stacklogger):
    return stacklogger.log(suffix=SUCCESS)


def fail(stacklogger):
    return stacklogger.log(suffix=FAILURE)


def match_condition(exc_type):
    return lambda _exc_type: issubclass(exc_type, _exc_type)


def log_condition(suffix):
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

    def on_enter(_):
        global start
        start = time.time()

    def on_exit(_):
        global start, duration
        duration = time_formatters[unit](time.time() - start).lstrip()

    def on_success(s):
        global duration
        suffix = SUCCESS + ' in ' + duration
        s.log(suffix=suffix)

    stacklogger.on_enter(on_enter)
    stacklogger.on_exit(on_exit)
    stacklogger.on_success(on_success)

    return stacklogger
