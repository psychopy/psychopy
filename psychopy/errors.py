# -*- coding: utf-8 -*-
"""Errors used within Psychopy for testing and handling situations.
"""
# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

class TimeoutError(StandardError):
    '''Error to signify that waiting for something took too long.'''

class ExperimentException(Exception):
    '''Exception thrown when standard experiment path fails.'''
    pass

class DataImportError(Exception):
    '''Error when working with data files'''
    pass

class DataFormatError(Exception):
    '''Error raised when file does not seem to be in expected format.'''
    pass
