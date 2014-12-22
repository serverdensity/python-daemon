import os
import sys
import time
import unittest
from daemon import Daemon

class TDaemon(Daemon):
    def __init__(self, *args, **kwargs):
        super(TDaemon, self).__init__(*args, **kwargs)
        open('testing_daemon', 'w').write('inited')

    def run(self):
        time.sleep(0.3)
        open('testing_daemon', 'w').write('finished')

def control_daemon(action):
    os.system('{0} {1} {2}'.format(sys.executable, __file__, action)) 

class TestDaemon(unittest.TestCase):
    def setUp(self):
        control_daemon('stop')
        time.sleep(0.05)
        os.system('rm testing_daemon*')

    def test_daemon_can_start(self):
        control_daemon('start')
        time.sleep(0.1)
        assert os.path.exists('testing_daemon.pid')
        assert open('testing_daemon').read() == 'inited'

    def test_daemon_can_stop(self):
        control_daemon('start')
        time.sleep(0.1)
        control_daemon('stop')
        time.sleep(0.1)
        assert os.path.exists('testing_daemon.pid') is False
        assert open('testing_daemon').read() == 'inited'

    def test_daemon_can_finish(self):
        control_daemon('start')
        time.sleep(0.4)
        assert os.path.exists('testing_daemon.pid') is False
        assert open('testing_daemon').read() == 'finished'

    def test_daemon_can_restart(self):
        control_daemon('start')
        time.sleep(0.1)
        assert os.path.exists('testing_daemon.pid') 
        pid1 = open('testing_daemon.pid').read()
        control_daemon('restart')
        time.sleep(0.1)
        assert os.path.exists('testing_daemon.pid') 
        pid2 = open('testing_daemon.pid').read()
        assert pid1 != pid2

    def tearDown(self):
        control_daemon('stop')
        time.sleep(0.05)
        os.system('rm testing_daemon*')

if __name__ == '__main__':
    if len(sys.argv) == 1:
        unittest.main()
    elif len(sys.argv) == 2:
        arg = sys.argv[1]
        if arg in ['start', 'stop', 'restart']:
            d = TDaemon('testing_daemon.pid')
            getattr(d, arg)()
