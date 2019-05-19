#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Various math functions for working with vectors, matrices, and quaternions.

"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['normalize', 'slerp', 'quatFromAxisAngle', 'quatToMatrix']

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
    if norm != 0.0:
        v /= norm
    else:
        return np.zeros(v.shape, dtype=dtype)

    return v


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

    """
    rad = np.radians(float(angle)) if not degrees else float(angle)
    q = np.zeros((4,), dtype=dtype)
    axis = np.asarray(axis, dtype=dtype)
    np.multiply(axis, np.sin(rad / 2.0), out=q[:3])
    q[3] = np.cos(rad / 2.0)

    return q


def quatToMatrix(q, dtype='float32'):
    """Create a rotation matrix from an orientation represented by a quaternion.

    Parameters
    ----------
    q : tuple, list or ndarray of float
        Quaternion to convert in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    dtype : str or obj
        Data type to use for all computations (eg. 'float32', 'float64', float,
        etc.)

    Returns
    -------
    ndarray
        4x4 rotation matrix in row-major order.
    
    """
    # based off implementations from
    # https://github.com/glfw/glfw/blob/master/deps/linmath.h
    q = normalize(q, dtype=dtype)
    print(q)
    a = q[3]
    b, c, d = q[:3]
    a2 = a * a
    b2 = b * b
    c2 = c * c
    d2 = d * d

    R = np.zeros((4, 4,), dtype=dtype)
    R[0, 0] = a2 + b2 - c2 - d2
    R[1, 0] = 2.0 * (b * c + a * d)
    R[2, 0] = 2.0 * (b * d - a * c)
    R[3, 0] = 0.0

    R[0, 1] = 2.0 * (b * c - a * d)
    R[1, 1] = a2 - b2 + c2 - d2
    R[2, 1] = 2.0 * (c * d + a * b)
    R[3, 1] = 0.0

    R[0, 2] = 2.0 * (b * d + a * c)
    R[1, 2] = 2.0 * (c * d - a * b)
    R[2, 2] = a2 - b2 - c2 + d2
    R[3, 2] = 0.0

    R[:3, 3] = 0.0
    R[3, 3] = 1.0

    return R
