from . import stim3d
from . import ImageStim
from .. import constants
from ..tools import gltools as gt, mathtools as mt, viewtools as vt
import numpy as np
import pyglet.gl as GL
import psychopy.colors as colors

from ..tools.attributetools import attributeSetter, setAttribute


class PanoramicImageStim(ImageStim):
    """Map an image to the inside of a sphere and allow view to be changed via
    latitude and longitude coordinates (between -1 and 1). This is a 
    lazy-imported class, therefore import using full path 
    `from psychopy.visual.panorama import PanoramicImageStim` when inheriting
    from it.


    Parameters
    ----------
    win : psychopy.visual.Window
        The window to draw the stimulus to.
    image : pathlike
        File path of image to present as a panorama. Most modern phones have a
        "panoramic" camera mode,
        which will output an image with all the correct warping applied.
    elevation : float (-1 to 1)
        Initial vertical look position.
    azimuth : float (-1 to 1)
        Initial horizontal look position.

    """
    def __init__(self, win,
                 image=None,
                 elevation=None,
                 azimuth=None,
                 depth=0,
                 interpolate=True,
                 autoDraw=False,
                 name=None,
                 autoLog=False):

        self._initParams = dir()
        self._initParams.remove('self')

        super(PanoramicImageStim, self).__init__(
            win, image=image, units="", interpolate=interpolate, name=name,
            autoLog=autoLog)

        # internal object for storing information pose
        self._thePose = stim3d.RigidBodyPose()

        # Set starting lat- and long-itude
        self.elevation = elevation
        self.azimuth = azimuth
        # Set starting zoom
        self.zoom = 0
        # Set starting status
        self.status = constants.NOT_STARTED
        self.autoDraw = autoDraw
        self.depth = 0
        # Add default attribute for control handler (updated from Builder if used)
        self.ctrl = None

        # generate buffers for vertex data
        vertices, textureCoords, normals, faces = gt.createUVSphere(
            sectors=128,
            stacks=256,
            radius=1.0,
            flipFaces=True)  # faces are on the inside of the sphere

        # flip verts
        vertices = np.ascontiguousarray(
            np.flipud(vertices), dtype=vertices.dtype)

        # flip texture coords to view upright
        textureCoords[:, 0] = np.flipud(textureCoords[:, 0])
        textureCoords = np.ascontiguousarray(
           textureCoords, dtype=textureCoords.dtype)

        # handle to the VAO used to draw the sphere
        self._vao = None
        self._createVAO(vertices, textureCoords, normals, faces)

        # flag if orientation needs an update
        self._needsOriUpdate = True

    def _createVAO(self, vertices, textureCoords, normals, faces):
        """Create a vertex array object for handling vertex attribute data.
        """
        # upload to buffers
        vertexVBO = gt.createVBO(vertices)
        texCoordVBO = gt.createVBO(textureCoords)
        normalsVBO = gt.createVBO(normals)

        # create an index buffer with faces
        indexBuffer = gt.createVBO(
            faces.flatten(),
            target=GL.GL_ELEMENT_ARRAY_BUFFER,
            dataType=GL.GL_UNSIGNED_INT)

        bufferMapping = {
            GL.GL_VERTEX_ARRAY: vertexVBO,
            GL.GL_TEXTURE_COORD_ARRAY: texCoordVBO,
            GL.GL_NORMAL_ARRAY: normalsVBO
        }

        self._vao = gt.createVAO(
            bufferMapping, indexBuffer=indexBuffer, legacy=True)

    @attributeSetter
    def azimuth(self, value):
        """Horizontal view point between -1 (180 degrees to the left) and +1
        (180 degrees to the right). Values outside this range will still be
        accepted (e.g. -1.5 will be 270 degrees to the left).
        """
        if value is None:
            value = 0

        # Store value
        self.__dict__['azimuth'] = self.__dict__['longitude'] = value

        # Shift 90deg left so centre of image is azimuth 0
        value = value + 0.5

        # Get lat and long in degrees
        value = self._normToDegrees(value)

        # Calculate ori
        self.latQuat = mt.quatFromAxisAngle((0, 0, 1), value, degrees=True)
        self._needsOriUpdate = True

    @attributeSetter
    def longitude(self, value):
        """Alias of `azimuth`.
        """
        self.azimuth = value

    def setAzimuth(self, value, operation='', log=False):
        setAttribute(self, "azimuth", value, operation=operation, log=log)

    def setLongitude(self, value, operation='', log=False):
        setAttribute(self, "longitude", value, operation=operation, log=log)

    @attributeSetter
    def elevation(self, value):
        """Vertical view point between -1 (directly downwards) and 1 (directly
        upwards). Values outside this range will be clipped to within range
        (e.g. -1.5 will be directly downwards).
        """
        if value is None:
            value = 0
        # Store value
        value = np.clip(value, -1, 1)
        self.__dict__['elevation'] = self.__dict__['latitude'] = value
        # Force to positive as we only need 180 degrees of rotation, and flip
        value = -value
        value += 1
        value /= 2
        value = np.clip(value, 0, 1)
        # Get lat and long in degrees
        value = self._normToDegrees(value)
        # Calculate ori
        self.longQuat = mt.quatFromAxisAngle((1, 0, 0), value, degrees=True)
        self._needsOriUpdate = True

    @attributeSetter
    def latitude(self, value):
        """Alias of `elevation`.
        """
        self.elevation = value

    def setElevation(self, value, operation='', log=False):
        setAttribute(self, "elevation", value, operation=operation, log=log)

    def setLatitude(self, value, operation='', log=False):
        setAttribute(self, "latitude", value, operation=operation, log=log)

    @attributeSetter
    def zoom(self, value):
        value = max(value, 0)
        self.__dict__['zoom'] = value
        # Modify fov relative to actual view distance (in m)
        self.fov = value + self.win.monitor.getDistance() / 100

    def setZoom(self, value, operation='', log=False):
        setAttribute(self, "zoom", value, operation=operation, log=log)

    @attributeSetter
    def fov(self, value):
        """Set the field-of-view (FOV).
        """
        if 'fov' in self.__dict__ and value == self.__dict__['fov']:
            # Don't recalculate if value hasn't changed
            return

        self.__dict__['fov'] = value
        fov = vt.computeFrustumFOV(
            scrFOV=80,
            scrAspect=self.win.aspect,
            scrDist=value
        )
        self._projectionMatrix = vt.perspectiveProjectionMatrix(*fov)

    def setFov(self, value, operation='', log=False):
        setAttribute(self, "fov", value, operation=operation, log=log)

    def draw(self, win=None):
        # substitute with own win if none given
        if win is None:
            win = self.win
        self._selectWindow(win)

        # check the type of image we're dealing with
        if (type(self.image) != np.ndarray and
                self.image in (None, "None", "none")):
            return

        # check if we need to update the texture
        if self._needTextureUpdate:
            self.setImage(value=self._imName, log=False)

        # Calculate ori from latitude and longitude quats if needed
        if self._needsOriUpdate:
            self._thePose.ori = mt.multQuat(self.longQuat, self.latQuat)
            win.viewMatrix = self._thePose.getViewMatrix(inverse=True)

        # Enter 3d perspective
        win.projectionMatrix = self._projectionMatrix
        win.applyEyeTransform()
        win.useLights = True

        # setup the shaderprogram
        if self.isLumImage:
            # for a luminance image do recoloring
            _prog = self.win._progSignedTexMask
            GL.glUseProgram(_prog)
            # set the texture to be texture unit 0
            GL.glUniform1i(GL.glGetUniformLocation(_prog, b"texture"), 0)
            # mask is texture unit 1
            GL.glUniform1i(GL.glGetUniformLocation(_prog, b"mask"), 1)
        else:
            # for an rgb image there is no recoloring
            _prog = self.win._progImageStim
            GL.glUseProgram(_prog)
            # set the texture to be texture unit 0
            GL.glUniform1i(GL.glGetUniformLocation(_prog, b"texture"), 0)
            # mask is texture unit 1
            GL.glUniform1i(GL.glGetUniformLocation(_prog, b"mask"), 1)

        # mask
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._maskID)
        GL.glEnable(GL.GL_TEXTURE_2D)  # implicitly disables 1D

        # main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        GL.glFrontFace(GL.GL_CW)

        gt.useProgram(self.win._shaders['imageStim'])

        # pass values to OpenGL as material
        r, g, b = self._foreColor.render('rgb')
        color = np.ctypeslib.as_ctypes(
            np.array((r, g, b, 1.0), np.float32))
        GL.glColor4f(*color)

        gt.drawVAO(self._vao, GL.GL_TRIANGLES)

        gt.useProgram(0)

        # unbind the textures
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)  # implicitly disables 1D
        # main texture
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)

        GL.glFrontFace(GL.GL_CW)

        # Exit 3d perspective
        win.useLights = False
        win.resetEyeTransform()

    @staticmethod
    def _normToDegrees(value):
        # Convert to between 0 and 1
        value += 1
        value /= 2
        # Convert to degrees
        value *= 360

        return value

    @staticmethod
    def _degreesToNorm(value):
        # Convert from degrees
        value /= 360
        # Convert to between -1 and 1
        value *= 2
        value -= 1

        return value


if __name__ == "__main__":
    pass
