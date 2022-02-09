#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Tools for working with view projections for 2- and 3-D rendering.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['Frustum',
           'visualAngle',
           'computeFrustum',
           'computeFrustumFOV',
           'projectFrustum',
           'projectFrustumToPlane',
           'generalizedPerspectiveProjection',
           'orthoProjectionMatrix',
           'perspectiveProjectionMatrix',
           'lookAt',
           'pointToNdc',
           'cursorToRay',
           'visible',
           'visibleBBox']

import numpy as np
from collections import namedtuple
import psychopy.tools.mathtools as mt

DEG_TO_RAD = np.pi / 360.0
VEC_FWD_AND_UP = np.array(((0., 0., -1.), (0., 1., 0.)), dtype=np.float32)


def visualAngle(size, distance, degrees=True, out=None, dtype=None):
    """Get the visual angle for an object of `size` at `distance`. Object is
    assumed to be fronto-parallel with the viewer.

    This function supports vector inputs. Values for `size` and `distance` can
    be arrays or single values. If both inputs are arrays, they must have the
    same size.

    Parameters
    ----------
    size : float or array_like
        Size of the object in meters.
    distance : float or array_like
        Distance to the object in meters.
    degrees : bool
        Return result in degrees, if `False` result will be in radians.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for arrays, can either be 'float32' or 'float64'. If `None` is
        specified, the data type is inferred by `out`. If `out` is not provided,
        the default is 'float64'.

    Returns
    -------
    float
        Visual angle.

    Examples
    --------
    Calculating the visual angle (vertical FOV) of a monitor screen::

        monDist = 0.5  # monitor distance, 50cm
        monHeight = 0.45  # monitor height, 45cm

        vertFOV = visualAngle(monHeight, monDist)

    Compute visual angle at multiple distances for objects with the same size::

        va = visualAngle(0.20, [1.0, 2.0, 3.0])  # returns
        # [11.42118627  5.72481045  3.81830487]

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    size, distance = np.atleast_1d(size, distance)

    if out is not None:
        out[:] = 2 * np.arctan(size / (2 * distance), dtype=dtype)
        if degrees:
            out[:] = np.degrees(out, dtype=dtype)
        toReturn = out
    else:
        toReturn = 2 * np.arctan(size / (2 * distance), dtype=dtype)
        if degrees:
            toReturn[:] = np.degrees(toReturn, dtype=dtype)

    return toReturn


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
                   farClip=100.0,
                   dtype=None):
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
        at least less than `scrDist`.
    farClip : float
        Distance to the far clipping plane from the viewer in meters. Must be
        >nearClip.
    dtype : dtype or str, optional
        Data type for arrays, can either be 'float32' or 'float64'. If `None` is
        specified, the data type is inferred by `out`. If `out` is not provided,
        the default is 'float64'.

    Returns
    -------
    ndarray
        Array of frustum parameters. Can be directly passed to
        glFrustum (e.g. glFrustum(*f)).

    Notes
    -----

    * The view point must be transformed for objects to appear correctly.
      Offsets in the X-direction must be applied +/- eyeOffset to account for
      inter-ocular separation. A transformation in the Z-direction must be
      applied to account for screen distance. These offsets MUST be applied to
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
        leftFrustum = viewtools.computeFrustum(
            scrWidth, scrAspect, scrDist, eyeOffset[0])
        rightFrustum = viewtools.computeFrustum(
            scrWidth, scrAspect, scrDist, eyeOffset[1])
        # make sure your view matrix accounts for the screen distance and eye
        # offsets!

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
    d = scrWidth / 2.0
    ratio = nearClip / float((convergeOffset + scrDist))

    right = (d - eyeOffset) * ratio
    left = (d + eyeOffset) * -ratio
    top = d / float(scrAspect) * ratio
    bottom = -top

    return np.asarray((left, right, bottom, top, nearClip, farClip),
                      dtype=dtype)


def computeFrustumFOV(scrFOV,
                      scrAspect,
                      scrDist,
                      convergeOffset=0.0,
                      eyeOffset=0.0,
                      nearClip=0.01,
                      farClip=100.0,
                      dtype=None):
    """Compute a frustum for a given field-of-view (FOV).

    Similar to `computeFrustum`, but computes a frustum based on FOV rather than
    screen dimensions.

    Parameters
    ----------
    scrFOV : float
        Vertical FOV in degrees (fovY).
    scrAspect : float
        Aspect between the horizontal and vertical FOV (ie. fovX / fovY).
    scrDist : float
        Distance to the screen from the view in meters. Measured from the center
        of the viewer's eye(s).
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
        at least less than `scrDist`. Never should be 0.
    farClip : float
        Distance to the far clipping plane from the viewer in meters. Must be
        >nearClip.
    dtype : dtype or str, optional
        Data type for arrays, can either be 'float32' or 'float64'. If `None` is
        specified, the data type is inferred by `out`. If `out` is not provided,
        the default is 'float64'.

    Examples
    --------
    Equivalent to `gluPerspective`::

        frustum =  computeFrustumFOV(45.0, 1.0, 0.5)
        projectionMatrix = perspectiveProjectionMatrix(*frustum)
    """
    d = np.tan(scrFOV * DEG_TO_RAD)
    ratio = nearClip / float((convergeOffset + scrDist))

    right = (d - eyeOffset) * ratio
    left = (d + eyeOffset) * -ratio
    top = d / float(scrAspect) * ratio
    bottom = -top

    return np.asarray((left, right, bottom, top, nearClip, farClip),
                      dtype=dtype)


def projectFrustum(frustum, dist, dtype=None):
    """Project a frustum on a fronto-parallel plane and get the width and height
    of the required drawing area.

    This function can be used to determine the size of the drawing area required
    for a given frustum on a screen. This is useful for cases where the observer
    is viewing the screen through a physical aperture that limits the FOV to a
    sub-region of the display. You must convert the size in meters to units of
    your screen and apply any offsets.

    Parameters
    ----------
    frustum : array_like
        Frustum parameters (left, right, bottom, top, near, far), you can
        exclude `far` since it is not used in this calculation. However, the
        function will still succeed if given.
    dist : float
        Distance to project points to in meters.
    dtype : dtype or str, optional
        Data type for arrays, can either be 'float32' or 'float64'. If `None` is
        specified, the data type is inferred by `out`. If `out` is not provided,
        the default is 'float64'.

    Returns
    -------
    ndarray
        Width and height (w, h) of the area intersected by the given frustum at
        `dist`.

    Examples
    --------
    Compute the viewport required to draw in the area where the frustum
    intersects the screen::

        # needed information
        scrWidthM = 0.52
        scrDistM = 0.72
        scrWidthPIX = 1920
        scrHeightPIX = 1080
        scrAspect = scrWidthPIX / float(scrHeightPIX)
        pixPerMeter = scrWidthPIX / scrWidthM

        # Compute a frustum for 20 degree vertical FOV at distance of the
        # screen.
        frustum = computeFrustumFOV(20., scrAspect, scrDistM)

        # get the dimensions of the frustum
        w, h = projectFrustum(frustum, scrDistM) * pixPerMeter

        # get the origin of the viewport, relative to center of screen.
        x = (scrWidthPIX - w) / 2.
        y = (scrHeightPIX - h) / 2.

        # if there is an eye offset ...
        # x = (scrWidthPIX - w + eyeOffsetM * pixPerMeter) / 2.

        # viewport rectangle
        rect = np.asarray((x, y, w, h), dtype=int)

    You can then set the viewport/scissor rectangle of the buffer to restrict
    drawing to `rect`.

    """
    dtype = np.float64 if dtype is None else np.dtype(dtype).type

    frustum = np.asarray(frustum, dtype=dtype)
    l, r, t, b = np.abs(frustum[:4] * dist / frustum[4], dtype=dtype)

    return np.array((l + r, t + b), dtype=dtype)


def projectFrustumToPlane(frustum, planeOrig, dtype=None):
    """Project a frustum on a fronto-parallel plane and get the coordinates of
    the corners in physical space.

    Parameters
    ----------
    frustum : array_like
        Frustum parameters (left, right, bottom, top, near, far), you can
        exclude `far` since it is not used in this calculation. However, the
        function will still succeed if given.
    planeOrig : float
        Distance of plane to project points on in meters.
    dtype : dtype or str, optional
        Data type for arrays, can either be 'float32' or 'float64'. If `None` is
        specified, the data type is inferred by `out`. If `out` is not provided,
        the default is 'float64'.

    Returns
    -------
    ndarray
        4x3 array of coordinates in the physical reference frame with origin
        at the eye.

    """
    dtype = np.float64 if dtype is None else np.dtype(dtype).type

    frustum = np.asarray(frustum, dtype=dtype)
    l, r, t, b = frustum[:4] * planeOrig / frustum[4]
    d = -planeOrig

    return np.array(((l, t, d), (l, b, d), (r, b, d), (r, t, d)), dtype=dtype)


def generalizedPerspectiveProjection(posBottomLeft,
                                     posBottomRight,
                                     posTopLeft,
                                     eyePos,
                                     nearClip=0.01,
                                     farClip=100.0,
                                     dtype=None):
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
    dtype : dtype or str, optional
        Data type for arrays, can either be 'float32' or 'float64'. If `None` is
        specified, the data type is inferred by `out`. If `out` is not provided,
        the default is 'float64'.

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
    # get data type of arrays
    dtype = np.float64 if dtype is None else np.dtype(dtype).type

    # convert everything to numpy arrays
    posBottomLeft = np.asarray(posBottomLeft, dtype=dtype)
    posBottomRight = np.asarray(posBottomRight, dtype=dtype)
    posTopLeft = np.asarray(posTopLeft, dtype=dtype)
    eyePos = np.asarray(eyePos, dtype=dtype)

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
    left = np.dot(vr, va) * nearOverDist
    right = np.dot(vr, vb) * nearOverDist
    bottom = np.dot(vu, va) * nearOverDist
    top = np.dot(vu, vc) * nearOverDist

    # projection matrix to return
    projMat = perspectiveProjectionMatrix(
        left, right, bottom, top, nearClip, farClip, dtype=dtype)

    # view matrix to return, first compute the rotation component
    rotMat = np.zeros((4, 4), dtype=dtype)
    rotMat[0, :3] = vr
    rotMat[1, :3] = vu
    rotMat[2, :3] = vn
    rotMat[3, 3] = 1.0

    transMat = np.identity(4, dtype=dtype)
    transMat[:3, 3] = -eyePos

    return projMat, np.matmul(rotMat, transMat)


def orthoProjectionMatrix(left, right, bottom, top, nearClip=0.01, farClip=100.,
                          out=None, dtype=None):
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
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for arrays, can either be 'float32' or 'float64'. If `None` is
        specified, the data type is inferred by `out`. If `out` is not provided,
        the default is 'float64'.

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
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    projMat = np.zeros((4, 4,), dtype=dtype) if out is None else out
    if out is not None:
        projMat.fill(0.0)

    u = dtype(2.0)
    projMat[0, 0] = u / (right - left)
    projMat[1, 1] = u / (top - bottom)
    projMat[2, 2] = -u / (farClip - nearClip)
    projMat[0, 3] = -((right + left) / (right - left))
    projMat[1, 3] = -((top + bottom) / (top - bottom))
    projMat[2, 3] = -((farClip + nearClip) / (farClip - nearClip))
    projMat[3, 3] = 1.0

    return projMat


def perspectiveProjectionMatrix(left, right, bottom, top, nearClip=0.01,
                                farClip=100., out=None, dtype=None):
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
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for arrays, can either be 'float32' or 'float64'. If `None` is
        specified, the data type is inferred by `out`. If `out` is not provided,
        the default is 'float64'.

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
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    projMat = np.zeros((4, 4,), dtype=dtype) if out is None else out
    if out is not None:
        projMat.fill(0.0)

    u = dtype(2.0)
    projMat[0, 0] = (u * nearClip) / (right - left)
    projMat[1, 1] = (u * nearClip) / (top - bottom)
    projMat[0, 2] = (right + left) / (right - left)
    projMat[1, 2] = (top + bottom) / (top - bottom)
    projMat[2, 2] = -(farClip + nearClip) / (farClip - nearClip)
    projMat[3, 2] = -1.0
    projMat[2, 3] = -(u * farClip * nearClip) / (farClip - nearClip)

    return projMat


def lookAt(eyePos, centerPos, upVec=(0.0, 1.0, 0.0), out=None, dtype=None):
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
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for arrays, can either be 'float32' or 'float64'. If `None` is
        specified, the data type is inferred by `out`. If `out` is not provided,
        the default is 'float64'.

    Returns
    -------
    ndarray
        4x4 view matrix

    Notes
    -----

    * The returned matrix is row-major. Values are floats with 32-bits of
      precision stored as a contiguous (C-order) array.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    toReturn = np.zeros((4, 4,), dtype=dtype) if out is None else out
    if out is not None:
        toReturn.fill(0.0)

    eyePos = np.asarray(eyePos, dtype=dtype)
    centerPos = np.asarray(centerPos, dtype=dtype)
    upVec = np.asarray(upVec, dtype=dtype)

    f = centerPos - eyePos
    f /= np.linalg.norm(f)
    upVec /= np.linalg.norm(upVec)

    s = np.cross(f, upVec)
    u = np.cross(s / np.linalg.norm(s), f)

    rotMat = np.zeros((4, 4), dtype=dtype)
    rotMat[0, :3] = s
    rotMat[1, :3] = u
    rotMat[2, :3] = -f
    rotMat[3, 3] = 1.0

    transMat = np.identity(4, dtype=dtype)
    transMat[:3, 3] = -eyePos

    return np.matmul(rotMat, transMat, out=toReturn)


def viewMatrix(pos, ori=(0., 0., 0., -1.), out=None, dtype=None):
    """Get a view matrix from a pose.

    A pose consists of a position coordinate [X, Y, Z, 1] and orientation
    quaternion [X, Y, Z, W]. Assumes that the identity pose has a forward vector
    pointing along the -Z axis and up vector along the +Y axis. The quaternion
    for `ori` must be normalized.

    Parameters
    ----------
    pos : ndarray, tuple, or list of float
        Position vector [x, y, z].
    ori : tuple, list or ndarray of float
        Orientation quaternion in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(dtype).type

    # convert if needed
    pos = np.asarray(pos, dtype=dtype)
    ori = np.asarray(ori, dtype=dtype)
    axes = np.asarray(VEC_FWD_AND_UP, dtype=dtype)  # convert to type
    toReturn = np.zeros((4, 4), dtype=dtype) if out is None else out

    # generate rotation matrix
    b, c, d, a = ori[:]
    vsqr = np.square(ori)
    R = np.zeros((3, 3,), dtype=dtype)
    u = dtype(2.0)
    R[0, 0] = vsqr[3] + vsqr[0] - vsqr[1] - vsqr[2]
    R[1, 0] = u * (b * c + a * d)
    R[2, 0] = u * (b * d - a * c)
    R[0, 1] = u * (b * c - a * d)
    R[1, 1] = vsqr[3] - vsqr[0] + vsqr[1] - vsqr[2]
    R[2, 1] = u * (c * d + a * b)
    R[0, 2] = u * (b * d + a * c)
    R[1, 2] = u * (c * d - a * b)
    R[2, 2] = vsqr[3] - vsqr[0] - vsqr[1] + vsqr[2]

    # transform the axes
    transformedAxes = axes.dot(R.T)
    fwdVec = transformedAxes[0, :] + pos
    upVec = transformedAxes[1, :]

    toReturn[:, :] = lookAt(pos, fwdVec, upVec, dtype=dtype)

    return toReturn


