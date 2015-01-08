#!/usr/bin/env python2

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import wx
from wx import grid

from wx.lib import intctrl
from psychopy.app import localization
from psychopy import monitors, hardware, logging
from psychopy.app import dialogs
import time, os
import locale

DEBUG=False
NOTEBOOKSTYLE = False
NO_MEASUREMENTS=False

if DEBUG: logging.console.setLevel(logging.DEBUG)
else:logging.console.setLevel(logging.INFO)

try:
    import matplotlib
    matplotlib.use('WXAgg')
    from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
    from matplotlib.figure import Figure
except:
    pass
import numpy
#wx IDs for menu items
[idMenuSave] = \
    map(lambda _makeID: wx.NewId(), range(1))
#wx IDs for controllers (admin panel)
[idCtrlMonList, idCtrlCalibList,
    idBtnCopyCalib,idBtnSaveMon,
    idBtnNewMon, idBtnDeleteMon,
    idBtnNewCalib, idBtnDeleteCalib] = \
    map(lambda _makeID: wx.NewId(), range(8))
#wx IDs for controllers (info panel)
[idCtrlScrDist, idCtrlScrWidth,
    idCtrlCalibDate, idCtrlCalibNotes] = \
    map(lambda _makeID: wx.NewId(), range(4))

def unicodeToFloat(val):
    """Convert a unicode object from wx dialogs into a float, accounting for
    locale settings (comma might be dec place)
    """
    if val=='None':
        val=None
    else:
        try:
            val=locale.atof(val)
        except ValueError:
            return None #ignore values that can't be a float
    return val

class SimpleGrid(grid.Grid): ##, wxGridAutoEditMixin):
    def __init__(self, parent, id=-1, rows=[], cols=[], data=None):
        self.parent=parent
        self.moveTo = None
        self.nRows, self.nCols = len(rows), len(cols)
        grid.Grid.__init__(self, parent, -1, wx.Point( 0, 0 ))#,wx.Size( 300, 150 ))

        self.numEditor = grid.GridCellFloatEditor()
        self.CreateGrid(self.nRows,self.nCols)
        for nCol, col in enumerate(cols):
            self.SetColLabelValue(nCol,col)
            self.SetColFormatFloat(nCol,4,4)
            #self.SetColMinimalWidth(nCol,800)
        for nRow, row in enumerate(rows):
            self.SetRowLabelValue(nRow,row)
        for nRow in range(self.nRows):
            for nCol in range(self.nCols):
                self.SetCellEditor(nRow,nCol, self.numEditor)
        self.setData(data)
        #self.SetMargins(-5,-5)
        wx.EVT_IDLE(self, self.OnIdle)
        self.Bind(grid.EVT_GRID_SELECT_CELL, self.onSelectCell)

    def OnIdle(self, evt):
        if self.moveTo != None:
            self.SetGridCursor(self.moveTo[0], self.moveTo[1])
            self.moveTo = None
        evt.Skip()
    def setData(self, data=None):
        #update the data for the grid
        for nRow in range(self.nRows):
            for nCol in range(self.nCols):
                if data!=None and nRow<data.shape[0] and nCol<data.shape[1]:
                    self.SetCellValue(nRow, nCol, '%f' %data[nRow, nCol])
                else: self.SetCellValue(nRow,nCol,'0.000')
        self.AutoSize()
    def onSelectCell(self, evt=None):
        #data might have changed so redo layout
        self.AutoSize()
        self.parent.Layout()#expands the containing sizer if needed
        evt.Skip()#allow grid to handle the rest of the update

class PlotFrame(wx.Frame):
    def __init__(self, parent, ID, title, plotCanvas=None, pos=wx.DefaultPosition,
                 size=wx.DefaultSize, style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, ID, title, pos, size, style)
        panel = wx.Panel(self, -1)
        self.sizer = wx.GridBagSizer(1,1)
        if plotCanvas is not None:
            self.addCanvas(plotCanvas)
        wx.EVT_SIZE(self, self.OnSize)
    def addCanvas(self, canvas):
        self.canvas=canvas
        self.sizer.Add(canvas, pos=(0,0), flag=wx.EXPAND)
        self.SetSizerAndFit(self.sizer)
        self.SetAutoLayout(True)
        self.Show()
    def OnSize(self,event):
        self.canvas.SetSize(event.GetSize())

