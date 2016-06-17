from __future__ import with_statement

try:
    from setuptools import setup
except ImportError:
    from distutils.core import setup

import inputs

inputs_classifiers = [
    "Programming Language :: Python :: 2.7",
    "Programming Language :: Python :: 3",
    "Intended Audience :: Developers",
    "License :: OSI Approved :: BSD License",
    "Topic :: Software Development :: Libraries",
    "Topic :: Utilities",
]

with open("README.rst", "r") as fp:
    inputs_long_description = fp.read()

setup(name="inputs",
      description = 'Easy to use, cross-platform, user input device support for Python, i.e. keyboards, mice, gamepads, etc.',
      version=inputs.__version__,
      author="Zeth",
      author_email="theology@gmail.com",
      py_modules=["inputs"],
      long_description=inputs_long_description,
      license="BSD",
      classifiers=inputs_classifiers,
      url = 'https://github.com/zeth/inputs', # use the URL to the github repo
)
