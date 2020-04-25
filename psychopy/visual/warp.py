#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes for warping image buffers.

Classes in this module implement several common warping methods, including all
those found in the original `windowwarp.Warper` class. Pass these objects to
`~psychopy.visual.Window.warpBuffer()` to use them.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import numpy as np
import pyglet.gl as GL
import psychopy.tools.gltools as gltools


class BaseWarp(object):
    """Base class for transferring and remapping image data from one buffer onto
    another. This is done by rendering the window's current buffer using a
    textured mesh to the target buffer.

    Subclasses of `BaseWarp` can have additional arguments or properties to
    configure warping.

    """
    def __init__(self, win, viewPos=(0., 0.), viewOri=0.0, viewScale=(1.0, 1.0),
                 flipHorizontal=False, flipVertical=False):
        """
        Parameters
        ----------
        win : `~psychopy.visual.Window`
            Window object. When a warp operation is executed, this object will
            use the buffer presently selected for input.
        viewPos : array_like
            Translation (x, y) for the output.
        viewOri : float
            Rotation angle for the output (degrees).
        viewScale : array_like
            Scaling factor for each dimension of the output.

        """
        self.win = win
        self._viewPos = np.array(viewPos, dtype=np.float32)
        self._viewOri = viewOri
        self._viewScale = np.array(viewScale, dtype=np.float32)
        self._flipHorizontal = flipHorizontal
        self._flipVertical = flipVertical

        # vertex array object for the render mesh
        self._vao = None

    @property
    def viewPos(self):
        return self._viewPos

    @viewPos.setter
    def viewPos(self, value):
        self._viewPos[:] = value

    @property
    def viewOri(self):
        return self._viewOri

    @viewOri.setter
    def viewOri(self, value):
        self._viewOri = value

    @property
    def viewScale(self):
        """Cal"""
        return self._viewScale

    @viewScale.setter
    def viewScale(self, value):
        self._viewScale[:] = value

    def _setupVertexBuffers(self):
        pass

    def _renderFBO(self):
        """Render the warping mesh to the target buffer."""
        pass

    def _prepareFBOrender(self):
        """Setup for the FBO render."""
        pass

    def _finishFBOrender(self):
        """Called to finish up warping."""
        pass

    def _afterFBOrender(self):
        """Called after the warp operation is complete."""
        pass

    def drawWarp(self, targetBuffer='back'):
        """Warp the output. Current buffer must be an off-screen window."""
        pass


class NullWarp(BaseWarp):
    """Null warping class.

    This class transfers the image of the current buffer to another using a
    rectilinear mesh that has the same dimensions as the drawable area of the
    target buffer. If the current and target buffer has the same shape, color
    data is mapped one-to-one.

    """
    def __init__(self, win, viewPos=(0., 0.), viewOri=0.0, viewScale=1.0,
                 flipHorizontal=False, flipVertical=False):
        super(NullWarp, self).__init__(win, viewPos, viewOri, viewScale,
                                       flipHorizontal, flipVertical)
        self._setupVertexBuffers()

    def _setupVertexBuffers(self):
        """Setup the vertex buffers."""
        vertices = ((-1., 1.), (-1., -1.), (1., 1.), (1., -1.))
        texCoord = ((0., 1.), (0., 0.), (1., 1.), (1., 0.))
        attribBuffers = {GL.GL_VERTEX_ARRAY: gltools.createVBO(vertices),
                         GL.GL_TEXTURE_COORD_ARRAY: gltools.createVBO(texCoord)}

        self._vao = gltools.createVAO(attribBuffers, legacy=True)

    def _renderFBO(self):
        """Render the warping mesh to the target buffer. The read buffer should
        be set to the current buffer and the draw buffer to the target buffer.
        After this function returns, the draw buffer should contain the warped
        texture."""
        gltools.drawVAO(self._vao, GL.GL_TRIANGLE_STRIP)

    def _prepareFBOrender(self):
        GL.glUseProgram(self.win._progFBOtoFrame)

    def _finishFBOrender(self):
        GL.glUseProgram(0)

    def _afterFBOrender(self):
        pass


class BaseGridWarp(BaseWarp):
    """Base class for warping classes which use a grid mesh."""
    def __init__(self, win, eyePoint=(0., 0.), warpGridSize=300,
                 viewPos=(0., 0.), viewOri=0.0, viewScale=1.0):
        super(BaseWarp, self).__init__(win, viewPos, viewOri, viewScale)
        self._eyePoint = eyePoint
        self._warpGridSize = warpGridSize


class SphericalWarp(BaseGridWarp):
    """Spherical warping class.
    """
    def __init__(self, win, eyePoint=(0., 0.), warpGridSize=300,
                 viewPos=(0., 0.), viewOri=0.0, viewScale=1.0):
        super(SphericalWarp, self).__init__(win, eyePoint, warpGridSize,
                                            viewPos, viewOri, viewScale)


class CylindricalWarp(BaseGridWarp):
    """Cylindrical warping class.
    """
    def __init__(self, win, eyePoint=(0., 0.), warpGridSize=300,
                 viewPos=(0., 0.), viewOri=0.0, viewScale=1.0):
        super(CylindricalWarp, self).__init__(win, eyePoint, warpGridSize,
                                              viewPos, viewOri, viewScale)


class LensCorrectionWarp(BaseGridWarp):
    """Class for lens correction warping.

    Radial barrel and pincushion distortion results from viewing the display
    through magnifying optical elements (i.e. a lens) causing the image to no
    longer appear rectilinear. To correct for this, the inverse of the
    distortion can be applied to the image on the display to mostly correct for
    the optical distortion.

    """
    def __init__(self, win, eyePoint=(0., 0.), warpGridSize=300,
                 viewPos=(0., 0.), viewOri=0.0, viewScale=1.0):
        super(LensCorrectionWarp, self).__init__(win, eyePoint, warpGridSize,
                                                 viewPos, viewOri, viewScale)