class MainFrame(wx.Frame):
    def __init__(self, parent, title):
        #create a default monitor with no name
        self.currentMon = monitors.Monitor('', verbose=False)
        self.currentMonName=None #can use this to test whether monitor is placeholder
        self.currentCalibName=None
        self.unSavedMonitor=False
        self.comPort = 1
        self.photom=None

        #start building the frame
        wx.Frame.__init__(self, parent, -1, title,size=wx.DefaultSize,
                            style=wx.DEFAULT_FRAME_STYLE )

        self.makeMenuBar()

        if NOTEBOOKSTYLE:
            #make the notebook
            self.noteBook = wx.Notebook(self, -1)

            #add the info page
            self.infoPanel = wx.Panel(self.noteBook,-1)
            self.noteBook.AddPage(self.infoPanel, _translate('Monitor Info'))
            infoSizer = wx.BoxSizer(wx.HORIZONTAL)
            infoSizer.Add(self.makeAdminBox(self.infoPanel), 1, wx.EXPAND)
            infoSizer.Add(self.makeInfoBox(self.infoPanel), 1, wx.EXPAND)
            self.infoPanel.SetAutoLayout(True)
            self.infoPanel.SetSizerAndFit(infoSizer)

            #add the calibration page
            self.calibPanel = wx.Panel(self.noteBook,-1)
            self.noteBook.AddPage(self.calibPanel, _translate('Calibration'))
            calibSizer = self.makeCalibBox(self.calibPanel)
            self.calibPanel.SetAutoLayout(True)
            self.calibPanel.SetSizerAndFit(calibSizer)

            self.noteBookSizer.Layout()
            self.noteBookSizer.Fit(self)
        else:
            #just one page
            self.infoPanel = wx.Panel(self,-1)
            mainSizer = wx.BoxSizer(wx.HORIZONTAL)
            leftSizer = wx.BoxSizer(wx.VERTICAL)
            rightSizer = wx.BoxSizer(wx.VERTICAL)
            leftSizer.Add(self.makeAdminBox(self.infoPanel), 1, wx.EXPAND|wx.ALL, 2)
            leftSizer.Add(self.makeInfoBox(self.infoPanel), 1, wx.EXPAND|wx.ALL, 2)
            rightSizer.Add(self.makeCalibBox(self.infoPanel), 1, wx.EXPAND|wx.ALL,2)
            #
            mainSizer.Add(leftSizer, 1, wx.EXPAND|wx.ALL, 2)
            mainSizer.Add(rightSizer, 1, wx.EXPAND|wx.ALL, 2)

            #finalise panel layout
            mainSizer.Layout()
            self.infoPanel.SetAutoLayout(True)
            self.infoPanel.SetSizerAndFit(mainSizer)

        #if wx version 2.5+:
        self.SetSize(self.GetBestSize())
        #self.CreateStatusBar()
        #self.SetStatusText("Maybe put tooltips down here one day")
        if os.path.isfile('psychopy.ico'):
            try:
                self.SetIcon(wx.Icon('psychopy.ico', wx.BITMAP_TYPE_ICO))
            except:
                pass

        wx.EVT_CLOSE(self, self.onCloseWindow)
        self.updateMonList()

    def makeMenuBar(self):
        menuBar = wx.MenuBar()
        fileMenu = wx.Menu()
        fileMenu.Append(idMenuSave,_translate('Save\tCtrl+S'), _translate('Save the current monitor'))
        wx.EVT_MENU(self, idMenuSave, self.onSaveMon)
        fileMenu.Append(wx.ID_CLOSE,_translate('Close Monitor Center\tCtrl+W'), _translate('Close Monitor Center (but not other PsychoPy windows)'))
        wx.EVT_MENU(self, wx.ID_CLOSE, self.onCloseWindow)
        menuBar.Append(fileMenu, _translate('&File'))

        # Edit
        editMenu = wx.Menu()
        id = wx.NewId()
        editMenu.Append(id, _translate('Copy\tCtrl+C'), _translate("Copy the current monitor's name to clipboard"))
        wx.EVT_MENU(self, id, self.onCopyMon)
        menuBar.Append(editMenu, _translate('&Edit'))

        self.SetMenuBar(menuBar)

    def makeAdminBox(self, parent):
        #make the box for the controls
        boxLabel = wx.StaticBox(parent, -1, _translate('Choose Monitor'))
        boxLabel.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.NORMAL))
        adminBox = wx.StaticBoxSizer(boxLabel)

        #build the controls
        self.ctrlMonList = wx.ListBox(parent, idCtrlMonList,
            choices=['iiyama571','sonyG500'],
            size=(350,100))
        wx.EVT_LISTBOX(self,idCtrlMonList, self.onChangeMonSelection)

        monButtonsBox = wx.BoxSizer(wx.VERTICAL)

        self.btnNewMon = wx.Button(parent,idBtnNewMon,_translate('New...'))
        wx.EVT_BUTTON(self, idBtnNewMon, self.onNewMon)
        monButtonsBox.Add(self.btnNewMon)
        self.btnNewMon.SetToolTipString(
            _translate("Create a new monitor"))

        self.btnSaveMon = wx.Button(parent,idBtnSaveMon,_translate('Save'))
        wx.EVT_BUTTON(self, idBtnSaveMon, self.onSaveMon)
        monButtonsBox.Add(self.btnSaveMon)
        self.btnSaveMon.SetToolTipString(
            _translate("Save all calibrations for this monitor"))

        self.btnDeleteMon = wx.Button(parent,idBtnDeleteMon,_translate('Delete'))
        wx.EVT_BUTTON(self, idBtnDeleteMon, self.onDeleteMon)
        monButtonsBox.Add(self.btnDeleteMon)
        self.btnDeleteMon.SetToolTipString(
            _translate("Delete this monitor entirely"))

        self.ctrlCalibList = wx.ListBox(parent, idCtrlCalibList,
            choices=[''],
            size=(350,100))
        wx.EVT_LISTBOX(self,idCtrlCalibList, self.onChangeCalibSelection)
        calibButtonsBox = wx.BoxSizer(wx.VERTICAL)

        self.btnCopyCalib = wx.Button(parent,idBtnCopyCalib,_translate('Copy...'))
        wx.EVT_BUTTON(self, idBtnCopyCalib, self.onCopyCalib)
        calibButtonsBox.Add(self.btnCopyCalib)
        self.btnCopyCalib.SetToolTipString(
            _translate("Creates a new calibration entry for this monitor"))

        self.btnDeleteCalib = wx.Button(parent,idBtnDeleteCalib,_translate('Delete'))
        wx.EVT_BUTTON(self, idBtnDeleteCalib, self.onDeleteCalib)
        calibButtonsBox.Add(self.btnDeleteCalib)
        self.btnDeleteCalib.SetToolTipString(
            _translate("Remove this calibration entry (finalized when monitor is saved)"))

        #add controls to box
        adminBoxMainSizer = wx.FlexGridSizer(cols=2, hgap=6, vgap=6)
        adminBoxMainSizer.AddMany([
            (1,10),(1,10), #a pair of empty boxes each 1x10pix
            self.ctrlMonList, monButtonsBox,
            self.ctrlCalibList, calibButtonsBox,
            ])
        adminBox.Add(adminBoxMainSizer)
        return adminBox

    def makeInfoBox(self, parent):
        #create the box
        infoBox = wx.StaticBox(parent, -1, _translate('Monitor Info'))
        infoBox.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.NORMAL))
        infoBoxSizer = wx.StaticBoxSizer(infoBox,wx.VERTICAL)

        #scr distance
        labl_scrDist = wx.StaticText(parent, -1,
            _translate("Screen Distance (cm):"),style=wx.ALIGN_RIGHT)
        self.ctrlScrDist = wx.TextCtrl(parent, idCtrlScrDist, "")
        wx.EVT_TEXT(self, idCtrlScrDist, self.onChangeScrDist)

        #scr width
        labl_scrWidth = wx.StaticText(parent, -1,
            _translate("Screen Width (cm):"),style=wx.ALIGN_RIGHT)
        self.ctrlScrWidth = wx.TextCtrl(parent, idCtrlScrWidth, "")
        wx.EVT_TEXT(self, idCtrlScrWidth, self.onChangeScrWidth)

        ##scr pixels
        labl_ScrPixels = wx.StaticText(parent, -1,
            _translate("Size (pixels; Horiz,Vert):"),style=wx.ALIGN_RIGHT)
        self.ctrlScrPixHoriz = wx.TextCtrl(parent, -1, "", size=(50,20))
        wx.EVT_TEXT(self, self.ctrlScrPixHoriz.GetId(), self.onChangeScrPixHoriz)
        self.ctrlScrPixVert = wx.TextCtrl(parent, -1, "", size=(50,20))
        wx.EVT_TEXT(self, self.ctrlScrPixVert.GetId(), self.onChangeScrPixVert)
        ScrPixelsSizer = wx.BoxSizer(wx.HORIZONTAL)
        ScrPixelsSizer.AddMany([ self.ctrlScrPixHoriz, self.ctrlScrPixVert])

        #date
        labl_calibDate = wx.StaticText(parent, -1,
            _translate("Calibration Date:"),style=wx.ALIGN_RIGHT)
        self.ctrlCalibDate = wx.TextCtrl(parent, idCtrlCalibDate, "",
            size=(150,20))
        self.ctrlCalibDate.Disable()
        #notes
        labl_calibNotes = wx.StaticText(parent, -1,
            _translate("Notes:"),style=wx.ALIGN_RIGHT)
        self.ctrlCalibNotes = wx.TextCtrl(parent, idCtrlCalibNotes, "",
            size=(150,150),
            style=wx.TE_MULTILINE)
        wx.EVT_TEXT(self, idCtrlCalibNotes, self.onChangeCalibNotes)

        #bits++
        self.ctrlUseBits = wx.CheckBox(parent, -1,_translate('Use Bits++'))
        wx.EVT_CHECKBOX(self, self.ctrlUseBits.GetId(), self.onChangeUseBits)

        infoBoxGrid = wx.FlexGridSizer(cols=2, hgap=6, vgap=6)
        infoBoxGrid.AddMany([
            (1,10),(1,10), #a pair of empty boxes each 1x10pix
            (1,10),self.ctrlUseBits,
            labl_scrDist, self.ctrlScrDist,
            labl_ScrPixels, ScrPixelsSizer,
            labl_scrWidth, self.ctrlScrWidth,
            labl_calibDate, self.ctrlCalibDate
            ])
        infoBoxGrid.Layout()
        infoBoxSizer.Add(infoBoxGrid)
        #put the notes box below the main grid sizer
        infoBoxSizer.Add(labl_calibNotes)
        infoBoxSizer.Add(self.ctrlCalibNotes, 1, wx.EXPAND)
        return infoBoxSizer

    def makeCalibBox(self, parent):
        boxLabel = wx.StaticBox(parent, -1, _translate('Calibration'))
        boxLabel.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.NORMAL))
        calibBox = wx.StaticBoxSizer(boxLabel)

        photometerBox = wx.FlexGridSizer(cols=2, hgap=6, vgap=6)
        #com port entry number
        self.comPortLabel =  wx.StaticText(parent, -1, " ", size=(150,20))
        #photometer button
        # photom type choices should not need localization:
        self.ctrlPhotomType = wx.Choice(parent, -1, name="Type:",
            choices=list([p.longName for p in hardware.getAllPhotometers()]))

        self._photomChoices = [_translate("Scan all ports")] + list(hardware.getSerialPorts())
        self.ctrlPhotomPort = wx.ComboBox(parent, -1, name="Port:",
                                          value=self._photomChoices[0], # scan all ports
                                          choices=self._photomChoices,
                                          size=self.ctrlPhotomType.GetSize()+[0,5]
                                    )

        #wx.EVT_CHOICE(self, self.ctrlPhotomType.GetId(), self.onChangePhotomType)#not needed?
        self.btnFindPhotometer = wx.Button(parent, -1, _translate("Get Photometer"))
        wx.EVT_BUTTON(self, self.btnFindPhotometer.GetId(), self.onBtnFindPhotometer)

        #gamma controls
        self.btnCalibrateGamma = wx.Button(
            parent, -1, _translate("Gamma Calibration..."))
        wx.EVT_BUTTON(self, self.btnCalibrateGamma.GetId(), self.onCalibGammaBtn)
        self.btnTestGamma = wx.Button(
            parent, -1, _translate("Gamma Test..."))
        self.btnTestGamma.Enable(False)

        #color controls
        wx.EVT_BUTTON(self, self.btnTestGamma.GetId(), self.onCalibTestBtn)
        self.btnCalibrateColor = wx.Button(
            parent, -1, _translate("Chromatic Calibration..."))
        self.btnCalibrateColor.Enable(False)
        wx.EVT_BUTTON(self, self.btnCalibrateColor.GetId(), self.onCalibColorBtn)
        self.btnPlotGamma = wx.Button(
            parent, -1, _translate("Plot gamma"))
        wx.EVT_BUTTON(self, self.btnPlotGamma.GetId(), self.plotGamma)
        self.btnPlotSpectra = wx.Button(
            parent, -1, _translate("Plot spectra"))
        wx.EVT_BUTTON(self, self.btnPlotSpectra.GetId(), self.plotSpectra)

        photometerBox.AddMany([self.ctrlPhotomType,self.btnFindPhotometer,
                               self.ctrlPhotomPort,(0,0),
                                self.comPortLabel,(0,0),
                                self.btnCalibrateGamma, (0,0),
                                self.btnTestGamma, self.btnPlotGamma,
                                self.btnCalibrateColor, self.btnPlotSpectra])

        #-----------------------
        #----GAMMA------------
        #-----------------------
        #calibration grid
        gammaBox = wx.StaticBox(parent,-1,_translate('Linearization'))
        gammaBox.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.NORMAL))
        gammaBoxSizer = wx.StaticBoxSizer(gammaBox, wx.VERTICAL)

        # don't localize the choices
        self.choiceLinearMethod = wx.Choice(parent, -1, name='formula:',
                    choices=['easy: a+kx^g', 'full: a+(b+kx)^g'])
        if self.currentMon.getLinearizeMethod()==4:
            self.choiceLinearMethod.SetSelection(1)
        else: self.choiceLinearMethod.SetSelection(0)
        wx.EVT_CHOICE(self, self.choiceLinearMethod.GetId(), self.onChangeLinearMethod)
        gammaBoxSizer.Add(self.choiceLinearMethod, 1, wx.ALL, 2)

        self.gammaGrid = SimpleGrid(parent, id=-1,
                                    cols=['Min','Max','Gamma','a','b','k'],
                                    rows=['lum','R','G','B'])
        gammaBoxSizer.Add(self.gammaGrid)
        grid.EVT_GRID_CELL_CHANGE(self.gammaGrid,self.onChangeGammaGrid)
        gammaBoxSizer.Layout()

        #LMS grid
        LMSbox = wx.StaticBox(parent,-1,'LMS->RGB')
        LMSboxSizer = wx.StaticBoxSizer(LMSbox, wx.VERTICAL)
        self.LMSgrid = SimpleGrid(parent, id=-1,
                                  cols=['L','M','S'],
                                  rows=['R','G','B'])
        LMSboxSizer.Add(self.LMSgrid)
        LMSboxSizer.Layout()
        grid.EVT_GRID_CELL_CHANGE(self.LMSgrid,self.onChangeLMSgrid)

        #DKL grid
        DKLbox = wx.StaticBox(parent,-1,'DKL->RGB')
        DKLboxSizer = wx.StaticBoxSizer(DKLbox, wx.VERTICAL)
        self.DKLgrid = SimpleGrid(parent, id=-1,
                                  cols=['Lum','L-M','L+M-S'],
                                  rows=['R','G','B'])
        DKLboxSizer.Add(self.DKLgrid)
        DKLboxSizer.Layout()
        grid.EVT_GRID_CELL_CHANGE(self.DKLgrid,self.onChangeDKLgrid)


        calibBoxMainSizer = wx.BoxSizer(wx.VERTICAL)
        calibBoxMainSizer.AddMany([photometerBox,
                                   gammaBoxSizer,
                                   LMSboxSizer,
                                   DKLboxSizer,
                                  ])
        calibBoxMainSizer.Layout()

        if NOTEBOOKSTYLE:
            return calibBoxMainSizer
        else:
            #put the main sizer into a labeled box
            calibBox.Add(calibBoxMainSizer)
            return calibBox

    def loadMonitor(self, name=None):
        self.currentMon = monitors.Monitor(name, verbose=False)
        self.currentCalibName= self.currentMon.setCurrent(-1)
        self.updateCalibList()
        self.unSavedMonitor=False

    def updateMonList(self):
        #refresh list of all available monitors on path
        monList = monitors.getAllMonitors()
        self.ctrlMonList.Set(monList)
        #if we had selected a monitor, make sure it's still selected
        if len(monList)>0:
            if self.currentMonName!=None:
                self.ctrlMonList.SetStringSelection(self.currentMonName)
            else:
                self.ctrlMonList.SetSelection(0)
                self.onChangeMonSelection(event=-1)
            #do we need to update the calibList always after this?
            return 1
        else:
            #there are no monitors - create an empty one to popoulate the fields
            self.currentMon = monitors.Monitor('',verbose=False)
            self.currentMonName=None
            return 0 #there were no monitors on the path
    def updateCalibList(self, thisList=None):
        """update the list of calibrations either from the current
        monitor or to a given list
        """
        if thisList is None: #fetch it from monitor file
            thisList = self.currentMon.calibNames
        #populate the listbox
        self.ctrlCalibList.Set(thisList)
        #select the current calib
        if self.currentCalibName in thisList:
            self.ctrlCalibList.SetStringSelection(self.currentCalibName)
            self.onChangeCalibSelection(event=-1)

