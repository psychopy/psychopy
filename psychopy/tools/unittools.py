#!/usr/bin/env python

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

'''Functions and classes related to unit conversion'''

import numpy


def radians(degrees):
    """Convert degrees to radians

    >>> radians(180)
    3.1415926535897931
    >>> radians(45)
    0.78539816339744828
    """
    return degrees*0.017453292519943295 #0.017453292519943295 = pi/180

def degrees(radians):
    """Convert degrees to radians

    >>> from numpy import pi
    >>> degrees(pi/2)
    90.0
    >>> degrees(pi/2)
    90.0
    """
    return radians/0.017453292519943295 #0.017453292519943295 = pi/180
