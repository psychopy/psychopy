#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Functions and classes related to color space conversion.
"""
from __future__ import absolute_import, division, print_function

__all__ = ['srgbTF', 'rec709TF', 'cielab2rgb', 'cielch2rgb', 'dkl2rgb',
           'dklCart2rgb', 'rgb2dklCart', 'hsv2rgb', 'rgb2lms', 'lms2rgb']

import numpy
from psychopy import logging

from psychopy.colors import Color, AdvancedColor, unpackColors, lms2rgb, hsv2rgb, dkl2rgb

def srgbTF(rgb, reverse=False, **kwargs):
    """Apply sRGB transfer function (or gamma) to linear RGB values.

    Input values must have been transformed using a conversion matrix derived
    from sRGB primaries relative to D65.

    Parameters
    ----------
    rgb : tuple, list or ndarray of floats
        Nx3 or NxNx3 array of linear RGB values, last dim must be size == 3
        specifying RBG values.
    reverse : boolean
        If True, the reverse transfer function will convert sRGB -> linear RGB.

    Returns
    -------
    ndarray
        Array of transformed colors with same shape as input.

    """

    col = AdvancedColor(tuple(rgb), 'rgb')
    if len(rgb) == 3:
        return unpackColors(col.srgbTF)
    elif len(rgb) == 4:
        return unpackColors(col.srgbTFa)


def rec709TF(rgb, **kwargs):
    """Apply the Rec. 709 transfer function (or gamma) to linear RGB values.

    This transfer function is defined in the ITU-R BT.709 (2015) recommendation
    document (http://www.itu.int/rec/R-REC-BT.709-6-201506-I/en) and is
    commonly used with HDTV televisions.

    Parameters
    ----------
    rgb : tuple, list or ndarray of floats
        Nx3 or NxNx3 array of linear RGB values, last dim must be size == 3
        specifying RBG values.

    Returns
    -------
    ndarray
        Array of transformed colors with same shape as input.

    """

    col = AdvancedColor(tuple(rgb), 'rgb')
    if len(rgb) == 3:
        return unpackColors(col.rec709TF)
    elif len(rgb) == 4:
        return unpackColors(col.rec709TF)


def cielab2rgb(lab,
               whiteXYZ=None,
               conversionMatrix=None,
               transferFunc=None,
               clip=False,
               **kwargs):
    """Transform CIE L*a*b* (1976) color space coordinates to RGB tristimulus
    values.

    CIE L*a*b* are first transformed into CIE XYZ (1931) color space, then the
    RGB conversion is applied. By default, the sRGB conversion matrix is used
    with a reference D65 white point. You may specify your own RGB conversion
    matrix and white point (in CIE XYZ) appropriate for your display.

    Parameters
    ----------
    lab : tuple, list or ndarray
        1-, 2-, 3-D vector of CIE L*a*b* coordinates to convert. The last
        dimension should be length-3 in all cases specifying a single
        coordinate.
    whiteXYZ : tuple, list or ndarray
        1-D vector coordinate of the white point in CIE-XYZ color space. Must be
        the same white point needed by the conversion matrix. The default
        white point is D65 if None is specified, defined as X, Y, Z = 0.9505,
        1.0000, 1.0890.
    conversionMatrix : tuple, list or ndarray
        3x3 conversion matrix to transform CIE-XYZ to RGB values. The default
        matrix is sRGB with a D65 white point if None is specified. Note that
        values must be gamma corrected to appear correctly according to the sRGB
        standard.
    transferFunc : pyfunc or None
        Signature of the transfer function to use. If None, values are kept as
        linear RGB (it's assumed your display is gamma corrected via the
        hardware CLUT). The TF must be appropriate for the conversion matrix
        supplied (default is sRGB). Additional arguments to 'transferFunc' can
        be passed by specifying them as keyword arguments. Gamma functions that
        come with PsychoPy are 'srgbTF' and 'rec709TF', see their docs for more
        information.
    clip : bool
        Make all output values representable by the display. However, colors
        outside of the display's gamut may not be valid!

    Returns
    -------
    ndarray
        Array of RGB tristimulus values.

    Example
    -------
    Converting a CIE L*a*b* color to linear RGB::

        import psychopy.tools.colorspacetools as cst
        cielabColor = (53.0, -20.0, 0.0)  # greenish color (L*, a*, b*)
        rgbColor = cst.cielab2rgb(cielabColor)

    Using a transfer function to convert to sRGB::

        rgbColor = cst.cielab2rgb(cielabColor, transferFunc=cst.srgbTF)

    """
    lab, orig_shape, orig_dim = unpackColors(lab)

    if conversionMatrix is None:
        # XYZ -> sRGB conversion matrix, assumes D65 white point
        # mdc - computed using makeXYZ2RGB with sRGB primaries
        conversionMatrix = numpy.asmatrix([
            [3.24096994, -1.53738318, -0.49861076],
            [-0.96924364, 1.8759675, 0.04155506],
            [0.05563008, -0.20397696, 1.05697151]
        ])

    if whiteXYZ is None:
        # D65 white point in CIE-XYZ color space
        #   See: https://en.wikipedia.org/wiki/SRGB
        whiteXYZ = numpy.asarray([0.9505, 1.0000, 1.0890])

    L = lab[:, 0]  # lightness
    a = lab[:, 1]  # green (-)  <-> red (+)
    b = lab[:, 2]  # blue (-) <-> yellow (+)
    wht_x, wht_y, wht_z = whiteXYZ  # white point in CIE-XYZ color space

    # convert Lab to CIE-XYZ color space
    # uses reverse transformation found here:
    #   https://en.wikipedia.org/wiki/Lab_color_space
    xyz_array = numpy.zeros(lab.shape)
    s = (L + 16.0) / 116.0
    xyz_array[:, 0] = s + (a / 500.0)
    xyz_array[:, 1] = s
    xyz_array[:, 2] = s - (b / 200.0)

    # evaluate the inverse f-function
    delta = 6.0 / 29.0
    xyz_array = numpy.where(xyz_array > delta,
                            xyz_array ** 3.0,
                            (xyz_array - (4.0 / 29.0)) * (3.0 * delta ** 2.0))

    # multiply in white values
    xyz_array[:, 0] *= wht_x
    xyz_array[:, 1] *= wht_y
    xyz_array[:, 2] *= wht_z

    # convert to sRGB using the specified conversion matrix
    rgb_out = numpy.asarray(numpy.dot(xyz_array, conversionMatrix.T))

    # apply sRGB gamma correction if requested
    if transferFunc is not None:
        rgb_out = transferFunc(rgb_out, **kwargs)

    # clip unrepresentable colors if requested
    if clip:
        rgb_out = numpy.clip(rgb_out, 0.0, 1.0)

    # make the output match the dimensions/shape of input
    if orig_dim == 1:
        rgb_out = rgb_out[0]
    elif orig_dim == 3:
        rgb_out = numpy.reshape(rgb_out, orig_shape)

    return rgb_out * 2.0 - 1.0


def cielch2rgb(lch,
               whiteXYZ=None,
               conversionMatrix=None,
               transferFunc=None,
               clip=False,
               **kwargs):
    """Transform CIE L*C*h* coordinates to RGB tristimulus values.

    Parameters
    ----------
    lch : tuple, list or ndarray
        1-, 2-, 3-D vector of CIE L*C*h* coordinates to convert. The last
        dimension should be length-3 in all cases specifying a single
        coordinate. The hue angle *h is expected in degrees.
    whiteXYZ : tuple, list or ndarray
        1-D vector coordinate of the white point in CIE-XYZ color space. Must be
        the same white point needed by the conversion matrix. The default
        white point is D65 if None is specified, defined as X, Y, Z = 0.9505,
        1.0000, 1.0890
    conversionMatrix : tuple, list or ndarray
        3x3 conversion matrix to transform CIE-XYZ to RGB values. The default
        matrix is sRGB with a D65 white point if None is specified. Note that
        values must be gamma corrected to appear correctly according to the sRGB
        standard.
    transferFunc : pyfunc or None
        Signature of the transfer function to use. If None, values are kept as
        linear RGB (it's assumed your display is gamma corrected via the
        hardware CLUT). The TF must be appropriate for the conversion matrix
        supplied. Additional arguments to 'transferFunc' can be passed by
        specifying them as keyword arguments. Gamma functions that come with
        PsychoPy are 'srgbTF' and 'rec709TF', see their docs for more
        information.
    clip : boolean
        Make all output values representable by the display. However, colors
        outside of the display's gamut may not be valid!

    Returns
    -------
    ndarray
        array of RGB tristimulus values

    """
    lch, orig_shape, orig_dim = unpackColors(lch)

    # convert values to L*a*b*
    lab = numpy.empty(lch.shape, dtype=lch.dtype)
    lab[:, 0] = lch[:, 0]
    lab[:, 1] = lch[:, 1] * numpy.math.cos(numpy.math.radians(lch[:, 2]))
    lab[:, 2] = lch[:, 1] * numpy.math.sin(numpy.math.radians(lch[:, 2]))

    # convert to RGB using the CIE L*a*b* function
    rgb_out = cielab2rgb(lab,
                         whiteXYZ=whiteXYZ,
                         conversionMatrix=conversionMatrix,
                         transferFunc=transferFunc,
                         clip=clip,
                         **kwargs)

    # make the output match the dimensions/shape of input
    if orig_dim == 1:
        rgb_out = rgb_out[0]
    elif orig_dim == 3:
        rgb_out = numpy.reshape(rgb_out, orig_shape)

    return rgb_out  # don't do signed RGB conversion, done by cielab2rgb





def dklCart2rgb(LUM, LM, S, conversionMatrix=None):
    """Like dkl2rgb except that it uses cartesian coords (LM,S,LUM)
    rather than spherical coords for DKL (elev, azim, contr).

    NB: this may return rgb values >1 or <-1
    """
    NxNx3 = list(LUM.shape)
    NxNx3.append(3)
    dkl_cartesian = numpy.asarray(
        [LUM.reshape([-1]), LM.reshape([-1]), S.reshape([-1])])

    if conversionMatrix is None:
        conversionMatrix = numpy.asarray([
            # (note that dkl has to be in cartesian coords first!)
            # LUMIN    %L-M    %L+M-S
            [1.0000, 1.0000, -0.1462],  # R
            [1.0000, -0.3900, 0.2094],  # G
            [1.0000, 0.0180, -1.0000]])  # B
    rgb = numpy.dot(conversionMatrix, dkl_cartesian)
    return numpy.reshape(numpy.transpose(rgb), NxNx3)

def rgb2dklCart(picture, conversionMatrix=None):
    """Convert an RGB image into Cartesian DKL space.
    """
    # Turn the picture into an array so we can do maths
    picture = numpy.array(picture)
    # Find the original dimensions of the picture
    origShape = picture.shape

    # this is the inversion of the dkl2rgb conversion matrix
    if conversionMatrix is None:
        conversionMatrix = numpy.asarray([
            # LUMIN->    %L-M->        L+M-S
            [0.25145542, 0.64933633, 0.09920825],
            [0.78737943, -0.55586618, -0.23151325],
            [0.26562825, 0.63933074, -0.90495899]])
        logging.warning('This monitor has not been color-calibrated. '
                        'Using default DKL conversion matrix.')
    else:
        conversionMatrix = numpy.linalg.inv(conversionMatrix)

    # Reshape the picture so that it can multiplied by the conversion matrix
    red = picture[:, :, 0]
    green = picture[:, :, 1]
    blue = picture[:, :, 2]

    dkl = numpy.asarray([red.reshape([-1]),
                         green.reshape([-1]),
                         blue.reshape([-1])])

    # Multiply the picture by the conversion matrix
    dkl = numpy.dot(conversionMatrix, dkl)

    # Reshape the picture so that it's back to it's original shape
    dklPicture = numpy.reshape(numpy.transpose(dkl), origShape)
    return dklPicture


def rgb2lms(rgb_Nx3, conversionMatrix=None):
    """Convert from RGB to cone space (LMS).

    Requires a conversion matrix, which will be generated from generic
    Sony Trinitron phosphors if not supplied (note that you will not get
    an accurate representation of the color space unless you supply a
    conversion matrix)

    usage::

        lms_Nx3 = rgb2lms(rgb_Nx3(el,az,radius), conversionMatrix)

    """
    col = Color(tuple(rgb_Nx3))
    if len(rgb_Nx3) == 3:
        return unpackColors(col.lms)
    elif len(rgb_Nx3) == 4:
        return unpackColors(col.lms)
