from psychopy.hardware.base import BaseDevice
import pyglet.canvas
import numpy as np

from psychopy.localization import _translate
from psychopy.monitors.calibTools import Monitor


class MonitorDevice(BaseDevice, Monitor):
    """
    A computer monitor (or laptop screen)

    Parameters
    ----------
    index : int
        Numeric index of the monitor, starting at 1
    pos : tuple[int, int], optional
        Pixel position of top left corner of the monitor relative to the full display (top-leftmost 
        point to bottom-rightmost point of all monitors)
    size : tuple[int, int], optional
        Pixel size of the monitor
    frameRate : int, optional
        Number of frame flips per second
    width : float, optional
        Physical width (cm) of the monitor, for calculating positions in cm units
    distance : float, optional
        Distance (cm) between the monitor and the participant, for calculating positions in degrees 
        of visual angle
    gamma : int or numpy.ndarray, optional
        Gamma calibration of this monitor
    """
    
    def __init__(
            self,
            index,
            pos=None,
            size=None,
            frameRate=None,
            width=None,
            distance=None,
            gamma=None,
            otherCalib=None
        ):
        BaseDevice.__init__(self)
        Monitor.__init__(
            self,
            f"Screen {index}",
            width=width,
            distance=distance,
            gamma=gamma,
            currentCalib=otherCalib
        )
        self.setSizePix(size)
        # set attributes not already handled by Monitor
        self.index = index
        self.pos = pos
        self.frameRate = frameRate
    
    @property
    def pyglet(self):
        """
        Returns
        -------
        pyglet.canvas.Screen
            The pyglet object corresponding to this monitor
        """
        if not hasattr(self, "_pyglet"):
            # get all screens
            screens = pyglet.canvas.Display().get_screens()
            # convert index to from-zero with looping
            i = (self.index - 1) % len(screens)
            # store pyglet screen
            self._pyglet = screens[i]
        
        return self._pyglet

    
    def isSameDevice(self, other):
        """
        Determine whether this object represents the same physical device as a given other object.

        Parameters
        ----------
        other : BaseDevice, dict
            Other device object to compare against, or a dict of params.

        Returns
        -------
        bool
            True if the two objects represent the same physical device
        """
        # compare against another MonitorDevice
        if isinstance(other, MonitorDevice):
            return other.index == self.index
        # compare against index
        if isinstance(other, int):
            return other == self.index
        # compare against device profile
        if isinstance(other, dict) and "index" in other:
            return other['index']
        
        return False

    @staticmethod
    def getAvailableDevices():
        """
        Get all available devices of this type.

        Returns
        -------
        list[dict]
            List of dictionaries containing the parameters needed to initialise each device.
        """
        output = []
        # iterate through pyglet screens
        for i, screen in enumerate(pyglet.canvas.Display().get_screens()):
            # get ScreenMode object
            mode = screen.get_mode()
            # construct profile
            output.append({
                'deviceName': f"Screen {i+1} ({screen.width}x{screen.height}px)",
                'deviceClass': "psychopy.hardware.monitor.MonitorDevice",
                'index': i+1,
                'pos': (screen.x, screen.y),
                'size': (screen.width, screen.height),
                'frameRate': mode.rate
            })

        return output