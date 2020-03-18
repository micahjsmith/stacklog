import sys


try:
    from inspect import getfullargspec

    def getnargs(func):
        return len(getfullargspec(func).args)
except ImportError:
    from inspect import getargspec

    def getnargs(func):
        return len(getargspec(func).args)


if sys.version_info >= (3,):
    def clearlist(l):
        l.clear()
else:
    def clearlist(l):
        del l[:]