def pointToNdc(wcsPos, viewMatrix, projectionMatrix, out=None, dtype=None):
    """Map the position of a point in world space to normalized device
    coordinates/space.

    Parameters
    ----------
    wcsPos : tuple, list or ndarray
        Nx3 position vector(s) (xyz) in world space coordinates.
    viewMatrix : ndarray
        4x4 view matrix.
    projectionMatrix : ndarray
        4x4 projection matrix.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for arrays, can either be 'float32' or 'float64'. If `None` is
        specified, the data type is inferred by `out`. If `out` is not provided,
        the default is 'float64'.

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
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    wcsPos = np.asarray(wcsPos, dtype=dtype)  # convert to array
    toReturn = np.zeros_like(wcsPos, dtype=dtype) if out is None else out

    # forward transform from world to clipping space
    viewProjMatrix = np.zeros((4, 4,), dtype=dtype)
    np.matmul(projectionMatrix, viewMatrix, viewProjMatrix)

    pnts, rtn = np.atleast_2d(wcsPos, toReturn)

    # convert to 4-vector with W=1.0
    wcsVec = np.zeros((pnts.shape[0], 4), dtype=dtype)
    wcsVec[:, :3] = wcsPos
    wcsVec[:, 3] = 1.0

    # convert to homogeneous clip space
    wcsVec = mt.applyMatrix(viewProjMatrix, wcsVec, dtype=dtype)

    # handle the singularity where perspective division will fail
    wcsVec[np.abs(wcsVec[:, 3]) <= np.finfo(dtype).eps] = np.finfo(dtype).eps
    rtn[:, :] = wcsVec[:, :3] / wcsVec[:, 3:]  # xyz / w

    return toReturn


def cursorToRay(cursorX, cursorY, winSize, viewport, projectionMatrix,
                normalize=True, out=None, dtype=None):
    """Convert a 2D mouse coordinate to a 3D ray.

    Takes a 2D window/mouse coordinate and transforms it to a 3D direction
    vector from the viewpoint in eye space (vector origin is [0, 0, 0]). The
    center of the screen projects to vector [0, 0, -1].

    Parameters
    ----------
    cursorX, cursorY :  float or int
        Window coordinates. These need to be scaled if you are using a
        framebuffer that does not have 1:1 pixel mapping (i.e. retina display).
    winSize : array_like
        Size of the window client area [w, h].
    viewport : array_like
        Viewport rectangle [x, y, w, h] being used.
    projectionMatrix : ndarray
        4x4 projection matrix being used.
    normalize : bool
        Normalize the resulting vector.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for arrays, can either be 'float32' or 'float64'. If `None` is
        specified, the data type is inferred by `out`. If `out` is not provided,
        the default is 'float64'.

    Returns
    -------
    ndarray
        Direction vector (x, y, z).

    Examples
    --------
    Place a 3D stim at the mouse location 5.0 scene units (meters) away::

        # define camera
        camera = RigidBodyPose((-3.0, 5.0, 3.5))
        camera.alignTo((0, 0, 0))

        # in the render loop

        dist = 5.0
        mouseRay = vt.cursorToRay(x, y, win.size, win.viewport, win.projectionMatrix)
        mouseRay *= dist  # scale the vector

        # set the sphere position by transforming vector to world space
        sphere.thePose.pos = camera.transform(mouseRay)

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    toReturn = np.zeros((3,), dtype=dtype) if out is None else out

    projectionMatrix = np.asarray(projectionMatrix, dtype=dtype)

    # compute the inverse model/view and projection matrix
    invPM = np.linalg.inv(projectionMatrix)

    # transform psychopy mouse coordinates to viewport coordinates
    cursorX = cursorX + (winSize[0] / 2.0)
    cursorY = cursorY + (winSize[1] / 2.0)

    # get the NDC coordinates of the
    projX = 2. * (cursorX - viewport[0]) / viewport[2] - 1.0
    projY = 2. * (cursorY - viewport[1]) / viewport[3] - 1.0

    vecNear = np.array((projX, projY, 0.0, 1.0), dtype=dtype)
    vecFar = np.array((projX, projY, 1.0, 1.0), dtype=dtype)

    vecNear[:] = vecNear.dot(invPM.T)
    vecFar[:] = vecFar.dot(invPM.T)

    vecNear /= vecNear[3]
    vecFar /= vecFar[3]

    # direction vector
    toReturn[:] = (vecFar - vecNear)[:3]

    if normalize:
        mt.normalize(toReturn, out=toReturn)

    return toReturn


