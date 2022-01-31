#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Various math functions for working with vectors, matrices, and quaternions.
#

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['normalize',
           'lerp',
           'slerp',
           'multQuat',
           'quatFromAxisAngle',
           'quatToMatrix',
           'scaleMatrix',
           'rotationMatrix',
           'transform',
           'translationMatrix',
           'concatenate',
           'applyMatrix',
           'invertQuat',
           'quatToAxisAngle',
           'posOriToMatrix',
           'applyQuat',
           'orthogonalize',
           'reflect',
           'cross',
           'distance',
           'dot',
           'quatMagnitude',
           'length',
           'project',
           'bisector',
           'surfaceNormal',
           'invertMatrix',
           'angleTo',
           'surfaceBitangent',
           'surfaceTangent',
           'vertexNormal',
           'isOrthogonal',
           'isAffine',
           'perp',
           'ortho3Dto2D',
           'intersectRayPlane',
           'matrixToQuat',
           'lensCorrection',
           'matrixFromEulerAngles',
           'alignTo',
           'quatYawPitchRoll',
           'intersectRaySphere',
           'intersectRayAABB',
           'intersectRayOBB',
           'intersectRayTriangle',
           'scale',
           'multMatrix',
           'normalMatrix',
           'fitBBox',
           'computeBBoxCorners',
           'zeroFix',
           'accumQuat',
           'fixTangentHandedness',
           'articulate',
           'forwardProject',
           'reverseProject',
           'lensCorrectionSpherical']


import numpy as np
import functools
import itertools


VEC_AXES = {'+x': (1, 0, 0), '-x': (-1, 0, 0),
            '+y': (0, 1, 0), '-y': (0, -1, 0),
            '+z': (0, 0, 1), '-z': (0, 0, -1)}


# ------------------------------------------------------------------------------
# Vector Operations
#

def length(v, squared=False, out=None, dtype=None):
    """Get the length of a vector.

    Parameters
    ----------
    v : array_like
        Vector to normalize, can be Nx2, Nx3, or Nx4. If a 2D array is
        specified, rows are treated as separate vectors.
    squared : bool, optional
        If ``True`` the squared length is returned. The default is ``False``.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    float or ndarray
        Length of vector `v`.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    v = np.asarray(v, dtype=dtype)

    if v.ndim == 2:
        assert v.shape[1] <= 4
        toReturn = np.zeros((v.shape[0],), dtype=dtype) if out is None else out
        v2d, vr = np.atleast_2d(v, toReturn)  # 2d view of array
        if squared:
            vr[:, :] = np.sum(np.square(v2d), axis=1)
        else:
            vr[:, :] = np.sqrt(np.sum(np.square(v2d), axis=1))
    elif v.ndim == 1:
        assert v.shape[0] <= 4
        if squared:
            toReturn = np.sum(np.square(v))
        else:
            toReturn = np.sqrt(np.sum(np.square(v)))
    else:
        raise ValueError("Input arguments have invalid dimensions.")

    return toReturn


def normalize(v, out=None, dtype=None):
    """Normalize a vector or quaternion.

    v : array_like
        Vector to normalize, can be Nx2, Nx3, or Nx4. If a 2D array is
        specified, rows are treated as separate vectors. All vectors should have
        nonzero length.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Normalized vector `v`.

    Notes
    -----
    * If the vector has length is zero, a vector of all zeros is returned after
      normalization.

    Examples
    --------
    Normalize a vector::

        v = [1., 2., 3., 4.]
        vn = normalize(v)

    The `normalize` function is vectorized. It's considerably faster to
    normalize large arrays of vectors than to call `normalize` separately for
    each one::

        v = np.random.uniform(-1.0, 1.0, (1000, 4,))  # 1000 length 4 vectors
        vn = np.zeros((1000, 4))  # place to write values
        normalize(v, out=vn)  # very fast!

        # don't do this!
        for i in range(1000):
            vn[i, :] = normalize(v[i, :])

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
        toReturn = np.array(v, dtype=dtype)
    else:
        toReturn = out

    v2d = np.atleast_2d(toReturn)  # 2d view of array
    norm = np.linalg.norm(v2d, axis=1)
    norm[norm == 0.0] = np.NaN  # make sure if length==0 division succeeds
    v2d /= norm[:, np.newaxis]
    np.nan_to_num(v2d, copy=False)  # fix NaNs

    return toReturn


def orthogonalize(v, n, out=None, dtype=None):
    """Orthogonalize a vector relative to a normal vector.

    This function ensures that `v` is perpendicular (or orthogonal) to `n`.

    Parameters
    ----------
    v : array_like
        Vector to orthogonalize, can be Nx2, Nx3, or Nx4. If a 2D array is
        specified, rows are treated as separate vectors.
    n : array_like
        Normal vector, must have same shape as `v`.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Orthogonalized vector `v` relative to normal vector `n`.

    Warnings
    --------
    If `v` and `n` are the same, the direction of the perpendicular vector is
    indeterminate. The resulting vector is degenerate (all zeros).

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    v = np.asarray(v, dtype=dtype)
    n = np.asarray(n, dtype=dtype)

    if out is None:
        toReturn = np.zeros_like(v, dtype=dtype)
    else:
        toReturn = out
        toReturn.fill(0.0)

    v, n, vr = np.atleast_2d(v, n, toReturn)
    vr[:, :] = v
    vr[:, :] -= n * np.sum(n * v, axis=1)[:, np.newaxis]  # dot product
    normalize(vr, out=vr)

    return toReturn


def reflect(v, n, out=None, dtype=None):
    """Reflection of a vector.

    Get the reflection of `v` relative to normal `n`.

    Parameters
    ----------
    v : array_like
        Vector to reflect, can be Nx2, Nx3, or Nx4. If a 2D array is specified,
        rows are treated as separate vectors.
    n : array_like
        Normal vector, must have same shape as `v`.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Reflected vector `v` off normal `n`.

    """
    # based off https://github.com/glfw/glfw/blob/master/deps/linmath.h
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    v = np.asarray(v, dtype=dtype)
    n = np.asarray(n, dtype=dtype)

    if out is None:
        toReturn = np.zeros_like(v, dtype=dtype)
    else:
        toReturn = out
        toReturn.fill(0.0)

    v, n, vr = np.atleast_2d(v, n, toReturn)

    vr[:, :] = v
    vr[:, :] -= (dtype(2.0) * np.sum(n * v, axis=1))[:, np.newaxis] * n

    return toReturn


def dot(v0, v1, out=None, dtype=None):
    """Dot product of two vectors.

    The behaviour of this function depends on the format of the input arguments:

    * If `v0` and `v1` are 1D, the dot product is returned as a scalar and `out`
      is ignored.
    * If `v0` and `v1` are 2D, a 1D array of dot products between corresponding
      row vectors are returned.
    * If either `v0` and `v1` are 1D and 2D, an array of dot products
      between each row of the 2D vector and the 1D vector are returned.

    Parameters
    ----------
    v0, v1 : array_like
        Vector(s) to compute dot products of (e.g. [x, y, z]). `v0` must have
        equal or fewer dimensions than `v1`.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Dot product(s) of `v0` and `v1`.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    v0 = np.asarray(v0, dtype=dtype)
    v1 = np.asarray(v1, dtype=dtype)

    if v0.ndim == v1.ndim == 2 or v0.ndim == 2 and v1.ndim == 1:
        toReturn = np.zeros((v0.shape[0],), dtype=dtype) if out is None else out
        vr = np.atleast_2d(toReturn)  # make sure we have a 2d view
        vr[:] = np.sum(v1 * v0, axis=1)
    elif v0.ndim == v1.ndim == 1:
        toReturn = np.sum(v1 * v0)
    elif v0.ndim == 1 and v1.ndim == 2:
        toReturn = np.zeros((v1.shape[0],), dtype=dtype) if out is None else out
        vr = np.atleast_2d(toReturn)  # make sure we have a 2d view
        vr[:] = np.sum(v1 * v0, axis=1)
    else:
        raise ValueError("Input arguments have invalid dimensions.")

    return toReturn


def cross(v0, v1, out=None, dtype=None):
    """Cross product of 3D vectors.

    The behavior of this function depends on the dimensions of the inputs:

    * If `v0` and `v1` are 1D, the cross product is returned as 1D vector.
    * If `v0` and `v1` are 2D, a 2D array of cross products between
      corresponding row vectors are returned.
    * If either `v0` and `v1` are 1D and 2D, an array of cross products
      between each row of the 2D vector and the 1D vector are returned.

    Parameters
    ----------
    v0, v1 : array_like
        Vector(s) in form [x, y, z] or [x, y, z, 1].
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Cross product of `v0` and `v1`.

    Notes
    -----
    * If input vectors are 4D, the last value of cross product vectors is always
      set to one.
    * If input vectors `v0` and `v1` are Nx3 and `out` is Nx4, the cross product
      is computed and the last column of `out` is filled with ones.

    Examples
    --------

    Find the cross product of two vectors::

        a = normalize([1, 2, 3])
        b = normalize([3, 2, 1])
        c = cross(a, b)

    If input arguments are 2D, the function returns the cross products of
    corresponding rows::

        # create two 6x3 arrays with random numbers
        shape = (6, 3,)
        a = normalize(np.random.uniform(-1.0, 1.0, shape))
        b = normalize(np.random.uniform(-1.0, 1.0, shape))
        cprod = np.zeros(shape)  # output has the same shape as inputs
        cross(a, b, out=cprod)

    If a 1D and 2D vector are specified, the cross product of each row of the
    2D array and the 1D array is returned as a 2D array::

        a = normalize([1, 2, 3])
        b = normalize(np.random.uniform(-1.0, 1.0, (6, 3,)))
        cprod = np.zeros(a.shape)
        cross(a, b, out=cprod)

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    v0 = np.asarray(v0, dtype=dtype)
    v1 = np.asarray(v1, dtype=dtype)

    if v0.ndim == v1.ndim == 2:  # 2D x 2D
        assert v0.shape == v1.shape
        toReturn = np.zeros(v0.shape, dtype=dtype) if out is None else out
        vr = np.atleast_2d(toReturn)
        vr[:, 0] = v0[:, 1] * v1[:, 2] - v0[:, 2] * v1[:, 1]
        vr[:, 1] = v0[:, 2] * v1[:, 0] - v0[:, 0] * v1[:, 2]
        vr[:, 2] = v0[:, 0] * v1[:, 1] - v0[:, 1] * v1[:, 0]

        if vr.shape[1] == 4:
            vr[:, 3] = dtype(1.0)

    elif v0.ndim == v1.ndim == 1:  # 1D x 1D
        assert v0.shape == v1.shape
        toReturn = np.zeros(v0.shape, dtype=dtype) if out is None else out
        toReturn[0] = v0[1] * v1[2] - v0[2] * v1[1]
        toReturn[1] = v0[2] * v1[0] - v0[0] * v1[2]
        toReturn[2] = v0[0] * v1[1] - v0[1] * v1[0]

        if toReturn.shape[0] == 4:
            toReturn[3] = dtype(1.0)

    elif v0.ndim == 2 and v1.ndim == 1:  # 2D x 1D
        toReturn = np.zeros(v0.shape, dtype=dtype) if out is None else out
        vr = np.atleast_2d(toReturn)
        vr[:, 0] = v0[:, 1] * v1[2] - v0[:, 2] * v1[1]
        vr[:, 1] = v0[:, 2] * v1[0] - v0[:, 0] * v1[2]
        vr[:, 2] = v0[:, 0] * v1[1] - v0[:, 1] * v1[0]

        if vr.shape[1] == 4:
            vr[:, 3] = dtype(1.0)

    elif v0.ndim == 1 and v1.ndim == 2:  # 1D x 2D
        toReturn = np.zeros(v1.shape, dtype=dtype) if out is None else out
        vr = np.atleast_2d(toReturn)
        vr[:, 0] = v1[:, 2] * v0[1] - v1[:, 1] * v0[2]
        vr[:, 1] = v1[:, 0] * v0[2] - v1[:, 2] * v0[0]
        vr[:, 2] = v1[:, 1] * v0[0] - v1[:, 0] * v0[1]

        if vr.shape[1] == 4:
            vr[:, 3] = dtype(1.0)

    else:
        raise ValueError("Input arguments have incorrect dimensions.")

    return toReturn


def project(v0, v1, out=None, dtype=None):
    """Project a vector onto another.

    Parameters
    ----------
    v0 : array_like
        Vector can be Nx2, Nx3, or Nx4. If a 2D array is specified, rows are
        treated as separate vectors.
    v1 : array_like
        Vector to project onto `v0`.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray or float
        Projection of vector `v0` on `v1`.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    v0 = np.asarray(v0, dtype=dtype)
    v1 = np.asarray(v1, dtype=dtype)

    if v0.ndim == v1.ndim == 2 or v0.ndim == 1 and v1.ndim == 2:
        toReturn = np.zeros_like(v1, dtype=dtype) if out is None else out
        toReturn[:, :] = v1[:, :]
        toReturn *= (dot(v0, v1, dtype=dtype) / length(v1))[:, np.newaxis]
    elif v0.ndim == v1.ndim == 1:
        toReturn = v1 * (dot(v0, v1, dtype=dtype) / np.sum(np.square(v1)))
    elif v0.ndim == 2 and v1.ndim == 1:
        toReturn = np.zeros_like(v0, dtype=dtype) if out is None else out
        toReturn[:, :] = v1[:]
        toReturn *= (dot(v0, v1, dtype=dtype) / length(v1))[:, np.newaxis]
    else:
        raise ValueError("Input arguments have invalid dimensions.")

    toReturn += 0.0  # remove negative zeros
    return toReturn


