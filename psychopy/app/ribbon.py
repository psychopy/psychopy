import sys
import webbrowser
from pathlib import Path

import numpy
import requests
import wx

from psychopy.app import utils
from psychopy.app import pavlovia_ui as pavui
from psychopy.app.pavlovia_ui import sync
from psychopy.app.themes import icons, handlers, colors
from psychopy.localization import _translate
from psychopy.projects import pavlovia


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
        # dicts in which to store sections and buttons
        self.sections = {}
        self.buttons = {}

    def addSection(self, name, label=None, icon=None):
        """
        Add a section to the ribbon.

        Parameters
        ----------
        name : str
            Name by which to internally refer to this section
        label : str
            Label to display on the section
        icon : str or None
            File stem of the icon for the section's label

        Returns
        -------
        FrameRibbonSection
            The created section handle
        """
        # create section
        self.sections[name] = sct = FrameRibbonSection(
            self, label=label, icon=icon
        )
        # add section to sizer
        self.sizer.Add(sct, border=0, flag=wx.EXPAND | wx.ALL)

        return sct

    def addPluginSections(self, group):
        """
        Add any sections to the ribbon which are defined by plugins, targeting the given entry point group.

        Parameters
        ----------
        group : str
            Entry point group to look for plugin sections in.

        Returns
        -------
        list[FrameRubbinPluginSection]
            List of section objects which were added
        """
        from importlib import metadata
        # start off with no entry points or sections
        entryPoints = []
        sections = []
        # iterate through all entry point groups
        for thisGroup, eps in metadata.entry_points().items():
            # get entry points for matching group
            if thisGroup == group:
                # add to list of all entry points
                entryPoints += eps
        # iterate through found entry points
        for ep in entryPoints:
            try:
                # load (import) module
                cls = ep.load()
            except:
                # if failed for any reason, skip it
                continue
            # if the target is not a subclass of FrameRibbonPluginSection, discard it
            if not isinstance(cls, type) or not issubclass(cls, FrameRibbonPluginSection):
                continue
            # if it's a section, add it
            sct = cls(parent=self)
            self.sections[sct.name] = sct
            sections.append(sct)
            # add to sizer
            self.sizer.Add(sct, border=0, flag=wx.EXPAND | wx.ALL)
            # add separator
            self.addSeparator()

        return sections

    def addButton(self, section, name, label="", icon=None, tooltip="", callback=None,
                  style=wx.BU_NOTEXT):
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
        tooltip : str
            Tooltip to display on hover
        callback : function
            Function to call when this button is clicked
        style : wx.StyleFlag
            Style flags from wx to control button appearance

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
            name, label=label, icon=icon, tooltip=tooltip, callback=callback, style=style
        )

        return btn

    def addDropdownButton(self, section, name, label, icon=None, callback=None, menu=None):
        """
        Add a dropdown button to a given section.

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
        menu : wx.Menu or function
            Menu to show when the dropdown arrow is clicked, or a function to generate this menu

        Returns
        -------
        FrameRibbonDropdownButton
            The created button handle
        """
        # if section doesn't exist, make it
        if section not in self.sections:
            self.addSection(section, label=section)
        # call addButton method from given section
        btn = self.sections[section].addDropdownButton(
            name, label=label, icon=icon, callback=callback, menu=menu
        )

        return btn

    def addSwitchCtrl(
            self, section, name, labels=("", ""), startMode=0, callback=None, style=wx.HORIZONTAL
    ):
        # if section doesn't exist, make it
        if section not in self.sections:
            self.addSection(section, label=section)
        btn = self.sections[section].addSwitchCtrl(
            name, labels, startMode=startMode, callback=callback, style=style
        )

        return btn

    def addPavloviaUserCtrl(self, section="pavlovia", name="pavuser", frame=None):
        # if section doesn't exist, make it
        if section not in self.sections:
            self.addSection(section, label=section)
        # call addButton method from given section
        btn = self.sections[section].addPavloviaUserCtrl(name=name, ribbon=self, frame=frame)

        return btn

    def addPavloviaProjectCtrl(self, section="pavlovia", name="pavproject", frame=None):
        # if section doesn't exist, make it
        if section not in self.sections:
            self.addSection(section, label=section)
        # call addButton method from given section
        btn = self.sections[section].addPavloviaProjectCtrl(name=name, ribbon=self, frame=frame)

        return btn

    def addSeparator(self):
        """
        Add a vertical line.
        """
        if sys.platform == "win32":
            # make separator
            sep = wx.StaticLine(self, style=wx.LI_VERTICAL)
            # add separator
            self.sizer.Add(sep, border=6, flag=wx.EXPAND | wx.ALL)
        else:
            # on non-Windows, just use a big space
            self.sizer.AddSpacer(36)

    def addSpacer(self, size=6, section=None):
        """
        Add a non-streching space.
        """
        # choose sizer to add to
        if section is None:
            sizer = self.sizer
        else:
            sizer = self.sections[section].sizer
        # add space
        sizer.AddSpacer(size=size)

    def addStretchSpacer(self, prop=1, section=None):
        """
        Add a stretching space.
        """
        # choose sizer to add to
        if section is None:
            sizer = self.sizer
        else:
            sizer = self.sections[section].sizer
        # add space
        sizer.AddStretchSpacer(prop=prop)

    def _applyAppTheme(self):
        self.SetBackgroundColour(colors.app['frame_bg'])
        self.Refresh()


