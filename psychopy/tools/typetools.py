#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Functions and classes related to variable type conversion
"""
import numpy


def float_uint8(inarray):
    """Converts arrays, lists, tuples and floats ranging -1:1
    into an array of Uint8s ranging 0:255

    >>> float_uint8(-1)
    0
    >>> float_uint8(0)
    128

    """
    retVal = numpy.around(255 * (0.5 + 0.5 * numpy.asarray(inarray)))
    return retVal.astype(numpy.uint8)


def float_uint16(inarray):
    """Converts arrays, lists, tuples and floats ranging -1:1
    into an array of Uint16s ranging 0:2^16

    >>> float_uint16(-1)
    0
    >>> float_uint16(0)
    32768

    """
    i16max = 2**16 - 1
    retVal = numpy.around(i16max * (1.0 + numpy.asarray(inarray)) / 2.0)
    return retVal.astype(numpy.uint16)


def uint8_float(inarray):
    """Converts arrays, lists, tuples and UINTs ranging 0:255
    into an array of floats ranging -1:1

    >>> uint8_float(0)
    -1.0
    >>> uint8_float(128)
    0.0

    """
    return numpy.asarray(inarray, 'f')/127.5 - 1
