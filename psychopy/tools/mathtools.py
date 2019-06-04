#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Various math functions for working with vectors, matrices, and quaternions.

"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['normalize', 'lerp', 'slerp', 'multQuat', 'quatFromAxisAngle',
           'matrixFromQuat', 'scaleMatrix', 'rotationMatrix',
           'translationMatrix', 'concatenate', 'applyMatrix', 'invertQuat',
           'quatToAxisAngle', 'poseToMatrix']

import numpy as np


def normalize(v):
    """Normalize a vector or quaternion.

    v : tuple, list or ndarray of float
        Vector to normalize.

    Returns
    -------
    ndarray
        Normalized vector `v`.

    Notes
    -----
    * If the vector is degenerate (length is zero), a vector of all zeros is
      returned.

    """
    v = np.asarray(v)
    norm = np.linalg.norm(v)
    if norm == 1.0:  # already normalized
        return v
    elif norm != 0.0:
        v /= norm
    else:
        return np.zeros_like(v)

    return v


def lerp(v0, v1, t, out=None):
    """Linear interpolation (LERP) between two vectors/coordinates.

    Parameters
    ----------
    v0 : tuple, list or ndarray of float
        Initial vector. Can be 2D where each row is a point.
    v1 : tuple, list or ndarray of float
        Final vector. Must be the same shape as `v0`.
    t : float
        Interpolation weight factor [0, 1].
    out : ndarray, optional
        Optional output array. Must have the same `shape` and `dtype` as `v0`.

    Returns
    -------
    ndarray
        Vector  at `t` with same shape as `v0` and `v1`.

    Examples
    --------
    Find the coordinate of the midpoint between two vectors::

        u = [0., 0., 0.]
        v = [0., 0., 1.]
        midpoint = lerp(u, v, 0.5)  # 0.5 to interpolate half-way between points

    """
    v0 = np.asarray(v0)
    v1 = np.asarray(v1)
    assert v0.shape == v1.shape  # make sure the inputs have the same dims
    origShape = v0.shape
    v0, v1 = np.atleast_2d(v0, v1)

    if out is None:
        toReturn = np.zeros_like(v0)
    else:
        toReturn = out

    ncols = v0.shape[1]
    t0 = 1.0 - t
    toReturn[:, 0:ncols] = t0 * v0[:, 0:ncols] + t * v1[:, 0:ncols]

    if out is None:
        return np.reshape(toReturn, origShape)


def slerp(q0, q1, t):
    """Spherical linear interpolation (SLERP) between two quaternions.

    Interpolation occurs along the shortest arc between the initial and final
    quaternion.

    Parameters
    ----------
    q0 : tuple, list or ndarray of float
        Initial quaternion in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    q1 : tuple, list or ndarray of float
        Final quaternion in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    t : float
        Interpolation weight factor [0, 1].

    Returns
    -------
    ndarray
        Quaternion [x, y, z, w] at `t`.

    Notes
    -----
    * If the dot product between quaternions is >0.9995, linear interpolation is
      used instead of SLERP.

    """
    # Implementation based on code found here:
    #  https://en.wikipedia.org/wiki/Slerp
    #
    q0 = normalize(q0)
    q1 = normalize(q1)

    dot = np.dot(q0, q1)
    if dot < 0.0:
        q1 = -q1
        dot = -dot

    # small angle, use linear interpolation instead and return
    if dot > 0.9995:
        interp = q0 + t * (q1 - q0)
        return normalize(interp)

    theta0 = np.arccos(dot)
    theta = theta0 * t
    sinTheta = np.sin(theta)
    sinTheta0 = np.sin(theta0)
    s0 = np.cos(theta) - dot * sinTheta / sinTheta0
    s1 = sinTheta / sinTheta0

    return (q0 * s0) + (q1 * s1)


