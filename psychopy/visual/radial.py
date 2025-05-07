#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Stimulus class for drawing radial stimuli.

These are optional components that can be obtained by installing the
`psychopy-visionscience` extension into the current environment.

"""

from psychopy.plugins import PluginStub

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+


class RadialStim(
    PluginStub,
    plugin="psychopy-visionscience",
    docsHome="https://psychopy.github.io/psychopy-visionscience",
    docsRef="/coder/RadialStim/"
):
    pass
