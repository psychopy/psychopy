from . import shape
from psychopy.tools.attributetools import attributeSetter, setAttribute

# Aliases for directions
_directionAliases = {
        # Horizontal
        "horizontal": "horizontal",
        "horiz": "horizontal",
        "x": "horizontal",
        "0": "horizontal",
        "False": "horizontal",
        0: "horizontal",
        False: "horizontal",
        # Vertical
        "vertical": "vertical",
        "vert": "vertical",
        "y": "vertical",
        "1": "vertical",
        "True": "vertical",
        1: "vertical",
        True: "vertical",
    }


class Progress(shape.ShapeStim):
    """
    A basic progress bar, consisting of two rectangles: A background and a foreground. The foreground rectangle
    fill the background as progress approaches 1.

    Parameters
    ==========
    win : :class:`~psychopy.visual.Window`
        Window this shape is being drawn to. The stimulus instance will
        allocate its required resources using that Windows context. In many
        cases, a stimulus instance cannot be drawn on different windows
        unless those windows share the same OpenGL context, which permits
        resources to be shared between them.
    name : str
        Name to refer to this Progress bar by
    progress : float
        Value between 0 (not started) and 1 (complete) to set the progress
        bar to.
    direction : str
        Which dimension the bar should fill along, either "horizontal"
        (also accepts "horiz", "x" or 0) or "vertical" (also accepts
        "vert", "y" or 1)
    pos : array_like
        Initial position (`x`, `y`) of the shape on-screen relative to
        the origin located at the center of the window or buffer in `units`.
        This can be updated after initialization by setting the `pos`
        property. The default value is `(0.0, 0.0)` which results in no
        translation.
    size : array_like, float, int or None
        Width and height of the shape as `(w, h)` or `[w, h]`. If a single
        value is provided, the width and height will be set to the same
        specified value. If `None` is specified, the `size` will be set
        with values passed to `width` and `height`.
    anchor : str
        Point within the shape where size and pos are set from. This also
        affects where the progress bar fills up from (e.g. if anchor is
        "left" and direction is "horizontal", then the bar will fill from
        left to right)
    units : str
        Units to use when drawing. This will affect how parameters and
        attributes `pos` and `size` are interpreted.
    barColor, foreColor : array_like, str, :class:`~psychopy.colors.Color` or None
        Color of the full part of the progress bar.
    backColor, fillColor : array_like, str, :class:`~psychopy.colors.Color` or None
        Color of the empty part of the progress bar.
    borderColor, lineColor : array_like, str, :class:`~psychopy.colors.Color` or None
        Color of the outline around the outside of the progress bar.
    colorSpace : str
        Sets the colorspace, changing how values passed to `foreColor`,
        `lineColor` and `fillColor` are interpreted.
    lineWidth : float
        Width of the shape outline.
    opacity : float
        Opacity of the shape. A value of 1.0 indicates fully opaque and 0.0
        is fully transparent (therefore invisible). Values between 1.0 and
        0.0 will result in colors being blended with objects in the
        background.
    """
    def __init__(
            self, win, name="pb",
            progress=0, direction="horizontal",
            pos=(-.5, 0), size=(1, 0.1), anchor="center left", units=None,
            barColor=False, backColor=False, borderColor=False, colorSpace=None,
            lineWidth=1.5, opacity=1.0, ori=0.0,
            depth=0, autoLog=None, autoDraw=False,
            # aliases
            foreColor="white", fillColor=False, lineColor="white",
    ):
        # Alias color names
        if backColor is False and fillColor is not False:
            backColor = fillColor
        if barColor is False and foreColor is not False:
            barColor = foreColor
        if borderColor is False and lineColor is not False:
            borderColor = lineColor


        # Create backboard
        shape.ShapeStim.__init__(
            self, win, name=name,
            pos=pos, size=size, anchor=anchor, units=units,
            fillColor=backColor, lineColor=borderColor, colorSpace=colorSpace,
            lineWidth=lineWidth, opacity=opacity, ori=ori,
            depth=depth, autoLog=autoLog, autoDraw=autoDraw,
            vertices="rectangle"
        )
        # Create bar
        self.bar = shape.ShapeStim(
            win, name=f"{name}Bar",
            pos=pos, size=size, anchor=anchor, units=units,
            fillColor=barColor, lineColor=None, colorSpace=colorSpace,
            opacity=opacity, ori=ori,
            depth=depth, autoLog=autoLog, autoDraw=autoDraw,
            vertices="rectangle"
        )
        # Store direction
        self.direction = direction
        self.progress = progress

    # --- Basic ---

    @attributeSetter
    def progress(self, value):
        """
        How far along the progress bar is

        Parameters
        ==========
        value : float
            Between 0 (not complete) and 1 (fully complete)
        """
        # Sanitize value
        value = float(value)
        value = max(value, 0)
        value = min(value, 1)
        # Store value
        self.__dict__['progress'] = value
        # Multiply size by progress to get bar size
        i = 0
        if self.direction == "vertical":
            i = 1
        sz = self.size.copy()
        sz[i] *= value
        self.bar.size = sz

    def setProgress(self, value, log=None, operation=False):
        setAttribute(self, "progress", value, log=log, operation=operation)

    @attributeSetter
    def direction(self, value):
        """
        What direction is this progress bar progressing in? Use in combination with "anchor"
        to control which direction the bar fills up from.

        Parameters
        ==========
        value : str, int, bool
            Is progress bar horizontal or vertical? Accepts the following values:
            * horizontal: "horizontal", "horiz", "x", "0", "False", 0, False
            * vertical: "vertical", "vert", "y", "1", "True", 1, True
        """
        # Set value (sanitized)
        self.__dict__['direction'] = self._sanitizeDirection(value)

        if not isinstance(self.progress, attributeSetter):
            # Get current progress
            progress = self.progress
            # Set progress to 1 so both dimensions are the same as box size
            self.setProgress(1, log=False)
            # Set progress back to layout
            self.setProgress(progress, log=False)

    def setDirection(self, value, log=None, operation=False):
        setAttribute(self, "direction", value, log=log, operation=operation)

    @staticmethod
    def _sanitizeDirection(direction):
        """
        Take a value indicating direction and convert it to a human readable string
        """
        # Ignore case for strings
        if isinstance(direction, str):
            direction = direction.lower().strip()
        # Return sanitized if valid, otherwise assume horizontal
        return _directionAliases.get(direction, "horizontal")

    @property
    def complete(self):
        return self.progress == 1

    @complete.setter
    def complete(self, value):
        if value:
            # If True, set progress to full
            self.progress = 1
        else:
            # If False and complete, set progress to 0
            if self.progress == 1:
                self.progress = 0

    def setComplete(self, value, log, operation=False):
        setAttribute(self, "complete", value, log=log, operation=operation)

    @property
    def win(self):
        return shape.ShapeStim.win.fget(self)

    @win.setter
    def win(self, value):
        shape.ShapeStim.win.fset(self, value)
        if hasattr(self, "bar"):
            self.bar.win = value

    def draw(self, win=None, keepMatrix=False):
        shape.ShapeStim.draw(self, win=win, keepMatrix=keepMatrix)
        self.bar.draw()

    # --- Appearance ---

    @property
    def barColor(self):
        return self.foreColor

    @barColor.setter
    def barColor(self, value):
        self.foreColor = value

    @property
    def foreColor(self):
        """
        Color of the full part of the progress bar.
        """
        if hasattr(self, "bar"):
            return self.bar.fillColor

    @foreColor.setter
    def foreColor(self, value):
        if hasattr(self, "bar"):
            self.bar.fillColor = value
            # Store bar color as protected attribute, mostly just for the test suite
            self._foreColor = self.bar._fillColor

    @property
    def opacity(self):
        return shape.ShapeStim.opacity.fget(self)

    @opacity.setter
    def opacity(self, value):
        shape.ShapeStim.opacity.fset(self, value)
        if hasattr(self, "bar"):
            self.bar.opacity = value

    @property
    def colorSpace(self):
        return shape.ShapeStim.colorSpace.fget(self)

    @colorSpace.setter
    def colorSpace(self, value):
        # Set color space for self and bar
        shape.ShapeStim.colorSpace.fset(self, value)
        if hasattr(self, "bar"):
            self.bar.colorSpace = value

    # --- Layout ---
    @property
    def pos(self):
        return shape.ShapeStim.pos.fget(self)

    @pos.setter
    def pos(self, value):
        shape.ShapeStim.pos.fset(self, value)
        if hasattr(self, "bar"):
            self.bar.pos = value

    @property
    def size(self):
        return shape.ShapeStim.size.fget(self)

    @size.setter
    def size(self, value):
        shape.ShapeStim.size.fset(self, value)
        if hasattr(self, "bar"):
            self.progress = self.progress

    @property
    def anchor(self):
        return shape.ShapeStim.anchor.fget(self)

    @anchor.setter
    def anchor(self, value):
        shape.ShapeStim.anchor.fset(self, value)
        if hasattr(self, "bar"):
            self.bar.anchor = value

    @property
    def units(self):
        return shape.ShapeStim.units.fget(self)

    @units.setter
    def units(self, value):
        shape.ShapeStim.units.fset(self, value)
        if hasattr(self, "bar"):
            self.bar.units = value

    @attributeSetter
    def ori(self, value):
        shape.ShapeStim.ori.func(self, value)
        if hasattr(self, "bar"):
            self.bar.ori = value
