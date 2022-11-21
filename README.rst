***********************
Python Daemonizer Class
***********************

.. image:: https://img.shields.io/badge/License-CC--3-blue.svg
   :target: https://creativecommons.org/licenses/by-sa/3.0
   :alt: License

.. image:: https://api.travis-ci.com/cnobile2012/python-daemon.svg?branch=master
   :target: https://app.travis-ci.com/cnobile2012/python-daemon
   :alt: Build Status

.. image:: http://img.shields.io/coveralls/cnobile2012/python-daemon/master.svg?branch=master
   :target: https://coveralls.io/github/cnobile2012/python-daemon?branch=master
   :alt: Test Coverage

License: `Creative Commons <http://creativecommons.org/licenses/by-sa/3.0/>`_

Overview
========

This is a Python class that will daemonize your Python code so it can continue
running in the background. It works on Unix and Linux systems. It creates a PID
file that is controlled by system file locks so the need to remove a stale pid
file is not necessary.

The **Daemon** class will write to a log file if you set one up. Any code that
uses the **Daemon** class can also write to the same log file making it easy to
have a combined log.

The **Daemon** class has standard start, stop, restart commands plus a
foreground mode. This current version no longer supports Python 2. This code
may still support OSX but since I don't have a machine that runs OSX I cannot
test it.

This code is based on the `original version from jejik.com <http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/>`_.

Usage
=====

Define a class which inherits from **Daemon** and has a **run()** method
which is what will be called once the daemonization is completed.

.. code-block:: python

   from daemonize import Daemon

   class MyDaemon(Daemon):

       def run(self, *args, **kwards):
           # Do stuff

Create a new object of your class, specifying where you want your PID file
to exist:

.. code-block:: python

   md = MyDaemon('/path/to/pid.pid')
   md.start()

There are a lot of arguments that can be used in the constructor of the
**Daemon** class.

Positional Arguments
--------------------

- pidfile: Manditory fullpath including file name of the pid file.

Keyword Arguments
-----------------

- stdin: The input data stream, defaults to `os.devnull`.
- stdout: The output data stream, defaults to `os.devnull`.
- stderr: The error data stream, defaults to `os.devnull`.
- base_dir: The absolute or relative path to the directory that will be used
  after the process is detached from the terminal, defaults to `.` (current
  working directory).
- umask: The mask used for any files created by the daemon, defaults to `0o22`.
- verbose: The default logging level. The values `1 = INFO`, `2 = DEBUG`, `3 =
  ERROR`, and any number (other than 1, 2, 3) `= WARNING`, defaults to `1`.
- use_gevent: Use `gevent` to handle the killing of the daemon, defaults to
  `False`.
- logger_name: The logger name used for logging, defaults to `''` (the root
  logger).

Run Actions
===========

1. **start()** -- Starts the daemon (creates PID and daemonizes).
2. **stop()** -- Stops the daemon (stops the child process and removes the PID).
3. **restart()** -- Does a **stop()** and then **start()**.

Foreground
==========

This is useful for debugging because you can start the code without making
it a daemon. The running script then depends on the open shell like any
normal Python script.

To do this, just call the **run()** method directly.

.. code-block:: python

   md = MyDaemon('/path/to/pid.pid')
   md.run()

Continuous Execution
====================

The **run()** method will be executed just once so if you want the daemon to
be doing stuff continuously you may wish to use the [1]_ sched module to
execute code repeatedly [2]_ example or just use a `while True`.

.. rubric:: Footnotes

.. [1] http://docs.python.org/library/sched.html
.. [2] https://github.com/serverdensity/sd-agent/blob/master/agent.py#L339
