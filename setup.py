#!/usr/bin/env python
from os.path import join, dirname

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup


def read(name, *args):
    try:
        return open(join(dirname(__file__), name)).read(*args)
    except OSError:
        return ''


setup(
    name='tulipcore',
    version='0.1.0a2',
    description='An alternative Gevent core loop implementation with asyncio',
    long_description=read('README.rst'),
    author='Fantix King',
    author_email='fantix.king@gmail.com',
    url='https://github.com/decentfox/tulipcore',
    py_modules=['tulipcore'],
    install_requires=['gevent>=1.1'],
    classifiers=[
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.3",
        "Programming Language :: Python :: 3.4",
        "Operating System :: MacOS :: MacOS X",
        "Operating System :: POSIX",
        # "Operating System :: Microsoft :: Windows",
        "Topic :: Internet",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "Intended Audience :: Developers",
        "Development Status :: 3 - Alpha"])
