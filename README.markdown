[![Build Status](https://travis-ci.org/serverdensity/python-daemon.svg?branch=master)](https://travis-ci.org/serverdensity/python-daemon)

Python daemonizer class
====================

This is a Python class that will daemonize your Python script so it can continue running in the background. It works on Unix, Linux and OS X, creates a PID file and has standard commands (start, stop, restart) + a foreground mode.

Based on [this original version from jejik.com](http://www.jejik.com/articles/2007/02/a_simple_unix_linux_daemon_in_python/).

Usage
---------------------

Define a class which inherits from `Daemon` and has a `run()` method (which is what will be called once the daemonization is completed.

	from daemon import Daemon
	
	class pantalaimon(Daemon):
		def run(self):
			# Do stuff
			
Create a new object of your class, specifying where you want your PID file to exist:

	pineMarten = pantalaimon('/path/to/pid.pid')
	pineMarten.start()

Actions
---------------------

* `start()` - starts the daemon (creates PID and daemonizes).
* `stop()` - stops the daemon (stops the child process and removes the PID).
* `restart()` - does `stop()` then `start()`.

Foreground
---------------------

This is useful for debugging because you can start the code without making it a daemon. The running script then depends on the open shell like any normal Python script.

To do this, just call the `run()` method directly.

	pineMarten.run()

Continuous execution
---------------------

The `run()` method will be executed just once so if you want the daemon to be doing stuff continuously you may wish to use the [sched][1] module to execute code repeatedly ([example][2]).


  [1]: http://docs.python.org/library/sched.html
  [2]: https://github.com/serverdensity/sd-agent/blob/master/agent.py#L339
