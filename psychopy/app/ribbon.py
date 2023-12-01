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

    def addButton(self, section, name, label="", icon=None, tooltip="", callback=None):
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
            name, label=label, icon=icon, tooltip=tooltip, callback=callback
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
            self, section, name, modes, labels, startMode=0
    ):
        # if section doesn't exist, make it
        if section not in self.sections:
            self.addSection(section, label=section)
        btn = self.sections[section].addSwitchCtrl(
            name, modes, labels, startMode=startMode
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
        # make separator
        sep = wx.StaticLine(self, style=wx.LI_VERTICAL)
        # add separator
        self.sizer.Add(sep, border=6, flag=wx.EXPAND | wx.ALL)

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
        self.border.Add(
            self.sizer, proportion=1, border=0, flag=wx.EXPAND | wx.ALL
        )
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

    def addButton(self, name, label="", icon=None, tooltip="", callback=None):
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

        Returns
        -------
        FrameRibbonButton
            The created button handle
        """
        # create button
        btn = FrameRibbonButton(
            self, label=label, icon=icon, tooltip=tooltip, callback=callback
        )
        # store references
        self.buttons[name] = self.ribbon.buttons[name] = btn
        # add button to sizer
        self.sizer.Add(btn, border=0, flag=wx.EXPAND | wx.ALL)

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

    def addSwitchCtrl(self, name, modes, labels, startMode=0):
        # create button
        btn = FrameRibbonSwitchCtrl(
            self, modes, labels, startMode=startMode
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
        self.SetBackgroundColour(colors.app['frame_bg'])

        self.icon.SetBitmap(self._icon.bitmap)


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
        # set label
        self.SetLabelText(label)
        # set tooltip
        if tooltip and style | wx.BU_NOTEXT == style:
            # if there's no label, include it in the tooltip
            tooltip = f"{label}: {tooltip}"
        self.SetToolTipString(tooltip)
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
        self.button.SetBitmap(
            icons.ButtonIcon(icon, size=32).bitmap
        )
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
        self.SetBackgroundColour(colors.app['frame_bg'])
        self.button.SetBackgroundColour(colors.app['frame_bg'])
        self.drop.SetBackgroundColour(colors.app['frame_bg'])

    def onHover(self, evt):
        if evt.EventType == wx.EVT_ENTER_WINDOW.typeId:
            # on hover, lighten background
            evt.EventObject.SetBackgroundColour(colors.app['panel_bg'])
        else:
            # otherwise, keep same colour as parent
            evt.EventObject.SetBackgroundColour(colors.app['frame_bg'])


class FrameRibbonSwitchCtrl(wx.Panel, handlers.ThemeMixin):
    """
    A switch with multiple modes. Use `addDependency` to make presentation of other buttons
    conditional on this control's state.
    """
    class FrameRibbonSwitchButton(wx.Window, handlers.ThemeMixin):
        def __init__(self, parent, label):
            wx.Window.__init__(self, parent, style=wx.BORDER_NONE)
            # setup sizer
            self.sizer = wx.BoxSizer(wx.HORIZONTAL)
            self.SetSizer(self.sizer)
            # make label
            self.label = wx.StaticText(
                self, label=label, style=wx.BORDER_NONE
            )
            self.sizer.Add(self.label, proportion=1, border=6, flag=wx.ALIGN_CENTER_VERTICAL | wx.LEFT | wx.RIGHT)
            # make icon
            self.icon = wx.StaticBitmap(self)
            self.sizer.Add(self.icon, border=6, flag=wx.EXPAND | wx.LEFT | wx.RIGHT)
            # bind to relevant functions
            for child in (self, self.icon, self.label):
                child.Bind(wx.EVT_LEFT_DOWN, self.onClick)
                child.Bind(wx.EVT_ENTER_WINDOW, self.onHover)
                child.Bind(wx.EVT_LEAVE_WINDOW, self.onHover)

            # start off deselected
            self.setSelected(False)

        def onClick(self, evt):
            # emit a button event when clicked
            evt = wx.CommandEvent(wx.EVT_BUTTON.typeId)
            evt.SetEventObject(self)
            wx.PostEvent(self, evt)

        def setSelected(self, selected):
            # store state
            self.selected = selected
            # update appearance
            if selected:
                self.label.SetForegroundColour(colors.app['text'])
                self.icon.SetBitmap(
                    icons.ButtonIcon("greendot", size=16).bitmap
                )
            else:
                self.label.SetForegroundColour(colors.app['rt_timegrid'])
                self.icon.SetBitmap(
                    icons.ButtonIcon("greydot", size=16).bitmap
                )

        def onHover(self, evt):
            if self.HitTest(evt.Position) == wx.HT_WINDOW_INSIDE:
                # on hover, lighten background
                self.SetBackgroundColour(colors.app['panel_bg'])
                self.label.SetBackgroundColour(colors.app['panel_bg'])
                self.icon.SetBackgroundColour(colors.app['panel_bg'])
            else:
                # otherwise, keep same colour as parent
                self.SetBackgroundColour(colors.app['frame_bg'])
                self.label.SetBackgroundColour(colors.app['frame_bg'])
                self.icon.SetBackgroundColour(colors.app['frame_bg'])
            self.Update()
            self.Refresh()

        def _applyAppTheme(self):
            self.SetBackgroundColour(colors.app['frame_bg'])
            self.setSelected(self.selected)

    def __init__(
            self, parent, modes, labels, startMode=0,
            style=wx.BU_RIGHT
    ):
        wx.Panel.__init__(self, parent)
        self.parent = parent
        # setup sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.sizer)
        # setup depends dict
        self.depends = []
        # make switcher buttons and indicators
        self.btns = {}
        for mode, label in zip(modes, labels):
            # make sizer
            btnSizer = wx.BoxSizer(wx.HORIZONTAL)
            self.sizer.Add(btnSizer, flag=wx.EXPAND)
            # make button with label
            self.btns[mode] = self.FrameRibbonSwitchButton(self, label=label)
            self.sizer.Add(self.btns[mode], proportion=1, flag=wx.EXPAND)
            self.btns[mode].Bind(wx.EVT_BUTTON, self.onModeSwitch)

        # set start mode
        if isinstance(startMode, int) and startMode not in modes:
            # if given an index, get mode name
            startMode = modes[startMode]
        self.setMode(startMode)

    def _applyAppTheme(self):
        self.SetBackgroundColour(colors.app['frame_bg'])
        for mode, btn in self.btns.items():
            btn.SetBackgroundColour(colors.app['frame_bg'])
            if mode == self.mode:
                btn.SetForegroundColour(colors.app['text'])
            else:
                btn.SetForegroundColour(colors.app['rt_timegrid'])

    def onModeSwitch(self, evt):
        evtBtn = evt.GetEventObject()
        # iterate through switch buttons
        for mode, btn in self.btns.items():
            # if button matches this event...
            if btn is evtBtn:
                # change mode
                self.setMode(mode)

    def setMode(self, mode):
        # set mode
        self.mode = mode
        # iterate through switch buttons
        for btnMode, btn in self.btns.items():
            # if it's the correct button...
            if btnMode == mode:
                # style accordingly
                btn.setSelected(True)
            else:
                btn.setSelected(False)

        # handle depends
        for depend in self.depends:
            # get linked ctrl
            ctrl = depend['ctrl']
            # show/enable according to mode
            if depend['action'] == "show":
                ctrl.Show(mode == depend['mode'])
            if depend['action'] == "enable":
                ctrl.Enable(mode == depend['mode'])
        # refresh
        self.Refresh()
        self.Update()
        self.GetTopLevelParent().Layout()

    def onHover(self, evt):
        if evt.EventType == wx.EVT_ENTER_WINDOW.typeId:
            # on hover, lighten background
            evt.EventObject.SetForegroundColour(colors.app['text'])
            evt.EventObject.SetBackgroundColour(colors.app['panel_bg'])
        else:
            # otherwise, keep same colour as parent
            if evt.EventObject is self.btns[self.mode]:
                evt.EventObject.SetForegroundColour(colors.app['text'])
            else:
                evt.EventObject.SetForegroundColour(colors.app['rt_timegrid'])
            evt.EventObject.SetBackgroundColour(colors.app['frame_bg'])

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

    def __del__(self):
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

    def __del__(self):
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

        if project is None:
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
