import os
from io import BufferedRandom
from io import BufferedReader
from io import BufferedWriter
from io import BytesIO
from io import DEFAULT_BUFFER_SIZE
from io import RawIOBase
from io import TextIOWrapper
from io import UnsupportedOperation

from gevent._socketcommon import EBADF
from gevent.hub import get_hub
from gevent.lock import Semaphore, DummySemaphore
from gevent.os import _read
from gevent.os import _write
from gevent.os import ignored_errors
from gevent.os import make_nonblocking


cancel_wait_ex = IOError(EBADF, 'File descriptor was closed in another greenlet')
FileObjectClosed = IOError(EBADF, 'Bad file descriptor (FileObject was closed)')

try:
    from fcntl import fcntl
except ImportError:
    fcntl = None


__all__ = ['FileObjectPosix',
           'FileObjectThread',
           'FileObject']


if fcntl is None:

    __all__.remove('FileObjectPosix')

else:
    class GreenFileDescriptorIO(RawIOBase):
        def __init__(self, fileno, mode='r', closefd=True):
            super().__init__()
            self._closed = False
            self._closefd = closefd
            self._fileno = fileno
            make_nonblocking(fileno)
            self._readable = 'r' in mode
            self._writable = 'w' in mode
            self.hub = get_hub()
            io = self.hub.loop.io
            if self._readable:
                self._read_event = io(fileno, 1)
            else:
                self._read_event = None
            if self._writable:
                self._write_event = io(fileno, 2)
            else:
                self._write_event = None

        def readable(self):
            return self._readable

        def writable(self):
            return self._writable

        def fileno(self):
            return self._fileno

        @property
        def closed(self):
            return self._closed

        def close(self):
            if self._closed:
                return
            self.flush()
            self._closed = True
            if self._readable:
                self.hub.cancel_wait(self._read_event, cancel_wait_ex)
            if self._writable:
                self.hub.cancel_wait(self._write_event, cancel_wait_ex)
            fileno = self._fileno
            if self._closefd:
                self._fileno = None
                os.close(fileno)

        def read(self, n=1):
            if not self._readable:
                raise UnsupportedOperation('readinto')
            while True:
                try:
                    return _read(self._fileno, n)
                except (IOError, OSError) as ex:
                    if ex.args[0] not in ignored_errors:
                        raise
                self.hub.wait(self._read_event)

        def readall(self):
            ret = BytesIO()
            while True:
                data = self.read(DEFAULT_BUFFER_SIZE)
                if not data:
                    break
                ret.write(data)
            return ret.getvalue()

        def write(self, b):
            if not self._writable:
                raise UnsupportedOperation('write')
            while True:
                try:
                    return _write(self._fileno, b)
                except (IOError, OSError) as ex:
                    if ex.args[0] not in ignored_errors:
                        raise
                self.hub.wait(self._write_event)

    class FileObjectPosix:
        default_bufsize = 8192

        def __init__(self, fobj, mode='rb', bufsize=-1, close=True):
            if isinstance(fobj, int):
                fileno = fobj
                fobj = None
            else:
                fileno = fobj.fileno()
            if not isinstance(fileno, int):
                raise TypeError('fileno must be int: %r' % fileno)

            mode = (mode or 'rb').replace('b', '')
            if 'U' in mode:
                self._translate = True
                mode = mode.replace('U', '')
            else:
                self._translate = False
            assert len(mode) == 1, 'mode can only be [rb, rU, wb]'

            self._fobj = fobj
            self._closed = False
            self._close = close

            self.fileio = GreenFileDescriptorIO(fileno, mode, closefd=close)

            if bufsize < 0:
                bufsize = self.default_bufsize
            if mode == 'r':
                if bufsize == 0:
                    bufsize = 1
                elif bufsize == 1:
                    bufsize = self.default_bufsize
                self.io = BufferedReader(self.fileio, bufsize)
            elif mode == 'w':
                self.io = BufferedWriter(self.fileio, bufsize)
            else:
                # QQQ: not used
                self.io = BufferedRandom(self.fileio, bufsize)
            if self._translate:
                self.io = TextIOWrapper(self.io)

        @property
        def closed(self):
            """True if the file is cloed"""
            return self._closed

        def close(self):
            if self._closed:
                # make sure close() is only ran once when called concurrently
                return
            self._closed = True
            try:
                self.io.close()
                self.fileio.close()
            finally:
                self._fobj = None

        def flush(self):
            self.io.flush()

        def fileno(self):
            return self.io.fileno()

        def write(self, data):
            self.io.write(data)

        def writelines(self, list):
            self.io.writelines(list)

        def read(self, size=-1):
            return self.io.read(size)

        def readline(self, size=-1):
            return self.io.readline(size)

        def readlines(self, sizehint=0):
            return self.io.readlines(sizehint)

        def __iter__(self):
            return self.io


