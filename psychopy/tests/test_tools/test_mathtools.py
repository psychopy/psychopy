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
        q0 = quatFromAxisAngle(axes[i, :], angles[i, 0], degrees=True)
        q1 = quatFromAxisAngle(axes[i, :], angles[i, 1], degrees=True)
        quatTarget = quatFromAxisAngle(axes[i, :], totalAngle, degrees=True)

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
        qr = quatToMatrix(q)
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


@pytest.mark.mathtools
def test_transform():
    """Test if `transform` gives the same results as a matrix."""
    np.random.seed(123456)
    N = 1000
    axes = np.random.uniform(-1.0, 1.0, (N, 3,))  # random axes
    angles = np.random.uniform(0.0, 360.0, (N,))  # random angles
    translations = np.random.uniform(-10.0, 10.0, (N, 3,)) # random translations
    points = np.zeros((N, 4,))
    points[:, :3] = np.random.uniform(-10.0, 10.0, (N, 3,))  # random points
    points[:, 3] = 1.0

    for i in range(N):
        ori = quatFromAxisAngle(axes[i, :], angles[i], degrees=True)
        rm = rotationMatrix(angles[i], axes[i, :])
        tm = translationMatrix(translations[i, :])
        m = concatenate([rm, tm])

        tPoint = transform(translations[i, :], ori, points=points[:, :3])
        mPoint = applyMatrix(m, points=points)

        assert np.allclose(tPoint, mPoint[:, :3])  # is identity?


@pytest.mark.mathtools
def test_quatToMatrix():
    """Test converting quaternions to matrices and vice-versa. The end result
    should be the same transformed vectors."""
    np.random.seed(123456)
    N = 1000
    axes = np.random.uniform(-1.0, 1.0, (N, 3,))  # random axes
    angles = np.random.uniform(0.0, 360.0, (N,))  # random angles
    vectors = normalize(np.random.uniform(-1.0, 1.0, (N, 3,)))

    for i in range(N):
        q = matrixToQuat(rotationMatrix(angles[i], normalize(axes[i, :])))
        m = quatToMatrix(quatFromAxisAngle(normalize(axes[i, :]), angles[i]))

        # The returned quaternion might no be the same, but will result in the
        # same rotation.
        assert np.allclose(applyMatrix(m, vectors[i]), applyQuat(q, vectors[i]))


@pytest.mark.mathtools
def test_vectorized():
    """Test vectorization of various functions.

    Test vectorization of math functions by first computing each value in a
    loop, then doing the same computation vectorized.

    """
    np.random.seed(123456)
    N = 1000
    vectors1 = np.random.uniform(-1.0, 1.0, (N, 3,))
    vectors2 = np.random.uniform(-1.0, 1.0, (N, 3,))

    # test normalize() vectorization
    result = np.zeros_like(vectors1)

    for i in range(N):
        result[i, :] = normalize(vectors1[i, :])

    assert np.allclose(normalize(vectors1), result)

    # test length() vectorization
    result = np.zeros((N,))
    for i in range(N):
        result[i] = length(vectors1[i, :])

    assert np.allclose(length(vectors1), result)

    # test dot()
    result = np.zeros((N,))
    for i in range(N):
        result[i] = dot(vectors1[i, :], vectors2[i, :])

    assert np.allclose(dot(vectors1, vectors2), result)

    for i in range(N):
        result[i] = dot(vectors1[0, :], vectors2[i, :])

    assert np.allclose(dot(vectors1[0, :], vectors2), result)

    for i in range(N):
        result[i] = dot(vectors1[i, :], vectors2[0, :])

    assert np.allclose(dot(vectors1, vectors2[0, :]), result)

    # test cross()
    result = np.zeros_like(vectors1)
    for i in range(N):
        result[i, :] = cross(vectors1[i, :], vectors2[i, :])

    assert np.allclose(cross(vectors1, vectors2), result)

    for i in range(N):
        result[i, :] = cross(vectors1[0, :], vectors2[i, :])

    assert np.allclose(cross(vectors1[0, :], vectors2), result)

    for i in range(N):
        result[i, :] = cross(vectors1[i, :], vectors2[0, :])

    assert np.allclose(cross(vectors1, vectors2[0, :]), result)


@pytest.mark.mathtools
def test_alignTo():
    """Test quaternion alignment function `alignTo`. Check general nonparallel
    and parallel cases.

    Tests are successful if the resulting quaternion rotates the initial vector
    to match the target vector.

    """
    np.random.seed(12345)
    N = 1000

    # general use cases
    vec = normalize(np.random.uniform(-1.0, 1.0, (N, 3)))
    target = normalize(np.random.uniform(-1.0, 1.0, (N, 3)))
    qr = alignTo(vec, target)
    out = applyQuat(qr, vec)

    assert np.allclose(out, target)

    # test when rotation is 180 degrees, or vectors are parallel in opposite
    # directions
    target = -vec
    qr = alignTo(vec, target)
    out = applyQuat(qr, vec)

    assert np.allclose(out, target)


if __name__ == "__main__":
    pytest.main()
