# This file is renamed to "Makefile.ext" in release tarballs so that setup.py won't try to
# run it.  If you want setup.py to run "make" automatically, rename it back to "Makefile".

PYTHON ?= python${TRAVIS_PYTHON_VERSION}
CYTHON ?= cython

all:
	echo

clean:
	echo

doc:
	cd doc && PYTHONPATH=.. make html

whitespace:
	! find . -not -path "./.git/*" -not -path "./build/*" -not -path "./libev/*" -not -path "./c-ares/*" -not -path "./doc/_build/*" -type f | xargs egrep -l " $$"

pep8:
	${PYTHON} `which pep8` .

pyflakes:
	${PYTHON} util/pyflakes.py

lint: whitespace pep8 pyflakes

travistest:
	which ${PYTHON}
	${PYTHON} --version

	cd greenlet-* && ${PYTHON} setup.py install -q
	${PYTHON} -c 'import greenlet; print(greenlet, greenlet.__version__)'

ifeq ($(shell ${PYTHON} -c 'import sys;print(".".join(map(str, sys.version_info[:2])))'), 3.3)
	cd asyncio* && ${PYTHON} setup.py install -q
	${PYTHON} -c 'import asyncio'
endif

	${PYTHON} setup.py install

	cd greentest && GEVENT_RESOLVER=thread ${PYTHON} testrunner.py --expected ../known_failures.txt
	cd greentest && GEVENT_FILE=thread ${PYTHON} testrunner.py --expected ../known_failures.txt `grep -l subprocess test_*.py`

travis:
	make whitespace

	sudo -E apt-get install ${PYTHON} ${PYTHON}-dev

	pip install -q pep8
	PYTHON=python make pep8

	pip install -q pyflakes
	PYTHON=python make pyflakes

	pip install -q --download . greenlet
	unzip -q greenlet-*.zip

ifeq ($(shell ${PYTHON} -c 'import sys;print(".".join(map(str, sys.version_info[:2])))'), 3.3)
	pip install -q --download . asyncio
	tar xf asyncio*.tar.gz
endif

	sudo -E make travistest

	sudo -E apt-get install ${PYTHON}-dbg

	sudo -E PYTHON=${PYTHON}-dbg GEVENTSETUP_EV_VERIFY=3 make travistest


.PHONY: clean all doc pep8 whitespace pyflakes lint travistest travis
