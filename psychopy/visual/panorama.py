from . import stim3d
from .basevisual import MinimalStim
from .. import constants
from ..tools import gltools as gl, mathtools as mt, viewtools as vt
import numpy as np

from ..tools.attributetools import attributeSetter, setAttribute


class PanoramicImageStim(stim3d.SphereStim, MinimalStim):
    """
    Map an image to the inside of a sphere and allow view to be changed via latitude and longitude
    coordinates (between -1 and 1).

    win : psychopy.visual.Window
        The window to draw the stimulus to.
    image : pathlike
        File path of image to present as a panorama. Most modern phones have a "panoramic" camera mode,
        which will output an image with all the correct warping applied.
    altitude : float (-1 to 1)
        Initial vertical look position.
    azimuth : float (-1 to 1)
        Initial horizontal look position.
    """
    def __init__(self, win,
                 image=None,
                 altitude=None,
                 azimuth=None,
                 depth=0,
                 autoDraw=False,
                 autoLog=False):
        # Create sphere
        stim3d.SphereStim.__init__(
            self, win,
            pos=(0, 0, 0),
            flipFaces=True,
            autoLog=autoLog
        )
        # Create material to host image
        self.material = stim3d.BlinnPhongMaterial(
            win,
            diffuseColor="black",
            specularColor="black",
            emissionColor="white",
            shininess=1
        )
        # Put the panoramic image onto the texture
        self.material.diffuseTexture = gl.createTexImage2dFromFile(image, transpose=False)
        # Set starting lat- and long- itude
        self.altitude = altitude
        self.azimuth = azimuth
        # Set starting zoom
        self.zoom = 0
        # Set starting status
        self.status = constants.NOT_STARTED
        self.autoDraw = autoDraw
        self.depth = 0
        # Add default attribute for control handler (updated from Builder if used)
        self.ctrl = None

    @attributeSetter
    def image(self, value):
        # Store value
        self.__dict__['image'] = value
        # Set texture
        self.material.diffuseTexture = gl.createTexImage2dFromFile(value, transpose=False)

    def setImage(self, value, log=None):
        setAttribute(self, "image", value, log=log)

    @attributeSetter
    def azimuth(self, value):
        """
        Horizontal view point between -1 (180 degrees to the left) and +1 (180 degrees to the right). Values
        outside this range will still be accepted (e.g. -1.5 will be 270 degrees to the left).
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
        """
        Alias of azimuth
        """
        self.azimuth = value

    def setAzimuth(self, value, operation='', log=False):
        setAttribute(self, "azimuth", value, operation=operation, log=log)

    def setLongitude(self, value, operation='', log=False):
        setAttribute(self, "longitude", value, operation=operation, log=log)

    @attributeSetter
    def altitude(self, value):
        """
        Vertical view point between -1 (directly downwards) and 1 (directly upwards). Values outside this range will
        be clipped to within range (e.g. -1.5 will be directly downwards).
        """
        if value is None:
            value = 0
        # Store value
        value = np.clip(value, -1, 1)
        self.__dict__['altitude'] = self.__dict__['latitude'] = value
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
        """
        Alias of altitude
        """
        self.altitude = value

    def setAltitude(self, value, operation='', log=False):
        setAttribute(self, "altitude", value, operation=operation, log=log)

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
        # Substitude with own win if none given
        if win is None:
            win = self.win
        # Enter 3d perspective
        win.projectionMatrix = self._projectionMatrix
        win.applyEyeTransform()
        win.useLights = True
        # Calculate ori from latitude and longitude quats if needed
        if self._needsOriUpdate:
            self.ori = mt.multQuat(self.longQuat, self.latQuat)
        # Do base sphere drawing
        stim3d.SphereStim.draw(self, win=win)
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
