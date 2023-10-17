from psychopy.visual.shape import ShapeStim
from psychopy.visual.slider import Slider
from psychopy.visual.button import ButtonStim


class DropDownCtrl(ButtonStim):
    """
    Class to create a "Drop Down" control, similar to a HTML <select> tag. Consists of a psychopy.visual.ButtonStim
    which, when clicked on, shows a psychopy.visual.Slider with style "choice", which closes again when a value is
    selected. This is a lazy-imported class, therefore import using full path
    `from psychopy.visual.dropdown import DropDownCtrl` when inheriting from it.


    win : psychopy.visual.Window
        Window to draw the control to
    startValue : str
        Which of the available values should be the starting value? Use `""` for no selection
    font : str
        Name of the font to display options in
    pos : tuple, list, np.ndarray, psychopy.layout.Position
        Position of the stimulus on screen
    size : tuple, list, np.ndarray, psychopy.layout.Position
        Size of the persistent control, size of the menu will be calculated according to this size and the number of
        options.
    anchor : str
        Which point on the stimulus should be at the point specified by pos?
    units : str, None
        Spatial units in which to interpret this stimulus' size and position, use None to use the window's units
    color : Color
        Color of the text in the control
    markerColor : Color
        Color of the highlight on the selected element in the drop down menu
    lineColor : Color
        Background color of both the persistent control and drop-down menu. Called "lineColor" for consistency with
        Slider, as the background is technically just a thick line on a Slider.
    colorSpace : str
        Color space in which to interpret stimulus colors
    padding : int, float, tuple
        Padding between edge and text on both the persistent control and each item in the drop down menu.
    choices : tuple, list, np.ndarray
        Options to choose from in the drop down menu
    labelHeight : int, float
        Height of text within both the persistent control and each item in the drop down menu
    name : str
        Name of this stimulus
    autoLog : bool
        Whether or not to log changes to this stimulus automatically
    """
    def __init__(self, win, startValue="", font='Arvo',
                 pos=(0, 0), size=(0.4, 0.2), anchor='center', units=None,
                 color='black', markerColor='lightblue', lineColor='white',
                 colorSpace='rgb',
                 padding=None,
                 choices=("one", "two", "three"),
                 labelHeight=0.04,
                 name="", autoLog=None):
        # Need to flip labels and add blank
        choices = [""] + list(choices)
        choices.reverse()
        self.choices = choices
        # Textbox to display current value
        ButtonStim.__init__(
            self, win, text=startValue, font=font,
            bold=False, name=name,
            letterHeight=labelHeight, padding=padding,
            pos=pos, size=size, anchor=anchor, units=units,
            color=color, fillColor=lineColor, borderColor=None, borderWidth=1, colorSpace=colorSpace,
            autoLog=autoLog
        )
        # Dropdown icon
        self.icon = ShapeStim(win,
                              size=labelHeight / 2,
                              anchor="center right",
                              vertices="triangle",
                              fillColor=color)
        self.icon.flipVert = True
        # Menu object to show when clicked on
        self.menu = Slider(
            win, startValue=choices.index(startValue), labels=choices, ticks=list(range(len(choices))),
            labelColor=color, markerColor=markerColor, lineColor=lineColor,
            colorSpace=colorSpace,
            style="choice", granularity=1, font=font,
            labelHeight=labelHeight, labelWrapWidth=self.size[0]
        )
        self.menu.active = False

        # Set size and pos
        self.size = size
        self.pos = pos

    @property
    def size(self):
        return ButtonStim.size.fget(self)

    @size.setter
    def size(self, value):
        ButtonStim.size.fset(self, value)
        if hasattr(self, "menu"):
            self.menu.size = self._size * (1, len(self.choices))

    @property
    def pos(self):
        return ButtonStim.pos.fget(self)

    @pos.setter
    def pos(self, value):
        ButtonStim.pos.fset(self, value)
        # Set icon pos
        if hasattr(self, "icon"):
            self.icon.pos = (self.contentBox.pos[0] + self.contentBox.size[0] / 2, self.contentBox.pos[1])
        # Set menu pos
        if hasattr(self, "menu"):
            pos = self.pos - (self.size * self._vertices.anchorAdjust)
            pos[1] -= self.menu.size[1] / 2 + self.size[1]
            self.menu.pos = pos

    def showMenu(self, value=True):
        # Show menu
        self.menu.active = value
        # Clear rating
        self.menu.rating = None
        # Set marker pos
        self.menu.markerPos = self.choices.index(self.text)
        # Rotate icon
        self.icon.flipVert = not value

    def hideMenu(self):
        self.showMenu(False)

    @property
    def value(self):
        return self.text

    @value.setter
    def value(self, value):
        if value is None:
            value = ""
        self.menu.rating = self.choices.index(value)

    def draw(self):
        # Check mouse clicks
        if self.isClicked:
            if not self.wasClicked and not self.menu.active:
                # If new click and menu inactive, show menu
                self.showMenu()
            elif not self.wasClicked:
                # If new click and menu active, hide menu
                self.hideMenu()
            # Mark as was clicked
            self.wasClicked = True
        else:
            # Mark as not clicked
            self.wasClicked = False

        # If menu is active, draw it
        if self.menu.active:
            self.menu.draw()
        # Update current value
        if self.menu.rating is not None:
            self.text = self.choices[self.menu.rating]
            self.hideMenu()
        # Draw self
        ButtonStim.draw(self)
        # Draw icon
        self.icon.draw()