class FrameRibbonSection(wx.Panel, handlers.ThemeMixin):
    """
    Section within a FrameRibbon, containing controls marked by a label.

    Parameters
    ----------
    parent : FrameRibbon
        Ribbon containing this section
    label : str
        Label to display on this section
    icon : str or None
        File stem of the icon for the section's label
    """
    def __init__(self, parent, label=None, icon=None):
        wx.Panel.__init__(self, parent)
        self.ribbon = parent
        # setup sizers
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.border.Add(self.sizer, proportion=1, border=0, flag=(
            wx.EXPAND | wx.ALL | wx.RESERVE_SPACE_EVEN_IF_HIDDEN
        ))
        # add label sizer
        self.labelSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.border.Add(
            self.labelSizer, border=6, flag=wx.ALIGN_CENTRE | wx.TOP
        )
        # add label icon
        self._icon = icons.ButtonIcon(icon, size=16)
        self.icon = wx.StaticBitmap(
            self, bitmap=self._icon.bitmap
        )
        if icon is None:
            self.icon.Hide()
        self.labelSizer.Add(
            self.icon, border=6, flag=wx.EXPAND | wx.RIGHT
        )
        # add label text
        if label is None:
            label = ""
        self.label = wx.StaticText(self, label=label, style=wx.ALIGN_CENTRE_HORIZONTAL)
        self.labelSizer.Add(
            self.label, flag=wx.EXPAND
        )

        # add space
        self.border.AddSpacer(6)

        # dict in which to store buttons
        self.buttons = {}

        self._applyAppTheme()

    def addButton(self, name, label="", icon=None, tooltip="", callback=None, style=wx.BU_NOTEXT):
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
        tooltip : str
            Tooltip to display on hover
        callback : function
            Function to call when this button is clicked
        style : wx.StyleFlag
            Style flags from wx to control button appearance

        Returns
        -------
        FrameRibbonButton
            The created button handle
        """
        # create button
        btn = FrameRibbonButton(
            self, label=label, icon=icon, tooltip=tooltip, callback=callback, style=style
        )
        # store references
        self.buttons[name] = self.ribbon.buttons[name] = btn
        # add button to sizer
        flags = wx.EXPAND
        if sys.platform == "darwin":
            # add top padding on Mac
            flags |= wx.TOP
        self.sizer.Add(btn, border=12, flag=flags)

        return btn

    def addDropdownButton(self, name, label, icon=None, callback=None, menu=None):
        """
        Add a dropdown button to this section.

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
        menu : wx.Menu or function
            Menu to show when the dropdown arrow is clicked, or a function to generate this menu

        Returns
        -------
        FrameRibbonDropdownButton
            The created button handle
        """
        # create button
        btn = FrameRibbonDropdownButton(
            self, label=label, icon=icon, callback=callback, menu=menu
        )
        # store references
        self.buttons[name] = self.ribbon.buttons[name] = btn
        # add button to sizer
        self.sizer.Add(btn, border=0, flag=wx.EXPAND | wx.ALL)

        return btn

    def addSwitchCtrl(self, name, labels=("", ""), startMode=0, callback=None, style=wx.HORIZONTAL):
        # create button
        btn = FrameRibbonSwitchCtrl(
            self, labels, startMode=startMode, callback=callback, style=style
        )
        # store references
        self.buttons[name] = self.ribbon.buttons[name] = btn
        # add button to sizer
        self.sizer.Add(btn, border=0, flag=wx.EXPAND | wx.ALL)

        return btn

    def addPavloviaUserCtrl(self, name="pavuser", ribbon=None, frame=None):
        # substitute ribbon if not given
        if ribbon is None:
            ribbon = self.GetParent()
        # create button
        btn = PavloviaUserCtrl(self, ribbon=ribbon, frame=frame)
        # store references
        self.buttons[name] = self.ribbon.buttons[name] = btn
        # add button to sizer
        self.sizer.Add(btn, border=0, flag=wx.EXPAND | wx.ALL)

        return btn

    def addPavloviaProjectCtrl(self, name="pavproject", ribbon=None, frame=None):
        # substitute ribbon if not given
        if ribbon is None:
            ribbon = self.GetParent()
        # create button
        btn = PavloviaProjectCtrl(self, ribbon=ribbon, frame=frame)
        # store references
        self.buttons[name] = self.ribbon.buttons[name] = btn
        # add button to sizer
        self.sizer.Add(btn, border=0, flag=wx.EXPAND | wx.ALL)

        return btn

    def _applyAppTheme(self):
        # set color
        self.SetBackgroundColour(colors.app['frame_bg'])
        self.SetForegroundColour(colors.app['text'])
        # set bitmaps again
        self._icon.reload()
        self.icon.SetBitmap(self._icon.bitmap)
        # refresh
        self.Refresh()


class FrameRibbonPluginSection(FrameRibbonSection):
    """
    Subclass of FrameRibbonSection specifically for adding sections to the ribbon via plugins. To
    add a section, create a subclass of FrameRibbonPluginSection in your plugin and add any buttons
    you want it to have in the `__init__` function. Then give it an entry point in either
    "psychopy.app.builder", "psychopy.app.coder" or "psychopy.app.runner" to tell PsychoPy which
    frame to add it to.
    """
    def __init__(self, parent, name, label=None):
        # if not given a label, use name
        if label is None:
            label = name
        # store name
        self.name = name
        # initialise subclass
        FrameRibbonSection.__init__(
            self, parent, label=label, icon="plugin"
        )


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
    tooltip : str
        Tooltip to display on hover
    callback : function
        Function to call when this button is clicked
    style : int
        Combination of wx button styles to apply
    """
    def __init__(self, parent, label, icon=None, tooltip="", callback=None, style=wx.BU_NOTEXT):
        # figure out width
        w = -1
        if style | wx.BU_NOTEXT == style:
            w = 40
        # initialize
        wx.Button.__init__(self, parent, style=wx.BORDER_NONE | style, size=(w, 44))
        self.SetMinSize((40, 44))
        # set label
        self.SetLabelText(label)
        # set tooltip
        if tooltip and style | wx.BU_NOTEXT == style:
            # if there's no label, include it in the tooltip
            tooltip = f"{label}: {tooltip}"
        self.SetToolTip(tooltip)
        # set icon
        self._icon = icons.ButtonIcon(icon, size=32)
        bmpStyle = style & (wx.TOP | wx.BOTTOM | wx.LEFT | wx.RIGHT)
        # if given, bind callback
        if callback is not None:
            self.Bind(wx.EVT_BUTTON, callback)
        # setup hover behaviour
        self.Bind(wx.EVT_ENTER_WINDOW, self.onHover)
        self.Bind(wx.EVT_LEAVE_WINDOW, self.onHover)

        self._applyAppTheme()

    def _applyAppTheme(self):
        # set color
        self.SetBackgroundColour(colors.app['frame_bg'])
        self.SetForegroundColour(colors.app['text'])
        # set bitmaps again
        self._icon.reload()
        self.SetBitmap(self._icon.bitmap)
        self.SetBitmapCurrent(self._icon.bitmap)
        self.SetBitmapPressed(self._icon.bitmap)
        self.SetBitmapFocus(self._icon.bitmap)
        # refresh
        self.Refresh()

    def onHover(self, evt):
        if evt.EventType == wx.EVT_ENTER_WINDOW.typeId:
            # on hover, lighten background
            self.SetBackgroundColour(colors.app['panel_bg'])
        else:
            # otherwise, keep same colour as parent
            self.SetBackgroundColour(colors.app['frame_bg'])


