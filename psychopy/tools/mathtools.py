#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Various math functions for working with vectors, matrices, and quaternions.
#

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
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
           'intersectRayTriangle']

import numpy as np
import functools


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
        dist = np.zeros((v0.shape[0],), dtype=dtype) if out is None else out
        dist[:] = np.sqrt(np.sum(np.square(v1 - v0), axis=1))
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


# ------------------------------------------------------------------------------
# Collision Detection and Interaction
#

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
    # based off example from http://antongerdelan.net/opengl/raycasting.html
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
    sign = np.zeros((3,), dtype=np.int)
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
    # http://www.opengl-tutorial.org/miscellaneous/clicking-on-objects/
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
    """Get the intersection of a ray and signle triangle.

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
    axis : tuple, list or ndarray, optional
        Axis of rotation [x, y, z].
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
    """Get tht multiplicative inverse of a quaternion.

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
        rotQuat = quatFromAxisAngle(axis, angle, degrees=True)
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

    # remove values very close to zero
    toReturn[np.abs(toReturn) <= np.finfo(dtype).eps] = 0.0

    return toReturn


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

    qr, v2d, t2d = np.atleast_2d(toReturn, v,t)

    b = bisector(v2d, t2d, norm=True, dtype=dtype)
    cosHalfAngle = dot(v2d, b, dtype=dtype)

    nonparallel = cosHalfAngle > 0.0 # rotation is not 180 degrees
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
    axis : ndarray, list, or tuple of float
        Axis vector components.
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


def invertMatrix(m, homogeneous=False, out=None, dtype=None):
    """Invert a 4x4 matrix.

    Parameters
    ----------
    m : array_like
        4x4 matrix to invert.
    homogeneous : bool, optional
        Set as ``True`` if the input matrix specifies affine (homogeneous)
        transformations (rotation and translation only). This will use a faster
        inverse method which handles such cases. Default is ``False``.
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
        4x4 matrix which is the inverse of `m`

    """
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
        toReturn = np.zeros((4, 4), dtype=dtype)
    else:
        dtype = out.dtype
        toReturn = out
        toReturn.fill(0.0)

    m = np.asarray(m, dtype=dtype)  # input as array
    assert m.shape == (4, 4,)

    if not homogeneous:
        if not isOrthogonal(m[:3, :3]):
            toReturn[:, :] = np.linalg.inv(m)
        else:
            toReturn[:, :] = m.T
    else:
        toReturn[:3, :3] = m[:3, :3].T
        toReturn[0, 3] = -(m[0, 0] * m[0, 3] + m[1, 0] * m[1, 3] + m[2, 0] * m[2, 3])
        toReturn[1, 3] = -(m[0, 1] * m[0, 3] + m[1, 1] * m[1, 3] + m[2, 1] * m[2, 3])
        toReturn[2, 3] = -(m[0, 2] * m[0, 3] + m[1, 2] * m[1, 3] + m[2, 2] * m[2, 3])
        toReturn[3, 3] = 1.0

    toReturn[np.abs(toReturn) <= np.finfo(dtype).eps] = 0.0  # very small, make zero

    return toReturn


def concatenate(matrices, out=None, dtype=None):
    """Concatenate matrix transformations.

    Combine 4x4 transformation matrices into a single matrix. This is similar to
    what occurs when building a matrix stack in OpenGL using `glRotate`,
    `glTranslate`, and `glScale` calls. Matrices are multiplied together from
    right-to-left, or the last item to first. Note that changing the order of
    the input matrices changes the final result.

    The data types of input matrices are coerced to match that of `out` or
    `dtype` if `out` is `None`. For performance reasons, it is best that all
    arrays passed to this function have matching data types.

    Parameters
    ----------
    matrices : list or tuple
        List of matrices to concatenate. All matrices must be 4x4.
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
        Concatenation of input matrices as a 4x4 matrix in row-major order.

    Examples
    --------
    Create an SRT (scale, rotate, and translate) matrix to convert model-space
    coordinates to world-space::

        S = scaleMatrix([2.0, 2.0, 2.0])  # scale model 2x
        R = rotationMatrix(-90., [0., 0., -1])  # rotate -90 about -Z axis
        T = translationMatrix([0., 0., -5.])  # translate point 5 units away
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
    if out is None:
        dtype = np.float64 if dtype is None else np.dtype(dtype).type
        toReturn = np.zeros((4, 4,), dtype=dtype)
    else:
        dtype = np.dtype(dtype).type
        toReturn = out

    toReturn[:, :] = functools.reduce(
        np.matmul,
        map(lambda x: np.asarray(x, dtype=dtype), reversed(matrices)))

    toReturn[np.abs(toReturn) <= np.finfo(dtype).eps] = 0.0  # very small, make zero

    return toReturn


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
    # from http://www.j3d.org/matrix_faq/matrfaq_latest.html
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

    # very small, make zero
    toReturn[np.abs(toReturn) <= np.finfo(dtype).eps] = 0.0

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

    assert 2 <= m.shape[0] <= 4
    assert m.shape[0] == m.shape[1]

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
    assert m.shape[0] == m.shape[1]

    if not isinstance(m, (np.ndarray,)):
        m = np.asarray(m)

    dtype = np.dtype(m.dtype).type
    eps = np.finfo(dtype).eps

    if np.all(m[3, :3] < eps) and (dtype(1.0) - m[3, 3]) < eps:
        return True

    return False


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

    pout[np.abs(pout) <= np.finfo(dtype).eps] = 0.0  # very small, make zero

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


# ------------------------------------------------------------------------------
# Misc. Math Functions
#

def lensCorrection(xys, coefK=(1.0,), distCenter=(0., 0.), out=None, dtype=None):
    """Lens correction (or distortion) using the division model with even
    polynomial terms.

    Calculate new vertex positions or texture coordinates to apply radial
    warping, such as 'pincushion' and 'barrel' distortion. This is to compensate
    for optical distortion introduced by lenses placed in the optical path of
    the viewer and the display (such as in an HMD).

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

