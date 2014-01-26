import sys
import errno
from asyncio import StreamReader
from asyncio.protocols import SubprocessProtocol
from gevent.event import AsyncResult
from gevent.hub import get_hub, linkproxy, sleep, getcurrent
from gevent.greenlet import Greenlet, joinall
spawn = Greenlet.spawn
import subprocess as __subprocess__


# Standard functions and classes that this module re-implements in a gevent-aware way.
__implements__ = ['Popen',
                  'call',
                  'check_call',
                  'check_output']


# Standard functions and classes that this module re-imports.
__imports__ = ['PIPE',
               'STDOUT',
               'CalledProcessError',
               # Python 3:
               'DEVNULL',
               # Windows:
               'CREATE_NEW_CONSOLE',
               'CREATE_NEW_PROCESS_GROUP',
               'STD_INPUT_HANDLE',
               'STD_OUTPUT_HANDLE',
               'STD_ERROR_HANDLE',
               'SW_HIDE',
               'STARTF_USESTDHANDLES',
               'STARTF_USESHOWWINDOW']


__extra__ = ['MAXFD',
             '_eintr_retry_call',
             'STARTUPINFO',
             'pywintypes',
             'list2cmdline',
             '_subprocess',
             # Python 2.5 does not have _subprocess, so we don't use it
             'WAIT_OBJECT_0',
             'WaitForSingleObject',
             'GetExitCodeProcess',
             'GetStdHandle',
             'CreatePipe',
             'DuplicateHandle',
             'GetCurrentProcess',
             'DUPLICATE_SAME_ACCESS',
             'GetModuleFileName',
             'GetVersion',
             'CreateProcess',
             'INFINITE',
             'TerminateProcess']


for name in __imports__[:]:
    try:
        value = getattr(__subprocess__, name)
        globals()[name] = value
    except AttributeError:
        __imports__.remove(name)
        __extra__.append(name)

_subprocess = getattr(__subprocess__, '_subprocess', None)
_NONE = object()

for name in __extra__[:]:
    if name in globals():
        continue
    value = _NONE
    try:
        value = getattr(__subprocess__, name)
    except AttributeError:
        if _subprocess is not None:
            try:
                value = getattr(_subprocess, name)
            except AttributeError:
                pass
    if value is _NONE:
        __extra__.remove(name)
    else:
        globals()[name] = value


__all__ = __implements__ + __imports__


mswindows = sys.platform == 'win32'
if mswindows:
    import msvcrt
else:
    import fcntl
    import pickle
    from gevent import monkey
    fork = monkey.get_original('os', 'fork')


def call(*popenargs, **kwargs):
    """Run command with arguments.  Wait for command to complete, then
    return the returncode attribute.

    The arguments are the same as for the Popen constructor.  Example:

    retcode = call(["ls", "-l"])
    """
    return Popen(*popenargs, **kwargs).wait()


def check_call(*popenargs, **kwargs):
    """Run command with arguments.  Wait for command to complete.  If
    the exit code was zero then return, otherwise raise
    CalledProcessError.  The CalledProcessError object will have the
    return code in the returncode attribute.

    The arguments are the same as for the Popen constructor.  Example:

    check_call(["ls", "-l"])
    """
    retcode = call(*popenargs, **kwargs)
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        raise CalledProcessError(retcode, cmd)
    return 0


def check_output(*popenargs, **kwargs):
    r"""Run command with arguments and return its output as a byte string.

    If the exit code was non-zero it raises a CalledProcessError.  The
    CalledProcessError object will have the return code in the returncode
    attribute and output in the output attribute.

    The arguments are the same as for the Popen constructor.  Example:

    >>> check_output(["ls", "-1", "/dev/null"])
    b'/dev/null\n'

    The stdout argument is not allowed as it is used internally.
    To capture standard error in the result, use stderr=STDOUT.

    >>> check_output(["/bin/sh", "-c", "echo hello world"], stderr=STDOUT)
    b'hello world\n'
    """
    if 'stdout' in kwargs:
        raise ValueError('stdout argument not allowed, it will be overridden.')
    process = Popen(stdout=PIPE, *popenargs, **kwargs)
    output = process.communicate()[0]
    retcode = process.poll()
    if retcode:
        cmd = kwargs.get("args")
        if cmd is None:
            cmd = popenargs[0]
        ex = CalledProcessError(retcode, cmd)
        # on Python 2.6 and older CalledProcessError does not accept 'output' argument
        ex.output = output
        raise ex
    return output


