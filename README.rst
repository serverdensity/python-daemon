***********************
Python Daemonizer Class
***********************

.. image:: https://travis-ci.org/serverdensity/python-daemon.svg?branch=master
   :target: https://travis-ci.org/serverdensity/python-daemon
   :alt: Build Status

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
