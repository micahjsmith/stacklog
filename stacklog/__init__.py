# -*- coding: utf-8 -*-

"""Top-level package for stacklog."""

__author__ = 'Micah Smith'
__email__ = 'micahjsmith@gmail.com'
__version__ = '1.0.0'


from collections import defaultdict
from functools import wraps
from inspect import getfullargspec


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

        self._callbacks = defaultdict(list)
        self._conditions = []
        self._condition_index = None

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
        self._on(Event.BEGIN, func)

    def on_success(self, func):
        self._on(Event.SUCCESS, func)

    def on_failure(self, func):
        self._on(Event.FAILURE, func)

    def on_condition(self, match, func):
        self._conditions.insert(0, (match, func))

    def on_enter(self, func):
        self._on(Event.ENTER, func, clear=False)

    def on_exit(self, func):
        self._on(Event.EXIT, func, clear=False)

    def _on(self, event, func, clear=True):
        if clear:
            self._callbacks[event].clear()
        self._callbacks[event].append(func)

    def _signal(self, condition):
        if condition in self._callbacks:
            for func in self._callbacks[condition]:
                func(self)

    def _call_with_args(self, func, *args):
        nargs = len(getfullargspec(func).args)
        return func(*args[:nargs])

    def _matches_exception(self, exc_type, exc_val, exc_tb):
        for i, (match, _) in enumerate(self._conditions):
            if self._call_with_args(match, exc_type, exc_val, exc_tb):
                self._condition_index = i
                return True
        return False

    def _handle_exception(self, exc_type, exc_val, exc_tb):
        func = self._conditions[self._condition_index][1]
        self._call_with_args(func, self, exc_type, exc_val, exc_tb)

    def __call__(self, func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return wrapper

    def __enter__(self):
        self._signal(Event.ENTER)
        self._signal(Event.BEGIN)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._signal(Event.EXIT)

        if exc_type is None:
            self._signal(Event.SUCCESS)
        elif self._matches_exception(exc_type, exc_val, exc_tb):
            self._handle_exception(exc_type, exc_val, exc_tb)
        else:
            self._signal(Event.FAILURE)

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
    return stacklogger.log(suffix='DONE')


def fail(stacklogger):
    return stacklogger.log(suffix='FAILURE')


def match_condition(exc_type):
    return lambda _exc_type: issubclass(exc_type, _exc_type)


def log_condition(suffix):
    return lambda stacklogger: stacklogger.log(suffix=suffix)