def quatToAxisAngle(q, degrees=False):
    """Convert a quaternion to `axis` and `angle` representation.

    This allows you to use quaternions to set the orientation of stimuli that
    have an `ori` property.

    Parameters
    ----------
    q : tuple, list or ndarray of float
        Quaternion in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    degrees : bool
        Indicate `angle` is to returned in degrees, otherwise `angle` will be
        returned in radians.

    Returns
    -------
    tuple
        Axis and angle of quaternion in form ([ax, ay, az], angle). If `degrees`
        is `True`, the angle returned is in degrees, radians if `False`.

    Examples
    --------
    Using a quaternion to rotate a stimulus each frame::

        # initial orientation, axis rotates in the Z direction
        qr = quatFromAxisAngle(0.0, [0., 0., -1.], degrees=True)
        # rotation per-frame, here it's 0.1 degrees per frame
        qf = quatFromAxisAngle(0.1, [0., 0., -1.], degrees=True)

        # ---- within main experiment loop ----
        # myStim is a GratingStim or anything with an 'ori' argument which
        # accepts angle in degrees
        qr = multQuat(qr, qf)  # cumulative rotation
        _, angle = quatToAxisAngle(qr)  # discard axis, only need angle
        myStim.ori = angle
        myStim.draw()

    """
    q = normalize(q)
    v = np.sqrt(np.sum(np.square(q[:3])))
    axis = (q[:3] / v) + 0.0
    angle = 2.0 * np.arctan2(v, q[3])

    return axis, np.degrees(angle) if degrees else angle


def quatFromAxisAngle(axis, angle, degrees=False):
    """Create a quaternion to represent a rotation about `axis` vector by
    `angle`.

    Parameters
    ----------
    axis : tuple, list or ndarray of float
        Axis of rotation [x, y, z].
    angle : float
        Rotation angle in radians (or degrees if `degrees` is `True`. Rotations
        are right-handed about the specified `axis`.
    degrees : bool
        Indicate `angle` is in degrees, otherwise `angle` will be treated as
        radians.

    Returns
    -------
    ndarray
        Quaternion [x, y, z, w].

    Examples
    --------
    Create a quaternion from specified `axis` and `angle`::

        axis = [0., 0., -1.]  # rotate about -Z axis
        angle = 90.0  # angle in degrees
        ori = quatFromAxisAngle(axis, angle, degrees=True)  # using degrees!

    """
    halfRad = np.radians(float(angle)) / 2.0 if degrees else float(angle) / 2.0
    q = np.zeros((4,))
    axis = normalize(axis)
    np.multiply(axis, np.sin(halfRad), out=q[:3])
    q[3] = np.cos(halfRad)

    return q + 0.0  # remove negative zeros


def multQuat(q0, q1, out=None):
    """Multiply quaternion `q0` and `q1`.

    The orientation of the returned quaternion is the combination of the input
    quaternions.

    Parameters
    ----------
    q0, q1 : ndarray, list, or tuple of float
        Quaternions to multiply in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    out : ndarray or None
        Alternative array to write values. Must be `shape` == (4,) and same
        `dtype` as the `dtype` argument.

    Returns
    -------
    ndarray
        Combined orientation of `q0` amd `q1`. Returns `None` if `out` is
        specified.

    Notes
    -----
    * Quaternions are normalized prior to multiplication.

    """
    q0 = normalize(q0)
    q1 = normalize(q1)

    if out is None:
        qr = np.zeros_like(q0)
    else:
        qr = out

    qr[:3] = np.cross(q0[:3], q1[:3]) + q0[:3] * q1[3] + q1[:3] * q0[3]
    qr[3] = q0[3] * q1[3] - q0[:3].dot(q1[:3])

    if out is None:
        return qr

    return qr


