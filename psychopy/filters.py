#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""filters.py placeholder file for backwards compatibility; Dec 2015
"""
from psychopy import logging

logging.warning('Deprecated v1.84.00: instead of `from psychopy import '
                'filters`, now do `from psychopy.visual import filters`')

from psychopy.visual.filters import *  # pylint: disable=0401,W0614
