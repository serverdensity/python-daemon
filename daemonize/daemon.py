"""
***
Modified generic daemon class
***

This work is based off the original work of Sander Marechal, you can see his
code at: http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/www.boxedice.com

License:  http://creativecommons.org/licenses/by-sa/3.0/

Changes:  23rd Jan 2009 (David Mytton <david@boxedice.com>)
          - Replaced hard coded '/dev/null in __init__ with os.devnull
          - Added OS check to conditionally remove code that doesn't
            work on OS X
          - Added output to console on completion
          - Tidied up formatting
          11th Mar 2009 (David Mytton <david@boxedice.com>)
          - Fixed problem with daemon exiting on Python 2.4
            (before SystemExit was part of the Exception base)
          13th Aug 2010 (David Mytton <david@boxedice.com>
          - Fixed unhandled exception if PID file is empty
          23rd Nov 2018 (Carl Nobile <carl.nobile@gmail.com>)
          - Now using fcntl to put an OS lock on the pid file, this will
            catch all instances of the application exiting including
            application and machine crashes making the PID file no longer
            necessory to delete before a restart.
          - Added a log file. A daemon process is disconnected from the
            terminal so cannot print to the screen. The only soluction is to
            send messages to a log file.
          10th Nov 2022 (Carl Nobile <carl.nobile@gmail.com>)
          - Removed support for Python 2.
          20th Nov 2022 (Carl Nobile <carl.nobile@gmail.com>)
          - Fixed a few bug with how redirecting of stdin, stdout, and
            stderr was being done.

Exit values
-----------
0 = Exited as expected with no errors.
1 = Fork #1 failed
2 = Fork #2 failed
3 = Another process has a lock.
4 = User could not create PID file.
5 = Could not find a process to kill.
6 = An external signal caused the exit (Could actually be a normal way to kill).
"""

# Core modules
import errno
import fcntl
import io
import logging
import os
import pwd
import sys
import time
import signal


