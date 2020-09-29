#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Helper functions shared by the visual classes
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, division, print_function

from past.builtins import basestring
from builtins import range
import os
import copy
from pkg_resources import parse_version

from psychopy import logging, colors

# tools must only be imported *after* event or MovieStim breaks on win32
# (JWP has no idea why!)
from psychopy.colors import Color
from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import setAttribute
from psychopy.tools.filetools import pathToString

import numpy as np


reportNImageResizes = 5  # stop raising warning after this
# global _nImageResizes
_nImageResizes = 0

try:
    import matplotlib
    if parse_version(matplotlib.__version__) > parse_version('1.2'):
        from matplotlib.path import Path as mplPath
    else:
        from matplotlib import nxutils
    haveMatplotlib = True
except Exception:
    haveMatplotlib = False


def pointInPolygon(x, y, poly):
    """Determine if a point is inside a polygon; returns True if inside.

    (`x`, `y`) is the point to test. `poly` is a list of 3 or more vertices
    as (x,y) pairs. If given an object, such as a `ShapeStim`, will try to
    use its vertices and position as the polygon.

    Same as the `.contains()` method elsewhere.
    """
    try:  # do this using try:...except rather than hasattr() for speed
        poly = poly.verticesPix  # we want to access this only once
    except Exception:
        pass
    nVert = len(poly)
    if nVert < 3:
        msg = 'pointInPolygon expects a polygon with 3 or more vertices'
        logging.warning(msg)
        return False

    # faster if have matplotlib tools:
    if haveMatplotlib:
        if parse_version(matplotlib.__version__) > parse_version('1.2'):
            return mplPath(poly).contains_point([x, y])
        else:
            try:
                return bool(nxutils.pnpoly(x, y, poly))
            except Exception:
                pass

    # fall through to pure python:
    # adapted from http://local.wasp.uwa.edu.au/~pbourke/geometry/insidepoly/
    # via http://www.ariel.com.au/a/python-point-int-poly.html

    inside = False
    # trace (horizontal?) rays, flip inside status if cross an edge:
    p1x, p1y = poly[-1]
    for p2x, p2y in poly:
        if y > min(p1y, p2y) and y <= max(p1y, p2y) and x <= max(p1x, p2x):
            if p1y != p2y:
                xints = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
            if p1x == p2x or x <= xints:
                inside = not inside
        p1x, p1y = p2x, p2y
    return inside


def polygonsOverlap(poly1, poly2):
    """Determine if two polygons intersect; can fail for very pointy polygons.

    Accepts two polygons, as lists of vertices (x,y) pairs. If given an object
    with with (vertices + pos), will try to use that as the polygon.

    Checks if any vertex of one polygon is inside the other polygon. Same as
    the `.overlaps()` method elsewhere.

    :Notes:

    We implement special handling for the `Line` stimulus as it is not a
    proper polygon.
    We do not check for class instances because this would require importing of
    `visual.Line`, creating a circular import. Instead, we assume that a
    "polygon" with only two vertices is meant to specify a line. Pixels between
    the endpoints get interpolated before testing for overlap.

    """
    try:  # do this using try:...except rather than hasattr() for speed
        if poly1.verticesPix.shape == (2, 2):  # Line
            # Interpolate pixels.
            x = np.arange(poly1.verticesPix[0, 0],
                          poly1.verticesPix[1, 0] + 1)
            y = np.arange(poly1.verticesPix[0, 1],
                          poly1.verticesPix[1, 1] + 1)
            poly1_vert_pix = np.column_stack((x,y))
        else:
            poly1_vert_pix = poly1.verticesPix
    except AttributeError:
        poly1_vert_pix = poly1

    try:  # do this using try:...except rather than hasattr() for speed
        if poly2.verticesPix.shape == (2, 2):  # Line
            # Interpolate pixels.
            x = np.arange(poly2.verticesPix[0, 0],
                          poly2.verticesPix[1, 0] + 1)
            y = np.arange(poly2.verticesPix[0, 1],
                          poly2.verticesPix[1, 1] + 1)
            poly2_vert_pix = np.column_stack((x,y))
        else:
            poly2_vert_pix = poly2.verticesPix
    except AttributeError:
        poly2_vert_pix = poly2

    # faster if have matplotlib tools:
    if haveMatplotlib:
        if parse_version(matplotlib.__version__) > parse_version('1.2'):
            if any(mplPath(poly1_vert_pix).contains_points(poly2_vert_pix)):
                return True
            return any(mplPath(poly2_vert_pix).contains_points(poly1_vert_pix))
        else:
            try:  # deprecated in matplotlib 1.2
                if any(nxutils.points_inside_poly(poly1_vert_pix,
                                                  poly2_vert_pix)):
                    return True
                return any(nxutils.points_inside_poly(poly2_vert_pix,
                                                      poly1_vert_pix))
            except Exception:
                pass

    # fall through to pure python:
    for p1 in poly1_vert_pix:
        if pointInPolygon(p1[0], p1[1], poly2_vert_pix):
            return True
    for p2 in poly2_vert_pix:
        if pointInPolygon(p2[0], p2[1], poly1_vert_pix):
            return True
    return False


def setTexIfNoShaders(obj):
    """Useful decorator for classes that need to update Texture after
    other properties. This doesn't actually perform the update, but sets
    a flag so the update occurs at draw time (in case multiple changes all
    need updates only do it once).
    """
    if hasattr(obj, 'useShaders') and not obj.useShaders:
        # we aren't using shaders
        if hasattr(obj, '_needTextureUpdate'):
            obj._needTextureUpdate = True


