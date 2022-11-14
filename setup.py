# -*- coding: utf-8 -*-
import os
import re
from setuptools import setup

def version():
    regex = r'^(?m){}[\s]*=[\s]*(?P<ver>\d*)$'

    with open(os.path.join(os.path.dirname(__file__), 'include.mk')) as f:
        ver = f.read()

    major = re.search(regex.format('MAJORVERSION'), ver).group('ver')
    minor = re.search(regex.format('MINORVERSION'), ver).group('ver')
    patch = re.search(regex.format('PATCHLEVEL'), ver).group('ver')
    return "{}.{}.{}".format(major, minor, patch)

with open(os.path.join(os.path.dirname(__file__), 'README.rst')) as readme:
    README = readme.read()

setup(
    name="python-daemon",
    version=version(),
    packages=['daemonize'],
    license="http://creativecommons.org/licenses/by-sa/3.0/",
    url="https://github.com/cnobile2012/python-daemon",
    author="Carl J. Nobile",
    author_email='carl.nobile@gmail.com',
    description="Python daemonizer for Unix and Linux",
    long_description=README,
    classifiers=[
        'License :: OSI Approved :: Creative Commons License',
        'Intended Audience :: Developers',
        'Environment :: No Input/Output (Daemon)',
        'Development Status :: Version 1.0.0',
        'Operating System :: Unix',
        'Operating System :: POSIX :: Linux',
        'Operating System :: MacOS :: MacOS X',
        'Programming Language :: Python :: 3',
    ],
)
