# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.viewtools
"""

from psychopy.tools.mathtools import alignTo, lookAt, distance
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


if __name__ == "__main__":
    pytest.main()
