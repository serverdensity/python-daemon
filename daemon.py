"""
***
Modified generic daemon class
***

Author:   http://www.jejik.com/articles/2007/02/
                 a_simple_unix_linux_daemon_in_python/www.boxedice.com

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
            application and machine crashes. The PID file no longer needs
            to be deleted.
          - Added a log file. A daemon process is disconnected from the
            terminal so cannot print to the screen after the process is
            daemonized.
"""

# Core modules
from __future__ import print_function
import errno
import fcntl
import io
import logging
import os
import pwd
import sys
import time
import signal


class Daemon(object):
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, pidfile, stdin=os.devnull, stdout=os.devnull,
                 stderr=os.devnull, home_dir='.', umask=0o22, verbose=1,
                 use_gevent=False, use_eventlet=False, logger_name=''):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.home_dir = home_dir
        self.verbose = verbose
        self.umask = umask
        self.daemon_alive = True
        self.use_gevent = use_gevent
        self.use_eventlet = use_eventlet
        self._pf = None
        self._log = logging.getLogger(logger_name)

        if verbose == 1:
            self._log.setLevel(logging.INFO)
        elif verbose == 2:
            self._log.setLevel(logging.DEBUG)
        else:
            self._log.setLevel(logging.WARNING)

    def daemonize(self):
        """
        Do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        if self.use_eventlet:
            import eventlet.tpool
            eventlet.tpool.killall()
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(
                "fork #1 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        # Decouple from parent environment
        os.chdir(self.home_dir)
        os.setsid()
        os.umask(self.umask)

        # Do second fork
        try:
            pid = os.fork()
            if pid > 0:
                # Exit from second parent
                sys.exit(0)
        except OSError as e:
            sys.stderr.write(
                "fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(2)

        if sys.platform != 'darwin':  # This block breaks on OS X
            # Redirect standard file descriptors
            sys.stdout.flush()
            sys.stderr.flush()
            si = open(self.stdin, 'r')
            so = open(self.stdout, 'a+')
            if self.stderr:
                try:
                    se = open(self.stderr, 'a+', 0)
                except ValueError:
                    # Python 3 can't have unbuffered text I/O
                    se = open(self.stderr, 'a+', 1)
            else:
                se = so

            os.dup2(si.fileno(), sys.stdin.fileno())
            os.dup2(so.fileno(), sys.stdout.fileno())
            os.dup2(se.fileno(), sys.stderr.fileno())

        def sigtermhandler(signum, frame):
            self.daemon_alive = False
            self.unlock_pid_file()
            sys.exit(0)

        if self.use_gevent:
            import gevent
            gevent.reinit()
            gevent.signal(signal.SIGTERM, sigtermhandler, signal.SIGTERM, None)
            gevent.signal(signal.SIGINT, sigtermhandler, signal.SIGINT, None)
        else:
            signal.signal(signal.SIGTERM, sigtermhandler)
            signal.signal(signal.SIGINT, sigtermhandler)

    def lock_pid_file(self):
        """
        The lock file is released whenever the application releases the
        lock or the OS detects the application is no longer running so
        the locked file never needs to be removed.
        """
        user = pwd.getpwuid(os.getuid()).pw_name

        try:
            self._pf = open(self.pidfile, 'a+')
            fcntl.flock(self._pf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            msg = "Successfully created/locked pid file %s."
            self._log.info(msg, self.pidfile)
        except IOError as e:
            msg = ("Another process has a lock on this file %s for user "
                   "'%s', %s (%s)")
            self._log.warning(msg, self.pidfile, user, e.errno, e.strerror)
            sys.exit(3)
        except OSError as e:
            msg = "User '%s' could not create path: %s, %s (%s)"
            self._log.error(msg, user, self.pidfile, e.errno, e.strerror)
            sys.exit(4)

    def unlock_pid_file(self):
        """
        Unlock a file. The OS will unlock the file when the app is no
        longer running.
        """
        if self._pf:
            try:
                fcntl.flock(self._pf.fileno(), fcntl.LOCK_UN)
            except IOError as e:
                self._pf.close()
                msg = "The lock file %s could not be unlocked, %s, %s (%s)"
                self._log.error(msg, self.pidfile, e.errno, e.strerror)
            else:
                self._pf.close()
                msg = "Successfully unlocked lock file %s."
                self._log.info(msg, self.pidfile)

    def start(self, *args, **kwargs):
        """
        Start the daemon
        """
        # Check for a pidfile to see if the daemon already runs
        self.lock_pid_file()
        self._log.info("Starting...")
        # Start the daemon
        self.daemonize()
        # Update the pid in the PID file, can only be done after
        # daemonization.
        self._update_pid_file()
        self._log.info("Started")
        self.run(*args, **kwargs)

    def _update_pid_file(self):
        pid = os.getpid()
        self._pf.seek(io.SEEK_SET)
        self._pf.write("{:d}\n".format(pid))
        self._pf.flush()

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
                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
                i = i + 1

                if i % 10 == 0:
                    os.kill(pid, signal.SIGHUP)
        except OSError as err:
            self._log.error(err)
            sys.exit(5)
        else:
            self.unlock_pid_file()

        self._log.info("Stopped")

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def get_pid(self):
        try:
            pf = open(self.pidfile, 'r')
        except (IOError, SystemExit) as e:
            self._log.error(e)
            pid = None
        else:
            pid = int(pf.read().strip())
            pf.close()

        return pid

    def is_running(self):
        result = False
        pid = self.get_pid()

        if pid is None:
            self._log.info('Process is stopped')
            result = False
        elif os.path.exists('/proc/%d' % pid):
            self._log.info('Process (pid %d) is running...', pid)
            result = True
        else:
            self._log.info('Process (pid %d) is killed', pid)

        return result

    def run(self):
        """
        You should override this method when you subclass Daemon.
        It will be called after the process has been
        daemonized by start() or restart().
        """
        raise NotImplementedError


if __name__ == '__main__':
    class MyDaemon(Daemon):

        def run(self):
            while True:
                time.sleep(1.0)

    base_dir = os.path.dirname(os.path.dirname(__file__))
    log_path = os.path.join(base_dir, 'logs')
    pidfile = os.path.abspath(os.path.join(log_path, 'daemon.pid'))
    log_format = ("%(asctime)s %(levelname)s %(name)s %(funcName)s "
                  "[line:%(lineno)d] %(message)s")
    logfile = os.path.abspath(os.path.join(log_path, 'daemon.log'))
    logging.basicConfig(filename=logfile, format=log_format,
                        level=logging.DEBUG)
    #logging.basicConfig(format=log_format)
    md = MyDaemon(pidfile, verbose=1)
    md.start()