class StreamWriter:
    """Wraps a Transport.

    This exposes write(), writelines(), [can_]write_eof(),
    get_extra_info() and close().  It adds drain() which returns an
    optional Future on which you can wait for flow control.  It also
    adds a transport attribute which references the Transport
    directly.
    """

    def __init__(self, transport):
        self._transport = transport

    @property
    def transport(self):
        return self._transport

    def write(self, data):
        self._transport.write(data)

    def writelines(self, data):
        self._transport.writelines(data)

    def write_eof(self):
        return self._transport.write_eof()

    def can_write_eof(self):
        return self._transport.can_write_eof()

    def close(self):
        return self._transport.close()

    def get_extra_info(self, name, default=None):
        return self._transport.get_extra_info(name, default)


class GreenStreamReader(StreamReader):
    def close(self):
        self._transport.close()

    def readline(self):
        return get_hub().wait_async(super().readline())

    def read(self, n=-1):
        return get_hub().wait_async(super().read(n))

    def readexactly(self, n):
        return get_hub().wait_aync(super().readexactly(n))


class _DelegateProtocol(SubprocessProtocol):
    def __init__(self, popen):
        self._popen = popen
        self._transport = None

    def connection_made(self, transport):
        self._transport = transport
        self._popen._transport = transport
        self._popen.pid = self._transport.get_pid()
        stdin_transport = self._transport.get_pipe_transport(0)
        if stdin_transport is None:
            self._popen.stdin = None
        else:
            self._popen.stdin = StreamWriter(stdin_transport)
        stdout_transport = self._transport.get_pipe_transport(1)
        if stdout_transport is None:
            self._popen.stdout = None
        else:
            self._popen.stdout = GreenStreamReader()
            self._popen.stdout.set_transport(stdout_transport)
        stderr_transport = self._transport.get_pipe_transport(2)
        if stderr_transport is None:
            self._popen.stderr = None
        else:
            self._popen.stderr = GreenStreamReader()
            self._popen.stderr.set_transport(stderr_transport)

    def pipe_data_received(self, fd, data):
        if fd == 1 and self._popen.stdout is not None:
            self._popen.stdout.feed_data(data)
        elif fd == 2 and self._popen.stderr is not None:
            self._popen.stderr.feed_data(data)

    def pipe_connection_lost(self, fd, exc):
        if exc is None:
            if fd == 1 and self._popen.stdout is not None:
                self._popen.stdout.feed_eof()
            elif fd == 2 and self._popen.stderr is not None:
                self._popen.stderr.feed_eof()
        else:
            if fd == 1 and self._popen.stdout is not None:
                self._popen.stdout.set_exception(exc)
            elif fd == 2 and self._popen.stderr is not None:
                self._popen.stderr.set_exception(exc)

    def process_exited(self):
        self._popen.returncode = self._transport.get_returncode()
        self._popen.result.set(self._popen.returncode)


