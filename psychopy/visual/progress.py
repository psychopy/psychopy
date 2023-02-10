from . import shape
from psychopy.tools.attributetools import attributeSetter, setAttribute


class Progress(shape.ShapeStim):
    """
    A basic progress bar, consisting of two rectangles: A background and a foreground. The foreground rectangle
    fill the background as progress approaches 1.

    Parameters
    ==========

    """
    def __init__(
            self, win, name="pb",
            progress=0, direction="horizontal",
            pos=(-.5, 0), size=(1, 0.1), anchor="center left", units=None,
            foreColor="white", backColor=False, lineColor="white", colorSpace=None,
            lineWidth=1.5, opacity=1.0, ori=0.0,
            depth=0, autoLog=None, autoDraw=False,
            # aliases
            fillColor=False
    ):
        # If fillColor given in place of backColor, use it
        if backColor is False and fillColor is not False:
            backColor = fillColor

        # Create backboard
        shape.ShapeStim.__init__(
            self, win, name=name,
            pos=pos, size=size, anchor=anchor, units=units,
            fillColor=backColor, lineColor=lineColor, colorSpace=colorSpace,
            lineWidth=lineWidth, opacity=opacity, ori=ori,
            depth=depth, autoLog=autoLog, autoDraw=autoDraw,
            vertices="rectangle"
        )
        # Create bar
        self.bar = shape.ShapeStim(
            win, name=f"{name}Bar",
            pos=pos, size=size, anchor=anchor, units=units,
            fillColor=foreColor, lineColor=None, colorSpace=colorSpace,
            opacity=opacity, ori=ori,
            depth=depth, autoLog=autoLog, autoDraw=autoDraw,
            vertices="rectangle"
        )
        # Store direction
        self.direction = direction
        self.progress = progress

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

    def setProgress(self, value, log, operation=False):
        setAttribute(self, "progress", value, log=log, operation=operation)

    @staticmethod
    def _sanitizeDirection(direction):
        """
        Take a value indicating direction and convert it to a human readable string
        """
        # Map aliases to direction
        aliases = {
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
        # Ignore case for strings
        if isinstance(direction, str):
            direction = direction.lower().strip()
        # Return sanitized if valid, otherwise assume horizontal
        return aliases.get(direction, default="horizontal")

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

    def draw(self, win=None, keepMatrix=False):
        shape.ShapeStim.draw(self, win=win, keepMatrix=keepMatrix)
        self.bar.draw()
