from os import path
from _base import *
import os
from psychopy import logging

#this is not a standard component - it will appear on toolbar not in components panel

class SettingsComponent:
    """This component stores general info about how to run the experiment"""
    def __init__(self, parentName, exp, expName='', fullScr=True, winSize=[1024,768], screen=1, monitor='testMonitor', showMouse=False,
                 saveLogFile=True, showExpInfo=True, expInfo="{'participant':'', 'session':'001'}",units='use prefs',
                 logging='exp', color='$[0,0,0]', colorSpace='rgb', enableEscape=True, blendMode='avg',
                 saveXLSXFile=False, saveCSVFile=False, saveWideCSVFile=True, savePsydatFile=True,
                 savedDataFolder='', filename="'xxxx/%s_%s_%s' %(expInfo['participant'], expName, expInfo['date'])"):
        self.type='Settings'
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual', 'gui'])
        self.parentName=parentName
        self.url="http://www.psychopy.org/builder/settings.html"

        #if filename is the default value fetch the builder pref for the folder instead
        if filename.startswith("'xxxx"):
            filename = filename.replace("xxxx", self.exp.prefsBuilder['savedDataFolder'].strip())
        else:
            print filename[0:5]
        #params
        self.params={}
        self.order=['expName','Show info dlg','Experiment info',
            'Data filename',
            'Save excel file','Save csv file','Save wide csv file','Save psydat file','Save log file','logging level',
            'Monitor','Screen', 'Full-screen window','Window size (pixels)',
            'color','colorSpace','Units',]
        #basic params
        self.params['expName']=Param(expName, valType='str', allowedTypes=[],
            hint="Name of the entire experiment (taken by default from the filename on save)",
            label="Experiment name")
        self.params['Show info dlg']=Param(showExpInfo, valType='bool', allowedTypes=[],
            hint="Start the experiment with a dialog to set info (e.g.participant or condition)",
            categ='Basic')
        self.params['Enable Escape']=Param(enableEscape, valType='bool', allowedTypes=[],
            hint="Enable the <esc> key, to allow subjects to quit / break out of the experiment")
        self.params['Experiment info']=Param(expInfo, valType='code', allowedTypes=[],
            hint="The info to present in a dialog box. Right-click to check syntax and preview the dialog box.",
            categ='Basic')
        #data params
        self.params['Data filename']=Param(filename, valType='code', allowedTypes=[],
            hint="Code to create your custom file name base. Don't give a file extension - this will be added.",
            categ='Data')
        self.params['Full-screen window']=Param(fullScr, valType='bool', allowedTypes=[],
            hint="Run the experiment full-screen (recommended)",
            categ='Screen')
        self.params['Window size (pixels)']=Param(winSize, valType='code', allowedTypes=[],
            hint="Size of window (if not fullscreen)",
            categ='Screen')
        self.params['Screen']=Param(screen, valType='num', allowedTypes=[],
            hint="Which physical screen to run on (1 or 2)",
            categ='Screen')
        self.params['Monitor']=Param(monitor, valType='str', allowedTypes=[],
            categ="Screen",
            hint="Name of the monitor (from Monitor Center). Right-click to go there, then copy & paste a monitor name here.")
        self.params['color']=Param(color, valType='str', allowedTypes=[],
            hint="Color of the screen (e.g. black, $[1.0,1.0,1.0], $variable. Right-click to bring up a color-picker.)",
            label="Color",
            categ='Screen')
        self.params['colorSpace']=Param(colorSpace, valType='str', allowedVals=['rgb','dkl','lms'],
            hint="Needed if color is defined numerically (see PsychoPy documentation on color spaces)",
            categ="Screen")
        self.params['Units']=Param(units, valType='str', allowedTypes=[],
            allowedVals=['use prefs', 'deg','pix','cm','norm','height'],
            hint="Units to use for window/stimulus coordinates (e.g. cm, pix, deg)",
            categ='Screen')
        self.params['blendMode']=Param(blendMode, valType='str', allowedTypes=[],
            label='Blend mode',
            allowedVals=['add','avg'],
            hint="Should new stimuli be added or averaged with the stimuli that have been drawn already",
            categ='Screen')
        self.params['Show mouse']=Param(showMouse, valType='bool', allowedTypes=[],
            hint="Should the mouse be visible on screen?",
            categ='Screen')
        self.params['Save log file']=Param(saveLogFile, valType='bool', allowedTypes=[],
            hint="Save a detailed log (more detailed than the excel/csv files) of the entire experiment",
            categ='Data')
        self.params['Save wide csv file']=Param(saveWideCSVFile, valType='bool', allowedTypes=[],
            hint="Save data from loops in comma-separated-value (.csv) format for maximum portability",
            label="Save csv file (trial-by-trial)",
            categ='Data')
        self.params['Save csv file']=Param(saveCSVFile, valType='bool', allowedTypes=[],
            hint="Save data from loops in comma-separated-value (.csv) format for maximum portability",
            label="Save csv file (summaries)",
            categ='Data')
        self.params['Save excel file']=Param(saveXLSXFile, valType='bool', allowedTypes=[],
            hint="Save data from loops in Excel (.xlsx) format",
            categ='Data')
        self.params['Save psydat file']=Param(savePsydatFile, valType='bool', allowedVals=[True],
            hint="Save data from loops in psydat format. This is useful for python programmers to generate analysis scripts.",
            categ='Data')
        self.params['logging level']=Param(logging, valType='code',
            allowedVals=['error','warning','data','exp','info','debug'],
            hint="How much output do you want in the log files? ('error' is fewest messages, 'debug' is most)",
            label="Logging level",
            categ='Data')
    def getType(self):
        return self.__class__.__name__
    def getShortType(self):
        return self.getType().replace('Component','')
    def getSaveDataDir(self):
        if 'Saved data folder' in self.params:
            #we have a param for the folder (deprecated since 1.80)
            saveToDir = self.params['Saved data folder'].val.strip()
            if not saveToDir: #it was blank so try preferences
                saveToDir = self.exp.prefsBuilder['savedDataFolder'].strip()
                if not saveToDir: #still blank so just use 'data' folder
                    saveToDir = 'data'
        else:
            saveToDir = os.path.split(self.params['Data filename'].val)[0]
        return saveToDir
    def writeStartCode(self,buff):
        buff.writeIndented("# Store info about the experiment session\n")
        if self.params['expName'].val in [None,'']:
            expName = ''
        else:
            buff.writeIndented("expName = %s  # from the Builder filename that created this script\n" %(self.params['expName']))
        expInfo = self.params['Experiment info'].val.strip()
        if not len(expInfo):
            expInfo = '{}'
        try:
            expInfoDict = eval('dict(' + expInfo + ')')
        except SyntaxError, err:
            logging.error('Builder Expt: syntax error in "Experiment info" settings (expected a dict)')
            raise SyntaxError, 'Builder: error in "Experiment info" settings (expected a dict)'
        buff.writeIndented("expInfo = %s\n" % expInfo)
        if self.params['Show info dlg'].val:
            buff.writeIndented("dlg = gui.DlgFromDict(dictionary=expInfo, title=expName)\n")
            buff.writeIndented("if dlg.OK == False: core.quit()  # user pressed cancel\n")
        buff.writeIndented("expInfo['date'] = data.getDateStr()  # add a simple timestamp\n")
        buff.writeIndented("expInfo['expName'] = expName\n")
        level=self.params['logging level'].val.upper()

        saveToDir = self.getSaveDataDir()
        buff.writeIndentedLines("\n# Setup filename for saving\n")
        #deprecated code: before v1.80.00 we had 'Saved data folder' param but fairly fixed filename
        if 'Saved data folder' in self.params:
            participantField=''
            for field in ['participant','Participant', 'Subject', 'Observer']:
                if field in expInfoDict:
                    participantField=field
                    self.params['Data filename'].val = repr(saveToDir) + \
                            " + os.path.sep + '%s_%s' %(expInfo['" + field + "'], expInfo['date'])"
                    break
            if not participantField: #we didn't find a participant-type field so skip that part of filename
                self.params['Data filename'].val = repr(saveToDir) + " + os.path.sep + expInfo['date']"
            del self.params['Saved data folder'] #so that we don't overwrite users changes doing this again

        #now write that data file name to the script
        buff.writeIndented("filename = %s\n" %self.params['Data filename'])

        #set up the ExperimentHandler
        buff.writeIndentedLines("\n# An ExperimentHandler isn't essential but helps with data saving\n")
        buff.writeIndented("thisExp = data.ExperimentHandler(name=expName, version='',\n")
        buff.writeIndented("    extraInfo=expInfo, runtimeInfo=None,\n")
        buff.writeIndented("    originPath=%s,\n" %repr(self.exp.expPath))
        buff.writeIndented("    savePickle=%(Save psydat file)s, saveWideText=%(Save wide csv file)s,\n" %self.params)
        buff.writeIndented("    dataFileName=filename)\n")

        if self.params['Save log file'].val:
            buff.writeIndented("#save a log file for detail verbose info\n")
            buff.writeIndented("logFile = logging.LogFile(filename+'.log', level=logging.%s)\n" %(level))
        buff.writeIndented("logging.console.setLevel(logging.WARNING)  # this outputs to the screen, not a file\n")

        if self.exp.settings.params['Enable Escape'].val:
            buff.writeIndentedLines("\nendExpNow = False  # flag for 'escape' or other condition => quit the exp\n")

    def writeWindowCode(self,buff):
        """ setup the window code
        """
        buff.writeIndentedLines("\n# Setup the Window\n")
        #get parameters for the Window
        fullScr = self.params['Full-screen window'].val
        allowGUI = (not bool(fullScr)) or bool(self.params['Show mouse'].val) #if fullscreen then hide the mouse, unless its requested explicitly
        allowStencil = False
        for thisRoutine in self.exp.routines.values(): #NB routines is a dict
           for thisComp in thisRoutine: #a single routine is a list of components
               if thisComp.type=='Aperture': allowStencil = True
               if thisComp.type=='RatingScale': allowGUI = True # to have a mouse; BUT might not want it shown in other routines

        requestedScreenNumber = int(self.params['Screen'].val)
        if requestedScreenNumber > wx.Display.GetCount():
            logging.warn("Requested screen can't be found. Writing script using first available screen.")
            screenNumber = 0
        else:
            screenNumber = requestedScreenNumber-1 #computer has 1 as first screen

        if fullScr:
            size = wx.Display(screenNumber).GetGeometry()[2:4]
        else:
            size=self.params['Window size (pixels)']
        buff.writeIndented("win = visual.Window(size=%s, fullscr=%s, screen=%s, allowGUI=%s, allowStencil=%s,\n" %
                           (size, fullScr, screenNumber, allowGUI, allowStencil))
        buff.writeIndented("    monitor=%(Monitor)s, color=%(color)s, colorSpace=%(colorSpace)s,\n" %(self.params))
        if self.params['blendMode'].val:
            buff.writeIndented("    blendMode=%(blendMode)s, useFBO=True,\n" %(self.params))

        if self.params['Units'].val=='use prefs':
            buff.write("    )\n")
        else:
            buff.write("    units=%s)\n" %self.params['Units'])

        if 'microphone' in self.exp.psychopyLibs: # need a pyo Server
            buff.writeIndentedLines("\n# Enable sound input/output:\n"+
                                "microphone.switchOn()\n")

        buff.writeIndented("# store frame rate of monitor if we can measure it successfully\n")
        buff.writeIndented("expInfo['frameRate']=win.getActualFrameRate()\n")
        buff.writeIndented("if expInfo['frameRate']!=None:\n")
        buff.writeIndented("    frameDur = 1.0/round(expInfo['frameRate'])\n")
        buff.writeIndented("else:\n")
        buff.writeIndented("    frameDur = 1.0/60.0 # couldn't get a reliable measure so guess\n")

    def writeEndCode(self,buff):
        """write code for end of experiment (e.g. close log file)
        """
        buff.writeIndented("win.close()\n")
        buff.writeIndented("core.quit()\n")
