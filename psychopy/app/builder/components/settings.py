from os import path
from _base import *

#this is not a standard component - it will appear on toolbar not in components panel

class SettingsComponent:
    """This component stores general info about how to run the experiment"""
    def __init__(self, parentName, exp, fullScr=True, winSize=[1024,768], screen=1, monitor='testMonitor',
                 saveLogFile=True, showExpInfo=True, expInfo="{'participant':001, 'session':001}",
                 logging='warning'):
        self.type='Settings'
        self.exp=exp#so we can access the experiment if necess
        self.exp.requirePsychopyLibs(['visual', 'gui'])
        self.parentName=parentName
        #params
        self.params={}
        self.order=['Screen', 'Full-screen window','Window size (pixels)']
        self.params['Full-screen window']=Param(fullScr, valType='bool', allowedTypes=[],
            hint="Run the experiment full-screen (recommended)") 
        self.params['Window size (pixels)']=Param(winSize, valType='code', allowedTypes=[],
            hint="Size of window (if not fullscreen)") 
        self.params['Screen']=Param(screen, valType='num', allowedTypes=[],
            hint="Which physical screen to run on (1 or 2)")  
        self.params['Monitor']=Param(monitor, valType='str', allowedTypes=[],
            hint="Name of the monitor (must match one in Monitor Center)") 
        self.params['Units']=Param(screen, valType='str', allowedTypes=[],
            allowedVals=['use prefs', 'deg','pix','cm','norm'],
            hint="Units to use for window/stimulus coordinates (e.g. cm, pix, deg") 
        self.params['Save log file']=Param(saveLogFile, valType='bool', allowedTypes=[],
            hint="Save a detailed log (more detailed than the normal data file) of the entire experiment") 
        self.params['Show info dlg']=Param(showExpInfo, valType='bool', allowedTypes=[],
            hint="Start the experiment with a dialog to set info (e.g.participant or condition)")  
        self.params['Experiment info']=Param(expInfo, valType='code', allowedTypes=[],
            hint="A dictionary of info about the experiment, e.g. {'participant':001, 'session':001}") 
        self.params['logging level']=Param(logging, valType='code', 
            allowedVals=['error','warning','info','debug'],
            hint="How much output do you want from the script? ('error' is fewest messages, 'debug' is most)")
    def getType(self):
        return self.__class__.__name__
    def getShortType(self):
        return self.getType().replace('Component','')
    def writeStartCode(self, buff):
        
        buff.writeIndented("#store info about the experiment\n")
        buff.writeIndented("expName='%s'#from the Builder filename that created this script\n" %(self.exp.name))
        buff.writeIndented("expInfo=%s\n" %self.params['Experiment info'])
        if self.params['Show info dlg'].val:            
            buff.writeIndented("dlg=gui.DlgFromDict(dictionary=expInfo,title=expName)\n")
            buff.writeIndented("if dlg.OK==False: core.quit() #user pressed cancel\n")            
        buff.writeIndented("expInfo['date']=data.getDateStr()#add a simple timestamp\n")          
        buff.writeIndented("expInfo['expName']=expName\n")
        
        if self.params['Save log file']:
            buff.writeIndented("#setup files for saving\n")
            buff.writeIndented("if not os.path.isdir('data'):\n")
            buff.writeIndented("    os.makedirs('data')#if this fails we will get error\n")
            if 'participant' in self.params['Experiment info'].val:
                buff.writeIndented("filename= 'data/%s_%s' %(expInfo['participant'], expInfo['date'])\n")
            buff.writeIndented("logFile=open(filename+'.log', 'w')\n")
            buff.writeIndented("psychopy.log.console.setLevel(psychopy.log.%s)#this outputs to the screen, not a file\n" %(self.params['logging level'].val.upper()))
        
        buff.writeIndented("\n#setup the Window\n")
        #get parameters for the Window
        size=self.params['Window size (pixels)']#
        fullScr = self.params['Full-screen window']
        monitor=self.params['Monitor']
        if self.params['Units'].val=='use prefs': unitsCode=""
        else: unitsCode=", units=%s" %self.params['Units'].val
        screenNumber = int(self.params['Screen'].val)-1#computer has 1 as first screen
        buff.writeIndented("win = visual.Window(size=%s, fullscr=%s, screen=%s,\n" %(size, fullScr, screenNumber))
        buff.writeIndented("    monitor=%s%s)\n" %(self.params['Monitor'], unitsCode))
        
    def writeEndCode(self, buff):
        """write code for end of experiment (e.g. close log file)
        """
        buff.writeIndented("logFile.close()")