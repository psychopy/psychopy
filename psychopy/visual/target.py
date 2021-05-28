from .shape import ShapeStim
from .basevisual import ColorMixin
from psychopy.colors import Color

knownStyles = ["circles", "cross", ]


class TargetStim(ShapeStim):
    """
    A target for use in eyetracker calibration, if converted to a dict will return in the correct format for ioHub
    """
    def __init__(self,
                 win, name=None, style="circles",
                 radius=.05, fillColor=(1, 1, 1, 0.1), borderColor="white", lineWidth=2,
                 innerRadius=.01, innerFillColor="red", innerBorderColor=None, innerLineWidth=None,
                 pos=(0, 0),  units='height',
                 colorSpace="rgb",
                 autoLog=None, autoDraw=False):
        # Init super (creates outer circle)
        ShapeStim.__init__(self, win, name=name,
                           vertices="circle",
                           size=(radius*2, radius*2), pos=pos,
                           lineWidth=lineWidth, units=(units or ''),
                           fillColor=fillColor, lineColor=borderColor, colorSpace=colorSpace,
                           autoLog=autoLog, autoDraw=autoDraw)

        self.inner = ShapeStim(win, name=name+"Inner",
                               vertices="circle",
                               size=(innerRadius*2, innerRadius*2), pos=pos, units=(units or ''),
                               lineWidth=(innerLineWidth or lineWidth),
                               fillColor=innerFillColor, lineColor=innerBorderColor, colorSpace=colorSpace,
                               autoLog=autoLog, autoDraw=autoDraw)
        self.style = style

    @property
    def style(self):
        if hasattr(self, "_style"):
            return self._style

    @style.setter
    def style(self, value):
        self._style = value
        if value == "circles":
            # Two circles
            self.vertices = self.inner.vertices = "circle"
        elif value == "cross":
            # Circle with a cross inside
            self.vertices = "circle"
            self.inner.vertices = "cross"

    @property
    def scale(self):
        if hasattr(self, "_scale"):
            return self._scale
        else:
            return 1

    @property
    def pos(self):
        """For target stims, pos is overloaded so that it moves both the inner and outer shapes."""
        return self._pos

    @pos.setter
    def pos(self, value):
        self._pos = value
        ShapeStim.pos.__set__(self, value)
        if hasattr(self, "inner"):
            self.inner.pos = value

    @scale.setter
    def scale(self, newScale):
        oldScale = self.scale
        self.radius = self.radius / oldScale * newScale
        self._scale = newScale

    @property
    def radius(self):
        return sum(self.size)/2

    @radius.setter
    def radius(self, value):
        self.size = (value*2, value*2)

    @property
    def innerRadius(self):
        return sum(self.inner.size) / 2

    @innerRadius.setter
    def innerRadius(self, value):
        self.inner.size = (value * 2, value * 2)

    @property
    def foreColor(self):
        # Return whichever inner color is not None
        return self.inner.fillColor or self.inner.borderColor

    @foreColor.setter
    def foreColor(self, value):
        # Set whichever inner color is not None
        if self.inner.fillColor is not None:
            self.inner.fillColor = value
        if self.inner.borderColor is not None:
            self.inner.borderColor = value

    def draw(self, win=None, keepMatrix=False):
        ShapeStim.draw(self, win, keepMatrix)
        self.inner.draw(win, keepMatrix)

    def __iter__(self):
        """Overload dict() method to return in ioHub format"""
        # ioHub doesn't treat None as transparent, so we need to handle transparency here
        # For outer circle, use window color as transparent
        fillColor = self.fillColor if self._fillColor else self.win.color
        borderColor = self.borderColor if self._borderColor else self.win.color
        # For inner circle, use outer circle fill as transparent
        innerFillColor = self.inner.fillColor if self.inner._fillColor else fillColor
        innerBorderColor = self.inner.borderColor if self.inner._borderColor else borderColor
        # Assemble dict
        asDict = {
            # Outer circle
            'outer_diameter': self.radius * 2,
            'outer_stroke_width': self.lineWidth,
            'outer_fill_color': fillColor,
            'outer_line_color': borderColor,
            # Inner circle
            'inner_diameter': self.innerRadius * 2,
            'inner_stroke_width': self.lineWidth,
            'inner_fill_color': innerFillColor,
            'inner_line_color': innerBorderColor,
        }
        for key, value in asDict.items():
            yield key, value


def targetFromDict(win, spec,
                   name="target", style="circles",
                   pos=(0, 0), units='height',
                   colorSpace="rgb",
                   autoLog=None, autoDraw=False):
    # Make sure spec has all the required keys, even if it just fills them with None
    required = [
        'outer_diameter', 'outer_stroke_width', 'outer_fill_color', 'outer_line_color',
        'inner_diameter', 'inner_stroke_width', 'inner_fill_color', 'inner_line_color'
    ]
    for key in required:
        if key not in spec:
            spec[key] = None
    # Make a target stim from spec
    TargetStim(win, name=name, style=style,
               radius=spec['outer_diameter']/2, lineWidth=spec['outer_stroke_width'],
               fillColor=spec['outer_fill_color'], borderColor=spec['outer_line_color'],
               innerRadius=spec['outer_diameter']/2, innerLineWidth=spec['inner_stroke_width'],
               innerFillColor=spec['inner_fill_color'], innerBorderColor=spec['inner_line_color'],
               pos=pos, units=units,
               colorSpace=colorSpace,
               autoLog=autoLog, autoDraw=autoDraw)