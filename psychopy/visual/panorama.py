from . import stim3d
from ..tools import gltools as gl, mathtools as mt
import numpy as np


class PanoramicImageStim(stim3d.SphereStim):
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
                 latitude=0,
                 longitude=0):
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
        self.material.diffuseTexture = gl.createTexImage2dFromFile(image)
        # Set starting lat- and long- itude
        self.latitude = latitude
        self.longitude = longitude

    @property
    def latitude(self):
        """
        Horizontal view point between -1 (180 degrees to the left) and +1 (180 degrees to the right).
        """
        # todo: Calculate angle from ori
        if hasattr(self, "_latitude"):
            return self._latitude
        else:
            return 0

    @latitude.setter
    def latitude(self, value):
        value = np.clip(value, -1, 1)
        # Store value
        self._latitude = value
        # Force long to positive as we only need 180 degrees of rotation
        long = self.longitude
        long += 1
        long /= 2
        long = np.clip(value, 0, 1)
        # Get lat and long in degrees
        value = self._normToDegrees(value)
        long = self._normToDegrees(long)
        # Calculate ori
        self.ori = mt.multQuat(
            mt.quatFromAxisAngle((1, 0, 0), value, degrees=True),
            mt.quatFromAxisAngle((0, 0, 1), long, degrees=True),
        )

    @property
    def longitude(self):
        """
        Vertical view point between -1 (directly downwards) and 1 (directly upwards).
        """
        # todo: Calculate angle from ori
        if hasattr(self, "_longitude"):
            return self._longitude
        else:
            return 0

    @longitude.setter
    def longitude(self, value):
        # Store value
        self._longitude = value
        # Force to positive as we only need 180 degrees of rotation
        value += 1
        value /= 2
        value = np.clip(value, 0, 1)
        # Get lat and long in degrees
        value = self._normToDegrees(value)
        lat = self._normToDegrees(self.latitude)
        # Calculate ori
        self.ori = mt.multQuat(
            mt.quatFromAxisAngle((1, 0, 0), value, degrees=True),
            mt.quatFromAxisAngle((0, 0, 1), lat, degrees=True),
        )

    def draw(self, win=None):
        # Substitude with own win if none given
        if win is None:
            win = self.win
        # Enter 3d perspective
        win.setPerspectiveView()
        win.useLights = True
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
