#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for working with view projections for 2- and 3-D rendering.

"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import numpy as np
from collections import namedtuple

# convenient named tuple for storing frustum parameters
Frustum = namedtuple(
    'Frustum',
    ['left', 'right', 'bottom', 'top', 'nearVal', 'farVal'])


def computeFrustum(scrWidth,
                   scrAspect,
                   scrDist,
                   convergeOffset=0.0,
                   eyeOffset=0.0,
                   nearClip=0.01,
                   farClip=100.0):
    """Calculate frustum parameters. If an eye offset is provided, an asymmetric
    frustum is returned which can be used for stereoscopic rendering.

    Parameters
    ----------
    scrWidth : float
        The display's width in meters.
    scrAspect : float
        Aspect ratio of the display (width / height).
    scrDist : float
        Distance to the screen from the view in meters. Measured from the center
        of their eyes.
    convergeOffset : float
        Offset of the convergence plane from the screen. Objects falling on this
        plane will have zero disparity. For best results, the convergence plane
        should be set to the same distance as the screen (0.0 by default).
    eyeOffset : float
        Half the inter-ocular separation (i.e. the horizontal distance between
        the nose and center of the pupil) in meters. If eyeOffset is 0.0, a
        symmetric frustum is returned.
    nearClip : float
        Distance to the near clipping plane in meters from the viewer. Should be
        at least less than scrDist.
    farClip : float
        Distance to the far clipping plane from the viewer in meters. Must be
        >nearClip.

    Returns
    -------
    Frustum
        Namedtuple with frustum parameters. Can be directly passed to
        glFrustum (e.g. glFrustum(*f)).

    Notes
    -----
    The view point must be transformed for objects to appear correctly. Offsets
    in the X-direction must be applied +/- eyeOffset to account for inter-ocular
    separation. A transformation in the Z-direction must be applied to account
    for screen distance. These offsets MUST be applied to the MODELVIEW matrix,
    not the PROJECTION matrix! Doing so may break lighting calculations.

    """
    d = scrWidth * (convergeOffset + scrDist)
    ratio = nearClip / float((convergeOffset + scrDist))

    right = (d - eyeOffset) * ratio
    left = (d + eyeOffset) * -ratio
    top = (scrWidth / float(scrAspect)) * nearClip
    bottom = -top

    return Frustum(left, right, bottom, top, nearClip, farClip)


def generalizedPerspectiveProjection(posBottomLeft,
                                     posBottomRight,
                                     posTopLeft,
                                     eyePos,
                                     nearClip=0.01,
                                     farClip=100.0):
    """Generalized derivation of projection and view matrices based on the
    physical configuration of the display system.

    This implementation is based on Robert Kooima's 'Generalized Perspective
    Projection' (see http://csc.lsu.edu/~kooima/articles/genperspective/)
    method.

    Parameters
    ----------
    posBottomLeft : list of float or ndarray
        Bottom-left 3D coordinate of the screen in meters.
    posBottomRight : list of float or ndarray
        Bottom-right 3D coordinate of the screen in meters.
    posTopLeft : list of float or ndarray
        Top-left 3D coordinate of the screen in meters.
    eyePos : list of float or ndarray
        Coordinate of the eye in meters.
    nearClip : float
        Near clipping plane distance from viewer in meters.
    farClip : float
        Far clipping plane distance from viewer in meters.

    Returns
    -------
    tuple
        The 4x4 projection and view matrix.

    Notes
    -----
    The resulting projection frustums are off-axis relative to the center of the
    display. The returned matrices are row-major. Values are floats with 32-bits
    of precision stored as a contiguous (C-order) array.

    """
    # convert everything to numpy arrays
    posBottomLeft = np.asarray(posBottomLeft, np.float32)
    posBottomRight = np.asarray(posBottomRight, np.float32)
    posTopLeft = np.asarray(posTopLeft, np.float32)
    eyePos = np.asarray(eyePos, np.float32)

    # orthonormal basis of the screen plane
    vr = posBottomRight - posBottomLeft
    vr /= np.linalg.norm(vr)
    vu = posTopLeft - posBottomLeft
    vu /= np.linalg.norm(vu)
    vn = np.cross(vr, vu)
    vn /= np.linalg.norm(vn)

    # screen corner vectors
    va = posBottomLeft - eyePos
    vb = posBottomRight - eyePos
    vc = posTopLeft - eyePos

    dist = -np.dot(va, vn)
    nearOverDist = nearClip / dist
    left = float(np.dot(vr, va) * nearOverDist)
    right = float(np.dot(vr, vb) * nearOverDist)
    bottom = float(np.dot(vu, va) * nearOverDist)
    top = float(np.dot(vu, vc) * nearOverDist)

    # projection matrix to return
    projMat = perspectiveProjectionMatrix(
        left, right, bottom, top, nearClip, farClip)

    # view matrix to return, first compute the rotation component
    rotMat = np.zeros((4, 4), np.float32)
    rotMat[0, :3] = vr
    rotMat[1, :3] = vu
    rotMat[2, :3] = vn
    rotMat[3, 3] = 1.0

    transMat = np.zeros((4, 4), np.float32)
    np.fill_diagonal(transMat, 1.0)
    transMat[:3, 3] = -eyePos

    return projMat, np.matmul(rotMat, transMat)


