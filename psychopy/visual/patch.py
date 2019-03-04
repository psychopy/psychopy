#!/usr/bin/env python
# -*- coding: utf-8 -*-

'''Deprecated (as of version 1.74.00):
please use the :class:`~psychopy.visual.GratingStim`
or the :class:`~psychopy.visual.ImageStim` classes.'''

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, print_function

from psychopy.visual.grating import GratingStim


class PatchStim(GratingStim):

    def __init__(self, *args, **kwargs):
        """
        Deprecated (as of version 1.74.00):
        please use the :class:`~psychopy.visual.GratingStim`
        or the :class:`~psychopy.visual.ImageStim` classes.

        The GratingStim has identical abilities to the PatchStim
        (but possibly different initial values)
        whereas the ImageStim is designed to be use for non-cyclic images
        (photographs, not gratings).
        """
        super(PatchStim, self).__init__(*args, **kwargs)
        self.setImage = self.setTex
