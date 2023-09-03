import wx
import wx.ribbon
from psychopy.app.themes import icons, handlers, colors


class FrameRibbon(wx.Panel, handlers.ThemeMixin):
    """
    Similar to a wx.Toolbar but with labelled sections and the option to add any wx.Window as a ctrl.
    """
    def __init__(self, parent):
        # initialize panel
        wx.Panel.__init__(self, parent)
        # setup sizer
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)
        # dict in which to store sections
        self.sections = {}

    def addSection(self, name, label=None):
        """
        Add a section to the ribbon.

        Parameters
        ----------
        name : str
            Name by which to internally refer to this section
        label : str
            Label to display on the section

        Returns
        -------
        FrameRibbonSection
            The created section handle
        """
        # if there are preceeding sections, add a separator
        if len(self.sections):
            self.addSeparator()
        # create section
        self.sections[name] = sct = FrameRibbonSection(
            self, label=label
        )
        # add section to sizer
        self.sizer.Add(sct, border=0, flag=wx.EXPAND | wx.ALL)

        return sct

    def addButton(self, section, name, label="", icon=None, callback=None):
        """
        Add a button to a given section.

        Parameters
        ----------
        section : str
            Name of section to add button to
        name : str
            Name by which to internally refer to this button
        label : str
            Label to display on this button
        icon : str
            Stem of icon to use for this button
        callback : function
            Function to call when this button is clicked

        Returns
        -------
        FrameRibbonButton
            The created button handle
        """
        # if section doesn't exist, make it
        if section not in self.sections:
            self.addSection(section, label=section)
        # call addButton method from given section
        btn = self.sections[section].addButton(
            name, label=label, icon=icon, callback=callback
        )

        return btn

    def addSeparator(self):
        """
        Add a vertical line.
        """
        # make separator
        sep = wx.StaticLine(self, style=wx.LI_VERTICAL)
        # add separator
        self.sizer.Add(sep, border=6, flag=wx.EXPAND | wx.ALL)

    def _applyAppTheme(self):
        self.SetBackgroundColour(colors.app['frame_bg'])


class FrameRibbonSection(wx.Panel, handlers.ThemeMixin):
    """
    Section within a FrameRibbon, containing controls marked by a label.

    Parameters
    ----------
    parent : FrameRibbon
        Ribbon containing this section
    label : str
        Label to display on this section
    """
    def __init__(self, parent, label=None):
        wx.Panel.__init__(self, parent)
        # setup sizers
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.border.Add(
            self.sizer, proportion=1, border=0, flag=wx.EXPAND | wx.ALL
        )
        # add label
        if label is None:
            label = ""
        self.label = wx.StaticText(self, label=label, style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.border.Add(
            self.label, border=0, flag=wx.EXPAND | wx.ALL
        )

        # dict in which to store buttons
        self.buttons = {}

    def addButton(self, name, label="", icon=None, callback=None):
        """
        Add a button to this section.

        Parameters
        ----------
        name : str
            Name by which to internally refer to this button
        label : str
            Label to display on this button
        icon : str
            Stem of icon to use for this button
        callback : function
            Function to call when this button is clicked

        Returns
        -------
        FrameRibbonButton
            The created button handle
        """
        # create button
        self.buttons[name] = btn = FrameRibbonButton(
            self, label=label, icon=icon, callback=callback
        )
        # add button to sizer
        self.sizer.Add(btn, border=0, flag=wx.EXPAND | wx.ALL)

        return btn

    def _applyAppTheme(self):
        self.SetBackgroundColour(colors.app['frame_bg'])


class FrameRibbonButton(wx.Button, handlers.ThemeMixin):
    """
    Button on a FrameRibbon.

    Parameters
    ----------
    parent : FrameRibbonSection
        Section containing this button
    label : str
        Label to display on this button
    icon : str
        Stem of icon to use for this button
    callback : function
        Function to call when this button is clicked
    """
    def __init__(self, parent, label, icon=None, callback=None):
        """

        """
        # initialize
        wx.Button.__init__(self, parent, style=wx.BU_NOTEXT | wx.BORDER_NONE, size=(40, 44))
        # set tooltip
        self.SetToolTipString(label)
        # set icon
        self.SetBitmap(
            icons.ButtonIcon(icon, size=32).bitmap
        )
        # if given, bind callback
        if callback is not None:
            self.Bind(wx.EVT_BUTTON, callback)
        # setup hover behaviour
        self.Bind(wx.EVT_ENTER_WINDOW, self.onHover)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.onHover)

    def _applyAppTheme(self):
        self.SetBackgroundColour(colors.app['frame_bg'])

    def onHover(self, evt):
        if evt.EventType == wx.EVT_ENTER_WINDOW.typeId:
            # on hover, lighten background
            self.SetBackgroundColour(colors.app['panel_bg'])
        else:
            # otherwise, keep same colour as parent
            self.SetBackgroundColour(colors.app['frame_bg'])
