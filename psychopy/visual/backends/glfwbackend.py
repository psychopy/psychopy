#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""A Backend class defines the core low-level functions required by a Window
class, such as the ability to create an OpenGL context and flip the window.
Users simply call visual.Window(..., winType='glfw') and the winType is then
used by backends.getBackend(winType) which will locate the appropriate class
and initialize an instance using the attributes of the Window.
"""

import psychopy.logging as logging

try:
    from psychopy_glfw import GLFWBackend
except (ModuleNotFoundError, ImportError):
    logging.warning(
        "GLFW window backend support is not installed. To get support, install "
        "the `psychopy-glfw` package and restart your session."
    )
    logging.flush()


if __name__ == "__main__":
    pass
