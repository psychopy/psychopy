#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for working with view projections for 2- and 3-D rendering.

"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['Frustum', 'computeFrustum', 'generalizedPerspectiveProjection',
           'orthoProjectionMatrix', 'perspectiveProjectionMatrix', 'lookAt',
           'pointToNdc']

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

    * The view point must be transformed for objects to appear correctly.
      Offsets in the X-direction must be applied +/- eyeOffset to account for
      inter-ocular separation. A transformation in the Z-direction must be
      applied to accountfor screen distance. These offsets MUST be applied to
      the GL_MODELVIEW matrix, not the GL_PROJECTION matrix! Doing so may break
      lighting calculations.

    Examples
    --------

    Creating a frustum and setting a window's projection matrix::

        scrWidth = 0.5  # screen width in meters
        scrAspect = win.size[0] / win.size[1]
        scrDist = win.scrDistCM * 100.0  # monitor setting, can be anything
        frustum = viewtools.computeFrustum(scrWidth, scrAspect, scrDist)

    Accessing frustum parameters::

        left, right, bottom, top, nearVal, farVal = frustum
        # ... or ...
        left = frustum.left

    Off-axis frustums for stereo rendering::

        # compute view matrix for each eye, these value usually don't change
        eyeOffset = (-0.035, 0.035)  # +/- IOD / 2.0
        scrDist = 0.50  # 50cm
        scrWidth = 0.53  # 53cm
        scrAspect = 1.778
        leftFrustum = viewtools.computeFrustum(scrWidth, scrAspect, scrDist, eyeOffset[0])
        rightFrustum = viewtools.computeFrustum(scrWidth, scrAspect, scrDist, eyeOffset[1])
        # make sure your view matrix accounts for the screen distance and eye offsets!

    Using computed view frustums with a window::

        win.projectionMatrix = viewtools.perspectiveProjectionMatrix(*frustum)
        # generate a view matrix looking ahead with correct viewing distance,
        # origin is at the center of the screen. Assumes eye is centered with
        # the screen.
        eyePos = [0.0, 0.0, scrDist]
        screenPos = [0.0, 0.0, 0.0]  # look at screen center
        eyeUp = [0.0, 1.0, 0.0]
        win.viewMatrix = viewtools.lookAt(eyePos, screenPos, eyeUp)
        win.applyViewTransform()  # call before drawing

    """
    # mdc - uses display size instead of the horizontal FOV gluPerspective needs
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
    Projection' method [1]_.

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

    See Also
    --------
    computeFrustum : Compute frustum parameters.

    Notes
    -----
    * The resulting projection frustums are off-axis relative to the center of
      the display.

    * The returned matrices are row-major. Values are floats with 32-bits
      of precision stored as a contiguous (C-order) array.

    References
    ----------
    .. [1] Kooima, R. (2009). Generalized perspective projection. J. Sch.
    Electron. Eng. Comput. Sci.

    Examples
    --------
    Computing a projection and view matrices for a window::

        projMatrix, viewMatrix = viewtools.generalizedPerspectiveProjection(
            posBottomLeft, posBottomRight, posTopLeft, eyePos)
        # set the window matrices
        win.projectionMatrix = projMatrix
        win.viewMatrix = viewMatrix
        # before rendering
        win.applyEyeTransform()

    Stereo-pair rendering example from Kooima (2009)::

        # configuration of screen and eyes
        posBottomLeft = [-1.5, -0.75, -18.0]
        posBottomRight = [1.5, -0.75, -18.0]
        posTopLeft = [-1.5, 0.75, -18.0]
        posLeftEye = [-1.25, 0.0, 0.0]
        posRightEye = [1.25, 0.0, 0.0]
        # create projection and view matrices
        leftProjMatrix, leftViewMatrix = generalizedPerspectiveProjection(
            posBottomLeft, posBottomRight, posTopLeft, posLeftEye)
        rightProjMatrix, rightViewMatrix = generalizedPerspectiveProjection(
            posBottomLeft, posBottomRight, posTopLeft, posRightEye)

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

    transMat = np.identity(4, np.float32)
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

    See Also
    --------
    perspectiveProjectionMatrix : Compute a perspective projection matrix.

    Notes
    -----

    * The returned matrix is row-major. Values are floats with 32-bits of
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

    See Also
    --------
    orthoProjectionMatrix : Compute a orthographic projection matrix.

    Notes
    -----

    * The returned matrix is row-major. Values are floats with 32-bits of
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


def lookAt(eyePos, centerPos, upVec=(0.0, 1.0, 0.0)):
    """Create a transformation matrix to orient a view towards some point. Based
    on the same algorithm as 'gluLookAt'. This does not generate a projection
    matrix, but rather the matrix to transform the observer's view in the scene.

    For more information see:
    https://www.khronos.org/registry/OpenGL-Refpages/gl2.1/xhtml/gluLookAt.xml

    Parameters
    ----------
    eyePos : list of float or ndarray
        Eye position in the scene.
    centerPos : list of float or ndarray
        Position of the object center in the scene.
    upVec : list of float or ndarray, optional
        Vector defining the up vector. Default is +Y is up.

    Returns
    -------
    ndarray
        4x4 view matrix

    Notes
    -----

    * The returned matrix is row-major. Values are floats with 32-bits of
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

    transMat = np.identity(4, np.float32)
    transMat[:3, 3] = -eyePos

    return np.matmul(rotMat, transMat)


def pointToNdc(wcsPos, viewMatrix, projectionMatrix):
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

    * The point is not visible, falling outside of the viewing frustum, if the
      returned coordinates fall outside of -1 and 1 along any dimension.

    * In the rare instance the point falls directly on the eye in world
      space where the frustum converges to a point (singularity), the divisor
      will be zero during perspective division. To avoid this, the divisor is
      'bumped' to 1e-5.

    * This function assumes the display area is rectilinear. Any distortion or
      warping applied in normalized device or viewport space is not considered.

    Examples
    --------
    Determine if a point is visible::

        point = (0.0, 0.0, 10.0)  # behind the observer
        ndc = pointToNdc(point, win.viewMatrix, win.projectionMatrix)
        isVisible = not np.any((ndc > 1.0) | (ndc < -1.0))

    Convert NDC to viewport (or pixel) coordinates::

        scrRes = (1920, 1200)
        point = (0.0, 0.0, -5.0)  # forward -5.0 from eye
        x, y, z = pointToNdc(point, win.viewMatrix, win.projectionMatrix)
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

    # handle the singularity where perspective division will fail
    if clipCoords[3] < 1e-05:
        clipCoords[3] = 1e-05

    return clipCoords[:3] / clipCoords[3]  # xyz / w
