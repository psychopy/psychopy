from os import path
from _base import *

#this is not a standard component - it will appear on toolbar not in components panel

class SettingsComponent:
    """This component stores general info about how to run the experiment"""
    def __init__(self, parentName, fullScr=True, winSize=[1024,768], screen=1, 
                 saveLogFile=True, showExpInfo=True, expInfo="{'participant':001, 'session':001}"):
        self.type='Settings'
        self.params={}
        self.order=['Screen', 'Full-screen window','Window size (pixels)']
        self.params['Full-screen window']=Param(fullScr, valType='bool', allowedTypes=[],
            hint="Run the experiment full-screen (recommended)") 
        self.params['Window size (pixels)']=Param(winSize, valType='code', allowedTypes=[],
            hint="Size of window (if not fullscreen)") 
        self.params['Screen']=Param(screen, valType='num', allowedTypes=[],
            hint="Which physical screen to run on") 
        self.params['Save log file']=Param(saveLogFile, valType='bool', allowedTypes=[],
            hint="Save a detailed log (more detailed than the normal data file) of the entire experiment") 
        self.params['Show info dlg']=Param(showExpInfo, valType='bool', allowedTypes=[],
            hint="Start the experiment with a dialog to set info (e.g.participant or condition)")  
        self.params['Experiment info']=Param(expInfo, valType='code', allowedTypes=[],
            hint="A dictionary of info about the experiment, e.g. {'participant':001, 'session':001}") 
    def getType(self):
        return self.__class__.__name__
    def getShortType(self):
        return self.getType().replace('Component','')
    def writeStartCode(self):
        
        s.writeIndented("#setup files for saving\n")
        s.writeIndented("info={participant':'001'}\n")
        s.writeIndented("logFile=")
        s.writeIndented("date=data.getDateStr()#get a timestamp for running the exp\n")
        
        s.writeIndented("#setup the Window\n")
        s.writeIndented("win = visual.Window([400,400])\n")
    def writeEndCodeself(self):
        """write code for end of experiment (e.g. close log file)
        """