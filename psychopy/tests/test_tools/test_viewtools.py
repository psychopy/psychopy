# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.viewtools
"""

from psychopy.tools.mathtools import (
    alignTo, lookAt, distance, applyQuat, intersectRaySphere, normalize,
    quatToAxisAngle)
from psychopy.tools.viewtools import *
import numpy as np
import pytest


@pytest.mark.viewtools
def test_visualAngle():
    """Test visual angle calculation.

    This tests the visual angle calculation for a few values. The test is
    performed by converting the visual angle back to a distance and checking if
    it is the same as the original distance.

    """
    # test calculation against value computed by hand
    # obj distance = 0.57m, obj size = 0.01m
    assert np.isclose(visualAngle(0.01, 0.57), 1.0051633)  # ~1 degree

    # test input vectorization
    N = 1000
    np.random.seed(12345)
    distances = np.random.uniform(0.1, 100.0, (N,))
    sizes = np.random.uniform(0.01, 10.0, (N,))

    a  = visualAngle(sizes, distances)
    b = visualAngle(sizes, 0.57)
    c = visualAngle(1.0, distances)

    # make sure no values are >180 degrees or less than 0
    assert np.all(a <= 180) and np.all(b <= 180) and np.all(c <= 180)
    assert np.all(a >= 0) and np.all(b >= 0) and np.all(c >= 0)


@pytest.mark.viewtools
def test_viewMatrix():
    """Test view matrix generation.

    This create a view matrix using `lookAt` and `viewMatrix` and checks if
    they look at the same point.

    """
    N = 1000
    np.random.seed(12345)
    targets = np.random.uniform(-100., 100., (N, 3,))
    origin = [0, 0, 0]
    orthoProj = orthoProjectionMatrix(-1, 1, -1, 1, 0.1, 100)

    for i in range(N):
        target = targets[i].tolist()

        # View matrix generation using a quaternion will be canted, but will 
        # center on the same point
        V0 = viewMatrix(origin, alignTo([0, 0, -1], target))
        
        # Use `lookAt` to generate a view matrix, same as `gluLookAt`
        V1 = lookAt(origin, target, [0, 1, 0])

        # Check if the the matricies look at the same point if we project the 
        # target to NDC space. They should both be near the very center of the 
        # screen
        posOut0 = pointToNdc(target, V0, orthoProj)
        posOut1 = pointToNdc(target, V1, orthoProj)

        assert np.isclose(posOut0, posOut1).all()


@pytest.mark.viewtools
def test_projectFrustumToPlane():
    """Test the projection of the frustum to a plane.
    """
    N = 1000
    np.random.seed(12345)
    nearClip = 0.025
    scrDims = np.random.uniform(0.01, 10.0, (N, 2,))
    viewDists = np.random.uniform(nearClip, 10.0, (N,))
    eyeOffsets = np.random.uniform(-0.1, 0.1, (N,))

    for i in range(N):
        scrWidth = scrDims[i, 0]
        scrAspect = scrDims[i, 0] / scrDims[i, 1]
        scrHeight = scrWidth * (1.0 / scrAspect)
        viewDist = viewDists[i]

        farClip = viewDist

        frustum = computeFrustum(
            scrWidth,
            scrAspect,
            viewDist,
            eyeOffset=eyeOffsets[i],
            nearClip=nearClip,
            farClip=farClip)

        frustum = [v.item() for v in frustum]

        topLeft, bottomLeft, _, topRight = projectFrustumToPlane(
            frustum, viewDist)
        
        # should match the screen dimensions
        assert (np.isclose(distance(topLeft, topRight), scrWidth) and 
                np.isclose(distance(topLeft, bottomLeft), scrHeight))


@pytest.mark.viewtools
def test_frustumToProjectionMatrix():
    """Ensure the `computeFrustum` + `perspectiveProjectionMatrix` and
    `generalizedPerspectiveProjection` give similar results, therefore testing
    them both at the same time.

    """
    # random screen parameters
    N = 1000
    np.random.seed(12345)
    scrDims = np.random.uniform(0.01, 10.0, (N, 2,))
    viewDists = np.random.uniform(0.025, 10.0, (N,))
    eyeOffsets = np.random.uniform(-0.1, 0.1, (N,))

    for i in range(N):
        scrWidth = scrDims[i, 0]
        scrAspect = scrDims[i, 0] / scrDims[i, 1]
        viewDist = viewDists[i]

        # nearClip some distance between screen and eye
        nearClip = np.random.uniform(0.001, viewDist, (1,))

        # nearClip some distance beyond screen
        fcMin = viewDist + nearClip
        farClip = np.random.uniform(fcMin, 1000.0, (1,))

        frustum = computeFrustum(
            scrWidth,
            scrAspect,
            viewDist,
            eyeOffset=eyeOffsets[i],
            nearClip=nearClip,
            farClip=farClip)
        
        frustum = [v.item() for v in frustum]  # ensure scalars

        P = perspectiveProjectionMatrix(*frustum)

        # configuration of screen and eyes
        x = scrWidth / 2.
        y = scrDims[i, 1] / 2.0
        z = -viewDist
        posBottomLeft = [-x, -y, z]
        posBottomRight = [x, -y, z]
        posTopLeft = [-x, y, z]
        posEye = [eyeOffsets[i], 0.0, 0.0]

        # create projection and view matrices
        GP, _ = generalizedPerspectiveProjection(posBottomLeft,
                                                 posBottomRight,
                                                 posTopLeft,
                                                 posEye,
                                                 nearClip=nearClip,
                                                 farClip=farClip)

        assert np.allclose(P, GP)


# arcball used by the `getArcballVector` tests, viewed from the origin
_ARCBALL_CENTER = np.array([0., 0., -3.])
_ARCBALL_RADIUS = 1.


@pytest.mark.viewtools
@pytest.mark.parametrize('rayDir', [
    (0., 0., -1.),       # center
    (.2, -.1, -1.),      # off center
    (0., .3, -1.),       # near the edge
    (0., 0., -10.),      # not normalized
])
def test_getArcballVector_hit(rayDir):
    """Rays hitting the arcball give the direction to the near point where they
    hit it."""
    vec = getArcballVector(
        (0., 0., 0.), rayDir, _ARCBALL_CENTER, _ARCBALL_RADIUS)
    point, _ = intersectRaySphere(
        (0., 0., 0.), rayDir, _ARCBALL_CENTER, _ARCBALL_RADIUS)

    assert np.isclose(np.linalg.norm(vec), 1.)
    assert np.allclose(vec, normalize(point - _ARCBALL_CENTER))
    assert vec[2] > 0.  # on the side facing the viewer


@pytest.mark.viewtools
@pytest.mark.parametrize('rayDir, expected', [
    ((1., 0., -1.), (1., 0., 0.)),
    ((-1., 0., -1.), (-1., 0., 0.)),
    ((0., 2., -1.), (0., 1., 0.)),
    ((1., -1., -1.), normalize((1., -1., 0.))),
])
def test_getArcballVector_miss(rayDir, expected):
    """Rays missing the arcball give directions at right angles to the line of
    sight to its center, on the side the ray passes."""
    vec = getArcballVector(
        (0., 0., 0.), rayDir, _ARCBALL_CENTER, _ARCBALL_RADIUS)

    assert np.isclose(np.linalg.norm(vec), 1.)
    assert np.isclose(np.dot(vec, _ARCBALL_CENTER), 0.)  # line of sight
    assert np.allclose(vec, expected)


@pytest.mark.viewtools
@pytest.mark.parametrize('dtype', [np.float32, np.float64])
def test_getArcballVector_away(dtype):
    """A ray pointing directly away from the arcball gives the direction
    towards the ray origin, the same as a ray through the center."""
    for rayOrig in [(0., 0., 0.), (1., 2., 3.)]:
        towardsCenter = _ARCBALL_CENTER - np.asarray(rayOrig)
        vec = getArcballVector(
            rayOrig, -towardsCenter, _ARCBALL_CENTER, _ARCBALL_RADIUS,
            dtype=dtype)
        throughCenter = getArcballVector(
            rayOrig, towardsCenter, _ARCBALL_CENTER, _ARCBALL_RADIUS,
            dtype=dtype)

        assert np.allclose(vec, normalize(-towardsCenter), atol=1e-6)
        assert np.allclose(vec, throughCenter, atol=1e-6)


@pytest.mark.viewtools
def test_getArcballVector_rotation():
    """The rotation between the vectors for two rays hitting the arcball takes
    the point under the first ray to the point under the second, and rays
    missing it rotate around the line of sight."""
    def point(rayDir):
        return intersectRaySphere(
            (0., 0., 0.), rayDir, _ARCBALL_CENTER, _ARCBALL_RADIUS)[0]

    startDir, endDir = (.2, .1, -1.), (-.1, -.2, -1.)
    startVec = getArcballVector(
        (0., 0., 0.), startDir, _ARCBALL_CENTER, _ARCBALL_RADIUS)
    endVec = getArcballVector(
        (0., 0., 0.), endDir, _ARCBALL_CENTER, _ARCBALL_RADIUS)
    rotation = alignTo(startVec, endVec)
    rotated = applyQuat(rotation, point(startDir) - _ARCBALL_CENTER)
    assert np.allclose(rotated + _ARCBALL_CENTER, point(endDir))

    # around the outside, a quarter turn about the line of sight
    startVec = getArcballVector(
        (0., 0., 0.), (1., 0., -1.), _ARCBALL_CENTER, _ARCBALL_RADIUS)
    endVec = getArcballVector(
        (0., 0., 0.), (0., 1., -1.), _ARCBALL_CENTER, _ARCBALL_RADIUS)
    axis, angle = quatToAxisAngle(alignTo(startVec, endVec), degrees=True)
    assert np.allclose(np.abs(axis), (0., 0., 1.))
    assert np.isclose(angle, 90.)


@pytest.mark.viewtools
@pytest.mark.parametrize('dtype', [np.float32, np.float64])
def test_getArcballVector_dtype(dtype):
    for rayDir in [(.2, -.1, -1.), (1., 0., -1.)]:  # hit and miss
        vec = getArcballVector(
            (0., 0., 0.), rayDir, _ARCBALL_CENTER, _ARCBALL_RADIUS,
            dtype=dtype)
        assert vec.dtype == dtype


if __name__ == "__main__":
    pytest.main()
