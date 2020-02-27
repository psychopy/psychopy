#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from past.builtins import basestring
from builtins import str
import wx
import wx.propgrid as pg
import platform
import re
import os

from . import dialogs
from psychopy import localization
from psychopy.localization import _translate
from pkg_resources import parse_version
from psychopy import sound
from psychopy.app.utils import getSystemFonts

# this will be overridden by the size of the scrolled panel making the prefs
dlgSize = (600, 500)

# labels mappings for display:
_localized = {
    # section labels:
    'general': _translate('General'),
    'app': _translate('App'),
    'builder': "Builder",  # not localized
    'coder': "Coder",  # not localized
    'hardware': _translate('Hardware'),
    'connections': _translate('Connections'),
    'keyBindings': _translate('Key bindings'),
    # pref labels:
    'winType': _translate("window type"),
    'units': _translate("units"),
    'fullscr': _translate("full-screen"),
    'allowGUI': _translate("allow GUI"),
    'paths': _translate('paths'),
    'audioLib': _translate("audio library"),
    'audioDriver': _translate("audio driver"),
    'audioDevice': _translate("audio device"),
    'audioLatencyMode': _translate("audio latency mode"),
    'flac': _translate('flac audio compression'),
    'parallelPorts': _translate("parallel ports"),
    'qmixConfiguration': _translate("Qmix configuration"),
    'shutdownKey': _translate("shutdown key"),
    'shutdownKeyModifiers': _translate("shutdown key modifier keys"),
    'showStartupTips': _translate("show start-up tips"),
    'largeIcons': _translate("large icons"),
    'defaultView': _translate("default view"),
    'resetPrefs': _translate('reset preferences'),
    'autoSavePrefs': _translate('auto-save prefs'),
    'debugMode': _translate('debug mode'),
    'locale': _translate('locale'),
    'readonly': _translate('read-only'),
    'codeFont': _translate('code font'),
    'commentFont': _translate('comment font'),
    'outputFont': _translate('output font'),
    'outputFontSize': _translate('output font size'),
    'codeFontSize': _translate('code font size'),
    'showSourceAsst': _translate('show source asst'),
    'showOutput': _translate('show output'),
    'reloadPrevFiles': _translate('reload previous files'),
    'preferredShell': _translate('preferred shell'),
    'reloadPrevExp': _translate('reload previous exp'),
    'unclutteredNamespace': _translate('uncluttered namespace'),
    'componentsFolders': _translate('components folders'),
    'hiddenComponents': _translate('hidden components'),
    'unpackedDemosDir': _translate('unpacked demos dir'),
    'savedDataFolder': _translate('saved data folder'),
    'topFlow': _translate('Flow at top'),
    'alwaysShowReadme': _translate('always show readme'),
    'maxFavorites': _translate('max favorites'),
    'proxy': _translate('proxy'),
    'autoProxy': _translate('auto-proxy'),
    'allowUsageStats': _translate('allow usage stats'),
    'checkForUpdates': _translate('check for updates'),
    'timeout': _translate('timeout'),
    'open': _translate('open'),
    'new': _translate('new'),
    'save': _translate('save'),
    'saveAs': _translate('save as'),
    'print': _translate('print'),
    'close': _translate('close'),
    'quit': _translate('quit'),
    'preferences': _translate('preferences'),
    'exportHTML': _translate('export HTML'),
    'cut': _translate('cut'),
    'copy': _translate('copy'),
    'paste': _translate('paste'),
    'duplicate': _translate('duplicate'),
    'indent': _translate('indent'),
    'dedent': _translate('dedent'),
    'smartIndent': _translate('smart indent'),
    'find': _translate('find'),
    'findAgain': _translate('find again'),
    'undo': _translate('undo'),
    'redo': _translate('redo'),
    'comment': _translate('comment'),
    'uncomment': _translate('uncomment'),
    'toggle comment': _translate('toggle comment'),
    'fold': _translate('fold'),
    'enlargeFont': _translate('enlarge Font'),
    'shrinkFont': _translate('shrink Font'),
    'analyseCode': _translate('analyze code'),
    'compileScript': _translate('compile script'),
    'runScript': _translate('run script'),
    'stopScript': _translate('stop script'),
    'toggleWhitespace': _translate('toggle whitespace'),
    'toggleEOLs': _translate('toggle EOLs'),
    'toggleIndentGuides': _translate('toggle indent guides'),
    'newRoutine': _translate('new Routine'),
    'copyRoutine': _translate('copy Routine'),
    'pasteRoutine': _translate('paste Routine'),
    'pasteCompon': _translate('paste Component'),
    'toggleOutputPanel': _translate('toggle output panel'),
    'renameRoutine': _translate('rename Routine'),
    'switchToBuilder': _translate('switch to Builder'),
    'switchToCoder': _translate('switch to Coder'),
    'switchToRunner': _translate('switch to Runner'),
    'largerFlow': _translate('larger Flow'),
    'smallerFlow': _translate('smaller Flow'),
    'largerRoutine': _translate('larger routine'),
    'smallerRoutine': _translate('smaller routine'),
    'toggleReadme': _translate('toggle readme'),
    'projectsLogIn': _translate('login to projects'),
    'pavlovia_logIn': _translate('login to pavlovia'),
    'OSF_logIn': _translate('login to OSF'),
    'projectsSync': _translate('sync projects'),
    'projectsFind': _translate('find projects'),
    'projectsOpen': _translate('open projects'),
    'projectsNew': _translate('new projects'),
    # pref wxChoice lists:
    'last': _translate('same as last session'),
    'both': _translate('both Builder & Coder'),
    'keep': _translate('same as in the file'),  # line endings
    # not translated:
    'pix': 'pix',
    'deg': 'deg',
    'cm': 'cm',
    'norm': 'norm',
    'height': 'height',
    'pyshell': 'pyshell',
    'iPython': 'iPython'
}
# add pre-translated names-of-langauges, for display in locale pref:
_localized.update(localization.locname)

