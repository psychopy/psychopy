#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Functions and classes related to color space conversion
"""
from __future__ import absolute_import, division, print_function

from past.utils import old_div
import numpy

from psychopy import logging
from psychopy.tools.coordinatetools import sph2cart


def dkl2rgb(dkl, conversionMatrix=None):
    """Convert from DKL color space (Derrington, Krauskopf & Lennie) to RGB.

    Requires a conversion matrix, which will be generated from generic
    Sony Trinitron phosphors if not supplied (note that this will not be
    an accurate representation of the color space unless you supply a
    conversion matrix).

    usage::

        rgb(Nx3) = dkl2rgb(dkl_Nx3(el,az,radius), conversionMatrix)
        rgb(NxNx3) = dkl2rgb(dkl_NxNx3(el,az,radius), conversionMatrix)

    """
    if conversionMatrix is None:
        conversionMatrix = numpy.asarray([
            # (note that dkl has to be in cartesian coords first!)
            # LUMIN    %L-M    %L+M-S
            [1.0000, 1.0000, -0.1462],  # R
            [1.0000, -0.3900, 0.2094],  # G
            [1.0000, 0.0180, -1.0000]])  # B
        logging.warning('This monitor has not been color-calibrated. '
                        'Using default DKL conversion matrix.')

    if len(dkl.shape) == 3:
        dkl_NxNx3 = dkl
        # convert a 2D (image) of Spherical DKL colours to RGB space
        origShape = dkl_NxNx3.shape  # remember for later
        NxN = origShape[0] * origShape[1]  # find nPixels
        dkl = numpy.reshape(dkl_NxNx3, [NxN, 3])  # make Nx3
        rgb = dkl2rgb(dkl, conversionMatrix)  # convert
        return numpy.reshape(rgb, origShape)  # reshape and return

    else:
        dkl_Nx3 = dkl
        # its easier to use in the other orientation!
        dkl_3xN = numpy.transpose(dkl_Nx3)
        if numpy.size(dkl_3xN) == 3:
            RG, BY, LUM = sph2cart(dkl_3xN[0],
                                   dkl_3xN[1],
                                   dkl_3xN[2])
        else:
            RG, BY, LUM = sph2cart(dkl_3xN[0, :],
                                   dkl_3xN[1, :],
                                   dkl_3xN[2, :])
        dkl_cartesian = numpy.asarray([LUM, RG, BY])
        rgb = numpy.dot(conversionMatrix, dkl_cartesian)

        # return in the shape we received it:
        return numpy.transpose(rgb)


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


def hsv2rgb(hsv_Nx3):
    """Convert from HSV color space to RGB gun values.

    usage::

        rgb_Nx3 = hsv2rgb(hsv_Nx3)

    Note that in some uses of HSV space the Hue component is given in
    radians or cycles (range 0:1]). In this version H is given in
    degrees (0:360).

    Also note that the RGB output ranges -1:1, in keeping with other
    PsychoPy functions.
    """
    # based on method in
    # http://en.wikipedia.org/wiki/HSL_and_HSV#Converting_to_RGB

    hsv_Nx3 = numpy.asarray(hsv_Nx3, dtype=float)
    # we expect a 2D array so convert there if needed
    origShape = hsv_Nx3.shape
    hsv_Nx3 = hsv_Nx3.reshape([-1, 3])

    H_ = old_div((hsv_Nx3[:, 0] % 360), 60.0)  # this is H' in the wikipedia version
    # multiply H and V to give chroma (color intensity)
    C = hsv_Nx3[:, 1] * hsv_Nx3[:, 2]
    X = C * (1 - abs(H_ % 2 - 1))

    # rgb starts
    rgb = hsv_Nx3 * 0  # only need to change things that are no longer zero
    II = (0 <= H_) * (H_ < 1)
    rgb[II, 0] = C[II]
    rgb[II, 1] = X[II]
    II = (1 <= H_) * (H_ < 2)
    rgb[II, 0] = X[II]
    rgb[II, 1] = C[II]
    II = (2 <= H_) * (H_ < 3)
    rgb[II, 1] = C[II]
    rgb[II, 2] = X[II]
    II = (3 <= H_) * (H_ < 4)
    rgb[II, 1] = X[II]
    rgb[II, 2] = C[II]
    II = (4 <= H_) * (H_ < 5)
    rgb[II, 0] = X[II]
    rgb[II, 2] = C[II]
    II = (5 <= H_) * (H_ < 6)
    rgb[II, 0] = C[II]
    rgb[II, 2] = X[II]
    m = (hsv_Nx3[:, 2] - C)
    rgb += m.reshape([len(m), 1])  # V-C is sometimes called m
    return rgb.reshape(origShape) * 2 - 1


def lms2rgb(lms_Nx3, conversionMatrix=None):
    """Convert from cone space (Long, Medium, Short) to RGB.

    Requires a conversion matrix, which will be generated from generic
    Sony Trinitron phosphors if not supplied (note that you will not get
    an accurate representation of the color space unless you supply a
    conversion matrix)

    usage::

        rgb_Nx3 = lms2rgb(dkl_Nx3(el,az,radius), conversionMatrix)

    """

    # its easier to use in the other orientation!
    lms_3xN = numpy.transpose(lms_Nx3)

    if conversionMatrix is None:
        cones_to_rgb = numpy.asarray([
            # L        M        S
            [4.97068857, -4.14354132, 0.17285275],  # R
            [-0.90913894, 2.15671326, -0.24757432],  # G
            [-0.03976551, -0.14253782, 1.18230333]])  # B

        logging.warning('This monitor has not been color-calibrated. '
                        'Using default LMS conversion matrix.')
    else:
        cones_to_rgb = conversionMatrix

    rgb = numpy.dot(cones_to_rgb, lms_3xN)
    return numpy.transpose(rgb)  # return in the shape we received it


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

    # its easier to use in the other orientation!
    rgb_3xN = numpy.transpose(rgb_Nx3)

    if conversionMatrix is None:
        cones_to_rgb = numpy.asarray([
            # L        M        S
            [4.97068857, -4.14354132, 0.17285275],  # R
            [-0.90913894, 2.15671326, -0.24757432],  # G
            [-0.03976551, -0.14253782, 1.18230333]])  # B

        logging.warning('This monitor has not been color-calibrated. '
                        'Using default LMS conversion matrix.')
    else:
        cones_to_rgb = conversionMatrix
    rgb_to_cones = numpy.linalg.inv(cones_to_rgb)

    lms = numpy.dot(rgb_to_cones, rgb_3xN)
    return numpy.transpose(lms)  # return in the shape we received it
