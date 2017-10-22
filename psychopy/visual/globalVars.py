#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This stores variables that are needed globally through the visual package.

It needs to be imported by anything that uses those variables as:

    from psychopy.visual import globalVars
    print(globalVars.currWindow)  # read it
    globalVars.currentWindow = newWin  # change it

Note that if you import using::

    from psychopy.visual.globalVars import currWindow

then if the variable changes your copy won't!
"""

from __future__ import absolute_import, division, print_function

currWindow = None
# for logging purposes, how many times have we resized an image:
nImageResizes = 0
