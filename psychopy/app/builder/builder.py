#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Defines the behavior of Psychopy's Builder view window
Part of the PsychoPy library
Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
Distributed under the terms of the GNU General Public License (GPL).
"""

from __future__ import absolute_import, division, print_function

import os, sys
import glob
import copy
import traceback
import codecs
import numpy

from pkg_resources import parse_version
import wx.stc
from wx.lib import scrolledpanel
from wx.lib import platebtn

import wx.lib.agw.aui as aui  # some versions of phoenix
try:
    from wx.adv import PseudoDC
except ImportError:
    from wx import PseudoDC

if parse_version(wx.__version__) < parse_version('4.0.3'):
    wx.NewIdRef = wx.NewId

try:
    from queue import Queue, Empty
except ImportError:
    from Queue import Queue, Empty  # python 2.x

from psychopy.localization import _translate
from ... import experiment, prefs
from .. import dialogs, icons
from ..themes import IconCache, ThemeMixin
from ..themes._themes import PsychopyDockArt, PsychopyTabArt, ThemeSwitcher
from psychopy import logging, constants, data
from psychopy.tools.filetools import mergeFolder
from .dialogs import (DlgComponentProperties, DlgExperimentProperties,
                      DlgCodeComponentProperties, DlgLoopProperties)
from ..utils import (PsychopyToolbar, PsychopyPlateBtn, WindowFrozen,
                     FileDropTarget, FrameSwitcher)

from psychopy.experiment import components
from builtins import str
from psychopy.app import pavlovia_ui
from psychopy.projects import pavlovia

from psychopy.scripts.psyexpCompile import generateScript

# _localized separates internal (functional) from displayed strings
# long form here allows poedit string discovery
_localized = {
    'Field': _translate('Field'),
    'Default': _translate('Default'),
    'Favorites': _translate('Favorites'),
    'Stimuli': _translate('Stimuli'),
    'Responses': _translate('Responses'),
    'Custom': _translate('Custom'),
    'I/O': _translate('I/O'),
    'Add to favorites': _translate('Add to favorites'),
    'Remove from favorites': _translate('Remove from favorites'),
    # contextMenuLabels
    'edit': _translate('edit'),
    'remove': _translate('remove'),
    'copy': _translate('copy'),
    'move to top': _translate('move to top'),
    'move up': _translate('move up'),
    'move down': _translate('move down'),
    'move to bottom': _translate('move to bottom')
}

cs = ThemeMixin.appColors

class BuilderFrame(wx.Frame, ThemeMixin):
    """Defines construction of the Psychopy Builder Frame"""

    def __init__(self, parent, id=-1, title='PsychoPy (Experiment Builder)',
                 pos=wx.DefaultPosition, fileName=None, frameData=None,
                 style=wx.DEFAULT_FRAME_STYLE, app=None):

        if (fileName is not None) and (type(fileName) == bytes):
            fileName = fileName.decode(sys.getfilesystemencoding())

        self.app = app
        self.dpi = self.app.dpi
        # things the user doesn't set like winsize etc:
        self.appData = self.app.prefs.appData['builder']
        # things about the builder that the user can set:
        self.prefs = self.app.prefs.builder
        self.appPrefs = self.app.prefs.app
        self.paths = self.app.prefs.paths
        self.frameType = 'builder'
        self.filename = fileName
        self.htmlPath = None
        self.project = None  # type: pavlovia.PavloviaProject
        self.btnHandles = {}  # stores toolbar buttons so they can be altered
        self.scriptProcess = None
        self.stdoutBuffer = None
        self.generateScript = generateScript

        if fileName in self.appData['frames']:
            self.frameData = self.appData['frames'][fileName]
        else:  # work out a new frame size/location
            dispW, dispH = self.app.getPrimaryDisplaySize()
            default = self.appData['defaultFrame']
            default['winW'] = int(dispW * 0.75)
            default['winH'] = int(dispH * 0.75)
            if default['winX'] + default['winW'] > dispW:
                default['winX'] = 5
            if default['winY'] + default['winH'] > dispH:
                default['winY'] = 5
            self.frameData = dict(self.appData['defaultFrame'])  # copy
            # increment default for next frame
            default['winX'] += 10
            default['winY'] += 10

        # we didn't have the key or the win was minimized / invalid
        if self.frameData['winH'] == 0 or self.frameData['winW'] == 0:
            self.frameData['winX'], self.frameData['winY'] = (0, 0)
        if self.frameData['winY'] < 20:
            self.frameData['winY'] = 20
        wx.Frame.__init__(self, parent=parent, id=id, title=title,
                          pos=(int(self.frameData['winX']), int(
                              self.frameData['winY'])),
                          size=(int(self.frameData['winW']), int(
                              self.frameData['winH'])),
                          style=style)
        self.Bind(wx.EVT_CLOSE, self.closeFrame)
        #self.panel = wx.Panel(self)

        # detect retina displays (then don't use double-buffering)
        self.isRetina = self.GetContentScaleFactor() != 1
        self.SetDoubleBuffered(not self.isRetina)

        # create icon
        if sys.platform != 'darwin':
            # doesn't work on darwin and not necessary: handled by app bundle
            iconFile = os.path.join(self.paths['resources'], 'builder.ico')
            if os.path.isfile(iconFile):
                self.SetIcon(wx.Icon(iconFile, wx.BITMAP_TYPE_ICO))

        # create our panels
        self.flowPanel = FlowPanel(frame=self)
        self.routinePanel = RoutinesNotebook(self)
        self.componentButtons = ComponentsPanel(self)
        # menus and toolbars
        self.toolbar = PsychopyToolbar(frame=self)
        self.SetToolBar(self.toolbar)
        self.makeMenus()
        self.CreateStatusBar()
        self.SetStatusText("")

        # setup universal shortcuts
        accelTable = self.app.makeAccelTable()
        self.SetAcceleratorTable(accelTable)

        # setup a default exp
        if fileName is not None and os.path.isfile(fileName):
            self.fileOpen(filename=fileName, closeCurrent=False)
        else:
            self.lastSavedCopy = None
            # don't try to close before opening
            self.fileNew(closeCurrent=False)
        self.updateReadme()

        # control the panes using aui manager
        self._mgr = aui.AuiManager(self)
        #self._mgr.SetArtProvider(PsychopyDockArt())
        #self._art = self._mgr.GetArtProvider()
        # Create panels
        self._mgr.AddPane(self.routinePanel,
                          aui.AuiPaneInfo().
                          Name("Routines").Caption("Routines").CaptionVisible(True).
                          CloseButton(False).MaximizeButton(True).PaneBorder(False).
                          Center())  # 'center panes' expand
        rtPane = self._mgr.GetPane('Routines')
        self._mgr.AddPane(self.componentButtons,
                          aui.AuiPaneInfo().
                          Name("Components").Caption("Components").CaptionVisible(True).
                          RightDockable(True).LeftDockable(True).
                          CloseButton(False).PaneBorder(False).
                          Right())
        compPane = self._mgr.GetPane('Components')
        self._mgr.AddPane(self.flowPanel,
                          aui.AuiPaneInfo().
                          Name("Flow").Caption("Flow").CaptionVisible(True).
                          BestSize((8 * self.dpi, 2 * self.dpi)).
                          RightDockable(True).LeftDockable(True).
                          CloseButton(False).PaneBorder(False).
                          Bottom())
        flowPane = self._mgr.GetPane('Flow')
        # Arrange panes
        if self.prefs['topFlow']:
            flowPane.Top()
            compPane.Left()
            rtPane.CenterPane()
        rtPane.CaptionVisible(True)
        # tell the manager to 'commit' all the changes just made
        self._mgr.Update()
        # self.SetSizer(self.mainSizer)  # not necessary for aui type controls
        if self.frameData['auiPerspective']:
            self._mgr.LoadPerspective(self.frameData['auiPerspective'])
        self.SetMinSize(wx.Size(600, 400))  # min size for the whole window
        self.SetSize(
            (int(self.frameData['winW']), int(self.frameData['winH'])))
        self.SendSizeEvent()
        self._mgr.Update()

        # self.SetAutoLayout(True)
        self.Bind(wx.EVT_CLOSE, self.closeFrame)

        self.app.trackFrame(self)
        self.SetDropTarget(FileDropTarget(targetFrame=self))
        self._applyAppTheme()

    # def _applyAppTheme(self, target=None):
    #     # self.SetArtProvider(PsychopyDockArt())
    #     for c in self.GetChildren():
    #         if hasattr(c, '_applyAppTheme'):
    #             c._applyAppTheme()
    #     self.Refresh()
    #     self.Update()

    # Synonymise Aui manager for use with theme mixin
    def GetAuiManager(self):
        return self._mgr

    def makeMenus(self):
        """
        Produces Menus for the Builder Frame
        """

        # ---Menus---#000000#FFFFFF-------------------------------------------
        menuBar = wx.MenuBar()
        # ---_file---#000000#FFFFFF-------------------------------------------
        self.fileMenu = wx.Menu()
        menuBar.Append(self.fileMenu, _translate('&File'))

        # create a file history submenu
        self.fileHistoryMaxFiles = 10
        self.fileHistory = wx.FileHistory(maxFiles=self.fileHistoryMaxFiles)
        self.recentFilesMenu = wx.Menu()
        self.fileHistory.UseMenu(self.recentFilesMenu)
        for filename in self.appData['fileHistory']:
            if os.path.exists(filename):
                self.fileHistory.AddFileToHistory(filename)
        self.Bind(wx.EVT_MENU_RANGE, self.OnFileHistory,
                  id=wx.ID_FILE1, id2=wx.ID_FILE9)
        keys = self.app.keys
        menu = self.fileMenu
        menu.Append(
            wx.ID_NEW,
            _translate("&New\t%s") % keys['new'])
        menu.Append(
            wx.ID_OPEN,
            _translate("&Open...\t%s") % keys['open'])
        menu.AppendSubMenu(
            self.recentFilesMenu,
            _translate("Open &Recent"))
        menu.Append(
            wx.ID_SAVE,
            _translate("&Save\t%s") % keys['save'],
            _translate("Save current experiment file"))
        menu.Append(
            wx.ID_SAVEAS,
            _translate("Save &as...\t%s") % keys['saveAs'],
            _translate("Save current experiment file as..."))
        exportMenu = menu.Append(
            -1,
            _translate("Export HTML...\t%s") % keys['exportHTML'],
            _translate("Export experiment to html/javascript file"))
        menu.Append(
            wx.ID_CLOSE,
            _translate("&Close file\t%s") % keys['close'],
            _translate("Close current experiment"))
        self.Bind(wx.EVT_MENU, self.app.newBuilderFrame, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.fileExport, id=exportMenu.GetId())
        self.Bind(wx.EVT_MENU, self.fileSave, id=wx.ID_SAVE)
        menu.Enable(wx.ID_SAVE, False)
        self.Bind(wx.EVT_MENU, self.fileSaveAs, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.fileOpen, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.commandCloseFrame, id=wx.ID_CLOSE)
        self.fileMenu.AppendSeparator()
        item = menu.Append(
            wx.ID_PREFERENCES,
            _translate("&Preferences\t%s") % keys['preferences'])
        self.Bind(wx.EVT_MENU, self.app.showPrefs, item)
        # item = menu.Append(wx.NewId(), "Plug&ins")
        # self.Bind(wx.EVT_MENU, self.pluginManager, item)
        menu.AppendSeparator()
        msg = _translate("Close PsychoPy Builder")
        item = menu.Append(wx.ID_ANY, msg)
        self.Bind(wx.EVT_MENU, self.closeFrame, id=item.GetId())
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(wx.ID_EXIT,
                             _translate("&Quit\t%s") % keys['quit'],
                             _translate("Terminate the program"))
        self.Bind(wx.EVT_MENU, self.quit, id=wx.ID_EXIT)

        # ------------- edit ------------------------------------
        self.editMenu = wx.Menu()
        menuBar.Append(self.editMenu, _translate('&Edit'))
        menu = self.editMenu
        self._undoLabel = menu.Append(wx.ID_UNDO,
                                      _translate("Undo\t%s") % keys['undo'],
                                      _translate("Undo last action"),
                                      wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.undo, id=wx.ID_UNDO)
        self._redoLabel = menu.Append(wx.ID_REDO,
                                      _translate("Redo\t%s") % keys['redo'],
                                      _translate("Redo last action"),
                                      wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.redo, id=wx.ID_REDO)
        menu.Append(wx.ID_PASTE, _translate("&Paste\t%s") % keys['paste'])
        self.Bind(wx.EVT_MENU, self.paste, id=wx.ID_PASTE)

        # ---_view---#000000#FFFFFF-------------------------------------------
        self.viewMenu = wx.Menu()
        menuBar.Append(self.viewMenu, _translate('&View'))
        menu = self.viewMenu

        item = menu.Append(wx.ID_ANY,
                           _translate("Open Coder view"),
                           _translate("Open a new Coder view"))
        self.Bind(wx.EVT_MENU, self.app.showCoder, item)

        item = menu.Append(wx.ID_ANY,
                           _translate("Open Runner view"),
                           _translate("Open the Runner view"))
        self.Bind(wx.EVT_MENU, self.app.showRunner, item)
        menu.AppendSeparator()

        item = menu.Append(wx.ID_ANY,
                           _translate("&Toggle readme\t%s") % self.app.keys[
                               'toggleReadme'],
                           _translate("Toggle Readme"))
        self.Bind(wx.EVT_MENU, self.toggleReadme, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("&Flow Larger\t%s") % self.app.keys[
                               'largerFlow'],
                           _translate("Larger flow items"))
        self.Bind(wx.EVT_MENU, self.flowPanel.increaseSize, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("&Flow Smaller\t%s") % self.app.keys[
                               'smallerFlow'],
                           _translate("Smaller flow items"))
        self.Bind(wx.EVT_MENU, self.flowPanel.decreaseSize, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("&Routine Larger\t%s") % keys[
                               'largerRoutine'],
                           _translate("Larger routine items"))
        self.Bind(wx.EVT_MENU, self.routinePanel.increaseSize, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("&Routine Smaller\t%s") % keys[
                               'smallerRoutine'],
                           _translate("Smaller routine items"))
        self.Bind(wx.EVT_MENU, self.routinePanel.decreaseSize, item)
        menu.AppendSeparator()
        # Add Theme Switcher
        self.themesMenu = ThemeSwitcher(self)
        menu.AppendSubMenu(self.themesMenu,
                               _translate("Themes"))

        # ---_tools ---#000000#FFFFFF-----------------------------------------
        self.toolsMenu = wx.Menu()
        menuBar.Append(self.toolsMenu, _translate('&Tools'))
        menu = self.toolsMenu
        item = menu.Append(wx.ID_ANY,
                           _translate("Monitor Center"),
                           _translate("To set information about your monitor"))
        self.Bind(wx.EVT_MENU, self.app.openMonitorCenter, item)

        item = menu.Append(wx.ID_ANY,
                           _translate("Compile\t%s") % keys['compileScript'],
                           _translate("Compile the exp to a script"))
        self.Bind(wx.EVT_MENU, self.compileScript, item)
        self.bldrRun = menu.Append(wx.ID_ANY,
                           _translate("Run\t%s") % keys['runScript'],
                           _translate("Run the current script"))
        self.Bind(wx.EVT_MENU, self.runFile, self.bldrRun, id=self.bldrRun)
        item = menu.Append(wx.ID_ANY,
                           _translate("Send to runner\t%s") % keys['runnerScript'],
                           _translate("Send current script to runner"))
        self.Bind(wx.EVT_MENU, self.runFile, item)
        menu.AppendSeparator()
        item = menu.Append(wx.ID_ANY,
                           _translate("PsychoPy updates..."),
                           _translate("Update PsychoPy to the latest, or a "
                                      "specific, version"))
        self.Bind(wx.EVT_MENU, self.app.openUpdater, item)
        if hasattr(self.app, 'benchmarkWizard'):
            item = menu.Append(wx.ID_ANY,
                               _translate("Benchmark wizard"),
                               _translate("Check software & hardware, generate "
                                          "report"))
            self.Bind(wx.EVT_MENU, self.app.benchmarkWizard, item)

        # ---_experiment---#000000#FFFFFF-------------------------------------
        self.expMenu = wx.Menu()
        menuBar.Append(self.expMenu, _translate('&Experiment'))
        menu = self.expMenu
        item = menu.Append(wx.ID_ANY,
                           _translate("&New Routine\t%s") % keys['newRoutine'],
                           _translate("Create a new routine (e.g. the trial "
                                      "definition)"))
        self.Bind(wx.EVT_MENU, self.addRoutine, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("&Copy Routine\t%s") % keys[
                               'copyRoutine'],
                           _translate("Copy the current routine so it can be "
                                      "used in another exp"),
                           wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onCopyRoutine, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("&Paste Routine\t%s") % keys[
                               'pasteRoutine'],
                           _translate("Paste the Routine into the current "
                                      "experiment"),
                           wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onPasteRoutine, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("&Rename Routine\t%s") % keys[
                               'renameRoutine'],
                           _translate("Change the name of this routine"))
        self.Bind(wx.EVT_MENU, self.renameRoutine, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("Paste Component\t%s") % keys[
                               'pasteCompon'],
                           _translate(
                               "Paste the Component at bottom of the current "
                               "Routine"),
                           wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onPasteCompon, item)
        menu.AppendSeparator()

        item = menu.Append(wx.ID_ANY,
                           _translate("Insert Routine in Flow"),
                           _translate(
                               "Select one of your routines to be inserted"
                               " into the experiment flow"))
        self.Bind(wx.EVT_MENU, self.flowPanel.onInsertRoutine, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("Insert Loop in Flow"),
                           _translate("Create a new loop in your flow window"))
        self.Bind(wx.EVT_MENU, self.flowPanel.insertLoop, item)

        # ---_demos---#000000#FFFFFF------------------------------------------
        # for demos we need a dict where the event ID will correspond to a
        # filename

        self.demosMenu = wx.Menu()
        # unpack demos option
        menu = self.demosMenu
        item = menu.Append(wx.ID_ANY,
                           _translate("&Unpack Demos..."),
                           _translate(
                               "Unpack demos to a writable location (so that"
                               " they can be run)"))
        self.Bind(wx.EVT_MENU, self.demosUnpack, item)
        menu.AppendSeparator()
        # add any demos that are found in the prefs['demosUnpacked'] folder
        self.updateDemosMenu()
        menuBar.Append(self.demosMenu, _translate('&Demos'))

        # ---_onlineStudies---#000000#FFFFFF-------------------------------------------
        self.pavloviaMenu = pavlovia_ui.menu.PavloviaMenu(parent=self)
        menuBar.Append(self.pavloviaMenu, _translate("Pavlovia.org"))

        # ---_window---#000000#FFFFFF-----------------------------------------
        self.windowMenu = FrameSwitcher(self)
        menuBar.Append(self.windowMenu,
                    _translate("Window"))

        # ---_help---#000000#FFFFFF-------------------------------------------
        self.helpMenu = wx.Menu()
        menuBar.Append(self.helpMenu, _translate('&Help'))
        menu = self.helpMenu

        item = menu.Append(wx.ID_ANY,
                           _translate("&PsychoPy Homepage"),
                           _translate("Go to the PsychoPy homepage"))
        self.Bind(wx.EVT_MENU, self.app.followLink, item)
        self.app.urls[item.GetId()] = self.app.urls['psychopyHome']
        item = menu.Append(wx.ID_ANY,
                           _translate("&PsychoPy Builder Help"),
                           _translate(
                               "Go to the online documentation for PsychoPy"
                               " Builder"))
        self.Bind(wx.EVT_MENU, self.app.followLink, item)
        self.app.urls[item.GetId()] = self.app.urls['builderHelp']

        menu.AppendSeparator()
        item = menu.Append(wx.ID_ANY,
                           _translate("&System Info..."),
                           _translate("Get system information."))
        self.Bind(wx.EVT_MENU, self.app.showSystemInfo, id=item.GetId())

        menu.AppendSeparator()
        menu.Append(wx.ID_ABOUT, _translate(
            "&About..."), _translate("About PsychoPy"))
        self.Bind(wx.EVT_MENU, self.app.showAbout, id=wx.ID_ABOUT)
        item = menu.Append(wx.ID_ANY,
                           _translate("&News..."),
                           _translate("News"))
        self.Bind(wx.EVT_MENU, self.app.showNews, id=item.GetId())

        self.SetMenuBar(menuBar)

    def commandCloseFrame(self, event):
        """Defines Builder Frame Closing Event"""
        self.Close()

    def closeFrame(self, event=None, checkSave=True):
        """Defines Frame closing behavior, such as checking for file
           saving"""
        # close file first (check for save) but no need to update view
        okToClose = self.fileClose(updateViews=False, checkSave=checkSave)

        if not okToClose:
            if hasattr(event, 'Veto'):
                event.Veto()
            return
        else:
            # as of wx3.0 the AUI manager needs to be uninitialised explicitly
            self._mgr.UnInit()
            # is it the last frame?
            lastFrame = len(self.app.getAllFrames()) == 1
            quitting = self.app.quitting
            if lastFrame and sys.platform != 'darwin' and not quitting:
                self.app.quit(event)
            else:
                self.app.forgetFrame(self)
                self.Destroy()  # required

            # Show Runner if hidden
            if self.app.runner is not None:
                self.app.showRunner()
        self.app.updateWindowMenu()

    def quit(self, event=None):
        """quit the app
        """
        self.app.quit(event)

    def fileNew(self, event=None, closeCurrent=True):
        """Create a default experiment (maybe an empty one instead)
        """
        # Note: this is NOT the method called by the File>New menu item.
        # That calls app.newBuilderFrame() instead
        if closeCurrent:  # if no exp exists then don't try to close it
            if not self.fileClose(updateViews=False):
                # close the existing (and prompt for save if necess)
                return False
        self.filename = 'untitled.psyexp'
        self.exp = experiment.Experiment(prefs=self.app.prefs)
        defaultName = 'trial'
        # create the trial routine as an example
        self.exp.addRoutine(defaultName)
        self.exp.flow.addRoutine(
            self.exp.routines[defaultName], pos=1)  # add it to flow
        # add it to user's namespace
        self.exp.namespace.add(defaultName, self.exp.namespace.user)
        routine = self.exp.routines[defaultName]
        ## add an ISI component by default
        # components = self.componentButtons.components
        # Static = components['StaticComponent']
        # ISI = Static(self.exp, parentName=defaultName, name='ISI',
        #             startType='time (s)', startVal=0.0,
        #             stopType='duration (s)', stopVal=0.5)
        # routine.addComponent(ISI)
        self.resetUndoStack()
        self.setIsModified(False)
        self.updateAllViews()
        self.app.updateWindowMenu()

    def fileOpen(self, event=None, filename=None, closeCurrent=True):
        """Open a FileDialog, then load the file if possible.
        """
        if filename is None:
            _wld = "PsychoPy experiments (*.psyexp)|*.psyexp|Any file (*.*)|*"
            dlg = wx.FileDialog(self, message=_translate("Open file ..."),
                                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                                wildcard=_translate(_wld))
            if dlg.ShowModal() != wx.ID_OK:
                return 0
            filename = dlg.GetPath()

        # did user try to open a script in Builder?
        if filename.endswith('.py'):
            self.app.showCoder()  # ensures that a coder window exists
            self.app.coder.setCurrentDoc(filename)
            self.app.coder.setFileModified(False)
            return
        with WindowFrozen(ctrl=self):
            # try to pause rendering until all panels updated
            if closeCurrent:
                if not self.fileClose(updateViews=False):
                    # close the existing (and prompt for save if necess)
                    return False
            self.exp = experiment.Experiment(prefs=self.app.prefs)
            try:
                self.exp.loadFromXML(filename)
            except Exception:
                print(u"Failed to load {}. Please send the following to"
                      u" the PsychoPy user list".format(filename))
                traceback.print_exc()
                logging.flush()
            self.resetUndoStack()
            self.setIsModified(False)
            self.filename = filename
            # routinePanel.addRoutinePage() is done in
            # routinePanel.redrawRoutines(), called by self.updateAllViews()
            # update the views
            self.updateAllViews()  # if frozen effect will be visible on thaw
        self.updateReadme()
        self.fileHistory.AddFileToHistory(filename)
        self.htmlPath = None  # so we won't accidentally save to other html exp

        if self.app.runner:
            self.app.runner.addTask(fileName=self.filename)  # Add to Runner

        try:
            self.project = pavlovia.getProject(filename)
        except Exception as e:  # failed for
            self.project = None
            print(e)
        self.app.updateWindowMenu()

    def fileSave(self, event=None, filename=None):
        """Save file, revert to SaveAs if the file hasn't yet been saved
        """
        if filename is None:
            filename = self.filename
        if filename.startswith('untitled'):
            if not self.fileSaveAs(filename):
                return False  # the user cancelled during saveAs
        else:
            filename = self.exp.saveToXML(filename)
            self.fileHistory.AddFileToHistory(filename)
        self.setIsModified(False)
        # if export on save then we should have an html file to update
        if self._getExportPref('on save') and os.path.split(filename)[0]:
            self.filename = filename
            self.fileExport(htmlPath=self.htmlPath)
        return True

    def fileSaveAs(self, event=None, filename=None):
        """Defines Save File as Behavior
        """
        shortFilename = self.getShortFilename()
        expName = self.exp.getExpName()
        if (not expName) or (shortFilename == expName):
            usingDefaultName = True
        else:
            usingDefaultName = False
        if filename is None:
            filename = self.filename
        initPath, filename = os.path.split(filename)

        _w = "PsychoPy experiments (*.psyexp)|*.psyexp|Any file (*.*)|*"
        if sys.platform != 'darwin':
            _w += '.*'
        wildcard = _translate(_w)
        returnVal = False
        dlg = wx.FileDialog(
            self, message=_translate("Save file as ..."), defaultDir=initPath,
            defaultFile=filename, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            wildcard=wildcard)

        if dlg.ShowModal() == wx.ID_OK:
            newPath = dlg.GetPath()
            # update exp name
            # if user has not manually renamed experiment
            if usingDefaultName:
                newShortName = os.path.splitext(
                    os.path.split(newPath)[1])[0]
                self.exp.setExpName(newShortName)
            # actually save
            self.fileSave(event=None, filename=newPath)
            self.filename = newPath
            returnVal = 1
        dlg.Destroy()

        self.updateWindowTitle()
        return returnVal

    def fileExport(self, event=None, htmlPath=None):
        """Exports the script as an HTML file (PsychoJS library)
        """
        # get path if not given one
        expPath, expName = os.path.split(self.filename)
        if htmlPath is None:
            htmlPath = self._getHtmlPath(self.filename)
        if not htmlPath:
            return
        dlg = ExportFileDialog(self, wx.ID_ANY,
                               title=_translate("Export HTML file"),
                               filePath=htmlPath,
                               exp=self.exp)

        export = dlg.exportOnSave
        if self.exp.settings.params['exportHTML'].val == 'manually':
            retVal = dlg.ShowModal()
            self.exp.settings.params['exportHTML'].val = export.GetString(export.GetCurrentSelection())
            if retVal != wx.ID_OK:  # User cancelled export
                return False

        exportPath = os.path.join(htmlPath, expName.replace('.psyexp', '.js'))
        self.generateScript(experimentPath=exportPath,
                            exp=self.exp,
                            target="PsychoJS")

    def getShortFilename(self):
        """returns the filename without path or extension
        """
        return os.path.splitext(os.path.split(self.filename)[1])[0]

    # def pluginManager(self, evt=None, value=True):
    #     """Show the plugin manger frame."""
    #     PluginManagerFrame(self).ShowModal()

    def updateReadme(self):
        """Check whether there is a readme file in this folder and try to show
        """
        # create the frame if we don't have one yet
        if not hasattr(self, 'readmeFrame') or self.readmeFrame is None:
            self.readmeFrame = ReadmeFrame(parent=self)
        # look for a readme file
        if self.filename and self.filename != 'untitled.psyexp':
            dirname = os.path.dirname(self.filename)
            possibles = glob.glob(os.path.join(dirname, 'readme*'))
            if len(possibles) == 0:
                possibles = glob.glob(os.path.join(dirname, 'Readme*'))
                possibles.extend(glob.glob(os.path.join(dirname, 'README*')))
            # still haven't found a file so use default name
            if len(possibles) == 0:
                self.readmeFilename = os.path.join(
                    dirname, 'readme.txt')  # use this as our default
            else:
                self.readmeFilename = possibles[0]  # take the first one found
        else:
            self.readmeFilename = None
        self.readmeFrame.setFile(self.readmeFilename)
        content = self.readmeFrame.ctrl.GetValue()
        if content and self.prefs['alwaysShowReadme']:
            self.showReadme()

    def showReadme(self, evt=None, value=True):
        """Shows Readme file
        """
        if not self.readmeFrame.IsShown():
            self.readmeFrame.Show(value)

    def toggleReadme(self, evt=None):
        """Toggles visibility of Readme file
        """
        if self.readmeFrame is None:
            self.updateReadme()
            self.showReadme()
        else:
            self.readmeFrame.toggleVisible()

    def OnFileHistory(self, evt=None):
        """get the file based on the menu ID
        """
        fileNum = evt.GetId() - wx.ID_FILE1
        path = self.fileHistory.GetHistoryFile(fileNum)
        self.fileOpen(filename=path)
        # add it back to the history so it will be moved up the list
        self.fileHistory.AddFileToHistory(path)

    def checkSave(self):
        """Check whether we need to save before quitting
        """
        if hasattr(self, 'isModified') and self.isModified:
            self.Show(True)
            self.Raise()
            self.app.SetTopWindow(self)
            msg = _translate('Experiment %s has changed. Save before '
                             'quitting?') % self.filename
            dlg = dialogs.MessageDialog(self, msg, type='Warning')
            resp = dlg.ShowModal()
            if resp == wx.ID_CANCEL:
                return False  # return, don't quit
            elif resp == wx.ID_YES:
                if not self.fileSave():
                    return False  # user might cancel during save
            elif resp == wx.ID_NO:
                pass  # don't save just quit
        return True

    def fileClose(self, event=None, checkSave=True, updateViews=True):
        """This is typically only called when the user x
        """
        if checkSave:
            ok = self.checkSave()
            if not ok:
                return False  # user cancelled
        if self.filename is None:
            frameData = self.appData['defaultFrame']
        else:
            frameData = dict(self.appData['defaultFrame'])
            self.appData['prevFiles'].append(self.filename)

            # get size and window layout info
        if self.IsIconized():
            self.Iconize(False)  # will return to normal mode to get size info
            frameData['state'] = 'normal'
        elif self.IsMaximized():
            # will briefly return to normal mode to get size info
            self.Maximize(False)
            frameData['state'] = 'maxim'
        else:
            frameData['state'] = 'normal'
        frameData['auiPerspective'] = self._mgr.SavePerspective()
        frameData['winW'], frameData['winH'] = self.GetSize()
        frameData['winX'], frameData['winY'] = self.GetPosition()

        # truncate history to the recent-most last N unique files, where
        # N = self.fileHistoryMaxFiles, as defined in makeMenus()
        for ii in range(self.fileHistory.GetCount()):
            self.appData['fileHistory'].append(
                self.fileHistory.GetHistoryFile(ii))
        # fileClose gets calls multiple times, so remove redundancy
        # while preserving order; end of the list is recent-most:
        tmp = []
        fhMax = self.fileHistoryMaxFiles
        for f in self.appData['fileHistory'][-3 * fhMax:]:
            if f not in tmp:
                tmp.append(f)
        self.appData['fileHistory'] = copy.copy(tmp[-fhMax:])

        # assign the data to this filename
        self.appData['frames'][self.filename] = frameData
        # save the display data only for those frames in the history:
        tmp2 = {}
        for f in self.appData['frames']:
            if f in self.appData['fileHistory']:
                tmp2[f] = self.appData['frames'][f]
        self.appData['frames'] = copy.copy(tmp2)

        # close self
        self.routinePanel.removePages()
        self.filename = 'untitled.psyexp'
        # add the current exp as the start point for undo:
        self.resetUndoStack()
        if updateViews:
            self.updateAllViews()
        return 1

    def updateAllViews(self):
        """Updates Flow Panel, Routine Panel, and Window Title simultaneously
        """
        self.flowPanel.draw()
        self.routinePanel.redrawRoutines()
        self.updateWindowTitle()

    def updateWindowTitle(self, newTitle=None):
        """Defines behavior to update window Title
        """
        if newTitle is None:
            shortName = os.path.split(self.filename)[-1]
            newTitle = '%s - PsychoPy Builder' % (shortName)
        self.SetTitle(newTitle)

    def setIsModified(self, newVal=None):
        """Sets current modified status and updates save icon accordingly.

        This method is called by the methods fileSave, undo, redo,
        addToUndoStack and it is usually preferably to call those
        than to call this directly.

        Call with ``newVal=None``, to only update the save icon(s)
        """
        if newVal is None:
            newVal = self.getIsModified()
        else:
            self.isModified = newVal
        if hasattr(self, 'bldrBtnSave'):
            self.toolbar.EnableTool(self.bldrBtnSave.Id, newVal)
        self.fileMenu.Enable(wx.ID_SAVE, newVal)

    def getIsModified(self):
        """Checks if changes were made"""
        return self.isModified

    def resetUndoStack(self):
        """Reset the undo stack. do *immediately after* creating a new exp.

        Implicitly calls addToUndoStack() using the current exp as the state
        """
        self.currentUndoLevel = 1  # 1 is current, 2 is back one setp...
        self.currentUndoStack = []
        self.addToUndoStack()
        self.updateUndoRedo()
        self.setIsModified(newVal=False)  # update save icon if needed

    def addToUndoStack(self, action="", state=None):
        """Add the given ``action`` to the currentUndoStack, associated
        with the @state@. ``state`` should be a copy of the exp
        from *immediately after* the action was taken.
        If no ``state`` is given the current state of the experiment is used.

        If we are at end of stack already then simply append the action.  If
        not (user has done an undo) then remove orphan actions and append.
        """
        if state is None:
            state = copy.deepcopy(self.exp)
        # remove actions from after the current level
        if self.currentUndoLevel > 1:
            self.currentUndoStack = self.currentUndoStack[
                                    :-(self.currentUndoLevel - 1)]
            self.currentUndoLevel = 1
        # append this action
        self.currentUndoStack.append({'action': action, 'state': state})
        self.setIsModified(newVal=True)  # update save icon if needed
        self.updateUndoRedo()

    def undo(self, event=None):
        """Step the exp back one level in the @currentUndoStack@ if possible,
        and update the windows.

        Returns the final undo level (1=current, >1 for further in past)
        or -1 if redo failed (probably can't undo)
        """
        if self.currentUndoLevel >= len(self.currentUndoStack):
            return -1  # can't undo
        self.currentUndoLevel += 1
        state = self.currentUndoStack[-self.currentUndoLevel]['state']
        self.exp = copy.deepcopy(state)
        self.updateAllViews()
        self.setIsModified(newVal=True)  # update save icon if needed
        self.updateUndoRedo()

        return self.currentUndoLevel

    def redo(self, event=None):
        """Step the exp up one level in the @currentUndoStack@ if possible,
        and update the windows.

        Returns the final undo level (0=current, >0 for further in past)
        or -1 if redo failed (probably can't redo)
        """
        if self.currentUndoLevel <= 1:
            return -1  # can't redo, we're already at latest state
        self.currentUndoLevel -= 1
        self.exp = copy.deepcopy(
            self.currentUndoStack[-self.currentUndoLevel]['state'])
        self.updateUndoRedo()
        self.updateAllViews()
        self.setIsModified(newVal=True)  # update save icon if needed
        return self.currentUndoLevel

    def paste(self, event=None):
        """This receives paste commands for all child dialog boxes as well
        """
        foc = self.FindFocus()
        if hasattr(foc, 'Paste'):
            foc.Paste()

    def updateUndoRedo(self):
        """Defines Undo and Redo commands for the window
        """
        undoLevel = self.currentUndoLevel
        # check undo
        if undoLevel >= len(self.currentUndoStack):
            # can't undo if we're at top of undo stack
            label = _translate("Undo\t%s") % self.app.keys['undo']
            enable = False
        else:
            action = self.currentUndoStack[-undoLevel]['action']
            txt = _translate("Undo %(action)s\t%(key)s")
            fmt = {'action': action, 'key': self.app.keys['undo']}
            label = txt % fmt
            enable = True
        self._undoLabel.SetItemLabel(label)
        if hasattr(self, 'bldrBtnUndo'):
            self.toolbar.EnableTool(self.bldrBtnUndo.Id, enable)
        self.editMenu.Enable(wx.ID_UNDO, enable)

        # check redo
        if undoLevel == 1:
            label = _translate("Redo\t%s") % self.app.keys['redo']
            enable = False
        else:
            action = self.currentUndoStack[-undoLevel + 1]['action']
            txt = _translate("Redo %(action)s\t%(key)s")
            fmt = {'action': action, 'key': self.app.keys['redo']}
            label = txt % fmt
            enable = True
        self._redoLabel.SetItemLabel(label)
        if hasattr(self, 'bldrBtnRedo'):
            self.toolbar.EnableTool(self.bldrBtnRedo.Id, enable)
        self.editMenu.Enable(wx.ID_REDO, enable)

    def demosUnpack(self, event=None):
        """Get a folder location from the user and unpack demos into it."""
        # choose a dir to unpack in
        dlg = wx.DirDialog(parent=self, message=_translate(
            "Location to unpack demos"))
        if dlg.ShowModal() == wx.ID_OK:
            unpackFolder = dlg.GetPath()
        else:
            return -1  # user cancelled
        # ensure it's an empty dir:
        if os.listdir(unpackFolder) != []:
            unpackFolder = os.path.join(unpackFolder, 'PsychoPy3 Demos')
            if not os.path.isdir(unpackFolder):
                os.mkdir(unpackFolder)
        mergeFolder(os.path.join(self.paths['demos'], 'builder'),
                    unpackFolder)
        self.prefs['unpackedDemosDir'] = unpackFolder
        self.app.prefs.saveUserPrefs()
        self.updateDemosMenu()

    def demoLoad(self, event=None):
        """Defines Demo Loading Event."""
        fileDir = self.demos[event.GetId()]
        files = glob.glob(os.path.join(fileDir, '*.psyexp'))
        if len(files) == 0:
            print("Found no psyexp files in %s" % fileDir)
        else:
            self.fileOpen(event=None, filename=files[0], closeCurrent=True)

    def updateDemosMenu(self):
        """Update Demos menu as needed."""
        unpacked = self.prefs['unpackedDemosDir']
        if not unpacked:
            return
        # list available demos
        demoList = sorted(glob.glob(os.path.join(unpacked, '*')))
        self.demos = {wx.NewIdRef(): demoList[n]
                      for n in range(len(demoList))}
        for thisID in self.demos:
            junk, shortname = os.path.split(self.demos[thisID])
            if (shortname.startswith('_') or
                    shortname.lower().startswith('readme.')):
                continue  # ignore 'private' or README files
            self.demosMenu.Append(thisID, shortname)
            self.Bind(wx.EVT_MENU, self.demoLoad, id=thisID)

    def runFile(self, event=None):
        """Open Runner for running the psyexp file."""
        if not os.path.exists(self.filename):
            ok = self.fileSave(self.filename)
            if not ok:
                return  # save file before compiling script

        if self.getIsModified():
            ok = self.fileSave(self.filename)
            if not ok:
                return  # save file before compiling script

        self.stdoutFrame.addTask(fileName=self.filename)
        self.app.runner.Raise()
        if event:
            if event.Id in [self.bldrBtnRun.Id, self.bldrRun.Id]:
                self.app.runner.panel.runLocal(event)
            else:
                self.app.showRunner()

    def onCopyRoutine(self, event=None):
        """copy the current routine from self.routinePanel
        to self.app.copiedRoutine.
        """
        r = copy.deepcopy(self.routinePanel.getCurrentRoutine())
        if r is not None:
            self.app.copiedRoutine = r

    def onPasteRoutine(self, event=None):
        """Paste the current routine from self.app.copiedRoutine to a new page
        in self.routinePanel after promting for a new name.
        """
        if self.app.copiedRoutine is None:
            return -1
        origName = self.app.copiedRoutine.name
        defaultName = self.exp.namespace.makeValid(origName)
        msg = _translate('New name for copy of "%(copied)s"?  [%(default)s]')
        vals = {'copied': origName, 'default': defaultName}
        message = msg % vals
        dlg = wx.TextEntryDialog(self, message=message,
                                 caption=_translate('Paste Routine'))
        if dlg.ShowModal() == wx.ID_OK:
            routineName = dlg.GetValue()
            newRoutine = copy.deepcopy(self.app.copiedRoutine)
            if not routineName:
                routineName = defaultName
            newRoutine.name = self.exp.namespace.makeValid(routineName)
            newRoutine.params['name'] = newRoutine.name
            self.exp.namespace.add(newRoutine.name)
            # add to the experiment
            self.exp.addRoutine(newRoutine.name, newRoutine)
            for newComp in newRoutine:  # routine == list of components
                newName = self.exp.namespace.makeValid(newComp.params['name'])
                self.exp.namespace.add(newName)
                newComp.params['name'].val = newName
            # could do redrawRoutines but would be slower?
            self.routinePanel.addRoutinePage(newRoutine.name, newRoutine)
            self.addToUndoStack("PASTE Routine `%s`" % newRoutine.name)
        dlg.Destroy()

    def onPasteCompon(self, event=None):
        """
        Paste the copied Component (if there is one) into the current
        Routine
        """
        routinePage = self.routinePanel.getCurrentPage()
        routinePage.pasteCompon()

    def onURL(self, evt):
        """decompose the URL of a file and line number"""
        # "C:\Program Files\wxPython...\samples\hangman\hangman.py"
        filename = evt.GetString().split('"')[1]
        lineNumber = int(evt.GetString().split(',')[1][5:])
        self.app.showCoder()
        self.app.coder.gotoLine(filename, lineNumber)

    def setExperimentSettings(self, event=None, timeout=None):
        """Defines ability to save experiment settings
        """
        component = self.exp.settings
        # does this component have a help page?
        if hasattr(component, 'url'):
            helpUrl = component.url
        else:
            helpUrl = None
        title = '%s Properties' % self.exp.getExpName()
        dlg = DlgExperimentProperties(frame=self, title=title,
                                      params=component.params,
                                      helpUrl=helpUrl, order=component.order,
                                      timeout=timeout)
        if dlg.OK:
            self.addToUndoStack("EDIT experiment settings")
            self.setIsModified(True)

    def addRoutine(self, event=None):
        """Defines ability to add routine in the routine panel
        """
        self.routinePanel.createNewRoutine()

    def renameRoutine(self, name, event=None, returnName=True):
        """Defines ability to rename routine in the routine panel
        """
        # get notebook details
        currentRoutine = self.routinePanel.getCurrentPage()
        currentRoutineIndex = self.routinePanel.GetPageIndex(currentRoutine)
        routine = self.routinePanel.GetPage(
            self.routinePanel.GetSelection()).routine
        oldName = routine.name
        msg = _translate("What is the new name for the Routine?")
        dlg = wx.TextEntryDialog(self, message=msg, value=oldName,
                                 caption=_translate('Rename'))
        exp = self.exp
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.GetValue()
            # silently auto-adjust the name to be valid, and register in the
            # namespace:
            name = exp.namespace.makeValid(
                name, prefix='routine')
            if oldName in self.exp.routines:
                # Swap old with new names
                self.exp.routines[oldName].name = name
                self.exp.routines[name] = self.exp.routines.pop(oldName)
                for comp in self.exp.routines[name]:
                    comp.parentName = name
                self.exp.namespace.rename(oldName, name)
                self.routinePanel.renameRoutinePage(currentRoutineIndex, name)
                self.addToUndoStack("`RENAME Routine `%s`" % oldName)
                dlg.Destroy()
                self.flowPanel.draw()

    def compileScript(self, event=None):
        """Defines compile script button behavior"""
        fullPath = self.filename.replace('.psyexp', '.py')
        self.generateScript(experimentPath=fullPath, exp=self.exp)
        self.app.showCoder()  # make sure coder is visible
        self.app.coder.fileNew(filepath=fullPath)
        self.app.coder.fileReload(event=None, filename=fullPath)

    @property
    def stdoutFrame(self):
        """
        Gets Experiment Runner stdout.
        """
        if not self.app.runner:
            self.app.runner = self.app.newRunnerFrame()
        return self.app.runner

    def _getHtmlPath(self, filename):
        expPath = os.path.split(filename)[0]
        if not os.path.isdir(expPath):
            retVal = self.fileSave()
            if retVal:
                return self._getHtmlPath(self.filename)
            else:
                return False

        htmlPath = os.path.join(expPath, self.exp.htmlFolder)
        return htmlPath

    def _getExportPref(self, pref):
        """Returns True if pref matches exportHTML preference"""
        if pref.lower() not in [prefs.lower() for prefs in self.exp.settings.params['exportHTML'].allowedVals]:
            raise ValueError("'{}' is not an allowed value for {}".format(pref, 'exportHTML'))
        exportHtml = str(self.exp.settings.params['exportHTML'].val).lower()
        if exportHtml == pref.lower():
            return True

    def onPavloviaSync(self, evt=None):
        if self._getExportPref('on sync'):
            htmlPath = self._getHtmlPath(self.filename)
            if htmlPath:
                self.fileExport(htmlPath=htmlPath)
            else:
                return

        self.enablePavloviaButton(['pavloviaSync', 'pavloviaRun'], False)
        try:
            retVal = pavlovia_ui.syncProject(parent=self, project=self.project)
            pavlovia.knownProjects.save()  # update projects.json
            self.gitFeedback(retVal)
        finally:
            self.enablePavloviaButton(['pavloviaSync', 'pavloviaRun'], True)

    def onPavloviaRun(self, evt=None):
        if self._getExportPref('on save'):
            self.fileSave()
            retVal = pavlovia_ui.syncProject(parent=self, project=self.project,
                                             closeFrameWhenDone=False)
            self.gitFeedback(retVal)
        elif self._getExportPref('on sync'):
            self.fileExport(htmlPath=self._getHtmlPath(self.filename))
            retVal = pavlovia_ui.syncProject(parent=self, project=self.project,
                                             closeFrameWhenDone=False)
            self.gitFeedback(retVal)
        elif self._getExportPref('manually'):
            # Check htmlpath and projects exists
            noHtmlFolder = not os.path.isdir(self._getHtmlPath(self.filename))
            noProject = not bool(pavlovia.getProject(self.filename))
            if noHtmlFolder:
                self.fileExport()
            if noProject or noHtmlFolder:
                retVal = pavlovia_ui.syncProject(parent=self, project=self.project,
                                                 closeFrameWhenDone=False)
                self.gitFeedback(retVal)
        if self.project:
            htmlPath = self.exp.settings.params['HTML path'].val
            self.project.pavloviaStatus = 'ACTIVATED'
            url = "https://pavlovia.org/run/{}/{}".format(self.project.id, htmlPath)
            wx.LaunchDefaultBrowser(url)

    def enablePavloviaButton(self, buttons, enable):
        """
        Enables or disables Pavlovia buttons.

        Parameters
        ----------
        name: string, list
            Takes single buttons 'pavloviaSync', 'pavloviaRun', 'pavloviaSearch', 'pavloviaUser',
            or multiple buttons in string 'pavloviaSync, pavloviaRun',
            or comma separated list of strings ['pavloviaSync', 'pavloviaRun', ...].
        enable: bool
            True enables and False disables the button
        """
        if isinstance(buttons, str):
            buttons = buttons.split(',')
        for button in buttons:
            self.toolbar.EnableTool(self.btnHandles[button.strip(' ')].GetId(), enable)

    def setPavloviaUser(self, user):
        # TODO: update user icon on button to user avatar
        pass

    def gitFeedback(self, val):
        """
        Set feedback color for the Pavlovia Sync toolbar button.

        Parameters
        ----------
        val: int
            Status of git sync. 1 for SUCCESS (green), 0 or -1 for FAIL (RED)
        """
        feedbackTime = 1500
        colour = {0: "red", -1: "red", 1: "green"}
        toolbarSize = 32

        # Store original
        origBtn = self.btnHandles['pavloviaSync'].NormalBitmap
        # Create new feedback bitmap
        feedbackBmp = self.app.iconCache.getBitmap(
                name='{}globe.png'.format(colour[val]),
                size=toolbarSize)

        # Set feedback button
        self.btnHandles['pavloviaSync'].SetNormalBitmap(feedbackBmp)
        self.toolbar.Realize()
        self.toolbar.Refresh()

        # Reset button to default state after time
        wx.CallLater(feedbackTime, self.btnHandles['pavloviaSync'].SetNormalBitmap, origBtn)
        wx.CallLater(feedbackTime + 50, self.toolbar.Realize)
        wx.CallLater(feedbackTime + 50, self.toolbar.Refresh)

    @property
    def project(self):
        """A PavloviaProject object if one is known for this experiment
        """
        if 'project' in self.__dict__ and self.__dict__['project']:
            return self.__dict__['project']
        elif self.filename and pavlovia.getProject(self.filename):
            return pavlovia.getProject(self.filename)
        else:
            return None

    @project.setter
    def project(self, project):
        self.__dict__['project'] = project


class RoutinesNotebook(aui.AuiNotebook, ThemeMixin):
    """A notebook that stores one or more routines
    """

    def __init__(self, frame, id=-1):
        self.frame = frame
        self.app = frame.app
        self.routineMaxSize = 2
        self.appData = self.app.prefs.appData
        aui.AuiNotebook.__init__(self, frame, id)
        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.onClosePane)

        # double buffered better rendering except if retina
        self.SetDoubleBuffered(self.frame.IsDoubleBuffered())

        self._applyAppTheme()
        if not hasattr(self.frame, 'exp'):
            return  # we haven't yet added an exp

    def _applyAppTheme(self, target=None):
        self.SetArtProvider(PsychopyTabArt())
        self.GetAuiManager().SetArtProvider(PsychopyDockArt())
        for index in range(self.GetPageCount()):
            page = self.GetPage(index)
            # double buffered better rendering except if retina
            self.SetDoubleBuffered(self.frame.IsDoubleBuffered())
            page._applyAppTheme()
        self.Refresh()

    def getCurrentRoutine(self):
        routinePage = self.getCurrentPage()
        if routinePage:
            return routinePage.routine  # no routine page
        return None

    def setCurrentRoutine(self, routine):
        for ii in range(self.GetPageCount()):
            if routine is self.GetPage(ii).routine:
                self.SetSelection(ii)

    def getCurrentPage(self):
        if self.GetSelection() >= 0:
            return self.GetPage(self.GetSelection())
        return None

    def addRoutinePage(self, routineName, routine):
        #        routinePage = RoutinePage(parent=self, routine=routine)
        routinePage = RoutineCanvas(notebook=self, routine=routine)
        self.AddPage(routinePage, routineName)

    def renameRoutinePage(self, index, newName, ):
        self.SetPageText(index, newName)

    def removePages(self):
        for ii in range(self.GetPageCount()):
            currId = self.GetSelection()
            self.DeletePage(currId)

    def createNewRoutine(self, returnName=False):
        msg = _translate("What is the name for the new Routine? "
                         "(e.g. instr, trial, feedback)")
        dlg = wx.TextEntryDialog(self, message=msg,
                                 caption=_translate('New Routine'))
        exp = self.frame.exp
        routineName = None
        if dlg.ShowModal() == wx.ID_OK:
            routineName = dlg.GetValue()
            # silently auto-adjust the name to be valid, and register in the
            # namespace:
            routineName = exp.namespace.makeValid(
                routineName, prefix='routine')
            exp.namespace.add(routineName)  # add to the namespace
            exp.addRoutine(routineName)  # add to the experiment
            # then to the notebook:
            self.addRoutinePage(routineName, exp.routines[routineName])
            self.frame.addToUndoStack("NEW Routine `%s`" % routineName)
        dlg.Destroy()
        if returnName:
            return routineName

    def onClosePane(self, event=None):
        """Close the pane and remove the routine from the exp
        """
        routine = self.GetPage(event.GetSelection()).routine
        name = routine.name
        # update experiment object, namespace, and flow window (if this is
        # being used)
        if name in self.frame.exp.routines:
            # remove names of the routine and its components from namespace
            _nsp = self.frame.exp.namespace
            for c in self.frame.exp.routines[name]:
                _nsp.remove(c.params['name'].val)
            _nsp.remove(self.frame.exp.routines[name].name)
            del self.frame.exp.routines[name]
        if routine in self.frame.exp.flow:
            self.frame.exp.flow.removeComponent(routine)
            self.frame.flowPanel.draw()
        self.frame.addToUndoStack("REMOVE Routine `%s`" % (name))

    def increaseSize(self, event=None):
        self.appData['routineSize'] = min(
            self.routineMaxSize, self.appData['routineSize'] + 1)
        with WindowFrozen(self):
            self.redrawRoutines()

    def decreaseSize(self, event=None):
        self.appData['routineSize'] = max(0, self.appData['routineSize'] - 1)
        with WindowFrozen(self):
            self.redrawRoutines()

    def redrawRoutines(self):
        """Removes all the routines, adds them back (alphabetical order),
        sets current back to orig
        """
        currPage = self.GetSelection()
        self.removePages()
        displayOrder = sorted(self.frame.exp.routines.keys())  # alphabetical
        for routineName in displayOrder:
            self.addRoutinePage(
                routineName, self.frame.exp.routines[routineName])
        if currPage > -1:
            self.SetSelection(currPage)


class RoutineCanvas(wx.ScrolledWindow):
    """Represents a single routine (used as page in RoutinesNotebook)"""

    def __init__(self, notebook, id=wx.ID_ANY, routine=None):
        """This window is based heavily on the PseudoDC demo of wxPython
        """
        wx.ScrolledWindow.__init__(
            self, notebook, id, (0, 0), style=wx.BORDER_NONE | wx.VSCROLL)

        self.frame = notebook.frame
        self.app = self.frame.app
        self.dpi = self.app.dpi
        self.lines = []
        self.maxWidth = self.GetSize().GetWidth()
        self.maxHeight = 15 * self.dpi
        self.x = self.y = 0
        self.curLine = []
        self.drawing = False
        self.drawSize = self.app.prefs.appData['routineSize']
        # auto-rescale based on number of components and window size is jumpy
        # when switch between routines of diff drawing sizes
        self.iconSize = (24, 24, 48)[self.drawSize]  # only 24, 48 so far
        self.fontBaseSize = (1100, 1200, 1300)[self.drawSize]  # depends on OS?
        #self.scroller = PsychopyScrollbar(self, wx.VERTICAL)
        self.SetVirtualSize((self.maxWidth, self.maxHeight))
        self.SetScrollRate(self.dpi / 4, self.dpi / 4)

        self.routine = routine
        self.yPositions = None
        self.yPosTop = (25, 40, 60)[self.drawSize]
        # the step in Y between each component
        self.componentStep = (25, 32, 50)[self.drawSize]
        self.timeXposStart = (150, 150, 200)[self.drawSize]
        # the left hand edge of the icons:
        _scale = (1.3, 1.5, 1.5)[self.drawSize]
        self.iconXpos = self.timeXposStart - self.iconSize * _scale
        self.timeXposEnd = self.timeXposStart + 400  # onResize() overrides

        # create a PseudoDC to record our drawing
        self.pdc = PseudoDC()
        self.pen_cache = {}
        self.brush_cache = {}
        # vars for handling mouse clicks
        self.dragid = -1
        self.lastpos = (0, 0)
        # use the ID of the drawn icon to retrieve component name:
        self.componentFromID = {}
        self.contextMenuItems = ['copy', 'edit', 'remove',
                                 'move to top', 'move up',
                                 'move down', 'move to bottom']
        # labels are only for display, and allow localization
        self.contextMenuLabels = {k: _localized[k]
                                  for k in self.contextMenuItems}
        self.contextItemFromID = {}
        self.contextIDFromItem = {}
        for item in self.contextMenuItems:
            id = wx.NewIdRef()
            self.contextItemFromID[id] = item
            self.contextIDFromItem[item] = id

        self._applyAppTheme()

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x: None)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)
        self.Bind(wx.EVT_SIZE, self.onResize)
        # crashes if drop on OSX:
        # self.SetDropTarget(FileDropTarget(builder = self.frame))

    def _applyAppTheme(self, target=None):
        """Synonymise app theme method with redraw method"""
        return self.redrawRoutine()

    def onResize(self, event):
        self.sizePix = event.GetSize()
        self.timeXposStart = (150, 150, 200)[self.drawSize]
        self.timeXposEnd = self.sizePix[0] - (60, 80, 100)[self.drawSize]
        self.redrawRoutine()  # then redraw visible

    def ConvertEventCoords(self, event):
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        return (event.GetX() + (xView * xDelta),
                event.GetY() + (yView * yDelta))

    def OffsetRect(self, r):
        """Offset the rectangle, r, to appear in the given pos in the window
        """
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        r.OffsetXY(-(xView * xDelta), -(yView * yDelta))

    def OnMouse(self, event):
        if event.LeftDown():
            x, y = self.ConvertEventCoords(event)
            icons = self.pdc.FindObjectsByBBox(x, y)
            if len(icons):
                self.editComponentProperties(
                    component=self.componentFromID[icons[0]])
        elif event.RightDown():
            x, y = self.ConvertEventCoords(event)
            icons = self.pdc.FindObjectsByBBox(x, y)
            menuPos = event.GetPosition()
            if self.app.prefs.builder['topFlow']:
                # width of components panel
                menuPos[0] += self.frame.componentButtons.GetSize()[0]
                # height of flow panel
                menuPos[1] += self.frame.flowPanel.GetSize()[1]
            if len(icons):
                self._menuComponent = self.componentFromID[icons[0]]
                self.showContextMenu(self._menuComponent, xy=menuPos)
        elif event.Dragging() or event.LeftUp():
            if self.dragid != -1:
                pass
            if event.LeftUp():
                pass
        elif event.Moving():
            try:
                x, y = self.ConvertEventCoords(event)
                id = self.pdc.FindObjectsByBBox(x, y)[0]
                component = self.componentFromID[id]
                self.frame.SetStatusText("Component: "+component.params['name'].val)
            except IndexError:
                self.frame.SetStatusText("")

    def showContextMenu(self, component, xy):
        menu = wx.Menu()
        for item in self.contextMenuItems:
            id = self.contextIDFromItem[item]
            menu.Append(id, self.contextMenuLabels[item])
            menu.Bind(wx.EVT_MENU, self.onContextSelect, id=id)
        self.frame.PopupMenu(menu, xy)
        menu.Destroy()  # destroy to avoid mem leak

    def onContextSelect(self, event):
        """Perform a given action on the component chosen
        """
        op = self.contextItemFromID[event.GetId()]
        component = self._menuComponent
        r = self.routine
        if op == 'edit':
            self.editComponentProperties(component=component)
        elif op == 'copy':
            self.copyCompon(component=component)
        elif op == 'remove':
            r.removeComponent(component)
            self.frame.addToUndoStack(
                "REMOVE `%s` from Routine" % (component.params['name'].val))
            self.frame.exp.namespace.remove(component.params['name'].val)
        elif op.startswith('move'):
            lastLoc = r.index(component)
            r.remove(component)
            if op == 'move to top':
                r.insert(0, component)
            if op == 'move up':
                r.insert(lastLoc - 1, component)
            if op == 'move down':
                r.insert(lastLoc + 1, component)
            if op == 'move to bottom':
                r.append(component)
            self.frame.addToUndoStack("MOVED `%s`" %
                                      component.params['name'].val)
        self.redrawRoutine()
        self._menuComponent = None

    def OnPaint(self, event):
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.
        dc = wx.GCDC(wx.BufferedPaintDC(self))
        # we need to clear the dc BEFORE calling PrepareDC
        bg = wx.Brush(self.GetBackgroundColour())
        dc.SetBackground(bg)
        dc.Clear()
        # use PrepareDC to set position correctly
        self.PrepareDC(dc)
        # create a clipping rect from our position and size
        # and the Update Region
        xv, yv = self.GetViewStart()
        dx, dy = self.GetScrollPixelsPerUnit()
        x, y = (xv * dx, yv * dy)
        rgn = self.GetUpdateRegion()
        rgn.Offset(x, y)
        r = rgn.GetBox()
        # draw to the dc using the calculated clipping rect
        self.pdc.DrawToDCClipped(dc, r)

    def redrawRoutine(self):
        self.pdc.Clear()  # clear the screen
        self.pdc.RemoveAll()  # clear all objects (icon buttons)

        self.SetBackgroundColour(ThemeMixin.appColors['tab_bg'])
        # work out where the component names and icons should be from name
        # lengths
        self.setFontSize(self.fontBaseSize // self.dpi, self.pdc)
        longest = 0
        w = 50
        for comp in self.routine:
            name = comp.params['name'].val
            if len(name) > longest:
                longest = len(name)
                w = self.GetFullTextExtent(name)[0]
        self.timeXpos = w + (50, 50, 90)[self.drawSize]

        # separate components according to whether they are drawn in separate
        # row
        rowComponents = []
        staticCompons = []
        for n, component in enumerate(self.routine):
            if component.type == 'Static':
                staticCompons.append(component)
            else:
                rowComponents.append(component)

        # draw static, time grid, normal (row) comp:
        yPos = self.yPosTop
        yPosBottom = yPos + len(rowComponents) * self.componentStep
        # draw any Static Components first (below the grid)
        for component in staticCompons:
            bottom = max(yPosBottom, self.GetSize()[1])
            self.drawStatic(self.pdc, component, yPos, bottom)
        self.drawTimeGrid(self.pdc, yPos, yPosBottom)
        # normal components, one per row
        for component in rowComponents:
            self.drawComponent(self.pdc, component, yPos)
            yPos += self.componentStep

        # the 50 allows space for labels below the time axis
        self.SetVirtualSize((self.maxWidth, yPos + 50))
        self.Refresh()  # refresh the visible window after drawing (OnPaint)
        #self.scroller.Resize()

    def getMaxTime(self):
        """Return the max time to be drawn in the window
        """
        maxTime, nonSlip = self.routine.getMaxTime()
        if self.routine.hasOnlyStaticComp():
            maxTime = int(maxTime) + 1.0
        return maxTime

    def drawTimeGrid(self, dc, yPosTop, yPosBottom, labelAbove=True):
        """Draws the grid of lines and labels the time axes
        """
        tMax = self.getMaxTime() * 1.1
        xScale = self.getSecsPerPixel()
        xSt = self.timeXposStart
        xEnd = self.timeXposEnd

        # dc.SetId(wx.NewIdRef())
        dc.SetPen(wx.Pen(ThemeMixin.appColors['rt_timegrid']))
        dc.SetTextForeground(wx.Colour(ThemeMixin.appColors['rt_timegrid']))
        # draw horizontal lines on top and bottom
        dc.DrawLine(x1=xSt, y1=yPosTop,
                    x2=xEnd, y2=yPosTop)
        dc.DrawLine(x1=xSt, y1=yPosBottom,
                    x2=xEnd, y2=yPosBottom)
        # draw vertical time points
        # gives roughly 1/10 the width, but in rounded to base 10 of
        # 0.1,1,10...
        unitSize = 10 ** numpy.ceil(numpy.log10(tMax * 0.8)) / 10.0
        if tMax / unitSize < 3:
            # gives units of 2 (0.2,2,20)
            unitSize = 10 ** numpy.ceil(numpy.log10(tMax * 0.8)) / 50.0
        elif tMax / unitSize < 6:
            # gives units of 5 (0.5,5,50)
            unitSize = 10 ** numpy.ceil(numpy.log10(tMax * 0.8)) / 20.0
        for lineN in range(int(numpy.floor((tMax / unitSize)))):
            # vertical line:
            dc.DrawLine(xSt + lineN * unitSize / xScale, yPosTop - 4,
                        xSt + lineN * unitSize / xScale, yPosBottom + 4)
            # label above:
            dc.DrawText('%.2g' % (lineN * unitSize), xSt + lineN *
                        unitSize / xScale - 4, yPosTop - 30)
            if yPosBottom > 300:
                # if bottom of grid is far away then draw labels here too
                dc.DrawText('%.2g' % (lineN * unitSize), xSt + lineN *
                            unitSize / xScale - 4, yPosBottom + 10)
        # add a label
        self.setFontSize(self.fontBaseSize // self.dpi, dc)
        # y is y-half height of text
        dc.DrawText('t (sec)', xEnd + 5,
                    yPosTop - self.GetFullTextExtent('t')[1] / 2.0)
        # or draw bottom labels only if scrolling is turned on, virtual size >
        # available size?
        if yPosBottom > 300:
            # if bottom of grid is far away then draw labels there too
            # y is y-half height of text
            dc.DrawText('t (sec)', xEnd + 5,
                        yPosBottom - self.GetFullTextExtent('t')[1] / 2.0)
        dc.SetTextForeground(ThemeMixin.appColors['text'])

    def setFontSize(self, size, dc):
        font = self.GetFont()
        font.SetPointSize(size)
        dc.SetFont(font)
        self.SetFont(font)

    def drawStatic(self, dc, component, yPosTop, yPosBottom):
        """draw a static (ISI) component box"""
        # set an id for the region of this component (so it can
        # act as a button). see if we created this already.
        id = None
        for key in self.componentFromID:
            if self.componentFromID[key] == component:
                id = key
        if not id:  # then create one and add to the dict
            id = wx.NewIdRef()
            self.componentFromID[id] = component
        dc.SetId(id)
        # deduce start and stop times if possible
        startTime, duration, nonSlipSafe = component.getStartAndDuration()
        # ensure static comps are clickable (even if $code start or duration)
        unknownTiming = False
        if startTime is None:
            startTime = 0
            unknownTiming = True
        if duration is None:
            duration = 0  # minimal extent ensured below
            unknownTiming = True
        # calculate rectangle for component
        xScale = self.getSecsPerPixel()

        if component.params['disabled'].val:
            dc.SetBrush(wx.Brush(ThemeMixin.appColors['rt_static_disabled']))
            dc.SetPen(wx.Pen(ThemeMixin.appColors['rt_static_disabled']))

        else:
            dc.SetBrush(wx.Brush(ThemeMixin.appColors['rt_static']))
            dc.SetPen(wx.Pen(ThemeMixin.appColors['rt_static']))

        xSt = self.timeXposStart + startTime // xScale
        w = duration // xScale + 1  # +1 b/c border alpha=0 in dc.SetPen
        w = max(min(w, 10000), 2)  # ensure 2..10000 pixels
        h = yPosBottom - yPosTop
        # name label, position:
        name = component.params['name'].val  # "ISI"
        if unknownTiming:
            # flag it as not literally represented in time, e.g., $code
            # duration
            name += ' ???'
        nameW, nameH = self.GetFullTextExtent(name)[0:2]
        x = xSt + w // 2
        staticLabelTop = (0, 50, 60)[self.drawSize]
        y = staticLabelTop - nameH * 3
        fullRect = wx.Rect(x - 20, y, nameW, nameH)
        # draw the rectangle, draw text on top:
        dc.DrawRectangle(xSt, yPosTop - nameH * 4, w, h + nameH * 5)
        dc.DrawText(name, x - nameW // 2, y)
        # update bounds to include time bar
        fullRect.Union(wx.Rect(xSt, yPosTop, w, h))
        dc.SetIdBounds(id, fullRect)

    def drawComponent(self, dc, component, yPos):
        """Draw the timing of one component on the timeline"""
        # set an id for the region of this component (so it
        # can act as a button). see if we created this already
        id = None
        for key in self.componentFromID:
            if self.componentFromID[key] == component:
                id = key
        if not id:  # then create one and add to the dict
            id = wx.NewIdRef()
            self.componentFromID[id] = component
        dc.SetId(id)

        iconYOffset = (6, 6, 0)[self.drawSize]
        icons = self.app.iconCache

        thisIcon = icons.getComponentBitmap(component, self.iconSize)
        dc.DrawBitmap(thisIcon, self.iconXpos, yPos + iconYOffset, True)
        fullRect = wx.Rect(self.iconXpos, yPos,
                           thisIcon.GetWidth(), thisIcon.GetHeight())

        self.setFontSize(self.fontBaseSize // self.dpi, dc)

        name = component.params['name'].val
        # get size based on text
        w, h = self.GetFullTextExtent(name)[0:2]
        if w > self.iconXpos - self.dpi/5:
            # If width is greater than space available, split word at point calculated by average letter width
            maxLen = int(
                (self.iconXpos - self.GetFullTextExtent("...")[0] - self.dpi/5)
                / (w/len(name))
            )
            splitAt = int(maxLen/2)
            name = name[:splitAt] + "..." + name[-splitAt:]
            w = self.iconXpos - self.dpi/5
        # draw text
        # + x position of icon (left side)
        # - half width of icon (including whitespace around it)
        # - FULL width of text
        # + slight adjustment for whitespace
        x = self.iconXpos - thisIcon.GetWidth()/2 - w + thisIcon.GetWidth()/3
        _adjust = (5, 5, -2)[self.drawSize]
        y = yPos + thisIcon.GetHeight() // 2 - h // 2 + _adjust
        dc.DrawText(name, x, y)
        fullRect.Union(wx.Rect(x - 20, y, w, h))

        # deduce start and stop times if possible
        startTime, duration, nonSlipSafe = component.getStartAndDuration()
        # draw entries on timeline (if they have some time definition)
        if startTime is not None and duration is not None:
            # then we can draw a sensible time bar!
            dc.SetPen(wx.Pen(ThemeMixin.appColors['rt_comp'],
                             style=wx.TRANSPARENT))

            if component.params['disabled'].val:
                # Grey bar if comp is disabled
                dc.SetBrush(wx.Brush(ThemeMixin.appColors['rt_comp_disabled']))
                dc.DrawBitmap(thisIcon.ConvertToDisabled(), self.iconXpos, yPos + iconYOffset, True)
            elif 'forceEndRoutine' in component.params \
                    or 'forceEndRoutineOnPress' in component.params:
                if any(component.params[key].val
                       for key in ['forceEndRoutine', 'forceEndRoutineOnPress']
                       if key in component.params):
                    # Orange bar if component has forceEndRoutine or forceEndRoutineOnPress and either are true
                    dc.SetBrush(wx.Brush(ThemeMixin.appColors['rt_comp_force']))
                else:
                    # Blue bar if component has forceEndRoutine or forceEndRoutineOnPress but none are true
                    dc.SetBrush(wx.Brush(ThemeMixin.appColors['rt_comp']))
                dc.DrawBitmap(thisIcon, self.iconXpos, yPos + iconYOffset, True)
            else:
                # Blue bar otherwise
                dc.SetBrush(wx.Brush(ThemeMixin.appColors['rt_comp']))
                dc.DrawBitmap(thisIcon, self.iconXpos, yPos + iconYOffset, True)

            xScale = self.getSecsPerPixel()
            yOffset = (3.5, 3.5, 0.5)[self.drawSize]
            h = self.componentStep // (4, 3.25, 2.5)[self.drawSize]
            xSt = self.timeXposStart + startTime // xScale
            w = duration // xScale + 1
            if w > 10000:
                w = 10000  # limit width to 10000 pixels!
            if w < 2:
                w = 2  # make sure at least one pixel shows
            dc.DrawRectangle(xSt, y + yOffset, w, h)
            # update bounds to include time bar
            fullRect.Union(wx.Rect(xSt, y + yOffset, w, h))
        dc.SetIdBounds(id, fullRect)

    def copyCompon(self, event=None, component=None):
        """This is easy - just take a copy of the component into memory
        """
        self.app.copiedCompon = copy.deepcopy(component)

    def pasteCompon(self, event=None, component=None):
        if not self.app.copiedCompon:
            return -1  # not possible to paste if nothing copied
        exp = self.frame.exp
        origName = self.app.copiedCompon.params['name'].val
        defaultName = exp.namespace.makeValid(origName)
        msg = _translate('New name for copy of "%(copied)s"?  [%(default)s]')
        vals = {'copied': origName, 'default': defaultName}
        message = msg % vals
        dlg = wx.TextEntryDialog(self, message=message,
                                 caption=_translate('Paste Component'))
        if dlg.ShowModal() == wx.ID_OK:
            newName = dlg.GetValue()
            newCompon = copy.deepcopy(self.app.copiedCompon)
            if not newName:
                newName = defaultName
            newName = exp.namespace.makeValid(newName)
            newCompon.params['name'].val = newName
            if 'name' in dir(newCompon):
                newCompon.name = newName
            self.routine.addComponent(newCompon)
            self.frame.exp.namespace.user.append(newName)
            # could do redrawRoutines but would be slower?
            self.redrawRoutine()
            self.frame.addToUndoStack("PASTE Component `%s`" % newName)
        dlg.Destroy()

    def editComponentProperties(self, event=None, component=None):
        # we got here from a wx.button press (rather than our own drawn icons)
        if event:
            componentName = event.EventObject.GetName()
            component = self.routine.getComponentFromName(componentName)
        # does this component have a help page?
        if hasattr(component, 'url'):
            helpUrl = component.url
        else:
            helpUrl = None
        old_name = component.params['name'].val
        old_disabled = component.params['disabled'].val
        # check current timing settings of component (if it changes we
        # need to update views)
        initialTimings = component.getStartAndDuration()
        if 'forceEndRoutine' in component.params \
                or 'forceEndRoutineOnPress' in component.params:
            # If component can force end routine, check if it did before
            initialForce = [component.params[key].val
                            for key in ['forceEndRoutine', 'forceEndRoutineOnPress']
                            if key in component.params]
        else:
            initialForce = False
        # create the dialog
        if hasattr(component, 'type') and component.type.lower() == 'code':
            _Dlg = DlgCodeComponentProperties
        else:
            _Dlg = DlgComponentProperties
        dlg = _Dlg(frame=self.frame,
                   title=component.params['name'].val + ' Properties',
                   params=component.params,
                   order=component.order, helpUrl=helpUrl, editing=True,
                   depends=component.depends)
        if dlg.OK:
            # Redraw if force end routine has changed
            if 'forceEndRoutine' in component.params \
                    or 'forceEndRoutineOnPress' in component.params:
                newForce = [component.params[key].val
                            for key in ['forceEndRoutine', 'forceEndRoutineOnPress']
                            if key in component.params]
                if initialForce != newForce:
                    self.redrawRoutine()  # need to refresh timings section
                    self.Refresh()  # then redraw visible
                    self.frame.flowPanel.draw()
            # Redraw if timings have changed
            if component.getStartAndDuration() != initialTimings:
                self.redrawRoutine()  # need to refresh timings section
                self.Refresh()  # then redraw visible
                self.frame.flowPanel.draw()
                # self.frame.flowPanel.Refresh()
            elif component.params['name'].val != old_name:
                self.redrawRoutine()  # need to refresh name
            elif component.params['disabled'].val != old_disabled:
                self.redrawRoutine()  # need to refresh color
            self.frame.exp.namespace.remove(old_name)
            self.frame.exp.namespace.add(component.params['name'].val)
            self.frame.addToUndoStack("EDIT `%s`" %
                                      component.params['name'].val)

    def getSecsPerPixel(self):
        pixels = float(self.timeXposEnd - self.timeXposStart)
        return self.getMaxTime() / pixels


class ComponentsPanel(scrolledpanel.ScrolledPanel):

    def __init__(self, frame, id=-1):
        """A panel that displays available components.
        """
        self.frame = frame
        self.app = frame.app
        self.dpi = self.app.dpi
        panelWidth = 3 * 48 + 50
        scrolledpanel.ScrolledPanel.__init__(self,
                                             frame,
                                             id,
                                             size=(panelWidth, 10 * self.dpi),
                                             style=wx.BORDER_NONE)
        self._maxBtnWidth = 0  # will store width of widest button
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.componentButtons = []
        self.components = experiment.getAllComponents(
            self.app.prefs.builder['componentsFolders'])
        categories = ['Favorites']
        categories.extend(components.getAllCategories(
            self.app.prefs.builder['componentsFolders']))
        # get rid of hidden components
        for hiddenComp in self.frame.prefs['hiddenComponents']:
            if hiddenComp in self.components:
                del self.components[hiddenComp]
        # also remove settings - that's in toolbar not components panel
        del self.components['SettingsComponent']
        # get favorites
        self.favorites = FavoriteComponents(componentsPanel=self)
        # create labels and sizers for each category
        self.componentFromID = {}
        self.panels = {}
        # to keep track of the objects (sections and section labels)
        # within the main sizer
        self.sizerList = []

        for categ in categories:
            if categ in _localized:
                label = _localized[categ]
            else:
                label = categ
            _style = platebtn.PB_STYLE_DROPARROW | platebtn.PB_STYLE_SQUARE
            sectionBtn = PsychopyPlateBtn(self, -1, label, style=_style, name=categ)
            # Link to onclick functions
            sectionBtn.Bind(wx.EVT_LEFT_DOWN, self.onSectionBtn)
            sectionBtn.Bind(wx.EVT_RIGHT_DOWN, self.onSectionBtn)
            # Set button background and link to onhover functions
            #sectionBtn.Bind(wx.EVT_ENTER_WINDOW, self.onHover)
            #sectionBtn.Bind(wx.EVT_LEAVE_WINDOW, self.offHover)
            self.panels[categ] = wx.FlexGridSizer(cols=1)
            self.sizer.Add(sectionBtn, flag=wx.EXPAND)
            self.sizerList.append(sectionBtn)
            self.sizer.Add(self.panels[categ], flag=wx.ALIGN_CENTER)
            self.sizerList.append(self.panels[categ])
        maxWidth = self.makeComponentButtons()
        self._rightClicked = None
        # start all except for Favorites collapsed
        for section in categories[1:]:
            self.toggleSection(self.panels[section])

        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)
        self.SetupScrolling()
        # double buffered better rendering except if retina
        self.SetDoubleBuffered(self.frame.IsDoubleBuffered())
        self._applyAppTheme()  # bitmaps only just loaded

    def _applyAppTheme(self, target=None):
        cs = ThemeMixin.appColors
        # Style component panel
        self.SetForegroundColour(cs['text'])
        self.SetBackgroundColour(cs['panel_bg'])
        # Style component buttons
        for btn in self.componentButtons:
            btn.SetForegroundColour(cs['text'])
            btn.SetBackgroundColour(cs['panel_bg'])
            # then apply to all children as well
        for c in self.GetChildren():
            if hasattr(c, '_applyAppTheme'):
                # if the object understands themes then request that
                c._applyAppTheme()
        self.Refresh()
        self.Update()

    def on_resize(self, event):
        cols = self.GetClientSize()[0] // self._maxBtnWidth
        for category in list(self.panels.values()):
            category.SetCols(max(1, cols))

    def makeFavoriteButtons(self):
        # add a copy of each favorite to that panel first
        for thisName in self.favorites.getFavorites():
            self.addComponentButton(thisName, self.panels['Favorites'])

    def makeComponentButtons(self):
        """Make all the components buttons, including favorites
        """
        self.makeFavoriteButtons()
        # then add another copy for each category that the component itself
        # lists
        componentNames = list(self.components.keys())
        componentNames.sort()
        for thisName in componentNames:
            thisComp = self.components[thisName]
            # NB thisComp is a class - we can't use its methods/attribs until
            # it is an instance
            for category in thisComp.categories:
                panel = self.panels[category]
                self.addComponentButton(thisName, panel)

    def addComponentButton(self, name, panel):
        """Create a component button and add it to a specific panel's sizer
        """
        iconCache = self.app.iconCache
        # get a shorter name too (without "Component")
        shortName = name
        for redundant in ['component', 'Component', "ButtonBox"]:
            shortName = shortName.replace(redundant, "")
        # Convert from CamelCase to Title Case for button label
        label = ""
        for i, c in enumerate(shortName):
            if c.isupper() and i > 0:
                label += "\n"
            label += c
        # set size
        size = 48
        # get tooltip
        if name in components.tooltips:
            thisTip = components.tooltips[name]
        else:
            thisTip = shortName
        btn = iconCache.getComponentButton(
                parent=self,
                name=name,
                label=label,
                size=size,
                tip=thisTip,
        )
        # btn will be none if a favorite is not found (e.g. user has multiple
        # versions of psychopy installed
        if btn is None:
            return
        # then set up positioning etc
        btn.SetBitmapPosition(wx.TOP)
        self.componentFromID[btn.GetId()] = name
        # use btn.bind instead of self.Bind in oder to trap event here
        btn.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)
        self.Bind(wx.EVT_BUTTON, self.onClick, btn)
        # ,wx.EXPAND|wx.ALIGN_CENTER )
        panel.Add(btn, proportion=0, flag=wx.ALIGN_RIGHT)
        self._maxBtnWidth = max(btn.GetSize()[0], self._maxBtnWidth)
        self.componentButtons.append(btn)

    def onSectionBtn(self, evt):
        if hasattr(evt, 'GetString'):
            buttons = self.panels[evt.GetString()]
        else:
            btn = evt.GetEventObject()
            buttons = self.panels[btn.GetName()]
        self.toggleSection(buttons)

    def toggleSection(self, section):
        ii = self.sizerList.index(section)
        self.sizer.Show(ii, not self.sizer.IsShown(ii))  # ie toggle this item
        self.sizer.Layout()
        self.SetupScrolling()

    def getIndexInSizer(self, obj, sizer):
        """Find index of an item within a sizer (to see if it's there
        or to toggle visibility)
        WX sizers don't (as of v2.8.11) have a way to find the index of
        their contents. This method helps get around that.
        """
        # if the obj is itself a sizer (e.g. within the main sizer then
        # we can't even use sizer.Children (as far as I can work out)
        # so we keep a list to track the contents.
        # for the main sizer we kept track of everything with a list:
        if sizer == self.sizer:
            return self.sizerList.index(obj)
        index = None
        for ii, child in enumerate(sizer.Children):
            if child.GetWindow() == obj:
                index = ii
                break
        return index

    def onRightClick(self, evt):
        """
        Defines rightclick behavior within builder view's
        components panel
        """
        btn = evt.GetEventObject()
        self._rightClicked = btn
        index = self.getIndexInSizer(btn, self.panels['Favorites'])
        if index is None:
            # not currently in favs
            msg = "Add to favorites"
            clickFunc = self.onAddToFavorites
        else:
            # is currently in favs
            msg = "Remove from favorites"
            clickFunc = self.onRemFromFavorites
        menu = wx.Menu()
        id = wx.NewIdRef()
        menu.Append(id, _localized[msg])
        menu.Bind(wx.EVT_MENU, clickFunc, id=id)
        # where to put the context menu
        x, y = evt.GetPosition()  # this is position relative to object
        xBtn, yBtn = evt.GetEventObject().GetPosition()
        self.PopupMenu(menu, (x + xBtn, y + yBtn))
        menu.Destroy()  # destroy to avoid mem leak

    def onClick(self, evt, timeout=None):
        """
        Defines left-click behavior for builder views components panel
        :param: evt can be a wx.Event OR a component class name (MouseComponent)
        """
        # get name of current routine
        currRoutinePage = self.frame.routinePanel.getCurrentPage()
        if not currRoutinePage:
            msg = _translate("Create a routine (Experiment menu) "
                             "before adding components")
            dialogs.MessageDialog(self, msg, type='Info',
                                  title=_translate('Error')).ShowModal()
            return False
        currRoutine = self.frame.routinePanel.getCurrentRoutine()
        # get component name
        if hasattr(evt, "GetId"):
            newClassStr = self.componentFromID[evt.GetId()]
        else:
            newClassStr = evt
        newCompClass = self.components[newClassStr]
        newComp = newCompClass(parentName=currRoutine.name,
                               exp=self.frame.exp)
        # does this component have a help page?
        if hasattr(newComp, 'url'):
            helpUrl = newComp.url
        else:
            helpUrl = None
        # create component template
        if newClassStr == 'CodeComponent':
            _Dlg = DlgCodeComponentProperties
        else:
            _Dlg = DlgComponentProperties
        dlg = _Dlg(frame=self.frame,
                   title='{} Properties'.format(newComp.params['name']),
                   params=newComp.params, order=newComp.order,
                   helpUrl=helpUrl,
                   depends=newComp.depends,
                   timeout=timeout)

        compName = newComp.params['name']
        if dlg.OK:
            currRoutine.addComponent(newComp)  # add to the actual routing
            namespace = self.frame.exp.namespace
            newComp.params['name'].val = namespace.makeValid(
                newComp.params['name'].val)
            namespace.add(newComp.params['name'].val)
            # update the routine's view with the new component too
            currRoutinePage.redrawRoutine()
            self.frame.addToUndoStack(
                "ADD `%s` to `%s`" % (compName, currRoutine.name))
            wasNotInFavs = (newClassStr not in self.favorites.getFavorites())
            self.favorites.promoteComponent(newClassStr, 1)
            # was that promotion enough to be a favorite?
            if wasNotInFavs and newClassStr in self.favorites.getFavorites():
                self.addComponentButton(newClassStr, self.panels['Favorites'])
                self.sizer.Layout()
        return True

    def onAddToFavorites(self, evt=None, btn=None):
        """Defines Add To Favorites Menu Behavior"""
        if btn is None:
            btn = self._rightClicked
        if btn.Name not in self.favorites.getFavorites():
            # check we aren't duplicating
            self.favorites.makeFavorite(btn.Name)
            self.addComponentButton(btn.Name, self.panels['Favorites'])
        self.sizer.Layout()
        self._rightClicked = None

    def onRemFromFavorites(self, evt=None, btn=None):
        """Defines Remove from Favorites Menu Behavior"""
        if btn is None:
            btn = self._rightClicked
        index = self.getIndexInSizer(btn, self.panels['Favorites'])
        if index is None:
            pass
        else:
            self.favorites.setLevel(btn.Name, -100)
            btn.Destroy()
        self.sizer.Layout()
        self._rightClicked = None

    def onHover(self, evt):
        cs = ThemeMixin.appColors
        btn = evt.GetEventObject()
        btn.SetBackgroundColour(cs['bmpbutton_bg_hover'])
        btn.SetForegroundColour(cs['bmpbutton_fg_hover'])

    def offHover(self, evt):
        cs = ThemeMixin.appColors
        btn = evt.GetEventObject()
        btn.SetBackgroundColour(cs['panel_bg'])
        btn.SetForegroundColour(cs['text'])


class FavoriteComponents(object):
    """Defines the Favorite Components Object class, meant for dealing with
    the user's frequently accessed components"""

    def __init__(self, componentsPanel, threshold=20, neutral=0):
        super(FavoriteComponents, self).__init__()
        self.threshold = 20
        self.neutral = 0
        self.panel = componentsPanel
        self.frame = componentsPanel.frame
        self.app = self.frame.app
        self.prefs = self.app.prefs
        self.currentLevels = self.prefs.appDataCfg['builder']['favComponents']
        self.setDefaults()

    def setDefaults(self):
        """Defines Default Favorite Components"""
        # set those that are favorites by default
        for comp in ('ImageComponent', 'KeyboardComponent',
                     'SoundComponent', 'TextComponent',
                     'MouseComponent', 'SliderComponent',
                     ):
            if comp not in self.currentLevels or self.currentLevels[comp] != 0:
                self.currentLevels[comp] = self.threshold
        for comp in self.panel.components:
            if comp not in self.currentLevels:
                self.currentLevels[comp] = self.neutral

    def makeFavorite(self, compName):
        """Set the value of this component to an arbitrary high value (10000)
        """
        self.currentLevels[compName] = 10000

    def promoteComponent(self, compName, value=1):
        """Promote this component by a certain value (negative to demote)
        """
        self.currentLevels[compName] += value

    def setLevel(self, compName, value=0):
        """Set the level to neutral (0) favourite (20?) or banned (-1000?)
        """
        self.currentLevels[compName] = value

    def getFavorites(self):
        """Returns a list of favorite components. Each must have level greater
        than the threshold and there will be not more than
        max length prefs['builder']['maxFavorites']
        """
        sortedVals = sorted(list(self.currentLevels.items()),
                            key=lambda x: x[1], reverse=True)
        favorites = []
        maxFav = self.prefs.builder['maxFavorites']
        for name, level in sortedVals:
            # this has been explicitly requested (or REALLY liked!)
            if level >= 10000:
                favorites.append(name)
            elif level >= self.threshold and len(favorites) < maxFav:
                favorites.append(name)
            else:
                # either we've run out of levels>10000 or exceeded maxFavs or
                # run out of level >= thresh
                break
        return favorites


class ReadmeFrame(wx.Frame):
    """Defines construction of the Readme Frame"""

    def __init__(self, parent):
        """
        A frame for presenting/loading/saving readme files
        """
        self.parent = parent
        title = "%s readme" % (parent.exp.name)
        self._fileLastModTime = None
        pos = wx.Point(parent.Position[0] + 80, parent.Position[1] + 80)
        _style = wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT
        wx.Frame.__init__(self, parent, title=title,
                          size=(600, 500), pos=pos, style=_style)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Hide()
        self.makeMenus()
        self.ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE)

    def onClose(self, evt=None):
        """
        Defines behavior on close of the Readme Frame
        """
        self.parent.readmeFrame = None
        self.Destroy()

    def makeMenus(self):
        """Produces menus for the Readme Frame"""

        # ---Menus---#000000#FFFFFF-------------------------------------------
        menuBar = wx.MenuBar()
        # ---_file---#000000#FFFFFF-------------------------------------------
        self.fileMenu = wx.Menu()
        menuBar.Append(self.fileMenu, _translate('&File'))
        menu = self.fileMenu
        keys = self.parent.app.keys
        menu.Append(wx.ID_SAVE, _translate("&Save\t%s") % keys['save'])
        menu.Append(wx.ID_CLOSE,
                    _translate("&Close readme\t%s") % keys['close'])
        item = menu.Append(-1,
                           _translate("&Toggle readme\t%s") % keys[
                               'toggleReadme'],
                           _translate("Toggle Readme"))
        self.Bind(wx.EVT_MENU, self.toggleVisible, item)
        self.Bind(wx.EVT_MENU, self.fileSave, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.toggleVisible, id=wx.ID_CLOSE)
        self.SetMenuBar(menuBar)

    def setFile(self, filename):
        """Sets the readme file found with current builder experiment"""
        self.filename = filename
        self.expName = self.parent.exp.getExpName()
        # check we can read
        if filename is None:  # check if we can write to the directory
            return False
        elif not os.path.exists(filename):
            self.filename = None
            return False
        elif not os.access(filename, os.R_OK):
            msg = "Found readme file (%s) no read permissions"
            logging.warning(msg % filename)
            return False
        # attempt to open
        try:
            f = codecs.open(filename, 'r', 'utf-8-sig')
        except IOError as err:
            msg = ("Found readme file for %s and appear to have"
                   " permissions, but can't open")
            logging.warning(msg % self.expName)
            logging.warning(err)
            return False
            # attempt to read
        try:
            readmeText = f.read().replace("\r\n", "\n")
        except Exception:
            msg = ("Opened readme file for %s it but failed to read it "
                   "(not text/unicode?)")
            logging.error(msg % self.expName)
            return False
        f.close()
        self._fileLastModTime = os.path.getmtime(filename)
        self.ctrl.SetValue(readmeText)
        self.SetTitle("%s readme (%s)" % (self.expName, filename))

    def fileSave(self, evt=None):
        """Defines save behavior for readme frame"""
        mtime = os.path.getmtime(self.filename)
        if self._fileLastModTime and mtime > self._fileLastModTime:
            logging.warning(
                'readme file has been changed by another programme?')
        txt = self.ctrl.GetValue()
        with codecs.open(self.filename, 'w', 'utf-8-sig') as f:
            f.write(txt)

    def toggleVisible(self, evt=None):
        """Defines visibility toggle for readme frame"""
        if self.IsShown():
            self.Hide()
        else:
            self.Show()


class ExportFileDialog(wx.Dialog):
    def __init__(self, parent, ID, title, size=wx.DefaultSize,
                 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
                 filePath=None, exp=None):
        wx.Dialog.__init__(self, parent, ID, title,
                           size=size, pos=pos, style=style)
        # Now continue with the normal construction of the dialog
        # contents
        self.exp = exp
        sizer = wx.BoxSizer(wx.VERTICAL)
        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, wx.ID_ANY, _translate("Filepath:"))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        if len(filePath) > 70:
            filePath = filePath[:20] + "....." + filePath[-40:]
        self.filePath = wx.StaticText(self, wx.ID_ANY, filePath, size=(500, -1))
        box.Add(self.filePath, 1, wx.ALIGN_CENTRE | wx.ALL, 5)

        sizer.Add(box, 0, wx.GROW | wx.ALL, 5)

        # Set save on export HTML choice
        box = wx.BoxSizer(wx.HORIZONTAL)
        choices = ['on Save', 'on Sync', 'manually']
        exportLabel = _translate("Select 'manually' to receive this alert when exporting HTML.\n"
                                 "Click 'OK' to export HTML, or click 'Cancel' to return.")
        self.exportOnSave = wx.Choice(self, wx.ID_ANY,
                                      size=wx.DefaultSize,
                                      choices=choices)
        self.exportOnSave.SetSelection(choices.index(self.exp.settings.params['exportHTML']))
        self.exportText = wx.StaticText(self, wx.ID_ANY, exportLabel)
        self.exportOnSave.SetHelpText(exportLabel)
        box.Add(self.exportOnSave, .5, wx.ALIGN_CENTRE | wx.ALL, 5)
        box.Add(self.exportText, 1, wx.ALIGN_CENTRE | wx.ALL, 5)

        sizer.Add(box, 0, wx.GROW | wx.ALL, 5)

        line = wx.StaticLine(self, wx.ID_ANY, size=(20, -1),
                             style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0,
                  wx.GROW | wx.RIGHT | wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()

        btn = wx.Button(self, wx.ID_OK)
        btn.SetHelpText("The OK button completes the dialog")
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetHelpText("The Cancel button cancels the dialog. (Crazy, huh?)")
        btnsizer.AddButton(btn)

        sizer.Add(btnsizer, 0, wx.ALL, 5)

        self.SetSizerAndFit(sizer)


class FlowPanel(wx.ScrolledWindow):

    def __init__(self, frame, id=-1):
        """A panel that shows how the routines will fit together
        """
        self.frame = frame
        self.app = frame.app
        self.dpi = self.app.dpi
        wx.ScrolledWindow.__init__(self, frame, id, (0, 0),
                                   size=wx.Size(8 * self.dpi, 3 * self.dpi),
                                   style=wx.HSCROLL | wx.VSCROLL | wx.BORDER_NONE)
        self.needUpdate = True
        self.maxWidth = 50 * self.dpi
        self.maxHeight = 2 * self.dpi
        self.mousePos = None
        # if we're adding a loop or routine then add spots to timeline
        # self.drawNearestRoutinePoint = True
        # self.drawNearestLoopPoint = False
        # lists the x-vals of points to draw, eg loop locations:
        self.pointsToDraw = []
        # for flowSize, showLoopInfoInFlow:
        self.appData = self.app.prefs.appData

        # self.SetAutoLayout(True)
        self.SetScrollRate(self.dpi / 4, self.dpi / 4)

        # create a PseudoDC to record our drawing
        self.pdc = PseudoDC()
        if parse_version(wx.__version__) < parse_version('4.0.0a1'):
            self.pdc.DrawRoundedRectangle = self.pdc.DrawRoundedRectangleRect
        self.pen_cache = {}
        self.brush_cache = {}
        # vars for handling mouse clicks
        self.hitradius = 5
        self.dragid = -1
        self.entryPointPosList = []
        self.entryPointIDlist = []
        self.gapsExcluded = []
        # mode can also be 'loopPoint1','loopPoint2','routinePoint'
        self.mode = 'normal'
        self.insertingRoutine = ""

        # for the context menu use the ID of the drawn icon to retrieve
        # the component (loop or routine)
        self.componentFromID = {}
        self.contextMenuLabels = {
            'remove': _translate('remove'),
            'rename': _translate('rename')}
        self.contextMenuItems = ['remove', 'rename']
        self.contextItemFromID = {}
        self.contextIDFromItem = {}
        for item in self.contextMenuItems:
            id = wx.NewIdRef()
            self.contextItemFromID[id] = item
            self.contextIDFromItem[item] = id

        # self.btnInsertRoutine = wx.Button(self,-1,
        #                                  'Insert Routine', pos=(10,10))
        # self.btnInsertLoop = wx.Button(self,-1,'Insert Loop', pos=(10,30))
        labelRoutine = _translate('Insert Routine ')
        labelLoop = _translate('Insert Loop     ')
        btnHeight = 50
        # Create add routine button
        self.btnInsertRoutine = PsychopyPlateBtn(
            self, -1, labelRoutine, pos=(10, 10), size=(120, btnHeight),
            style=platebtn.PB_STYLE_SQUARE
        )
        # Create add loop button
        self.btnInsertLoop = PsychopyPlateBtn(
            self, -1, labelLoop, pos=(10, btnHeight+20),
            size=(120, btnHeight),
            style=platebtn.PB_STYLE_SQUARE
        )  # spaces give size for CANCEL

        # use self.appData['flowSize'] to index a tuple to get a specific
        # value, eg: (4,6,8)[self.appData['flowSize']]
        self.flowMaxSize = 2  # upper limit on increaseSize

        # bind events
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)
        self.Bind(wx.EVT_BUTTON, self.onInsertRoutine, self.btnInsertRoutine)
        self.Bind(wx.EVT_BUTTON, self.setLoopPoint1, self.btnInsertLoop)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        idClear = wx.NewIdRef()
        self.Bind(wx.EVT_MENU, self.clearMode, id=idClear)
        aTable = wx.AcceleratorTable([
            (wx.ACCEL_NORMAL, wx.WXK_ESCAPE, idClear)
        ])
        self.SetAcceleratorTable(aTable)

        # double buffered better rendering except if retina
        self.SetDoubleBuffered(self.frame.IsDoubleBuffered())

        self._applyAppTheme()

    def _applyAppTheme(self, target=None):
        """Apply any changes which have been made to the theme since panel was last loaded"""
        cs = ThemeMixin.appColors
        # Style loop/routine buttons
        self.btnInsertLoop.SetBackgroundColour(cs['frame_bg'])
        self.btnInsertLoop.SetForegroundColour(cs['text'])
        self.btnInsertLoop.Update()
        self.btnInsertRoutine.SetBackgroundColour(cs['frame_bg'])
        self.btnInsertRoutine.SetForegroundColour(cs['text'])
        self.btnInsertRoutine.Update()
        # Set background
        self.SetBackgroundColour(cs['panel_bg'])

        self.draw()

    def clearMode(self, event=None):
        """If we were in middle of doing something (like inserting routine)
        then end it, allowing user to cancel
        """
        self.mode = 'normal'
        self.insertingRoutine = None
        for id in self.entryPointIDlist:
            self.pdc.RemoveId(id)
        self.entryPointPosList = []
        self.entryPointIDlist = []
        self.gapsExcluded = []
        self.draw()
        self.frame.SetStatusText("")
        self.btnInsertRoutine.SetLabel(_translate('Insert Routine'))
        self.btnInsertRoutine.Update()
        self.btnInsertLoop.SetLabel(_translate('Insert Loop'))
        self.btnInsertRoutine.Update()

    def ConvertEventCoords(self, event):
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        return (event.GetX() + (xView * xDelta),
                event.GetY() + (yView * yDelta))

    def OffsetRect(self, r):
        """Offset the rectangle, r, to appear in the given position
        in the window
        """
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        r.Offset((-(xView * xDelta), -(yView * yDelta)))

    def onInsertRoutine(self, evt):
        """For when the insert Routine button is pressed - bring up
        dialog and present insertion point on flow line.
        see self.insertRoutine() for further info
        """
        if self.mode.startswith('loopPoint'):
            self.clearMode()
        elif self.mode == 'routine':
            # clicked again with label now being "Cancel..."
            self.clearMode()
            return
        self.frame.SetStatusText(_translate(
            "Select a Routine to insert (Esc to exit)"))
        menu = wx.Menu()
        self.routinesFromID = {}
        id = wx.NewIdRef()
        menu.Append(id, '(new)')
        self.routinesFromID[id] = '(new)'
        menu.Bind(wx.EVT_MENU, self.insertNewRoutine, id=id)
        for routine in self.frame.exp.routines:
            id = wx.NewIdRef()
            menu.Append(id, routine)
            self.routinesFromID[id] = routine
            menu.Bind(wx.EVT_MENU, self.onInsertRoutineSelect, id=id)
        btnPos = self.btnInsertRoutine.GetRect()
        menuPos = (btnPos[0], btnPos[1] + btnPos[3])
        self.PopupMenu(menu, menuPos)
        menu.Bind(wx.EVT_MENU_CLOSE, self.clearMode)
        menu.Destroy()  # destroy to avoid mem leak

    def insertNewRoutine(self, event):
        """selecting (new) is a short-cut for:
        make new routine, insert it into the flow
        """
        newRoutine = self.frame.routinePanel.createNewRoutine(returnName=True)
        if newRoutine:
            self.routinesFromID[event.GetId()] = newRoutine
            self.onInsertRoutineSelect(event)
        else:
            self.clearMode()

    def onInsertRoutineSelect(self, event):
        """User has selected a routine to be entered so bring up the
        entrypoint marker and await mouse button press.
        see self.insertRoutine() for further info
        """
        self.mode = 'routine'
        self.btnInsertRoutine.SetLabel(_translate('CANCEL Insert'))
        self.frame.SetStatusText(_translate(
            'Click where you want to insert the Routine, or CANCEL insert.'))
        self.insertingRoutine = self.routinesFromID[event.GetId()]
        x = self.getNearestGapPoint(0)
        self.drawEntryPoints([x])

    def insertRoutine(self, ii):
        """Insert a routine into the Flow knowing its name and location

        onInsertRoutine() the button has been pressed so present menu
        onInsertRoutineSelect() user selected the name so present entry points
        OnMouse() user has selected a point on the timeline to insert entry

        """
        rtn = self.frame.exp.routines[self.insertingRoutine]
        self.frame.exp.flow.addRoutine(rtn, ii)
        self.frame.addToUndoStack("ADD Routine `%s`" % rtn.name)
        # reset flow drawing (remove entry point)
        self.clearMode()

    def setLoopPoint1(self, evt=None):
        """Someone pushed the insert loop button.
        Fetch the dialog
        """
        if self.mode == 'routine':
            self.clearMode()
        # clicked again, label is "Cancel..."
        elif self.mode.startswith('loopPoint'):
            self.clearMode()
            return
        self.btnInsertLoop.SetLabel(_translate('CANCEL insert'))
        self.mode = 'loopPoint1'
        self.frame.SetStatusText(_translate(
            'Click where you want the loop to start/end, or CANCEL insert.'))
        x = self.getNearestGapPoint(0)
        self.drawEntryPoints([x])

    def setLoopPoint2(self, evt=None):
        """We have the location of the first point, waiting to get the second
        """
        self.mode = 'loopPoint2'
        self.frame.SetStatusText(_translate(
            'Click the other end for the loop'))
        thisPos = self.entryPointPosList[0]
        self.gapsExcluded = [thisPos]
        self.gapsExcluded.extend(self.getGapPointsCrossingStreams(thisPos))
        # is there more than one available point
        diff = wx.GetMousePosition()[0] - self.GetScreenPosition()[0]
        x = self.getNearestGapPoint(diff, exclude=self.gapsExcluded)
        self.drawEntryPoints([self.entryPointPosList[0], x])
        nAvailableGaps = len(self.gapMidPoints) - len(self.gapsExcluded)
        if nAvailableGaps == 1:
            self.insertLoop()  # there's only one place - use it

    def insertLoop(self, evt=None):
        # bring up listbox to choose the routine to add, and / or a new one
        loopDlg = DlgLoopProperties(frame=self.frame,
                                    helpUrl=self.app.urls['builder.loops'])
        startII = self.gapMidPoints.index(min(self.entryPointPosList))
        endII = self.gapMidPoints.index(max(self.entryPointPosList))
        if loopDlg.OK:
            handler = loopDlg.currentHandler
            self.frame.exp.flow.addLoop(handler,
                                        startPos=startII, endPos=endII)
            action = "ADD Loop `%s` to Flow" % handler.params['name'].val
            self.frame.addToUndoStack(action)
        self.clearMode()
        self.draw()

    def increaseSize(self, event=None):
        if self.appData['flowSize'] == self.flowMaxSize:
            self.appData['showLoopInfoInFlow'] = True
        self.appData['flowSize'] = min(
            self.flowMaxSize, self.appData['flowSize'] + 1)
        self.clearMode()  # redraws

    def decreaseSize(self, event=None):
        if self.appData['flowSize'] == 0:
            self.appData['showLoopInfoInFlow'] = False
        self.appData['flowSize'] = max(0, self.appData['flowSize'] - 1)
        self.clearMode()  # redraws

    def editLoopProperties(self, event=None, loop=None):
        # add routine points to the timeline
        self.setDrawPoints('loops')
        self.draw()
        if 'conditions' in loop.params:
            condOrig = loop.params['conditions'].val
            condFileOrig = loop.params['conditionsFile'].val
        title = loop.params['name'].val + ' Properties'
        loopDlg = DlgLoopProperties(frame=self.frame,
                                    helpUrl=self.app.urls['builder.loops'],
                                    title=title, loop=loop)
        if loopDlg.OK:
            prevLoop = loop
            if loopDlg.params['loopType'].val == 'staircase':
                loop = loopDlg.stairHandler
            elif loopDlg.params['loopType'].val == 'interleaved staircases':
                loop = loopDlg.multiStairHandler
            else:
                # ['random','sequential', 'fullRandom', ]
                loop = loopDlg.trialHandler
            # if the loop is a whole new class then we can't just update the
            # params
            if loop.getType() != prevLoop.getType():
                # get indices for start and stop points of prev loop
                flow = self.frame.exp.flow
                # find the index of the initiator
                startII = flow.index(prevLoop.initiator)
                # minus one because initiator will have been deleted
                endII = flow.index(prevLoop.terminator) - 1
                # remove old loop completely
                flow.removeComponent(prevLoop)
                # finally insert the new loop
                flow.addLoop(loop, startII, endII)
            self.frame.addToUndoStack("EDIT Loop `%s`" %
                                      (loop.params['name'].val))
        elif 'conditions' in loop.params:
            loop.params['conditions'].val = condOrig
            loop.params['conditionsFile'].val = condFileOrig
        # remove the points from the timeline
        self.setDrawPoints(None)
        self.draw()

    def OnMouse(self, event):
        x, y = self.ConvertEventCoords(event)
        handlerTypes = ('StairHandler', 'TrialHandler', 'MultiStairHandler')
        if self.mode == 'normal':
            if event.LeftDown():
                icons = self.pdc.FindObjectsByBBox(x, y)
                for thisIcon in icons:
                    # might intersect several and only one has a callback
                    if thisIcon in self.componentFromID:
                        comp = self.componentFromID[thisIcon]
                        if comp.getType() in handlerTypes:
                            self.editLoopProperties(loop=comp)
                        if comp.getType() == 'Routine':
                            self.frame.routinePanel.setCurrentRoutine(
                                routine=comp)
            elif event.RightDown():
                icons = self.pdc.FindObjectsByBBox(x, y)
                # todo: clean-up remove `comp`, its unused
                comp = None
                for thisIcon in icons:
                    # might intersect several and only one has a callback
                    if thisIcon in self.componentFromID:
                        # loop through comps looking for Routine, or a Loop if
                        # no routine
                        thisComp = self.componentFromID[thisIcon]
                        if thisComp.getType() in handlerTypes:
                            comp = thisComp  # unused
                            icon = thisIcon
                        if thisComp.getType() == 'Routine':
                            comp = thisComp
                            icon = thisIcon
                            break  # we've found a Routine so stop looking
                self.frame.routinePanel.setCurrentRoutine(comp)
                try:
                    self._menuComponentID = icon
                    xy = wx.Point(x + self.GetPosition()[0],
                                  y + self.GetPosition()[1])
                    self.showContextMenu(self._menuComponentID, xy=xy)
                except UnboundLocalError:
                    # right click but not on an icon
                    # might as well do something
                    self.Refresh()
        elif self.mode == 'routine':
            if event.LeftDown():
                pt = self.entryPointPosList[0]
                self.insertRoutine(ii=self.gapMidPoints.index(pt))
            else:  # move spot if needed
                point = self.getNearestGapPoint(mouseX=x)
                self.drawEntryPoints([point])
        elif self.mode == 'loopPoint1':
            if event.LeftDown():
                self.setLoopPoint2()
            else:  # move spot if needed
                point = self.getNearestGapPoint(mouseX=x)
                self.drawEntryPoints([point])
        elif self.mode == 'loopPoint2':
            if event.LeftDown():
                self.insertLoop()
            else:  # move spot if needed
                point = self.getNearestGapPoint(mouseX=x,
                                                exclude=self.gapsExcluded)
                self.drawEntryPoints([self.entryPointPosList[0], point])

    def getNearestGapPoint(self, mouseX, exclude=()):
        """Get gap that is nearest to a particular mouse location
        """
        d = 1000000000
        nearest = None
        for point in self.gapMidPoints:
            if point in exclude:
                continue
            if (point - mouseX) ** 2 < d:
                d = (point - mouseX) ** 2
                nearest = point
        return nearest

    def getGapPointsCrossingStreams(self, gapPoint):
        """For a given gap point, identify the gap points that are
        excluded by crossing a loop line
        """
        gapArray = numpy.array(self.gapMidPoints)
        nestLevels = numpy.array(self.gapNestLevels)
        thisLevel = nestLevels[gapArray == gapPoint]
        invalidGaps = (gapArray[nestLevels != thisLevel]).tolist()
        return invalidGaps

    def showContextMenu(self, component, xy):
        menu = wx.Menu()
        # get ID
        # the ID is also the index to the element in the flow list
        compID = self._menuComponentID
        flow = self.frame.exp.flow
        component = flow[compID]
        compType = component.getType()
        if compType == 'Routine':
            for item in self.contextMenuItems:
                id = self.contextIDFromItem[item]
                menu.Append(id, self.contextMenuLabels[item])
                menu.Bind(wx.EVT_MENU, self.onContextSelect, id=id)
            self.frame.PopupMenu(menu, xy)
            # destroy to avoid mem leak:
            menu.Destroy()
        else:
            for item in self.contextMenuItems:
                if item == 'rename':
                    continue
                id = self.contextIDFromItem[item]
                menu.Append(id, self.contextMenuLabels[item])
                menu.Bind(wx.EVT_MENU, self.onContextSelect, id=id)
            self.frame.PopupMenu(menu, xy)
            # destroy to avoid mem leak:
            menu.Destroy()

    def onContextSelect(self, event):
        """Perform a given action on the component chosen
        """
        # get ID
        op = self.contextItemFromID[event.GetId()]
        # the ID is also the index to the element in the flow list
        compID = self._menuComponentID
        flow = self.frame.exp.flow
        component = flow[compID]
        # if we have a Loop Initiator, remove the whole loop
        if component.getType() == 'LoopInitiator':
            component = component.loop
        if op == 'remove':
            self.removeComponent(component, compID)
            self.frame.addToUndoStack(
                "REMOVE `%s` from Flow" % component.params['name'])
        if op == 'rename':
            self.frame.renameRoutine(component)

    def removeComponent(self, component, compID):
        """Remove either a Routine or a Loop from the Flow
        """
        flow = self.frame.exp.flow
        if component.getType() == 'Routine':
            # check whether this will cause a collapsed loop
            # prev and next elements on flow are a loop init/end
            prevIsLoop = nextIsLoop = False
            if compID > 0:  # there is at least one preceding
                prevIsLoop = (flow[compID - 1]).getType() == 'LoopInitiator'
            if len(flow) > (compID + 1):  # there is at least one more compon
                nextIsLoop = (flow[compID + 1]).getType() == 'LoopTerminator'
            if prevIsLoop and nextIsLoop:
                # because flow[compID+1] is a terminator
                loop = flow[compID + 1].loop
                msg = _translate('The "%s" Loop is about to be deleted as '
                                 'well (by collapsing). OK to proceed?')
                title = _translate('Impending Loop collapse')
                warnDlg = dialogs.MessageDialog(
                    parent=self.frame, message=msg % loop.params['name'],
                    type='Warning', title=title)
                resp = warnDlg.ShowModal()
                if resp in [wx.ID_CANCEL, wx.ID_NO]:
                    return  # abort
                elif resp == wx.ID_YES:
                    # make recursive calls to this same method until success
                    # remove the loop first
                    self.removeComponent(loop, compID)
                    # because the loop has been removed ID is now one less
                    self.removeComponent(component, compID - 1)
                    return  # have done the removal in final successful call
        # remove name from namespace only if it's a loop;
        # loops exist only in the flow
        elif 'conditionsFile' in component.params:
            conditionsFile = component.params['conditionsFile'].val
            if conditionsFile and conditionsFile not in ['None', '']:
                try:
                    trialList, fieldNames = data.importConditions(
                        conditionsFile, returnFieldNames=True)
                    for fname in fieldNames:
                        self.frame.exp.namespace.remove(fname)
                except Exception:
                    msg = ("Conditions file %s couldn't be found so names not"
                           " removed from namespace")
                    logging.debug(msg % conditionsFile)
            self.frame.exp.namespace.remove(component.params['name'].val)
        # perform the actual removal
        flow.removeComponent(component, id=compID)
        self.draw()

    def OnPaint(self, event):
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.
        dc = wx.GCDC(wx.BufferedPaintDC(self))
        # use PrepareDC to set position correctly
        self.PrepareDC(dc)
        # we need to clear the dc BEFORE calling PrepareDC
        bg = wx.Brush(self.GetBackgroundColour())
        dc.SetBackground(bg)
        dc.Clear()
        # create a clipping rect from our position and size
        # and the Update Region
        xv, yv = self.GetViewStart()
        dx, dy = self.GetScrollPixelsPerUnit()
        x, y = (xv * dx, yv * dy)
        rgn = self.GetUpdateRegion()
        rgn.Offset(x, y)
        r = rgn.GetBox()
        # draw to the dc using the calculated clipping rect
        self.pdc.DrawToDCClipped(dc, r)

    def draw(self, evt=None):
        """This is the main function for drawing the Flow panel.
        It should be called whenever something changes in the exp.

        This then makes calls to other drawing functions,
        like drawEntryPoints...
        """
        if not hasattr(self.frame, 'exp'):
            # we haven't yet added an exp
            return
        # retrieve the current flow from the experiment
        expFlow = self.frame.exp.flow
        pdc = self.pdc

        # use the ID of the drawn icon to retrieve component (loop or routine)
        self.componentFromID = {}

        pdc.Clear()  # clear the screen
        pdc.RemoveAll()  # clear all objects (icon buttons)

        font = self.GetFont()

        # draw the main time line
        self.linePos = (2.5 * self.dpi, 0.5 * self.dpi)  # x,y of start
        gap = self.dpi / (6, 4, 2)[self.appData['flowSize']]
        dLoopToBaseLine = (15, 25, 43)[self.appData['flowSize']]
        dBetweenLoops = (20, 24, 30)[self.appData['flowSize']]

        # guess virtual size; nRoutines wide by nLoops high
        # make bigger than needed and shrink later
        nRoutines = len(expFlow)
        nLoops = 0
        for entry in expFlow:
            if entry.getType() == 'LoopInitiator':
                nLoops += 1
        sizeX = nRoutines * self.dpi * 2
        sizeY = nLoops * dBetweenLoops + dLoopToBaseLine * 3
        self.SetVirtualSize(size=(sizeX, sizeY))

        # step through components in flow, get spacing from text size, etc
        currX = self.linePos[0]
        lineId = wx.NewIdRef()
        pdc.SetPen(wx.Pen(colour=cs['fl_flowline_bg']))
        pdc.DrawLine(x1=self.linePos[0] - gap, y1=self.linePos[1],
                     x2=self.linePos[0], y2=self.linePos[1])
        # NB the loop is itself the key, value is further info about it
        self.loops = {}
        nestLevel = 0
        maxNestLevel = 0
        self.gapMidPoints = [currX - gap / 2]
        self.gapNestLevels = [0]
        for ii, entry in enumerate(expFlow):
            if entry.getType() == 'LoopInitiator':
                # NB the loop is itself the dict key!?
                self.loops[entry.loop] = {
                    'init': currX, 'nest': nestLevel, 'id': ii}
                nestLevel += 1  # start of loop so increment level of nesting
                maxNestLevel = max(nestLevel, maxNestLevel)
            elif entry.getType() == 'LoopTerminator':
                # NB the loop is itself the dict key!
                self.loops[entry.loop]['term'] = currX
                nestLevel -= 1  # end of loop so decrement level of nesting
            elif entry.getType() == 'Routine':
                # just get currX based on text size, don't draw anything yet:
                currX = self.drawFlowRoutine(pdc, entry, id=ii,
                                             pos=[currX, self.linePos[1] - 10],
                                             draw=False)
            self.gapMidPoints.append(currX + gap / 2)
            self.gapNestLevels.append(nestLevel)
            pdc.SetId(lineId)
            pdc.SetPen(wx.Pen(colour=cs['fl_flowline_bg']))
            pdc.DrawLine(x1=currX, y1=self.linePos[1],
                         x2=currX + gap, y2=self.linePos[1])
            currX += gap
        lineRect = wx.Rect(self.linePos[0] - 2, self.linePos[1] - 2,
                           currX - self.linePos[0] + 2, 4)
        pdc.SetIdBounds(lineId, lineRect)

        # draw the loops first:
        maxHeight = 0
        for thisLoop in self.loops:
            thisInit = self.loops[thisLoop]['init']
            thisTerm = self.loops[thisLoop]['term']
            thisNest = maxNestLevel - self.loops[thisLoop]['nest'] - 1
            thisId = self.loops[thisLoop]['id']
            height = (self.linePos[1] + dLoopToBaseLine +
                      thisNest * dBetweenLoops)
            self.drawLoop(pdc, thisLoop, id=thisId,
                          startX=thisInit, endX=thisTerm,
                          base=self.linePos[1], height=height)
            self.drawLoopStart(pdc, pos=[thisInit, self.linePos[1]])
            self.drawLoopEnd(pdc, pos=[thisTerm, self.linePos[1]])
            if height > maxHeight:
                maxHeight = height

        # draw routines second (over loop lines):
        currX = self.linePos[0]
        for ii, entry in enumerate(expFlow):
            if entry.getType() == 'Routine':
                currX = self.drawFlowRoutine(pdc, entry, id=ii,
                                             pos=[currX, self.linePos[1] - 10])
            pdc.SetPen(wx.Pen(wx.Pen(colour=cs['fl_flowline_bg'])))
            pdc.DrawLine(x1=currX, y1=self.linePos[1],
                         x2=currX + gap, y2=self.linePos[1])
            currX += gap

        self.SetVirtualSize(size=(currX + 100, maxHeight + 50))

        self.drawLineStart(pdc, (self.linePos[0] - gap, self.linePos[1]))
        self.drawLineEnd(pdc, (currX, self.linePos[1]))

        # refresh the visible window after drawing (using OnPaint)
        self.Refresh()

    def drawEntryPoints(self, posList):
        ptSize = (3, 4, 5)[self.appData['flowSize']]
        for n, pos in enumerate(posList):
            if n >= len(self.entryPointPosList):
                # draw for first time
                id = wx.NewIdRef()
                self.entryPointIDlist.append(id)
                self.pdc.SetId(id)
                self.pdc.SetBrush(wx.Brush(cs['fl_flowline_bg']))
                self.pdc.DrawCircle(pos, self.linePos[1], ptSize)
                r = self.pdc.GetIdBounds(id)
                self.OffsetRect(r)
                self.RefreshRect(r, False)
            elif pos == self.entryPointPosList[n]:
                pass  # nothing to see here, move along please :-)
            else:
                # move to new position
                dx = pos - self.entryPointPosList[n]
                dy = 0
                r = self.pdc.GetIdBounds(self.entryPointIDlist[n])
                self.pdc.TranslateId(self.entryPointIDlist[n], dx, dy)
                r2 = self.pdc.GetIdBounds(self.entryPointIDlist[n])
                # combine old and new locations to get redraw area
                rectToRedraw = r.Union(r2)
                rectToRedraw.Inflate(4, 4)
                self.OffsetRect(rectToRedraw)
                self.RefreshRect(rectToRedraw, False)

        self.entryPointPosList = posList
        # refresh the visible window after drawing (using OnPaint)
        self.Refresh()

    def setDrawPoints(self, ptType, startPoint=None):
        """Set the points of 'routines', 'loops', or None
        """
        if ptType == 'routines':
            self.pointsToDraw = self.gapMidPoints
        elif ptType == 'loops':
            self.pointsToDraw = self.gapMidPoints
        else:
            self.pointsToDraw = []

    def drawLineStart(self, dc, pos):
        # draw bar at start of timeline; circle looked bad, offset vertically
        ptSize = (9, 9, 12)[self.appData['flowSize']]
        thic = (1, 1, 2)[self.appData['flowSize']]
        dc.SetBrush(wx.Brush(cs['fl_flowline_bg']))
        dc.SetPen(wx.Pen(cs['fl_flowline_bg']))
        dc.DrawPolygon([[0, -ptSize], [thic, -ptSize],
                        [thic, ptSize], [0, ptSize]], pos[0], pos[1])

    def drawLineEnd(self, dc, pos):
        # draws arrow at end of timeline
        # tmpId = wx.NewIdRef()
        # dc.SetId(tmpId)
        dc.SetBrush(wx.Brush(cs['fl_flowline_bg']))
        dc.SetPen(wx.Pen(cs['fl_flowline_bg']))
        dc.DrawPolygon([[0, -3], [5, 0], [0, 3]], pos[0], pos[1])
        # dc.SetIdBounds(tmpId,wx.Rect(pos[0],pos[1]+3,5,6))

    def drawLoopEnd(self, dc, pos, downwards=True):
        # define the right side of a loop but draw nothing
        # idea: might want an ID for grabbing and relocating the loop endpoint
        tmpId = wx.NewIdRef()
        dc.SetId(tmpId)
        # dc.SetBrush(wx.Brush(wx.Colour(0,0,0, 250)))
        # dc.SetPen(wx.Pen(wx.Colour(0,0,0, 255)))
        size = (3, 4, 5)[self.appData['flowSize']]
        # if downwards:
        #   dc.DrawPolygon([[size, 0], [0, size], [-size, 0]],
        #                  pos[0], pos[1] + 2 * size)  # points down
        # else:
        #   dc.DrawPolygon([[size, size], [0, 0], [-size, size]],
        #   pos[0], pos[1]-3*size)  # points up
        dc.SetIdBounds(tmpId, wx.Rect(
            pos[0] - size, pos[1] - size, 2 * size, 2 * size))
        return

    def drawLoopStart(self, dc, pos, downwards=True):
        # draws direction arrow on left side of a loop
        tmpId = wx.NewIdRef()
        dc.SetId(tmpId)
        dc.SetBrush(wx.Brush(cs['fl_flowline_bg']))
        dc.SetPen(wx.Pen(cs['fl_flowline_bg']))
        size = (3, 4, 5)[self.appData['flowSize']]
        offset = (3, 2, 0)[self.appData['flowSize']]
        if downwards:
            dc.DrawPolygon([[size, size], [0, 0], [-size, size]],
                           pos[0], pos[1] + 3 * size - offset)  # points up
        else:
            dc.DrawPolygon([[size, 0], [0, size], [-size, 0]],
                           pos[0], pos[1] - 4 * size)  # points down
        dc.SetIdBounds(tmpId, wx.Rect(
            pos[0] - size, pos[1] - size, 2 * size, 2 * size))

    def drawFlowRoutine(self, dc, routine, id, pos=[0, 0], draw=True):
        """Draw a box to show a routine on the timeline
        draw=False is for a dry-run, esp to compute and return size
        without drawing or setting a pdc ID
        """
        name = routine.name
        if self.appData['flowSize'] == 0 and len(name) > 5:
            name = ' ' + name[:4] + '..'
        else:
            name = ' ' + name + ' '
        if draw:
            dc.SetId(id)
        font = self.GetFont()
        if sys.platform == 'darwin':
            fontSizeDelta = (9, 6, 0)[self.appData['flowSize']]
            font.SetPointSize(1400 / self.dpi - fontSizeDelta)
        elif sys.platform.startswith('linux'):
            fontSizeDelta = (6, 4, 0)[self.appData['flowSize']]
            font.SetPointSize(1400 / self.dpi - fontSizeDelta)
        else:
            fontSizeDelta = (8, 4, 0)[self.appData['flowSize']]
            font.SetPointSize(1000 / self.dpi - fontSizeDelta)

        maxTime, nonSlip = routine.getMaxTime()
        if nonSlip:
            rtFill = cs['fl_routine_bg_nonslip']
            rtEdge = cs['fl_routine_bg_nonslip']
            rtText = cs['fl_routine_fg']
        else:
            rtFill = cs['fl_routine_bg_slip']
            rtEdge = cs['fl_routine_bg_slip']
            rtText = cs['fl_routine_fg']

        # get size based on text
        self.SetFont(font)
        if draw:
            dc.SetFont(font)
        w, h = self.GetFullTextExtent(name)[0:2]
        pad = (5, 10, 20)[self.appData['flowSize']]
        # draw box
        pos[1] += 2 - self.appData['flowSize']
        rect = wx.Rect(pos[0], pos[1], w + pad, h + pad)
        endX = pos[0] + w + pad
        # the edge should match the text
        if draw:
            dc.SetPen(wx.Pen(wx.Colour(rtEdge[0], rtEdge[1],
                                       rtEdge[2], wx.ALPHA_OPAQUE)))
            dc.SetBrush(wx.Brush(rtFill))
            dc.DrawRoundedRectangle(
                rect, (4, 6, 8)[self.appData['flowSize']])
            # draw text
            dc.SetTextForeground(rtText)
            dc.DrawLabel(name, rect, alignment=wx.ALIGN_CENTRE)
            if nonSlip and self.appData['flowSize'] != 0:
                font.SetPointSize(font.GetPointSize() * 0.6)
                dc.SetFont(font)
                _align = wx.ALIGN_CENTRE | wx.ALIGN_BOTTOM
                dc.DrawLabel("(%.2fs)" % maxTime, rect, alignment=_align)

            self.componentFromID[id] = routine
            # set the area for this component
            dc.SetIdBounds(id, rect)

        return endX

    def drawLoop(self, dc, loop, id, startX, endX,
                 base, height, downwards=True):
        if downwards:
            up = -1
        else:
            up = +1

        # draw loop itself, as transparent rect with curved corners
        tmpId = wx.NewIdRef()
        dc.SetId(tmpId)
        # extra distance, in both h and w for curve
        curve = (6, 11, 15)[self.appData['flowSize']]
        yy = [base, height + curve * up, height +
              curve * up / 2, height]  # for area
        dc.SetPen(wx.Pen(cs['fl_flowline_bg']))
        vertOffset = 0  # 1 is interesting too
        area = wx.Rect(startX, base + vertOffset,
                       endX - startX, max(yy) - min(yy))
        dc.SetBrush(wx.Brush(wx.Colour(0, 0, 0, 0), style=wx.TRANSPARENT))
        # draws outline:
        dc.DrawRoundedRectangle(area, curve)
        dc.SetIdBounds(tmpId, area)

        flowsize = self.appData['flowSize']  # 0, 1, or 2

        # add a name label, loop info, except at smallest size
        name = loop.params['name'].val
        _show = self.appData['showLoopInfoInFlow']
        if _show and flowsize:
            _cond = 'conditions' in list(loop.params)
            if _cond and loop.params['conditions'].val:
                xnumTrials = 'x' + str(len(loop.params['conditions'].val))
            else:
                xnumTrials = ''
            name += '  (' + str(loop.params['nReps'].val) + xnumTrials
            abbrev = ['',  # for flowsize == 0
                      {'random': 'rand.',
                       'sequential': 'sequ.',
                       'fullRandom': 'f-ran.',
                       'staircase': 'stair.',
                       'interleaved staircases': "int-str."},
                      {'random': 'random',
                       'sequential': 'sequential',
                       'fullRandom': 'fullRandom',
                       'staircase': 'staircase',
                       'interleaved staircases': "interl'vd stairs"}]
            name += ' ' + abbrev[flowsize][loop.params['loopType'].val] + ')'
        if flowsize == 0:
            if len(name) > 9:
                name = ' ' + name[:8] + '..'
            else:
                name = ' ' + name[:9]
        else:
            name = ' ' + name + ' '

        dc.SetId(id)
        font = self.GetFont()
        if sys.platform == 'darwin':
            basePtSize = (650, 750, 900)[flowsize]
        elif sys.platform.startswith('linux'):
            basePtSize = (750, 850, 1000)[flowsize]
        else:
            basePtSize = (700, 750, 800)[flowsize]
        font.SetPointSize(basePtSize / self.dpi)
        self.SetFont(font)
        dc.SetFont(font)

        # get size based on text
        pad = (5, 8, 10)[self.appData['flowSize']]
        w, h = self.GetFullTextExtent(name)[0:2]
        x = startX + (endX - startX) / 2 - w / 2 - pad / 2
        y = (height - h / 2)

        # draw box
        rect = wx.Rect(x, y, w + pad, h + pad)
        # the edge should match the text
        dc.SetPen(wx.Pen(cs['fl_flowline_bg']))
        # try to make the loop fill brighter than the background canvas:
        dc.SetBrush(wx.Brush(cs['fl_flowline_bg']))

        dc.DrawRoundedRectangle(rect, (4, 6, 8)[flowsize])
        # draw text
        dc.SetTextForeground(cs['fl_flowline_fg'])
        dc.DrawText(name, x + pad / 2, y + pad / 2)

        self.componentFromID[id] = loop
        # set the area for this component
        dc.SetIdBounds(id, rect)

def extractText(stream):
    """Take a byte stream (or any file object of type b?) and return

    :param stream: stream from wx.Process or any byte stream from a file
    :return: text converted to unicode ready for appending to wx text view
    """
    if constants.PY3:
        return stream.read().decode('utf-8')
    else:
        return stream.read()