def invertQuat(q):
    """Get tht multiplicative inverse of a quaternion.

    This gives a quaternion which rotates in the opposite direction with equal
    magnitude. Multiplying a quaternion by its inverse returns an identity
    quaternion as both orientations cancel out.

    Parameters
    ----------
    q : ndarray, list, or tuple of float
        Quaternion to invert in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.

    Returns
    -------
    ndarray
        Inverse of quaternion `q`.

    Examples
    --------
    Show that multiplying a quaternion by its inverse returns an identity
    quaternion where [x=0, y=0, z=0, w=1]::

        angle = 90.0
        axis = [0., 0., -1.]
        q = quatFromAxisAngle(axis, angle, degrees=True)
        qinv = invertQuat(q)
        qr = multQuat(q, qinv)
        qi = np.array([0., 0., 0., 1.])  # identity quaternion
        print(np.allclose(qi, qr))   # True

    Notes
    -----
    * Quaternions are normalized prior to inverting.

    """
    qn = normalize(q)
    # conjugate the quaternion
    conj = np.zeros((4,))
    conj[:3] = -1.0 * qn[:3]
    conj[3] = qn[3]

    return conj / np.sqrt(np.sum(np.square(qn)))


def matrixFromQuat(q, out=None):
    """Create a rotation matrix from a quaternion.

    Parameters
    ----------
    q : tuple, list or ndarray of float
        Quaternion to convert in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    out : ndarray or None
        Alternative array to write values. Must be `shape` == (4,4,) and same
        `dtype` as the `dtype` argument.

    Returns
    -------
    ndarray or None
        4x4 rotation matrix in row-major order. Returns `None` if `out` is
        specified.

    Examples
    --------
    Convert a quaternion to a rotation matrix::

        point = [0., 1., 0., 1.]  # 4-vector form [x, y, z, 1.0]
        ori = [0., 0., 0., 1.]
        rotMat = matrixFromQuat(ori)
        # rotate 'point' using matrix multiplication
        newPoint = np.matmul(rotMat.T, point)  # returns [-1., 0., 0., 1.]

    Rotate all points in an array (each row is a coordinate)::

        points = np.asarray([[0., 0., 0., 1.],
                             [0., 1., 0., 1.],
                             [1., 1., 0., 1.]])
        newPoints = points.dot(rotMat)

    Notes
    -----
    * Quaternions are normalized prior to conversion.

    """
    # based off implementations from
    # https://github.com/glfw/glfw/blob/master/deps/linmath.h
    q = normalize(q)
    b, c, d, a = q[:]
    vsqr = np.square(q)

    if out is None:
        R = np.zeros((4, 4,), dtype=q.dtype)
    else:
        R = out

    R[0, 0] = vsqr[3] + vsqr[0] - vsqr[1] - vsqr[2]
    R[1, 0] = 2.0 * (b * c + a * d)
    R[2, 0] = 2.0 * (b * d - a * c)
    R[3, 0] = 0.0

    R[0, 1] = 2.0 * (b * c - a * d)
    R[1, 1] = vsqr[3] - vsqr[0] + vsqr[1] - vsqr[2]
    R[2, 1] = 2.0 * (c * d + a * b)
    R[3, 1] = 0.0

    R[0, 2] = 2.0 * (b * d + a * c)
    R[1, 2] = 2.0 * (c * d - a * b)
    R[2, 2] = vsqr[3] - vsqr[0] - vsqr[1] + vsqr[2]
    R[3, 2] = 0.0

    R[:3, 3] = 0.0
    R[3, 3] = 1.0

    R += 0.0  # remove negative zeros

    if out is None:
        return R


def scaleMatrix(s):
    """Create a scaling matrix.

    The resulting matrix is the same as a generated by a `glScale` call.

    Parameters
    ----------
    s : ndarray, tuple, or list of float
        Scaling factors [sx, sy, sz].

    Returns
    -------
    ndarray
        4x4 scaling matrix in row-major order.

    """
    # from glScale
    s = np.asarray(s)
    S = np.zeros((4, 4,), dtype=s.dtype)
    S[0, 0] = s[0]
    S[1, 1] = s[1]
    S[2, 2] = s[2]
    S[3, 3] = 1.0

    return S


