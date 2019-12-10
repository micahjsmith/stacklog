[![PyPI Shield](https://img.shields.io/pypi/v/stacklog.svg)](https://pypi.python.org/pypi/stacklog)
[![Downloads](https://pepy.tech/badge/stacklog)](https://pepy.tech/project/stacklog)
[![Travis CI Shield](https://travis-ci.org/micahjsmith/stacklog.svg?branch=master)](https://travis-ci.org/micahjsmith/stacklog)

# stacklog

Stack log messages

- Documentation: https://micahjsmith.github.io/stacklog
- Homepage: https://github.com/micahjsmith/stacklog

## Overview

Stacklog is a tiny Python library to stack log messages.

A stack-structured log is an approach to logging in which log messages are (conceptually)
pushed onto a stack and emitted only when the pusher returns. Stacklog provides a single
method, `stacklog`, which serves as either a decorator or a context manager. This is
exceptionally useful in small projects or one-off scripts.

This is illustrated best with an example:

```
with stacklog(print, 'Running some code'):
    with stacklog(print, 'Running some other code'):
        pass
```

This produces the following logging output:

```
Running some code...
Running some other code...
Running some other code...DONE
Running some code...DONE
```

When the code within a stacklog context completes, the provided message is echoed along with
the return status, one of `DONE` or `FAILURE`. That's pretty much it.

## Install

stacklog has been developed and tested on Python 2.7 and 3.4+.

```bash
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

```
@stacklog(logging.info, 'Running a')
def a():
    raise Exception

@stacklog(logging.info, 'Running b')
def b():
    a()

b()
```

This produces logging output:

```
INFO:root:Running b...
INFO:root:Running a...
INFO:root:Running a...FAILURE
INFO:root:Running b...FAILURE
```

### Usage as context manager

Here is another example using stacklog as a context manager:

```
>>> with stacklog(logging.info, 'Running some code'):
...     do_something()
...
INFO:root:Running some code...
INFO:root:Running some code...DONE
```

### Providing custom conditions

A *condition* is a tuple `exception, status`. If the provided exception is raised during the
execution of the provided code, the provided status is logged instead of the default
`FAILURE`.

```
>>> with stacklog(logging.info, 'Running some code', conditions=[(NotImplementedError,
'SKIPPED')]):
...     raise NotImplementedError
...
INFO:root:Running some code...
INFO:root:Running some code...SKIPPED
```
