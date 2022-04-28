#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import sys
import re
import glob
import time
import zipfile
import platform
import os
from pkg_resources import parse_version
import wx
import wx.lib.filebrowsebutton
try:
    import wx.lib.agw.hyperlink as wxhl  # 4.0+
except ImportError:
    import wx.lib.hyperlink as wxhl # <3.0.2

import psychopy
from .. import dialogs
from psychopy.localization import _translate
from psychopy import logging
from psychopy import web
import io
urllib = web.urllib

versionURL = "https://www.psychopy.org/version.txt"

"""The Updater class checks for updates and suggests that an update is carried
out if a new version is found. The actual updating is handled by
InstallUpdateDialog (via Updater.doUpdate() ).
"""


def getLatestVersionInfo(app=None):
    """
    Fetch info about the latest available version.
    Returns -1 if fails to make a connection
    """
    try:
        page = urllib.request.urlopen(versionURL)
    except urllib.error.URLError:
        return -1
    # parse update file as a dictionary
    latest = {}
    for line in page.readlines():
        # in some odd circumstances (wifi hotspots) you can fetch a
        # page that is not the correct URL but a redirect
        line = line.decode()  # convert from a byte to a str
        if line.find(':') == -1:
            return -1
            # this will succeed if every line has a key
        key, keyInfo = line.split(':')
        latest[key] = keyInfo.replace('\n', '').replace('\r', '')
    if app:
        app._latestAvailableVersion = latest
    return latest


class Updater():

    def __init__(self, app=None, runningVersion=None):
        """The updater will check for updates and download/install as needed.
        Several dialogs may be created as needed during the process.

        Usage::

            if app.prefs['AutoUpdate']:
                app.updates = Updater(app)
                app.updater.checkForUpdates()
                # if updates are found further dialogs will prompt
        """
        super(Updater, self).__init__()
        self.app = app
        if runningVersion is None:
            self.runningVersion = psychopy.__version__
        else:
            self.runningVersion = runningVersion

        # self.headers = {'User-Agent': psychopy.constants.PSYCHOPY_USERAGENT}
        self.latest = getLatestVersionInfo()
        if web.proxies is None:
            web.setupProxy()

    def getLatestInfo(self, warnMsg=False):
        # open page
        latest = getLatestVersionInfo()
        if latest == -1:
            m1 = _translate("Couldn't connect to psychopy.org to check for "
                            "updates. \n")
            m2 = _translate("Check internet settings (and proxy setting in "
                            "PsychoPy Preferences).")
            confirmDlg = dialogs.MessageDialog(
                parent=None, message=m1 + m2, type='Info',
                title=_translate('PsychoPy updates'))
            confirmDlg.ShowModal()
        return latest

    def suggestUpdate(self, confirmationDlg=False):
        """Query user about whether to update (if it's possible to update)
        """
        if self.latest is None:  # we haven't checked for updates yet
            self.latest = self.getLatestInfo()

        if self.latest == -1:
            return -1  # failed to find out about updates
        # have found 'latest'. Is it newer than running version?
        try:
            newer = self.latest['version'] > self.runningVersion
        except KeyError as err:
            print(self.latest)
            raise(err)
        skip = self.app.prefs.appData['skipVersion'] == self.latest['version']
        if newer and not skip:
            if (parse_version(self.latest['lastUpdatable'])
                    <= parse_version(self.runningVersion)):
                # go to the updating window
                confirmDlg = SuggestUpdateDialog(
                    self.latest, self.runningVersion)
                resp = confirmDlg.ShowModal()
                confirmDlg.Destroy()
                # what did the user ask us to do?
                if resp == wx.ID_CANCEL:
                    return 0  # do nothing
                if resp == wx.ID_NO:
                    self.app.prefs.appData[
                        'skipVersion'] = self.latest['version']
                    self.app.prefs.saveAppData()
                    return 0  # do nothing
                if resp == wx.ID_YES:
                    self.doUpdate()
            else:
                # the latest version needs a full install, not autoupdate
                msg = _translate("PsychoPy v%(latest)s is available (you are"
                                 " running %(running)s).\n\n")
                msg = msg % {'latest': self.latest['version'],
                             'running': self.runningVersion}
                msg += _translate("This version is too big an update to be "
                                  "handled automatically.\n")
                msg += _translate("Please fetch the latest version from "
                                  "www.psychopy.org and install manually.")
                confirmDlg = dialogs.MessageDialog(
                    parent=None, message=msg, type='Warning',
                    title=_translate('PsychoPy updates'))
                confirmDlg.cancelBtn.SetLabel(_translate('Go to downloads'))
                confirmDlg.cancelBtn.SetDefault()
                confirmDlg.noBtn.SetLabel(_translate('Go to changelog'))
                confirmDlg.yesBtn.SetLabel(_translate('Later'))
                resp = confirmDlg.ShowModal()
                confirmDlg.Destroy()
                if resp == wx.ID_CANCEL:
                    self.app.followLink(url=self.app.urls['downloads'])
                if resp == wx.ID_NO:
                    self.app.followLink(url=self.app.urls['changelog'])
        elif not confirmationDlg:  # do nothing
            return 0
        else:
            txt = _translate(
                "You are running the latest version of PsychoPy (%s). ")
            msg = txt % self.runningVersion
            confirmDlg = dialogs.MessageDialog(
                parent=None, message=msg, type='Info',
                title=_translate('PsychoPy updates'))
            confirmDlg.ShowModal()
            return -1

    def doUpdate(self):
        """Should be called from suggestUpdate
        (separate dialog to ask user whether they want to)
        """
        # app contains a reciprocal pointer to this Updater object
        dlg = InstallUpdateDialog(None, -1, app=self.app)


