def s2ns(sec):
    return '%8.2f ns' % (sec * 1e9)


def s2mks(sec):
    return '%8.2f mks' % (sec * 1e6)


def s2ms(sec):
    return '%8.2f ms' % (sec * 1e3)


def s2s(sec):
    return '%8.2f s' % sec


def s2min(sec):
    return '%8.2f min' % (sec / 60)


def s2auto(sec):
    if sec < 1e-6:
        return s2ns(sec)
    elif sec < 1e-3:
        return s2mks(sec)
    elif sec < 1:
        return s2ms(sec)
    elif sec < 180:
        return s2s(sec)
    else:
        return s2min(sec)


TIME_FORMATTERS = {
    'auto': s2auto,
    'ns': s2ns,
    'mks': s2mks,
    'ms': s2ms,
    's': s2s,
    'min': s2min,
}


def format_time(unit, sec):
    return TIME_FORMATTERS[unit](sec).lstrip()
