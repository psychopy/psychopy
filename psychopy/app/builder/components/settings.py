from os import path
from _base import *
import os
from psychopy import logging

#this is not a standard component - it will appear on toolbar not in components panel

class SettingsComponent:
    """This component stores general info about how to run the experiment"""
    def __init__(self, parentName, exp, expName='', fullScr=True, winSize=[1024,768], screen=1, monitor='testMonitor', showMouse=False,
                 saveLogFile=True, showExpInfo=True, expInfo="{'participant':'', 'session':'001'}",units='use prefs',
                 logging='exp', color='$[0,0,0]', colorSpace='rgb', enableEscape=True,
                 saveXLSXFile=False, saveCSVFile=False, saveWideCSVFile=True, savePsydatFile=True,
                 savedDataFolder=''):
        self.type='Settings'
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual', 'gui'])
        self.parentName=parentName
        self.url="http://www.psychopy.org/builder/settings.html"
        #params
        self.params={}
        self.order=['expName','Show info dlg','Experiment info',
            'Save excel file','Save csv file','Save wide csv file','Save psydat file','Save log file','logging level',
            'Monitor','Screen', 'Full-screen window','Window size (pixels)',
            'color','colorSpace','Units',]
        self.params['expName']=Param(expName, valType='str', allowedTypes=[],
            hint="Name of the entire experiment (taken by default from the filename on save)",
            label="Experiment name")
        self.params['Full-screen window']=Param(fullScr, valType='bool', allowedTypes=[],
            hint="Run the experiment full-screen (recommended)")
        self.params['Window size (pixels)']=Param(winSize, valType='code', allowedTypes=[],
            hint="Size of window (if not fullscreen)")
        self.params['Screen']=Param(screen, valType='num', allowedTypes=[],
            hint="Which physical screen to run on (1 or 2)")
        self.params['Monitor']=Param(monitor, valType='str', allowedTypes=[],
            hint="Name of the monitor (from Monitor Center). Right-click to go there, then copy & paste a monitor name here.")
        self.params['color']=Param(color, valType='str', allowedTypes=[],
            hint="Color of the screen (e.g. black, $[1.0,1.0,1.0], $variable. Right-click to bring up a color-picker.)",
            label="Color")
        self.params['colorSpace']=Param(colorSpace, valType='str', allowedVals=['rgb','dkl','lms'],
            hint="Needed if color is defined numerically (see PsychoPy documentation on color spaces)")
        self.params['Units']=Param(units, valType='str', allowedTypes=[],
            allowedVals=['use prefs', 'deg','pix','cm','norm'],
            hint="Units to use for window/stimulus coordinates (e.g. cm, pix, deg")
        self.params['Show mouse']=Param(showMouse, valType='bool', allowedTypes=[],
            hint="Should the mouse be visible on screen?")
        self.params['Save log file']=Param(saveLogFile, valType='bool', allowedTypes=[],
            hint="Save a detailed log (more detailed than the excel/csv files) of the entire experiment")
        self.params['Save wide csv file']=Param(saveWideCSVFile, valType='bool', allowedTypes=[],
            hint="Save data from loops in comma-separated-value (.csv) format for maximum portability",
            label="Save csv file (trial-by-trial)")
        self.params['Save csv file']=Param(saveCSVFile, valType='bool', allowedTypes=[],
            hint="Save data from loops in comma-separated-value (.csv) format for maximum portability",
            label="Save csv file (summaries)")
        self.params['Save excel file']=Param(saveXLSXFile, valType='bool', allowedTypes=[],
            hint="Save data from loops in Excel (.xlsx) format")
        self.params['Save psydat file']=Param(savePsydatFile, valType='bool', allowedVals=[True],
            hint="Save data from loops in psydat format. This is useful for python programmers to generate analysis scripts.")
        self.params['Saved data folder']=Param(savedDataFolder, valType='code', allowedTypes=[],
            hint="Name of the folder in which to save data and log files (blank defaults to the builder pref)")
        self.params['Show info dlg']=Param(showExpInfo, valType='bool', allowedTypes=[],
            hint="Start the experiment with a dialog to set info (e.g.participant or condition)")
        self.params['Enable Escape']=Param(enableEscape, valType='bool', allowedTypes=[],
            hint="Enable the <esc> key, to allow subjects to quit / break out of the experiment")
        self.params['Experiment info']=Param(expInfo, valType='code', allowedTypes=[],
            hint="The info to present in a dialog box. Right-click to check syntax and preview the dialog box.")
        self.params['logging level']=Param(logging, valType='code',
            allowedVals=['error','warning','data','exp','info','debug'],
            hint="How much output do you want in the log files? ('error' is fewest messages, 'debug' is most)",
            label="Logging level")
    def getType(self):
        return self.__class__.__name__
    def getShortType(self):
        return self.getType().replace('Component','')
    def getSaveDataDir(self):
        saveToDir = self.params['Saved data folder'].val.strip()
        if not saveToDir:
            saveToDir = self.exp.prefsBuilder['savedDataFolder'].strip()
            if not saveToDir:
                saveToDir = 'data'
        return saveToDir
    def writeStartCode(self,buff):
        buff.writeIndented("# Store info about the experiment session\n")
        if self.params['expName'].val in [None,'']:
            expName = ''
        else:
            buff.writeIndented("expName = %s  # from the Builder filename that created this script\n" %(self.params['expName']))
        expInfo = self.params['Experiment info'].val.strip()
        if not len(expInfo): expInfo = '{}'
        try: eval('dict('+expInfo+')')
        except SyntaxError, err:
            logging.error('Builder Expt: syntax error in "Experiment info" settings (expected a dict)')
            raise SyntaxError, 'Builder: error in "Experiment info" settings (expected a dict)'
        buff.writeIndented("expInfo = %s\n" % expInfo)
        if self.params['Show info dlg'].val:
            buff.writeIndented("dlg = gui.DlgFromDict(dictionary=expInfo, title=expName)\n")
            buff.writeIndented("if dlg.OK == False: core.quit()  # user pressed cancel\n")
        buff.writeIndented("expInfo['date'] = data.getDateStr()  # add a simple timestamp\n")
        buff.writeIndented("expInfo['expName'] = expName\n")
        saveToDir = self.getSaveDataDir()
        level=self.params['logging level'].val.upper()

        buff.writeIndentedLines("\n# Setup files for saving\n")
        buff.writeIndented("if not os.path.isdir('%s'):\n" % saveToDir)
        buff.writeIndented("    os.makedirs('%s')  # if this fails (e.g. permissions) we will get error\n" % saveToDir)
        if 'participant' in self.params['Experiment info'].val:
            buff.writeIndented("filename = '" + saveToDir + "' + os.path.sep + '%s_%s' %(expInfo['participant'], expInfo['date'])\n")
        elif 'Participant' in self.params['Experiment info'].val:
            buff.writeIndented("filename = '" + saveToDir + "' + os.path.sep + '%s_%s' %(expInfo['Participant'], expInfo['date'])\n")
        elif 'Subject' in self.params['Experiment info'].val:
            buff.writeIndented("filename = '" + saveToDir + "' + os.path.sep + '%s_%s' %(expInfo['Subject'], expInfo['date'])\n")
        elif 'Observer' in self.params['Experiment info'].val:
            buff.writeIndented("filename = '" + saveToDir + "' + os.path.sep + '%s_%s' %(expInfo['Observer'], expInfo['date'])\n")
        else:
            buff.writeIndented("filename = '" + saveToDir + "' + os.path.sep + '%s' %(expInfo['date'])\n")

        if self.params['Save log file'].val:
            buff.writeIndented("logFile = logging.LogFile(filename+'.log', level=logging.%s)\n" %(level))

        buff.writeIndented("logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file\n")

        #set up the ExperimentHandler
        buff.writeIndentedLines("\n# An ExperimentHandler isn't essential but helps with data saving\n")
        buff.writeIndented("thisExp = data.ExperimentHandler(name=expName, version='',\n")
        buff.writeIndented("    extraInfo=expInfo, runtimeInfo=None,\n")
        buff.writeIndented("    originPath=%s,\n" %repr(self.exp.expPath))
        buff.writeIndented("    savePickle=%(Save psydat file)s, saveWideText=%(Save wide csv file)s,\n" %self.params)
        buff.writeIndented("    dataFileName=filename)\n")

        buff.writeIndentedLines("\n# Setup the Window\n")
        #get parameters for the Window
        fullScr = self.params['Full-screen window'].val
        allowGUI = (not bool(fullScr)) or bool(self.params['Show mouse'].val) #if fullscreen then hide the mouse, unless its requested explicitly
        allowStencil = False
        for thisRoutine in self.exp.routines.values(): #NB routines is a dict
           for thisComp in thisRoutine: #a single routine is a list of components
               if thisComp.type=='Aperture': allowStencil = True
               if thisComp.type=='RatingScale': allowGUI = True # to have a mouse; BUT might not want it shown in other routines

        screenNumber = int(self.params['Screen'].val)-1 #computer has 1 as first screen
        if fullScr:
            size = wx.Display(screenNumber).GetGeometry()[2:4]
        else:
            size=self.params['Window size (pixels)']
        buff.writeIndented("win = visual.Window(size=%s, fullscr=%s, screen=%s, allowGUI=%s, allowStencil=%s,\n" %
                           (size, fullScr, screenNumber, allowGUI, allowStencil))
        buff.writeIndented("    monitor=%(Monitor)s, color=%(color)s, colorSpace=%(colorSpace)s" %(self.params))

        if self.params['Units'].val=='use prefs': unitsCode=""
        else: unitsCode=", units=%s" %self.params['Units']
        buff.write(unitsCode+")\n")

        if 'microphone' in self.exp.psychopyLibs: # need a pyo Server
            buff.writeIndentedLines("\n# Enable sound input/output:\n"+
                                "microphone.switchOn()\n")
    def writeEndCode(self,buff):
        """write code for end of experiment (e.g. close log file)
        """
        buff.writeIndentedLines("\n# Shutting down:\n")
        if 'microphone' in self.exp.psychopyLibs:
            buff.writeIndented("microphone.switchOff()\n")
        buff.writeIndented("win.close()\n")
        buff.writeIndented("core.quit()\n")
