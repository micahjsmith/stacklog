[![PyPI Shield](https://img.shields.io/pypi/v/stacklog.svg)](https://pypi.python.org/pypi/stacklog)
[![Downloads](https://pepy.tech/badge/stacklog)](https://pepy.tech/project/stacklog)
[![.github/workflows/test.yml](https://github.com/micahjsmith/stacklog/actions/workflows/test.yml/badge.svg)](https://github.com/micahjsmith/stacklog/actions/workflows/test.yml)

# stacklog

Stack log messages

- Documentation: <https://micahjsmith.github.io/stacklog>
- Homepage: <https://github.com/micahjsmith/stacklog>

## Overview

Stacklog is a tiny Python library to stack log messages.

A stack-structured log is an approach to logging in which log messages are (conceptually)
pushed onto a stack and emitted only when the corresponding block returns.
Stacklog provides a single method, `stacklog`, which serves as either a decorator or a
context manager. This is exceptionally useful in small projects or one-off scripts.

This is illustrated best with an example:

```python
with stacklog(print, 'Running some code'):
    with stacklog(print, 'Running some other code'):
        pass
```

This produces the following logging output:

```shell
Running some code...
Running some other code...
Running some other code...DONE
Running some code...DONE
```

When the code within a stacklog context completes, the provided message is echoed along with
the return status, one of `DONE` or `FAILURE`. That's pretty much it.
Customization and advanced features are available through callbacks.

## Install

stacklog has been developed and tested on Python 2.7 and 3.5+.

```shell
pip install stacklog
```

## Quickstart

How often do you find yourself using the following logging anti-pattern in Python?

```python
import logging

def a():
    logging.info('Running a')
    do_something()
    logging.info('Done with a')

def b():
    logging.info('Running b')
    a()
    logging.info('Done with b')

try:
    b()
except:
    logging.info('There was an error running b')
```

The intention here is to log the beginning and end of procedure calls for use in debugging
or user monitoring. I call this an anti-pattern because:

- it requires excessive manual attention to writing/updating logging calls at entry/exit sites
- it results in redundant exception handling logic
- the resulting log messages can be misleading if errors occur

Instead, the approach taken by stacklog is to accomplish this using only decorators and
context managers.

### Usage as decorator

Here is the above example using the stacklog as a decorator:

```python
@stacklog(logging.info, 'Running a')
def a():
    raise Exception

@stacklog(logging.info, 'Running b')
def b():
    a()

b()
```

This produces logging output:

```shell
INFO:root:Running b...
INFO:root:Running a...
INFO:root:Running a...FAILURE
INFO:root:Running b...FAILURE
```

### Usage as context manager

Here is another example using stacklog as a context manager:

```pycon
>>> with stacklog(logging.info, 'Running some code'):
...     do_something()
...
INFO:root:Running some code...
INFO:root:Running some code...DONE
```

## Advanced usage

### Providing custom conditions

A *condition* is a tuple `exception, status`. If the provided exception is raised during the
execution of the provided code, the provided status is logged instead of the default
`FAILURE`.

```pycon
>>> with stacklog(logging.info, 'Running some code', conditions=[(NotImplementedError,
'SKIPPED')]):
...     raise NotImplementedError
...
INFO:root:Running some code...
INFO:root:Running some code...SKIPPED
```

### Customization with callbacks

The behavior of `stacklog` is fully customizable with callbacks.

The main thing that a callback will do is call the passed `stacklog` instance's
`log` method with some custom suffix.

First, there are three callbacks to customize the behavior of logging at the
beginning of the block, at successful completion of the block, and at failure
of the block. Only one function can be registered at a time for each of
these events.

- `on_begin(func: stacklog -> None)`
- `on_success(func: stacklog -> None)`
- `on_failure(func: stacklog -> None)`

Second, one can customize failure behavior given different possible
exceptions that are raised, by passing a pair of functions, the first to match
an exception that was raised during block execution and the second to respond
to the exception. Many pairs of functions can be registered, but only the most
recent one to be registered will be executed in the case that multiple
functions match.

- `on_condition(match: *exc_info -> bool, func: stacklog, *exc_info -> None)`

Third, one can initialize and dispose of resources before and after the
block's execution. This is relevant for starting/stopping timers, etc. Many
functions can be registered and they will all be executed.

- `on_enter(func: stacklog -> None)`
- `on_exit(func: stacklog -> None)`

See the implementation of `stacktime` for an example.

### Adding timing information

One can customize `stacklog` with callbacks to, for example, add information
on the duration of block execution. This is packaged with the library itself
as the `stacktime` decorator/context manager. It's usage is the same as
`stacklog` except that it also logs timing information at the successful
completion of block.

```pycon
>>> with stacktime(print, 'Running some code', unit='ms'):
...     time.sleep(1e-2)
...
Running some code...
Running some code...DONE in 11.11 ms
```