audioLatencyLabels = {0:_translate('Latency not important'),
                      1:_translate('Share low-latency driver'),
                      2:_translate('Exclusive low-latency'),
                      3:_translate('Aggressive low-latency'),
                      4:_translate('Latency critical')}


class PreferencesDlg(wx.Dialog):
    """Class for a dialog which edits PsychoPy's preferences.
    """
    def __init__(self, app):
        wx.Dialog.__init__(
            self, None, id=wx.ID_ANY, title=u"PsychoPy Preferences",
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

        self.nbPrefs = wx.Listbook(
            self.pnlMain, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.LB_DEFAULT)

        nbPrefsImageSize = wx.Size(48, 48)
        self.nbPrefsIndex = 0
        self.nbPrefsImages = wx.ImageList(
            nbPrefsImageSize.GetWidth(), nbPrefsImageSize.GetHeight())
        self.nbPrefs.AssignImageList(self.nbPrefsImages)

        # add pages
        self._pages = {
            'general': self.addPrefPage(
                'General', 'general', 'preferences-general48.png', True),
            'app': self.addPrefPage(
                'Application', 'app', 'preferences-app48.png'),
            'keyBindings': self.addPrefPage(
                'Key Bindings', 'keyBindings',
                'preferences-keyboard48.png'),
            'hardware': self.addPrefPage(
                'Hardware', 'hardware', 'preferences-hardware48.png'),
            'connections': self.addPrefPage(
                'Connections', 'connections', 'preferences-conn48.png')
        }

        sbPrefs.Add(self.nbPrefs, 1, wx.EXPAND | wx.ALL, 5)

        self.stlMain = wx.StaticLine(
            self.pnlMain, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.LI_HORIZONTAL)
        sbPrefs.Add(self.stlMain, 0, wx.EXPAND | wx.ALL, 5)

        sdbControls = wx.StdDialogButtonSizer()
        self.sdbControlsHelp = wx.Button(self.pnlMain, wx.ID_HELP)
        sdbControls.AddButton(self.sdbControlsHelp)
        self.sdbControlsApply = wx.Button(self.pnlMain, wx.ID_APPLY)
        sdbControls.AddButton(self.sdbControlsApply)
        self.sdbControlsOK = wx.Button(self.pnlMain, wx.ID_OK)
        sdbControls.AddButton(self.sdbControlsOK)
        self.sdbControlsCancel = wx.Button(self.pnlMain, wx.ID_CANCEL)
        sdbControls.AddButton(self.sdbControlsCancel)

        sdbControls.Realize()

        sbPrefs.Add(sdbControls, 0, wx.ALL | wx.ALIGN_RIGHT, 0)

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
        self.fontList = list(getSystemFonts(fixedWidthOnly=True))

        # get sound devices for "audioDevice" property
        try:
            devnames = sorted(sound.getDevices('output'))
        except (ValueError, OSError, ImportError):
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

    def addPrefPage(self, label, sectionName, bitmap, sel=False):
        """Add a preferences page."""
        pnlPage = wx.Panel(
            self.nbPrefs, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.TAB_TRAVERSAL)
        sbPage = wx.BoxSizer(wx.VERTICAL)

        propGridManager = pg.PropertyGridManager(
            pnlPage, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.propgrid.PGMAN_DEFAULT_STYLE | wx.propgrid.PG_BOLD_MODIFIED |
            wx.propgrid.PG_DESCRIPTION | wx.propgrid.PG_SPLITTER_AUTO_CENTER)
        propGridManager.SetExtraStyle(wx.propgrid.PG_EX_MODE_BUTTONS)

        _ = propGridManager.AddPage(sectionName, wx.NullBitmap)
        sbPage.Add(propGridManager, 1, wx.EXPAND, 5)

        pnlPage.SetSizer(sbPage)
        pnlPage.Layout()
        sbPage.Fit(pnlPage)
        self.nbPrefs.AddPage(pnlPage, label, sel)
        nbBitmap = wx.Bitmap(
            os.path.join(
                self.app.prefs.paths['resources'],
                bitmap),
            wx.BITMAP_TYPE_ANY)
        if nbBitmap.IsOk():
            self.nbPrefsImages.Add(nbBitmap)
            self.nbPrefs.SetPageImage(self.nbPrefsIndex, self.nbPrefsIndex)
            self.nbPrefsIndex += 1

        return propGridManager

    def populatePrefs(self):
        """Populate pages with pref properties from file."""
        sectionOrdering = ['general', 'app', 'builder', 'coder',
                           'keyBindings', 'hardware', 'connections']

        self.secPropGrids = secPropGrids = {
            'general': self._pages['general'],
            'app': self._pages['app'],
            'builder': self._pages['app'],
            'coder': self._pages['app'],
            'hardware': self._pages['hardware'],
            'connections': self._pages['connections'],
            'keyBindings': self._pages['keyBindings']}

        # clear pages
        for _, propMgr in self._pages.items():
            propMgr.ClearPage(0)

        for sectionName in sectionOrdering:
            propGrid = secPropGrids[sectionName].GetPage(0)

            prefsSection = self.prefsCfg[sectionName]
            specSection = self.prefsSpec[sectionName]

            if sectionName == 'general':
                item = propGrid.Append(
                            pg.PropertyCategory(u"General", u"General"))
                propGrid.SetPropertyHelpString(
                    item,
                    "General preferences for PsychoPy which affect aspects of "
                    "the library and runtime.")
                secPropGrids[sectionName].SelectProperty(item, focus=False)
            elif sectionName == 'app':
                item = propGrid.Append(
                            pg.PropertyCategory(u"Application", u"Application"))
                propGrid.SetPropertyHelpString(
                    item,
                    "General preferences related to the PsychoPy GUI suite "
                    "(Coder, Builder, etc.)")
                secPropGrids[sectionName].SelectProperty(item, focus=False)
            elif sectionName == 'builder':
                item = propGrid.Append(
                            pg.PropertyCategory(u"Builder", u"builder"))
                propGrid.SetPropertyHelpString(
                    item,
                    "Preferences specific to the Builder GUI.")
            elif sectionName == 'coder':
                item = propGrid.Append(
                            pg.PropertyCategory(u"Coder", u"coder"))
                propGrid.SetPropertyHelpString(
                    item,
                    "Preferences specific to the Coder GUI.")
            elif sectionName == 'keyBindings':
                item = propGrid.Append(
                            pg.PropertyCategory(u"Key Bindings", u"keyBindings"))
                propGrid.SetPropertyHelpString(
                    item,
                    "Key bindings for the PsychoPy GUI suite (Builder, Coder, "
                    "etc.) Requires a restart to take effect.")
                secPropGrids[sectionName].SelectProperty(item, focus=False)
            elif sectionName == 'hardware':
                item = propGrid.Append(
                            pg.PropertyCategory(u"Hardware", u"Hardware"))
                propGrid.SetPropertyHelpString(
                    item,
                    "Settings for hardware interfaces and drivers.")
                secPropGrids[sectionName].SelectProperty(item, focus=False)
            elif sectionName == 'connections':
                item = propGrid.Append(
                            pg.PropertyCategory(u"Connections", u"Connections"))
                propGrid.SetPropertyHelpString(
                    item,
                    "Settings for network and internet connections.")
                secPropGrids[sectionName].SelectProperty(item, focus=False)
            else:
                continue

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
                try:
                    pLabel = _localized[prefName]
                except Exception:
                    pLabel = prefName
                if prefName == 'locale':
                    # fake spec -> option: use available locale info not spec file
                    thisSpec = 'option(' + ','.join(
                        [''] + self.app.localization.available) + ', default=xxx)'
                    thisPref = self.app.prefs.app['locale']

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
                    item = propGrid.Append(
                        wx.propgrid.BoolProperty(prefName, value=thisPref))
                    propGrid.SetPropertyAttribute(
                        prefName,
                        "UseCheckbox", True)
                # properties for fonts, dropdown gives a list of system fonts
                elif prefName in ('codeFont', 'commentFont', 'outputFont'):
                    try:
                        default = self.fontList.index(thisPref)
                    except ValueError:
                        default = 0
                    item = propGrid.Append(
                        wx.propgrid.EnumProperty(
                            pLabel,
                            prefName,
                            labels=self.fontList,
                            values=[i for i in range(len(self.fontList))],
                            value=default))
                # single directory
                elif prefName in ('unpackedDemosDir',):
                    item = propGrid.Append(
                        wx.propgrid.DirProperty(
                            pLabel, prefName, thisPref))
                # single file
                elif prefName in ('flac',):
                    item = propGrid.Append(
                        wx.propgrid.FileProperty(
                            pLabel, prefName, thisPref))
                # audio latency mode for the PTB driver
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

                    item = propGrid.Append(
                        wx.propgrid.EnumProperty(
                            pLabel,
                            prefName,
                            labels=labels,
                            values=[i for i in range(len(labels))],
                            value=default))
                # option items are given a dropdown, current value is shown
                # in the box
                elif thisSpec.startswith('option') or prefName == 'audioDevice':
                    if prefName == 'audioDevice':
                        options = self.audioDevNames
                        try:
                            default = self.audioDevNames.index(
                                self.audioDevDefault)
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
                        try:
                            labels.append(_localized[opt])
                        except Exception:
                            labels.append(opt)

                    item = propGrid.Append(
                        wx.propgrid.EnumProperty(
                            pLabel,
                            prefName,
                            labels=labels,
                            values=[i for i in range(len(labels))],
                            value=default))
                # lists are given a property that can edit and reorder items
                elif thisSpec.startswith('list'):  # list
                    item = propGrid.Append(
                        wx.propgrid.ArrayStringProperty(pLabel,
                            prefName, value=[str(i) for i in thisPref]))
                # integer items
                elif thisSpec.startswith('integer'):  # integer
                    item = propGrid.Append(
                        wx.propgrid.IntProperty(pLabel,
                            prefName, value=int(thisPref)))
                    propGrid.SetPropertyEditor(prefName, "SpinCtrl")
                # all other items just use a string field
                else:
                    item = propGrid.Append(
                        wx.propgrid.StringProperty(pLabel,
                            prefName, value=str(thisPref)))

                if item is not None:
                    propGrid.SetPropertyHelpString(item, helpText)

            secPropGrids[sectionName].SetSplitterLeft()

    def listToString(self, seq, depth=8, errmsg='\'too_deep\''):
        """Convert list to string.

        This function is necessary because Unicode characters come to be
        converted to hexadecimal values if unicode() is used to convert a
        list to string. This function applies str() or unicode() to each
        element of the list.
        """
        if depth > 0:
            l = '['
            for e in seq:
                # if element is a sequence, call listToString recursively.
                if isinstance(e, basestring):
                    en = "{!r}, ".format(e)  # using !r adds '' or u'' as needed
                elif hasattr(e, '__iter__'):  # just tuples and lists (but in Py3 str has __iter__)
                    en = self.listToString(e, depth - 1) + ','
                else:
                    e = e.replace('\\', '\\\\').replace("'", "\\'")  # in path names?
                    en = "{!r}, ".format(e)
                l += en
            # remove unnecessary comma
            if l[-1] == ',':
                l = l[:-1]
            l += ']'
        else:
            l = errmsg
        return l

    def applyPrefs(self):
        """Write preferences to the current configuration."""
        re_cmd2ctrl = re.compile('^Cmd\+', re.I)
        for sectionName in self.prefsSpec:
            ctrls = self.secPropGrids[sectionName].GetPropertyValues(
                inc_attributes=False)
            for prefName in self.prefsSpec[sectionName]:
                if prefName in ['version']:  # any other prefs not to show?
                    continue

                thisPref = ctrls[prefName]
                # handle special cases
                if prefName in ('codeFont', 'commentFont', 'outputFont'):
                    self.prefsCfg[sectionName][prefName] = \
                        self.fontList[thisPref]
                    continue
                elif prefName == 'audioDevice':
                    self.prefsCfg[sectionName][prefName] = \
                        self.audioDevNames[thisPref]
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
                        try:
                            pLabel = _localized[prefName]
                            sLabel = _localized[sectionName]
                        except Exception:
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
                        resp = warnDlg.ShowModal()
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

    # Virtual event handlers, overide them in your derived class
    def OnApplyClicked(self, event):
        self.applyPrefs()
        # maybe then go back and set GUI from prefs again, because validation
        # may have changed vals?
        # > sure, why not? - mdc
        self.populatePrefs()
        event.Skip()

    def OnCancelClicked(self, event):
        event.Skip()

    def OnHelpClicked(self, event):
        currentPane = self.nbPrefs.GetPageText(self.nbPrefs.GetSelection())
        # # what the url should be called in psychopy.app.urls
        urlName = "prefs.%s" % currentPane
        if urlName in self.app.urls:
            url = self.app.urls[urlName]
        else:
            # couldn't find that section - use default prefs
            url = self.app.urls["prefs"]
        self.app.followLink(url=url)
        event.Skip()

    def OnOKClicked(self, event):
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