class FrameRibbonDropdownButton(wx.Panel, handlers.ThemeMixin):
    def __init__(self, parent, label, icon=None, callback=None, menu=None):
        wx.Panel.__init__(self, parent)
        # setup sizer
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)

        # make button
        self.button = wx.Button(self, label=label, style=wx.BORDER_NONE)
        self.sizer.Add(self.button, proportion=1, border=0, flag=wx.EXPAND | wx.ALL)
        # set icon
        self._icon = icons.ButtonIcon(icon, size=32)
        # bind button callback
        if callback is not None:
            self.button.Bind(wx.EVT_BUTTON, callback)

        # make dropdown
        self.drop = wx.Button(self, label="▾", style=wx.BU_EXACTFIT | wx.BORDER_NONE)
        self.sizer.Add(self.drop, border=0, flag=wx.EXPAND | wx.ALL)
        # bind menu
        self.drop.Bind(wx.EVT_BUTTON, self.onMenu)
        self.menu = menu

        # setup hover behaviour
        self.button.Bind(wx.EVT_ENTER_WINDOW, self.onHover)
        self.button.Bind(wx.EVT_LEAVE_WINDOW, self.onHover)
        self.drop.Bind(wx.EVT_ENTER_WINDOW, self.onHover)
        self.drop.Bind(wx.EVT_LEAVE_WINDOW, self.onHover)

        self._applyAppTheme()

    def onMenu(self, evt):
        menu = self.menu
        # skip if there's no menu
        if menu is None:
            return
        # if menu is created live, create it
        if callable(menu):
            menu = menu(self, evt)
        # show menu
        self.PopupMenu(menu)

    def _applyAppTheme(self):
        # set color
        for obj in (self, self.button, self.drop):
            obj.SetBackgroundColour(colors.app['frame_bg'])
            obj.SetForegroundColour(colors.app['text'])
        # set bitmaps again
        self._icon.reload()
        self.button.SetBitmap(self._icon.bitmap)
        self.button.SetBitmapCurrent(self._icon.bitmap)
        self.button.SetBitmapPressed(self._icon.bitmap)
        self.button.SetBitmapFocus(self._icon.bitmap)
        # refresh
        self.Refresh()

    def onHover(self, evt):
        if evt.EventType == wx.EVT_ENTER_WINDOW.typeId:
            # on hover, lighten background
            evt.EventObject.SetBackgroundColour(colors.app['panel_bg'])
        else:
            # otherwise, keep same colour as parent
            evt.EventObject.SetBackgroundColour(colors.app['frame_bg'])


