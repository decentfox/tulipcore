advance_iterator = next

import builtins
exec_ = getattr(builtins, "exec")


def reraise(tp, value, tb=None):
    if value.__traceback__ is not tb:
        raise value.with_traceback(tb)
    raise value
