from psychopy.visual.shape import ShapeStim
from psychopy.visual.slider import Slider
from psychopy.visual.button import ButtonStim


class DropDownCtrl(ButtonStim):
    def __init__(self, win, startValue="", font='Arvo',
                 pos=(0, 0), size=(0.4, 0.2), anchor='center', units=None,
                 color='black', markerColor='lightblue', lineColor='white',
                 padding=None,
                 colorSpace='rgb',
                 labels=("one", "two", "three"),
                 labelHeight=0.04,
                 name="", autoLog=None):
        # Need to flip labels and add blank
        labels = [""] + list(labels)
        labels.reverse()
        self.labels = labels
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
            win, startValue=labels.index(startValue), labels=labels, ticks=list(range(len(labels))),
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
            self.menu.size = self._size * (1, len(self.labels))

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
        self.menu.markerPos = self.labels.index(self.text)
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
        self.menu.rating = self.labels.index(value)

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
            self.text = self.menu.labels[self.menu.rating]
            self.hideMenu()
        # Draw self
        ButtonStim.draw(self)
        # Draw icon
        self.icon.draw()
