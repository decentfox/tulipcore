#!/bin/sh
set -e -x
python -mtimeit -r 6 -s'from gevent import spawn; g = spawn(lambda: 5); l = lambda: 5' 'for _ in range(1000): g.link(l)'
python -mtimeit -r 6 -s'from gevent import spawn; g = spawn(lambda: 5); l = lambda *args: 5' 'for _ in range(10): g.link(l);' 'g.join()'
python -mtimeit -r 6 -s'from gevent import spawn; g = spawn(lambda: 5); l = lambda *args: 5' 'for _ in range(100): g.link(l);' 'g.join()'
python -mtimeit -r 6 -s'from gevent import spawn; g = spawn(lambda: 5); l = lambda *args: 5' 'for _ in range(1000): g.link(l);' 'g.join()'
python -mtimeit -r 6 -s'from gevent import spawn; g = spawn(lambda: 5); l = lambda *args: 5' 'for _ in range(10000): g.link(l);' 'g.join()'
python -mtimeit -r 6 -s'from gevent import spawn; g = spawn(lambda: 5); l = lambda *args: 5' 'for _ in range(100000): g.link(l);' 'g.join()'
