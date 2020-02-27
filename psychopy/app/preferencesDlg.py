#!/usr/bin/env python
# -*- coding: utf-8 -*-

from __future__ import absolute_import, print_function

from past.builtins import basestring
from builtins import str
from builtins import object
import wx
import wx.lib.scrolledpanel as scrolled
import wx.lib.agw.flatnotebook as fnb
import platform
import re
import copy
import os

from . import dialogs
from psychopy import logging, localization
from psychopy.exceptions import DependencyError
from psychopy.localization import _translate
from pkg_resources import parse_version
from psychopy import sound

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
    defaultStyle = (wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT |
                    wx.TAB_TRAVERSAL | wx.RESIZE_BORDER)

    def __init__(self, app, pos=wx.DefaultPosition, size=dlgSize,
                 style=defaultStyle):
        title = _translate("PsychoPy Preferences")
        wx.Dialog.__init__(self, None, -1, title, pos, size, style)
        self.app = app
        self.Center()
        self.prefsCfg = self.app.prefs.userPrefsCfg
        self.prefsSpec = self.app.prefs.prefsSpec
        sizer = wx.BoxSizer(wx.VERTICAL)

        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        lineStyle = wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.TOP
        sizer.Add(line, 0, lineStyle, 5)

        # notebook, flatnotebook or something else?

        self.nb = fnb.FlatNotebook(
            self, style=fnb.FNB_NO_X_BUTTON | fnb.FNB_NO_NAV_BUTTONS)
        # self.nb = wx.Notebook(self)  # notebook not nice with lots of pages

        self.ctrls = {}
        sectionOrdering = ['general', 'app', 'builder', 'coder',
                           'hardware', 'connections', 'keyBindings']
        for section in sectionOrdering:
            prefsPage = self.makePrefPage(parent=self.nb,
                                          sectionName=section,
                                          prefsSection=self.prefsCfg[section],
                                          specSection=self.prefsSpec[section])
            self.nb.AddPage(prefsPage, _localized[section])
        self.nb.SetSelection(self.app.prefs.pageCurrent)
        sizer.Add(self.nb, 1, wx.EXPAND)

        aTable = wx.AcceleratorTable([
            (wx.ACCEL_NORMAL, wx.WXK_ESCAPE, wx.ID_CANCEL),
            (wx.ACCEL_NORMAL, wx.WXK_RETURN, wx.ID_OK),
        ])
        self.SetAcceleratorTable(aTable)

        # create buttons
        line = wx.StaticLine(self, -1, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL |
                  wx.RIGHT | wx.TOP, 5)
        btnsizer = wx.StdDialogButtonSizer()
        # ok
        btn = wx.Button(self, wx.ID_OK, _translate('OK'))
        btn.SetHelpText(_translate("Save prefs (in all sections) and close "
                                   "window"))
        btn.Bind(wx.EVT_BUTTON, self.onOK)
        btn.SetDefault()
        btnsizer.AddButton(btn)
        # cancel
        btn = wx.Button(self, wx.ID_CANCEL, _translate('Cancel'))
        btn.SetHelpText(_translate("Cancel any changes (to any panel)"))
        btn.Bind(wx.EVT_BUTTON, self.onCancel)
        btnsizer.AddButton(btn)
        # help
        btn = wx.Button(self, wx.ID_HELP, _translate('Help'))
        btn.SetHelpText(_translate("Get help on prefs"))
        btn.Bind(wx.EVT_BUTTON, self.onHelp)
        btnsizer.AddButton(btn)
        btnsizer.Realize()
        # add buttons to dlg
        sizer.Add(btnsizer, 0, wx.BOTTOM | wx.ALL, 5)

        self.SetSizerAndFit(sizer)
        self.SetAutoLayout(True)
        sizer.Fit(self)

    def onHelp(self, event=None):
        """Uses self.app.followLink() and app/urls.py to go to correct url
        """
        currentPane = self.nb.GetPageText(self.nb.GetSelection())
        # what the url should be called in psychopy.app.urls
        urlName = "prefs.%s" % currentPane
        if urlName in self.app.urls:
            url = self.app.urls[urlName]
        else:
            # couldn't find that section - use default prefs
            url = self.app.urls["prefs"]
        self.app.followLink(url=url)

    def onCancel(self, event=None):
        self.Destroy()

    def onOK(self, event=None):
        self.setPrefsFromCtrls()
        self.app.prefs.pageCurrent = self.nb.GetSelection()
        self.Destroy()

    def makePrefPage(self, parent, sectionName, prefsSection, specSection):
        panel = scrolled.ScrolledPanel(
            parent, -1, size=(dlgSize[0] - 100, dlgSize[1] - 200))
        vertBox = wx.BoxSizer(wx.VERTICAL)
        # add each pref for this section
        for prefName in specSection:
            if prefName in ['version']:  # any other prefs not to show?
                continue
            # allowModuleImports pref is handled by generateSpec.py
            # NB if something is in prefs but not in spec then it won't be
            # shown (removes outdated prefs)
            thisPref = prefsSection[prefName]
            thisSpec = specSection[prefName]
            ctrlName = sectionName + '.' + prefName

            # for keybindings replace Ctrl with Cmd on Mac
            if platform.system() == 'Darwin' and sectionName == 'keyBindings':
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

            # create the actual controls
            self.ctrls[ctrlName] = ctrls = PrefCtrls(
                parent=panel, name=prefName, value=thisPref,
                spec=thisSpec, plabel=pLabel)
            ctrlSizer = wx.BoxSizer(wx.HORIZONTAL)
            ctrlSizer.Add(ctrls.nameCtrl, 0, wx.ALL, 5)
            ctrlSizer.Add(ctrls.valueCtrl, 0, wx.ALL, 5)

            # get tooltips from comment lines from the spec, as parsed by
            # configobj
            hints = self.prefsSpec[sectionName].comments[prefName]  # a list
            if len(hints):
                # use only one comment line, from right above the pref
                hint = hints[-1].lstrip().lstrip('#').lstrip()
                ctrls.valueCtrl.SetToolTip(wx.ToolTip(_translate(hint)))
            else:
                ctrls.valueCtrl.SetToolTip(wx.ToolTip(''))

            vertBox.Add(ctrlSizer)
        # size the panel and setup scrolling
        panel.SetSizer(vertBox)
        panel.SetAutoLayout(True)
        panel.SetupScrolling()
        return panel

    def setPrefsFromCtrls(self):
        # extract values, adjust as needed:
        # a) strip() to remove whitespace
        # b) case-insensitive match for Cmd+ at start of string
        # c) reverse-map locale display names to canonical names (ja_JP)
        re_cmd2ctrl = re.compile('^Cmd\+', re.I)
        for sectionName in self.prefsSpec:
            for prefName in self.prefsSpec[sectionName]:
                if prefName in ['version']:  # any other prefs not to show?
                    continue
                ctrlName = sectionName + '.' + prefName
                ctrl = self.ctrls[ctrlName]
                thisPref = ctrl.getValue()
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
        self.app.prefs.saveUserPrefs()  # includes a validation
        # maybe then go back and set GUI from prefs again, because validation
        # may have changed vals?


