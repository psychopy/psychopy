#!/usr/bin/env python
# -*- coding: utf-8 -*-
import json
import sys
from pathlib import Path

import wx
import wx.propgrid as pg
import wx.py
import platform
import re
import os

from psychopy.app.themes import icons
from . import dialogs
from psychopy import localization, prefs
from psychopy.localization import _translate
from pkg_resources import parse_version
from psychopy import sound
from psychopy.app.utils import getSystemFonts
import collections


audioLatencyLabels = {0: _translate('Latency not important'),
                      1: _translate('Share low-latency driver'),
                      2: _translate('Exclusive low-latency'),
                      3: _translate('Aggressive low-latency'),
                      4: _translate('Latency critical')}


class PrefPropGrid(wx.Panel):
    """Class for the property grid portion of the preference window."""

    def __init__(self, parent, id=wx.ID_ANY, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.TAB_TRAVERSAL,
                 name=wx.EmptyString):
        wx.Panel.__init__(
            self, parent, id=id, pos=pos, size=size, style=style, name=name)
        bSizer1 = wx.BoxSizer(wx.HORIZONTAL)
        self.app = wx.GetApp()
        # make splitter so panels are resizable
        self.splitter = wx.SplitterWindow(self)
        bSizer1.Add(self.splitter, proportion=1, border=6, flag=wx.EXPAND | wx.ALL)
        # tabs panel
        self.lstPrefPages = wx.ListCtrl(
            self.splitter, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.LC_ALIGN_TOP | wx.LC_LIST | wx.LC_SINGLE_SEL)
        # images for tabs panel
        prefsImageSize = wx.Size(48, 48)
        self.prefsIndex = 0
        self.prefsImages = wx.ImageList(
            prefsImageSize.GetWidth(), prefsImageSize.GetHeight())
        self.lstPrefPages.AssignImageList(self.prefsImages, wx.IMAGE_LIST_SMALL)
        # property grid
        self.proPrefs = pg.PropertyGridManager(
            self.splitter, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.propgrid.PGMAN_DEFAULT_STYLE | wx.propgrid.PG_BOLD_MODIFIED |
            wx.propgrid.PG_DESCRIPTION | wx.TAB_TRAVERSAL)
        self.proPrefs.SetExtraStyle(wx.propgrid.PG_EX_MODE_BUTTONS)
        # assign panels to splitter
        self.splitter.SplitVertically(
            self.lstPrefPages, self.proPrefs
        )
        # move sash to min extent of page ctrls
        self.splitter.SetMinimumPaneSize(prefsImageSize[0] + 2)

        if sys.platform == 'win32':
            # works on windows only since it has a column
            self.splitter.SetSashPosition(self.lstPrefPages.GetColumnWidth(0))
        else:
            # size that make sense on other platforms
            self.splitter.SetSashPosition(150)

        self.SetSizer(bSizer1)
        self.Layout()

        # Connect Events
        self.lstPrefPages.Bind(
            wx.EVT_LIST_ITEM_DESELECTED, self.OnPrefPageDeselected)
        self.lstPrefPages.Bind(
            wx.EVT_LIST_ITEM_SELECTED, self.OnPrefPageSelected)
        self.proPrefs.Bind(pg.EVT_PG_CHANGED, self.OnPropPageChanged)
        self.proPrefs.Bind(pg.EVT_PG_CHANGING, self.OnPropPageChanging)

        # categories and their items are stored here
        self.sections = collections.OrderedDict()

        # pages in the property manager
        self.pages = dict()
        self.pageNames = dict()

        # help text
        self.helpText = dict()

        self.pageIdx = 0

    def __del__(self):
        pass

    def setSelection(self, page):
        """Select the page."""
        # set the page
        self.lstPrefPages.Focus(1)
        self.lstPrefPages.Select(page)

    def addPage(self, label, name, sections=(), bitmap=None):
        """Add a page to the property grid manager."""

        if name in self.pages.keys():
            raise ValueError("Page already exists.")

        for s in sections:
            if s not in self.sections.keys():
                self.sections[s] = dict()

        nbBitmap = icons.ButtonIcon(stem=bitmap, size=(48, 48)).bitmap
        if nbBitmap.IsOk():
            self.prefsImages.Add(nbBitmap)

        self.pages[self.pageIdx] = (self.proPrefs.AddPage(name, wx.NullBitmap),
                                    list(sections))
        self.pageNames[name] = self.pageIdx
        self.lstPrefPages.InsertItem(
            self.lstPrefPages.GetItemCount(), label, self.pageIdx)

        self.pageIdx += 1

    def addStringItem(self, section, label=wx.propgrid.PG_LABEL,
                      name=wx.propgrid.PG_LABEL, value='', helpText=""):
        """Add a string property to a category.

        Parameters
        ----------
        section : str
            Category name to add the item too.
        label : str
            Label to be displayed in the property grid.
        name : str
            Internal name for the property.
        value : str
            Default value for the property.
        helpText: str
            Help text for this item.

        """
        # create a new category if not present
        if section not in self.sections.keys():
            self.sections[section] = dict()

        # if isinstance(page, str):
        #     page = self.proPrefs.GetPageByName(page)
        # else
        #     page = self.proPrefs.GetPage(page)
        self.sections[section].update(
            {name: wx.propgrid.StringProperty(label, name, value=str(value))})

        self.helpText[name] = helpText

    def addStringArrayItem(self, section, label=wx.propgrid.PG_LABEL,
                           name=wx.propgrid.PG_LABEL, values=(), helpText=""):
        """Add a string array item."""
        if section not in self.sections.keys():
            self.sections[section] = dict()

        self.sections[section].update(
            {name: wx.propgrid.ArrayStringProperty(
                label, name, value=[str(i) for i in values])})

        self.helpText[name] = helpText

    def addBoolItem(self, section, label=wx.propgrid.PG_LABEL,
                    name=wx.propgrid.PG_LABEL, value=False, helpText=""):
        if section not in self.sections.keys():
            self.sections[section] = dict()

        self.sections[section].update(
            {name: wx.propgrid.BoolProperty(label, name, value)})

        self.helpText[name] = helpText

    def addFileItem(self, section, label=wx.propgrid.PG_LABEL,
                    name=wx.propgrid.PG_LABEL, value='', helpText=""):
        if section not in self.sections.keys():
            self.sections[section] = []

        prop = wx.propgrid.FileProperty(label, name, value)
        self.sections[section].update({name: prop})
        prop.SetAttribute(wx.propgrid.PG_FILE_SHOW_FULL_PATH, True)

        self.helpText[name] = helpText

    def addDirItem(self, section, label=wx.propgrid.PG_LABEL,
                    name=wx.propgrid.PG_LABEL, value='', helpText=""):
        if section not in self.sections.keys():
            self.sections[section] = dict()

        self.sections[section].update(
            {name: wx.propgrid.DirProperty(label, name, value)})

        self.helpText[name] = helpText

    def addIntegerItem(self, section, label=wx.propgrid.PG_LABEL,
                       name=wx.propgrid.PG_LABEL, value=0, helpText=""):
        """Add an integer property to a category.

        Parameters
        ----------
        section : str
            Category name to add the item too.
        label : str
            Label to be displayed in the property grid.
        name : str
            Internal name for the property.
        value : int
            Default value for the property.
        helpText: str
            Help text for this item.

        """
        if section not in self.sections.keys():
            self.sections[section] = dict()

        self.sections[section].update(
            {name: wx.propgrid.IntProperty(label, name, value=int(value))})

        self.helpText[name] = helpText

    def addEnumItem(self, section, label=wx.propgrid.PG_LABEL,
                    name=wx.propgrid.PG_LABEL, labels=(), values=(), value=0,
                    helpText=""):
        if section not in self.sections.keys():
            self.sections[section] = dict()

        self.sections[section].update({
            name: wx.propgrid.EnumProperty(label, name, labels, values, value)})

        self.helpText[name] = helpText

    def populateGrid(self):
        """Go over pages and add items to the property grid."""
        for i in range(self.proPrefs.GetPageCount()):
            pagePtr, sections = self.pages[i]
            pagePtr.Clear()

            for s in sections:
                _ = pagePtr.Append(pg.PropertyCategory(s, s))
                for name, prop in self.sections[s].items():
                    if name in prefs.legacy:
                        # If this is included in the config file only for legacy, don't show it
                        continue

                    item = pagePtr.Append(prop)

                    # set the appropriate control to edit the attribute
                    if isinstance(prop, wx.propgrid.IntProperty):
                        self.proPrefs.SetPropertyEditor(item, "SpinCtrl")
                    elif isinstance(prop, wx.propgrid.BoolProperty):
                        self.proPrefs.SetPropertyAttribute(
                            item, "UseCheckbox", True)
                    try:
                        self.proPrefs.SetPropertyHelpString(
                            item, self.helpText[item.GetName()])
                    except KeyError:
                        pass

        self.proPrefs.SetSplitterLeft()
        self.setSelection(0)

    def setPrefVal(self, section, name, value):
        """Set the value of a preference."""
        try:
            self.sections[section][name].SetValue(value)
            return True
        except KeyError:
            return False

    def getPrefVal(self, section, name):
        """Get the value of a preference."""
        try:
            return self.sections[section][name].GetValue()
        except KeyError:
            return None

    def OnPrefPageDeselected(self, event):
        event.Skip()

    def OnPrefPageSelected(self, event):
        sel = self.lstPrefPages.GetFirstSelected()

        if sel >= 0:
            self.proPrefs.SelectPage(sel)

        event.Skip()

    def OnPropPageChanged(self, event):
        event.Skip()

    def OnPropPageChanging(self, event):
        event.Skip()

    def isModified(self):
        return self.proPrefs.IsAnyModified()


