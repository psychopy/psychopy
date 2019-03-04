#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Interface to `EGI Netstation <http://www.egi.com/>`_

This is currently a simple import of
`pynetstation <https://github.com/gaelen/python-egi/>`_
which is now simply called
`egi <https://pypi.python.org/pypi/egi>`_ on pypi.

`egi <https://github.com/gaelen/python-egi/>`_ is included in Standalone
distributions of PsychoPy but you can install it with::

    pip install egi


For examples on usage see the `example_simple` and `example_multi` files on
the `egi github repository <https://github.com/gaelen/python-egi/>`_

For an example see the demos menu of the PsychoPy Coder
For further documentation see the pynetstation website

"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from psychopy import logging
try:
    from .egi import *  # pyline: disable=W0614
except ImportError:
    msg = """Failed to import egi (pynetstation). If you're using your own
copy of python (not the Standalone distribution of PsychoPy)
then try installing pynetstation.

See:
    http://code.google.com/p/pynetstation/wiki/Installation

"""
    logging.error(msg)
