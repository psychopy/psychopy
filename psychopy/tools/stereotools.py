#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for stereoscopy.

"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import numpy as np
import math
from collections import namedtuple

Frustum = namedtuple(
    'Frustum',
    ['left', 'right', 'bottom', 'top', 'nearVal', 'farVal'])


def computeOffAxisFrustums(fov,
                           aspect,
                           scrDist,
                           convergeDist,
                           eyeOffset=0.031,
                           nearClip=0.01,
                           farClip=100.0):
    """Calculate frustum parameters for symmetric off-axis views.

    Parameters
    ----------
    fov : float
        Field of view of the display in degrees.
    aspect : float
        Aspect ratio of the display (width / height).
    scrDist : float
        Distance to the screen in meters.
    convergeDist : float
        Distance to the convergence plane in meters.
    eyeOffset : float
        Half the inter-ocular separation.
    nearClip : float
        Distance to the near clipping plane in meters.
    farClip : float
        Distance to the far clipping plane in meters.

    Returns
    -------
    tuple of Frustum
        A tuple which contains Frustum objects which stores the left and right
        frustums.

    """
    hfovx = math.tan(math.radians(fov) / 2.0)
    hfovy = hfovx / float(aspect)

    d1 = hfovx * (convergeDist + scrDist) + eyeOffset
    d2 = hfovx * (convergeDist + scrDist) - eyeOffset
    ratio = nearClip / float((nearClip + scrDist))

    # left view frustum
    leftL = -1.0 * d1 * ratio
    rightL = d2 * ratio
    topL = hfovy * nearClip
    bottomL = -topL

    leftFrustum = Frustum(leftL, rightL, bottomL, topL, nearClip, farClip)

    # right view frustum
    leftR = -1.0 * d2 * ratio
    rightR = d1 * ratio
    topR = hfovy * nearClip
    bottomR = -topR

    rightFrustum = Frustum(leftR, rightR, bottomR, topR, nearClip, farClip)

    # apply frustums as such, for example the left eye ...
    #
    # GL.glMatrixMode(GL.GL_PROJECTION)
    # GL.glLoadIdentity()
    # GL.glFrustum(*leftFrustum)
    #
    # translate the viewer in the scene
    # GL.glMatrixMode(GL.GL_MODELVIEW)
    # GL.glTranslate(iod / 2.0, 0, -scrDist)

    return leftFrustum, rightFrustum


def frustumToProjectionMatrix(frustum):
    """Generate a projection matrix with the provided frustum.

    Returns
    -------

    """
    mOut = np.zeros((4, 4), float)
    mOut[0, 0] = (2.0 * frustum.nearVal) / (frustum.right - frustum.left)
    mOut[1, 1] = (2.0 * frustum.nearVal) / (frustum.top - frustum.bottom)
    mOut[2, 0] = (frustum.right + frustum.left) / (frustum.right - frustum.left)
    mOut[2, 1] = (frustum.top + frustum.bottom) / (frustum.top - frustum.bottom)
    mOut[2, 2] = \
        (frustum.farVal + frustum.nearVal) / (frustum.farVal - frustum.nearVal)
    mOut[2, 3] = -1.0
    mOut[3, 2] = (2.0 * frustum.farVal * frustum.nearVal) / \
                 (frustum.farVal - frustum.nearVal)

    return mOut


if __name__ == "__main__":
    l, r = computeOffAxisFrustums(38.0, 1.0, 0.25, 0.0)
    print(frustumToProjectionMatrix(l))
