import numpy as np

from .shape import ShapeStim
from ..event import Mouse
from ..core import Clock


class ROI(ShapeStim):
    """
    A class to handle regions of interest for eyetracking, is essentially a :class:`~psychopy.visual.polygon` but
    with some extra methods and properties for interacting with eyetracking.

    Parameters
    ----------
    win : :class:`~psychopy.visual.Window`
        Window which device position input will be relative to. The stimulus instance will
        allocate its required resources using that Windows context. In many
        cases, a stimulus instance cannot be drawn on different windows
        unless those windows share the same OpenGL context, which permits
        resources to be shared between them.
    name : str
        Optional name of the ROI for logging.
    device : :class:`~psychopy.iohub.devices.eyetracking.EyeTrackerDevice`
        The device which this ROI is getting position data from.
    debug : bool
        If True, then the ROI becomes visible as a red shape on screen. This is intended purely for
        debugging purposes, so that you can see where on screen the ROI is when building an expriment.
    shape : str
        The shape of this ROI, will accept an array of vertices
    pos : array_like
        Initial position (`x`, `y`) of the ROI on-screen relative to the
        origin located at the center of the window or buffer in `units`.
        This can be updated after initialization by setting the `pos`
        property. The default value is `(0.0, 0.0)` which results in no
        translation.
    size : float or array_like
        Initial scale factor for adjusting the size of the ROI. A single
        value (`float`) will apply uniform scaling, while an array (`sx`,
        `sy`) will result in anisotropic scaling in the horizontal (`sx`)
        and vertical (`sy`) direction. Providing negative values to `size`
        will cause the shape being mirrored. Scaling can be changed by
        setting the `size` property after initialization. The default value
        is `1.0` which results in no scaling.
    units : str
        Units to use when drawing. This will affect how parameters and
        attributes `pos`, `size` and `radius` are interpreted.
    ori : float
        Initial orientation of the shape in degrees about its origin.
        Positive values will rotate the shape clockwise, while negative
        values will rotate counterclockwise. The default value for `ori` is
        0.0 degrees.
    isLookedIn : bool
        Returns True if participant is currently looking at the ROI.
    timesOn : list
        List of times when the participant's gaze entered the ROI.
    timesOff : list
        List of times when the participant's gaze left the ROI.
    """

    def __init__(self, win, name=None, device=None,
                 debug=False,
                 shape="rectangle",
                 units='', pos=(0, 0), size=(1, 1), anchor="center", ori=0.0,
                 depth=0, autoLog=None, autoDraw=False):

        # Create red polygon which doesn't draw if `debug == False`
        ShapeStim.__init__(self, win, name=name,
                         units=units, pos=pos, size=size, anchor=anchor, ori=ori,
                         vertices=shape,
                         fillColor='white', lineColor="#F2545B", lineWidth=2, opacity=0.5,
                         autoLog=autoLog, autoDraw=autoDraw)
        self.depth = depth
        self.debug = debug
        if device is None:
            self.device = Mouse(win=win)
        else:
            self.device = device
        self.wasLookedIn = False
        self.clock = Clock()
        self.timesOn = []
        self.timesOff = []

    @property
    def numLooks(self):
        """How many times has this ROI been looked at"""
        return len(self.timesOn)

    @property
    def isLookedIn(self):
        """Is this ROI currently being looked at"""
        try:
            # Get current device position
            if hasattr(self.device, "getPos"):
                pos = self.device.getPos()
            elif hasattr(self.device, "pos"):
                pos = self.device.pos
            else:
                raise AttributeError(f"ROI device ({self.device}) does not have any method for getting position.")
            if not isinstance(pos, (list, tuple, np.ndarray)):
                # If there's no valid device position, assume False
                return False
            # Check contains
            return bool(self.contains(pos[0], pos[1], self.win.units))
        except Exception:
            # If there's an exception getting device position,
            # assume False
            return False
        return False

    @property
    def currentLookTime(self):
        if self.isLookedIn and self.timesOn and self.timesOff:
            # If looked at, subtract most recent time from last time on
            return self.timesOff[-1] - self.timesOn[-1]
        else:
            # If not looked at, look time is 0
            return 0

    @property
    def lastLookTime(self):
        if self.timesOn and self.timesOff and not self.isLookedIn:
            # If not looked at, subtract most recent time from last time on
            return self.timesOff[-1] - self.timesOn[-1]
        elif len(self.timesOn) > 1 and len(self.timesOff) > 1:
            # If looked at, return previous look time
            return self.timesOff[-2] - self.timesOn[-2]
        else:
            # Otherwise, assume 0
            return 0

    def reset(self):
        """Clear stored data"""
        self.timesOn = []
        self.timesOff = []
        self.clock.reset()
        self.wasLookedIn = False

    def draw(self, win=None, keepMatrix=False):
        if self.debug:
            # Only draw if in debug mode
            ShapeStim.draw(self, win=win, keepMatrix=keepMatrix)
