try:
    from inspect import getfullargspec

    def getnargs(func: object) -> int:
        return len(getfullargspec(func).args)
except ImportError:
    from inspect import getargspec

    def getnargs(func: object) -> int:
        return len(getargspec(func).args)
