***********************
Python Daemonizer Class
***********************

.. comment::

   .. image:: http://img.shields.io/pypi/l/python-daemon.svg
      :target: https://pypi.python.org/pypi/python-daemon
      :alt: License

.. image:: https://travis-ci.com/cnobile2012/python-daemon.svg?branch=master
   :target: https://travis-ci.com/cnobile2012/python-daemon
   :alt: Build Status

.. image:: http://img.shields.io/coveralls/cnobile2012/python-daemon/master.svg?branch=master
   :target: https://coveralls.io/r/cnobile2012/python-daemon?branch=master
   :alt: Test Coverage

License: `Creative Commons <http://creativecommons.org/licenses/by-sa/3.0/>`_

Overview
========

This is a Python class that will daemonize your Python script so it can
continue running in the background. It works on Unix, Linux and OS X, creates
a PID file and has standard commands (start, stop, restart) plus a foreground
mode. This current version no longer supports Python 2.

This code is based on the `original version from jejik.com <http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/>`_.

Usage
=====

Define a class which inherits from **Daemon** and has a **run()** method
(which is what will be called once the daemonization is completed.

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

Actions
=======

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
