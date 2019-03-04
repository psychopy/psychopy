#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from .calibTools import *
"""# probably only need something like:
    DACrange, GammaCalculator, Monitor, Photometer,
    findPR650, gammaFun, gammaInvFun, getAllMonitors,
    getLumSeries, getLumSeriesPR650, getRGBspectra,
    makeDKL2RGB, makeLMS2RGB,
    monitorFolder, pr650code,
    wavelength_5nm, juddVosXYZ1976_5nm, cones_SmithPokorny
    )
"""

# create a test monitor if there isn't one already
if 'testMonitor' not in getAllMonitors():
    defMon = Monitor('testMonitor',
                     width=30,
                     distance=57,
                     gamma=1.0,
                     # can't always localize the notes easily;
                     # need app created first to import localization and
                     # use _translate( ) => issues
                     notes='default (not very useful) monitor')
    defMon.setSizePix([1024, 768])
    defMon.save()
