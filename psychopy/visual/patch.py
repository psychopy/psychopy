#!/usr/bin/env python

'''Deprecated (as of version 1.74.00):
please use the :class:`~psychopy.visual.GratingStim`
or the :class:`~psychopy.visual.ImageStim` classes.'''

# Part of the PsychoPy library
# Copyright (C) 2013 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

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
        GratingStim.__init__(self, *args, **kwargs)
        self.setImage = self.setTex