def visibleBBox(extents, mvp, dtype=None):
    """Check if a bounding box is visible.

    This function checks if a bonding box intersects a frustum defined by the
    current projection matrix, after being transformed by the model-view matrix.

    Parameters
    ----------
    extents : array_like
        Bounding box minimum and maximum extents as a 2x3 array. The first row
        if the minimum extents along each axis, and the second row the maximum
        extents (eg. [[minX, minY, minZ], [maxX, maxY, maxZ]]).
    mvp : array_like
        4x4 MVP matrix.
    dtype : dtype or str, optional
        Data type for arrays, can either be 'float32' or 'float64'. If `None` is
        specified, the data type is inferred by `out`. If `out` is not provided,
        the default is 'float64'.

    Returns
    -------
    ndarray or bool
        Visibility test results.

    """
    dtype = np.float64 if dtype is None else np.dtype(dtype).type

    # convert input if needed
    extents = np.asarray(extents, dtype=dtype)
    if not extents.shape == (2, 3):
        raise ValueError("Invalid array dimensions for `extents`.")

    # ensure matrix is array
    mvp = np.asarray(mvp, dtype=dtype)

    # convert BBox to corners
    corners = mt.computeBBoxCorners(extents, dtype=dtype)

    # apply the matrix
    corners = corners.dot(mvp.T)
    # break up into components
    x, y, z = corners[:, 0], corners[:, 1], corners[:, 2]
    wpos, wneg = corners[:, 3], -corners[:, 3]

    # test if box falls all to one side of the frustum
    if np.logical_xor(np.all(x <= wneg), np.all(x >= wpos)):  # x-axis
        return False
    elif np.logical_xor(np.all(y <= wneg), np.all(y >= wpos)):  # y-axis
        return False
    elif np.logical_xor(np.all(z <= wneg), np.all(z >= wpos)):  # z-axis
        return False
    else:
        return True


