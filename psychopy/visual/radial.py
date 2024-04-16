#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Stimulus class for drawing radial stimuli.

These are optional components that can be obtained by installing the
`psychopy-visionscience` extension into the current environment.

"""

import psychopy.logging as logging

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+

try:
    from psychopy_visionscience import RadialStim
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for `RadialStim` is not available this session. Please install "
        "`psychopy-visionscience` and restart the session to enable support.")


class RadialStim:
    """
    `psychopy.visual.RadialStim` is now located within the `psychopy-visionscience` plugin. You
    can find the documentation for it `here <https://psychopy.github.io/psychopy-visionscience/coder/RadialStim>`_
    """


if __name__ == "__main__":
    pass



