#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Functions and classes related to coordinate system conversion
"""
import numpy
from numpy import radians


def cart2pol(x, y, units='deg'):
    """Convert from cartesian to polar coordinates.

    :usage:

        theta, radius = cart2pol(x, y, units='deg')

    units refers to the units (rad or deg) for theta that should be returned
    """
    radius = numpy.hypot(x, y)
    theta = numpy.arctan2(y, x)
    if units in ('deg', 'degs'):
        theta = theta * 180 / numpy.pi
    return theta, radius


def pol2cart(theta, radius, units='deg'):
    """Convert from polar to cartesian coordinates.

    usage::

        x,y = pol2cart(theta, radius, units='deg')

    """
    if units in ('deg', 'degs'):
        theta = theta * numpy.pi / 180.0
    xx = radius * numpy.cos(theta)
    yy = radius * numpy.sin(theta)

    return xx, yy


def cart2sph(z, y, x):
    """Convert from cartesian coordinates (x,y,z) to spherical (elevation,
    azimuth, radius). Output is in degrees.

    usage:
        array3xN[el,az,rad] = cart2sph(array3xN[x,y,z])
        OR
        elevation, azimuth, radius = cart2sph(x,y,z)

        If working in DKL space, z = Luminance, y = S and x = LM
    """
    width = len(z)

    elevation = numpy.empty([width, width])
    radius = numpy.empty([width, width])
    azimuth = numpy.empty([width, width])

    radius = numpy.sqrt(x**2 + y**2 + z**2)
    azimuth = numpy.arctan2(y, x)
    # Calculating the elevation from x,y up
    elevation = numpy.arctan2(z, numpy.sqrt(x**2 + y**2))

    # convert azimuth and elevation angles into degrees
    azimuth *= 180.0 / numpy.pi
    elevation *= 180.0 / numpy.pi

    sphere = numpy.array([elevation, azimuth, radius])
    sphere = numpy.rollaxis(sphere, 0, 3)

    return sphere


def sph2cart(*args):
    """Convert from spherical coordinates (elevation, azimuth, radius)
    to cartesian (x,y,z).

    usage:
        array3xN[x,y,z] = sph2cart(array3xN[el,az,rad])
        OR
        x,y,z = sph2cart(elev, azim, radius)
    """
    if len(args) == 1:  # received an Nx3 array
        elev = args[0][0, :]
        azim = args[0][1, :]
        radius = args[0][2, :]
        returnAsArray = True
    elif len(args) == 3:
        elev = args[0]
        azim = args[1]
        radius = args[2]
        returnAsArray = False

    z = radius * numpy.sin(radians(elev))
    x = radius * numpy.cos(radians(elev)) * numpy.cos(radians(azim))
    y = radius * numpy.cos(radians(elev)) * numpy.sin(radians(azim))
    if returnAsArray:
        return numpy.asarray([x, y, z])
    else:
        return x, y, z
