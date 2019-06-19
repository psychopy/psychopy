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
    """Test if quaternion inversion works. When multiplied, the result should be
    an identity quaternion.

    """
    np.random.seed(123456)
    N = 1000
    axes = np.random.uniform(-1.0, 1.0, (N, 3,))  # random axes
    angles = np.random.uniform(0.0, 360.0, (N,))  # random angles
    qidt = np.array([0., 0., 0., 1.])  # identity quaternion

    for i in range(N):
        # create a quaternion and convert it to a rotation matrix
        q = quatFromAxisAngle(axes[i, :], angles[i], degrees=True)
        qinv = invertQuat(q)
        assert np.allclose(multQuat(q, qinv), qidt)  # is identity?


if __name__ == "__main__":
    pytest.main()
