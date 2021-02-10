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
    """Test the conversion (forward and inverse) for DKL to RGB (signed). This
    does not test for "correctness", but rather if the functions provided for
    the conversion are the inverse of each other.

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


if __name__ == "__main__":
    pytest.main()