def visible(points, mvp, mode='discrete', dtype=None):
    """Test if points are visible.

    This function is useful for visibility culling, where objects are only drawn
    if a portion of them are visible. This test can avoid costly drawing calls
    and OpenGL state changes if the object is not visible.

    Parameters
    ----------
    points : array_like
        Point(s) or bounding box to test. Input array must be Nx3 or Nx4, where
        each row is a point. It is recommended that the input be Nx4 since the
        `w` component will be appended if the input is Nx3 which adds overhead.
    mvp : array_like
        4x4 MVP matrix.
    mode : str
        Test mode. If `'discrete'`, rows of `points` are treated as individual
        points. This function will return an array of boolean values with length
        equal to the number of rows in `points`, where the value at each index
        corresponds to the visibility test results for points at the matching
        row index of `points`. If `'group'` a single boolean value is returned,
        which is `False` if all points fall to one side of the frustum.
    dtype : dtype or str, optional
        Data type for arrays, can either be 'float32' or 'float64'. If `None` is
        specified, the data type is inferred by `out`. If `out` is not provided,
        the default is 'float64'.

    Returns
    -------
    bool or ndarray
        Test results. The type returned depends on `mode`.

    Examples
    --------
    Visibility culling, only a draw line connecting two points if visible::

        linePoints = [[-1.0, -1.0, -1.0, 1.0],
                      [ 1.0,  1.0,  1.0, 1.0]]

        mvp = np.matmul(win.projectionMatrix, win.viewMatrix)
        if visible(linePoints, mvp, mode='group'):
            # drawing commands here ...

    """
    dtype = np.float64 if dtype is None else np.dtype(dtype).type

    # convert input if needed
    points = np.asarray(points, dtype=dtype)
    # keep track of dimension, return only a single value if ndim==1
    ndim = points.ndim

    # ensure matrix is array
    mvp = np.asarray(mvp, dtype=dtype)

    # convert to 2d view
    points = np.atleast_2d(np.asarray(points, dtype=dtype))
    if points.shape[1] == 3:  # make sure we are using Nx4
        temp = np.zeros((points.shape[0], 4), dtype=dtype)
        temp[:, :3] = points
        temp[:, 3] = 1.0
        points = temp

    # apply the matrix
    points = points.dot(mvp.T)
    # break up into components
    x, y, z = points[:, 0], points[:, 1], points[:, 2]
    wpos, wneg = points[:, 3], -points[:, 3]

    # test using the appropriate mode
    if mode == 'discrete':
        toReturn = np.logical_and.reduce(
            (x > wneg, x < wpos, y > wneg, y < wpos, z > wneg, z < wpos))
        return toReturn[0] if ndim == 1 else toReturn
    elif mode == 'group':
        # Check conditions for each axis. If all points fall to one side or
        # another, the bounding box is not visible. If all points fall outside
        # of both sides of the frustum along the same axis, that means the box
        # passes through the frustum or the viewer is inside the bounding box
        # and therefore is visible. We do an XOR to capture conditions where all
        # points fall all to one side only. Lastly, if any point is in the
        # bounding box, it will indicate that it's visible.
        #
        # mdc - This has been vectorized to be super fast, however maybe someone
        # smarter than me can figure out something better.
        #
        if np.logical_xor(np.all(x <= wneg), np.all(x >= wpos)):  # x-axis
            return False
        elif np.logical_xor(np.all(y <= wneg), np.all(y >= wpos)):  # y-axis
            return False
        elif np.logical_xor(np.all(z <= wneg), np.all(z >= wpos)):  # z-axis
            return False
        else:
            return True
    else:
        raise ValueError(
            "Invalid `mode` specified, should be either 'discrete' or 'group'.")