def rotationMatrix(angle, axis):
    """Create a rotation matrix.

    The resulting matrix will rotate points about `axis` by `angle`. The
    resulting matrix is similar to that produced by a `glRotate` call.

    Parameters
    ----------
    angle : float
        Rotation angle in degrees.
    axis : ndarray, list, or tuple of float
        Axis vector components.

    Returns
    -------
    ndarray
        4x4 scaling matrix in row-major order.

    Notes
    -----
    * Vector `axis` is normalized before creating the matrix.

    """
    axis = normalize(axis)
    angle = np.radians(angle)
    c = np.cos(angle)
    s = np.sin(angle)

    xs, ys, zs = axis * s
    x2, y2, z2 = np.square(axis)
    x, y, z = axis
    cd = 1.0 - c

    R = np.zeros((4, 4,), dtype=axis.dtype)
    R[0, 0] = x2 * cd + c
    R[0, 1] = x * y * cd - zs
    R[0, 2] = x * z * cd + ys

    R[1, 0] = y * x * cd + zs
    R[1, 1] = y2 * cd + c
    R[1, 2] = y * z * cd - xs

    R[2, 0] = x * z * cd - ys
    R[2, 1] = y * z * cd + xs
    R[2, 2] = z2 * cd + c

    R[3, 3] = 1.0

    return R + 0.0  # remove negative zeros


def translationMatrix(t):
    """Create a translation matrix.

    The resulting matrix is the same as generated by a `glTranslate` call.

    Parameters
    ----------
    t : ndarray, tuple, or list of float
        Translation vector [tx, ty, tz].

    Returns
    -------
    ndarray
        4x4 translation matrix in row-major order.

    """
    t = np.asarray(t)
    T = np.identity(4, dtype=t.dtype)
    T[:3, 3] = t

    return T


def concatenate(*args, out=None):
    """Concatenate matrix transformations.

    Combine transformation matrices into a single matrix. This is similar to
    what occurs when building a matrix stack in OpenGL using `glRotate`,
    `glTranslate`, and `glScale` calls. Matrices are multiplied together from
    right-to-left, or the last argument to first. Note that changing the order
    of the input matrices changes the final result.

    Parameters
    ----------
    *args
        4x4 matrices to combine of type `ndarray`. Matrices are multiplied from
        right-to-left.
    out : ndarray
        Optional 4x4 output array. All computations will use the data type of
        this array.

    Returns
    -------
    ndarray
        Concatenation of input matrices as a 4x4 matrix in row-major order.
        `None` is returned if `out` was specified.

    Examples
    --------
    Create an SRT (scale, rotate, and translate) matrix to convert model-space
    coordinates to world-space::

        S = scaleMatrix([2.0, 2.0, 2.0])  # scale model 2x
        R = rotationMatrix(-90., [0., 0., -1])  # rotate -90 about -Z axis
        T = translationMatrix([0., 0., -5.])  # translate point 5 units away
        SRT = concatenate(S, R, T)

        # transform a point in model-space coordinates to world-space
        pointModel = np.array([0., 1., 0., 1.])
        pointWorld = np.matmul(SRT, pointModel.T)  # point in WCS

    Create a model-view matrix from a world-space pose represented by an
    orientation (quaternion) and position (vector). The resulting matrix will
    transform model-space coordinates to eye-space::

        # stimulus pose as quaternion and vector
        stimOri = quatFromAxisAngle([0., 0., -1.], -45.0)
        stimPos = [0., 1.5, -5.]

        # create model matrix
        R = matrixFromQuat(stimOri)
        T = translationMatrix(stimPos)
        M = concatenate(R, T)  # model matrix

        # create a view matrix, can also be represented as 'pos' and 'ori'
        eyePos = [0., 1.5, 0.]
        eyeFwd = [0., 0., -1.]
        eyeUp = [0., 1., 0.]
        V = lookAt(eyePos, eyeFwd, eyeUp)  # from viewtools

        # modelview matrix
        MV = concatenate(M, V)

    You can put the created matrix in the OpenGL matrix stack as shown below.
    Note that the matrix must have a 32-bit floating-point data type and needs
    to be loaded transposed.::

        GL.glMatrixMode(GL.GL_MODELVIEW)
        MV = np.asarray(MV, dtype='float32')  # must be 32-bit float!
        ptrMV = MV.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        GL.glLoadTransposeMatrixf(ptrMV)

    Furthermore, you can go from model-space to homogeneous clip-space by
    concatenating the projection, view, and model matrices::

        # compute projection matrix, functions here are from 'viewtools'
        screenWidth = 0.52
        screenAspect = w / h
        scrDistance = 0.55
        frustum = computeFrustum(screenWidth, screenAspect, scrDistance)
        P = perspectiveProjectionMatrix(*frustum)

        # multiply model-space points by MVP to convert them to clip-space
        MVP = concatenate(M, V, P)
        pointModel = np.array([0., 1., 0., 1.])
        pointClipSpace = np.matmul(MVP, pointModel.T)

    """
    if out is None:
        toReturn = np.identity(4)
        use_dtype = toReturn.dtype
    else:
        use_dtype = out.dtype
        out[:, :] = np.identity(4, dtype=use_dtype)
        toReturn = out

    for mat in args:
        np.matmul(np.asarray(mat, dtype=use_dtype), toReturn, out=toReturn)

    if out is None:
        return toReturn