EVT_RIBBON_SWITCH = wx.PyEventBinder(wx.IdManager.ReserveId())


class FrameRibbonSwitchCtrl(wx.Panel, handlers.ThemeMixin):
    """
    A switch with two modes. Use `addDependency` to make presentation of other buttons
    conditional on this control's state.
    """
    def __init__(
            self, parent, labels=("", ""), startMode=0,
            callback=None,
            style=wx.HORIZONTAL
    ):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        # use style tag to get text alignment and control orientation
        alignh = style & (wx.BU_LEFT | wx.BU_RIGHT)
        alignv = style & (wx.BU_TOP | wx.BU_BOTTOM)
        alignEach = [alignh | alignv, alignh | alignv]
        orientation = style & (wx.HORIZONTAL | wx.VERTICAL)
        # if orientation is horizontal and no h alignment set, wrap text around button
        if orientation == wx.HORIZONTAL and not alignh:
            alignEach = [wx.BU_RIGHT | alignv, wx.BU_LEFT | alignv]
        # setup sizers
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(self.sizer)
        self.btnSizer = wx.BoxSizer(orientation)
        # setup depends dict
        self.depends = []
        # make icon
        self.icon = wx.Button(self, style=wx.BORDER_NONE | wx.BU_NOTEXT | wx.BU_EXACTFIT)
        self.icon.Bind(wx.EVT_BUTTON, self.onModeToggle)
        self.icon.Bind(wx.EVT_ENTER_WINDOW, self.onHover)
        self.icon.Bind(wx.EVT_LEAVE_WINDOW, self.onHover)
        # make switcher buttons
        self.btns = []
        for i in range(2):
            btn = wx.Button(
                self, label=labels[i], size=(-1, 16),
                style=wx.BORDER_NONE | wx.BU_EXACTFIT | alignEach[i]
            )
            if style & wx.BU_NOTEXT:
                btn.Hide()
            self.btnSizer.Add(btn, proportion=orientation == wx.VERTICAL, flag=wx.EXPAND)
            btn.Bind(wx.EVT_BUTTON, self.onModeSwitch)
            btn.Bind(wx.EVT_ENTER_WINDOW, self.onHover)
            btn.Bind(wx.EVT_LEAVE_WINDOW, self.onHover)
            self.btns.append(btn)
        # arrange icon/buttons according to style
        self.sizer.Add(self.btnSizer, proportion=1, border=3, flag=wx.EXPAND | wx.ALL)
        params = {'border': 6, 'flag': wx.EXPAND | wx.ALL}
        if orientation == wx.HORIZONTAL:
            # if horizontal, always put icon in the middle
            self.btnSizer.Insert(1, self.icon, **params)
        elif alignh == wx.BU_LEFT:
            # if left, put icon on left
            self.sizer.Insert(0, self.icon, **params)
        else:
            # if right, put icon on right
            self.sizer.Insert(1, self.icon, **params)
        # make icons
        if orientation == wx.HORIZONTAL:
            stems = ["switchCtrlLeft", "switchCtrlRight"]
            size = (32, 16)
        else:
            stems = ["switchCtrlTop", "switchCtrlBot"]
            size = (16, 32)
        self.icons = [
            icons.ButtonIcon(stem, size=size) for stem in stems
        ]
        # set starting mode
        self.setMode(startMode, silent=True)
        # bind callback
        if callback is not None:
            self.Bind(EVT_RIBBON_SWITCH, callback)

        self.Layout()

    def _applyAppTheme(self):
        self.SetBackgroundColour(colors.app['frame_bg'])
        self.icon.SetBackgroundColour(colors.app['frame_bg'])
        for mode, btn in enumerate(self.btns):
            btn.SetBackgroundColour(colors.app['frame_bg'])
            if mode == self.mode:
                btn.SetForegroundColour(colors.app['text'])
            else:
                btn.SetForegroundColour(colors.app['rt_timegrid'])

    def onModeSwitch(self, evt):
        evtBtn = evt.GetEventObject()
        # iterate through switch buttons
        for mode, btn in enumerate(self.btns):
            # if button matches this event...
            if btn is evtBtn:
                # change mode
                self.setMode(mode)

    def onModeToggle(self, evt=None):
        if self.mode == 0:
            self.setMode(1)
        else:
            self.setMode(0)

    def setMode(self, mode, silent=False):
        # set mode
        self.mode = mode
        # iterate through switch buttons
        for btnMode, btn in enumerate(self.btns):
            # if it's the correct button...
            if btnMode == mode:
                # style accordingly
                btn.SetForegroundColour(colors.app['text'])
            else:
                btn.SetForegroundColour(colors.app['rt_timegrid'])
        # set icon
        self.icon.SetBitmap(self.icons[mode].bitmap)

        # handle depends
        for depend in self.depends:
            # get linked ctrl
            ctrl = depend['ctrl']
            # show/enable according to mode
            if depend['action'] == "show":
                ctrl.Show(mode == depend['mode'])
            if depend['action'] == "enable":
                ctrl.Enable(mode == depend['mode'])
        # emit event
        if not silent:
            evt = wx.CommandEvent(EVT_RIBBON_SWITCH.typeId)
            evt.SetInt(mode)
            evt.SetString(self.btns[mode].GetLabel())
            wx.PostEvent(self, evt)
        # refresh
        self.Refresh()
        self.Update()
        self.GetTopLevelParent().Layout()

    def onHover(self, evt):
        if evt.EventType == wx.EVT_ENTER_WINDOW.typeId:
            # on hover, lighten background
            evt.EventObject.SetForegroundColour(colors.app['text'])
        else:
            # otherwise, keep same colour as parent
            if evt.EventObject is self.btns[self.mode]:
                evt.EventObject.SetForegroundColour(colors.app['text'])
            else:
                evt.EventObject.SetForegroundColour(colors.app['rt_timegrid'])

    def addDependant(self, ctrl, mode, action="show"):
        """
        Connect another button to one mode of this ctrl such that it is shown/enabled only when
        this ctrl is in that mode.

        Parameters
        ----------
        ctrl : wx.Window
            Control to act upon
        mode : str
            The mode in which to show/enable the linked ctrl
        action : str
            One of:
            - "show" Show the control
            - "enable" Enable the control
        """
        self.depends.append(
            {
                'mode': mode,  # when in mode...
                'action': action,  # then...
                'ctrl': ctrl,  # to...
            }
        )