class SuggestUpdateDialog(wx.Dialog):
    """A dialog explaining that a new version is available
    with a link to the changelog
    """

    def __init__(self, latest, runningVersion):
        wx.Dialog.__init__(self, None, -1, title='PsychoPy3 Updates')
        sizer = wx.BoxSizer(wx.VERTICAL)

        # info about current version
        txt = _translate("PsychoPy v%(latest)s is available (you are running "
                         "%(running)s).\n\n"
                         "(To disable this check, see Preferences > "
                         "connections > checkForUpdates)")
        label = txt % {'latest': latest['version'], 'running': runningVersion}
        msg1 = wx.StaticText(self, -1, style=wx.ALIGN_CENTRE, label=label)
        if latest['lastCompatible'] > runningVersion:
            label = _translate("This version MAY require you to modify your\n"
                               "scripts/exps slightly. Read the changelog "
                               "carefully.")
            msg2 = wx.StaticText(self, -1, style=wx.ALIGN_CENTRE, label=label)
            msg2.SetForegroundColour([200, 0, 0])
        else:
            label = _translate("There are no known compatibility\nissues "
                               "with your current version.")
            msg2 = wx.StaticText(self, -1, style=wx.ALIGN_CENTRE, label=label)
        changelog = wxhl.HyperLinkCtrl(self, wx.ID_ANY,
                                       _translate("View complete Changelog"),
                                       URL="https://www.psychopy.org/changelog.html")

        if sys.platform.startswith('linux'):
            msg = _translate("You can update PsychoPy with your package "
                             "manager")
            msg3 = wx.StaticText(self, -1, msg)
        else:
            msg = _translate("Should PsychoPy update itself?")
            msg3 = wx.StaticText(self, -1, msg)

        sizer.Add(msg1, flag=wx.ALL | wx.CENTER, border=15)
        sizer.Add(msg2, flag=wx.RIGHT | wx.LEFT | wx.CENTER, border=15)
        sizer.Add(changelog, flag=wx.RIGHT | wx.LEFT | wx.CENTER, border=5)
        sizer.Add(msg3, flag=wx.ALL | wx.CENTER, border=15)

        # add buttons
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)

        # for linux there should be no 'update' option
        if sys.platform.startswith('linux'):
            self.cancelBtn = wx.Button(
                self, wx.ID_CANCEL, _translate('Keep warning me'))
            self.cancelBtn.SetDefault()
            self.noBtn = wx.Button(
                self, wx.ID_NO, _translate('Stop warning me'))
        else:
            self.yesBtn = wx.Button(self, wx.ID_YES, _translate('Yes'))
            self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_YES)
            self.cancelBtn = wx.Button(
                self, wx.ID_CANCEL, _translate('Not now'))
            self.noBtn = wx.Button(
                self, wx.ID_NO, _translate('Skip this version'))
        self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_CANCEL)
        self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_NO)
        btnSizer.Add(self.noBtn, wx.ALIGN_LEFT)
        btnSizer.Add((60, 20), 0, wx.EXPAND)
        btnSizer.Add(self.cancelBtn)

        if not sys.platform.startswith('linux'):
            self.yesBtn.SetDefault()
            btnSizer.Add((5, 20), 0)
            btnSizer.Add(self.yesBtn)

        # configure sizers and fit
        sizer.Add(btnSizer, flag= wx.ALL, border=5)
        self.Center()
        self.SetSizerAndFit(sizer)

    def onButton(self, event):
        self.EndModal(event.GetId())


