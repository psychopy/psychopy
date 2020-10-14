# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.viewtools
"""

from psychopy.tools.viewtools import *
import numpy as np
import pytest


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
