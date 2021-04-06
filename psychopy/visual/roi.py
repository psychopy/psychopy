from .polygon import Polygon
from pandas import DataFrame

from ..event import Mouse


class ROI(Polygon):
    def __init__(self, win, name=None,
                 debug=False,
                 shape="rectangle", vertices=None,
                 units='', pos=(0, 0), size=(1, 1), ori=0.0,
                 autoLog=None):

        # Create red polygon which doesn't draw if `debug == False`
        Polygon.__init__(self, win, name=name,
                         units=units, pos=pos, size=size, ori=0.0,
                         fillColor='red', opacity=int(debug),
                         autoLog=None, autoDraw=debug)

        self.tracker = Mouse(win=win)
        self.wasLookedIn = False
        self.timesOn = []
        self.timesOff = []

    @property
    def numLooks(self):
        """How many times has this ROI been looked at"""
        return len(self.timesOn)

    @property
    def isLookedIn(self):
        (x, y) = self.tracker.getPos()
        print(bool(self.contains(x, y, self.units)))
        return bool(self.contains(x, y, self.units))