def orthoProjectionMatrix(left, right, bottom, top, nearClip, farClip):
    """Compute an orthographic projection matrix with provided frustum
    parameters.

    Parameters
    ----------
    left : float
        Left clipping plane coordinate.
    right : float
        Right clipping plane coordinate.
    bottom : float
        Bottom clipping plane coordinate.
    top : float
        Top clipping plane coordinate.
    nearClip : float
        Near clipping plane distance from viewer.
    farClip : float
        Far clipping plane distance from viewer.

    Returns
    -------
    ndarray
        4x4 projection matrix

    Notes
    -----
    The returned matrix is row-major. Values are floats with 32-bits of
    precision stored as a contiguous (C-order) array.

    """
    projMat = np.zeros((4, 4), np.float32)
    projMat[0, 0] = 2.0 / (right - left)
    projMat[1, 1] = 2.0 / (top - bottom)
    projMat[2, 2] = -2.0 / (farClip - nearClip)
    projMat[0, 3] = (right + left) / (right - left)
    projMat[1, 3] = (top + bottom) / (top - bottom)
    projMat[2, 3] = (farClip + nearClip) / (farClip - nearClip)
    projMat[3, 3] = 1.0

    return projMat


def perspectiveProjectionMatrix(left, right, bottom, top, nearClip, farClip):
    """Compute an perspective projection matrix with provided frustum
    parameters. The frustum can be asymmetric.

    Parameters
    ----------
    left : float
        Left clipping plane coordinate.
    right : float
        Right clipping plane coordinate.
    bottom : float
        Bottom clipping plane coordinate.
    top : float
        Top clipping plane coordinate.
    nearClip : float
        Near clipping plane distance from viewer.
    farClip : float
        Far clipping plane distance from viewer.

    Returns
    -------
    ndarray
        4x4 projection matrix

    Notes
    -----
    The returned matrix is row-major. Values are floats with 32-bits of
    precision stored as a contiguous (C-order) array.

    """
    projMat = np.zeros((4, 4), np.float32)
    projMat[0, 0] = (2.0 * nearClip) / (right - left)
    projMat[1, 1] = (2.0 * nearClip) / (top - bottom)
    projMat[0, 2] = (right + left) / (right - left)
    projMat[1, 2] = (top + bottom) / (top - bottom)
    projMat[2, 2] = -(farClip + nearClip) / (farClip - nearClip)
    projMat[3, 2] = -1.0
    projMat[2, 3] = -(2.0 * farClip * nearClip) / (farClip - nearClip)

    return projMat


