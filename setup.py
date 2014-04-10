#!/usr/bin/env python
"""gevent build & installation script"""
import re
from os.path import join, dirname

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


__version__ = re.search("__version__\s*=\s*'(.*)'", open('gevent/__init__.py').read(), re.M).group(1)
assert __version__


def read(name, *args):
    try:
        return open(join(dirname(__file__), name)).read(*args)
    except OSError:
        return ''


setup(
    name='gevent3',
    version=__version__,
    description='A Gevent-compatible wrapper of asyncio for Python 3',
    long_description=read('README.rst'),
    author='Fantix King',
    author_email='fantix.king@gmail.com',
    url='https://github.com/fantix/gevent3',
    packages=['gevent'],
    install_requires=['greenlet>=0.3.2'],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        "Operating System :: Microsoft :: Windows",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
        "Development Status :: 2 - Pre-Alpha"])
