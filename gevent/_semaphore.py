import sys
from asyncio import Semaphore as __Semaphore__, coroutine
from gevent.hub import get_hub, getcurrent
from gevent.timeout import Timeout


__all__ = ['Semaphore']


class Semaphore(__Semaphore__):
    """A semaphore manages a counter representing the number of release() calls minus the number of acquire() calls,
    plus an initial value. The acquire() method blocks if necessary until it can return without making the counter
    negative.

    If not given, value defaults to 1.

    This Semaphore's __exit__ method does not call the trace function.
    """

    def __init__(self, value=1):
        self._hub = get_hub()
        super().__init__(value, loop=self._hub.loop)
        self._links = []
        self._notifier = None
        # TODO: what about this below?
        # we don't want to do get_hub() here to allow module-level locks
        # without initializing the hub

    def __repr__(self):
        res = super().__repr__()
        if self._links:
            extra = '_links:{}'.format(len(self._links))
            return '<{} [{}]>'.format(res[1:-1], extra)
        else:
            return res

    def release(self):
        super().release()
        self._start_notify()

    def _start_notify(self):
        if self._links and not self._locked and not self._notifier:
            self._notifier = get_hub().loop.call_soon(self._notify_links)

    def _notify_links(self):
        self._notifier = None
        while True:
            self._dirty = False
            for link in self._links:
                if self._locked:
                    return
                try:
                    link(self)
                except:
                    getcurrent().handle_error((link, self), *sys.exc_info())
                if self._dirty:
                    break
            if not self._dirty:
                return

    def rawlink(self, callback):
        """Register a callback to call when a counter is more than zero.

        *callback* will be called in the :class:`Hub <gevent.hub.Hub>`, so it must not use blocking gevent API.
        *callback* will be passed one argument: this instance.
        """
        if not callable(callback):
            raise TypeError('Expected callable: %r' % (callback, ))
        self._links.append(callback)
        self._dirty = True

    def unlink(self, callback):
        """Remove the callback set by :meth:`rawlink`"""
        try:
            self._links.remove(callback)
            self._dirty = True
        except ValueError:
            pass

    def wait(self, timeout=None):
        if self._locked:
            switch = getcurrent().switch
            self.rawlink(switch)
            try:
                timer = Timeout.start_new(timeout)
                try:
                    try:
                        result = get_hub().switch()
                        assert result is self, 'Invalid switch into Semaphore.wait(): %r' % (result, )
                    except Timeout:
                        ex = sys.exc_info()[1]
                        if ex is not timer:
                            raise
                finally:
                    timer.cancel()
            finally:
                self.unlink(switch)
        return self._value

    @coroutine
    def _nonblocking_acquire(self):
        if self._locked:
            return False
        else:
            return (yield from super().acquire())

    def acquire(self, blocking=True, timeout=None):
        if blocking:
            timer = Timeout.start_new(timeout)
            try:
                try:
                    return self._hub.wait_async(super().acquire())
                except Timeout as ex:
                    if ex is timer:
                        return False
                    raise
            finally:
                timer.cancel()
        else:
            return self._hub.wait_async(self._nonblocking_acquire())

    def __enter__(self):
        self.acquire()
