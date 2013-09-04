#!/usr/bin/env python

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Functions and classes related to unit conversion'''

import numpy


def radians(degrees):
    """Convert degrees to radians

    >>> radians(180)
    3.1415926535897931
    >>> degrees(45)
    0.78539816339744828

    """
    return degrees*numpy.pi/180.0