class PavloviaUserCtrl(FrameRibbonDropdownButton):
    def __init__(self, parent, ribbon=None, frame=None):
        # make button
        FrameRibbonDropdownButton.__init__(
            self, parent, label=_translate("No user"), icon=None,
            callback=self.onClick, menu=self.makeMenu
        )
        # add left space
        self.sizer.InsertSpacer(0, size=6)
        # store reference to frame and ribbon
        self.frame = frame
        self.ribbon = ribbon
        # let app know about this button
        self.frame.app.pavloviaButtons['user'].append(self)

        # update info once now (in case creation happens after logging in)
        self.updateInfo()

        # bind deletion behaviour
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDelete)

        self._applyAppTheme()
    
    def _applyAppTheme(self):
        # set color
        for obj in (self, self.button, self.drop):
            obj.SetBackgroundColour(colors.app['frame_bg'])
            obj.SetForegroundColour(colors.app['text'])
        # refresh
        self.Refresh()

    def onDelete(self, evt=None):
        i = self.frame.app.pavloviaButtons['user'].index(self)
        self.frame.app.pavloviaButtons['user'].pop(i)

    def onClick(self, evt):
        # get user
        user = pavlovia.getCurrentSession().user
        # if we have a user, go to profile
        if user is None:
            self.onPavloviaLogin()
        else:
            webbrowser.open("https://pavlovia.org/%(username)s" % user)

    @staticmethod
    def makeMenu(self, evt):
        # get user
        user = pavlovia.getCurrentSession().user
        # make menu
        menu = wx.Menu()

        # edit user
        btn = menu.Append(wx.ID_ANY, _translate("Edit user..."))
        btn.SetBitmap(icons.ButtonIcon("editbtn", size=16).bitmap)
        menu.Bind(wx.EVT_MENU, self.onEditPavloviaUser, btn)
        menu.Enable(btn.GetId(), user is not None)
        # switch user
        switchTo = wx.Menu()
        item = menu.AppendSubMenu(switchTo, _translate("Switch user"))
        item.SetBitmap(icons.ButtonIcon("view-refresh", size=16).bitmap)
        for name in pavlovia.knownUsers:
            if user is None or name != user['username']:
                btn = switchTo.Append(wx.ID_ANY, name)
                switchTo.Bind(wx.EVT_MENU, self.onPavloviaSwitchUser, btn)
        # log in to new user
        switchTo.AppendSeparator()
        btn = switchTo.Append(wx.ID_ANY, _translate("New user..."))
        btn.SetBitmap(icons.ButtonIcon("plus", size=16).bitmap)
        menu.Bind(wx.EVT_MENU, self.onPavloviaLogin, btn)
        # log in/out
        menu.AppendSeparator()
        if user is not None:
            btn = menu.Append(wx.ID_ANY, _translate("Log out"))
            menu.Bind(wx.EVT_MENU, self.onPavloviaLogout, btn)
        else:
            btn = menu.Append(wx.ID_ANY, _translate("Log in"))
            menu.Bind(wx.EVT_MENU, self.onPavloviaLogin, btn)

        return menu

    def updateInfo(self):
        # get user
        user = pavlovia.getCurrentSession().user

        if user is None:
            # if no user, set as defaults
            self.button.SetLabel(_translate("No user"))
            icon = icons.ButtonIcon("user_none", size=32).bitmap
        else:
            # if there us a user, set username
            self.button.SetLabel(user['username'])
            # get icon (use blank if failed)
            try:
                content = utils.ImageData(user['avatar_url'])
                content = content.resize(size=(32, 32))
                icon = wx.Bitmap.FromBufferAndAlpha(
                    width=content.size[0],
                    height=content.size[1],
                    data=content.tobytes("raw", "RGB"),
                    alpha=content.tobytes("raw", "A")
                )
            except requests.exceptions.MissingSchema:
                icon = icons.ButtonIcon("user_none", size=32).bitmap

        # apply circle mask
        mask = icons.ButtonIcon("circle_mask", size=32).bitmap.ConvertToImage()
        icon = icon.ConvertToImage()
        maskAlpha = numpy.array(mask.GetAlpha(), dtype=int)
        icon.SetAlpha(numpy.uint8(maskAlpha))
        # set icon
        self.button.SetBitmap(wx.Bitmap(icon))

        self.Layout()
        if self.ribbon is not None:
            self.ribbon.Layout()

    def onEditPavloviaUser(self, evt=None):
        # open edit window
        dlg = pavui.PavloviaMiniBrowser(parent=self, loginOnly=False)
        dlg.editUserPage()
        dlg.ShowModal()
        # refresh user on close
        user = pavlovia.getCurrentSession().user
        user.user = user.user

    def onPavloviaSwitchUser(self, evt):
        menu = evt.GetEventObject()
        item = menu.FindItem(evt.GetId())[0]
        username = item.GetItemLabel()
        pavlovia.logout()
        pavlovia.login(username)

    def onPavloviaLogin(self, evt=None):
        pavui.logInPavlovia(self, evt)

    def onPavloviaLogout(self, evt=None):
        pavlovia.logout()