def lookAt(eyePos, centerPos, upVec):
    """Create a transformation matrix to orient towards some point. Based on the
    same algorithm as 'gluLookAt'. This does not generate a projection matrix,
    but rather the matrix to transform the observer's view in the scene.

    For more information see:
    https://www.khronos.org/registry/OpenGL-Refpages/gl2.1/xhtml/gluLookAt.xml

    Parameters
    ----------
    eyePos : list of float or ndarray
        Eye position in the scene.
    centerPos : list of float or ndarray
        Position of the object center in the scene.
    upVec : list of float or ndarray
        Vector defining the up vector.

    Returns
    -------
    ndarray
        4x4 view matrix

    Notes
    -----
    The returned matrix is row-major. Values are floats with 32-bits of
    precision stored as a contiguous (C-order) array.

    """
    eyePos = np.asarray(eyePos, np.float32)
    centerPos = np.asarray(centerPos, np.float32)
    upVec = np.asarray(upVec, np.float32)

    f = centerPos - eyePos
    f /= np.linalg.norm(f)
    upVec /= np.linalg.norm(upVec)

    s = np.cross(f, upVec)
    u = np.cross(s / np.linalg.norm(s), f)

    rotMat = np.zeros((4, 4), np.float32)
    rotMat[0, :3] = s
    rotMat[1, :3] = u
    rotMat[2, :3] = -f
    rotMat[3, 3] = 1.0

    transMat = np.zeros((4, 4), np.float32)
    np.fill_diagonal(transMat, 1.0)
    transMat[:3, 3] = -eyePos

    return np.matmul(rotMat, transMat)


def pointToNDC(wcsPos, viewMatrix, projectionMatrix):
    """Map the position of a point in world space to normalized device
    coordinates/space.

    Parameters
    ----------
    wcsPos : tuple, list or ndarray
        3x1 position vector(s) (xyz) in world space coordinates
    viewMatrix : ndarray
        4x4 view matrix
    projectionMatrix : ndarray
        4x4 projection matrix

    Returns
    -------
    ndarray
        3x1 vector of normalized device coordinates with type 'float32'

    Notes
    -----
    The point is not visible, falling outside of the viewing frustum, if the
    returned coordinates fall outside of -1 and 1 along any dimension.

    In the rare instance the point falls directly on the eye in world space
    where the frustum converges to a point (singularity), the divisor will be
    zero during perspective division. To avoid this, the divisor is 'bumped' to
    machine epsilon for the 'float32' type.

    This function assumes the display area is rectilinear. Any distortion or
    warping applied in normalized device or viewport space is not considered.

    Examples
    --------
    Determine if a point is visible::
        point = (0.0, 0.0, 10.0)  # behind the observer
        ndc = pointToNDC(point, win.viewMatrix, win.projectionMatrix)
        isVisible = not np.any((ndc > 1.0) | (ndc < -1.0))

    Convert NDC to viewport (or pixel) coordinates::
        scrRes = (1920, 1200)
        point = (0.0, 0.0, -5.0)  # forward -5.0 from eye
        x, y, z = pointToNDC(point, win.viewMatrix, win.projectionMatrix)
        pixelX = ((x + 1.0) / 2.0) * scrRes[0])
        pixelY = ((y + 1.0) / 2.0) * scrRes[1])
        # object at point will appear at (pixelX, pixelY)

    """
    # TODO - this would be more useful if this function accepted 3xN input too
    coord = np.asarray(wcsPos, dtype=np.float32)  # convert to array

    # forward transform from world to clipping space
    viewProjMatrix = np.zeros((4, 4), dtype=np.float32)
    np.matmul(projectionMatrix, viewMatrix, viewProjMatrix)  # c-order

    # convert to 4-vector with W=1.0
    wcsVec = np.zeros((4,), dtype=np.float32)
    wcsVec[:3] = coord
    wcsVec[3] = 1.0

    clipCoords = viewProjMatrix.dot(wcsVec)  # convert to clipping space

    # handle the singularity case when the point falls on the eye
    if np.isclose(clipCoords[3], 0.0):
        clipCoords[3] = np.finfo(np.float32).eps

    return clipCoords[:3] / clipCoords[3]  # xyz / w