class Daemon:
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method.
    """

    def __init__(self, pidfile, stdin=os.devnull, stdout=os.devnull,
                 stderr=os.devnull, base_dir='.', umask=0o22, verbose=1,
                 use_gevent=False, logger_name=''):
        """
        Constructor take the following positional and keyword arguments.

        :param pidfile: The full path to the pid file.
        :type pidfile: str
        :param stdin: The stdin stream (default is os.devnull).
        :type stdin: IO Stream
        :param stdout: The stdout stream (default is os.devnull).
        :type stdout: IO Stream
        :param stderr: The stderr stream (default is os.devnull).
        :type stderr: IO Stream
        :param base_dir: Path to base used by the daemon process
                         (defaults to .).
        :type base_dir: str
        :param umask: Set the permissions for the *base_dir* (defaults to 0o22).
        :type umask: Octal int
        :param verbose: Sets the logger to various levels. (1 = INFO,
                        2 = DEBUG, 3 = ERROR, any other number is WARNING)
        :type verbose: int
        :param use_gevent: Use gevent for signals (defaults to False).
        :type use_gevent: bool
        :param logger_name: The name of the pre defines logger (default is ''
                            (root)).
        """
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.base_dir = base_dir
        self.verbose = verbose
        self.umask = umask
        self.use_gevent = use_gevent
        self._pf = None
        self._log = logging.getLogger(logger_name)

        if verbose == 1: # pragma: no cover
            self._log.setLevel(logging.INFO)
        elif verbose == 2:
            self._log.setLevel(logging.DEBUG)
        elif verbose == 3: # pragma: no cover
            self._log.setLevel(logging.ERROR)
        else: # pragma: no cover
            self._log.setLevel(logging.WARNING)

    def daemonize(self):
        """
        Do the UNIX double-fork magic, see Stevens' 'Advanced
        Programming in the UNIX Environment' for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
        except OSError as e: # pragma: no cover
            self._log.error("Fork #1 failed: %d (%s)\n", e.errno, e.strerror)
            logging.shutdown()
            sys.exit(1)
        else:
            self._log.debug("1st fork was successful with pid %s", pid)

            if pid > 0:
                # Exit first parent
                logging.shutdown()
                sys.exit(0)

        # Decouple from parent environment
        os.chdir(self.base_dir)
        os.setsid()
        os.umask(self.umask)

        # Do second fork
        try:
            pid = os.fork()
        except OSError as e: # pragma: no cover
            self._log.error("Fork #2 failed: %d (%s)\n", e.errno, e.strerror)
            logging.shutdown()
            sys.exit(2)
        else:
            self._log.debug("2nd fork was successful with pid %s", pid)

            if pid > 0: # pragma: no cover
                # Exit from second parent
                logging.shutdown()
                sys.exit(0)

        if sys.platform != 'darwin':  # This block breaks on OS X
            self._redirect()

        def sigtermhandler(signum, frame): # pragma: no cover
            if self.get_pid():
                self._stop()

        if self.use_gevent:
            import gevent
            gevent.reinit()
            gevent.signal_handler(signal.SIGTERM, sigtermhandler,
                                  signal.SIGTERM, None)
            gevent.signal_handler(signal.SIGINT, sigtermhandler,
                                  signal.SIGINT, None)
        else:
            signal.signal(signal.SIGTERM, sigtermhandler)
            signal.signal(signal.SIGINT, sigtermhandler)

    def _redirect(self):
        """
        Redirect standard file descriptors.
        """
        self._log.debug("Starting redirect...")
        sys.stdin.flush()
        sys.stdout.flush()
        sys.stderr.flush()
        fd_si = os.open(self.stdin, os.O_RDWR)
        fd_so = os.open(self.stdout, os.O_RDWR)

        if self.stderr:
            fd_se = os.open(self.stderr, os.O_RDWR)
        else:
            fd_se = fd_so

        os.dup2(fd_si, sys.stdin.fileno())

        try:
            #https://stackoverflow.com/questions/10029697/file-descriptors-redirecting-is-stuck
            os.dup2(fd_so, sys.stdout.fileno())
        except io.UnsupportedOperation:
            pass

        os.dup2(fd_se, sys.stderr.fileno())
        os.close(fd_si)
        os.close(fd_so)
        if self.stderr: os.close(fd_se)
        self._log.debug("...Ending redirect")

    def lock_pid_file(self):
        """
        The lock file is released whenever the application releases the
        lock or the OS detects the application is no longer running so
        the locked file never needs to be removed.
        """
        user = pwd.getpwuid(os.getuid()).pw_name

        try:
            if not self._pf: self._pf = open(self.pidfile, 'a+')
            fcntl.flock(self._pf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError as e:
            self._pf.close()
            msg = ("Another process has a lock on this file %s for user "
                   "'%s', %s (%s)")
            self._log.warning(msg, self.pidfile, user, e.errno, e.strerror)
            logging.shutdown()
            sys.exit(3)
        except OSError as e: # pragma: no cover
            msg = "User '%s' could not create path: %s, %s (%s)"
            self._log.error(msg, user, self.pidfile, e.errno, e.strerror)
            logging.shutdown()
            sys.exit(4)
        else:
            msg = "Successfully created/locked pid file %s."
            self._log.info(msg, self.pidfile)

    def unlock_pid_file(self):
        """
        Unlock a file. The OS will unlock the file when the app is no
        longer running, so this may never get called.
        """
        try:
            pf = open(self.pidfile, 'a+') if not self._pf else self._pf
            fcntl.flock(pf.fileno(), fcntl.LOCK_UN)
        except IOError as e: # pragma: no cover
            pf is not self._pf and pf.close()
            msg = "The lock file %s could not be unlocked, %s, %s (%s)"
            self._log.error(msg, self.pidfile, e.errno, e.strerror)
        else:
            pf is not self._pf and pf.close()
            msg = "Successfully unlocked PID file %s."
            self._log.info(msg, self.pidfile)

    def start(self, *args, **kwargs):
        """
        Start the daemon

        :param args: Any positional arguments to pass to the user's run method.
        :type args: tuple
        :param kwargs: Any keyword arguments to pass to the user's run method.
        :type kwargs: dict
        """
        # Check for a pidfile to see if the daemon already runs
        self.lock_pid_file()
        self._log.info("Starting...")
        # Start the daemon
        self.daemonize()
        # Update the pid in the PID file, can only be done after
        # daemonization.
        self._update_pid_file()
        self._log.info("...Started")
        self.run(*args, **kwargs)

    def stop(self):
        """
        Stop the daemon
        """
        self._log.info("Stopping...")
        # Get the pid from the pidfile
        pid = self.get_pid()

        if not pid:
            msg = "pidfile %s does not exist. Not running?"
            self._log.warning(msg, self.pidfile)
            return  # Not an error in a restart

        # Try killing the daemon process
        try:
            i = 0

            while True:
                i += 1
                self._log.debug("Trying SIGTERM %s time(s).", i)
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.2)

                if i % 10 == 0: # pragma: no cover
                    self._log.debug("Trying SIGKILL.")
                    os.kill(pid, signal.SIGKILL)

                if not self.is_running(pid): break
        except OSError as e: # pragma: no cover
            self._log.error(e)
            sys.exit(5)
        finally:
            self.stop_callback()
            self._log.info("...Stopped")
            logging.shutdown()

    def _stop(self):
        self.unlock_pid_file()
        self.stop_callback()
        self._log.info("...Stopped")
        logging.shutdown()
        sys.exit(6)

    def stop_callback(self):
        """
        Override this callback if you need to do something before exiting.
        """
        return

    def restart(self): # pragma: no cover
        """
        Restart the daemon
        """
        self.stop()
        time.sleep(1.0)
        self.start()

    def is_running(self, pid):
        """
        Check to see if the pid is already in use.

        :param pid: The pid found in the pid file.
        :type pid: int
        """
        result = False

        if pid is None:
            self._log.info('Process has stopped.')
        elif os.path.exists('/proc/{:d}'.format(pid)):
            self._log.info('Process (pid %d) is running.', pid)
            result = True
        else:
            self._log.info('Process (pid %d) is not running.', pid)

        return result

    def get_pid(self):
        try:
            with open(self.pidfile, 'r') as pf:
                pid_txt = pf.read().strip()
                pid = int(pid_txt) if pid_txt else None
                pid = None if not self.is_running(pid) else pid
        except (IOError, SystemExit) as e: # pragma: no cover
            self._log.error("Could not open pid file %s, %s", self.pidfile, e)
            pid = None

        return pid

    def _update_pid_file(self, pid=None):
        self._pf.seek(io.SEEK_SET)
        self._pf.truncate()
        pid = pid if pid is not None else os.getpid()
        self._pf.write("{:d}\n".format(pid))
        self._pf.flush()

    def run(self, *args, **kwards): # pragma: no cover
        """
        You should override this method when you subclass Daemon. It will
        be called after the process has been daemonized by start() or
        restart().

        :param args: Any positional arguments to pass to the user's run method.
        :type args: tuple
        :param kwargs: Any keyword arguments to pass to the user's run method.
        :type kwargs: dict
        """
        raise NotImplementedError("The run() method must be implemented.")


if __name__ == '__main__': # pragma: no cover
    class MyDaemon(Daemon):

        def run(self):
            while True:
                time.sleep(1.0)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    log_path = os.path.abspath(os.path.join(base_dir, '..', 'logs'))
    not os.path.isdir(log_path) and os.mkdir(log_path, 0o0775)
    pidfile = os.path.abspath(os.path.join(log_path, 'daemon.pid'))
    log_format = ("%(asctime)s %(levelname)s %(name)s %(funcName)s "
                  "[line:%(lineno)d] %(message)s")
    logfile = os.path.abspath(os.path.join(log_path, 'daemon.log'))
    logging.basicConfig(filename=logfile, format=log_format,
                        level=logging.DEBUG)
    #logging.basicConfig(format=log_format)
    md = MyDaemon(pidfile, verbose=2)
    arg = sys.argv[1] if len(sys.argv) == 2 else ''
    arg = 'start' if arg not in ('start', 'stop', 'restart') else arg
    getattr(md, arg)()
