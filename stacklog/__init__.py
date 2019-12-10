# -*- coding: utf-8 -*-

"""Top-level package for stacklog."""

__author__ = 'Micah Smith'
__email__ = 'micahjsmith@gmail.com'
__version__ = '1.0.0'


from functools import wraps


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
        self.conditions = kwargs.pop('conditions', None)  # py2 compat
        self.kwargs = kwargs

    def _log(self, suffix=''):
        self.method(self.message + '...' + suffix, *self.args, **self.kwargs)

    _begin = _log

    def _succeed(self):
        self._log(suffix='DONE')

    def _fail(self):
        self._log(suffix='FAILURE')

    def _matches_condition(self, exc_type):
        return self.conditions is not None and any(
            issubclass(exc_type, e) for e, _ in self.conditions)

    def _log_condition(self, exc_type):
        for e, suffix in self.conditions:
            if issubclass(exc_type, e):
                self._log(suffix=suffix)
                return

    def __call__(self, func):

        @wraps(func)
        def wrapper(*args, **kwargs):
            with self:
                return func(*args, **kwargs)

        return wrapper

    def __enter__(self):
        self._begin()

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self._succeed()
        elif self._matches_condition(exc_type):
            self._log_condition(exc_type)
        else:
            self._fail()

        return False
