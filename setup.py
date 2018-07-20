"""Setup file for Inputs module."""

from __future__ import with_statement
import platform

import inputs


try:
    from setuptools import setup
except ImportError:
    SETUPTOOLS = False
    from distutils.core import setup
else:
    SETUPTOOLS = True

# Unit Tests require mock on Python 2
TESTS_REQUIRE = []
try:
    # pylint: disable=unused-import
    import unittest.mock
except ImportError:
    TESTS_REQUIRE.append('mock')

INSTALL_REQUIRES = []

MAC = True if platform.system() == 'Darwin' else False

if MAC:
    INSTALL_REQUIRES.append('pyobjc-framework-Quartz')

INPUTS_CLASSIFIERS = [
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Topic :: Software Development :: Libraries",
    "Topic :: Utilities",
    "Topic :: System :: Hardware :: Hardware Drivers",
    "Topic :: Software Development :: Embedded Systems",
    "Operating System :: POSIX :: Linux",
    "Operating System :: Microsoft :: Windows",
    "Operating System :: MacOS :: MacOS X",
]

with open("README.rst", "r") as fp:
    INPUTS_LONG_DESCRIPTION = fp.read()

SHORT_DESC = 'Cross-platform Python support for keyboards, mice and gamepads.'

KWARGS = {
    'name': 'inputs',
    'description': SHORT_DESC,
    'version': inputs.__version__,
    'author': 'Zeth',
    'author_email': 'theology@gmail.com',
    'py_modules': ['inputs'],
    'long_description': INPUTS_LONG_DESCRIPTION,
    'license': "BSD",
    'classifiers': INPUTS_CLASSIFIERS,
    'url': 'https://github.com/zeth/inputs',
}

if SETUPTOOLS:
    KWARGS['tests_require'] = TESTS_REQUIRE
    KWARGS['test_suite'] = 'tests'
    KWARGS['install_requires'] = INSTALL_REQUIRES


setup(**KWARGS)
