#!/usr/bin/python
import os
import sys
from distutils.sysconfig import get_python_lib

from setuptools import find_packages, setup

setup(
    name='tumblrSlurp',
    version=1,
    url='',
    author='Abram Wiebe',
    author_email='',
    description=('Tumblr access and user discovery program.'),
    license='BSD',
    packages=['pytumblr']
)