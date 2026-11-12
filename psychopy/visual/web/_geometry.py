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

__all__ = ['windowPixToPage', 'windowPixToPageArray', 'pageToWindowPix']


def _axes(verticesPix):
    """Origin (the page's top-left corner) and the vectors its x and y axes
    run along, across the whole page."""
    verts = np.asarray(verticesPix, dtype=float)
    origin = verts[2]
    return origin, verts[3] - origin, verts[1] - origin


def windowPixToPageArray(pos, verticesPix, pageSize):
    """Get the positions on a page of positions in the window, as
    `windowPixToPage` for many at once.

    Parameters
    ----------
    pos : ArrayLike
        Positions `(N, 2)` in the window, in 'pix' units from its center.
    verticesPix : ArrayLike
        Corners of the page in the window, as given by `verticesPix`.
    pageSize : ArrayLike
        Size `(w, h)` of the page in its pixels.

    Returns
    -------
    tuple
        `(xy, inside)`, the positions `(N, 2)` on the page in its pixels from
        its top-left corner (`y` increasing downwards), and whether each is on
        the page `(N,)`. Positions are `nan` if the page has no area.

    """
    pos = np.asarray(pos, dtype=float).reshape(-1, 2)
    origin, xAxis, yAxis = _axes(verticesPix)
    axes = np.column_stack((xAxis, yAxis))
    if abs(np.linalg.det(axes)) < 1e-9:
        return (np.full(pos.shape, np.nan),
                np.zeros(pos.shape[0], dtype=bool))
    uv = np.linalg.solve(axes, (pos - origin).T).T
    eps = 1e-9  # so the edges are inside despite rounding
    with np.errstate(invalid='ignore'):  # `nan` positions are outside
        inside = np.all((uv >= -eps) & (uv <= 1. + eps), axis=1)

    return uv * np.asarray(pageSize, dtype=float)[:2], inside


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
    xy, inside = windowPixToPageArray(pos, verticesPix, pageSize)

    return float(xy[0, 0]), float(xy[0, 1]), bool(inside[0])


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
