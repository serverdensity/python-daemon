# -*- coding: utf-8 -*-

__version__ = '0.1.2'

import os
import re
try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

with open(os.path.join(os.path.dirname(__file__), 'py_daemon', '__init__.py')) as v_file:
    package_version = re.compile(r".*__version__ = '(.*?)'", re.S).match(v_file.read()).group(1)


def read(filename):
    return open(os.path.join(os.path.dirname(__file__), filename)).read()

setup(
    name="py_daemon",
    version=package_version,
    author="Carlos Perelló Marín",
    license = "http://creativecommons.org/licenses/by-sa/3.0/",
    url="https://github.com/serverdensity/python-daemon",
    description="Python daemonizer for Unix, Linux and OS X",
    maintainer="Andrey Kulikov",
    maintainer_email="amdeich@gmail.com",
    packages=['py_daemon'],
    platforms=["any"],
    long_description=read('README.markdown'),
    classifiers=[
        "License :: OSI Approved :: Attribution Assurance License",
        'Intended Audience :: Developers',
        'Environment :: No Input/Output (Daemon)',
        'Development Status :: 4 - Beta',
        'Operating System :: Unix',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 2.4',
        'Programming Language :: Python :: 2.7',
        'Programming Language :: Python :: 3',
        'Topic :: Software Development :: Libraries'
    ],
)