class Popen(SubprocessProtocol):

    def __init__(self, args, bufsize=-1,
                 stdin=None, stdout=None, stderr=None,
                 shell=False, universal_newlines=False, **kwargs):
        """Create new Popen instance."""
        assert not universal_newlines, "universal_newlines must be False"
        hub = get_hub()
        self.pid = None
        self.returncode = None
        self.universal_newlines = universal_newlines
        self.result = AsyncResult()
        self.stdin = None
        self.stdout = None
        self.stderr = None
        self._transport = None

        if shell:
            hub.wait_async(hub.loop.subprocess_shell(
                lambda: _DelegateProtocol(self), *args,
                stdin=stdin, stdout=stdout, stderr=stderr,
                bufsize=bufsize, **kwargs))
        else:
            hub.wait_async(hub.loop.subprocess_exec(
                lambda: _DelegateProtocol(self), *args,
                stdin=stdin, stdout=stdout, stderr=stderr,
                bufsize=bufsize, **kwargs))

    def __repr__(self):
        return '<%s at 0x%x pid=%r returncode=%r>' % (self.__class__.__name__, id(self), self.pid, self.returncode)

    def communicate(self, input=None, timeout=None):
        """Interact with process: Send data to stdin.  Read data from
        stdout and stderr, until end-of-file is reached.  Wait for
        process to terminate.  The optional input argument should be a
        string to be sent to the child process, or None, if no data
        should be sent to the child.

        communicate() returns a tuple (stdout, stderr)."""
        #TODO: timeout
        greenlets = []
        if self.stdin:
            greenlets.append(spawn(write_and_close, self.stdin, input))

        if self.stdout:
            stdout = spawn(self.stdout.read)
            greenlets.append(stdout)
        else:
            stdout = None

        if self.stderr:
            stderr = spawn(self.stderr.read)
            greenlets.append(stderr)
        else:
            stderr = None

        joinall(greenlets)

        if self.stdout:
            self.stdout.close()
        if self.stderr:
            self.stderr.close()

        self.wait()
        return (None if stdout is None else stdout.value or '',
                None if stderr is None else stderr.value or '')

    def poll(self):
        return self._internal_poll()

    def rawlink(self, callback):
        self.result.rawlink(linkproxy(callback, self))
    # XXX unlink

    def send_signal(self, sig):
        self._transport.send_signal(sig)

    def terminate(self):
        self._transport.terminate()

    def kill(self):
        #noinspection PyProtectedMember
        if self._transport._proc is not None:
            self._transport.kill()

    if mswindows:
        #
        # Windows methods
        #
        def _internal_poll(self):
            """Check if child process has terminated.  Returns returncode
            attribute.
            """
            if self.returncode is None:
                if WaitForSingleObject(self._handle, 0) == WAIT_OBJECT_0:
                    self.returncode = GetExitCodeProcess(self._handle)
                    self.result.set(self.returncode)
            return self.returncode

        def rawlink(self, callback):
            if not self.result.ready() and not self._waiting:
                self._waiting = True
                Greenlet.spawn(self._wait)
            self.result.rawlink(linkproxy(callback, self))
            # XXX unlink

        def _blocking_wait(self):
            WaitForSingleObject(self._handle, INFINITE)
            self.returncode = GetExitCodeProcess(self._handle)
            return self.returncode

        def _wait(self):
            self.threadpool.spawn(self._blocking_wait).rawlink(self.result)

        def wait(self, timeout=None):
            """Wait for child process to terminate.  Returns returncode
            attribute."""
            if self.returncode is None:
                if not self._waiting:
                    self._waiting = True
                    self._wait()
            return self.result.wait(timeout=timeout)

    else:
        #
        # POSIX methods
        #
        def _internal_poll(self):
            """Check if child process has terminated.  Returns returncode
            attribute.
            """
            if self.returncode is None:
                if get_hub() is not getcurrent():
                    sig_pending = getattr(self._loop, 'sig_pending', True)
                    if sig_pending:
                        sleep(0.00001)
            return self.returncode

        def wait(self, timeout=None):
            """Wait for child process to terminate.  Returns returncode
            attribute."""
            return self.result.wait(timeout=timeout)


def write_and_close(fobj, data):
    try:
        if data:
            fobj.write(data)
    except (OSError, IOError) as ex:
        if ex.errno != errno.EPIPE and ex.errno != errno.EINVAL:
            raise
    finally:
        try:
            fobj.close()
        except EnvironmentError:
            pass