#application callbacks
    def onCloseWindow(self, event):
        if self.unSavedMonitor:
            #warn user that data will be lost
            dlg = dialogs.MessageDialog(self,message=_translate('Save changes to monitor settings before quitting?'),type='Warning')
            resp = dlg.ShowModal()
            if resp  == wx.ID_CANCEL:
                return 1 #return before quitting
            elif resp == wx.ID_YES:
                #save then quit
                self.currentMon.saveMon()
            elif resp == wx.ID_NO:
                pass #don't save just quit
            dlg.Destroy()
        self.onCopyMon() # save current monitor name to clipboard
        self.Destroy()

#admin callbacks
    def onChangeMonSelection(self, event):
        if self.unSavedMonitor:
            if self.currentMonName == self.ctrlMonList.GetStringSelection():
                #it didnt' really change
                return 1
            #warn user that data will be lost
            dlg = dialogs.MessageDialog(self, _translate('Save changes to monitor?'),
                type='Warning')
            resp = dlg.ShowModal()
            dlg.Destroy()
            if resp  == wx.ID_CANCEL:
                #revert and return
                self.ctrlMonList.SetStringSelection(self.currentMonName)
                return False #return before quitting
            elif resp == wx.ID_YES:
                #save then change
                self.currentMon.saveMon()
            elif resp == wx.ID_NO:
                pass #don't save just change
        self.currentMonName = self.ctrlMonList.GetStringSelection()
        self.loadMonitor(self.currentMonName)
    def onChangeCalibSelection(self, event, newCalib=None):
        #get data under current calibration
        if newCalib is None:
            #probably came from an event - check the new name
            newCalib = self.ctrlCalibList.GetStringSelection()
        #do the load and check new name
        self.currentCalibName= self.currentMon.setCurrent(newCalib)

        #keys that may not exist
        #todo remove this code - only needed for monitor objects made pre version 0.63
        if not 'gammaGrid' in self.currentMon.currentCalib:
            self.currentMon.currentCalib['gammaGrid']=monitors.numpy.ones((4,3), 'd')
        if not 'lms_rgb' in self.currentMon.currentCalib:
            self.currentMon.currentCalib['lms_rgb']=monitors.numpy.ones((3,3), 'd')
        if not 'dkl_rgb' in self.currentMon.currentCalib:
            self.currentMon.currentCalib['dkl_rgb']=monitors.numpy.ones((3,3), 'd')
        if not 'sizePix' in self.currentMon.currentCalib:
            self.currentMon.currentCalib['sizePix']= [1024,768]

        #insert values from new calib into GUI
        self.ctrlCalibDate.SetValue(
            monitors.strFromDate(self.currentMon.getCalibDate()))
        self.ctrlScrDist.SetValue(locale.str(self.currentMon.getDistance()))
        self.ctrlScrWidth.SetValue(locale.str(self.currentMon.getWidth()))
        self.ctrlScrPixHoriz.SetValue(locale.str(self.currentMon.currentCalib['sizePix'][0]))
        self.ctrlScrPixVert.SetValue(locale.str(self.currentMon.currentCalib['sizePix'][1]))
        #self.ctrlScrGamma.SetValue(str(self.currentMon.getGamma()))
        self.ctrlCalibNotes.SetValue(self.currentMon.getNotes() or '')
        self.ctrlUseBits.SetValue(self.currentMon.getUseBits())
        self.gammaGrid.setData(self.currentMon.getGammaGrid())
        if self.currentMon.getLinearizeMethod()==4:
            self.choiceLinearMethod.SetSelection(1)
        else: self.choiceLinearMethod.SetSelection(0)
        self.LMSgrid.setData(self.currentMon.getLMS_RGB())
        self.DKLgrid.setData(self.currentMon.getDKL_RGB())

        self.enableDisableCtrls()
        self.unSavedMonitor=False
        return 1

    def enableDisableCtrls(self):
        #update controls for current monitor
        if not 'lumsPre' in self.currentMon.currentCalib:
            self.btnPlotGamma.Enable(True)
        else: self.btnPlotGamma.Enable(True)
        if not 'spectraRGB' in self.currentMon.currentCalib:
            self.btnPlotSpectra.Enable(False)
        else: self.btnPlotSpectra.Enable(True)
        if self.currentMon.getLevelsPre() is None:
            self.choiceLinearMethod.Disable()
        else: self.choiceLinearMethod.Enable()

    def onCopyMon(self, event=None):
        """Copy monitor name to clipboard, to paste elsewhere
        """
        if wx.TheClipboard.Open():
            wx.TheClipboard.Clear()
            wx.TheClipboard.SetData(wx.TextDataObject(self.currentMon.name))
            wx.TheClipboard.Close()
    def onSaveMon(self, event):
        """Saves calibration entry to location.
        Note that the calibration date will reflect the save date/time"""
        self.currentMon.saveMon()
        self.unSavedMonitor=False
    def onCopyCalib(self, event):
        """Creates a new calibration entry for the monitor.
        Note that the calibration date will reflect the save date/time"""

        #use time as initial guess at name
        calibTime = time.localtime()
        calibTimeStr = monitors.strFromDate(calibTime)

        #then use dialogue so user can override
        infoStr=_translate('Name of this calibration (for monitor "%(name)s") will be:)') % {'name': self.currentMon.name}
        dlg = wx.TextEntryDialog(self, message=infoStr, defaultValue=calibTimeStr, caption=_translate('Input text'))
        if dlg.ShowModal() == wx.ID_OK:
            newCalibName= dlg.GetValue()
            #update the GUI to reflect new calibration
            self.currentMon.copyCalib(newCalibName)
            self.currentMon.setCalibDate(calibTime)

            self.onChangeCalibSelection(1,newCalibName)
            self.updateCalibList()
            self.unSavedMonitor=True
        dlg.Destroy()
    def onNewMon(self, event):
        #open a dialogue to get the name
        dlg = wx.TextEntryDialog(self, _translate('New monitor name:'), caption=_translate('Input text'))
        if dlg.ShowModal() == wx.ID_OK:
            self.currentMonName= dlg.GetValue()
            self.ctrlMonList.Append(self.currentMonName)
            self.ctrlMonList.SetStringSelection(self.currentMonName)
            self.currentMon = monitors.Monitor(self.currentMonName, verbose=True)
            self.updateCalibList()
            self.onChangeCalibSelection(event=1)
            self.unSavedMonitor=True
        dlg.Destroy()

    def onDeleteMon(self, event):
        monToDel = self.currentMonName
        dlg = dialogs.MessageDialog(parent=self,
                message=_translate('Are you sure you want to delete all details for %s? (cannot be undone)') % monToDel,
                type='Warning')
        response = dlg.ShowModal()
        dlg.Destroy()
        if response == wx.ID_YES:
            #delete it
            monitorFileName = os.path.join(monitors.monitorFolder,
                monToDel+".calib")
            os.remove(monitorFileName)
            self.currentMon=None
            self.currentMonName=None
            self.updateMonList()
            #load most recent calibration instead
            self.onChangeMonSelection(event=None)#this will load calibration "-1" (last calib)
            self.updateCalibList()

    def onDeleteCalib(self, event):
        calToDel = self.ctrlCalibList.GetStringSelection()
        #warn user that data will be lost
        dlg = dialogs.MessageDialog(parent=self,
                message=_translate('Are you sure you want to delete this calibration? (cannot be undone)'),
                type='Warning')
        if dlg.ShowModal() == wx.ID_YES:
            #delete it
            self.currentMon.delCalib(calToDel)
            #load most recent calibration instead
            self.onChangeCalibSelection(event=None, newCalib=-1)#this will load calibration "-1" (last calib)
            self.updateCalibList()
        dlg.Destroy()