class PavloviaProjectCtrl(FrameRibbonDropdownButton):
    def __init__(self, parent, ribbon=None, frame=None):
        # make button
        FrameRibbonDropdownButton.__init__(
            self, parent, label=_translate("No project"), icon=None,
            callback=self.onClick, menu=self.makeMenu
        )
        # store reference to frame and ribbon
        self.frame = frame
        self.ribbon = ribbon
        # let app know about this button
        self.frame.app.pavloviaButtons['project'].append(self)

        # update info once now (in case creation happens after logging in)
        self.updateInfo()

        # bind deletion behaviour
        self.Bind(wx.EVT_WINDOW_DESTROY, self.onDelete)

        self._applyAppTheme()
    
    def _applyAppTheme(self):
        # set color
        for obj in (self, self.button, self.drop):
            obj.SetBackgroundColour(colors.app['frame_bg'])
            obj.SetForegroundColour(colors.app['text'])
        # refresh
        self.Refresh()

    def onDelete(self, evt=None):
        i = self.frame.app.pavloviaButtons['project'].index(self)
        self.frame.app.pavloviaButtons['project'].pop(i)

    def onClick(self, evt):
        # get project
        project = self.GetTopLevelParent().project
        # if we have a user, go to profile
        if project is None:
            webbrowser.open("https://pavlovia.org")
        else:
            webbrowser.open(f"https://pavlovia.org/{project.stringId}")

    @staticmethod
    def makeMenu(self, evt):
        # get project
        project = self.GetTopLevelParent().project
        # make menu
        menu = wx.Menu()

        # create project
        if project is None:
            btn = menu.Append(wx.ID_ANY, _translate("New project"))
            btn.SetBitmap(icons.ButtonIcon("plus", size=16).bitmap)
            menu.Bind(wx.EVT_MENU, self.onPavloviaCreate, btn)
        # edit project
        btn = menu.Append(wx.ID_ANY, _translate("Edit project..."))
        btn.SetBitmap(icons.ButtonIcon("editbtn", size=16).bitmap)
        menu.Bind(wx.EVT_MENU, self.onPavloviaProject, btn)
        menu.Enable(btn.GetId(), project is not None)
        # search projects
        menu.AppendSeparator()
        btn = menu.Append(wx.ID_ANY, _translate("Search projects..."))
        btn.SetBitmap(icons.ButtonIcon("search", size=16).bitmap)
        menu.Bind(wx.EVT_MENU, self.onPavloviaSearch, btn)

        return menu

    def updateInfo(self):
        # get project
        project = self.GetTopLevelParent().project

        if project is None or project['path_with_namespace'] is None:
            self.button.SetLabel(_translate("No project"))
        else:
            self.button.SetLabel(project['path_with_namespace'])

        self.Layout()
        if self.ribbon is not None:
            self.ribbon.Layout()

    def onPavloviaSearch(self, evt=None):
        searchDlg = pavui.search.SearchFrame(
                app=self.frame.app, parent=self.frame,
                pos=self.frame.GetPosition())
        searchDlg.Show()

    def onPavloviaProject(self, evt=None):
        # search again for project if needed (user may have logged in since last looked)
        if self.frame.filename:
            self.frame.project = pavlovia.getProject(self.frame.filename)
        # get project
        if self.frame.project is not None:
            self.frame.project.refresh()
            dlg = pavui.project.ProjectFrame(
                app=self.frame.app,
                project=self.frame.project,
                parent=self.frame
            )
        else:
            dlg = pavui.project.ProjectFrame(app=self.frame.app)
        dlg.Show()

    def onPavloviaCreate(self, evt=None):
        if Path(self.frame.filename).is_file():
            # save file
            self.frame.fileSave(self.frame.filename)
            # if allowed by prefs, export html and js files
            if self.frame._getExportPref('on sync'):
                htmlPath = self.frame._getHtmlPath(self.frame.filename)
                if htmlPath:
                    self.frame.fileExport(htmlPath=htmlPath)
                else:
                    return
        # get start path and name from builder/coder if possible
        if self.frame.filename:
            file = Path(self.frame.filename)
            name = file.stem
            path = file.parent
        else:
            name = path = ""
        # open dlg to create new project
        createDlg = sync.CreateDlg(self,
                                   user=pavlovia.getCurrentSession().user,
                                   name=name,
                                   path=path)
        if createDlg.ShowModal() == wx.ID_OK and createDlg.project is not None:
            self.frame.project = createDlg.project
        else:
            return
        # do first sync
        self.frame.onPavloviaSync()
