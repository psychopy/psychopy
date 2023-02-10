#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Functions and classes related to image handling"""

try:
    from PIL import Image
except ImportError:
    import Image

import numpy

from psychopy.tools.typetools import float_uint8


def array2image(a):
    """Takes an array and returns an image object (PIL)."""
    # fredrik lundh, october 1998
    #
    # fredrik@pythonware.com
    # http://www.pythonware.com
    #
    if a.dtype.kind in ['u', 'I', 'B']:
        mode = "L"
    elif a.dtype.kind in [numpy.float32, 'f']:
        mode = "F"
    else:
        raise ValueError("unsupported image mode")

    im = Image.frombytes(mode, (a.shape[1], a.shape[0]), a.tobytes())

    return im


def image2array(im):
    """Takes an image object (PIL) and returns a numpy array.
    """
    #     fredrik lundh, october 1998
    #
    #     fredrik@pythonware.com
    #     http://www.pythonware.com
    #
    if im.mode not in ("L", "F"):
        raise ValueError("can only convert single-layer images")

    imdata = im.tobytes()

    if im.mode == "L":
        a = numpy.frombuffer(imdata, numpy.uint8)
    else:
        a = numpy.frombuffer(imdata, numpy.float32)

    a.shape = im.size[1], im.size[0]
    return a


def makeImageAuto(inarray):
    """Combines float_uint8 and image2array operations ie. scales a numeric
    array from -1:1 to 0:255 and converts to PIL image format.
    """
    return image2array(float_uint8(inarray))