#info callbacks
    def onChangeCalibDate(self, event):
        #do we want the user to change a calib date?
        pass
    def onChangeCalibNotes(self, event):
        newVal = self.ctrlCalibNotes.GetValue()
        self.currentMon.setNotes(newVal)
        self.unSavedMonitor=True
    def onChangeScrDist(self, event):
        newVal = unicodeToFloat(self.ctrlScrDist.GetValue())
        self.currentMon.setDistance( newVal )
        self.unSavedMonitor=True
    def onChangeScrWidth(self, event):
        newVal = unicodeToFloat(self.ctrlScrWidth.GetValue())
        self.currentMon.setWidth( newVal )
        self.unSavedMonitor=True
    def onChangeScrPixHoriz(self, event):
        newVal = unicodeToFloat(self.ctrlScrPixHoriz.GetValue())
        self.currentMon.currentCalib['sizePix'][0] = newVal
        self.unSavedMonitor=True
    def onChangeScrPixVert(self, event):
        newVal = unicodeToFloat(self.ctrlScrPixVert.GetValue())
        self.currentMon.currentCalib['sizePix'][1] = newVal
        self.unSavedMonitor=True

#calib callbacks
    def onChangeGammaGrid(self, event):
        #convert to float
        newVal = self.gammaGrid.GetCellValue(event.GetRow(), event.GetCol())
        newVal = unicodeToFloat(newVal)
        #insert in grid
        self.currentMon.currentCalib['gammaGrid'][event.GetRow(), event.GetCol()] = newVal
        self.unSavedMonitor=True

    def onChangeLMSgrid(self, event):
        #convert to float
        newVal = self.LMSgrid.GetCellValue(event.GetRow(), event.GetCol())
        newVal = unicodeToFloat(newVal)
        #insert in grid
        self.currentMon.currentCalib['lms_rgb'][event.GetRow(), event.GetCol()] = newVal
        self.unSavedMonitor=True

    def onChangeDKLgrid(self, event):
        #convert to float
        newVal = self.DKLgrid.GetCellValue(event.GetRow(), event.GetCol())
        newVal = unicodeToFloat(newVal)
        #insert in grid
        self.currentMon.currentCalib['dkl_rgb'][event.GetRow(), event.GetCol()] = newVal
        self.unSavedMonitor=True

    def onCalibGammaBtn(self, event):
        if NO_MEASUREMENTS:
            #recalculate from previous measure
            lumsPre = self.currentMon.getLumsPre()
            lumLevels = self.currentMon.getLevelsPre()
        else:
            #present a dialogue to get details for calibration
            calibDlg = GammaDlg(self, self.currentMon)
            if calibDlg.ShowModal()!=wx.ID_OK:
                calibDlg.Destroy()
                return 1
            nPoints = int(calibDlg.ctrlNPoints.GetValue())
            stimSize = unicodeToFloat(calibDlg.ctrlStimSize.GetValue())
            useBits = calibDlg.ctrlUseBits.GetValue()
            calibDlg.Destroy()
            autoMode = calibDlg.methodChoiceBx.GetStringSelection()
            screen = int(calibDlg.ctrlScrN.GetValue())-1 #lib starts at zero but here we allow 1

            #run the calibration itself
            lumLevels=monitors.DACrange(nPoints)
            lumsPre = monitors.getLumSeries(photometer=self.photom,
                                                 lumLevels=lumLevels,
                                                 useBits=useBits,
                                                 autoMode=autoMode,
                                                 winSize=self.currentMon.getSizePix(),
                                                 stimSize=stimSize, monitor=self.currentMon,
                                                 screen=screen)

            #allow user to type in values
            if autoMode=='semi':
                inputDlg = GammaLumValsDlg(parent=self, levels=lumLevels)
                lumsPre = inputDlg.show()#will be [] if user cancels
                inputDlg.Destroy()

        #fit the gamma curves
        if lumsPre is None or len(lumsPre)>1:
            self.onCopyCalib(1)#create a new dated calibration
            self.currentMon.setLumsPre(lumsPre)#save for future
            self.currentMon.setLevelsPre(lumLevels)#save for future
            self.btnPlotGamma.Enable(True)
            self.choiceLinearMethod.Enable()

            #do the fits
            self.doGammaFits(lumLevels,lumsPre)
        else:
            logging.warning('No lum values captured/entered')

    def doGammaFits(self, levels, lums):
        linMethod = self.currentMon.getLinearizeMethod()

        if linMethod==4:
            logging.info('Fitting gamma equation (%i) to luminance data' % linMethod)
            currentCal = numpy.ones([4,6],'f')*numpy.nan
            for gun in [0,1,2,3]:
                gamCalc = monitors.GammaCalculator(levels, lums[gun,:], eq=linMethod)
                currentCal[gun,0]=gamCalc.min#min
                currentCal[gun,1]=gamCalc.max#max
                currentCal[gun,2]=gamCalc.gamma#gamma
                currentCal[gun,3]=gamCalc.a#gamma
                currentCal[gun,4]=gamCalc.b#gamma
                currentCal[gun,5]=gamCalc.k#gamma
        else:
            currentCal = numpy.ones([4,3],'f')*numpy.nan
            logging.info('Fitting gamma equation (%i) to luminance data' % linMethod)
            for gun in [0,1,2,3]:
                gamCalc = monitors.GammaCalculator(levels, lums[gun,:], eq=linMethod)
                currentCal[gun,0]=lums[gun,0]#min
                currentCal[gun,1]=lums[gun,-1]#max
                currentCal[gun,2]=gamCalc.gamma#gamma

        self.gammaGrid.setData(currentCal)
        self.currentMon.setGammaGrid(currentCal)
        self.unSavedMonitor=True

    def onChangeLinearMethod(self,event):
        newMethod = self.choiceLinearMethod.GetStringSelection()
        if newMethod.startswith('full'):
            self.currentMon.setLineariseMethod(4)
        else:
            self.currentMon.setLineariseMethod(1)
        self.unSavedMonitor=True
        if self.currentMon.getLumsPre()!=None:
            self.doGammaFits(self.currentMon.getLevelsPre(), self.currentMon.getLumsPre())

    def onCalibTestBtn(self,event):
        #set the gamma and test calibration
        currentCal = self.currentMon.currentCalib['gammaGrid']

        calibDlg = GammaDlg(self, self.currentMon)
        if calibDlg.ShowModal()!=wx.ID_OK:
            calibDlg.Destroy()
            return 1
        nPoints = int(calibDlg.ctrlNPoints.GetValue())
        stimSize = unicodeToFloat(calibDlg.ctrlStimSize.GetValue())
        useBits = calibDlg.ctrlUseBits.GetValue()
        calibDlg.Destroy()
        autoMode = calibDlg.methodChoiceBx.GetStringSelection()
        screen = int(calibDlg.ctrlScrN.GetValue())-1 #lib starts at zero but here we allow 1

        lumLevels=monitors.DACrange(nPoints)
        lumsPost = monitors.getLumSeries(photometer=self.photom,
                                              lumLevels=lumLevels,
                                              useBits=useBits,
                                              autoMode=autoMode,
                                              winSize=self.currentMon.getSizePix(),
                                              stimSize=stimSize,
                                              monitor = self.currentMon,
                                              gamma=None,#causes the function to use monitor settings
                                              screen=screen,
                                              )

        if len(lumsPost)>1:
            self.currentMon.setLumsPost(lumsPost)#save for future
            self.currentMon.setLevelsPost(lumLevels)#save for future
            self.unSavedMonitor=True

    def onCalibColorBtn(self, event):
        if NO_MEASUREMENTS:
            #get previous spectra:
            nm, spectra = self.currentMon.getSpectra()
        else:
            #do spectral measurement:
            useBits=self.currentMon.getUseBits()
            nm, spectra = monitors.getRGBspectra(stimSize=0.5, photometer=self.photom, winSize=self.currentMon.getSizePix())
            self.currentMon.setSpectra(nm,spectra)
            self.btnPlotSpectra.Enable(True)#can definitely now plot spectra
            self.unSavedMonitor=True

        self.onCopyCalib(1)#create a new dated calibration

        #dkl
        dkl_rgb = monitors.makeDKL2RGB(nm,spectra)
        self.currentMon.setDKL_RGB(dkl_rgb)
        self.DKLgrid.setData(dkl_rgb)
        #lms
        lms_rgb = monitors.makeLMS2RGB(nm,spectra)
        self.currentMon.setLMS_RGB(lms_rgb)
        self.LMSgrid.setData(lms_rgb)

    def onChangeUseBits(self, event):
        newVal = self.ctrlUseBits.GetValue()
        self.currentMon.setUseBits(newVal)
        self.unSavedMonitor=True
    def onCtrlPhotomType(self, event):
        pass
    def onBtnFindPhotometer(self, event):

        # safer to get by index, but GetStringSelection will work for nonlocalized techincal names:
        photName = self.ctrlPhotomType.GetStringSelection()
        # not sure how
        photPort = self.ctrlPhotomPort.GetValue().strip()
        if not photPort or photPort == self._photomChoices[0]:  # [0] == Scan all ports
            photPort = None
        elif photPort.isdigit():
            photPort = int(photPort)
        #search all ports
        self.comPortLabel.SetLabel(_translate('Scanning ports...'))
        self.Update()
        self.photom = hardware.findPhotometer(device=photName,ports=photPort)
        if self.photom is not None and self.photom.OK:
            self.btnFindPhotometer.Disable()
            self.btnCalibrateGamma.Enable(True)
            self.btnTestGamma.Enable(True)
            if hasattr(self.photom, 'getLastSpectrum'):
                self.btnCalibrateColor.Enable(True)
            self.comPortLabel.SetLabel(_translate('%(photomType)s found on %(photomPort)s') %
                                       {'photomType': self.photom.type,
                                        'photomPort': self.photom.portString})
        else:
            self.comPortLabel.SetLabel(_translate('No photometers found'))
            self.photom=None

        #does this device need a dark calibration?
        if hasattr(self.photom, 'getNeedsCalibrateZero') and self.photom.getNeedsCalibrateZero():
            #prompt user if we need a dark calibration for the device
            if self.photom.getNeedsCalibrateZero():
                dlg = wx.Dialog(self,title=_translate('Dark calibration of ColorCAL'))
                msg=_translate('Your ColorCAL needs to be calibrated first. '
                      'Please block all light from getting into the lens and press OK.')
                while self.photom.getNeedsCalibrateZero():
                    dlg = dialogs.MessageDialog(self,message=msg,
                                                title=_translate('Dark calibration of ColorCAL'),
                                                type='Info')#info dlg has only an OK button
                    resp=dlg.ShowModal()
                    if resp== wx.ID_CANCEL:
                        self.photom=None
                        self.comPortLabel.SetLabel('')
                        return 0
                    elif resp == wx.ID_OK:
                        self.photom.calibrateZero()
                    #this failed at least once. Try again.
                    msg = _translate('Try again. Cover the lens fully and press OK')
    def plotGamma(self, event=None):
        figTitle = _translate('%(monName)s %(calibName)s Gamma Functions') % {
                        'monName': self.currentMonName,
                        'calibName': self.currentCalibName}
        plotWindow = PlotFrame(self,1003,figTitle)

        figure = Figure(figsize=(5,5), dpi=80)
        figureCanvas = FigureCanvas(plotWindow, -1, figure)
        plt = figure.add_subplot(111)
        plt.hold('off')

        gammaGrid = self.currentMon.getGammaGrid()
        lumsPre = self.currentMon.getLumsPre()
        levelsPre = self.currentMon.getLevelsPre()
        lumsPost = self.currentMon.getLumsPost()
        if lumsPre!=None:
            colors='krgb'
            xxSmooth = monitors.numpy.arange(0,255.5, 0.5)
            eq = self.currentMon.getLinearizeMethod()
            for gun in range(4): #includes lum
                gamma = gammaGrid[gun,2]
                minLum = gammaGrid[gun,0]
                maxLum = gammaGrid[gun,1]
                if  eq<=2:
                    #plot fitted curve
                    curve = monitors.gammaFun(xxSmooth, minLum, maxLum, gamma,
                        eq=eq, a=None, b=None, k=None)
                    plt.plot(xxSmooth, curve, colors[gun]+'-', linewidth=1.5)
                if self.currentMon.getLinearizeMethod() ==4:
                    a,b,k = gammaGrid[gun,3:]
                    #plot fitted curve
                    curve = monitors.gammaFun(xxSmooth, minLum, maxLum, gamma,
                        eq=eq, a=a, b=b, k=k)
                    plt.plot(xxSmooth, curve, colors[gun]+'-', linewidth=1.5)
                else:
                    pass
                    #polyFit = self.currentMon._gammaInterpolator[gun]
                    #curve = xxSmooth*0.0
                    #for expon, coeff in enumerate(polyFit):
                        #curve += coeff*xxSmooth**expon
                    #plt.plot(xxSmooth, curve, colors[gun]+'-', linewidth=1.5)
                #plot POINTS
                plt.plot(levelsPre, lumsPre[gun,:], colors[gun]+'o', linewidth=1.5)

            lumsPost = self.currentMon.getLumsPost()
            levelsPost = self.currentMon.getLevelsPost()
        if lumsPost!=None:
            for gun in range(4): #includes lum,r,g,b
                lums=lumsPost[gun,:]
                gamma = gammaGrid[gun,2]
                gamma = gammaGrid[gun,2]
                minLum = min(lums)
                maxLum = max(lums)
                #plot CURVE
                plt.plot([levelsPost[0], levelsPost[-1]], [minLum, maxLum], colors[gun]+'--', linewidth=1.5)
                #plot POINTS
                plt.plot(levelsPost,lums,'o', markerfacecolor = 'w', markeredgecolor=colors[gun], linewidth=1.5)
        figureCanvas.draw()#update the canvas
        plotWindow.addCanvas(figureCanvas)

    def plotSpectra(self, event=None):
        figTitle = _translate('%(monName)s %(calibName)s Spectra') % {
                      'monName': self.currentMonName,
                      'calibName': self.currentCalibName}
        plotWindow = PlotFrame(self,1003,figTitle)
        figure = Figure(figsize=(5,5), dpi=80)
        figureCanvas = FigureCanvas(plotWindow, -1, figure)
        plt = figure.add_subplot(111)
        plt.hold('off')

        nm, spectraRGB = self.currentMon.getSpectra()
        if nm!=None:
            plt.plot(nm,spectraRGB[0,:], 'r-', linewidth=1.5)
            plt.hold('on')
            plt.plot(nm,spectraRGB[1,:], 'g-', linewidth=2)
            plt.plot(nm,spectraRGB[2,:], 'b-', linewidth=2)
        figureCanvas.draw()#update the canvas
        plotWindow.addCanvas(figureCanvas)

    def onClosePlotWindow(self, event):
        print event

