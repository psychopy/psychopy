from .circle import Circle
from .basevisual import ColorMixin
from psychopy.colors import Color

knownStyles = ["ring", "dot"]

class TargetStim(Circle):
    def __init__(self,
                 win, name=None, style="ring",
                 outerRadius=.05, innerRadius=.01, pos=(0, 0), lineWidth=2, units='height',
                 color="red", fillColor=(1, 1, 1, 0.1), borderColor="white", colorSpace="rgb",
                 autoLog=None, autoDraw=False):
        # Init super (creates outer circle)
        Circle.__init__(self, win, name=name,
                        radius=outerRadius, pos=pos, lineWidth=lineWidth, units=units,
                        fillColor=fillColor, lineColor=borderColor, colorSpace=colorSpace,
                        autoLog=autoLog, autoDraw=autoDraw)
        self._outerRadius = outerRadius
        self._innerRadius = innerRadius
        self._foreColor = Color(color, space=colorSpace)
        self._scale = 1
        self.style = style

    @property
    def style(self):
        if hasattr(self, "_style"):
            return self._style

    @style.setter
    def style(self, value):
        if value == "ring":
            # PsychoPy default style
            self.inner = Circle(self.win, name=self.name + "Inner",
                                radius=self._innerRadius, pos=self.pos, lineWidth=self.lineWidth, units=self.units,
                                fillColor=None, lineColor=self._foreColor, colorSpace=self.colorSpace,
                                autoLog=self.autoLog, autoDraw=self.autoDraw)
            # Keeps track of the attribute of self.inner which self.color corresponds to
            self.inner.colorAttr = "lineColor"
        elif value == "dot":
            # PsychoPy default style
            self.inner = Circle(self.win, name=self.name + "Inner",
                                radius=self._innerRadius, pos=self.pos, lineWidth=self.lineWidth, units=self.units,
                                fillColor=self._foreColor, lineColor=None, colorSpace=self.colorSpace,
                                autoLog=self.autoLog, autoDraw=self.autoDraw)
            # Keeps track of the attribute of self.inner which self.color corresponds to
            self.inner.colorAttr = "fillColor"

    @property
    def innerRadius(self):
        return self.inner.radius

    @innerRadius.setter
    def innerRadius(self, value):
        self.inner.radius = value

    @property
    def outerRadius(self):
        return self.radius

    @outerRadius.setter
    def outerRadius(self, value):
        self.radius = value

    @property
    def scale(self):
        if hasattr(self, "_scale"):
            return self._scale
        else:
            return 1

    @scale.setter
    def scale(self, newScale):
        oldScale = self.scale
        self.outerRadius = self.outerRadius / oldScale * newScale
        self.innerRadius = self.innerRadius / oldScale * newScale
        self._scale = newScale

    @property
    def foreColor(self):
        if hasattr(self, "_foreColor"):
            return self._foreColor

    @foreColor.setter
    def foreColor(self, value):
        self._foreColor = value
        if hasattr(self.inner, "colorAttr"):
            # If self.inner has a colorAttr, set it according to new foreColor value
            setattr(self.inner, self.inner.colorAttr)

    def draw(self, win=None, keepMatrix=False):
        Circle.draw(self, win, keepMatrix)
        self.inner.draw(win, keepMatrix)