class InstallUpdateDialog(wx.Dialog):

    def __init__(self, parent, ID, app):
        """Latest is optional extra. If not given it will be fetched.
        """
        self.app = app
        # get latest version info if poss
        if app.updater in [False, None]:
            # user has turned off check for updates in prefs so check now
            app.updater = updater = Updater(app=self.app)
            # don't need a warning - we'll provide one ourselves
            self.latest = updater.getLatestInfo(warnMsg=False)
        else:
            self.latest = app.updater.latest
        self.runningVersion = app.updater.runningVersion
        wx.Dialog.__init__(self, parent, ID,
                           title=_translate('PsychoPy Updates'))

        borderSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(borderSizer)
        borderSizer.Add(mainSizer, border=12, proportion=1, flag=wx.ALL | wx.EXPAND)
        # set the actual content of status msg later in self.updateStatus()
        self.statusMessage = wx.StaticText(
            self, -1, "msg", style=wx.ALIGN_CENTER)
        mainSizer.Add(self.statusMessage, flag=wx.EXPAND | wx.ALL, border=5)
        # ctrls for auto-update from web
        msg = _translate(" Auto-update (will fetch latest version)")
        self.useLatestBtn = wx.RadioButton(self, -1, msg,
                                           style=wx.RB_GROUP)
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioSelect, self.useLatestBtn)
        self.progressBar = wx.Gauge(self, -1, 100, size=(250, 36))
        mainSizer.Add(self.useLatestBtn,
                      flag=wx.ALIGN_LEFT | wx.ALL, border=5)
        mainSizer.Add(self.progressBar, flag=wx.EXPAND | wx.ALL, border=5)
        # ctrls for updating from specific zip file
        msg = _translate(" Use zip file below (download a PsychoPy release "
                         "file ending .zip)")
        self.useZipBtn = wx.RadioButton(self, -1, msg)
        self.Bind(wx.EVT_RADIOBUTTON, self.onRadioSelect, self.useZipBtn)
        self.fileBrowseCtrl = wx.lib.filebrowsebutton.FileBrowseButton(
            self, -1, size=(450, 48), changeCallback=self.onFileBrowse,
            fileMask='*.zip')
        mainSizer.Add(self.useZipBtn, flag=wx.ALIGN_LEFT | wx.ALL, border=5)
        mainSizer.Add(self.fileBrowseCtrl, flag=wx.ALIGN_LEFT | wx.ALL, border=5)
        # ctrls for buttons (install/cancel)
        self.installBtn = wx.Button(self, -1, _translate('Install'))
        self.Bind(wx.EVT_BUTTON, self.onInstall, self.installBtn)
        self.installBtn.SetDefault()
        self.cancelBtn = wx.Button(self, -1, _translate('Close'))
        self.Bind(wx.EVT_BUTTON, self.onCancel, self.cancelBtn)
        btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        btnSizer.AddStretchSpacer()
        if sys.platform == "win32":
            btns = [self.installBtn, self.cancelBtn]
        else:
            btns = [self.cancelBtn, self.installBtn]
        btnSizer.Add(btns[0], 0, flag=wx.LEFT, border=5)
        btnSizer.Add(btns[1], 0, flag=wx.LEFT, border=5)
        mainSizer.AddStretchSpacer()
        mainSizer.Add(btnSizer, flag=wx.ALL | wx.EXPAND, border=5)

        self.Layout()
        self.Fit()

        # positioning and sizing
        self.updateStatus()
        self.Center()
        self.ShowModal()

    def updateStatus(self):
        """Check the current version and most recent version and update ctrls
        """
        if self.latest == -1:
            # Set message and display, and return early if version could not be found
            msg = _translate(
                "You are running PsychoPy v%s.\n ") % self.runningVersion
            msg += _translate("PsychoPy could not connect to the \n internet"
                              " to check for more recent versions.\n")
            msg += _translate("Check proxy settings in preferences.")
            self.statusMessage.SetLabel(msg)
            return
        elif (parse_version(self.latest['version'])
                  < parse_version(self.runningVersion)):
            msg = _translate(
                "You are running PsychoPy (%(running)s), which is ahead of "
                "the latest official version (%(latest)s)") % {
                'running':self.runningVersion, 'latest':self.latest['version']}
        elif self.latest['version'] == self.runningVersion:
            msg = _translate(
                "You are running the latest version of PsychoPy (%s)\n ") % self.runningVersion
            msg += _translate("You can revert to a previous version by "
                              "selecting a specific .zip source installation file")
        else:
            txt = _translate(
                "PsychoPy v%(latest)s is available\nYou are running v%(running)s")
            msg = txt % {'latest': self.latest['version'],
                         'running': self.runningVersion}
            if (parse_version(self.latest['lastUpdatable'])
                                  <= parse_version(self.runningVersion)):
                msg += _translate("\nYou can update to the latest version automatically")
            else:
                msg += _translate("\nYou cannot update to the latest version "
                                  "automatically.\nPlease fetch the latest "
                                  "Standalone package from www.psychopy.org")
        self.statusMessage.SetLabel(msg)
        areRunningLatest = self.latest['version'] == self.runningVersion
        notUpdateable = self.latest['lastUpdatable'] > self.runningVersion
        if self.latest == -1 or areRunningLatest or notUpdateable:
            # can't auto-update
            self.currentSelection = self.useZipBtn
            self.useZipBtn.SetValue(True)
            self.useLatestBtn.Disable()
        else:
            self.currentSelection = self.useLatestBtn
            self.useLatestBtn.SetValue(True)
        self.Layout()
        self.Fit()
        # this will enable/disable additional controls for the above:
        self.onRadioSelect()

    def onRadioSelect(self, event=None):
        """Set the controls of the appropriate selection to disabled/enabled
        """
        # if receive no event then just set everything to previous state
        if event != None:
            self.currentSelection = event.GetEventObject()
        else:
            pass
        if self.currentSelection == self.useLatestBtn:
            self.fileBrowseCtrl.Disable()
            self.progressBar.Enable()
        elif self.currentSelection == self.useZipBtn:
            self.fileBrowseCtrl.Enable()
            self.progressBar.Disable()
            # if this has been disabled by the fact that we couldn't connect
            self.installBtn.Enable()

    def onCancel(self, event):
        self.app.updater = None
        self.Close()

    def onFileBrowse(self, event):
        self.filename = event.GetString()

    def onInstall(self, event):
        if self.currentSelection == self.useLatestBtn:
            info = self.doAutoInstall()
        else:
            info = self.installZipFile(self.filename)
        self.statusMessage.SetLabel(str(info))
        self.Fit()

    def fetchPsychoPy(self, v='latest'):
        msg = _translate("Attempting to fetch PsychoPy %s...")
        self.statusMessage.SetLabel(msg % self.latest['version'])
        info = ""
        if v == 'latest':
            v = self.latest['version']

        # open page
        URL = "http://github.com/psychopy/psychopy/releases/download/%s/PsychoPy-%s.zip"
        page = urllib.request.urlopen(URL % v)
        # download in chunks so that we can monitor progress and abort mid-way
        chunk = 4096
        read = 0
        fileSize = int(page.info()['Content-Length'])
        buffer = io.StringIO()
        self.progressBar.SetRange(fileSize)
        while read < fileSize:
            ch = page.read(chunk)
            buffer.write(ch)
            read += chunk
            self.progressBar.SetValue(read)
            txt = _translate(
                "Fetched %(done)i of %(total)i kb of PsychoPy-%(version)s.zip")
            msg = txt % {'done': read // 1000,
                         'total': fileSize // 1000, 'version': v}
            self.statusMessage.SetLabel(msg)
            self.Update()
        info += _translate('Successfully downloaded PsychoPy-%s.zip') % v
        page.close()
        zfile = zipfile.ZipFile(buffer)
        # buffer.close()
        return zfile, info

    def installZipFile(self, zfile, v=None):
        """If v is provided this will be used as new version number;
        otherwise try and retrieve a version number from zip file name
        """
        info = ""  # return this at the end
        zfileIsName = type(zfile) == str
        if os.path.isfile(zfile) and zfileIsName:
            # zfile is filename not an actual file
            if v is None:  # try and deduce it
                zFilename = os.path.split(zfile)[-1]
                searchName = re.search(r'[0-9]*\.[0-9]*\.[0-9]*.', zFilename)
                if searchName != None:
                    v = searchName.group(0)[:-1]
                else:
                    msg = "Couldn't deduce version from zip file: %s"
                    logging.warning(msg % zFilename)
            f = open(zfile, 'rb')
            zfile = zipfile.ZipFile(f)
        else:  # assume here that zfile is a ZipFile
            pass  # todo: error checking - is it a zipfile?

        currPath = self.app.prefs.paths['psychopy']
        currVer = psychopy.__version__
        # any commands that are successfully executed may need to be undone if
        # a later one fails
        undoStr = ""
        # depending on install method, needs diff handling
        # if path ends with 'psychopy' then move it to 'psychopy-version' and
        # create a new 'psychopy' folder for new version
        # does the path contain any version number?
        versionLabelsInPath = re.findall('PsychoPy-.*/', currPath)
        # e.g. the mac standalone app, no need to refer to new version number
        onWin32 = bool(sys.platform == 'win32' and
                       int(sys.getwindowsversion()[1]) > 5)
        if len(versionLabelsInPath) == 0:
            unzipTarget = currPath
            try:  # to move existing PsychoPy
                os.rename(currPath, "%s-%s" % (currPath, currVer))
                undoStr += 'os.rename("%s-%s" %(currPath, currVer),currPath)\n'
            except Exception:
                if onWin32:
                    msg = _translate("To upgrade you need to restart the app"
                                     " as admin (Right-click the app and "
                                     "'Run as admin')")
                else:
                    msg = _translate("Could not move existing PsychoPy "
                                     "installation (permissions error?)")
                return msg
        else:  # setuptools-style installation
            # generate new target path
            unzipTarget = currPath
            for thisVersionLabel in versionLabelsInPath:
                # remove final slash from the re.findall
                pathVersion = thisVersionLabel[:-1]
                unzipTarget = unzipTarget.replace(pathVersion,
                                                  "PsychoPy-%s" % v)
                # find the .pth file that specifies the python dir
                # create the new installation directory BEFORE changing pth
                # file
                nUpdates, newInfo = self.updatePthFile(pathVersion,
                                                       "PsychoPy-%s" % v)
                if nUpdates == -1:  # there was an error (likely permissions)
                    undoStr += 'self.updatePthFile(unzipTarget, currPath)\n'
                    exec(undoStr)  # undo previous changes
                    return newInfo

        try:
            # create the new installation dir AFTER renaming existing dir
            os.makedirs(unzipTarget)
            undoStr += 'os.remove(%s)\n' % unzipTarget
        except Exception:  # revert path rename and inform user
            exec(undoStr)  # undo previous changes
            if onWin32:
                msg = _translate(
                    "Right-click the app and 'Run as admin'):\n%s")
            else:
                msg = _translate("Failed to create directory for new version"
                                 " (permissions error?):\n%s")
            return msg % unzipTarget

        # do the actual extraction
        for name in zfile.namelist():  # for each file within the zip
            # check that this file is part of psychopy (not metadata or docs)
            if name.count('/psychopy/') < 1:
                continue
            try:
                targetFile = os.path.join(unzipTarget,
                                          name.split('/psychopy/')[1])
                targetContainer = os.path.split(targetFile)[0]
                if not os.path.isdir(targetContainer):
                    os.makedirs(targetContainer)  # make the containing folder
                if targetFile.endswith('/'):
                    os.makedirs(targetFile)  # it's a folder
                else:
                    outfile = open(targetFile, 'wb')
                    outfile.write(zfile.read(name))
                    outfile.close()
            except Exception:
                exec(undoStr)  # undo previous changes
                logging.error('failed to unzip file: ' + name)
                logging.error(sys.exc_info()[0])
        info += _translate('Success. \nChanges to PsychoPy will be completed'
                           ' when the application is next run')
        self.cancelBtn.SetDefault()
        self.installBtn.Disable()
        return info

    def doAutoInstall(self, v='latest'):
        if v == 'latest':
            v = self.latest['version']
        msg = _translate("Downloading PsychoPy v%s") % v
        self.statusMessage.SetLabel(msg)
        try:
            zipFile, info = self.fetchPsychoPy(v)
        except Exception:
            msg = _translate('Failed to fetch PsychoPy release.\n'
                             'Check proxy setting in preferences')
            self.statusMessage.SetLabel(msg)
            return -1
        self.statusMessage.SetLabel(info)
        self.Fit()
        # got a download - try to install it
        info = self.installZipFile(zipFile, v)
        return info

    def updatePthFile(self, oldName, newName):
        """Searches site-packages for .pth files and replaces any instance of
        `oldName` with `newName`, expect names like PsychoPy-1.60.04
        """
        from distutils.sysconfig import get_python_lib
        siteDir = get_python_lib()
        pthFiles = glob.glob(os.path.join(siteDir, '*.pth'))
        # sometimes the site-packages dir isn't where the pth files are kept?
        enclosingSiteDir = os.path.split(siteDir)[0]
        pthFiles.extend(glob.glob(os.path.join(enclosingSiteDir, '*.pth')))
        nUpdates = 0  # no paths updated
        info = ""
        for filename in pthFiles:
            lines = open(filename, 'r').readlines()
            needSave = False
            for lineN, line in enumerate(lines):
                if oldName in line:
                    lines[lineN] = line.replace(oldName, newName)
                    needSave = True
            if needSave:
                try:
                    f = open(filename, 'w')
                    f.writelines(lines)
                    f.close()
                    nUpdates += 1
                    logging.info('Updated PsychoPy path in %s' % filename)
                except Exception:
                    info += 'Failed to update PsychoPy path in %s' % filename
                    return -1, info
        return nUpdates, info


def sendUsageStats():
    """Sends anonymous, very basic usage stats to psychopy server:
      the version of PsychoPy
      the system used (platform and version)
      the date
    """

    v = psychopy.__version__
    dateNow = time.strftime("%Y-%m-%d_%H:%M")
    miscInfo = ''

    # urllib.install_opener(opener)
    # check for proxies
    if web.proxies is None:
        web.setupProxy()

    # get platform-specific info
    if sys.platform == 'darwin':
        OSXver, junk, architecture = platform.mac_ver()
        systemInfo = "OSX_%s_%s" % (OSXver, architecture)
    elif sys.platform.startswith('linux'):
        from distro import linux_distribution
        systemInfo = '%s_%s_%s' % (
            'Linux',
            ':'.join([x for x in linux_distribution() if x != '']),
            platform.release())
        if len(systemInfo) > 30:  # if it's too long PHP/SQL fails to store!?
            systemInfo = systemInfo[0:30]
    elif sys.platform == 'win32':
        systemInfo = "win32_v" + platform.version()
    else:
        systemInfo = platform.system() + platform.release()
    u = "https://www.psychopy.org/usage.php?date=%s&sys=%s&version=%s&misc=%s"
    URL = u % (dateNow, systemInfo, v, miscInfo)
    try:
        req = urllib.request.Request(URL)
        page = urllib.request.urlopen(req)  # proxies
    except Exception:
        logging.warning("Couldn't connect to psychopy.org\n"
                        "Check internet settings (and proxy "
                        "setting in PsychoPy Preferences.")