def lerp(v0, v1, t, out=None, dtype=None):
    """Linear interpolation (LERP) between two vectors/coordinates.

    Parameters
    ----------
    v0 : array_like
        Initial vector/coordinate. Can be 2D where each row is a point.
    v1 : array_like
        Final vector/coordinate. Must be the same shape as `v0`.
    t : float
        Interpolation weight factor [0, 1].
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

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
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    t = dtype(t)
    t0 = dtype(1.0) - t
    v0 = np.asarray(v0, dtype=dtype)
    v1 = np.asarray(v1, dtype=dtype)

    toReturn = np.zeros_like(v0, dtype=dtype) if out is None else out

    v0, v1, vr = np.atleast_2d(v0, v1, toReturn)
    vr[:, :] = v0 * t0
    vr[:, :] += v1 * t

    return toReturn


def distance(v0, v1, out=None, dtype=None):
    """Get the distance between vectors/coordinates.

    The behaviour of this function depends on the format of the input arguments:

    * If `v0` and `v1` are 1D, the distance is returned as a scalar and `out` is
      ignored.
    * If `v0` and `v1` are 2D, an array of distances between corresponding row
      vectors are returned.
    * If either `v0` and `v1` are 1D and 2D, an array of distances
      between each row of the 2D vector and the 1D vector are returned.

    Parameters
    ----------
    v0, v1 : array_like
        Vectors to compute the distance between.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Distance between vectors `v0` and `v1`.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    v0 = np.asarray(v0, dtype=dtype)
    v1 = np.asarray(v1, dtype=dtype)

    if v0.ndim == v1.ndim == 2 or (v0.ndim == 2 and v1.ndim == 1):
        dist = np.zeros((v1.shape[0],), dtype=dtype) if out is None else out
        dist[:] = np.sqrt(np.sum(np.square(v1 - v0), axis=1))
    elif v0.ndim == v1.ndim == 1:
        dist = np.sqrt(np.sum(np.square(v1 - v0)))
    elif v0.ndim == 1 and v1.ndim == 2:
        dist = np.zeros((v1.shape[0],), dtype=dtype) if out is None else out
        dist[:] = np.sqrt(np.sum(np.square(v0 - v1), axis=1))
    else:
        raise ValueError("Input arguments have invalid dimensions.")

    return dist


def perp(v, n, norm=True, out=None, dtype=None):
    """Project `v` to be a perpendicular axis of `n`.

    Parameters
    ----------
    v : array_like
        Vector to project [x, y, z], may be Nx3.
    n : array_like
        Normal vector [x, y, z], may be Nx3.
    norm : bool
        Normalize the resulting axis. Default is `True`.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Perpendicular axis of `n` from `v`.

    Examples
    --------
    Determine the local `up` (y-axis) of a surface or plane given `normal`::

        normal = [0., 0.70710678, 0.70710678]
        up = [1., 0., 0.]

        yaxis = perp(up, normal)

    Do a cross product to get the x-axis perpendicular to both::

        xaxis = cross(yaxis, normal)

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    v = np.asarray(v, dtype=dtype)
    n = np.asarray(n, dtype=dtype)

    toReturn = np.zeros_like(v, dtype=dtype) if out is None else out
    v2d, n2d, r2d = np.atleast_2d(v, n, toReturn)

    # from GLM `glm/gtx/perpendicular.inl`
    r2d[:, :] = v2d - project(v2d, n2d, dtype=dtype)

    if norm:
        normalize(toReturn, out=toReturn)

    toReturn += 0.0  # clear negative zeros

    return toReturn


def bisector(v0, v1, norm=False, out=None, dtype=None):
    """Get the angle bisector.

    Computes a vector which bisects the angle between `v0` and `v1`. Input
    vectors `v0` and `v1` must be non-zero.

    Parameters
    ----------
    v0, v1 : array_like
        Vectors to bisect [x, y, z]. Must be non-zero in length and have the
        same shape. Inputs can be Nx3 where the bisector for corresponding
        rows will be returned.
    norm : bool, optional
        Normalize the resulting bisector. Default is `False`.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Bisecting vector [x, y, z].

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    v0 = np.asarray(v0, dtype=dtype)
    v1 = np.asarray(v1, dtype=dtype)

    assert v0.shape == v1.shape

    toReturn = np.zeros_like(v0, dtype=dtype) if out is None else out

    v02d, v12d, r2d = np.atleast_2d(v0, v1, toReturn)

    r2d[:, :] = v02d * length(v12d, dtype=dtype)[:, np.newaxis] + \
                v12d * length(v02d, dtype=dtype)[:, np.newaxis]

    if norm:
        normalize(r2d, out=r2d)

    return toReturn


def angleTo(v, point, degrees=True, out=None, dtype=None):
    """Get the relative angle to a point from a vector.

    The behaviour of this function depends on the format of the input arguments:

    * If `v0` and `v1` are 1D, the angle is returned as a scalar and `out` is
      ignored.
    * If `v0` and `v1` are 2D, an array of angles between corresponding row
      vectors are returned.
    * If either `v0` and `v1` are 1D and 2D, an array of angles
      between each row of the 2D vector and the 1D vector are returned.

    Parameters
    ----------
    v : array_like
        Direction vector [x, y, z].
    point : array_like
        Point(s) to compute angle to from vector `v`.
    degrees : bool, optional
        Return the resulting angles in degrees. If `False`, angles will be
        returned in radians. Default is `True`.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Distance between vectors `v0` and `v1`.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    v = np.asarray(v, dtype=dtype)
    point = np.asarray(point, dtype=dtype)

    if v.ndim == point.ndim == 2 or (v.ndim == 2 and point.ndim == 1):
        angle = np.zeros((v.shape[0],), dtype=dtype) if out is None else out
        u = np.sqrt(length(v, squared=True, dtype=dtype) *
                    length(point, squared=True, dtype=dtype))
        angle[:] = np.arccos(dot(v, point, dtype=dtype) / u)
    elif v.ndim == 1 and point.ndim == 2:
        angle = np.zeros((point.shape[0],), dtype=dtype) if out is None else out
        u = np.sqrt(length(v, squared=True, dtype=dtype) *
                    length(point, squared=True, dtype=dtype))
        angle[:] = np.arccos(dot(v, point, dtype=dtype) / u)
    elif v.ndim == point.ndim == 1:
        u = np.sqrt(length(v, squared=True, dtype=dtype) *
                    length(point, squared=True, dtype=dtype))
        angle = np.arccos(dot(v, point, dtype=dtype) / u)
    else:
        raise ValueError("Input arguments have invalid dimensions.")

    return np.degrees(angle) if degrees else angle


def surfaceNormal(tri, norm=True, out=None, dtype=None):
    """Compute the surface normal of a given triangle.

    Parameters
    ----------
    tri : array_like
        Triangle vertices as 2D (3x3) array [p0, p1, p2] where each vertex is a
        length 3 array [vx, xy, vz]. The input array can be 3D (Nx3x3) to
        specify multiple triangles.
    norm : bool, optional
        Normalize computed surface normals if ``True``, default is ``True``.
    out : ndarray, optional
        Optional output array. Must have one fewer dimensions than `tri`. The
        shape of the last dimension must be 3.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Surface normal of triangle `tri`.

    Examples
    --------
    Compute the surface normal of a triangle::

        vertices = [[-1., 0., 0.], [0., 1., 0.], [1, 0, 0]]
        norm = surfaceNormal(vertices)

    Find the normals for multiple triangles, and put results in a pre-allocated
    array::

        vertices = [[[-1., 0., 0.], [0., 1., 0.], [1, 0, 0]],  # 2x3x3
                    [[1., 0., 0.], [0., 1., 0.], [-1, 0, 0]]]
        normals = np.zeros((2, 3))  # normals from two triangles triangles
        surfaceNormal(vertices, out=normals)

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    tris = np.asarray(tri, dtype=dtype)
    if tris.ndim == 2:
        tris = np.expand_dims(tri, axis=0)

    if tris.shape[0] == 1:
        toReturn = np.zeros((3,), dtype=dtype) if out is None else out
    else:
        if out is None:
            toReturn = np.zeros((tris.shape[0], 3), dtype=dtype)
        else:
            toReturn = out

    # from https://www.khronos.org/opengl/wiki/Calculating_a_Surface_Normal
    nr = np.atleast_2d(toReturn)
    u = tris[:, 1, :] - tris[:, 0, :]
    v = tris[:, 2, :] - tris[:, 1, :]
    nr[:, 0] = u[:, 1] * v[:, 2] - u[:, 2] * v[:, 1]
    nr[:, 1] = u[:, 2] * v[:, 0] - u[:, 0] * v[:, 2]
    nr[:, 2] = u[:, 0] * v[:, 1] - u[:, 1] * v[:, 0]

    if norm:
        normalize(nr, out=nr)

    return toReturn


def surfaceBitangent(tri, uv, norm=True, out=None, dtype=None):
    """Compute the bitangent vector of a given triangle.

    This function can be used to generate bitangent vertex attributes for normal
    mapping. After computing bitangents, one may orthogonalize them with vertex
    normals using the :func:`orthogonalize` function, or within the fragment
    shader. Uses texture coordinates at each triangle vertex to determine the
    direction of the vector.

    Parameters
    ----------
    tri : array_like
        Triangle vertices as 2D (3x3) array [p0, p1, p2] where each vertex is a
        length 3 array [vx, xy, vz]. The input array can be 3D (Nx3x3) to
        specify multiple triangles.
    uv : array_like
        Texture coordinates associated with each face vertex as a 2D array (3x2)
        where each texture coordinate is length 2 array [u, v]. The input array
        can be 3D (Nx3x2) to specify multiple texture coordinates if multiple
        triangles are specified.
    norm : bool, optional
        Normalize computed bitangents if ``True``, default is ``True``.
    out : ndarray, optional
        Optional output array. Must have one fewer dimensions than `tri`. The
        shape of the last dimension must be 3.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Surface bitangent of triangle `tri`.

    Examples
    --------
    Computing the bitangents for two triangles from vertex and texture
    coordinates (UVs)::

        # array of triangle vertices (2x3x3)
        tri = np.asarray([
            [(-1.0, 1.0, 0.0), (-1.0, -1.0, 0.0), (1.0, -1.0, 0.0)],   # 1
            [(-1.0, 1.0, 0.0), (-1.0, -1.0, 0.0), (1.0, -1.0, 0.0)]])  # 2

        # array of triangle texture coordinates (2x3x2)
        uv = np.asarray([
            [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0)],   # 1
            [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0)]])  # 2

        bitangents = surfaceBitangent(tri, uv, norm=True)  # bitangets (2x3)

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    tris = np.asarray(tri, dtype=dtype)
    if tris.ndim == 2:
        tris = np.expand_dims(tri, axis=0)

    if tris.shape[0] == 1:
        toReturn = np.zeros((3,), dtype=dtype) if out is None else out
    else:
        if out is None:
            toReturn = np.zeros((tris.shape[0], 3), dtype=dtype)
        else:
            toReturn = out

    uvs = np.asarray(uv, dtype=dtype)
    if uvs.ndim == 2:
        uvs = np.expand_dims(uvs, axis=0)

    # based off the implementation from
    # https://learnopengl.com/Advanced-Lighting/Normal-Mapping
    e1 = tris[:, 1, :] - tris[:, 0, :]
    e2 = tris[:, 2, :] - tris[:, 0, :]
    d1 = uvs[:, 1, :] - uvs[:, 0, :]
    d2 = uvs[:, 2, :] - uvs[:, 0, :]

    # compute the bitangent
    nr = np.atleast_2d(toReturn)
    nr[:, 0] = -d2[:, 0] * e1[:, 0] + d1[:, 0] * e2[:, 0]
    nr[:, 1] = -d2[:, 0] * e1[:, 1] + d1[:, 0] * e2[:, 1]
    nr[:, 2] = -d2[:, 0] * e1[:, 2] + d1[:, 0] * e2[:, 2]

    f = dtype(1.0) / (d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1])
    nr *= f[:, np.newaxis]

    if norm:
        normalize(toReturn, out=toReturn, dtype=dtype)

    return toReturn


def surfaceTangent(tri, uv, norm=True, out=None, dtype=None):
    """Compute the tangent vector of a given triangle.

    This function can be used to generate tangent vertex attributes for normal
    mapping. After computing tangents, one may orthogonalize them with vertex
    normals using the :func:`orthogonalize` function, or within the fragment
    shader. Uses texture coordinates at each triangle vertex to determine the
    direction of the vector.

    Parameters
    ----------
    tri : array_like
        Triangle vertices as 2D (3x3) array [p0, p1, p2] where each vertex is a
        length 3 array [vx, xy, vz]. The input array can be 3D (Nx3x3) to
        specify multiple triangles.
    uv : array_like
        Texture coordinates associated with each face vertex as a 2D array (3x2)
        where each texture coordinate is length 2 array [u, v]. The input array
        can be 3D (Nx3x2) to specify multiple texture coordinates if multiple
        triangles are specified. If so `N` must be the same size as the first
        dimension of `tri`.
    norm : bool, optional
        Normalize computed tangents if ``True``, default is ``True``.
    out : ndarray, optional
        Optional output array. Must have one fewer dimensions than `tri`. The
        shape of the last dimension must be 3.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Surface normal of triangle `tri`.

    Examples
    --------
    Compute surface normals, tangents, and bitangents for a list of triangles::

        # triangle vertices (2x3x3)
        vertices = [[[-1., 0., 0.], [0., 1., 0.], [1, 0, 0]],
                    [[1., 0., 0.], [0., 1., 0.], [-1, 0, 0]]]

        # array of triangle texture coordinates (2x3x2)
        uv = np.asarray([
            [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0)],   # 1
            [(0.0, 1.0), (0.0, 0.0), (1.0, 0.0)]])  # 2

        normals = surfaceNormal(vertices)
        tangents = surfaceTangent(vertices, uv)
        bitangents = cross(normals, tangents)  # or use `surfaceBitangent`

    Orthogonalize a surface tangent with a vertex normal vector to get the
    vertex tangent and bitangent vectors::

        vertexTangent = orthogonalize(faceTangent, vertexNormal)
        vertexBitangent = cross(vertexTangent, vertexNormal)

    Ensure computed vectors have the same handedness, if not, flip the tangent
    vector (important for applications like normal mapping)::

        # tangent, bitangent, and normal are 2D
        tangent[dot(cross(normal, tangent), bitangent) < 0.0, :] *= -1.0

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    tris = np.asarray(tri, dtype=dtype)
    if tris.ndim == 2:
        tris = np.expand_dims(tri, axis=0)

    if tris.shape[0] == 1:
        toReturn = np.zeros((3,), dtype=dtype) if out is None else out
    else:
        if out is None:
            toReturn = np.zeros((tris.shape[0], 3), dtype=dtype)
        else:
            toReturn = out

    uvs = np.asarray(uv, dtype=dtype)
    if uvs.ndim == 2:
        uvs = np.expand_dims(uvs, axis=0)

    # based off the implementation from
    # https://learnopengl.com/Advanced-Lighting/Normal-Mapping
    e1 = tris[:, 1, :] - tris[:, 0, :]
    e2 = tris[:, 2, :] - tris[:, 0, :]
    d1 = uvs[:, 1, :] - uvs[:, 0, :]
    d2 = uvs[:, 2, :] - uvs[:, 0, :]

    # compute the bitangent
    nr = np.atleast_2d(toReturn)
    nr[:, 0] = d2[:, 1] * e1[:, 0] - d1[:, 1] * e2[:, 0]
    nr[:, 1] = d2[:, 1] * e1[:, 1] - d1[:, 1] * e2[:, 1]
    nr[:, 2] = d2[:, 1] * e1[:, 2] - d1[:, 1] * e2[:, 2]

    f = dtype(1.0) / (d1[:, 0] * d2[:, 1] - d2[:, 0] * d1[:, 1])
    nr *= f[:, np.newaxis]

    if norm:
        normalize(toReturn, out=toReturn, dtype=dtype)

    return toReturn


