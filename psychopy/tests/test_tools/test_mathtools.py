# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.mathtools
"""

from psychopy.tools.mathtools import *
import numpy as np
import pytest


@pytest.mark.mathtools
def test_mathtoolsDtypes():
    """Make sure that functions are returning the correct dtypes.
    """
    vf32_4x1 = np.asarray([0, 1, 2, 3], dtype=np.float32)
    vf64_4x1 = np.asarray([0, 1, 2, 3], dtype=np.float64)

    assert normalize(vf32_4x1).dtype == np.float32
    assert normalize(vf64_4x1).dtype == np.float64
    assert lerp(vf32_4x1, vf32_4x1, 1.0).dtype == np.float32
    assert lerp(vf64_4x1, vf64_4x1, 1.0).dtype == np.float64
    assert slerp(vf32_4x1, vf32_4x1, 1.0).dtype == np.float32
    assert slerp(vf64_4x1, vf64_4x1, 1.0).dtype == np.float64
    assert multQuat(vf32_4x1, vf32_4x1).dtype == np.float32
    assert multQuat(vf64_4x1, vf64_4x1).dtype == np.float64


@pytest.mark.mathtools
def test_rotationMatrix():
    """Test rotation matrix composition."""
    # identity check
    R = rotationMatrix(0., [0., 0., -1.])
    assert np.allclose(R, np.identity(4))


@pytest.mark.mathtools
def test_quatFromAxisAngle():
    """Test creating a quaternion from `axis` and `angle`."""
    # identity check
    axis = [0., 0., -1.]
    angle = 0.0
    q = quatFromAxisAngle(axis, angle, degrees=True)
    assert np.allclose(q, np.asarray([0., 0., 0., 1.]))


@pytest.mark.mathtools
def test_multQuat():
    """Test quaternion multiplication.

    Create two quaternions, multiply them, and check if the resulting
    orientation is as expected.
    """
    np.random.seed(123456)
    N = 1000
    axes = np.random.uniform(-1.0, 1.0, (N, 3,))  # random axes
    angles = np.random.uniform(0.0, 360.0, (N, 2,))  # random angles

    for i in range(N):
        totalAngle = angles[i, 0] + angles[i, 1]
        q0 = quatFromAxisAngle(
            axes[i, :], angles[i, 0], degrees=True)
        q1 = quatFromAxisAngle(
            axes[i, :], angles[i, 1], degrees=True)
        quatTarget = quatFromAxisAngle(
            axes[i, :], totalAngle, degrees=True)

        assert np.allclose(multQuat(q0, q1), quatTarget)


@pytest.mark.mathtools
def test_matrixFromQuat():
    """Test if a matrix created using `matrixFromQuat` is equivalent to a
    rotation matrix created by `rotationMatrix`.

    """
    # test if quaternion conversions give the same rotation matrices
    np.random.seed(123456)
    N = 1000
    axes = np.random.uniform(-1.0, 1.0, (N, 3,))  # random axes
    angles = np.random.uniform(0.0, 360.0, (N,))  # random angles

    for i in range(N):
        # create a quaternion and convert it to a rotation matrix
        q = quatFromAxisAngle(axes[i, :], angles[i], degrees=True)
        qr = matrixFromQuat(q)
        # create a rotation matrix directly
        rm = rotationMatrix(angles[i], axes[i, :])
        # check if they are close
        assert np.allclose(qr, rm)


@pytest.mark.mathtools
def test_invertQuat():
    """Test quaternion inverse. A quaternion should return the identity if
    multiplied with its inverse.

    """
    np.random.seed(123456)
    N = 1000
    q = np.random.uniform(-1.0, 1.0, (N, 4,))  # random quaternions
    qident = np.array([0., 0., 0., 1.])

    for i in range(N):
        qinv = invertQuat(q[i, :])
        qmult = multQuat(qinv, q[i, :])
        assert np.allclose(qident, qmult)


if __name__ == "__main__":
    pytest.main()