def setColor(obj, color, colorSpace='rgb', operation='',
             rgbAttrib='rgb',  # or 'fillRGB' etc
             colorAttrib='color',  # or 'fillColor' etc
             colorSpaceAttrib=None,  # e.g. 'colorSpace' or 'fillColorSpace'
             log=True):
    """Provides the workings needed by setColor, and can perform this for
    any arbitrary color type (e.g. fillColor,lineColor etc).

    OBS: log argument is deprecated - has no effect now.
    Logging should be done when setColor() is called.
    """

    # how this works:
    # rather than using obj.rgb=rgb this function uses setattr(obj,'rgb',rgb)
    # color represents the color in the native space
    # colorAttrib is the name that color will be assigned using
    #   setattr(obj,colorAttrib,color)
    # rgb is calculated from converting color
    # rgbAttrib is the attribute name that rgb is stored under,
    #   e.g. lineRGB for obj.lineRGB
    # colorSpace and takes name from colorAttrib+space e.g.
    # obj.lineRGBSpace=colorSpace

    if colorSpaceAttrib is None:
        colorSpaceAttrib = colorAttrib + 'Space'

    # Convert valid colours
    if isinstance(color, (list, tuple, str)):
        color = Color(color, colorSpace)
    # Convert single integers
    if isinstance(color, (float, int)):
        color = Color((color, color, color), colorSpace)
    # Iterate through arrays
    if isinstance(color, np.ndarray):
        for eachCol in color:
            setColor(obj, eachCol, colorSpace, operation, rgbAttrib, colorAttrib, colorSpaceAttrib, log)
        return
    # Color must be a Color object by now
    if not isinstance(color, Color):
        raise ValueError("color could not be coerced to Color object")

    # Do transformations
    if operation in ('', None):
        pass
    elif operation == '+':
        color = Color(getattr(obj, colorAttrib), colorSpace) + color
    elif operation == '*':
        color = Color(getattr(obj, colorAttrib), colorSpace) * color
    elif operation == '-':
        color = Color(getattr(obj, colorAttrib), colorSpace) - color
    elif operation == '/':
        color = Color(getattr(obj, colorAttrib), colorSpace) / color
    else:
        raise ValueError(f'Unsupported value "{operation}" for operation when setting {colorAttrib} in {colorSpace}')

    setattr(obj, colorSpaceAttrib, colorSpace)
    setattr(obj, colorAttrib, color)

# set for groupFlipVert:
immutables = {int, float, str, tuple, int, bool,
              np.float64, np.float, np.int, np.long}


def findImageFile(filename):
    """Tests whether the filename is an image file. If not will try some common
    alternatives (e.g. extensions .jpg .tif...)
    """
    # if user supplied correct path then reutnr quickly
    filename = pathToString(filename)
    isfile = os.path.isfile
    if isfile(filename):
        return filename
    orig = copy.copy(filename)

    # search for file using additional extensions

    extensions = ('.jpg', '.png', '.tif', '.bmp', '.gif', '.jpeg', '.tiff')
    # not supported: 'svg', 'eps'
    def logCorrected(orig, actual):
        logging.warn("Requested image {!r} not found but similar filename "
                    "{!r} exists. This will be used instead but changing the "
                    "filename is advised.".format(orig, actual))

    # it already has one but maybe it's wrong? Remove it
    if filename.endswith(extensions):
        filename = os.path.splitext(orig)[0]
    if isfile(filename):
        # had an extension but didn't need one (mac?)
        logCorrected(orig, filename)
        return filename

    # try adding the standard set of extensions
    for ext in extensions:
        if isfile(filename+ext):
            filename += ext
            logCorrected(orig, filename)
            return filename

def groupFlipVert(flipList, yReflect=0):
    """Reverses the vertical mirroring of all items in list ``flipList``.

    Reverses the .flipVert status, vertical (y) positions, and angular
    rotation (.ori). Flipping preserves the relations among the group's
    visual elements. The parameter ``yReflect`` is the y-value of an
    imaginary horizontal line around which to reflect the items;
    default = 0 (screen center).

    Typical usage is to call once prior to any display; call again to un-flip.
    Can be called with a list of all stim to be presented in a given routine.

    Will flip a) all psychopy.visual.xyzStim that have a setFlipVert method,
    b) the y values of .vertices, and c) items in n x 2 lists that are mutable
    (i.e., list, np.array, no tuples): [[x1, y1], [x2, y2], ...]
    """

    if type(flipList) != list:
        flipList = [flipList]
    for item in flipList:
        if type(item) in (list, np.ndarray):
            if type(item[0]) in (list, np.ndarray) and len(item[0]) == 2:
                for i in range(len(item)):
                    item[i][1] = 2 * yReflect - item[i][1]
            else:
                msg = 'Cannot vert-flip elements in "{}", type={}'
                raise ValueError(msg.format(item, type(item[0])))
        elif type(item) in immutables:
            raise ValueError('Cannot change immutable item "{}"'.format(item))
        if hasattr(item, 'setPos'):
            item.setPos([1, -1], '*')
            item.setPos([0, 2 * yReflect], '+')
        elif hasattr(item, 'pos'):  # only if no setPos available
            item.pos[1] *= -1
            item.pos[1] += 2 * yReflect
        if hasattr(item, 'setFlipVert'):  # eg TextStim, custom marker
            item.setFlipVert(not item.flipVert)
        elif hasattr(item, 'vertices'):  # and lacks a setFlipVert method
            try:
                v = item.vertices * [1, -1]  # np.array
            except Exception:
                v = [[item.vertices[i][0], -1 * item.vertices[i][1]]
                     for i in range(len(item.vertices))]
            item.setVertices(v)
        if hasattr(item, 'setOri') and item.ori:
            # non-zero orientation angle
            item.setOri(-1, '*')
            item._needVertexUpdate = True
