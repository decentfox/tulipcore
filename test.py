import asyncio
import gevent
from tulipcore import coroutine
from tulipcore import wait_future


def _raise():
    1/0


@coroutine
def run(tag):
    g = gevent.getcurrent()
    yield from asyncio.sleep(0)
    assert g is gevent.getcurrent()
    gevent.sleep(0)
    assert g is gevent.getcurrent()
    try:
        gevent.spawn(_raise).join()
    except ZeroDivisionError:
        pass
    else:
        assert False

wait_future(asyncio.tasks.async(run(tag='ha')))

