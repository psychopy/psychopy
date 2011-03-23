from os import path
from _base import *

#this is not a standard component - it will appear on toolbar not in components panel

class SettingsComponent:
    """This component stores general info about how to run the experiment"""
    def __init__(self, parentName, exp, fullScr=True, winSize=[1024,768], screen=1, monitor='testMonitor', showMouse=False,
                 saveLogFile=True, showExpInfo=True, expInfo="{'participant':'', 'session':'001'}",units='use prefs',
                 logging='exp', color='$[0,0,0]', colorSpace='rgb', saveXLSXFile=True, saveCSVFile=False, savePsydatFile=True):
        self.type='Settings'
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual', 'gui'])
        self.parentName=parentName
        self.url="http://www.psychopy.org/builder/settings.html"
        #params
        self.params={}
        self.order=['Show info dlg','Experiment info',
            'Save excel file','Save csv file','Save psydat file','Save log file','logging level',
            'Monitor','Screen', 'Full-screen window','Window size (pixels)',
            'color','colorSpace','Units',]
        self.params['Full-screen window']=Param(fullScr, valType='bool', allowedTypes=[],
            hint="Run the experiment full-screen (recommended)") 
        self.params['Window size (pixels)']=Param(winSize, valType='code', allowedTypes=[],
            hint="Size of window (if not fullscreen)") 
        self.params['Screen']=Param(screen, valType='num', allowedTypes=[],
            hint="Which physical screen to run on (1 or 2)")  
        self.params['Monitor']=Param(monitor, valType='str', allowedTypes=[],
            hint="Name of the monitor (must match one in Monitor Center)") 
        self.params['color']=Param(color, valType='str', allowedTypes=[],
            hint="Color of the screen (e.g. black, $[1.0,1.0,1.0], $variable)") 
        self.params['colorSpace']=Param(colorSpace, valType='str', allowedVals=['rgb','dkl','lms'],
            hint="Needed if color is defined numerically (see PsychoPy documentation on color spaces)") 
        self.params['Units']=Param(units, valType='str', allowedTypes=[],
            allowedVals=['use prefs', 'deg','pix','cm','norm'],
            hint="Units to use for window/stimulus coordinates (e.g. cm, pix, deg")
        self.params['Show mouse']=Param(showMouse, valType='bool', allowedTypes=[],
            hint="Should the mouse be visible on screen?") 
        self.params['Save log file']=Param(saveLogFile, valType='bool', allowedTypes=[],
            hint="Save a detailed log (more detailed than the excel/csv files) of the entire experiment")
        self.params['Save csv file']=Param(saveCSVFile, valType='bool', allowedTypes=[],
            hint="Save data from loops in comma-separated-value (.csv) format for maximu portability")
        self.params['Save excel file']=Param(saveXLSXFile, valType='bool', allowedTypes=[],
            hint="Save data from loops in Excel (.xlsx) format")
        self.params['Save psydat file']=Param(savePsydatFile, valType='bool', allowedTypes=[],
            hint="Save data from loops in psydat format. This is useful for python programmers to generate analysis scripts.")
        self.params['Show info dlg']=Param(showExpInfo, valType='bool', allowedTypes=[],
            hint="Start the experiment with a dialog to set info (e.g.participant or condition)")  
        self.params['Experiment info']=Param(expInfo, valType='code', allowedTypes=[],
            hint="A dictionary of info about the experiment, e.g. {'participant':001, 'session':001}") 
        self.params['logging level']=Param(logging, valType='code', 
            allowedVals=['error','warning','data','exp','info','debug'],
            hint="How much output do you want in the log files? ('error' is fewest messages, 'debug' is most)")
    def getType(self):
        return self.__class__.__name__
    def getShortType(self):
        return self.getType().replace('Component','')
    def writeStartCode(self,buff):
        buff.writeIndented("#store info about the experiment\n")
        buff.writeIndented("expName='%s'#from the Builder filename that created this script\n" %(self.exp.name))
        buff.writeIndented("expInfo=%s\n" %self.params['Experiment info'])
        if self.params['Show info dlg'].val:            
            buff.writeIndented("dlg=gui.DlgFromDict(dictionary=expInfo,title=expName)\n")
            buff.writeIndented("if dlg.OK==False: core.quit() #user pressed cancel\n")            
        buff.writeIndented("expInfo['date']=data.getDateStr()#add a simple timestamp\n")          
        buff.writeIndented("expInfo['expName']=expName\n")
        
        if self.params['Save log file'].val or self.params['Save csv file'].val or self.params['Save excel file'].val:
            buff.writeIndented("#setup files for saving\n")
            buff.writeIndented("if not os.path.isdir('data'):\n")
            buff.writeIndented("    os.makedirs('data')#if this fails (e.g. permissions) we will get error\n")
            if 'participant' in self.params['Experiment info'].val:
                buff.writeIndented("filename='data/%s_%s' %(expInfo['participant'], expInfo['date'])\n")
            else:
                buff.writeIndented("filename='data/%s' %(expInfo['date'])\n")
        #handle logging
        level=self.params['logging level'].val.upper()
        buff.writeIndented("psychopy.log.console.setLevel(psychopy.log.warning)#this outputs to the screen, not a file\n")
        if self.params['Save log file']:
            buff.writeIndented("logFile=psychopy.log.LogFile(filename+'.log', level=psychopy.log.%s)\n" %(level))
        
        buff.writeIndented("\n#setup the Window\n")
        #get parameters for the Window
        fullScr = self.params['Full-screen window'].val
        allowGUI = (not bool(fullScr)) or bool(self.params['Show mouse'].val) #if fullscreen then hide the mouse, unless its requested explicitly
        allowStencil = False 
        for thisRoutine in self.exp.routines.values(): #NB routines is a dict
           for thisComp in thisRoutine: #a single routine is a list of components
               if thisComp.type=='Aperture': allowStencil = True
               if thisComp.type=='RatingScale': allowGUI = True # to have a mouse; BUT might not want it shown in other routines
        size=self.params['Window size (pixels)']
        screenNumber = int(self.params['Screen'].val)-1 #computer has 1 as first screen
        buff.writeIndented("win = visual.Window(size=%s, fullscr=%s, screen=%s, allowGUI=%s, allowStencil=%s,\n" %
                           (size, fullScr, screenNumber, allowGUI, allowStencil))
        buff.writeIndented("    monitor=%(Monitor)s, color=%(color)s, colorSpace=%(colorSpace)s" %(self.params))
        
        if self.params['Units'].val=='use prefs': unitsCode=""
        else: unitsCode=", units=%s" %self.params['Units']
        buff.write(unitsCode+")\n")
        
    def writeEndCode(self,buff):
        """write code for end of experiment (e.g. close log file)
        """
        buff.writeIndented("\n#Shutting down:\n")
        
        buff.writeIndented("win.close()\n")
        buff.writeIndented("core.quit()\n")
