from .polygon import Polygon
from ..event import Mouse
from ..iohub.devices.eyetracker import EyeTrackerDevice


class ROI(Polygon):
    def __init__(self, win, name=None, tracker=None,
                 debug=False,
                 shape="rectangle", vertices=None,
                 units='', pos=(0, 0), size=(1, 1), ori=0.0,
                 autoLog=None):

        # Create red polygon which doesn't draw if `debug == False`
        Polygon.__init__(self, win, name=name,
                         units=units, pos=pos, size=size, ori=0.0,
                         fillColor='red', opacity=int(debug),
                         autoLog=None, autoDraw=debug)
        if tracker is None:
            self.tracker = Mouse(win=win)
        else:
            self.tracker = tracker
        self.wasLookedIn = False
        self.timesOn = []
        self.timesOff = []

    @property
    def numLooks(self):
        """How many times has this ROI been looked at"""
        return len(self.timesOn)

    @property
    def isLookedIn(self):
        if isinstance(self.tracker, Mouse):
            (x, y) = self.tracker.getPos()
        elif isinstance(self.tracker, EyeTrackerDevice):
            (x, y) = self.tracker.getPosition()
        else:
            (x, y) = (0, 0)
        return bool(self.contains(x, y, self.units))