class PrefCtrls(object):

    def __init__(self, parent, name, value, spec, plabel):
        """Create a set of ctrls for a particular preference entry
        """
        super(PrefCtrls, self).__init__()
        self.pref = value
        self.parent = parent
        self.name = name
        valueWidth = 200
        labelWidth = 200
        self.nameCtrl = self.valueCtrl = None

        _style = wx.ALIGN_RIGHT | wx.ALIGN_CENTER_VERTICAL
        self.nameCtrl = wx.StaticText(self.parent, -1, plabel,
                                      size=(labelWidth, -1), style=_style)
        if type(value) == bool:
            # only True or False - use a checkbox
            self.valueCtrl = wx.CheckBox(self.parent)
            self.valueCtrl.SetValue(value)
        elif name == 'audioLatencyMode':
            # get the labels from above
            labels = []
            for val, labl in audioLatencyLabels.items():
                labels.append(u'{}: {}'.format(val, labl))
            #get the options from the config file spec
            options = spec.replace("option(", "").replace("'", "")
            # item -1 is 'default=x' from spec
            options = options.replace(", ", ",").split(',')[:-1]

            self.valueCtrl = wx.Choice(self.parent, choices=labels)
            self.valueCtrl._choices = copy.copy(options)  # internal values
            self.valueCtrl.SetSelection(options.index(value))
        elif spec.startswith('option') or name == 'audioDevice':
            if name == 'audioDevice':
                devnames = sorted(sound.getDevices('output'))
                if type(value) == list:
                    value = value[0]
                if value in devnames:
                    options = [value]
                else:
                    options = []
                try:
                    # TODO: this assumes that the driver loaded is current selected
                    # we *could* fix that but hopefully PTB will soon dominate and
                    # then we don't need to worry!
                    for device in devnames:
                        # newline characters must be removed
                        thisDevName = device.replace('\r\n', '')
                        if thisDevName not in options:
                            options.append(thisDevName)
                except (ValueError, OSError, ImportError):
                    pass
            else:
                options = spec.replace("option(", "").replace("'", "")
                # item -1 is 'default=x' from spec
                options = options.replace(", ", ",").split(',')[:-1]
            labels = []  # display only
            for opt in options:
                try:
                    labels.append(_localized[opt])
                except Exception:
                    labels.append(opt)
            self.valueCtrl = wx.Choice(self.parent, choices=labels)
            self.valueCtrl._choices = copy.copy(options)  # internal values
            try:
                self.valueCtrl.SetSelection(0)
            except:
                pass
        elif spec.startswith('list'):  # list
            valuestring = self.listToString(value)
            self.valueCtrl = wx.TextCtrl(self.parent, -1, valuestring,
                                         size=(valueWidth, -1))
        else:  # just use a string
            self.valueCtrl = wx.TextCtrl(self.parent, -1, str(value),
                                         size=(valueWidth, -1))

    def _getCtrlValue(self, ctrl):
        """Retrieve the current value from the control (whatever type of ctrl
        it is, e.g. checkbox.GetValue, textctrl.GetStringSelection
        Different types of control have different methods for retrieving the
        value.  This function checks them all and returns the value or None.
        """
        if ctrl is None:
            return None
        elif hasattr(ctrl, '_choices'):  # for wx.Choice
            if self.name == 'audioDevice':
                # convert the option back to a list with preferred at top
                val = ctrl._choices
                preferred = ctrl._choices.pop(ctrl.GetSelection())
                val.insert(0, preferred)
                return val
            else:
                return ctrl._choices[ctrl.GetSelection()]
        elif hasattr(ctrl, 'GetValue'):  # e.g. TextCtrl
            return ctrl.GetValue()
        elif hasattr(ctrl, 'GetLabel'):  # for wx.StaticText
            return ctrl.GetLabel()
        else:
            msg = "failed to retrieve the value for pref: %s"
            logging.warning(msg % ctrl.valueCtrl)
            return None

    def getValue(self):
        """Get the current value of the value ctrl
        """
        return self._getCtrlValue(self.valueCtrl)

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


