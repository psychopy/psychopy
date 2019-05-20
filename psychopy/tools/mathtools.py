#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Various math functions for working with vectors, matrices, and quaternions.

"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['normalize', 'lerp', 'slerp', 'quatFromAxisAngle', 'matrixFromQuat',
           'scaleMatrix', 'rotationMatrix']

import numpy as np


def normalize(v, dtype='float32'):
    """Normalize a vector or quaternion.

    v : tuple, list or ndarray of float
        Vector to normalize.
    dtype : str or obj
        Data type to use for all computations (eg. 'float32', 'float64', float,
        etc.)

    Returns
    -------
    ndarray
        Normalized vector `v`.

    Notes
    -----
    * If the vector is degenerate (length is zero), a vector of all zeros is
      returned.

    """
    v = np.asarray(v, dtype=dtype)
    norm = np.linalg.norm(v)
    if norm == 1.0:  # already normalized
        return v
    elif norm != 0.0:
        v /= norm
    else:
        return np.zeros(v.shape, dtype=dtype)

    return v


def lerp(v0, v1, t, dtype='float32'):
    """Linear interpolation (LERP) between two vectors.

    Parameters
    ----------
    v0 : tuple, list or ndarray of float
        Initial vector in form [x, y, z].
    v1 : tuple, list or ndarray of float
        Final vector in form [x, y, z].
    t : float
        Interpolation factor [0, 1].
    dtype : str or obj
        Data type to use for all computations (eg. 'float32', 'float64', float,
        etc.)

    Returns
    -------
    ndarray
        Vector [x, y, z] at `t`.

    Examples
    --------
    Find the coordinate of the midpoint between two vectors::

        u = [0., 0., 0.]
        v = [0., 0., 1.]
        midpoint = lerp(u, v, 0.5)  # 0.5 to interpolate half-way between points

    """
    v0 = np.asarray(v0, dtype=dtype)
    v1 = np.asarray(v1, dtype=dtype)
    t = float(t)
    return (1.0 - t) * v0 + t * v1


def slerp(q0, q1, t, dtype='float32'):
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
        Interpolation factor [0, 1].
    dtype : str or obj
        Data type to use for all computations (eg. 'float32', 'float64', float,
        etc.)

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
    q0 = normalize(q0, dtype=dtype)
    q1 = normalize(q1, dtype=dtype)

    dot = np.dot(q0, q1)
    if dot < 0.0:
        q1 = -q1
        dot = -dot

    # small angle, use linear interpolation instead and return
    if dot > 0.9995:
        interp = q0 + t * (q1 - q0)
        return normalize(interp, dtype=dtype)

    theta0 = np.arccos(dot)
    theta = theta0 * t
    sinTheta = np.sin(theta)
    sinTheta0 = np.sin(theta0)
    s0 = np.cos(theta) - dot * sinTheta / sinTheta0
    s1 = sinTheta / sinTheta0

    return (q0 * s0) + (q1 * s1)


def quatFromAxisAngle(axis, angle, degrees=False, dtype='float32'):
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
    dtype : str or obj
        Data type to use for all computations (eg. 'float32', 'float64', float,
        etc.)

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
    q = np.zeros((4,), dtype=dtype)
    axis = normalize(axis, dtype=dtype)
    np.multiply(axis, np.sin(halfRad), out=q[:3])
    q[3] = np.cos(halfRad)

    return q + 0.0  # remove negative zeros


def multQuat(q0, q1, out=None, dtype='float32'):
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
    dtype : str or obj
        Data type to use for all computations (eg. 'float32', 'float64', float,
        etc.)

    Returns
    -------
    ndarray
        Combined orientation of `q0` amd `q1`. Returns `None` if `out` is
        specified.

    Notes
    -----
    * Quaternions are normalized prior to multiplication.

    """
    q0 = normalize(q0, dtype=dtype)
    q1 = normalize(q1, dtype=dtype)

    if out is None:
        qr = np.zeros((4,), dtype=dtype)
    else:
        qr = out

    qr[:3] = np.cross(q0[:3], q1[:3]) + q0[:3] * q1[3] + q1[:3] * q0[3]
    qr[3] = q0[3] * q1[3] - q0[:3].dot(q1[:3])

    if out is None:
        return qr

    return qr


def matrixFromQuat(q, out=None, dtype='float32'):
    """Create a rotation matrix from a quaternion.

    Parameters
    ----------
    q : tuple, list or ndarray of float
        Quaternion to convert in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    out : ndarray or None
        Alternative array to write values. Must be `shape` == (4,4,) and same
        `dtype` as the `dtype` argument.
    dtype : str or obj
        Data type to use for all computations (eg. 'float32', 'float64', float,
        etc.)

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
    
    """
    # based off implementations from
    # https://github.com/glfw/glfw/blob/master/deps/linmath.h
    q = normalize(q, dtype=dtype)
    b, c, d, a = q[:]
    vsqr = np.square(q)

    if out is None:
        R = np.zeros((4, 4,), dtype=dtype)
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


def scaleMatrix(s, dtype='float32'):
    """Create a scaling matrix.

    The resulting matrix is the same as a generated by a `glScale` call.

    Parameters
    ----------
    s : ndarray, tuple, or list of float
        Scaling factors [sx, sy, sz].
    dtype : str or obj
        Data type to use for all computations (eg. 'float32', 'float64', float,
        etc.)

    Returns
    -------
    ndarray
        4x4 scaling matrix in row-major order.

    """
    # from glScale
    S = np.zeros((4, 4,), dtype=dtype)
    S[0, 0] = s[0]
    S[1, 1] = s[1]
    S[2, 2] = s[2]
    S[3, 3] = 1.0

    return S


def rotationMatrix(angle, axis, dtype='float32'):
    """Create a rotation matrix.

    The resulting matrix will rotate points about `axis` by `angle`. The
    resulting matrix is similar to that produced by a `glRotate` call.

    Parameters
    ----------
    angle : float
        Rotation angle in degrees.
    axis : ndarray, list, or tuple of float
        Axis vector components.
    dtype : str or obj
        Data type to use for all computations (eg. 'float32', 'float64', float,
        etc.)

    Returns
    -------
    ndarray
        4x4 scaling matrix in row-major order.

    Notes
    -----
    * Vector `axis` is normalized before creating the matrix.

    """
    axis = normalize(axis, dtype=dtype)
    angle = np.radians(angle)
    c = np.cos(angle)
    s = np.sin(angle)

    xs, ys, zs = axis * s
    x2, y2, z2 = np.square(axis)
    x, y, z = axis
    cd = 1.0 - c

    R = np.zeros((4, 4,), dtype=dtype)
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


def translationMatrix(t, dtype='float32'):
    """Create a translation matrix.

    The resulting matrix is the same as generated by a `glTranslate` call.

    Parameters
    ----------
    t : ndarray, tuple, or list of float
        Translation vector [tx, ty, tz].
    dtype : str or obj
        Data type to use for all computations (eg. 'float32', 'float64', float,
        etc.)

    Returns
    -------
    ndarray
        4x4 translation matrix in row-major order.

    """
    S = np.identity(4, dtype=dtype)
    S[:3, 3] = t

    return S