def vertexNormal(faceNorms, norm=True, out=None, dtype=None):
    """Compute a vertex normal from shared triangles.

    This function computes a vertex normal by averaging the surface normals of
    the triangles it belongs to. If model has no vertex normals, first use
    :func:`surfaceNormal` to compute them, then run :func:`vertexNormal` to
    compute vertex normal attributes.

    While this function is mainly used to compute vertex normals, it can also
    be supplied triangle tangents and bitangents.

    Parameters
    ----------
    faceNorms : array_like
        An array (Nx3) of surface normals.
    norm : bool, optional
        Normalize computed normals if ``True``, default is ``True``.
    out : ndarray, optional
        Optional output array.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Vertex normal.

    Examples
    --------
    Compute a vertex normal from the face normals of the triangles it belongs
    to::

        normals = [[1., 0., 0.], [0., 1., 0.]]  # adjacent face normals
        vertexNorm = vertexNormal(normals)

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    triNorms2d = np.atleast_2d(np.asarray(faceNorms, dtype=dtype))
    nFaces = triNorms2d.shape[0]

    if out is None:
        toReturn = np.zeros((3,), dtype=dtype)
    else:
        toReturn = out

    toReturn[0] = np.sum(triNorms2d[:, 0])
    toReturn[1] = np.sum(triNorms2d[:, 1])
    toReturn[2] = np.sum(triNorms2d[:, 2])
    toReturn /= nFaces

    if norm:
        normalize(toReturn, out=toReturn, dtype=dtype)

    return toReturn


def fixTangentHandedness(tangents, normals, bitangents, out=None, dtype=None):
    """Ensure the handedness of tangent vectors are all the same.

    Often 3D computed tangents may not have the same handedness due to how
    texture coordinates are specified. This function takes input surface vectors
    are ensures that tangents have the same handedness. Use this function if you
    notice that normal mapping shading appears reversed with respect to the
    incident light direction. The output array of corrected tangents can be used
    inplace of the original.

    Parameters
    ----------
    tangents, normals, bitangents : array_like
        Input Nx3 arrays of triangle tangents, normals and bitangents. All
        arrays must have the same size.
    out : ndarray, optional
        Optional output array for tangents. If not specified, a new array of
        tangents will be allocated.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Array of tangents with handedness corrected.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    tangents = np.asarray(tangents, dtype=dtype)
    normals = np.asarray(normals, dtype=dtype)
    bitangents = np.asarray(bitangents, dtype=dtype)

    toReturn = np.zeros_like(tangents, dtype=dtype) if out is None else out
    toReturn[:, :] = tangents
    toReturn[dot(cross(normals, tangents, dtype=dtype),
                 bitangents, dtype=dtype) < 0.0, :] *= -1.0

    return toReturn


# ------------------------------------------------------------------------------
# Collision Detection, Interaction and Kinematics
#
def fitBBox(points, dtype=None):
    """Fit an axis-aligned bounding box around points.

    This computes the minimum and maximum extents for a bounding box to
    completely enclose `points`. Keep in mind the the output in bounds are
    axis-aligned and may not optimally fits the points (i.e. fits the points
    with the minimum required volume). However, this should work well enough for
    applications such as visibility testing (see
    `~psychopy.tools.viewtools.volumeVisible` for more information..

    Parameters
    ----------
    points : array_like
        Nx3 or Nx4 array of points to fit the bounding box to.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Extents (mins, maxs) as a 2x3 array.

    See Also
    --------
    computeBBoxCorners : Convert bounding box extents to corners.

    """
    dtype = np.float64 if dtype is None else np.dtype(dtype).type

    points = np.asarray(points, dtype=dtype)
    extents = np.zeros((2, 3), dtype=dtype)

    extents[0, :] = (np.min(points[:, 0]),
                     np.min(points[:, 1]),
                     np.min(points[:, 2]))
    extents[1, :] = (np.max(points[:, 0]),
                     np.max(points[:, 1]),
                     np.max(points[:, 2]))

    return extents


def computeBBoxCorners(extents, dtype=None):
    """Get the corners of an axis-aligned bounding box.

    Parameters
    ----------
    extents : array_like
        2x3 array indicating the minimum and maximum extents of the bounding
        box.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        8x4 array of points defining the corners of the bounding box.

    Examples
    --------
    Compute the corner points of a bounding box::

        minExtent = [-1, -1, -1]
        maxExtent = [1, 1, 1]
        corners = computeBBoxCorners([minExtent, maxExtent])

        # [[ 1.  1.  1.  1.]
        #  [-1.  1.  1.  1.]
        #  [ 1. -1.  1.  1.]
        #  [-1. -1.  1.  1.]
        #  [ 1.  1. -1.  1.]
        #  [-1.  1. -1.  1.]
        #  [ 1. -1. -1.  1.]
        #  [-1. -1. -1.  1.]]

    """
    extents = np.asarray(extents, dtype=dtype)

    assert extents.shape == (2, 3,)

    corners = np.zeros((8, 4), dtype=dtype)
    idx = np.arange(0, 8)
    corners[:, 0] = np.where(idx[:] & 1, extents[0, 0], extents[1, 0])
    corners[:, 1] = np.where(idx[:] & 2, extents[0, 1], extents[1, 1])
    corners[:, 2] = np.where(idx[:] & 4, extents[0, 2], extents[1, 2])
    corners[:, 3] = 1.0

    return corners


def intersectRayPlane(rayOrig, rayDir, planeOrig, planeNormal, dtype=None):
    """Get the point which a ray intersects a plane.

    Parameters
    ----------
    rayOrig : array_like
        Origin of the line in space [x, y, z].
    rayDir : array_like
        Direction vector of the line [x, y, z].
    planeOrig : array_like
        Origin of the plane to test [x, y, z].
    planeNormal : array_like
        Normal vector of the plane [x, y, z].
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    tuple or None
        Position (`ndarray`) in space which the line intersects the plane and
        the distance the intersect occurs from the origin (`float`). `None` is
        returned if the line does not intersect the plane at a single point or
        at all.

    Examples
    --------
    Find the point in the scene a ray intersects the plane::

        # plane information
        planeOrigin = [0, 0, 0]
        planeNormal = [0, 0, 1]
        planeUpAxis = perp([0, 1, 0], planeNormal)

        # ray
        rayDir = [0, 0, -1]
        rayOrigin = [0, 0, 5]

        # get the intersect and distance in 3D world space
        pnt, dist = intersectRayPlane(rayOrigin, rayDir, planeOrigin, planeNormal)

    """
    dtype = np.float64 if dtype is None else np.dtype(dtype).type

    # based off the method from GLM
    rayOrig = np.asarray(rayOrig, dtype=dtype)
    rayDir = np.asarray(rayDir, dtype=dtype)
    planeOrig = np.asarray(planeOrig, dtype=dtype)
    planeNormal = np.asarray(planeNormal, dtype=dtype)

    denom = dot(rayDir, planeNormal, dtype=dtype)
    if denom == 0.0:
        return None

    # distance to collision
    dist = dot((planeOrig - rayOrig), planeNormal, dtype=dtype) / denom
    intersect = dist * rayDir + rayOrig

    return intersect, dist


def intersectRaySphere(rayOrig, rayDir, sphereOrig=(0., 0., 0.), sphereRadius=1.0,
                       dtype=None):
    """Calculate the points which a ray/line intersects a sphere (if any).

    Get the 3D coordinate of the point which the ray intersects the sphere and
    the distance to the point from `orig`. The nearest point is returned if
    the line intersects the sphere at multiple locations. All coordinates should
    be in world/scene units.

    Parameters
    ----------
    rayOrig : array_like
        Origin of the ray in space [x, y, z].
    rayDir : array_like
        Direction vector of the ray [x, y, z], should be normalized.
    sphereOrig : array_like
        Origin of the sphere to test [x, y, z].
    sphereRadius : float
        Sphere radius to test in scene units.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    tuple
        Coordinate in world space of the intersection and distance in scene
        units from `orig`. Returns `None` if there is no intersection.

    """
    # based off example from https://antongerdelan.net/opengl/raycasting.html
    dtype = np.float64 if dtype is None else np.dtype(dtype).type

    rayOrig = np.asarray(rayOrig, dtype=dtype)
    rayDir = np.asarray(rayDir, dtype=dtype)
    sphereOrig = np.asarray(sphereOrig, dtype=dtype)
    sphereRadius = np.asarray(sphereRadius, dtype=dtype)

    d = rayOrig - sphereOrig
    b = np.dot(rayDir, d)
    c = np.dot(d, d) - np.square(sphereRadius)
    b2mc = np.square(b) - c  # determinant

    if b2mc < 0.0:  # no roots, ray does not intersect sphere
        return None

    u = np.sqrt(b2mc)
    nearestDist = np.minimum(-b + u, -b - u)
    pos = (rayDir * nearestDist) + rayOrig

    return pos, nearestDist


def intersectRayAABB(rayOrig, rayDir, boundsOffset, boundsExtents, dtype=None):
    """Find the point a ray intersects an axis-aligned bounding box (AABB).

    Parameters
    ----------
    rayOrig : array_like
        Origin of the ray in space [x, y, z].
    rayDir : array_like
        Direction vector of the ray [x, y, z], should be normalized.
    boundsOffset : array_like
        Offset of the bounding box in the scene [x, y, z].
    boundsExtents : array_like
        Minimum and maximum extents of the bounding box.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    tuple
        Coordinate in world space of the intersection and distance in scene
        units from `rayOrig`. Returns `None` if there is no intersection.

    Examples
    --------
    Get the point on an axis-aligned bounding box that the cursor is over and
    place a 3D stimulus there. The eye location is defined by `RigidBodyPose`
    object `camera`::

        # get the mouse position on-screen
        mx, my = mouse.getPos()

        # find the point which the ray intersects on the box
        result = intersectRayAABB(
            camera.pos,
            camera.transformNormal(win.coordToRay((mx, my))),
            myStim.pos,
            myStim.thePose.bounds.extents)

        # if the ray intersects, set the position of the cursor object to it
        if result is not None:
            cursorModel.thePose.pos = result[0]
            cursorModel.draw()  # don't draw anything if there is no intersect

    Note that if the model is rotated, the bounding box may not be aligned
    anymore with the axes. Use `intersectRayOBB` if your model rotates.

    """
    # based of the example provided here:
    # https://www.scratchapixel.com/lessons/3d-basic-rendering/
    # minimal-ray-tracer-rendering-simple-shapes/ray-box-intersection
    dtype = np.float64 if dtype is None else np.dtype(dtype).type

    rayOrig = np.asarray(rayOrig, dtype=dtype)
    rayDir = np.asarray(rayDir, dtype=dtype)
    boundsOffset = np.asarray(boundsOffset, dtype=dtype)
    extents = np.asarray(boundsExtents, dtype=dtype) + boundsOffset

    invDir = 1.0 / rayDir
    sign = np.zeros((3,), dtype=int)
    sign[invDir < 0.0] = 1

    tmin = (extents[sign[0], 0] - rayOrig[0]) * invDir[0]
    tmax = (extents[1 - sign[0], 0] - rayOrig[0]) * invDir[0]
    tymin = (extents[sign[1], 1] - rayOrig[1]) * invDir[1]
    tymax = (extents[1 - sign[1], 1] - rayOrig[1]) * invDir[1]

    if tmin > tymax or tymin > tmax:
        return None

    if tymin > tmin:
        tmin = tymin

    if tymax < tmax:
        tmax = tymax

    tzmin = (extents[sign[2], 2] - rayOrig[2]) * invDir[2]
    tzmax = (extents[1 - sign[2], 2] - rayOrig[2]) * invDir[2]

    if tmin > tzmax or tzmin > tmax:
        return None

    if tzmin > tmin:
        tmin = tzmin

    if tzmax < tmax:
        tmax = tzmax

    if tmin < 0:
        if tmax < 0:
            return None

    return (rayDir * tmin) + rayOrig, tmin


