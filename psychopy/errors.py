# -*- coding: utf-8 -*-
"""Errors used within Psychopy for testing and handling situations.
"""
# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

class TimeoutError(StandardError):
    '''Error to signify that waiting for something took too long.'''
