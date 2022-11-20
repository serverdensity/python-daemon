#
# daemonize/tests/test_daemon.py
#

from datetime import datetime
import fcntl
import io
import logging
import os
import sys
import time
import unittest

from unittest.mock import patch

BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(
    os.path.abspath(__file__))))
sys.path.append(BASE_DIR)

from daemonize import Daemon
from .t_daemon import TDaemon

LOG_FILE = 'test_daemon.log'
LOG_PATH = os.path.join(BASE_DIR, 'logs')
not os.path.isdir(LOG_PATH) and os.mkdir(LOG_PATH, 0o0775)


def create_logger(logfile=LOG_FILE):
    log_format = ("%(asctime)s %(levelname)s %(name)s %(funcName)s "
                  "[line:%(lineno)d] %(message)s")
    logfile = os.path.abspath(os.path.join(LOG_PATH, logfile))
    logging.basicConfig(filename=logfile, format=log_format,
                        level=logging.DEBUG)


def control_daemon(action):
    t_daemon_path = os.path.join(BASE_DIR, 'daemonize', 'tests', 't_daemon.py')
    cmd = " ".join((sys.executable, t_daemon_path, action))
    os.system(cmd)


class BaseTestDaemon(unittest.TestCase):
    #_multiprocess_can_split_ = True
    _multiprocess_shared_ = True
    pidfile = os.path.join(LOG_PATH, 'test_daemon.pid')

    @property
    def is_pid_file_locked(self):
        result = False

        try:
            pf = open(self.pidfile, 'a+')
            fcntl.flock(pf.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except IOError:
            # Another process has a lock on this file.
            pf.close()
            result = True
        except OSError:
            # User could not create path.
            pass
        else:
            # Unlock the PID file.
            try:
                fcntl.flock(pf.fileno(), fcntl.LOCK_UN)
            finally:
                pf.close()

        return result


class TestRunningDaemon(BaseTestDaemon):
    testoutput = None

    @classmethod
    def setUpClass(cls):
        create_logger()

    ## @classmethod
    ## def tearDownClass(cls):
    ##     time.sleep(0.05)
    ##     cmd = 'rm -f ' + os.path.join(LOG_PATH, 'test_daemon*')
    ##     os.system(cmd)

    def setUp(self):
        control_daemon('start')
        time.sleep(0.1)
        self.testoutput = open(TDaemon.daemon, 'r')

    def tearDown(self):
        self.testoutput.close()

        if self.is_pid_file_locked:
            control_daemon('stop')

    #@unittest.skip("Temporarily skipped")
    def test_daemon_can_start(self):
        self.assertTrue(os.path.exists(self.pidfile))
        self.assertEqual(self.testoutput.read(), 'initialized')

    #@unittest.skip("Temporarily skipped")
    def test_daemon_can_stop(self):
        control_daemon('stop')

        for i in range(100):
            out = self.testoutput.read()

            if out == 'initialized' and not self.is_pid_file_locked:
                self.assertEqual(out, 'initialized')
                break

    #@unittest.skip("Temporarily skipped")
    def test_daemon_can_finish(self):
        time.sleep(0.4)
        self.assertFalse(self.is_pid_file_locked)
        self.assertEqual(self.testoutput.read(), 'finished')

    #@unittest.skip("Temporarily skipped")
    def test_daemon_can_restart(self):
        self.assertTrue(self.is_pid_file_locked)

        with open(self.pidfile) as f:
            pid1 = f.read()

        control_daemon('restart')
        time.sleep(0.1)
        self.assertTrue(self.is_pid_file_locked)

        with open(self.pidfile) as f:
            pid2 = f.read()

        self.assertNotEqual(pid1, pid2)


# Mock functions
def shutdown():
    pass


def redirect(self):
    pass


def fork1():
    return os.getpid()


def fork2():
    return 0


def dup2(fd, fd2):
    pass


def setsid():
    pass


def kill(pid, signal):
    pass


def get_pid_1(self):
    return os.getpid()


def get_pid_2(self):
    return 0


def _stop(self):
    pass


def is_running(self, pid):
    return False
# End mock functions


class TestDaemonCoverage(BaseTestDaemon):
    _log = logging.getLogger()

    @classmethod
    def setUpClass(cls):
        create_logger()

    def setUp(self):
        self.truncate_log_file(self.id())
        self._da = Daemon(self.pidfile, verbose=2)

    def tearDown(self):
        self._da.unlock_pid_file()

        if self._da._pf:
            self._da._pf.close()

        self._da = None

    def update_pid_file(self, pid=None):
        pid = pid if pid is not None else os.getpid()

        pf = self.get_writable_pid_file_object()
        pf.write("{:d}\n".format(pid))
        pf.flush()
        self._da._pf = pf

    def get_writable_pid_file_object(self):
        pf = open(self.pidfile, 'w')
        pf.seek(io.SEEK_SET)
        pf.truncate()
        return pf

    def get_pid(self):
        with open(self.pidfile, 'r') as pf:
            pid_txt = pf.read().strip()
            pid = int(pid_txt) if pid_txt else None

        return pid

    def read_logfile(self, messages):
        """
        Read the log file
        """
        messages = messages if isinstance(messages, list) else [messages]
        full_path = os.path.abspath(os.path.join(LOG_PATH, LOG_FILE))
        found = False
        now = datetime.now().strftime('%Y-%m-%d %H:%M')

        with open(full_path, 'r') as lf:
            data = lf.readlines()

            for message in messages:
                for line in data:
                    # Be sure we have this test run.
                    if (line.startswith(now) and message in line):
                        found = True
                        break

                msg = (f"Could not find '{message}' with data {now} "
                       f"in log file {data}.")
                self.assertTrue(found, msg=msg)

    def truncate_log_file(self, test):
        full_path = os.path.abspath(os.path.join(LOG_PATH, LOG_FILE))

        with open(full_path, 'w') as f:
            f.seek(io.SEEK_SET)
            f.truncate()

        self._log.info("Current test is: %s", test)

    #@unittest.skip("Temporarily skipped")
    def test_lock_unlock_pid_file(self):
        """
        Test that the locking a pid file works properly.
        """
        self._da.lock_pid_file()
        self.assertTrue(self.is_pid_file_locked)
        self._da.unlock_pid_file()
        self.assertFalse(self.is_pid_file_locked)

    #@unittest.skip("Temporarily skipped")
    #@patch('sys.exit', exit)
    def test_cannot_lock_twice(self):
        """
        Try to lock the pid file more than once. 2nd time should fail.
        """
        # Try first lock
        self.assertFalse(self.is_pid_file_locked)
        self._da.lock_pid_file()
        self.assertTrue(self.is_pid_file_locked)
        # Try second lock
        da = Daemon(self.pidfile, verbose=2)

        with self.assertRaises(SystemExit) as e:
            ret = da.lock_pid_file()

        self.assertEqual(3, e.exception.code)
        self.assertTrue(self.is_pid_file_locked)

        # Read the log file
        self.read_logfile("Another process has a lock")

    #@unittest.skip("Temporarily skipped")
    def test_is_running_RUNNING(self):
        """
        Test is the daemon is running in normal operation.
        """
        pid = os.getpid()
        result = self._da.is_running(pid)
        self.assertTrue(result)

    #@unittest.skip("Temporarily skipped")
    def test_is_running_STOPPED(self):
        """
        Test is the daemon has stopped.
        """
        result = self._da.is_running(None)
        self.assertFalse(result)

    #@unittest.skip("Temporarily skipped")
    def test_is_running_NOT_RUNNING(self):
        """
        Test is the daemon has stopped.
        """
        result = self._da.is_running(123456789) # A bogus pid
        self.assertFalse(result)

    #@unittest.skip("Temporarily skipped")
    def test_get_pid(self):
        """
        Test that the pid can be read.
        """
        self.update_pid_file()
        expect_pid = self._da.get_pid()
        self.assertNotEqual(expect_pid, None)

    #@unittest.skip("Temporarily skipped")
    def test__update_pid_file(self):
        """
        Test that the pid file can be updated.
        """
        self._da._pf = self.get_writable_pid_file_object()
        self._da._update_pid_file()
        expect_pid = self.get_pid()
        self.assertEqual(expect_pid, os.getpid())

    #@unittest.skip("Temporarily skipped")
    @patch('logging.shutdown', shutdown)
    @patch('os.fork', fork1)
    def test_daemonize_fork_1(self):
        """
        Test that the daemonize function forks properly with and without
        eventlet.
        """
        with self.assertRaises(SystemExit) as e:
            self._da.daemonize()

        self.assertEqual(0, e.exception.code)
        # Read the log file
        self.read_logfile("1st fork was successful with pid ")

        da = Daemon(self.pidfile, verbose=2, use_eventlet=True)

        with self.assertRaises(SystemExit) as e:
            da.daemonize()

        self.assertEqual(0, e.exception.code)
        # Read the log file
        self.read_logfile("1st fork was successful with pid ")

    #@unittest.skip("Temporarily skipped")
    @patch.object(Daemon, '_redirect', redirect)
    @patch('os.setsid', setsid)
    @patch('os.fork', fork2)
    def test_daemonize_fork_2(self):
        """
        Test that the daemonize function forks properly.
        """
        self._da.daemonize()
        # Read the log file
        self.read_logfile(["1st fork was successful with pid ",
                           "2nd fork was successful with pid "])

        da = Daemon(self.pidfile, verbose=2, use_gevent=True)

        da.daemonize()
        # Read the log file
        self.read_logfile(["1st fork was successful with pid ",
                           "2nd fork was successful with pid "])

    #@unittest.skip("Temporarily skipped")
    @patch.object(Daemon, '_redirect', redirect)
    @patch('os.fork', fork2)
    def test_start(self):
        """
        Test the start method.
        """
        with self.assertRaises(NotImplementedError) as e:
            self._da.start()

        self.assertEqual(str(e.exception),
                         "The run() method must be implemented.")

    #@unittest.skip("Temporarily skipped")
    @patch.object(Daemon, 'is_running', is_running)
    @patch.object(Daemon, '_stop', _stop)
    @patch('os.kill', kill)
    @patch.object(Daemon, 'get_pid', get_pid_1)
    def test_stop_NORMAL(self):
        """
        Test that stop works correctly.
        """
        self.update_pid_file()
        self._da.stop()
        # Read the log file
        self.read_logfile(["Stopping...", "Trying SIGTERM ", "...Stopped"])

    #@unittest.skip("Temporarily skipped")
    @patch.object(Daemon, 'get_pid', get_pid_2)
    def test_stop_NO_PID(self):
        """
        Test that a missing pid in the stop() method returns correctly.
        """
        self._da.stop()
        # Read the log file
        self.read_logfile("does not exist. Not running?")

    #@unittest.skip("Temporarily skipped")
    @patch('logging.shutdown', shutdown)
    def test__stop(self):
        """
        Test that the method _stop() exits properly.
        """
        with self.assertRaises(SystemExit) as e:
            ret = self._da._stop()

        self.assertEqual(6, e.exception.code)
        self.assertFalse(self.is_pid_file_locked)
        # Read the log file
        self.read_logfile("...Stopped")

    #@unittest.skip("Temporarily skipped")
    @patch('os.dup2', dup2)
    def test__redirect(self):
        """
        Test that the _redirect method works properly.
        """
        # Test with stderr
        self._da._redirect()
        # Read the log file
        self.read_logfile(["Starting redirect...", "...Ending redirect"])
        # Test without stderr
        da = Daemon(self.pidfile, stderr=None, verbose=2, use_gevent=True)
        da._redirect()
        # Read the log file
        self.read_logfile(["Starting redirect...", "...Ending redirect"])
