from .shape import ShapeStim
from .basevisual import ColorMixin, WindowMixin, MinimalStim
from psychopy.colors import Color
from .. import layout

knownStyles = ["circles", "cross", ]


class TargetStim(MinimalStim, ColorMixin, WindowMixin):
    """
    A target for use in eyetracker calibration, if converted to a dict will return in the correct format for ioHub
    """
    def __init__(self,
                 win, name=None, style="circles",
                 radius=.05, fillColor=(1, 1, 1, 0.1), borderColor="white", lineWidth=2,
                 innerRadius=.01, innerFillColor="red", innerBorderColor=None, innerLineWidth=None,
                 pos=(0, 0), units=None, anchor="center",
                 colorSpace="rgb",
                 autoLog=None, autoDraw=False):
        self.win = win
        # Make sure name is a string
        if name is None:
            name = "target"
        # Create shapes
        self.outer = ShapeStim(win, name=name,
                               vertices="circle",
                               size=(radius*2, radius*2), pos=pos,
                               lineWidth=lineWidth, units=units,
                               fillColor=fillColor, lineColor=borderColor, colorSpace=colorSpace,
                               autoLog=autoLog, autoDraw=autoDraw)
        self.outerRadius = radius
        self.inner = ShapeStim(win, name=name+"Inner",
                               vertices="circle",
                               size=(innerRadius*2, innerRadius*2), pos=pos, units=units,
                               lineWidth=(innerLineWidth or lineWidth),
                               fillColor=innerFillColor, lineColor=innerBorderColor, colorSpace=colorSpace,
                               autoLog=autoLog, autoDraw=autoDraw)
        self.innerRadius = innerRadius

        self.style = style
        self.anchor = anchor

    @property
    def style(self):
        if hasattr(self, "_style"):
            return self._style

    @style.setter
    def style(self, value):
        self._style = value
        if value == "circles":
            # Two circles
            self.outer.vertices = self.inner.vertices = "circle"
        elif value == "cross":
            # Circle with a cross inside
            self.outer.vertices = "circle"
            self.inner.vertices = "cross"

    @property
    def anchor(self):
        return self.outer.anchor

    @anchor.setter
    def anchor(self, value):
        self.outer.anchor = value
        self.inner.pos = self.pos + self.size * self.outer._vertices.anchorAdjust

    @property
    def pos(self):
        """For target stims, pos is overloaded so that it moves both the inner and outer shapes."""
        return self.outer.pos

    @pos.setter
    def pos(self, value):
        # Do base pos setting
        WindowMixin.size.fset(self, value)

        self.outer.pos = value
        self.inner.pos = value

    def setPos(self, value):
        self.pos = value

    @property
    def size(self):
        return self.outer.size

    @size.setter
    def size(self, value):
        # Do base size setting
        WindowMixin.size.fset(self, value)
        # Set new sizes
        self.outer.size = value

    @property
    def minSize(self):
        return self.inner.size

    @property
    def units(self):
        if hasattr(self, "outer"):
            return self.outer.units

    @units.setter
    def units(self, value):
        if hasattr(self, "outer"):
            self.outer.units = value
        if hasattr(self, "inner"):
            self.inner.units = value

    @property
    def win(self):
        return WindowMixin.win.fget(self)

    @win.setter
    def win(self, value):
        WindowMixin.win.fset(self, value)
        if hasattr(self, "inner"):
            self.inner.win = value
        if hasattr(self, "outer"):
            self.outer.win = value

    @property
    def lineWidth(self):
        return self.outer.lineWidth

    @lineWidth.setter
    def lineWidth(self, value):
        self.outer.lineWidth = value

    @property
    def radius(self):
        """
        TODO: Deprecate use of radius in favor of using .size
        :return:
        """
        return self.outerRadius

    @radius.setter
    def radius(self, value):
        # Set outer radius
        self.outerRadius = value

    @property
    def outerRadius(self):
        """
        TODO: Deprecate use of outerRadius in favor of using .outer.size
        :return:
        """
        return self.outer.size[1]/2

    @outerRadius.setter
    def outerRadius(self, value):
        # Make buffer object to handle unit conversion
        _buffer = layout.Size((0, value * 2), units=self.units, win=self.win)
        # Use height of buffer object twice, so that size is always square even in norm
        self.outer.size = layout.Size((_buffer.pix[1], _buffer.pix[1]), units='pix', win=self.win)

    @property
    def innerRadius(self):
        """
        TODO: Deprecate use of innerRadius in favor of using .inner.size
        :return:
        """
        return self.inner.size[1] / 2

    @innerRadius.setter
    def innerRadius(self, value):
        # Make buffer object to handle unit conversion
        _buffer = layout.Size((0, value * 2), units=self.units, win=self.win)
        # Use height of buffer object twice, so that size is always square even in norm
        self.inner.size = layout.Size((_buffer.pix[1], _buffer.pix[1]), units='pix', win=self.win)

    @property
    def foreColor(self):
        # Return whichever inner color is not None
        if self.inner.fillColor is not None:
            return self.inner.fillColor
        if self.inner.borderColor is not None:
            return self.inner.borderColor

    @foreColor.setter
    def foreColor(self, value):
        ColorMixin.foreColor.fset(self, value)
        # Set whichever inner color is not None
        if self.inner.fillColor is not None:
            self.inner.fillColor = value
        if self.inner.borderColor is not None:
            self.inner.borderColor = value

    @property
    def borderColor(self):
        return self.outer.borderColor

    @borderColor.setter
    def borderColor(self, value):
        ColorMixin.borderColor.fset(self, value)
        self.outer.borderColor = value

    @property
    def fillColor(self):
        return self.outer.fillColor

    @fillColor.setter
    def fillColor(self, value):
        ColorMixin.fillColor.fset(self, value)
        self.outer.fillColor = value

    @property
    def colorSpace(self):
        return self.outer.colorSpace

    @colorSpace.setter
    def colorSpace(self, value):
        self.outer.colorSpace = value
        self.inner.colorSpace = value

    @property
    def opacity(self):
        return self.outer.opacity

    @opacity.setter
    def opacity(self, value):
        self.outer.opacity = value
        self.inner.opacity = value

    def draw(self, win=None, keepMatrix=False):
        self.outer.draw(win, keepMatrix)
        self.inner.draw(win, keepMatrix)

    def __iter__(self):
        """Overload dict() method to return in ioHub format"""
        # ioHub doesn't treat None as transparent, so we need to handle transparency here
        # For outer circle, use window color as transparent
        fillColor = self.outer.fillColor if self.outer._fillColor else self.win.color
        borderColor = self.outer.borderColor if self.outer._borderColor else self.win.color
        # For inner circle, use outer circle fill as transparent
        innerFillColor = self.inner.fillColor if self.inner._fillColor else fillColor
        innerBorderColor = self.inner.borderColor if self.inner._borderColor else borderColor
        # Assemble dict
        asDict = {
            # Outer circle
            'outer_diameter': self.radius * 2,
            'outer_stroke_width': self.outer.lineWidth,
            'outer_fill_color': fillColor,
            'outer_line_color': borderColor,
            # Inner circle
            'inner_diameter': self.innerRadius * 2,
            'inner_stroke_width': self.inner.lineWidth,
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
               innerRadius=spec['inner_diameter']/2, innerLineWidth=spec['inner_stroke_width'],
               innerFillColor=spec['inner_fill_color'], innerBorderColor=spec['inner_line_color'],
               pos=pos, units=units,
               colorSpace=colorSpace,
               autoLog=autoLog, autoDraw=autoDraw)