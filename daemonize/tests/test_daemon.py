#
# daemonize/tests/text_daemon.py
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
    pidfile = os.path.join(LOG_PATH, 'testing_daemon.pid')

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
    ##     cmd = 'rm -f ' + os.path.join(LOG_PATH, 'testing_daemon*')
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


# Used to override the sys.exit function in daemon.py.
def exit(value):
    pass


class TestDaemonCoverage(BaseTestDaemon):

    @classmethod
    def setUpClass(cls):
        create_logger()

    def setUp(self):
        self._da = Daemon(self.pidfile, verbose=2)

    def tearDown(self):
        self._da.unlock_pid_file()

        if self._da._pf:
            self._da._pf.close()

        self._da = None

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
    @patch('sys.exit', exit)
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
        now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        da.lock_pid_file()
        self.assertTrue(self.is_pid_file_locked)

        # Read the log file
        full_path = os.path.abspath(os.path.join(LOG_PATH, LOG_FILE))
        found = False

        with open(full_path, 'r') as lf:
            for line in lf:
                if (line.startswith(now) # Be sure we have this test run.
                    and "Another process has a lock" in line):
                    found = True
                    break

        self.assertTrue(found)
