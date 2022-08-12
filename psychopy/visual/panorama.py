from . import stim3d
from .basevisual import MinimalStim
from .. import constants
from ..tools import gltools as gl, mathtools as mt
import numpy as np

from ..tools.attributetools import attributeSetter


class PanoramicImageStim(stim3d.SphereStim, MinimalStim):
    """
    Map an image to the inside of a sphere and allow view to be changed via latitude and longitude
    coordinates (between -1 and 1).

    win : psychopy.visual.Window
        The window to draw the stimulus to.
    image : pathlike
        File path of image to present as a panorama. Most modern phones have a "panoramic" camera mode,
        which will output an image with all the correct warping applied.
    latitude : float (-1 to 1)
        Initial horizontal look position.
    longitude : float (-1 to 1)
        Initial vertical look position.
    """
    def __init__(self, win,
                 image=None,
                 latitude=None,
                 longitude=None,
                 depth=0,
                 autoDraw=False,
                 autoLog=False):
        # Create sphere
        stim3d.SphereStim.__init__(
            self, win,
            pos=(0, 0, 0),
            flipFaces=True
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
        self.latitude = latitude
        self.longitude = longitude
        # Set starting status
        self.status = constants.NOT_STARTED
        self.autoDraw = autoDraw
        self.depth = 0

    @attributeSetter
    def latitude(self, value):
        """
        Horizontal view point between -1 (180 degrees to the left) and +1 (180 degrees to the right).
        """
        if value is None:
            value = 0
        # Store value
        value = np.clip(value, -1, 1)
        self.__dict__['latitude'] = value
        # Get lat and long in degrees
        value = self._normToDegrees(value)
        # Calculate ori
        self.latQuat = mt.quatFromAxisAngle((0, 0, 1), value, degrees=True)
        self._needsOriUpdate = True

    def setLatitude(self, value, log=False):
        self.latitude = value

    @attributeSetter
    def longitude(self, value):
        """
        Vertical view point between -1 (directly downwards) and 1 (directly upwards).
        """
        if value is None:
            value = 0
        # Store value
        value = np.clip(value, -1, 1)
        self.__dict__['longitude'] = value
        # Force to positive as we only need 180 degrees of rotation
        value += 1
        value /= 2
        value = np.clip(value, 0, 1)
        # Get lat and long in degrees
        value = self._normToDegrees(value)
        # Calculate ori
        self.longQuat = mt.quatFromAxisAngle((1, 0, 0), value, degrees=True)
        self._needsOriUpdate = True

    def setLongitude(self, value, log=False):
        self.longitude = value

    def draw(self, win=None):
        # Substitude with own win if none given
        if win is None:
            win = self.win
        # Enter 3d perspective
        win.setPerspectiveView()
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
