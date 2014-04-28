tulipcore
=========

tulipcore_ is an alternative gevent_ core loop. It is based on asyncio_ a.k.a.
tulip, the async library for Python 3. With tulipcore_, you can run gevent_
code on top of asyncio_.

tulipcore_ is written and maintained by `Fantix King`_ and is licensed under
MIT license.


Install tulipcore
-----------------

Install Python 3.4 or newer, greenlet_ extension and gevent_ library. Note if
you are running on Python 3.3, you still need to install the asyncio_ library.

Please note, at this point (mid 2014) main line gevent_ is in a progress fully
supporting Python 3. So if you want to take a try right now, you can install
my gevent fork:

.. code:: sh

  pip install git+git://github.com/fantix/gevent.git

Install tulipcore:

.. code:: sh

  pip install git+git://github.com/decentfox/tulipcore.git


Use tulipcore
-------------

Add this environment variable, it will tell gevent_ to use tulipcore_:

.. code:: sh

  GEVENT_LOOP=tulipcore.Loop

For example, you can run the gevent_ test suite with tulipcore_ installed:

.. code:: sh

  cd gevent/greentest
  GEVENT_LOOP=tulipcore.Loop python testrunner.py


History
-------

This project was originally called gevent3_, which was a wrapper of asyncio_
for Python 3 offering a gevent-compatible API. It was developed in a wrong
direction and I decided to abandon it.


.. _gevent: http://www.gevent.org
.. _gevent3: https://github.com/decentfox/tulipcore/tree/gevent3
.. _asyncio: https://docs.python.org/3/library/asyncio.html
.. _greenlet: https://github.com/python-greenlet/greenlet
.. _Fantix King: http://about.me/fantix
.. _tulipcore: https://github.com/decentfox/tulipcore