def intersectRayOBB(rayOrig, rayDir, modelMatrix, boundsExtents, dtype=None):
    """Find the point a ray intersects an oriented bounding box (OBB).

    Parameters
    ----------
    rayOrig : array_like
        Origin of the ray in space [x, y, z].
    rayDir : array_like
        Direction vector of the ray [x, y, z], should be normalized.
    modelMatrix : array_like
        4x4 model matrix of the object and bounding box.
    boundsExtents : array_like
        Minimum and maximum extents of the bounding box.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    tuple
        Coordinate in world space of the intersection and distance in scene
        units from `rayOrig`. Returns `None` if there is no intersection.

    Examples
    --------
    Get the point on an oriented bounding box that the cursor is over and place
    a 3D stimulus there. The eye location is defined by `RigidBodyPose` object
    `camera`::

        # get the mouse position on-screen
        mx, my = mouse.getPos()

        # find the point which the ray intersects on the box
        result = intersectRayOBB(
            camera.pos,
            camera.transformNormal(win.coordToRay((mx, my))),
            myStim.thePose.getModelMatrix(),
            myStim.thePose.bounds.extents)

        # if the ray intersects, set the position of the cursor object to it
        if result is not None:
            cursorModel.thePose.pos = result[0]
            cursorModel.draw()  # don't draw anything if there is no intersect

    """
    # based off algorithm:
    # https://www.opengl-tutorial.org/miscellaneous/clicking-on-objects/
    # picking-with-custom-ray-obb-function/
    dtype = np.float64 if dtype is None else np.dtype(dtype).type

    rayOrig = np.asarray(rayOrig, dtype=dtype)
    rayDir = np.asarray(rayDir, dtype=dtype)
    modelMatrix = np.asarray(modelMatrix, dtype=dtype)
    boundsOffset = np.asarray(modelMatrix[:3, 3], dtype=dtype)
    extents = np.asarray(boundsExtents, dtype=dtype)

    tmin = 0.0
    tmax = np.finfo(dtype).max
    d = boundsOffset - rayOrig

    # solve intersects for each pair of planes along each axis
    for i in range(3):
        axis = modelMatrix[:3, i]
        e = np.dot(axis, d)
        f = np.dot(rayDir, axis)

        if np.fabs(f) > 1e-5:
            t1 = (e + extents[0, i]) / f
            t2 = (e + extents[1, i]) / f

            if t1 > t2:
                temp = t1
                t1 = t2
                t2 = temp

            if t2 < tmax:
                tmax = t2

            if t1 > tmin:
                tmin = t1

            if tmin > tmax:
                return None

        else:
            # very close to parallel with the face
            if -e + extents[0, i] > 0.0 or -e + extents[1, i] < 0.0:
                return None

    return (rayDir * tmin) + rayOrig, tmin


def intersectRayTriangle(rayOrig, rayDir, tri, dtype=None):
    """Get the intersection of a ray and triangle(s).

    This function can be used to achieve 'pixel-perfect' ray picking/casting on
    meshes defined with triangles. However, high-poly meshes may lead to
    performance issues.

    Parameters
    ----------
    rayOrig : array_like
        Origin of the ray in space [x, y, z].
    rayDir : array_like
        Direction vector of the ray [x, y, z], should be normalized.
    tri : array_like
        Triangle vertices as 2D (3x3) array [p0, p1, p2] where each vertex is a
        length 3 array [vx, xy, vz]. The input array can be 3D (Nx3x3) to
        specify multiple triangles.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    tuple
        Coordinate in world space of the intersection, distance in scene
        units from `rayOrig`, and the barycentric coordinates on the triangle
        [x, y]. Returns `None` if there is no intersection.

    """
    # based off `intersectRayTriangle` from GLM (https://glm.g-truc.net)
    dtype = np.float64 if dtype is None else np.dtype(dtype).type

    rayOrig = np.asarray(rayOrig, dtype=dtype)
    rayDir = np.asarray(rayDir, dtype=dtype)
    triVerts = np.asarray(tri, dtype=dtype)

    edge1 = triVerts[1, :] - triVerts[0, :]
    edge2 = triVerts[2, :] - triVerts[0, :]

    baryPos = np.zeros((2,), dtype=dtype)

    p = np.cross(rayDir, edge2)
    det = np.dot(edge1, p)

    if det > np.finfo(dtype).eps:
        dist = rayOrig - triVerts[0, :]

        baryPos[0] = np.dot(dist, p)
        if baryPos[0] < 0.0 or baryPos[0] > det:
            return None

        ortho = np.cross(dist, edge1)

        baryPos[1] = np.dot(rayDir, ortho)
        if baryPos[1] < 0.0 or baryPos[0] + baryPos[1] > det:
            return None

    elif det < -np.finfo(dtype).eps:
        dist = rayOrig - triVerts[0, :]

        baryPos[0] = np.dot(dist, p)
        if baryPos[0] > 0.0 or baryPos[0] < det:
            return None

        ortho = np.cross(dist, edge1)

        baryPos[1] = np.dot(rayDir, ortho)
        if baryPos[1] > 0.0 or baryPos[0] + baryPos[1] < det:
            return None
    else:
        return None

    invDet = 1.0 / det
    dist = np.dot(edge2, ortho) * invDet
    baryPos *= invDet

    return (rayDir * dist) + rayOrig, dist, baryPos


def ortho3Dto2D(p, orig, normal, up, right=None, dtype=None):
    """Get the planar coordinates of an orthogonal projection of a 3D point onto
    a 2D plane.

    This function gets the nearest point on the plane which a 3D point falls on
    the plane.

    Parameters
    ----------
    p : array_like
        Point to be projected on the plane.
    orig : array_like
        Origin of the plane to test [x, y, z].
    normal : array_like
        Normal vector of the plane [x, y, z], must be normalized.
    up : array_like
        Normalized up (+Y) direction of the plane's coordinate system. Must be
        perpendicular to `normal`.
    right : array_like, optional
        Perpendicular right (+X) axis. If not provided, the axis will be
        computed via the cross product between `normal` and `up`.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Coordinates on the plane [X, Y] where the 3D point projects towards
        perpendicularly.

    Examples
    --------
    This function can be used with :func:`intersectRayPlane` to find the
    location on the plane the ray intersects::

        # plane information
        planeOrigin = [0, 0, 0]
        planeNormal = [0, 0, 1]  # must be normalized
        planeUpAxis = perp([0, 1, 0], planeNormal)  # must also be normalized

        # ray
        rayDir = [0, 0, -1]
        rayOrigin = [0, 0, 5]

        # get the intersect in 3D world space
        pnt = intersectRayPlane(rayOrigin, rayDir, planeOrigin, planeNormal)

        # get the 2D coordinates on the plane the intersect occurred
        planeX, planeY = ortho3Dto2D(pnt, planeOrigin, planeNormal, planeUpAxis)

    """
    dtype = np.float64 if dtype is None else np.dtype(dtype).type

    p = np.asarray(p, dtype=dtype)
    orig = np.asarray(orig, dtype=dtype)
    normal = np.asarray(normal, dtype=dtype)
    up = np.asarray(up, dtype=dtype)

    toReturn = np.zeros((2,))

    offset = p - orig
    if right is None:
        # derive X axis with cross product
        toReturn[0] = dot(offset, cross(normal, up, dtype=dtype), dtype=dtype)
    else:
        toReturn[0] = dot(offset, np.asarray(right, dtype=dtype), dtype=dtype)

    toReturn[1] = dot(offset, up)

    return toReturn


def articulate(boneVecs, boneOris, dtype=None):
    """Articulate an armature.

    This function is used for forward kinematics and posing by specifying a list
    of 'bones'. A bone has a length and orientation, where sequential bones are
    linked end-to-end. Returns the transformed origins of the bones in scene
    coordinates and their orientations.

    There are many applications for forward kinematics such as posing armatures
    and stimuli for display (eg. mocap data). Another application is for getting
    the location of the end effector of coordinate measuring hardware, where
    encoders measure the joint angles and the length of linking members are
    known. This can be used for computing pose from "Sword of Damocles"[1]_ like
    hardware or some other haptic input devices which the participant wears (eg.
    a glove that measures joint angles in the hand). The computed pose of the
    joints can be used to interact with virtual stimuli.

    Parameters
    ----------
    boneVecs : array_like
        Bone lengths [x, y, z] as an Nx3 array.
    boneOris : array_like
        Orientation of the bones as quaternions in form [x, y, z, w], relative
        to the previous bone.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    tuple
        Array of bone origins and orientations. The first origin is root
        position which is always at [0, 0, 0]. Use :func:`transform` to
        reposition the armature, or create a transformation matrix and use
        `applyMatrix` to translate and rotate the whole armature into position.

    References
    ----------
    .. [1] Sutherland, I. E. (1968). "A head-mounted three dimensional display".
           Proceedings of AFIPS 68, pp. 757-764

    Examples
    --------
    Compute the orientations and origins of segments of an arm::

        # bone lengths
        boneLengths = [[0., 1., 0.], [0., 1., 0.], [0., 1., 0.]]

        # create quaternions for joints
        shoulder = mt.quatFromAxisAngle('-y', 45.0)
        elbow = mt.quatFromAxisAngle('+z', 45.0)
        wrist = mt.quatFromAxisAngle('+z', 45.0)

        # articulate the parts of the arm
        boxPos, boxOri = mt.articulate(pos, [shoulder, elbow, wrist])

        # assign positions and orientations to 3D objects
        shoulderModel.thePose.posOri = (boxPos[0, :], boxOri[0, :])
        elbowModel.thePose.posOri = (boxPos[1, :], boxOri[1, :])
        wristModel.thePose.posOri = (boxPos[2, :], boxOri[2, :])

    """
    dtype = np.float64 if dtype is None else np.dtype(dtype).type

    boneVecs = np.asarray(boneVecs, dtype=dtype)
    boneOris = np.asarray(boneOris, dtype=dtype)

    jointOri = accumQuat(boneOris, dtype=dtype)  # get joint orientations
    bonesRotated = applyQuat(jointOri, boneVecs, dtype=dtype)  # rotate bones

    # accumulate
    bonesTranslated = np.asarray(
        tuple(itertools.accumulate(bonesRotated[:], lambda a, b: a + b)),
        dtype=dtype)
    bonesTranslated -= bonesTranslated[0, :]  # offset root length

    return bonesTranslated, jointOri


# ------------------------------------------------------------------------------
# Quaternion Operations
#

def slerp(q0, q1, t, shortest=True, out=None, dtype=None):
    """Spherical linear interpolation (SLERP) between two quaternions.

    The behaviour of this function depends on the types of arguments:

    * If `q0` and `q1` are both 1-D and `t` is scalar, the interpolation at `t`
      is returned.
    * If `q0` and `q1` are both 2-D Nx4 arrays and `t` is scalar, an Nx4 array
      is returned with each row containing the interpolation at `t` for each
      quaternion pair at matching row indices in `q0` and `q1`.

    Parameters
    ----------
    q0 : array_like
        Initial quaternion in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    q1 : array_like
        Final quaternion in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    t : float
        Interpolation weight factor within interval 0.0 and 1.0.
    shortest : bool, optional
        Ensure interpolation occurs along the shortest arc along the 4-D
        hypersphere (default is `True`).
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Quaternion [x, y, z, w] at `t`.

    Examples
    --------
    Interpolate between two orientations::

        q0 = quatFromAxisAngle(90.0, degrees=True)
        q1 = quatFromAxisAngle(-90.0, degrees=True)
        # halfway between 90 and -90 is 0.0 or quaternion [0. 0. 0. 1.]
        qr = slerp(q0, q1, 0.5)

    Example of smooth rotation of an object with fixed angular velocity::

        degPerSec = 10.0  # rotate a stimulus at 10 degrees per second

        # initial orientation, axis rotates in the Z direction
        qr = quatFromAxisAngle([0., 0., -1.], 0.0, degrees=True)
        # amount to rotate every second
        qv = quatFromAxisAngle([0., 0., -1.], degPerSec, degrees=True)

        # ---- within main experiment loop ----
        # `frameTime` is the time elapsed in seconds from last `slerp`.
        qr = multQuat(qr, slerp((0., 0., 0., 1.), qv, degPerSec * frameTime))
        _, angle = quatToAxisAngle(qr)  # discard axis, only need angle

        # myStim is a GratingStim or anything with an 'ori' argument which
        # accepts angle in degrees
        myStim.ori = angle
        myStim.draw()

    """
    # Implementation based on code found here:
    #  https://en.wikipedia.org/wiki/Slerp
    #
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    q0 = normalize(q0, dtype=dtype)
    q1 = normalize(q1, dtype=dtype)
    assert q0.shape == q1.shape

    toReturn = np.zeros(q0.shape, dtype=dtype) if out is None else out
    toReturn.fill(0.0)
    t = dtype(t)
    q0, q1, qr = np.atleast_2d(q0, q1, toReturn)

    d = np.clip(np.sum(q0 * q1, axis=1), -1.0, 1.0)
    if shortest:
        d[d < 0.0] *= -1.0
        q1[d < 0.0] *= -1.0

    theta0 = np.arccos(d)
    theta = theta0 * t
    sinTheta = np.sin(theta)
    s1 = sinTheta / np.sin(theta0)
    s0 = np.cos(theta[:, np.newaxis]) - d[:, np.newaxis] * s1[:, np.newaxis]
    qr[:, :] = q0 * s0
    qr[:, :] += q1 * s1[:, np.newaxis]
    qr[:, :] += 0.0

    return toReturn


def quatToAxisAngle(q, degrees=True, dtype=None):
    """Convert a quaternion to `axis` and `angle` representation.

    This allows you to use quaternions to set the orientation of stimuli that
    have an `ori` property.

    Parameters
    ----------
    q : tuple, list or ndarray of float
        Quaternion in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    degrees : bool, optional
        Indicate `angle` is to be returned in degrees, otherwise `angle` will be
        returned in radians.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    tuple
        Axis and angle of quaternion in form ([ax, ay, az], angle). If `degrees`
        is `True`, the angle returned is in degrees, radians if `False`.

    Examples
    --------
    Using a quaternion to rotate a stimulus a fixed angle each frame::

        # initial orientation, axis rotates in the Z direction
        qr = quatFromAxisAngle([0., 0., -1.], 0.0, degrees=True)
        # rotation per-frame, here it's 0.1 degrees per frame
        qf = quatFromAxisAngle([0., 0., -1.], 0.1, degrees=True)

        # ---- within main experiment loop ----
        # myStim is a GratingStim or anything with an 'ori' argument which
        # accepts angle in degrees
        qr = multQuat(qr, qf)  # cumulative rotation
        _, angle = quatToAxisAngle(qr)  # discard axis, only need angle
        myStim.ori = angle
        myStim.draw()

    """
    dtype = np.float64 if dtype is None else np.dtype(dtype).type
    q = normalize(q, dtype=dtype)  # returns ndarray
    v = np.sqrt(np.sum(np.square(q[:3])))

    if np.count_nonzero(q[:3]):
        axis = q[:3] / v
        angle = dtype(2.0) * np.arctan2(v, q[3])
    else:
        axis = np.zeros((3,), dtype=dtype)
        axis[0] = 1.
        angle = 0.0

    axis += 0.0

    return axis, np.degrees(angle) if degrees else angle


