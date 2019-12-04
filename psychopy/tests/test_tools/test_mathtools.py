# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.mathtools
"""

from psychopy.tools.mathtools import *
from psychopy.tools.viewtools import *
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
def test_length():
    """Test function `length()`."""
    np.random.seed(123456)
    N = 1000
    v = np.random.uniform(-1.0, 1.0, (N, 3,))

    # test Nx2 vectorized input
    result0 = length(v)

    # test writing to another location
    result1 = np.zeros((N,))
    length(v, out=result1)

    assert np.allclose(result0, result1)

    # test squared==True
    result1 = length(v, squared=True)
    assert np.allclose(result0, np.sqrt(result1))

    # test ndim==1
    result1 = np.zeros((N,))
    for i in range(N):
        result1[i] = length(v[i, :])

    assert np.allclose(result0, result1)


@pytest.mark.mathtools
def test_invertMatrix():
    """Test of the `invertMatrix()` function.

    Checks if the function can handle both homogeneous (rotation and translation
    only), general, and view/projection cases.

    All inverses must return something very close to an identity matrix when
    multiplied with the original matrix for a test to succeed.

    """
    np.random.seed(123456)
    N = 1000
    axes = np.random.uniform(-1.0, 1.0, (N, 3,))  # random axes
    angles = np.random.uniform(-180.0, 180.0, (N,))  # random angles
    trans = np.random.uniform(-1000.0, 1000.0, (N, 3,))  # random translations
    scales = np.random.uniform(0.0001, 1000.0, (N, 3,))  # random scales

    # check homogeneous inverse
    ident = np.identity(4)
    for i in range(N):
        r = rotationMatrix(angles[i], axes[i, :])

        assert isOrthogonal(r)

        t = translationMatrix(trans[i, :])

        # combine them
        m = np.matmul(t, r)

        assert isAffine(m)  # must always be TRUE

        inv = invertMatrix(m, homogeneous=True)

        # check if we have identity
        assert np.allclose(np.matmul(inv, m), ident)

    # check non-homogeneous inverse and outputs
    rout = np.zeros((4, 4))
    tout = np.zeros((4, 4))
    sout = np.zeros((4, 4))
    inv = np.zeros((4, 4))
    ident = np.identity(4)
    for i in range(N):
        rotationMatrix(angles[i], axes[i, :], out=rout)

        assert isOrthogonal(rout)

        translationMatrix(trans[i, :], out=tout)
        scaleMatrix(scales[i, :], out=sout)

        # combine them
        m = np.matmul(tout, np.matmul(rout, sout))

        assert isAffine(m)  # must always be TRUE

        invertMatrix(m, out=inv)

        assert np.allclose(np.matmul(inv, m), ident)

    # test with view/projection matrices
    scrDims = np.random.uniform(0.01, 3.0, (N, 2,))
    viewDists = np.random.uniform(0.025, 10.0, (N,))
    eyeOffsets = np.random.uniform(-0.1, 0.1, (N,))

    for i in range(N):
        scrWidth = scrDims[i, 0]
        scrAspect = scrDims[i, 0] / scrDims[i, 1]
        viewDist = viewDists[i]

        # nearClip some distance between screen and eye
        nearClip = np.random.uniform(0.1, viewDist, (1,))

        # nearClip some distance beyond screen
        fcMin = viewDist + nearClip
        farClip = np.random.uniform(fcMin, 1000.0, (1,))

        # get projection matrix
        frustum = computeFrustum(
            scrWidth,
            scrAspect,
            viewDist,
            eyeOffset=eyeOffsets[i],
            nearClip=nearClip,
            farClip=farClip)

        proj = perspectiveProjectionMatrix(*frustum)
        assert not isAffine(proj)

        # create affine view matrix
        r = rotationMatrix(angles[i], axes[i, :])
        assert isOrthogonal(r)

        t = translationMatrix(trans[i, :])
        view = np.matmul(t, r)
        assert isAffine(view)

        # combine them
        vp = np.matmul(proj, view)

        # invert
        inv = invertMatrix(vp)

        assert np.allclose(ident, np.matmul(inv, vp))


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