import wx
import wx.propgrid as pg


class PropGridPreferencesDlg(wx.Dialog):

    def __init__(self, app):
        wx.Dialog.__init__(
            self, None, id=wx.ID_ANY, title=u"PsychoPy Preferences",
            pos=wx.DefaultPosition, size=wx.Size(800, 600),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)

        self.app = app
        self.prefsCfg = self.app.prefs.userPrefsCfg
        self.prefsSpec = self.app.prefs.prefsSpec

        self.SetSizeHints(wx.DefaultSize, wx.DefaultSize)

        sbMain = wx.BoxSizer(wx.VERTICAL)

        self.pnlMain = wx.Panel(
            self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.TAB_TRAVERSAL)
        sbPrefs = wx.BoxSizer(wx.VERTICAL)

        self.nbPrefs = wx.Listbook(
            self.pnlMain, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.LB_DEFAULT)
        nbPrefsImageSize = wx.Size(64, 64)
        nbPrefsIndex = 0
        nbPrefsImages = wx.ImageList(
            nbPrefsImageSize.GetWidth(), nbPrefsImageSize.GetHeight())
        self.nbPrefs.AssignImageList(nbPrefsImages)
        self.pnlGeneral = wx.Panel(
            self.nbPrefs, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.TAB_TRAVERSAL)
        sbGeneralConfig = wx.BoxSizer(wx.VERTICAL)

        self.pgMgrGeneral = pg.PropertyGridManager(
            self.pnlGeneral, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.propgrid.PGMAN_DEFAULT_STYLE | wx.propgrid.PG_BOLD_MODIFIED |
            wx.propgrid.PG_DESCRIPTION | wx.propgrid.PG_SPLITTER_AUTO_CENTER |
            wx.propgrid.PG_TOOLTIPS | wx.TAB_TRAVERSAL)
        self.pgMgrGeneral.SetExtraStyle(wx.propgrid.PG_EX_MODE_BUTTONS)

        self.pgPageGeneral = self.pgMgrGeneral.AddPage(u"Page", wx.NullBitmap)
        sbGeneralConfig.Add(self.pgMgrGeneral, 1, wx.EXPAND, 5)

        self.pnlGeneral.SetSizer(sbGeneralConfig)
        self.pnlGeneral.Layout()
        sbGeneralConfig.Fit(self.pnlGeneral)
        self.nbPrefs.AddPage(self.pnlGeneral, u"General", True)
        nbPrefsBitmap = wx.Bitmap(
            os.path.join(
                self.app.prefs.paths['resources'],
                u"preferences-other.png"),
            wx.BITMAP_TYPE_ANY)
        if (nbPrefsBitmap.IsOk()):
            nbPrefsImages.Add(nbPrefsBitmap)
            self.nbPrefs.SetPageImage(nbPrefsIndex, nbPrefsIndex)
            nbPrefsIndex += 1

        self.pnlApp = wx.Panel(
            self.nbPrefs, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.TAB_TRAVERSAL)
        sbApplicationConfig = wx.BoxSizer(wx.VERTICAL)

        self.pgMgrApplication = pg.PropertyGridManager(
            self.pnlApp, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.propgrid.PGMAN_DEFAULT_STYLE | wx.propgrid.PG_BOLD_MODIFIED |
            wx.propgrid.PG_DESCRIPTION | wx.propgrid.PG_SPLITTER_AUTO_CENTER |
            wx.propgrid.PG_TOOLTIPS | wx.TAB_TRAVERSAL)
        self.pgMgrApplication.SetExtraStyle(wx.propgrid.PG_EX_MODE_BUTTONS)

        self.pgApplicationPage = self.pgMgrApplication.AddPage(
            u"Page", wx.NullBitmap)
        sbApplicationConfig.Add(self.pgMgrApplication, 1, wx.EXPAND, 5)

        self.pnlApp.SetSizer(sbApplicationConfig)
        self.pnlApp.Layout()
        sbApplicationConfig.Fit(self.pnlApp)
        self.nbPrefs.AddPage(self.pnlApp, u"Application", False)
        nbPrefsBitmap = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], u"preferences-system-windows-actions.png"), wx.BITMAP_TYPE_ANY)
        if (nbPrefsBitmap.IsOk()):
            nbPrefsImages.Add(nbPrefsBitmap)
            self.nbPrefs.SetPageImage(nbPrefsIndex, nbPrefsIndex)
            nbPrefsIndex += 1

        self.pnlHardware = wx.Panel(
            self.nbPrefs, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        sbHardwareConfig = wx.BoxSizer(wx.VERTICAL)

        self.pgMgrHardware = pg.PropertyGridManager(
            self.pnlHardware, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
            wx.propgrid.PGMAN_DEFAULT_STYLE | wx.propgrid.PG_BOLD_MODIFIED |
            wx.propgrid.PG_DESCRIPTION | wx.propgrid.PG_SPLITTER_AUTO_CENTER |
            wx.propgrid.PG_TOOLTIPS | wx.TAB_TRAVERSAL)
        self.pgMgrHardware.SetExtraStyle(wx.propgrid.PG_EX_MODE_BUTTONS)

        self.pgHardwarePage = self.pgMgrHardware.AddPage(u"Page", wx.NullBitmap)
        sbHardwareConfig.Add(self.pgMgrHardware, 1, wx.EXPAND, 5)

        self.pnlHardware.SetSizer(sbHardwareConfig)
        self.pnlHardware.Layout()
        sbHardwareConfig.Fit(self.pnlHardware)
        self.nbPrefs.AddPage(self.pnlHardware, u"Hardware", False)
        nbPrefsBitmap = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'audio-card.png'), wx.BITMAP_TYPE_ANY)
        if (nbPrefsBitmap.IsOk()):
            nbPrefsImages.Add(nbPrefsBitmap)
            self.nbPrefs.SetPageImage(nbPrefsIndex, nbPrefsIndex)
            nbPrefsIndex += 1

        self.pnlConnections = wx.Panel(self.nbPrefs, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
        sbConnectionConfig = wx.BoxSizer(wx.VERTICAL)

        self.pgMgrConnections = pg.PropertyGridManager(self.pnlConnections, wx.ID_ANY, wx.DefaultPosition,
                                                       wx.DefaultSize,
                                                       wx.propgrid.PGMAN_DEFAULT_STYLE | wx.propgrid.PG_BOLD_MODIFIED | wx.propgrid.PG_DESCRIPTION | wx.propgrid.PG_SPLITTER_AUTO_CENTER | wx.propgrid.PG_TOOLTIPS | wx.TAB_TRAVERSAL)
        self.pgMgrConnections.SetExtraStyle(wx.propgrid.PG_EX_MODE_BUTTONS)

        self.pgConnectionsPage = self.pgMgrConnections.AddPage(u"Page", wx.NullBitmap)
        sbConnectionConfig.Add(self.pgMgrConnections, 1, wx.EXPAND, 5)

        self.pnlConnections.SetSizer(sbConnectionConfig)
        self.pnlConnections.Layout()
        sbConnectionConfig.Fit(self.pnlConnections)
        self.nbPrefs.AddPage(self.pnlConnections, u"Connections", False)
        nbPrefsBitmap = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], "applications-internet.png"), wx.BITMAP_TYPE_ANY)
        if nbPrefsBitmap.IsOk():
            nbPrefsImages.Add(nbPrefsBitmap)
            self.nbPrefs.SetPageImage(nbPrefsIndex, nbPrefsIndex)
            nbPrefsIndex += 1

        sbPrefs.Add(self.nbPrefs, 1, wx.EXPAND | wx.ALL, 5)

        self.stlMain = wx.StaticLine(self.pnlMain, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
        sbPrefs.Add(self.stlMain, 0, wx.EXPAND | wx.ALL, 5)

        sdbControls = wx.StdDialogButtonSizer()
        self.sdbControlsOK = wx.Button(self.pnlMain, wx.ID_OK)
        sdbControls.AddButton(self.sdbControlsOK)
        self.sdbControlsApply = wx.Button(self.pnlMain, wx.ID_APPLY)
        sdbControls.AddButton(self.sdbControlsApply)
        self.sdbControlsCancel = wx.Button(self.pnlMain, wx.ID_CANCEL)
        sdbControls.AddButton(self.sdbControlsCancel)
        self.sdbControlsHelp = wx.Button(self.pnlMain, wx.ID_HELP)
        sdbControls.AddButton(self.sdbControlsHelp)
        sdbControls.Realize()

        sbPrefs.Add(sdbControls, 0, wx.ALL | wx.EXPAND, 5)

        self.pnlMain.SetSizer(sbPrefs)
        self.pnlMain.Layout()
        sbPrefs.Fit(self.pnlMain)
        sbMain.Add(self.pnlMain, 1, wx.EXPAND | wx.ALL, 5)

        self.SetSizer(sbMain)
        self.Layout()

        self.Centre(wx.BOTH)

        # Connect Events
        self.sdbControlsApply.Bind(wx.EVT_BUTTON, self.OnApplyClicked)
        self.sdbControlsCancel.Bind(wx.EVT_BUTTON, self.OnCancelClicked)
        self.sdbControlsHelp.Bind(wx.EVT_BUTTON, self.OnHelpClicked)
        self.sdbControlsOK.Bind(wx.EVT_BUTTON, self.OnOKClicked)

        self.populatePrefs()

    def __del__(self):
        pass

    def populatePrefs(self):
        """Populate pages with pref properties from file."""
        sectionOrdering = ['general', 'app', 'builder', 'coder',
                           'hardware', 'connections', 'keyBindings']

        secPropGrids = {'general': self.pgPageGeneral,
                        'app': self.pgApplicationPage,
                        'builder': self.pgApplicationPage,
                        'coder': self.pgApplicationPage,
                        'hardware': self.pgHardwarePage,
                        'connections': self.pgConnectionsPage,
                        'keyBindings': self.pgApplicationPage}

        propItems = {'general': dict(),
                     'app': dict(),
                     'builder': dict(),
                     'coder': dict(),
                     'hardware': dict(),
                     'connections': dict(),
                     'keyBindings': dict()}

        # system font enumerator
        fontEnum = wx.FontEnumerator()
        fontEnum.EnumerateFacenames()
        fontList = fontEnum.GetFacenames()

        for sectionName in sectionOrdering:
            propGrid = secPropGrids[sectionName]
            prefsSection = self.prefsCfg[sectionName]
            specSection = self.prefsSpec[sectionName]

            if sectionName == 'general':
                item = propGrid.Append(
                            pg.PropertyCategory(u"General", u"General"))
                propItems[sectionName].update({u"General": item})
                propGrid.SetPropertyHelpString(
                    item,
                    "General preferences for PsychoPy which affect aspects of "
                    "the library and runtime.")
            elif sectionName == 'app':
                item = propGrid.Append(
                            pg.PropertyCategory(u"Application", u"Application"))
                propItems[sectionName].update({u"Application": item})
                propGrid.SetPropertyHelpString(
                    item,
                    "General preferences related to the PsychoPy GUI suite "
                    "(Coder, Builder, etc.)")
            elif sectionName == 'builder':
                propItems[sectionName].update(
                    {u"Builder":
                        propGrid.Append(
                            pg.PropertyCategory(u"Builder", u"Builder"))})
            elif sectionName == 'coder':
                propItems[sectionName].update(
                    {u"Coder":
                        propGrid.Append(
                            pg.PropertyCategory(u"Coder", u"Coder"))})
            elif sectionName == 'keyBindings':
                propItems[sectionName].update(
                    {u"Key Bindings":
                        propGrid.Append(
                            pg.PropertyCategory(
                                u"Key Bindings", u"Key Bindings"))})
            elif sectionName == 'hardware':
                propItems[sectionName].update(
                    {u"Hardware":
                        propGrid.Append(
                            pg.PropertyCategory(
                                u"Hardware", u"Hardware"))})
            elif sectionName == 'connections':
                propItems[sectionName].update(
                    {u"Connections":
                        propGrid.Append(
                            pg.PropertyCategory(
                                u"Connections", u"Connections"))})

            for prefName in specSection:
                if prefName in ['version']:  # any other prefs not to show?
                    continue
                # allowModuleImports pref is handled by generateSpec.py
                # NB if something is in prefs but not in spec then it won't be
                # shown (removes outdated prefs)
                thisPref = prefsSection[prefName]
                thisSpec = specSection[prefName]
                ctrlName = sectionName + '.' + prefName

                # for keybindings replace Ctrl with Cmd on Mac
                if platform.system() == 'Darwin' and sectionName == 'keyBindings':
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
                    item = propGrid.Append(
                        wx.propgrid.EditEnumProperty(
                            pLabel, prefName, fontList, value=str(thisPref)))
                # handle fields for font sizes
                elif prefName in ('codeFontSize', 'commentFontSize'):
                    item = propGrid.Append(wx.propgrid.IntProperty(
                            prefName, value=int(thisPref)))
                # audio latency mode for the PTB driver
                elif prefName == 'audioLatencyMode':
                    # get the labels from above
                    labels = []
                    for val, labl in audioLatencyLabels.items():
                        labels.append(u'{}: {}'.format(val, labl))
                    #get the options from the config file spec
                    vals = thisSpec.replace("option(", "").replace("'", "")
                    # item -1 is 'default=x' from spec
                    vals = vals.replace(", ", ",").split(',')
                    options = vals[:-1]
                    try:
                        default = options.index(
                            vals[-1].strip('()').split('=')[1])
                    except (IndexError, ValueError):
                        default = 0  # use first if default not in list
                    item = propGrid.Append(
                        wx.propgrid.EnumProperty(
                            pLabel,
                            prefName,
                            labels=labels,
                            values=[i for i in range(len(labels))],
                            value=default))
                # option items are given a dropdown, current value is shown
                # in the box
                elif thisSpec.startswith('option') or thisPref == 'audioDevice':
                    if thisPref == 'audioDevice':
                        devnames = sorted(sound.getDevices('output'))
                        if type(thisPref) == list:
                            thisPref = thisPref[0]
                        if thisPref in devnames:
                            options = [thisPref]
                        else:
                            options = []
                        try:
                            # TODO: this assumes that the driver loaded is current selected
                            # we *could* fix that but hopefully PTB will soon dominate and
                            # then we don't need to worry!
                            for device in devnames:
                                # newline characters must be removed
                                thisDevName = device.replace('\r\n', '')
                                if thisDevName not in options:
                                    options.append(thisDevName)
                        except (ValueError, OSError, ImportError):
                            pass
                        default = 0
                    else:
                        vals = thisSpec.replace("option(", "").replace("'", "")
                        # item -1 is 'default=x' from spec
                        vals = vals.replace(", ", ",").split(',')
                        options = vals[:-1]
                        try:
                            default = options.index(
                                vals[-1].strip('()').split('=')[1])
                        except (IndexError, ValueError):
                            default = 0  # use first if default not in list

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
                        wx.propgrid.ArrayStringProperty(
                            prefName, value=[str(i) for i in thisPref]))
                # integer items
                elif thisSpec.startswith('int'):  # integer
                    item = propGrid.Append(
                        wx.propgrid.IntProperty(
                            prefName, value=int(thisPref)))
                # all other items just use a string field
                else:
                    item = propGrid.Append(
                        wx.propgrid.StringProperty(
                            prefName, value=str(thisPref)))

                if item is not None:
                    propGrid.SetPropertyHelpString(item, helpText)

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


    # Virtual event handlers, overide them in your derived class
    def OnApplyClicked(self, event):
        event.Skip()

    def OnCancelClicked(self, event):
        event.Skip()

    def OnHelpClicked(self, event):
        event.Skip()

    def OnOKClicked(self, event):
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