def quatFromAxisAngle(axis, angle, degrees=True, dtype=None):
    """Create a quaternion to represent a rotation about `axis` vector by
    `angle`.

    Parameters
    ----------
    axis : tuple, list, ndarray or str
        Axis vector components or axis name. If a vector, input must be length
        3 [x, y, z]. A string can be specified for rotations about world axes
        (eg. `'+x'`, `'-z'`, `'+y'`, etc.)
    angle : float
        Rotation angle in radians (or degrees if `degrees` is `True`. Rotations
        are right-handed about the specified `axis`.
    degrees : bool, optional
        Indicate `angle` is in degrees, otherwise `angle` will be treated as
        radians.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

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
    dtype = np.float64 if dtype is None else np.dtype(dtype).type
    toReturn = np.zeros((4,), dtype=dtype)

    if degrees:
        halfRad = np.radians(angle, dtype=dtype) / dtype(2.0)
    else:
        halfRad = np.dtype(dtype).type(angle) / dtype(2.0)

    try:
        axis = VEC_AXES[axis] if isinstance(axis, str) else axis
    except KeyError:
        raise ValueError(
            "Value of `axis` must be either '+X', '-X', '+Y', '-Y', '+Z' or "
            "'-Z' or length 3 vector.")

    axis = normalize(axis, dtype=dtype)
    if np.count_nonzero(axis) == 0:
        raise ValueError("Value for `axis` is zero-length.")

    np.multiply(axis, np.sin(halfRad), out=toReturn[:3])
    toReturn[3] = np.cos(halfRad)
    toReturn += 0.0  # remove negative zeros

    return toReturn


def quatYawPitchRoll(q, degrees=True, out=None, dtype=None):
    """Get the yaw, pitch, and roll of a quaternion's orientation relative to
    the world -Z axis.

    You can multiply the quaternion by the inverse of some other one to make the
    returned values referenced to a local coordinate system.

    Parameters
    ----------
    q : tuple, list or ndarray of float
        Quaternion in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    degrees : bool, optional
        Indicate angles are to be returned in degrees, otherwise they will be
        returned in radians.
    out : ndarray
        Optional output array. Must have same `shape` and `dtype` as what is
        expected to be returned by this function of `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Yaw, pitch and roll [yaw, pitch, roll] of quaternion `q`.

    """
    # based off code found here:
    # https://en.wikipedia.org/wiki/Conversion_between_quaternions_and_Euler_angles
    # Yields the same results as PsychXR's LibOVRPose.getYawPitchRoll method.
    dtype = np.float64 if dtype is None else np.dtype(dtype).type
    q = np.asarray(q, dtype=dtype)

    toReturn = np.zeros((3,), dtype=dtype) if out is None else out

    sinRcosP = 2.0 * (q[3] * q[0] + q[1] * q[2])
    cosRcosP = 1.0 - 2.0 * (q[0] * q[0] + q[1] * q[1])

    toReturn[0] = np.arctan2(sinRcosP, cosRcosP)

    sinp = 2.0 * (q[3] * q[1] - q[2] * q[0])

    if np.fabs(sinp) >= 1.:
        toReturn[1] = np.copysign(np.pi / 2., sinp)
    else:
        toReturn[1] = np.arcsin(sinp)

    sinYcosP = 2.0 * (q[3] * q[2] + q[0] * q[1])
    cosYcosP = 1.0 - 2.0 * (q[1] * q[1] + q[2] * q[2])

    toReturn[2] = np.arctan2(sinYcosP, cosYcosP)

    if degrees:
        toReturn[:] = np.degrees(toReturn[:])

    return toReturn


def quatMagnitude(q, squared=False, out=None, dtype=None):
    """Get the magnitude of a quaternion.

    A quaternion is normalized if its magnitude is 1.

    Parameters
    ----------
    q : array_like
        Quaternion(s) in form [x, y, z, w] where w is real and x, y, z are
        imaginary components.
    squared : bool, optional
        If ``True`` return the squared magnitude. If you are just checking if a
        quaternion is normalized, the squared magnitude will suffice to avoid
        the square root operation.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    float or ndarray
        Magnitude of quaternion `q`.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    q = np.asarray(q, dtype=dtype)
    if q.ndim == 1:
        assert q.shape[0] == 4
        if squared:
            toReturn = np.sum(np.square(q))
        else:
            toReturn = np.sqrt(np.sum(np.square(q)))
    elif q.ndim == 2:
        assert q.shape[1] == 4
        toReturn = np.zeros((q.shape[0],), dtype=dtype) if out is None else out
        if squared:
            toReturn[:] = np.sum(np.square(q), axis=1)
        else:
            toReturn[:] = np.sqrt(np.sum(np.square(q), axis=1))
    else:
        raise ValueError("Input argument 'q' has incorrect dimensions.")

    return toReturn


def multQuat(q0, q1, out=None, dtype=None):
    """Multiply quaternion `q0` and `q1`.

    The orientation of the returned quaternion is the combination of the input
    quaternions.

    Parameters
    ----------
    q0, q1 : array_like
        Quaternions to multiply in form [x, y, z, w] where w is real and x, y, z
        are imaginary components. If 2D (Nx4) arrays are specified, quaternions
        are multiplied row-wise between each array.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Combined orientations of `q0` amd `q1`.

    Notes
    -----
    * Quaternions are normalized prior to multiplication.

    Examples
    --------
    Combine the orientations of two quaternions::

        a = quatFromAxisAngle([0, 0, -1], 45.0, degrees=True)
        b = quatFromAxisAngle([0, 0, -1], 90.0, degrees=True)
        c = multQuat(a, b)  # rotates 135 degrees about -Z axis

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    q0 = normalize(q0, dtype=dtype)
    q1 = normalize(q1, dtype=dtype)
    assert q0.shape == q1.shape
    toReturn = np.zeros(q0.shape, dtype=dtype) if out is None else out
    toReturn.fill(0.0)  # clear array
    q0, q1, qr = np.atleast_2d(q0, q1, toReturn)

    # multiply quaternions for each row of the operand arrays
    qr[:, :3] = np.cross(q0[:, :3], q1[:, :3], axis=1)
    qr[:, :3] += q0[:, :3] * np.expand_dims(q1[:, 3], axis=1)
    qr[:, :3] += q1[:, :3] * np.expand_dims(q0[:, 3], axis=1)
    qr[:, 3] = q0[:, 3]
    qr[:, 3] *= q1[:, 3]
    qr[:, 3] -= np.sum(np.multiply(q0[:, :3], q1[:, :3]), axis=1)  # dot product
    qr += 0.0

    return toReturn


def invertQuat(q, out=None, dtype=None):
    """Get the multiplicative inverse of a quaternion.

    This gives a quaternion which rotates in the opposite direction with equal
    magnitude. Multiplying a quaternion by its inverse returns an identity
    quaternion as both orientations cancel out.

    Parameters
    ----------
    q : ndarray, list, or tuple of float
        Quaternion to invert in form [x, y, z, w] where w is real and x, y, z
        are imaginary components. If `q` is 2D (Nx4), each row is treated as a
        separate quaternion and inverted.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

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
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    q = normalize(q, dtype=dtype)
    toReturn = np.zeros(q.shape, dtype=dtype) if out is None else out
    qn, qinv = np.atleast_2d(q, toReturn)  # 2d views

    # conjugate the quaternion
    qinv[:, :3] = -qn[:, :3]
    qinv[:, 3] = qn[:, 3]
    qinv /= np.sum(np.square(qn), axis=1)[:, np.newaxis]
    qinv += 0.0  # remove negative zeros

    return toReturn


def applyQuat(q, points, out=None, dtype=None):
    """Rotate points/coordinates using a quaternion.

    This is similar to using `applyMatrix` with a rotation matrix. However, it
    is computationally less intensive to use `applyQuat` if one only wishes to
    rotate points.

    Parameters
    ----------
    q : array_like
        Quaternion to invert in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    points : array_like
        2D array of vectors or points to transform, where each row is a single
        point. Only the x, y, and z components (the first three columns) are
        rotated. Additional columns are copied.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Transformed points.

    Examples
    --------
    Rotate points using a quaternion::

        points = [[1., 0., 0.], [0., -1., 0.]]
        quat = quatFromAxisAngle(-90.0, [0., 0., -1.], degrees=True)
        pointsRotated = applyQuat(quat, points)
        # [[0. 1. 0.]
        #  [1. 0. 0.]]

    Show that you get the same result as a rotation matrix::

        axis = [0., 0., -1.]
        angle = -90.0
        rotMat = rotationMatrix(axis, angle)[:3, :3]  # rotation sub-matrix only
        rotQuat = quatFromAxisAngle(angle, axis, degrees=True)
        points = [[1., 0., 0.], [0., -1., 0.]]
        isClose = np.allclose(applyMatrix(rotMat, points),  # True
                              applyQuat(rotQuat, points))

    Specifying an array to `q` where each row is a quaternion transforms points
    in corresponding rows of `points`::

        points = [[1., 0., 0.], [0., -1., 0.]]
        quats = [quatFromAxisAngle(-90.0, [0., 0., -1.], degrees=True),
                 quatFromAxisAngle(45.0, [0., 0., -1.], degrees=True)]
        applyQuat(quats, points)

    """
    # based on 'quat_mul_vec3' implementation from linmath.h
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    qin = np.asarray(q, dtype=dtype)
    points = np.asarray(points, dtype=dtype)

    if out is not None:
        assert points.shape == out.shape

    toReturn = np.zeros(points.shape, dtype=dtype) if out is None else out
    pin, pout = np.atleast_2d(points, toReturn)
    pout[:, :] = pin[:, :]  # copy values into output array

    if qin.ndim == 1:
        assert qin.shape[0] == 4
        t = cross(qin[:3], pin[:, :3]) * dtype(2.0)
        u = cross(qin[:3], t)
        t *= qin[3]
        pout[:, :3] += t
        pout[:, :3] += u
    elif qin.ndim == 2:
        assert qin.shape[1] == 4 and qin.shape[0] == pin.shape[0]
        t = cross(qin[:, :3], pin[:, :3])
        t *= dtype(2.0)
        u = cross(qin[:, :3], t)
        t *= np.expand_dims(qin[:, 3], axis=1)
        pout[:, :3] += t
        pout[:, :3] += u
    else:
        raise ValueError("Input arguments have invalid dimensions.")

    return toReturn


def accumQuat(qlist, out=None, dtype=None):
    """Accumulate quaternion rotations.

    Chain multiplies an Nx4 array of quaternions, accumulating their rotations.
    This function can be used for computing the orientation of joints in an
    armature for forward kinematics. The first quaternion is treated as the
    'root' and the last is the orientation of the end effector.

    Parameters
    ----------
    q : array_like
        Nx4 array of quaternions to accumulate, where each row is a quaternion.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified. In this case, the same shape as
        `qlist`.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Nx4 array of quaternions.

    Examples
    --------
    Get the orientation of joints in an armature if we know their relative
    angles::

        shoulder = quatFromAxisAngle('-x', 45.0)  # rotate shoulder down 45 deg
        elbow = quatFromAxisAngle('+x', 45.0)  # rotate elbow up 45 deg
        wrist = quatFromAxisAngle('-x', 45.0)  # rotate wrist down 45 deg
        finger = quatFromAxisAngle('+x', 0.0)  # keep finger in-line with wrist

        armRotations = accumQuat([shoulder, elbow, wrist, finger])

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    qlist = np.asarray(qlist, dtype=dtype)
    qlist = np.atleast_2d(qlist)

    qr = np.zeros_like(qlist, dtype=dtype) if out is None else out
    qr[:, :] = tuple(itertools.accumulate(
        qlist[:], lambda a, b: multQuat(a, b, dtype=dtype)))

    return qr


def alignTo(v, t, out=None, dtype=None):
    """Compute a quaternion which rotates one vector to align with another.

    Parameters
    ----------
    v : array_like
        Vector [x, y, z] to rotate. Can be Nx3, but must have the same shape as
        `t`.
    t : array_like
        Target [x, y, z] vector to align to. Can be Nx3, but must have the same
        shape as `v`.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Quaternion which rotates `v` to `t`.

    Examples
    --------
    Rotate some vectors to align with other vectors, inputs should be
    normalized::

        vec = [[1, 0, 0], [0, 1, 0], [1, 0, 0]]
        targets = [[0, 1, 0], [0, -1, 0], [-1, 0, 0]]

        qr = alignTo(vec, targets)
        vecRotated = applyQuat(qr, vec)

        numpy.allclose(vecRotated, targets)  # True

    Get matrix which orients vertices towards a point::

        point = [5, 6, 7]
        vec = [0, 0, -1]  # initial facing is -Z (forward in GL)

        targetVec = normalize(point - vec)
        qr = alignTo(vec, targetVec)  # get rotation to align

        M = quatToMatrix(qr)  # 4x4 transformation matrix

    """
    # based off Quaternion::align from Quaternion.hpp from OpenMP
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    v = normalize(v, dtype=dtype)
    t = normalize(t, dtype=dtype)

    if out is None:
        if v.ndim == 1:
            toReturn = np.zeros((4,), dtype=dtype)
        else:
            toReturn = np.zeros((v.shape[0], 4), dtype=dtype)
    else:
        toReturn = out

    qr, v2d, t2d = np.atleast_2d(toReturn, v, t)

    b = bisector(v2d, t2d, norm=True, dtype=dtype)
    cosHalfAngle = dot(v2d, b, dtype=dtype)

    nonparallel = cosHalfAngle > 0.0  # rotation is not 180 degrees
    qr[nonparallel, :3] = cross(v2d[nonparallel], b[nonparallel], dtype=dtype)
    qr[nonparallel, 3] = cosHalfAngle[nonparallel]

    if np.alltrue(nonparallel):  # don't bother handling special cases
        return toReturn + 0.0

    # deal with cases where the vectors are facing exact opposite directions
    ry = np.logical_and(np.abs(v2d[:, 0]) >= np.abs(v2d[:, 1]), ~nonparallel)
    rx = np.logical_and(~ry, ~nonparallel)

    getLength = lambda x, y: np.sqrt(x * x + y * y)
    if not np.alltrue(rx):
        invLength = getLength(v2d[ry, 0], v2d[ry, 2])
        invLength = np.where(invLength > 0.0, 1.0 / invLength, invLength)  # avoid x / 0
        qr[ry, 0] = -v2d[ry, 2] * invLength
        qr[ry, 2] = v2d[ry, 0] * invLength

    if not np.alltrue(ry):  # skip if all the same edge case
        invLength = getLength(v2d[rx, 1], v2d[rx, 2])
        invLength = np.where(invLength > 0.0, 1.0 / invLength, invLength)
        qr[rx, 1] = v2d[rx, 2] * invLength
        qr[rx, 2] = -v2d[rx, 1] * invLength

    return toReturn + 0.0


def matrixToQuat(m, out=None, dtype=None):
    """Convert a rotation matrix to a quaternion.

    Parameters
    ----------
    m : array_like
        3x3 rotation matrix (row-major). A 4x4 affine transformation matrix may
        be provided, assuming the top-left 3x3 sub-matrix is orthonormal and
        is a rotation group.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Rotation quaternion.

    Notes
    -----
    * Depending on the input, returned quaternions may not be exactly the same
      as the one used to construct the rotation matrix (i.e. by calling
      `quatToMatrix`), typically when a large rotation angle is used. However,
      the returned quaternion should result in the same rotation when applied to
      points.

    Examples
    --------
    Converting a rotation matrix from the OpenGL matrix stack to a quaternion::

        glRotatef(45., -1, 0, 0)

        m = np.zeros((4, 4), dtype='float32')  # store the matrix
        GL.glGetFloatv(
            GL.GL_MODELVIEW_MATRIX,
            m.ctypes.data_as(ctypes.POINTER(ctypes.c_float)))

        qr = matrixToQuat(m.T)  # must be transposed

    Interpolation between two 4x4 transformation matrices::

        interpWeight = 0.5

        posStart = mStart[:3, 3]
        oriStart = matrixToQuat(mStart)

        posEnd = mEnd[:3, 3]
        oriEnd = matrixToQuat(mEnd)

        oriInterp = slerp(qStart, qEnd, interpWeight)
        posInterp = lerp(posStart, posEnd, interpWeight)

        mInterp = posOriToMatrix(posInterp, oriInterp)

    """
    # based off example `Maths - Conversion Matrix to Quaternion` from
    # https://www.euclideanspace.com/
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    m = np.asarray(m, dtype=dtype)

    if m.shape == (4, 4,) or m.shape == (3, 4,):
        m = m[:3, :3]  # keep only rotation group sub-matrix
    elif m.shape == (3, 3,):
        pass  # fine, nop
    else:
        raise ValueError("Input matrix `m` must be 3x3 or 4x4.")

    toReturn = np.zeros((4,), dtype=dtype) if out is None else out

    tr = m[0, 0] + m[1, 1] + m[2, 2]
    if tr > 0.0:
        s = np.sqrt(tr + 1.0) * 2.0
        toReturn[3] = dtype(0.25) * s
        toReturn[0] = (m[2, 1] - m[1, 2]) / s
        toReturn[1] = (m[0, 2] - m[2, 0]) / s
        toReturn[2] = (m[1, 0] - m[0, 1]) / s
    elif m[0, 0] > m[1, 1] and m[0, 0] > m[2, 2]:
        s = np.sqrt(dtype(1.0) + m[0, 0] - m[1, 1] - m[2, 2]) * dtype(2.0)
        toReturn[3] = (m[2, 1] - m[1, 2]) / s
        toReturn[0] = dtype(0.25) * s
        toReturn[1] = (m[0, 1] + m[1, 0]) / s
        toReturn[2] = (m[0, 2] + m[2, 0]) / s
    elif m[1, 1] > m[2, 2]:
        s = np.sqrt(dtype(1.0) + m[1, 1] - m[0, 0] - m[2, 2]) * dtype(2.0)
        toReturn[3] = (m[0, 2] - m[2, 0]) / s
        toReturn[0] = (m[0, 1] + m[1, 0]) / s
        toReturn[1] = dtype(0.25) * s
        toReturn[2] = (m[1, 2] + m[2, 1]) / s
    else:
        s = np.sqrt(dtype(1.0) + m[2, 2] - m[0, 0] - m[1, 1]) * dtype(2.0)
        toReturn[3] = (m[1, 0] - m[0, 1]) / s
        toReturn[0] = (m[0, 2] + m[2, 0]) / s
        toReturn[1] = (m[1, 2] + m[2, 1]) / s
        toReturn[2] = dtype(0.25) * s

    return toReturn


# ------------------------------------------------------------------------------
# Matrix Operations
#

def quatToMatrix(q, out=None, dtype=None):
    """Create a 4x4 rotation matrix from a quaternion.

    Parameters
    ----------
    q : tuple, list or ndarray of float
        Quaternion to convert in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    out : ndarray or None
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray or None
        4x4 rotation matrix in row-major order.

    Examples
    --------
    Convert a quaternion to a rotation matrix::

        point = [0., 1., 0., 1.]  # 4-vector form [x, y, z, 1.0]
        ori = [0., 0., 0., 1.]
        rotMat = quatToMatrix(ori)
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
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
        R = np.zeros((4, 4,), dtype=dtype)
    else:
        dtype = np.dtype(out.dtype).type
        R = out
        R.fill(0.0)

    q = normalize(q, dtype=dtype)
    b, c, d, a = q[:]
    vsqr = np.square(q)

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

    R[3, 3] = dtype(1.0)
    R[:, :] += 0.0  # remove negative zeros

    return R


def scaleMatrix(s, out=None, dtype=None):
    """Create a scaling matrix.

    The resulting matrix is the same as a generated by a `glScale` call.

    Parameters
    ----------
    s : array_like, float or int
        Scaling factor(s). If `s` is scalar (float), scaling will be uniform.
        Providing a vector of scaling values [sx, sy, sz] will result in an
        anisotropic scaling matrix if any of the values differ.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        4x4 scaling matrix in row-major order.

    """
    # from glScale
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
        S = np.zeros((4, 4,), dtype=dtype)
    else:
        dtype = np.dtype(out.dtype).type
        S = out
        S.fill(0.0)

    if isinstance(s, (float, int,)):
        S[0, 0] = S[1, 1] = S[2, 2] = dtype(s)
    else:
        S[0, 0] = dtype(s[0])
        S[1, 1] = dtype(s[1])
        S[2, 2] = dtype(s[2])

    S[3, 3] = 1.0

    return S


def rotationMatrix(angle, axis=(0., 0., -1.), out=None, dtype=None):
    """Create a rotation matrix.

    The resulting matrix will rotate points about `axis` by `angle`. The
    resulting matrix is similar to that produced by a `glRotate` call.

    Parameters
    ----------
    angle : float
        Rotation angle in degrees.
    axis : array_like or str
        Axis vector components or axis name. If a vector, input must be length
        3. A string can be specified for rotations about world axes (eg. `'+x'`,
        `'-z'`, `'+y'`, etc.)
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        4x4 scaling matrix in row-major order. Will be the same array as `out`
        if specified, if not, a new array will be allocated.

    Notes
    -----
    * Vector `axis` is normalized before creating the matrix.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
        R = np.zeros((4, 4,), dtype=dtype)
    else:
        dtype = np.dtype(out.dtype).type
        R = out
        R.fill(0.0)

    try:
        axis = VEC_AXES[axis] if isinstance(axis, str) else axis
    except KeyError:
        raise ValueError(
            "Value of `axis` must be either '+x', '-x', '+y', '-x', '+z' or "
            "'-z' or length 3 vector.")

    axis = normalize(axis, dtype=dtype)
    if np.count_nonzero(axis) == 0:
        raise ValueError("Value for `axis` is zero-length.")

    angle = np.radians(angle, dtype=dtype)
    c = np.cos(angle, dtype=dtype)
    s = np.sin(angle, dtype=dtype)

    xs, ys, zs = axis * s
    x2, y2, z2 = np.square(axis)  # type inferred by input
    x, y, z = axis
    cd = dtype(1.0) - c

    R[0, 0] = x2 * cd + c
    R[0, 1] = x * y * cd - zs
    R[0, 2] = x * z * cd + ys

    R[1, 0] = y * x * cd + zs
    R[1, 1] = y2 * cd + c
    R[1, 2] = y * z * cd - xs

    R[2, 0] = x * z * cd - ys
    R[2, 1] = y * z * cd + xs
    R[2, 2] = z2 * cd + c

    R[3, 3] = dtype(1.0)
    R[:, :] += 0.0  # remove negative zeros

    return R


def translationMatrix(t, out=None, dtype=None):
    """Create a translation matrix.

    The resulting matrix is the same as generated by a `glTranslate` call.

    Parameters
    ----------
    t : ndarray, tuple, or list of float
        Translation vector [tx, ty, tz].
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        4x4 translation matrix in row-major order. Will be the same array as
        `out` if specified, if not, a new array will be allocated.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
        T = np.identity(4, dtype=dtype)
    else:
        dtype = np.dtype(out.dtype).type
        T = out
        T.fill(0.0)
        np.fill_diagonal(T, 1.0)

    T[:3, 3] = np.asarray(t, dtype=dtype)

    return T


def invertMatrix(m, out=None, dtype=None):
    """Invert a square matrix.

    Parameters
    ----------
    m : array_like
        Square matrix to invert. Inputs can be 4x4, 3x3 or 2x2.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Matrix which is the inverse of `m`

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = out.dtype

    m = np.asarray(m, dtype=dtype)  # input as array
    toReturn = np.empty_like(m, dtype=dtype) if out is None else out
    toReturn.fill(0.0)

    if m.shape == (4, 4,):
        # Special handling of 4x4 matrices, if affine and orthogonal
        # (homogeneous), simply transpose the matrix rather than doing a full
        # invert.
        if isOrthogonal(m[:3, :3]) and isAffine(m):
            rg = m[:3, :3]
            toReturn[:3, :3] = rg.T
            toReturn[:3, 3] = -m[:3, 3].dot(rg)
            #toReturn[0, 3] = \
            #    -(m[0, 0] * m[0, 3] + m[1, 0] * m[1, 3] + m[2, 0] * m[2, 3])
            #toReturn[1, 3] = \
            #    -(m[0, 1] * m[0, 3] + m[1, 1] * m[1, 3] + m[2, 1] * m[2, 3])
            #toReturn[2, 3] = \
            #    -(m[0, 2] * m[0, 3] + m[1, 2] * m[1, 3] + m[2, 2] * m[2, 3])
            toReturn[3, 3] = 1.0
        else:
            toReturn[:, :] = np.linalg.inv(m)
    elif m.shape[0] == m.shape[1]:  # square, other than 4x4
        toReturn[:, :] = np.linalg.inv(m) if not isOrthogonal(m) else m.T
    else:
        toReturn[:, :] = np.linalg.inv(m)

    return toReturn


def multMatrix(matrices, reverse=False, out=None, dtype=None):
    """Chain multiplication of two or more matrices.

    Multiply a sequence of matrices together, reducing to a single product
    matrix. For instance, specifying `matrices` the sequence of matrices (A, B,
    C, D) will return the product (((AB)C)D). If `reverse=True`, the product
    will be (A(B(CD))).

    Alternatively, a 3D array can be specified to `matrices` as a stack, where
    an index along axis 0 references a 2D slice storing matrix values. The
    product of the matrices along the axis will be returned. This is a bit more
    efficient than specifying separate matrices in a sequence, but the
    difference is negligible when only a few matrices are being multiplied.

    Parameters
    ----------
    matrices : list, tuple or ndarray
        Sequence or stack of matrices to multiply. All matrices must have the
        same dimensions.
    reverse : bool, optional
        Multiply matrices right-to-left. This is useful when dealing with
        transformation matrices, where the order of operations for transforms
        will appear the same as the order the matrices are specified. Default is
        'False'. When `True`, this function behaves similarly to
        :func:`concatenate`.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Matrix product.

    Notes
    -----
    * You may use `numpy.matmul` when dealing with only two matrices instead of
      `multMatrix`.
    * If a single matrix is specified, the returned product will have the same
      values.

    Examples
    --------
    Chain multiplication of SRT matrices::

        translate = translationMatrix((0.035, 0, -0.5))
        rotate = rotationMatrix(90.0, (0, 1, 0))
        scale = scaleMatrix(2.0)

        SRT = multMatrix((translate, rotate, scale))

    Same as above, but matrices are in a 3x4x4 array::

        matStack = np.array((translate, rotate, scale))

        # or ...
        # matStack = np.zeros((3, 4, 4))
        # matStack[0, :, :] = translate
        # matStack[1, :, :] = rotate
        # matStack[2, :, :] = scale

        SRT = multMatrix(matStack)

    Using `reverse=True` allows you to specify transformation matrices in the
    order which they will be applied::

        SRT = multMatrix(np.array((scale, rotate, translate)), reverse=True)

    """
    # convert matrix types
    dtype = np.float64 if dtype is None else np.dtype(dtype).type
    matrices = np.asarray(matrices, dtype=dtype)  # convert to array

    matrices = np.atleast_3d(matrices)
    prod = functools.reduce(
        np.matmul, matrices[:] if not reverse else matrices[::-1])

    if out is not None:
        toReturn = out
        toReturn[:, :] = prod
    else:
        toReturn = prod

    return toReturn


def concatenate(matrices, out=None, dtype=None):
    """Concatenate matrix transformations.

    Chain multiply matrices describing transform operations into a single matrix
    product, that when applied, transforms points and vectors with each
    operation in the order they're specified.

    Parameters
    ----------
    matrices : list or tuple
        List of matrices to concatenate. All matrices must all have the same
        size, usually 4x4 or 3x3.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Matrix product.

    See Also
    --------
    * multMatrix : Chain multiplication of matrices.

    Notes
    -----
    * This function should only be used for combining transformation matrices.
      Use `multMatrix` for general matrix chain multiplication.

    Examples
    --------
    Create an SRT (scale, rotate, and translate) matrix to convert model-space
    coordinates to world-space::

        S = scaleMatrix([2.0, 2.0, 2.0])  # scale model 2x
        R = rotationMatrix(-90., [0., 0., -1])  # rotate -90 about -Z axis
        T = translationMatrix([0., 0., -5.])  # translate point 5 units away

        # product matrix when applied to points will scale, rotate and transform
        # in that order.
        SRT = concatenate([S, R, T])

        # transform a point in model-space coordinates to world-space
        pointModel = np.array([0., 1., 0., 1.])
        pointWorld = np.matmul(SRT, pointModel.T)  # point in WCS
        # ... or ...
        pointWorld = matrixApply(SRT, pointModel)

    Create a model-view matrix from a world-space pose represented by an
    orientation (quaternion) and position (vector). The resulting matrix will
    transform model-space coordinates to eye-space::

        # eye pose as quaternion and vector
        stimOri = quatFromAxisAngle([0., 0., -1.], -45.0)
        stimPos = [0., 1.5, -5.]

        # create model matrix
        R = quatToMatrix(stimOri)
        T = translationMatrix(stimPos)
        M = concatenate(R, T)  # model matrix

        # create a view matrix, can also be represented as 'pos' and 'ori'
        eyePos = [0., 1.5, 0.]
        eyeFwd = [0., 0., -1.]
        eyeUp = [0., 1., 0.]
        V = lookAt(eyePos, eyeFwd, eyeUp)  # from viewtools

        # modelview matrix
        MV = concatenate([M, V])

    You can put the created matrix in the OpenGL matrix stack as shown below.
    Note that the matrix must have a 32-bit floating-point data type and needs
    to be loaded transposed since OpenGL takes matrices in column-major order::

        GL.glMatrixMode(GL.GL_MODELVIEW)

        # pyglet
        MV = np.asarray(MV, dtype='float32')  # must be 32-bit float!
        ptrMV = MV.ctypes.data_as(ctypes.POINTER(ctypes.c_float))
        GL.glLoadTransposeMatrixf(ptrMV)

        # PyOpenGL
        MV = np.asarray(MV, dtype='float32')
        GL.glLoadTransposeMatrixf(MV)

    Furthermore, you can convert a point from model-space to homogeneous
    clip-space by concatenating the projection, view, and model matrices::

        # compute projection matrix, functions here are from 'viewtools'
        screenWidth = 0.52
        screenAspect = w / h
        scrDistance = 0.55
        frustum = computeFrustum(screenWidth, screenAspect, scrDistance)
        P = perspectiveProjectionMatrix(*frustum)

        # multiply model-space points by MVP to convert them to clip-space
        MVP = concatenate([M, V, P])
        pointModel = np.array([0., 1., 0., 1.])
        pointClipSpace = np.matmul(MVP, pointModel.T)

    """
    return multMatrix(matrices, reverse=True, out=out, dtype=dtype)


def matrixFromEulerAngles(rx, ry, rz, degrees=True, out=None, dtype=None):
    """Construct a 4x4 rotation matrix from Euler angles.

    Rotations are combined by first rotating about the X axis, then Y, and
    finally Z.

    Parameters
    ----------
    rx, ry, rz : float
        Rotation angles (pitch, yaw, and roll).
    degrees : bool, optional
        Rotation angles are specified in degrees. If `False`, they will be
        assumed as radians. Default is `True`.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        4x4 rotation matrix.

    Examples
    --------
    Demonstration of how a combination of axis-angle rotations is equivalent
    to a single call of `matrixFromEulerAngles`::

        m1 = matrixFromEulerAngles(90., 45., 135.))

        # construct rotation matrix from 3 orthogonal rotations
        rx = rotationMatrix(90., (1, 0, 0))  # x-axis
        ry = rotationMatrix(45., (0, 1, 0))  # y-axis
        rz = rotationMatrix(135., (0, 0, 1))  # z-axis
        m2 = concatenate([rz, ry, rx])  # note the order

        print(numpy.allclose(m1, m2))  # True

    Not only does `matrixFromEulerAngles` require less code, it also is
    considerably more efficient than constructing and multiplying multiple
    matrices.

    """
    # from https://www.j3d.org/matrix_faq/matrfaq_latest.html
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
        toReturn = np.zeros((4, 4,), dtype=dtype)
    else:
        dtype = np.dtype(dtype).type
        toReturn = out
        toReturn.fill(0.0)

    angles = np.asarray([rx, ry, rz], dtype=dtype)
    if degrees:
        angles = np.radians(angles)

    a, c, e = np.cos(angles)
    b, d, f = np.sin(angles)
    ad = a * d
    bd = b * d

    toReturn[0, 0] = c * e
    toReturn[0, 1] = -c * f
    toReturn[0, 2] = d
    toReturn[1, 0] = bd * e + a * f
    toReturn[1, 1] = -bd * f + a * e
    toReturn[1, 2] = -b * c
    toReturn[2, 0] = -ad * e + b * f
    toReturn[2, 1] = ad * f + b * e
    toReturn[2, 2] = a * c
    toReturn[3, 3] = 1.0

    return toReturn


def isOrthogonal(m):
    """Check if a square matrix is orthogonal.

    If a matrix is orthogonal, its columns form an orthonormal basis and is
    non-singular. An orthogonal matrix is invertible by simply taking the
    transpose of the matrix.

    Parameters
    ----------
    m : array_like
        Square matrix, either 2x2, 3x3 or 4x4.

    Returns
    -------
    bool
        `True` if the matrix is orthogonal.

    """
    if not isinstance(m, (np.ndarray,)):
        m = np.asarray(m)

    assert 2 <= m.shape[0] <= 4   # 2x2 to 4x4
    assert m.shape[0] == m.shape[1]  # must be square

    dtype = np.dtype(m.dtype).type
    return np.allclose(np.matmul(m.T, m, dtype=dtype),
                       np.identity(m.shape[0], dtype))


def isAffine(m):
    """Check if a 4x4 square matrix describes an affine transformation.

    Parameters
    ----------
    m : array_like
        4x4 transformation matrix.

    Returns
    -------
    bool
        `True` if the matrix is affine.

    """
    assert m.shape[0] == m.shape[1] == 4

    if not isinstance(m, (np.ndarray,)):
        m = np.asarray(m)

    dtype = np.dtype(m.dtype).type
    eps = np.finfo(dtype).eps

    return np.all(m[3, :3] < eps) and (dtype(1.0) - m[3, 3]) < eps


def applyMatrix(m, points, out=None, dtype=None):
    """Apply a matrix over a 2D array of points.

    This function behaves similarly to the following `Numpy` statement::

        points[:, :] = points.dot(m.T)

    Transformation matrices specified to `m` must have dimensions 4x4, 3x4, 3x3
    or 2x2. With the exception of 4x4 matrices, input `points` must have the
    same number of columns as the matrix has rows. 4x4 matrices can be used to
    transform both Nx4 and Nx3 arrays.

    Parameters
    ----------
    m : array_like
        Matrix with dimensions 2x2, 3x3, 3x4 or 4x4.
    points : array_like
        2D array of points/coordinates to transform. Each row should have length
        appropriate for the matrix being used.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Transformed coordinates.

    Notes
    -----
    * Input (`points`) and output (`out`) arrays cannot be the same instance for
      this function.
    * In the case of 4x4 input matrices, this function performs optimizations
      based on whether the input matrix is affine, greatly improving performance
      when working with Nx3 arrays.

    Examples
    --------
    Construct a matrix and transform a point::

        # identity 3x3 matrix for this example
        M = [[1.0, 0.0, 0.0],
             [0.0, 1.0, 0.0],
             [0.0, 0.0, 1.0]]

        pnt = [1.0, 0.0, 0.0]

        pntNew = applyMatrix(M, pnt)

    Construct an SRT matrix (scale, rotate, transform) and transform an array of
    points::

        S = scaleMatrix([5.0, 5.0, 5.0])  # scale 5x
        R = rotationMatrix(180., [0., 0., -1])  # rotate 180 degrees
        T = translationMatrix([0., 1.5, -3.])  # translate point up and away
        M = concatenate([S, R, T])  # create transform matrix

        # points to transform
        points = np.array([[0., 1., 0., 1.], [-1., 0., 0., 1.]]) # [x, y, z, w]
        newPoints = applyMatrix(M, points)  # apply the transformation

    Convert CIE-XYZ colors to sRGB::

        sRGBMatrix = [[3.2404542, -1.5371385, -0.4985314],
                      [-0.969266,  1.8760108,  0.041556 ],
                      [0.0556434, -0.2040259,  1.0572252]]

        colorsRGB = applyMatrix(sRGBMatrix, colorsXYZ)

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(out.dtype).type

    m = np.asarray(m, dtype=dtype)
    points = np.asarray(points, dtype=dtype)

    if out is None:
        toReturn = np.zeros_like(points, dtype=dtype)
    else:
        if id(out) == id(points):
            raise ValueError('Output array cannot be same as input.')
        toReturn = out

    pout, p = np.atleast_2d(toReturn, points)

    if m.shape[0] == m.shape[1] == 4:  # 4x4 matrix
        if pout.shape[1] == 3:  # Nx3
            pout[:, :] = p.dot(m[:3, :3].T)
            pout += m[:3, 3]
            # find `rcpW` as suggested in OpenXR's xr_linear.h header
            # reciprocal of `w` if the matrix is not orthonormal
            if not isAffine(m):
                rcpW = 1.0 / (m[3, 0] * p[:, 0] +
                              m[3, 1] * p[:, 1] +
                              m[3, 2] * p[:, 2] +
                              m[3, 3])
                pout *= rcpW[:, np.newaxis]
        elif pout.shape[1] == 4:  # Nx4
            pout[:, :] = p.dot(m.T)
        else:
            raise ValueError(
                'Input array dimensions invalid. Should be Nx3 or Nx4 when '
                'input matrix is 4x4.')
    elif m.shape[0] == 3 and m.shape[1] == 4:  # 3x4 matrix
        if pout.shape[1] == 3:  # Nx3
            pout[:, :] = p.dot(m[:3, :3].T)
            pout += m[:3, 3]
        else:
            raise ValueError(
                'Input array dimensions invalid. Should be Nx3 when input '
                'matrix is 3x4.')
    elif m.shape[0] == m.shape[1] == 3:  # 3x3 matrix, e.g colors
        if pout.shape[1] == 3:  # Nx3
            pout[:, :] = p.dot(m.T)
        else:
            raise ValueError(
                'Input array dimensions invalid. Should be Nx3 when '
                'input matrix is 3x3.')
    elif m.shape[0] == m.shape[1] == pout.shape[1] == 2:  # 2x2 matrix
        if pout.shape[1] == 2:  # Nx2
            pout[:, :] = p.dot(m.T)
        else:
            raise ValueError(
                'Input array dimensions invalid. Should be Nx2 when '
                'input matrix is 2x2.')
    else:
        raise ValueError(
            'Only a square matrix with dimensions 2, 3 or 4 can be used.')

    return toReturn


def posOriToMatrix(pos, ori, out=None, dtype=None):
    """Convert a rigid body pose to a 4x4 transformation matrix.

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
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        4x4 transformation matrix.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
        toReturn = np.zeros((4, 4,), dtype=dtype)
    else:
        dtype = np.dtype(dtype).type
        toReturn = out

    transMat = translationMatrix(pos, dtype=dtype)
    rotMat = quatToMatrix(ori, dtype=dtype)

    return np.matmul(transMat, rotMat, out=toReturn)


def transform(pos, ori, points, out=None, dtype=None):
    """Transform points using a position and orientation. Points are rotated
    then translated.

    Parameters
    ----------
    pos : array_like
        Position vector in form [x, y, z] or [x, y, z, 1].
    ori : array_like
        Orientation quaternion in form [x, y, z, w] where w is real and x, y, z
        are imaginary components.
    points : array_like
        Point(s) [x, y, z] to transform.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Transformed points.

    Examples
    --------
    Transform points by a position coordinate and orientation quaternion::

        # rigid body pose
        ori = quatFromAxisAngle([0., 0., -1.], 90.0, degrees=True)
        pos = [0., 1.5, -3.]
        # points to transform
        points = np.array([[0., 1., 0., 1.], [-1., 0., 0., 1.]])  # [x, y, z, 1]
        outPoints = np.zeros_like(points)  # output array
        transform(pos, ori, points, out=outPoints)  # do the transformation

    You can get the same results as the previous example using a matrix by doing
    the following::

        R = rotationMatrix(90., [0., 0., -1])
        T = translationMatrix([0., 1.5, -3.])
        M = concatenate([R, T])
        applyMatrix(M, points, out=outPoints)

    If you are defining transformations with quaternions and coordinates, you
    can skip the costly matrix creation process by using `transform`.

    Notes
    -----
    * In performance tests, `applyMatrix` is noticeably faster than `transform`
      for very large arrays, however this is only true if you are applying the
      same transformation to all points.
    * If the input arrays for `points` or `pos` is Nx4, the last column is
      ignored.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(dtype).type

    pos = np.asarray(pos, dtype=dtype)
    ori = np.asarray(ori, dtype=dtype)
    points = np.asarray(points, dtype=dtype)

    if out is None:
        toReturn = np.zeros_like(points, dtype=dtype)
    else:
        if out.shape != points.shape:
            raise ValueError(
                "Array 'out' and 'points' do not have matching shapes.")

        toReturn = out

    pout, points, pos2d = np.atleast_2d(toReturn, points, pos)  # create 2d views

    # apply rotation
    applyQuat(ori, points, out=pout)

    # apply translation
    pout[:, 0] += pos2d[:, 0]
    pout[:, 1] += pos2d[:, 1]
    pout[:, 2] += pos2d[:, 2]

    return toReturn


def scale(sf, points, out=None, dtype=None):
    """Scale points by a factor.

    This is useful for converting points between units, and to stretch or
    compress points along a given axis. Scaling can be uniform which the same
    factor is applied along all axes, or anisotropic along specific axes.

    Parameters
    ----------
    sf : array_like or float
        Scaling factor. If scalar, all points will be scaled uniformly by that
        factor. If a vector, scaling will be anisotropic along an axis.
    points : array_like
        Point(s) [x, y, z] to scale.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Scaled points.

    Examples
    --------
    Apply uniform scaling to points, here we scale to convert points in
    centimeters to meters::

        CM_TO_METERS = 1.0 / 100.0
        pointsCM = [[1, 2, 3], [4, 5, 6], [-1, 1, 0]]
        pointsM = scale(CM_TO_METERS, pointsCM)

    Anisotropic scaling along the X and Y axis::

        pointsM = scale((SCALE_FACTOR_X, SCALE_FACTOR_Y), pointsCM)

    Scale only on the X axis::

        pointsM = scale((SCALE_FACTOR_X,), pointsCM)

    Apply scaling on the Z axis only::

        pointsM = scale((1.0, 1.0, SCALE_FACTOR_Z), pointsCM)

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(dtype).type

    points = np.asarray(points, dtype=dtype)
    toReturn = np.zeros_like(points, dtype=dtype) if out is None else out
    toReturn, points = np.atleast_2d(toReturn, points)  # create 2d views

    # uniform scaling
    if isinstance(sf, (float, int)):
        toReturn[:, :] = points * sf
    elif isinstance(sf, (list, tuple, np.ndarray)):  # anisotropic
        sf = np.asarray(sf, dtype=dtype)
        sfLen = len(sf)
        if sfLen <= 3:
            toReturn[:, :] = points
            toReturn[:, :len(sf)] *= sf
        else:
            raise ValueError("Scale factor array must have length <= 3.")

    return toReturn


def normalMatrix(modelMatrix, out=None, dtype=None):
    """Get the normal matrix from a model matrix.

    Parameters
    ----------
    modelMatrix : array_like
        4x4 homogeneous model matrix.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Normal matrix.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(dtype).type

    modelMatrix = np.asarray(modelMatrix, dtype=dtype)

    toReturn = np.zeros((4, 4), dtype=dtype) if out is None else out
    toReturn[:, :] = np.linalg.inv(modelMatrix).T

    return toReturn


def forwardProject(objPos, modelView, proj, viewport=None, out=None, dtype=None):
    """Project a point in a scene to a window coordinate.

    This function is similar to `gluProject` and can be used to find the window
    coordinate which a point projects to.

    Parameters
    ----------
    objPos : array_like
        Object coordinates (x, y, z). If an Nx3 array of coordinates is
        specified, where each row contains a window coordinate this function
        will return an array of projected coordinates with the same size.
    modelView : array_like
        4x4 combined model and view matrix for returned value to be object
        coordinates. Specify only the view matrix for a coordinate in the scene.
    proj : array_like
        4x4 projection matrix used for rendering.
    viewport : array_like
        Viewport rectangle for the window [x, y, w, h]. If not specified, the
        returned values will be in normalized device coordinates.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Normalized device or viewport coordinates [x, y, z] of the point. The
        `z` component is similar to the depth buffer value for the object point.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(dtype).type

    toReturn = np.zeros_like(objPos, dtype=dtype) if out is None else out
    winCoord, objPos = np.atleast_2d(toReturn, objPos)

    # transformation matrix
    mvp = np.matmul(proj, modelView)

    # must have `w` for this one
    if objPos.shape[1] == 3:
        temp = np.zeros((objPos.shape[1], 4), dtype=dtype)
        temp[:, :3] = objPos
        objPos = temp

    # transform the points
    objNorm = applyMatrix(mvp, objPos, dtype=dtype)

    if viewport is not None:
        # if we have a viewport, transform it
        objNorm[:, :] += 1.0
        winCoord[:, 0] = viewport[0] + viewport[2] * objNorm[:, 0]
        winCoord[:, 1] = viewport[1] + viewport[3] * objNorm[:, 1]
        winCoord[:, 2] = objNorm[:, 2]
        winCoord[:, :] /= 2.0
    else:
        # already in NDC
        winCoord[:, :] = objNorm

    return toReturn  # ref to winCoord


def reverseProject(winPos, modelView, proj, viewport=None, out=None, dtype=None):
    """Unproject window coordinates into object or scene coordinates.

    This function works like `gluUnProject` and can be used to find to an object
    or scene coordinate at the point on-screen (mouse coordinate or pixel). The
    coordinate can then be used to create a direction vector from the viewer's
    eye location. Another use of this function is to convert depth buffer
    samples to object or scene coordinates. This is the inverse operation of
    :func:`forwardProject`.

    Parameters
    ----------
    winPos : array_like
        Window coordinates (x, y, z). If `viewport` is not specified, these
        should be normalized device coordinates. If an Nx3 array of coordinates
        is specified, where each row contains a window coordinate this function
        will return an array of unprojected coordinates with the same size.
        Usually, you only need to specify the `x` and `y` coordinate, leaving
        `z` as zero. However, you can specify `z` if sampling from a depth map
        or buffer to convert a depth sample to an actual location.
    modelView : array_like
        4x4 combined model and view matrix for returned value to be object
        coordinates. Specify only the view matrix for a coordinate in the scene.
    proj : array_like
        4x4 projection matrix used for rendering.
    viewport : array_like
        Viewport rectangle for the window [x, y, w, h]. Do not specify one if
        `winPos` is in already in normalized device coordinates.
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Object or scene coordinates.

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(dtype).type

    toReturn = np.zeros_like(winPos, dtype=dtype) if out is None else out
    objCoord, winPos = np.atleast_2d(toReturn, winPos)

    # get inverse of model and projection matrix
    invMVP = np.linalg.inv(np.matmul(proj, modelView))

    if viewport is not None:
        # if we have a viewport, we need to transform to NDC first
        objCoord[:, 0] = ((2 * winPos[:, 0] - viewport[0]) / viewport[2])
        objCoord[:, 1] = ((2 * winPos[:, 1] - viewport[1]) / viewport[3])
        objCoord[:, 2] = 2 * winPos[:, 2]
        objCoord -= 1
        objCoord[:, :] = applyMatrix(invMVP, objCoord, dtype=dtype)
    else:
        # already in NDC, just apply
        objCoord[:, :] = applyMatrix(invMVP, winPos, dtype=dtype)

    return toReturn  # ref to objCoord


# ------------------------------------------------------------------------------
# Misc. Math Functions
#

def zeroFix(a, inplace=False, threshold=None):
    """Fix zeros in an array.

    This function truncates very small numbers in an array to zero and removes
    any negative zeros.

    Parameters
    ----------
    a : ndarray
        Input array, must be a Numpy array.
    inplace : bool
        Fix an array inplace. If `True`, the input array will be modified,
        otherwise a new array will be returned with same `dtype` and shape with
        the fixed values.
    threshold : float or None
        Threshold for truncation. If `None`, the machine epsilon value for the
        input array `dtype` will be used. You can specify a custom threshold as
        a float.

    Returns
    -------
    ndarray
        Output array with zeros fixed.

    """
    toReturn = np.copy(a) if not inplace else a
    toReturn += 0.0  # remove negative zeros
    threshold = np.finfo(a.dtype).eps if threshold is None else float(threshold)
    toReturn[np.abs(toReturn) < threshold] = 0.0  # make zero

    return toReturn


def lensCorrection(xys, coefK=(1.0,), distCenter=(0., 0.), out=None,
                   dtype=None):
    """Lens correction (or distortion) using the division model with even
    polynomial terms.

    Calculate new vertex positions or texture coordinates to apply radial
    warping, such as 'pincushion' and 'barrel' distortion. This is to compensate
    for optical distortion introduced by lenses placed in the optical path of
    the viewer and the display (such as in an HMD).

    See references[1]_ for implementation details.

    Parameters
    ----------
    xys : array_like
        Nx2 list of vertex positions or texture coordinates to distort. Works
        correctly only if input values range between -1.0 and 1.0.
    coefK : array_like or float
        Distortion coefficients K_n. Specifying multiple values will add more
        polynomial terms to the distortion formula. Positive values will produce
        'barrel' distortion, whereas negative will produce 'pincushion'
        distortion. In most cases, two or three coefficients are adequate,
        depending on the degree of distortion.
    distCenter : array_like, optional
        X and Y coordinate of the distortion center (eg. (0.2, -0.4)).
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Array of distorted vertices.

    Notes
    -----
    * At this time tangential distortion (i.e. due to a slant in the display)
      cannot be corrected for.

    References
    ----------
    .. [1] Fitzgibbon, W. (2001). Simultaneous linear estimation of multiple
       view geometry and lens distortion. Proceedings of the 2001 IEEE Computer
       Society Conference on Computer Vision and Pattern Recognition (CVPR).
       IEEE.

    Examples
    --------
    Creating a lens correction mesh with barrel distortion (eg. for HMDs)::

        vertices, textureCoords, normals, faces = gltools.createMeshGrid(
            subdiv=11, tessMode='center')

        # recompute vertex positions
        vertices[:, :2] = mt.lensCorrection(vertices[:, :2], coefK=(5., 5.))

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(dtype).type

    if isinstance(coefK, (float, int,)):
        coefK = (coefK,)

    xys = np.asarray(xys, dtype=dtype)
    coefK = np.asarray(coefK, dtype=dtype)

    d_minus_c = xys - np.asarray(distCenter, dtype=dtype)
    r = np.power(length(d_minus_c, dtype=dtype)[:, np.newaxis],
                 np.arange(len(coefK), dtype=dtype) * 2. + 2.)

    toReturn = np.zeros_like(xys, dtype=dtype) if out is None else out

    denom = dtype(1.0) + dot(coefK, r, dtype=dtype)
    toReturn[:, :] = xys + (d_minus_c / denom[:, np.newaxis])

    return toReturn


def lensCorrectionSpherical(xys, coefK=1.0, aspect=1.0, out=None, dtype=None):
    """Simple lens correction.

    Lens correction for a spherical lenses with distortion centered at the
    middle of the display. See references[1]_ for implementation details.

    Parameters
    ----------
    xys : array_like
        Nx2 list of vertex positions or texture coordinates to distort. Assumes
        the output will be rendered to normalized device coordinates where
        points range from -1.0 to 1.0.
    coefK : float
        Distortion coefficient. Use positive numbers for pincushion distortion
        and negative for barrel distortion.
    aspect : float
        Aspect ratio of the target window or buffer (width / height).
    out : ndarray, optional
        Optional output array. Must be same `shape` and `dtype` as the expected
        output if `out` was not specified.
    dtype : dtype or str, optional
        Data type for computations can either be 'float32' or 'float64'. If
        `out` is specified, the data type of `out` is used and this argument is
        ignored. If `out` is not provided, 'float64' is used by default.

    Returns
    -------
    ndarray
        Array of distorted vertices.

    References
    ----------
    .. [1] Lens Distortion White Paper, Andersson Technologies LLC,
           www.ssontech.com/content/lensalg.html (obtained 07/28/2020)

    Examples
    --------
    Creating a lens correction mesh with barrel distortion (eg. for HMDs)::

        vertices, textureCoords, normals, faces = gltools.createMeshGrid(
            subdiv=11, tessMode='center')

        # recompute vertex positions
        vertices[:, :2] = mt.lensCorrection2(vertices[:, :2], coefK=2.0)

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
    else:
        dtype = np.dtype(dtype).type

    toReturn = np.empty_like(xys, dtype=dtype) if out is None else out

    xys = np.asarray(xys, dtype=dtype)
    toReturn[:, 0] = u = xys[:, 0]
    toReturn[:, 1] = v = xys[:, 1]
    coefKCubed = np.power(coefK, 3, dtype=dtype)

    r2 = aspect * aspect * u * u + v * v
    r2sqr = np.sqrt(r2, dtype=dtype)
    f = 1. + r2 * (coefK + coefKCubed * r2sqr)

    toReturn[:, 0] *= f
    toReturn[:, 1] *= f

    return toReturn


class infrange():
    """
    Similar to base Python `range`, but allowing the step to be a float or even
    0, useful for specifying ranges for logical comparisons.
    """
    def __init__(self, min, max, step=0):
        self.min = min
        self.max = max
        self.step = step

    @property
    def range(self):
        return abs(self.max-self.min)

    def __lt__(self, other):
        return other > self.max

    def __le__(self, other):
        return other > self.min

    def __gt__(self, other):
        return self.min > other

    def __ge__(self, other):
        return self.max > other

    def __contains__(self, item):
        if self.step == 0:
            return self.min < item < self.max
        else:
            return item in np.linspace(self.min, self.max, int(self.range/self.step)+1)

    def __eq__(self, item):
        if isinstance(item, self.__class__):
            return all((
                self.min == item.min,
                self.max == item.max,
                self.step == item.step
            ))
        return item in self

    def __add__(self, other):
        return self.__class__(self.min+other, self.max+other, self.step)

    def __sub__(self, other):
        return self.__class__(self.min - other, self.max - other, self.step)

    def __mul__(self, other):
        return self.__class__(self.min * other, self.max * other, self.step * other)

    def __truedic__(self, other):
        return self.__class__(self.min / other, self.max / other, self.step / other)


if __name__ == "__main__":
    pass