def applyMatrix(m, points, out=None):
    """Apply a transformation matrix over a 2D array of points.

    Parameters
    ----------
    m : ndarray
        Transformation matrix.
    points : ndarray
        2D array of points/coordinates to transform, where each row is a single
        point and the number of columns should match the dimensions of the
        matrix.
    out : ndarray, optional
        Optional output array to write values. Must be same `shape` and `dtype`
        as `points`.

    Returns
    -------
    ndarray or None
        Transformed points. If `None` if `out` was specified.

    Examples
    --------
    Transform an array of points by some transformation matrix::

        S = scaleMatrix([5.0, 5.0, 5.0])  # scale 2x
        R = rotationMatrix(180., [0., 0., -1])  # rotate 180 degrees
        T = translationMatrix([0., 1.5, -3.])  # translate point up and away
        M = concatenate(S, R, T)  # create transform matrix

        # points to transform, must be 2D!
        points = np.array([[0., 1., 0., 1.], [-1., 0., 0., 1.]]) # [x, y, z, w]
        newPoints = applyMatrix(M, points)  # apply the transformation

    Extract the 3x3 rotation sub-matrix from a 4x4 matrix and apply it to
    points. Here the result in written to an already allocated array::

        points = np.array([[0., 1., 0.], [-1., 0., 0.]])  # [x, y, z]
        outPoints = np.zeros(points.shape)
        M = rotationMatrix(90., [1., 0., 0.])
        M3x3 = M[:3, :3]  # extract rotation groups from the 4x4 matrix
        # apply transformations, write to result to existing array
        applyMatrix(M3x3, points, out=outPoints)

    """
    m = np.asarray(m)
    points = np.asarray(points)
    assert points.ndim == 2

    if out is None:
        toReturn = np.zeros(points.shape, dtype=points.dtype)
    else:
        # make sure we have the same dtype as the input
        assert out.dtype == points.dtype and out.shape == points.shape
        toReturn = out

    np.dot(points, m.T, out=toReturn)
    # toReturn[:, :] = points.dot(m.T)

    if out is None:
        return toReturn


def poseToMatrix(pos, ori, out=None):
    """Convert a pose to a 4x4 transformation matrix.

    A pose is represented by a position coordinate `pos` and orientation
    quaternion `ori`.

    Parameters
    ----------
    pos : ndarray, tuple, or list of float
        Position vector [x, y, z].
    ori : tuple, list or ndarray of float
        Orientation quaternion in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    out : ndarray, optional
        Optional output array for 4x4 matrix. All computations will use the data
        type of this array.

    Returns
    -------
    ndarray
        4x4 transformation matrix. Returns `None` if `out` is specified.

    """
    if out is None:
        use_dtype = pos.dtype
        toReturn = np.zeros((4, 4,), dtype=use_dtype)
    else:
        use_dtype = out.dtype
        toReturn = out

    pos = np.asarray(pos, dtype=use_dtype)
    ori = np.asarray(ori, dtype=use_dtype)
    transMat = translationMatrix(pos)
    rotMat = matrixFromQuat(ori)

    np.matmul(rotMat, transMat, out=toReturn)

    if out is None:
        return toReturn

