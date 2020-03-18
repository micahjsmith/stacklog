try:
    from inspect import getfullargspec

    def getnargs(func):
        return len(getfullargspec(func).args)
except ImportError:
    from inspect import getargspec

    def getnargs(func):
        return len(getargspec(func).args)
