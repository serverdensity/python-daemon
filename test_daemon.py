import fcntl
import io
import os
import sys
import time
import unittest

from daemon import Daemon

try:
    from unittest.mock import patch
except:
    # Python 2.x doesn't have mock, you'll need to install it.
    from mock import patch

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_PATH = os.path.join(BASE_DIR, 'logs')
not os.path.isdir(LOG_PATH) and os.mkdir(LOG_PATH, 0o0775)


class TDaemon(Daemon):
    daemon = os.path.join(LOG_PATH, 'testing_daemon')

    def __init__(self, *args, **kwargs):
        super(TDaemon, self).__init__(*args, **kwargs)
        testoutput = open(self.daemon, 'w')
        testoutput.write('inited')
        testoutput.close()

    def run(self):
        time.sleep(0.3)
        testoutput = open(self.daemon, 'w')
        testoutput.write('finished')
        testoutput.close()


def control_daemon(action):
    os.system(" ".join((sys.executable, __file__, action)))


class BaseTestDaemon(unittest.TestCase):
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

    def setUp(self):
        control_daemon('start')
        time.sleep(0.1)
        self.testoutput = open(TDaemon.daemon, 'r')

    def tearDown(self):
        self.testoutput.close()

        if self.is_pid_file_locked:
            control_daemon('stop')

        time.sleep(0.05)
        cmd = 'rm -f ' + os.path.join(LOG_PATH, 'testing_daemon*')
        os.system(cmd)

    #@unittest.skip("Temporarily skipped")
    def test_daemon_can_start(self):
        self.assertTrue(self.pidfile)
        self.assertEqual(self.testoutput.read(), 'inited')

    #@unittest.skip("Temporarily skipped")
    def test_daemon_can_stop(self):
        control_daemon('stop')
        time.sleep(0.1)
        self.assertFalse(self.is_pid_file_locked)
        self.assertEqual(self.testoutput.read(), 'inited')

    #@unittest.skip("Temporarily skipped")
    def test_daemon_can_finish(self):
        time.sleep(0.4)
        self.assertFalse(self.is_pid_file_locked)
        self.assertEqual(self.testoutput.read(), 'finished')

    #@unittest.skip("Temporarily skipped")
    def test_daemon_can_restart(self):
        self.assertTrue(self.is_pid_file_locked)
        pidfile = open(self.pidfile)
        pid1 = pidfile.read()
        pidfile.close()
        control_daemon('restart')
        time.sleep(0.1)
        self.assertTrue(self.is_pid_file_locked)
        pidfile = open(self.pidfile)
        pid2 = pidfile.read()
        pidfile.close()
        self.assertNotEqual(pid1, pid2)


# Used to override the sys.exit function in daemon.py.
def exit(value):
    pass


def create_logger(logfile='test_daemon.log'):
    log_format = ("%(asctime)s %(levelname)s %(name)s %(funcName)s "
                  "[line:%(lineno)d] %(message)s")
    logfile = os.path.abspath(os.path.join(LOG_PATH, logfile))
    logging.basicConfig(filename=logfile, format=log_format,
                        level=logging.DEBUG)


class TestDaemonCoverage(BaseTestDaemon):

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
        logfile = 'testing_daemon_redirect.log'
        create_logger(logfile=logfile)
        da = Daemon(self.pidfile, verbose=2)
        da.lock_pid_file()
        self.assertTrue(self.is_pid_file_locked)

        # Read the log file
        found = False

        with open(os.path.abspath(os.path.join(LOG_PATH, logfile)), 'r') as lf:
            for line in lf:
                if "Another process has a lock" in line:
                    found = True
                    break

        self.assertTrue(found)


if __name__ == '__main__':
    import logging

    if len(sys.argv) == 1:
        unittest.main()
    elif len(sys.argv) == 2:
        arg = sys.argv[1]

        if arg in ('start', 'stop', 'restart'):
            create_logger()
            pidfile = os.path.join(LOG_PATH, 'testing_daemon.pid')
            d = TDaemon(pidfile, verbose=2)
            getattr(d, arg)()
