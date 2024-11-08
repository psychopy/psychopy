# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.colorspacetools
"""

from psychopy.tools.colorspacetools import *
import numpy as np
import pytest


@pytest.mark.colorspacetools
def test_rgb2hsv():
    """Test the conversion (forward and inverse) for HSV to RGB (signed). This
    does not test for "correctness", but rather if the functions provided for
    the conversion are the inverse of each other.

    """
    # basic test (Nx3)
    N = 1024
    np.random.seed(123456)
    hsvColors = np.zeros((N, 3))

    hsvColors[:, 0] = np.random.randint(0, 360, (N,))
    hsvColors[:, 1:] = np.random.uniform(0, 1, (N, 2))

    # test conversion back and forth
    hsvOut = rgb2hsv(hsv2rgb(hsvColors))

    assert np.allclose(hsvOut, hsvColors)

    # test if the function can handle pictures
    hsvColors = np.zeros((N, N, 3))
    hsvColors[:, :, 0] = np.random.randint(0, 360, (N, N,))
    hsvColors[:, :, 1:] = np.random.uniform(0, 1, (N, N, 2))

    hsvOut = rgb2hsv(hsv2rgb(hsvColors))

    assert np.allclose(hsvOut, hsvColors)


@pytest.mark.colorspacetools
def test_lms2rgb():
    """Test the conversion (forward and inverse) for LMS to RGB (signed). This
    does not test for "correctness", but rather if the functions provided for
    the conversion are the  inverse of each other.

    """
    N = 1024
    np.random.seed(123456)
    rgbColors = np.random.uniform(-1, 1, (N, 3))

    # test conversion back and forth
    rgbOut = lms2rgb(rgb2lms(rgbColors))

    assert np.allclose(rgbOut, rgbColors)


@pytest.mark.colorspacetools
def test_cartDKL2rgb():
    """Test the conversion (forward and inverse) for cartesian DKL to RGB
    (signed). This does not test for "correctness", but rather if the functions
    provided for the conversion are the inverse of each other.

    """
    N = 1024
    np.random.seed(123456)
    rgbColors = np.random.uniform(-1, 1, (N, N, 3))

    # test conversion, inputs are specified differently between functions
    rgbOut = dklCart2rgb(rgb2dklCart(rgbColors)[:, :, 0],
                         rgb2dklCart(rgbColors)[:, :, 1],
                         rgb2dklCart(rgbColors)[:, :, 2])

    assert np.allclose(rgbOut, rgbColors)


@pytest.mark.colorspacetools
def test_dkl2rgb():
    """Test the conversion (forward) for DKL to RGB (signed).

    """
    N = 1024
    np.random.seed(123456)
    dklColors = np.zeros((N, 3))

    # elevation
    dklColors[:, 0] = np.random.uniform(0, 90, (N,))
    # azimuth
    dklColors[:, 1] = np.random.uniform(0, 360, (N,))
    # radius
    dklColors[:, 2] = np.random.uniform(0, 1, (N,))

    # test conversion using vector input
    _ = dkl2rgb(dklColors)

    # now test with some known colors, just white for now until we generate more
    dklWhite = [90, 0, 1]
    assert np.allclose(np.asarray((1, 1, 1)), dkl2rgb(dklWhite))


@pytest.mark.colorspacetools
def test_srgbTF():
    """Test the sRGB transfer function which converts linear RGB values to
    gamma corrected according to the sRGB standard.

    """
    N = 1024
    np.random.seed(123456)
    rgbColors = np.random.uniform(-1, 1, (N, 3))

    # test conversion, inputs are specified differently between functions
    rgbOut = srgbTF(srgbTF(rgbColors), reverse=True)

    assert np.allclose(rgbOut, rgbColors)


@pytest.mark.colorspacetools
def test_cielch2rgb():
    """Test the CIE-LCh to linear RGB function.
    """
    # preset CIE-LCh colors
    cielchColors = np.array([
        [0.0,    0.0,     0.0],      # black
        [100.0,  0.0,     0.0],      # white
        [53.241, 104.552, 39.999],   # red
        [97.139, 96.905,  102.851],  # yellow
        [87.735, 119.776, 136.016],  # green
        [91.113, 50.121,  196.376],  # cyan
        [32.297, 133.808, 306.285],  # blue
        [60.324, 115.541, 328.235]   # magenta
    ])

    # test conversion using PsyhoPy RGB [-1:1] values
    rgbExpected = np.array([
        [-1.0, -1.0, -1.0],  # black
        [ 1.0,  1.0,  1.0],  # white
        [ 1.0, -1.0, -1.0],  # red
        [ 1.0,  1.0, -1.0],  # yellow
        [-1.0,  1.0, -1.0],  # green
        [-1.0,  1.0,  1.0],  # cyan
        [-1.0, -1.0,  1.0],  # blue
        [ 1.0, -1.0,  1.0]   # magenta
    ])

    # do the conversion
    rgbOutD65 = cielch2rgb(cielchColors)
    assert np.allclose(rgbOutD65, rgbExpected, atol=0.01)


if __name__ == "__main__":
    pytest.main()
