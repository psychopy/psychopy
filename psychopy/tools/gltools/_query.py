#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Functions and classes for querying OpenGL.

Functions here allow the user to generate query objects to access rendering
information and GPU timers. This can be used for performance related work, such
as optimization.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'createQueryObject',
    'QueryObjectInfo',
    'beginQuery',
    'endQuery',
    'getQuery',
    'getAbsTimeGPU'
]


import ctypes
import pyglet.gl as GL

# create a query counter to get absolute GPU time
QUERY_COUNTER = None  # prevent genQueries from being called

# -----------------------------------
# GL Query Objects
# -----------------------------------


class QueryObjectInfo(object):
    """Object for querying information. This includes GPU timing information."""
    __slots__ = ['name', 'target']

    def __init__(self, name, target):
        self.name = name
        self.target = target

    def isValid(self):
        """Check if the name associated with this object is valid."""
        return GL.glIsQuery(self.name) == GL.GL_TRUE


def createQueryObject(target=GL.GL_TIME_ELAPSED):
    """Create a GL query object.

    Parameters
    ----------
    target : Glenum or int
        Target for the query.

    Returns
    -------
    QueryObjectInfo
        Query object.

    Examples
    --------

    Get GPU time elapsed executing rendering/GL calls associated with some
    stimuli (this is not the difference in absolute time between consecutive
    `beginQuery` and `endQuery` calls!)::

        # create a new query object
        qGPU = createQueryObject(GL_TIME_ELAPSED)

        beginQuery(query)
        myStim.draw()  # OpenGL calls here
        endQuery(query)

        # get time elapsed in seconds spent on the GPU
        timeRendering = getQueryValue(qGPU) * 1e-9

    You can also use queries to test if vertices are occluded, as their samples
    would be rejected during depth testing::

        drawVAO(shape0, GL_TRIANGLES)  # draw the first object

        # check if the object was completely occluded
        qOcclusion = createQueryObject(GL_ANY_SAMPLES_PASSED)

        # draw the next shape within query context
        beginQuery(qOcclusion)
        drawVAO(shape1, GL_TRIANGLES)  # draw the second object
        endQuery(qOcclusion)

        isOccluded = getQueryValue(qOcclusion) == 1

    This can be leveraged to perform occlusion testing/culling, where you can
    render a `cheap` version of your mesh/shape, then the more expensive version
    if samples were passed.

    """
    result = GL.GLuint()
    GL.glGenQueries(1, ctypes.byref(result))

    return QueryObjectInfo(result, target)


def beginQuery(query):
    """Begin query.

    Parameters
    ----------
    query : QueryObjectInfo
        Query object descriptor returned by :func:`createQueryObject`.

    """
    if isinstance(query, (QueryObjectInfo,)):
        GL.glBeginQuery(query.target, query.name)
    else:
        raise TypeError('Type of `query` must be `QueryObjectInfo`.')


def endQuery(query):
    """End a query.

    Parameters
    ----------
    query : QueryObjectInfo
        Query object descriptor returned by :func:`createQueryObject`,
        previously passed to :func:`beginQuery`.

    """
    if isinstance(query, (QueryObjectInfo,)):
        GL.glEndQuery(query.target)
    else:
        raise TypeError('Type of `query` must be `QueryObjectInfo`.')


def getQuery(query):
    """Get the value stored in a query object.

    Parameters
    ----------
    query : QueryObjectInfo
        Query object descriptor returned by :func:`createQueryObject`,
        previously passed to :func:`endQuery`.

    """
    params = GL.GLuint64(0)
    if isinstance(query, QueryObjectInfo):
        GL.glGetQueryObjectui64v(
            query.name,
            GL.GL_QUERY_RESULT,
            ctypes.byref(params))

        return params.value
    else:
        raise TypeError('Argument `query` must be `QueryObjectInfo` instance.')


def getAbsTimeGPU():
    """Get the absolute GPU time in nanoseconds.

    Returns
    -------
    int
        Time elapsed in nanoseconds since the OpenGL context was fully realized.

    Examples
    --------
    Get the current GPU time in seconds::

        timeInSeconds = getAbsTimeGPU() * 1e-9

    Get the GPU time elapsed::

        t0 = getAbsTimeGPU()
        # some drawing commands here ...
        t1 = getAbsTimeGPU()
        timeElapsed = (t1 - t0) * 1e-9  # take difference, convert to seconds

    """
    global QUERY_COUNTER
    if QUERY_COUNTER is None:
        QUERY_COUNTER = GL.GLuint()
        GL.glGenQueries(1, ctypes.byref(QUERY_COUNTER))

    GL.glQueryCounter(QUERY_COUNTER, GL.GL_TIMESTAMP)

    params = GL.GLuint64(0)
    GL.glGetQueryObjectui64v(
        QUERY_COUNTER,
        GL.GL_QUERY_RESULT,
        ctypes.byref(params))

    return params.value


if __name__ == "__main__":
    pass
