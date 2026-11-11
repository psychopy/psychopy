#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Mapping between positions in a window and on a page drawn in it.

A page is drawn on a rectangle given by a stimulus' `verticesPix`, which
already has its position, size, orientation, anchor and flips applied, in the
order bottom-right, bottom-left, top-left, top-right of the page.
"""

import numpy as np

__all__ = ['windowPixToPage', 'pageToWindowPix']


def _axes(verticesPix):
    """Origin (the page's top-left corner) and the vectors its x and y axes
    run along, across the whole page."""
    verts = np.asarray(verticesPix, dtype=float)
    origin = verts[2]
    return origin, verts[3] - origin, verts[1] - origin


def windowPixToPage(pos, verticesPix, pageSize):
    """Get the position on a page of a position in the window.

    Parameters
    ----------
    pos : ArrayLike
        Position `(x, y)` in the window, in 'pix' units from its center.
    verticesPix : ArrayLike
        Corners of the page in the window, as given by `verticesPix`.
    pageSize : ArrayLike
        Size `(w, h)` of the page in its pixels.

    Returns
    -------
    tuple
        `(x, y, inside)`, the position on the page in its pixels from its
        top-left corner (`y` increasing downwards), and whether it is on the
        page. `x` and `y` are `nan` if the page has no area.

    """
    origin, xAxis, yAxis = _axes(verticesPix)
    axes = np.column_stack((xAxis, yAxis))
    if abs(np.linalg.det(axes)) < 1e-9:
        return float('nan'), float('nan'), False
    u, v = np.linalg.solve(axes, np.asarray(pos, dtype=float) - origin)
    eps = 1e-9  # so the edges are inside despite rounding
    inside = bool(-eps <= u <= 1. + eps and -eps <= v <= 1. + eps)

    return float(u * pageSize[0]), float(v * pageSize[1]), inside


def pageToWindowPix(pagePos, verticesPix, pageSize):
    """Get the position in the window of a position on a page, the inverse of
    `windowPixToPage`.

    Parameters
    ----------
    pagePos : ArrayLike
        Position `(x, y)` on the page in its pixels from its top-left corner.
    verticesPix : ArrayLike
        Corners of the page in the window, as given by `verticesPix`.
    pageSize : ArrayLike
        Size `(w, h)` of the page in its pixels.

    Returns
    -------
    ndarray
        Position `(x, y)` in the window, in 'pix' units from its center.

    """
    origin, xAxis, yAxis = _axes(verticesPix)
    u = pagePos[0] / float(pageSize[0])
    v = pagePos[1] / float(pageSize[1])

    return origin + u * xAxis + v * yAxis