class FileObjectThread(object):

    def __init__(self, fobj, *args, **kwargs):
        self._close = kwargs.pop('close', True)
        self.threadpool = kwargs.pop('threadpool', None)
        self.lock = kwargs.pop('lock', True)
        if kwargs:
            raise TypeError('Unexpected arguments: %r' % kwargs.keys())
        if self.lock is True:
            self.lock = Semaphore()
        elif not self.lock:
            self.lock = DummySemaphore()
        if not hasattr(self.lock, '__enter__'):
            raise TypeError('Expected a Semaphore or boolean, got %r' % type(self.lock))
        if isinstance(fobj, int):
            if not self._close:
                # we cannot do this, since fdopen object will close the descriptor
                raise TypeError('FileObjectThread does not support close=False')
            fobj = os.fdopen(fobj, *args)
        self._fobj = fobj
        if self.threadpool is None:
            self.threadpool = get_hub().threadpool

    def _apply(self, func, args=None, kwargs=None):
        with self.lock:
            return self.threadpool.apply_e(BaseException, func, args, kwargs)

    def close(self):
        fobj = self._fobj
        if fobj is None:
            return
        self._fobj = None
        try:
            self.flush(_fobj=fobj)
        finally:
            if self._close:
                fobj.close()

    def flush(self, _fobj=None):
        if _fobj is not None:
            fobj = _fobj
        else:
            fobj = self._fobj
        if fobj is None:
            raise FileObjectClosed
        return self._apply(fobj.flush)

    def __repr__(self):
        return '<%s _fobj=%r threadpool=%r>' % (self.__class__.__name__, self._fobj, self.threadpool)

    def __getattr__(self, item):
        assert item != '_fobj'
        if self._fobj is None:
            raise FileObjectClosed
        return getattr(self._fobj, item)

    for method in ['read', 'readinto', 'readline', 'readlines', 'write', 'writelines', 'xreadlines']:

        exec('''def %s(self, *args, **kwargs):
    fobj = self._fobj
    if fobj is None:
        raise FileObjectClosed
    return self._apply(fobj.%s, args, kwargs)
''' % (method, method))

    def __iter__(self):
        return self

    def __next__(self):
        line = self.readline()
        if line:
            return line
        raise StopIteration


try:
    FileObject = FileObjectPosix
except NameError:
    FileObject = FileObjectThread


class FileObjectBlock(object):

    def __init__(self, fobj, *args, **kwargs):
        self._close = kwargs.pop('close', True)
        if kwargs:
            raise TypeError('Unexpected arguments: %r' % kwargs.keys())
        if isinstance(fobj, int):
            if not self._close:
                # we cannot do this, since fdopen object will close the descriptor
                raise TypeError('FileObjectBlock does not support close=False')
            fobj = os.fdopen(fobj, *args)
        self._fobj = fobj

    def __repr__(self):
        return '<%s %r>' % (self._fobj, )

    def __getattr__(self, item):
        assert item != '_fobj'
        if self._fobj is None:
            raise FileObjectClosed
        return getattr(self._fobj, item)


config = os.environ.get('GEVENT_FILE')
if config:
    klass = {'thread': 'gevent.fileobject.FileObjectThread',
             'posix': 'gevent.fileobject.FileObjectPosix',
             'block': 'gevent.fileobject.FileObjectBlock'}.get(config, config)
    if klass.startswith('gevent.fileobject.'):
        FileObject = globals()[klass.split('.', 2)[-1]]
    else:
        from gevent.hub import _import
        FileObject = _import(klass)
    del klass
