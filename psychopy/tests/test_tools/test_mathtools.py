# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.mathtools
"""

from psychopy.tools.mathtools import *
import numpy as np
import pytest


@pytest.mark.mathtools
def test_rotationMatrix():
    """Test rotation matrix composition."""
    # identity check
    R = rotationMatrix(0., [0., 0., -1.], dtype=np.float64)
    assert np.allclose(R, np.identity(4))


@pytest.mark.mathtools
def test_quatFromAxisAngle():
    """Test creating a quaternion from `axis` and `angle`."""
    # identity check
    axis = [0., 0., -1.]
    angle = 0.0
    q = quatFromAxisAngle(axis, angle, degrees=True, dtype=np.float64)
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
            axes[i, :], angles[i, 0], degrees=True, dtype=np.float64)
        q1 = quatFromAxisAngle(
            axes[i, :], angles[i, 1], degrees=True, dtype=np.float64)
        quatTarget = quatFromAxisAngle(
            axes[i, :], totalAngle, degrees=True, dtype=np.float64)

        assert np.allclose(multQuat(q0, q1, dtype=np.float64), quatTarget)

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
        q = quatFromAxisAngle(axes[i, :], angles[i], degrees=True, dtype=np.float64)
        qr = matrixFromQuat(q, dtype=np.float64)
        # create a rotation matrix directly
        rm = rotationMatrix(angles[i], axes[i, :], dtype=np.float64)
        # check if they are close
        assert np.allclose(qr, rm)


if __name__ == "__main__":
    test_rotationMatrix()
    test_quatFromAxisAngle()
    test_matrixFromQuat()
    test_multQuat()
