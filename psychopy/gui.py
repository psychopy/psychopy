"""To build simple dialogues etc. (requires wxPython)
"""
# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).
from psychopy import log
#from wxPython import wx
import wx
import numpy
import string, os

OK = wx.ID_OK

class Dlg(wx.Dialog):
    """A simple dialogue box. You can add text or input boxes 
    (sequentially) and then retrieve the values.
    
    see also the function *dlgFromDict* for an **even simpler** version
    
    **Example:**    ::
        
        from psychopy import gui
        
        myDlg = gui.Dlg(title="JWP's experiment")
        myDlg.addText('Subject info')
        myDlg.addField('Name:')
        myDlg.addField('Age:', 21)
        myDlg.addText('Experiment Info')
        myDlg.addField('Grating Ori:',45)
        if myDlg.show()==gui.OK:
            thisInfo = myDlg.data
            print thisInfo
        else: print 'user cancelled'
    """
    def __init__(self,title='PsychoPy dialogue',
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT):
        style=style|wx.RESIZE_BORDER
        try:
            wx.Dialog.__init__(self, None,-1,title,pos,size,style)
        except:
            global app
            app = wx.PySimpleApp()
            wx.Dialog.__init__(self, None,-1,title,pos,size,style)
        self.inputFields = []
        self.inputFieldTypes= []
        self.inputFieldNames= []
        self.data = []
        #prepare a frame in which to hold objects
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        #self.addText('')#insert some space at top of dialogue
        self.Center()
    def addText(self, text):
        textLength = wx.Size(8*len(text)+16, 25)
        myTxt = wx.StaticText(self,-1,
                                label=text,
                                style=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL,
                                size=textLength)
        self.sizer.Add(myTxt,1,wx.ALIGN_CENTER)
        
    def addField(self, label='', initial=''):
        """
        Adds a (labelled) input field to the dialogue box
        Returns a handle to the field (but not to the label).
        """
        self.inputFieldNames.append(label)
        self.inputFieldTypes.append(type(initial))
        if type(initial)==numpy.ndarray:
            initial=initial.tolist() #convert numpy arrays to lists
        labelLength = wx.Size(9*len(label)+16,25)#was 8*until v0.91.4
        container=wx.BoxSizer(wx.HORIZONTAL)
        inputLabel = wx.StaticText(self,-1,label,
                                        size=labelLength,
                                        style=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL)
        container.Add(inputLabel, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        inputBox = wx.TextCtrl(self,-1,str(initial),size=(5*len(str(initial))+16,25))
        container.Add(inputBox,1)
        self.sizer.Add(container, 1, wx.ALIGN_CENTER)
        
        self.inputFields.append(inputBox)#store this to get data back on OK
        return inputBox
    
    def addFixedField(self,label='',value=''):
        """Adds a field to the dialogue box (like addField) but
        the field cannot be edited. e.g. Display experiment
        version.
        """
        thisField = self.addField(label,value)
        thisField.Disable()
        return thisField
        
    def show(self):
        #add buttons for OK and Cancel
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        OK = wx.Button(self, wx.ID_OK, " OK ")
        OK.SetDefault()
        buttons.Add(OK)	
        CANCEL = wx.Button(self, wx.ID_CANCEL, " Cancel ")
        buttons.Add(CANCEL)
        self.sizer.Add(buttons,1,flag=wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM,border=5)
        
        self.SetSizerAndFit(self.sizer)
        if self.ShowModal() == wx.ID_OK:
            self.data=[]
            #get data from input fields
            for n in range(len(self.inputFields)):
                thisVal = self.inputFields[n].GetValue()
                thisType= self.inputFieldTypes[n]
                #try to handle different types of input from strings
                log.debug("%s: %s" %(self.inputFieldNames[n], str(thisVal)))
                if thisType in [tuple,list,float,int]:
                    #probably a tuple or list
                    exec("self.data.append("+thisVal+")")#evaluate it
                elif thisType==numpy.ndarray:
                    exec("self.data.append(numpy.array("+thisVal+"))")
                elif thisType==str:#a num array or string?
                    self.data.append(thisVal)
                else:
                    log.warning('unknown type:'+self.inputFieldNames[n])
                    self.data.append(thisVal)
            self.OK=True
        else: 
            self.OK=False
        self.Destroy()
        #    global app
        #self.myApp.Exit()
       


class DlgFromDict(Dlg):
    """Creates a dialogue box that represents a dictionary of values.
    Any values changed by the user are change (in-place) by this 
    dialogue box.
    e.g.: 
    
    ::
    
        info = {'Observer':'jwp', 'GratingOri':45, 'ExpVersion': 1.1}
        infoDlg = gui.DlgFromDict(dictionary=info, title='TestExperiment', fixed=['ExpVersion'])
        if infoDlg.OK:
            print info
        else: print 'User Cancelled'
        
    In the code above, the contents of *info* will be updated to the values
    returned by the dialogue box. 
    
    If the user cancels (rather than pressing OK),
    then the dictionary remains unchanged. If you want to check whether
    the user hit OK, then check whether DlgFromDict.OK equals
    True or False    
    """
    def __init__(self, dictionary, title='',fixed=[]):
        Dlg.__init__(self, title)
        self.dictionary=dictionary
        keys = self.dictionary.keys()
        keys.sort()
        types=dict([])
        for field in keys:
            #DEBUG: print field, type(dictionary[field])
            types[field] = type(self.dictionary[field])
            if field in fixed:
                self.addFixedField(field,self.dictionary[field])
            else:
                self.addField(field,self.dictionary[field])
        #show it and collect data
        #tmp= wx.PySimpleApp()#this should have been done by Dlg ?
        self.show()
        if self.OK:
            for n,thisKey in enumerate(keys):
                self.dictionary[thisKey]=self.data[n]
        
def fileSaveDlg(initFilePath="", initFileName="", 
                prompt="Select file to save"):
    """A simple dialogue allowing access to the file system.
    (Useful in case you collect an hour of data and then try to 
    save to a non-existent directory!!)
    
    usage:
        validPathName = fileSaveDlg(initFilePath,initFileName)
    
    If initFilePath or initFileName are empty or invalid then
    current path and empty names are used to start search.
    
    If user cancels the None is returned.
    """
    allowed = "All files (*.*)|*.*"  #\
            #"txt (*.txt)|*.txt" \
            #"pickled files (*.pickle, *.pkl)|*.pickle" \
            #"shelved files (*.shelf)|*.shelf"
    tmpApp = wx.PySimpleApp()	
    dlg = wx.FileDialog(None,prompt, 
                          initFilePath, initFileName, allowed, wx.SAVE)
    if dlg.ShowModal() == OK:
        #get names of images and their directory
        outName = dlg.GetFilename()
        outPath = dlg.GetDirectory()
        dlg.Destroy()
        #tmpApp.Destroy() #this causes an error message for some reason
        fullPath = os.path.join(outPath, outName)
    else: fullPath = None
    return fullPath

def fileOpenDlg(tryFilePath="",
                tryFileName="",
                prompt="Select file to open"):
    """A simple dialogue allowing access to the file system.
    (Useful in case you collect an hour of data and then try to 
    save to a non-existent directory!!)
    
    usage:
        validPathName = fileSaveDlg(initFilePath,initFileName)
    
    If initFilePath or initFileName are empty or invalid then
    current path and empty names are used to start search.
    
    If user cancels the None is returned.
    """
    allowed = "PsychoPy Data (*.psydat)|*.psydat|"\
            "txt (*.txt,*.dlm)|*.txt|" \
            "pickled files (*.pickle, *.pkl)|*.pickle|" \
            "shelved files (*.shelf)|*.shelf|" \
            "All files (*.*)|*.*"
    tmpApp = wx.PySimpleApp()	
    dlg = wx.FileDialog(None, prompt,
                          tryFilePath, tryFileName, allowed, wx.OPEN|wx.FILE_MUST_EXIST|wx.MULTIPLE)
    if dlg.ShowModal() == OK:
        #get names of images and their directory
        fullPaths = dlg.GetPaths()
    else: fullPaths = None
    dlg.Destroy()
    return fullPaths
