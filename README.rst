gevent3_
========

gevent_ is a coroutine-based Python networking library. gevent3_ is a wrapper of asyncio_ for Python 3 offering a gevent-compatible API. Note, gevent3 is still very experimental.

gevent_ is written and maintained by `Denis Bilenko`_ and is licensed under MIT license.

gevent3_ is written and maintained by `Fantix King`_ and is licensed under MIT license.


get gevent
----------

Install Python 3.3 or newer, greenlet_ extension and asyncio_ library.

Clone `the repository`_.


installing from github
----------------------

To install the latest development version:

  pip install git+git://github.com/fantix/gevent3.git


running tests
-------------

  cd greentest

  PYTHONPATH=.. python testrunner.py --expected ../known_failures.txt


.. _gevent: http://www.gevent.org
.. _gevent3: https://github.com/fantix/gevent3
.. _greenlet: http://pypi.python.org/pypi/greenlet
.. _asyncio: http://pypi.python.org/pypi/asyncio
.. _Denis Bilenko: http://denisbilenko.com
.. _Fantix King: http://about.me/fantix
.. _the repository: https://github.com/fantix/gevent3