class GammaLumValsDlg(wx.Dialog):
    '''a dialogue to manually get the luminance values recorded for each level'''
    def __init__(self, parent, levels):

        wx.Dialog.__init__(self, parent, -1, _translate('Recorded luminance values'),
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER
            )

        pad=5

        panel = wx.Panel(self, -1)
        mainSizer = wx.BoxSizer(wx.VERTICAL)
        mainSizer.Add(self.makeCalibBox(parent=panel, levels=levels), 1, wx.EXPAND|wx.ALL, pad)

        butBox = wx.BoxSizer(wx.HORIZONTAL)
        btnOK = wx.Button(panel, wx.ID_OK, _translate(" OK "))
        btnOK.SetDefault()
        btnCANC = wx.Button(panel, wx.ID_CANCEL, _translate(" Cancel "))

        butBox.Add(btnOK,1,wx.BOTTOM|wx.ALIGN_RIGHT, pad)
        butBox.Add(btnCANC,1,wx.BOTTOM|wx.RIGHT|wx.ALIGN_RIGHT, pad)
        mainSizer.Add(butBox,
            flag=wx.ALIGN_CENTER|wx.TOP|wx.BOTTOM, border=10)

        #finalise panel layout
        panel.SetAutoLayout(True)
        panel.SetSizerAndFit(mainSizer)
        mainSizer.Layout()
        self.SetSize(self.GetBestSize())

    def makeCalibBox(self,parent,levels):
        '''do my best to make a calibration box'''
        gammaBox = wx.StaticBox(parent,-1, _translate('Luminance Values'))
        gammaBox.SetFont(wx.Font(14, wx.SWISS, wx.NORMAL, wx.NORMAL))
        gammaBoxSizer = wx.StaticBoxSizer(gammaBox, wx.VERTICAL)

        theCols = map(str,levels)

        self.gammaGrid = SimpleGrid(parent, id=-1,
                                    cols=theCols,
                                    rows=['lum','R','G','B'])
        gammaBoxSizer.Add(self.gammaGrid)
        grid.EVT_GRID_CELL_CHANGE(self.gammaGrid,self.onChangeGammaGrid)
        gammaBoxSizer.Layout()

        return gammaBoxSizer

    def onChangeGammaGrid(self, event):
        '''The first column = black, so it gets set same for all, let's help out!'''
        if event.GetCol()==0:
            newVal = self.gammaGrid.GetCellValue(event.GetRow(), event.GetCol())
            newVal = unicodeToFloat(newVal)
            for nRow in range(self.gammaGrid.nRows):
                self.gammaGrid.SetCellValue(nRow,0,'%f' %newVal)

    def getData(self):
        '''retrieve the data from the grid in same format as auto calibration'''
        data=[]
        for nRow in range(self.gammaGrid.nRows):
            bob=[]
            for nCol in range(self.gammaGrid.nCols):
                bob.append(self.gammaGrid.GetCellValue(nRow, nCol))
            data.append(map(float,bob))
        return data

    def show(self):
        '''show dialog, retrieve data, empty if cancel'''
        ok = self.ShowModal()
        if  ok == wx.ID_OK:
            return numpy.array(self.getData())
        else:
            return numpy.array([])

