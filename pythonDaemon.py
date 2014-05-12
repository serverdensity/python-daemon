"""
***
Modified generic daemon class
***

Author:         http://www.jejik.com/articles/2007/02/
                        a_simple_unix_linux_daemon_in_python/www.boxedice.com
                https://github.com/serverdensity/python-daemon

License:        http://creativecommons.org/licenses/by-sa/3.0/

Changes:        Various fixes where added in signal handling, pid file handling,
                return codes and exception handling

"""

# Core modules
import atexit
import os
import sys
import time
import signal
import logging
import traceback


class Daemon(object):
    """
    A generic daemon class.

    Usage: subclass the Daemon class and override the run() method
    """
    def __init__(self, pidfile, stdin=os.devnull,
                 stdout=os.devnull, stderr=os.devnull,
                 home_dir='.', umask=022, verbose=1):
        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.home_dir = home_dir
        self.verbose = verbose
        self.umask = umask

    def daemonize(self):
        """
        Do the UNIX double-fork magic, see Stevens' "Advanced
        Programming in the UNIX Environment" for details (ISBN 0201563177)
        http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        """
        try:
            pid = os.fork()
            if pid > 0:
                # Exit first parent
                sys.exit(0)
        except OSError, e:
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
        except OSError, e:
            sys.stderr.write(
                "fork #2 failed: %d (%s)\n" % (e.errno, e.strerror))
            sys.exit(1)

        if sys.platform != 'darwin':  # This block breaks on OS X
            # Redirect standard file descriptors
            sys.stdout.flush()
            sys.stderr.flush()
            si = file(self.stdin, 'r')
            so = file(self.stdout, 'a+')
            if self.stderr:
                se = file(self.stderr, 'a+', 0)
            else:
                se = so
            os.dup2(si.fileno(), sys.stdin.fileno())
            os.dup2(so.fileno(), sys.stdout.fileno())
            os.dup2(se.fileno(), sys.stderr.fileno())

            signal.signal(signal.SIGTERM, self._shutdown)
            signal.signal(signal.SIGINT, self._shutdown)

        if self.verbose >= 1:
            logging.info("Started")

        # Write pidfile
        atexit.register(
            self.delpid)  # Make sure pid file is removed if we quit
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write("%s\n" % pid)

    def delpid(self):
        if os.path.exists(self.pidfile):
            os.remove(self.pidfile)

    def start(self, return_on_exit=False, overwrite_pid=False, *args, **kwargs):
        """
        Start the daemon
        """

        if self.verbose >= 1:
            logging.info('Start daemon')

        # Check for a pidfile to see if the daemon already runs
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
        except SystemExit:
            pid = None

        if pid:
            if overwrite_pid:
                self.delpid()
            else:
                message = "pidfile %s already exist. Daemon already running?\n"
                sys.stderr.write(message % self.pidfile)
                if return_on_exit:
                    return False
                sys.exit(1)

        # Start the daemon
        _exitcode = 0
        try:
            self.daemonize()
            logging.info('Running process')
            self.run(*args, **kwargs)
            logging.info('Process finished normally.')
        except Exception as e:
            logging.error('Daemonized process threw an exception [%s].' % e)
            tb = traceback.format_exc()
            logging.error(tb)
            _exitcode = 255
        finally:
            # Make sure the pid file gets deleted even in case of errors
            self.delpid()
            if return_on_exit:
                return _exitcode if _exitcode else False
            sys.exit(_exitcode)

    def _shutdown(self, signum=None, frame=None):
        self.shutdown(frame)

    def shutdown(self, frame=None):
        os.kill(self.pid, signal.SIGTERM)

    def stop(self):
        """
        Stop the daemon
        """

        if self.verbose >= 1:
            logging.info("Stopping daemon...")

        # Get the pid from the pidfile
        pid = self.get_pid()

        if not pid:
            message = "pidfile %s does not exist. Daemon not running?\n"
            sys.stderr.write(message % self.pidfile)

            # Just to be sure. A ValueError might occur if the PID file is
            # empty but does actually exist
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)

            return  # Not an error in a restart

        # Try killing the daemon process
        try:
            os.kill(pid, signal.SIGTERM)
            _stime = time.time() + 10
            while 1:
                os.getpgid(pid)
                time.sleep(0.1)
                if time.time() > _stime:
                    os.kill(pid, signal.SIGTERM)
                    _stime += 3600
        except OSError, err:
            err = str(err)
            if err.find("No such process") > 0:
                self.delpid()
            else:
                print str(err)
                sys.exit(1)

        if self.verbose >= 1:
            logging.info("Stopped daemon")

    def restart(self):
        """
        Restart the daemon
        """
        self.stop()
        self.start()

    def get_pid(self):
        try:
            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()
        except IOError:
            pid = None
        except SystemExit:
            pid = None
        return pid

    def is_running(self):
        return self.running

    @property
    def running(self):
        pid = self.get_pid()
        return pid and os.path.exists('/proc/%d' % pid)

    def run(self):
        """
        You should override this method when you subclass Daemon.
        It will be called after the process has been
        daemonized by start() or restart().
        """
        raise NotImplemented('You should override this method when you subclass Daemon')
