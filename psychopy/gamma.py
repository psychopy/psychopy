#!/usr/bin/env python2

"""gamma.py placeholder file for backwards compatibility; Dec 2015
"""

from psychopy import logging

logging.warning('Deprecated v1.84.00: instead of `from psychopy import gamma`'
                ', now do `from psychopy.visual import gamma`')

from psychopy.visual.gamma import *  # pylint: disable=0401,W0614