class GammaDlg(wx.Dialog):
    def __init__(self, parent, monitor):
        self.method = 'auto'
        self.nPoints = 8
        assert isinstance(monitor, monitors.Monitor)
        self.useBits=monitor.getUseBits()

        wx.Dialog.__init__(self, parent, -1, _translate('Gamma Calibration'),
            style=wx.DEFAULT_DIALOG_STYLE|wx.RESIZE_BORDER
            )
        mainSizer =  wx.FlexGridSizer(cols=2, hgap=1, vgap=1)

        #select method of calib (auto, semi-auto, manual)
        #todo: make the input  tablefor manual method
        self.methodChoiceBx = wx.Choice(self, -1,
            choices=['auto','semi'])
        self.methodChoiceBx.SetStringSelection('auto')
        wx.EVT_CHOICE(self, self.methodChoiceBx.GetId(),self.onMethodChange)

        self.ctrlUseBits = wx.CheckBox(self, -1,_translate('Use Bits++'))
        self.ctrlUseBits.SetValue(self.useBits)

        self.labelNPoints = wx.StaticText(self, -1, _translate('Number of calibration points:'))
        self.ctrlNPoints = intctrl.IntCtrl(self, -1, value=8)

        self.labelScrN = wx.StaticText(self, -1, 'Screen number (primary is 1)')
        self.ctrlScrN = intctrl.IntCtrl(self, -1, value=1)

        self.labelStimSize = wx.StaticText(self, -1, _translate('Patch size (fraction of screen):'))
        self.ctrlStimSize = wx.TextCtrl(self, -1,'0.3')

        pad=5
        mainSizer.Add((0,0),1,wx.ALL, pad)
        mainSizer.Add(self.methodChoiceBx,1,wx.ALL, pad)
        mainSizer.Add(self.labelScrN,1,wx.ALL, pad)
        mainSizer.Add( self.ctrlScrN,1,wx.ALL, pad)
        mainSizer.Add(self.labelNPoints,1,wx.ALL, pad)
        mainSizer.Add( self.ctrlNPoints,1,wx.ALL, pad)
        mainSizer.Add(self.labelStimSize,1,wx.ALL, pad)
        mainSizer.Add( self.ctrlStimSize,1,wx.ALL, pad)
        mainSizer.Add((0,0),1,wx.ALL, pad)
        mainSizer.Add(self.ctrlUseBits,1,wx.ALL, pad)

        btnOK = wx.Button(self, wx.ID_OK, _translate(" OK "))
        btnOK.SetDefault()
        mainSizer.Add(btnOK,1,wx.TOP|wx.BOTTOM|wx.ALIGN_RIGHT, pad)
        btnCANC = wx.Button(self, wx.ID_CANCEL, _translate(" Cancel "))
        mainSizer.Add(btnCANC,1,wx.TOP|wx.BOTTOM|wx.RIGHT|wx.ALIGN_RIGHT, pad)
        self.Center()
        #mainSizer.Fit(self)
        self.SetAutoLayout(True)
        self.SetSizerAndFit(mainSizer)

    def onMethodChange(self, event):
        pass

class MonitorCenter(wx.App):
    def OnInit(self):
        frame = MainFrame(None, _translate('PsychoPy Monitor Center'))
        frame.Show(True)
        self.SetTopWindow(frame)
        return True

if __name__ == '__main__':
    app = MonitorCenter(0)
    app.MainLoop()
