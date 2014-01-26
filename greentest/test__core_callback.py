import gevent
from gevent.hub import get_hub

called = []


def f():
    called.append(1)


def main():
    loop = get_hub().loop
    x = loop.call_soon(f)

    assert x, x
    gevent.sleep(0)
    assert called == [1], called

    x = loop.call_soon(f)
    assert x, x
    x.cancel()
    gevent.sleep(0)
    assert called == [1], called


if __name__ == '__main__':
    called[:] = []
    main()
