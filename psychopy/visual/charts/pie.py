import math

import numpy as np
import pandas as pd

from ..circle import Circle
from psychopy import layout, colors


_defaultColors = {
    0: colors.Color("#EB692A"),  # Orange
    1: colors.Color("#26DCF0"),  # Blue
    2: colors.Color("#F7F11C"),  # Yellow
}


class PieChart(Circle):
    def __init__(
            # Basic
            self, win, data,
            name=None,
            # Layout
            pos=(0, 0), size=None, radius=.5, units=None,
            anchor=None, ori=0.0,
            # Appearance
            colors=None, colorSpace='rgb',
            opacity=None, contrast=1.0, depth=0,
            interpolate=True,
            # Other
            autoLog=None,
            autoDraw=False,
    ):
        # Handle default size
        if size is None:
            size = layout.Size(0.5, 'height', win)
        # Create containing circle
        Circle.__init__(
            # Basic
            self, win,
            # Layout
            pos=pos, size=size, radius=radius, units=units,
            anchor=anchor, ori=ori,
            # Appearance
            fillColor=None, lineColor="red", lineWidth=1,
            edges=360, colorSpace=colorSpace,
            # Other
            autoDraw=False
        )

        self.slices = {}
        self.data = data
        self.colors = colors
        self.update()

    @property
    def data(self):
        if hasattr(self, "_data"):
            return self._data
        else:
            return {}

    @data.setter
    def data(self, value):
        if isinstance(value, (list, tuple, np.ndarray)):
            # If given a list, convert to a dict
            value = {i: val for i, val in enumerate(value)}

        # Convert all values to numeric
        cleaned = {}
        for key in value:
            try:
                cleaned[key] = float(value[key])
            except (ValueError, TypeError):
                raise ValueError(
                    f"Value `{value[key]}` could not be converted to `float`. Values in PieChart data "
                    f"must be numeric."
                )
        # Store value
        self._data = cleaned

    @property
    def colors(self):
        if hasattr(self, "_colors"):
            return self._colors
        else:
            return {}

    @colors.setter
    def colors(self, value):
        if value is None:
            self._colors = {}
            return

        if isinstance(value, (list, tuple, np.ndarray)):
            # If given a list, convert to a dict
            value = {i: val for i, val in enumerate(value)}

        # Convert all values to Color objects
        cleaned = {}
        for key in value:
            try:
                cleaned[key] = colors.Color(value[key], self.colorSpace)
            except (ValueError, TypeError):
                raise ValueError(
                    f"Value `{value[key]}` could not be converted to `float`. Values in PieChart data "
                    f"must be numeric."
                )
        # Store value
        self._colors = cleaned

    def update(self):
        """
        Update appearance of slices to match data
        """
        # Work out total of all data values
        total = sum(list(self.data.values()))
        # Initial start point should be 0
        start = 0
        # Iterate through data
        for i, (key, value) in enumerate(self.data.items()):
            # Get color from either stored array or defaults
            if key in self.colors:
                color = self.colors[key]
            elif i in self.colors:
                color = self.colors[i]
            elif i in _defaultColors:
                color = _defaultColors[i]
            else:
                color = _defaultColors[i % len(_defaultColors)]
            # Check whether we already have a slice for this datum
            if key not in self.slices:
                self.slices[key] = Circle(
                    self.win,
                    autoLog=False,
                    autoDraw=True,
                )
            obj = self.slices[key]
            # Apply color to slice
            obj.fillColor = color
            # Fit to self
            obj.size = self._size
            obj.pos = self._pos
            # Extract vertices from full circle's vertices according to proportion of values
            theta = math.ceil((value / total) * 360)
            stop = start + theta
            if i == 0:
                # Bridge the gap between first and last
                obj.vertices = np.vstack([
                    (0, 0),
                    self.vertices[-1],
                    self.vertices[max(start-1, 0):min(stop+1, 360)],
                    (0, 0)])
            else:
                # Extract appropriate vertices and append the origin
                obj.vertices = np.vstack([
                    (0, 0),
                    self.vertices[max(start-1, 0):min(stop+1, 360)],
                    (0, 0)])


            # Store new start point
            start = stop

    def draw(self, win=None, keepMatrix=False):
        for thisSlice in self.slices.values():
            thisSlice.draw(win=win, keepMatrix=keepMatrix)