class PreferencesDlg(wx.Dialog):
    """Class for a dialog which edits PsychoPy's preferences.
    """
    def __init__(self, app):
        wx.Dialog.__init__(
            self, None, id=wx.ID_ANY,
            title=_translate('PsychoPy Preferences'),
            pos=wx.DefaultPosition, size=wx.Size(800, 600),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.app = app
        self.prefsCfg = self.app.prefs.userPrefsCfg
        self.prefsSpec = self.app.prefs.prefsSpec

        self._pages = {}  # property grids for each page

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        sbMain = wx.BoxSizer(wx.VERTICAL)

        self.pnlMain = wx.Panel(
            self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.TAB_TRAVERSAL)
        sbPrefs = wx.BoxSizer(wx.VERTICAL)

        self.proPrefs = PrefPropGrid(
            self.pnlMain, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.LB_DEFAULT)

        # add property pages to the manager
        self.proPrefs.addPage(
            label=_translate('General'),
            name='general',
            sections=['general'],
            bitmap='preferences-general')
        self.proPrefs.addPage(
            label=_translate('Application'),
            name='app',
            sections=['app', 'builder', 'coder'],
            bitmap='preferences-app'
        )
        self.proPrefs.addPage(
            label=_translate('Pilot mode'),
            name='piloting',
            sections=['piloting'],
            bitmap='preferences-pilot'
        )
        self.proPrefs.addPage(
            label=_translate('Key Bindings'),
            name='keyBindings',
            sections=['keyBindings'],
            bitmap='preferences-keyboard'
        )
        self.proPrefs.addPage(
            label=_translate('Hardware'),
            name='hardware',
            sections=['hardware'],
            bitmap='preferences-hardware'
        )
        self.proPrefs.addPage(
            label=_translate('Connections'),
            name='connections',
            sections=['connections'],
            bitmap='preferences-conn'
        )
        self.proPrefs.populateGrid()

        sbPrefs.Add(self.proPrefs, 1, wx.EXPAND)

        self.stlMain = wx.StaticLine(
            self.pnlMain, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.LI_HORIZONTAL)
        sbPrefs.Add(self.stlMain, 0, wx.EXPAND | wx.ALL, 5)

        # dialog controls, have builtin localization
        sdbControls = wx.BoxSizer(wx.HORIZONTAL)
        self.sdbControlsHelp = wx.Button(self.pnlMain, wx.ID_HELP, _translate(" Help "))
        sdbControls.Add(self.sdbControlsHelp, 0,
                        wx.LEFT | wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                        border=3)
        sdbControls.AddStretchSpacer()
        # Add Okay and Cancel buttons
        self.sdbControlsApply = wx.Button(self.pnlMain, wx.ID_APPLY, _translate(" Apply "))
        self.sdbControlsOK = wx.Button(self.pnlMain, wx.ID_OK, _translate(" OK "))
        self.sdbControlsCancel = wx.Button(self.pnlMain, wx.ID_CANCEL, _translate(" Cancel "))
        if sys.platform == "win32":
            btns = [self.sdbControlsOK, self.sdbControlsApply, self.sdbControlsCancel]
        else:
            btns = [self.sdbControlsCancel, self.sdbControlsApply, self.sdbControlsOK]
        sdbControls.Add(btns[0], 0,
                        wx.ALL | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
                        border=3)
        sdbControls.Add(btns[1], 0,
                        wx.ALL | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
                        border=3)
        sdbControls.Add(btns[2], 0,
                        wx.ALL | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
                        border=3)
        sbPrefs.Add(sdbControls, flag=wx.ALL | wx.EXPAND, border=3)

        self.pnlMain.SetSizer(sbPrefs)
        self.pnlMain.Layout()
        sbPrefs.Fit(self.pnlMain)
        sbMain.Add(self.pnlMain, 1, wx.EXPAND | wx.ALL, 8)

        self.SetSizer(sbMain)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.sdbControlsApply.Bind(wx.EVT_BUTTON, self.OnApplyClicked)
        self.sdbControlsCancel.Bind(wx.EVT_BUTTON, self.OnCancelClicked)
        self.sdbControlsHelp.Bind(wx.EVT_BUTTON, self.OnHelpClicked)
        self.sdbControlsOK.Bind(wx.EVT_BUTTON, self.OnOKClicked)

        # system fonts for font properties
        self.fontList = ['From theme...'] + list(getSystemFonts(fixedWidthOnly=True))

        # valid themes
        themePath = self.GetTopLevelParent().app.prefs.paths['themes']
        self.themeList = []
        for file in Path(themePath).glob("*.json"):
            self.themeList.append(file.stem)

        # get sound devices for "audioDevice" property
        try:
            devnames = sorted(sound.getDevices('output'))
        except (ValueError, OSError, ImportError, AttributeError):
            devnames = []

        audioConf = self.prefsCfg['hardware']['audioDevice']
        self.audioDevDefault = audioConf \
            if type(audioConf) != list else list(audioConf)
        self.audioDevNames = [
            dev.replace('\r\n', '') for dev in devnames
            if dev != self.audioDevDefault]

        self.populatePrefs()

    def __del__(self):
        pass

    def populatePrefs(self):
        """Populate pages with property items for each preference."""
        # clear pages
        for sectionName in self.prefsSpec.keys():
            prefsSection = self.prefsCfg[sectionName]
            specSection = self.prefsSpec[sectionName]

            for prefName in specSection:
                if prefName in ['version']:  # any other prefs not to show?
                    continue
                # allowModuleImports pref is handled by generateSpec.py
                # NB if something is in prefs but not in spec then it won't be
                # shown (removes outdated prefs)
                thisPref = prefsSection[prefName]
                thisSpec = specSection[prefName]

                # for keybindings replace Ctrl with Cmd on Mac
                if platform.system() == 'Darwin' and \
                        sectionName == 'keyBindings':
                    if thisSpec.startswith('string'):
                        thisPref = thisPref.replace('Ctrl+', 'Cmd+')

                # can we translate this pref?
                pLabel = prefName

                # get tooltips from comment lines from the spec, as parsed by
                # configobj
                helpText = ''
                hints = self.prefsSpec[sectionName].comments[prefName]  # a list
                if len(hints):
                    # use only one comment line, from right above the pref
                    hint = hints[-1].lstrip().lstrip('#').lstrip()
                    helpText = _translate(hint)

                if type(thisPref) == bool:
                    # only True or False - use a checkbox
                    self.proPrefs.addBoolItem(
                        sectionName, pLabel, prefName, thisPref,
                        helpText=helpText)

                # # properties for fonts, dropdown gives a list of system fonts
                elif prefName in ('codeFont', 'commentFont', 'outputFont'):
                    try:
                        default = self.fontList.index(thisPref)
                    except ValueError:
                        default = 0
                    labels = [_translate(font) for font in self.fontList]
                    self.proPrefs.addEnumItem(
                            sectionName,
                            pLabel,
                            prefName,
                            labels=labels,
                            values=[i for i in range(len(self.fontList))],
                            value=default, helpText=helpText)
                elif prefName in ('theme',):
                    try:
                        default = self.themeList.index(thisPref)
                    except ValueError:
                        default = self.themeList.index("PsychopyLight")
                    self.proPrefs.addEnumItem(
                            sectionName,
                            pLabel,
                            prefName,
                            labels=self.themeList,
                            values=[i for i in range(len(self.themeList))],
                            value=default, helpText=helpText)
                elif prefName == 'locale':
                    thisPref = self.app.prefs.app['locale']
                    # '' corresponds to system locale
                    locales = [''] + self.app.localization.available
                    try:
                        default = locales.index(thisPref)
                    except ValueError:
                        # set default locale ''
                        default = locales.index('')
                    # '' must be appended after other labels are translated
                    labels = self.app.localization.available.copy()
                    labels.insert(0, _translate('system locale'))
                    self.proPrefs.addEnumItem(
                            sectionName,
                            pLabel,
                            prefName,
                            labels=labels,
                            values=[i for i in range(len(locales))],
                            value=default, helpText=helpText)
                # # single directory
                elif prefName in ('unpackedDemosDir',):
                    self.proPrefs.addDirItem(
                        sectionName, pLabel, prefName, thisPref,
                        helpText=helpText)
                # single file
                elif prefName in ('flac', 'appKeyGoogleCloud',):
                    self.proPrefs.addFileItem(
                        sectionName, pLabel, prefName, thisPref,
                        helpText=helpText)
                # window backend items
                elif prefName == 'winType':
                    from psychopy.visual.backends import getAvailableWinTypes
                    labels = getAvailableWinTypes()
                    default = labels.index('pyglet')  # is always included
                    self.proPrefs.addEnumItem(
                            sectionName,
                            pLabel,
                            prefName,
                            labels=labels,
                            values=[i for i in range(len(labels))],
                            value=default, helpText=helpText)
                # # audio latency mode for the PTB driver
                elif prefName == 'audioLatencyMode':
                    # get the labels from above
                    labels = []
                    for val, labl in audioLatencyLabels.items():
                        labels.append(u'{}: {}'.format(val, labl))

                    # get the options from the config file spec
                    vals = thisSpec.replace("option(", "").replace("'", "")
                    # item -1 is 'default=x' from spec
                    vals = vals.replace(", ", ",").split(',')

                    try:
                        # set the field to the value in the pref
                        default = int(thisPref)
                    except ValueError:
                        try:
                            # use first if default not in list
                            default = int(vals[-1].strip('()').split('=')[1])
                        except (IndexError, TypeError, ValueError):
                            # no default
                            default = 0

                    self.proPrefs.addEnumItem(
                            sectionName,
                            pLabel,
                            prefName,
                            labels=labels,
                            values=[i for i in range(len(labels))],
                            value=default, helpText=helpText)
                # # option items are given a dropdown, current value is shown
                # # in the box
                elif thisSpec.startswith('option') or prefName == 'audioDevice':
                    if prefName == 'audioDevice':
                        options = self.audioDevNames
                        try:
                            default = self.audioDevNames.index(
                                self.audioDevDefault[0])
                        except ValueError:
                            default = 0
                    else:
                        vals = thisSpec.replace("option(", "").replace("'", "")
                        # item -1 is 'default=x' from spec
                        vals = vals.replace(", ", ",").split(',')
                        options = vals[:-1]
                        try:
                            # set the field to the value in the pref
                            default = options.index(thisPref)
                        except ValueError:
                            try:
                                # use first if default not in list
                                default = vals[-1].strip('()').split('=')[1]
                            except IndexError:
                                # no default
                                default = 0

                    labels = []  # display only
                    for opt in options:
                        labels.append(opt)

                    self.proPrefs.addEnumItem(
                            sectionName,
                            pLabel,
                            prefName,
                            labels=labels,
                            values=[i for i in range(len(labels))],
                            value=default, helpText=helpText)
                    if prefName == 'builderLayout':
                        item = self.proPrefs.sections[sectionName][prefName]
                        for i in range(len(item.GetChoices())):
                            choice = item.GetChoices()[i]
                            icon = icons.ButtonIcon(stem=choice.Text).bitmap
                            choice.SetBitmap(icon)
                # # lists are given a property that can edit and reorder items
                elif thisSpec.startswith('list'):  # list
                    self.proPrefs.addStringArrayItem(
                        sectionName, pLabel, prefName,
                        [str(i) for i in thisPref], helpText)
                # integer items
                elif thisSpec.startswith('integer'):  # integer
                    self.proPrefs.addIntegerItem(
                        sectionName, pLabel, prefName, thisPref, helpText)
                # # all other items just use a string field
                else:
                    self.proPrefs.addStringItem(
                        sectionName, pLabel, prefName, thisPref, helpText)

        self.proPrefs.populateGrid()

    def applyPrefs(self):
        """Write preferences to the current configuration."""
        if not self.proPrefs.isModified():
            return

        if platform.system() == 'Darwin':
            re_cmd2ctrl = re.compile(r'^Cmd\+', re.I)

        for sectionName in self.prefsSpec:
            for prefName in self.prefsSpec[sectionName]:
                if prefName in ['version']:  # any other prefs not to show?
                    continue

                thisPref = self.proPrefs.getPrefVal(sectionName, prefName)
                # handle special cases
                if prefName in ('codeFont', 'commentFont', 'outputFont'):
                    self.prefsCfg[sectionName][prefName] = \
                        self.fontList[thisPref]
                    continue
                if prefName in ('theme',):
                    self.app.theme = self.prefsCfg[sectionName][prefName] = self.themeList[thisPref]
                    continue
                elif prefName == 'audioDevice':
                    self.audioDevDefault = [self.audioDevNames[thisPref]]
                    self.prefsCfg[sectionName][prefName] = self.audioDevDefault
                    continue
                elif prefName == 'locale':
                    # '' corresponds to system locale
                    locales = [''] + self.app.localization.available
                    self.app.prefs.app['locale'] = \
                        locales[thisPref]
                    self.prefsCfg[sectionName][prefName] = \
                        locales[thisPref]
                    continue

                # remove invisible trailing whitespace:
                if hasattr(thisPref, 'strip'):
                    thisPref = thisPref.strip()
                # regularize the display format for keybindings
                if sectionName == 'keyBindings':
                    thisPref = thisPref.replace(' ', '')
                    thisPref = '+'.join([part.capitalize()
                                         for part in thisPref.split('+')])
                    if platform.system() == 'Darwin':
                        # key-bindings were displayed as 'Cmd+O', revert to
                        # 'Ctrl+O' internally
                        thisPref = re_cmd2ctrl.sub('Ctrl+', thisPref)
                self.prefsCfg[sectionName][prefName] = thisPref

                # make sure list values are converted back to lists (from str)
                if self.prefsSpec[sectionName][prefName].startswith('list'):
                    try:
                        # if thisPref is not a null string, do eval() to get a
                        # list.
                        if thisPref == '' or type(thisPref) == list:
                            newVal = thisPref
                        else:
                            newVal = eval(thisPref)
                    except Exception:
                        # if eval() failed, show warning dialog and return
                        pLabel = prefName
                        sLabel = sectionName
                        txt = _translate(
                            'Invalid value in "%(pref)s" ("%(section)s" Tab)')
                        msg = txt % {'pref': pLabel, 'section': sLabel}
                        title = _translate('Error')
                        warnDlg = dialogs.MessageDialog(parent=self,
                                                        message=msg,
                                                        type='Info',
                                                        title=title)
                        warnDlg.ShowModal()
                        return
                    if type(newVal) != list:
                        self.prefsCfg[sectionName][prefName] = [newVal]
                    else:
                        self.prefsCfg[sectionName][prefName] = newVal
                elif self.prefsSpec[sectionName][prefName].startswith('option'):
                    vals = self.prefsSpec[sectionName][prefName].replace(
                        "option(", "").replace("'", "")
                    # item -1 is 'default=x' from spec
                    options = vals.replace(", ", ",").split(',')[:-1]
                    self.prefsCfg[sectionName][prefName] = options[thisPref]

        self.app.prefs.saveUserPrefs()  # includes a validation
        # maybe then go back and set GUI from prefs again, because validation
        # may have changed vals?
        # > sure, why not? - mdc
        self.populatePrefs()

        # Update Builder window if needed
        if self.app.builder:
            self.app.builder.updateAllViews()

        # after validation, update the UI
        self.updateFramesUI()

    def updateFramesUI(self):
        """Update the Coder UI (eg. fonts, themes, etc.) from prefs."""
        for frame in self.app.getAllFrames():
            if frame.frameType == 'builder':
                frame.layoutPanes()
            elif frame.frameType == 'coder':
                # apply settings over document pages
                for ii in range(frame.notebook.GetPageCount()):
                    doc = frame.notebook.GetPage(ii)
                    doc.theme = prefs.app['theme']
                for ii in range(frame.shelf.GetPageCount()):
                    doc = frame.shelf.GetPage(ii)
                    doc.theme = prefs.app['theme']

                # apply console font, not handled by theme system ATM
                if hasattr(frame, 'shell'):
                    frame.shell.setFonts()

    def OnApplyClicked(self, event):
        """Apply button clicked, this makes changes to the UI without leaving
        the preference dialog. This can be used to see the effects of setting
        changes before closing the dialog.

        """
        self.applyPrefs()  # saves the preferences
        event.Skip()

    def OnCancelClicked(self, event):
        event.Skip()

    def OnHelpClicked(self, event):
        self.app.followLink(url=self.app.urls["prefs"])
        event.Skip()

    def OnOKClicked(self, event):
        """Called when OK is clicked. This closes the dialog after applying the
        settings.
        """
        self.applyPrefs()
        event.Skip()


if __name__ == '__main__':
    from psychopy import preferences
    if parse_version(wx.__version__) < parse_version('2.9'):
        app = wx.PySimpleApp()
    else:
        app = wx.App(False)
    # don't do this normally - use the existing psychopy.prefs instance
    app.prefs = preferences.Preferences()
    dlg = PreferencesDlg(app)
    dlg.ShowModal()
