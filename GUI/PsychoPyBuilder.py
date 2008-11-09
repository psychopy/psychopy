import wx
import wx.lib.scrolledpanel as scrolled
import wx.aui
import sys
import ExperimentObjects, numpy

eventTypes=['Patch','Text','Movie','Sound','Mouse','Keyboard']

class FlowPanel(wx.ScrolledWindow):
    def __init__(self, parent, id=-1,size = wx.DefaultSize):
        """A panel that shows how the procedures will fit together
        """
        wx.ScrolledWindow.__init__(self, parent, id, (0, 0), size=size)
        self.parent=parent   
        self.needUpdate=True
        self.maxWidth  = 1000
        self.maxHeight = 200
        
        self.btnSizer = wx.BoxSizer(wx.VERTICAL)
        self.btnInsertProc = wx.Button(self,-1,'Insert Procedure')   
        self.btnInsertLoop = wx.Button(self,-1,'Insert Loop')    
        
        #bind events     
        self.Bind(wx.EVT_BUTTON, self.onInsertProc,self.btnInsertProc)  
        self.Bind(wx.EVT_PAINT, self.onPaint)
        
        self.btnSizer.Add(self.btnInsertProc)
        self.btnSizer.Add(self.btnInsertLoop)        
        self.SetSizer(self.btnSizer)
        
        #self.SetAutoLayout(True)
        self.SetVirtualSize((self.maxWidth, self.maxHeight))
        self.SetScrollRate(20,20)
        
    def onInsertProc(self, evt):
        exp = self.parent.exp
        
        #bring up listbox to choose the procedure to add and/or create a new one
        addProcDlg = DlgAddProcToFlow(parent=self.parent)
        if addProcDlg.ShowModal():
            newProc = exp.procs[addProcDlg.proc]#fetch the proc with the returned name
            exp.flow.addProcedure(newProc, pos=1)        
        self.needUpdate=True
        self.Refresh()
        evt.Skip()
        
    def onPaint(self, evt=None):
        #check if we need to do drawing

        expFlow = self.parent.exp.flow #retrieve the current flow from the experiment
        
        #must create a fresh drawing context each frame (not store one)
        pdc = wx.PaintDC(self)
        try:
            dc = wx.GCDC(pdc)
        except:
            dc = pdc
        
        #dc.BeginDrawing()
        #dc.Clear()
        
        #draw the main time line
        linePos = 80
        dc.DrawLine(x1=100,y1=linePos,x2=500,y2=linePos)
        
        #step through objects in flow
        currX=120; gap=20
        loopInits = []
        loopTerms = []
        for entry in expFlow:
            if entry.getType()=='LoopInitiator':                
                loopInits.append(currX)
            if entry.getType()=='LoopTerminator':
                self.drawLoopAttach(dc,pos=[currX,linePos])
                loopTerms.append(currX)
            if entry.getType()=='Procedure':
                currX = self.drawFlowBox(dc,entry.name, pos=[currX,linePos-40])
            currX+=gap
            
        loopTerms.reverse()#reverse the terminators, so that last term goes with first init   
        for n in range(len(loopInits)):
            self.drawFlowLoop(dc,'Flow1',startX=loopInits[n],endX=loopTerms[n],base=linePos,height=20)
            self.drawLoopAttach(dc,pos=[loopInits[n],linePos])
            self.drawLoopAttach(dc,pos=[loopTerms[n],linePos])
        self.needUpdate=False
        
    def drawLoopAttach(self, dc, pos):
        #draws a spot that a loop will later attach to
        dc.SetBrush(wx.Brush(wx.Colour(100,100,100, 250)))
        dc.SetPen(wx.Pen(wx.Colour(0,0,0, wx.ALPHA_OPAQUE)))
        dc.DrawCirclePoint(pos,5)
    def drawFlowBox(self,dc, name,rgb=[200,50,50],pos=[0,0]):
        font = dc.GetFont()
        font.SetPointSize(24)
        r, g, b = rgb

        #get size based on text
        dc.SetFont(font)
        w,h = dc.GetFullTextExtent(name)[0:2]
        pad = 20
        #draw box
        rect = wx.Rect(pos[0], pos[1], w+pad,h+pad) 
        endX = pos[0]+w+20
        #the edge should match the text
        dc.SetPen(wx.Pen(wx.Colour(r, g, b, wx.ALPHA_OPAQUE)))
        #for the fill, draw once in white near-opaque, then in transp colour
        dc.SetBrush(wx.Brush(wx.Colour(255,255,255, 250)))
        dc.DrawRoundedRectangleRect(rect, 8)   
        dc.SetBrush(wx.Brush(wx.Colour(r,g,b,50)))
        dc.DrawRoundedRectangleRect(rect, 8)   
        #draw text        
        dc.SetTextForeground(rgb) 
        dc.DrawText(name, pos[0]+pad/2, pos[1]+pad/2)
        return endX
    def drawFlowLoop(self,dc,name,startX,endX,base,height,rgb=[200,50,50]):
        xx = [endX,  endX,   endX,   endX-5, endX-10, startX+10,startX+5, startX, startX, startX]
        yy = [base,height+10,height+5,height, height, height,  height,  height+5, height+10, base]
        pts=[]
        for n in range(len(xx)):
            pts.append([xx[n],yy[n]])
        dc.DrawSpline(pts)
class DlgAddProcToFlow(wx.Dialog):
    def __init__(self, parent, id=-1, title='Add a procedure to the flow',
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self,parent,id,title,pos,size,style)
        self.parent=parent
        
        # setup choices of procedures
        procChoices=['Select a procedure']
        procChoices.extend(self.parent.exp.procs.keys())
        self.choiceProc=wx.ComboBox(parent=self,id=-1,value='Select a procedure',
                            choices=procChoices, style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.EvtProcChoice, self.choiceProc)
        
        #add OK, cancel
        self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btnOK = wx.Button(self, wx.ID_OK)
        self.btnOK.Enable(False)
        self.btnCancel = wx.Button(self, wx.ID_CANCEL)
        self.btnSizer.Add(self.btnOK)
        self.btnSizer.Add(self.btnCancel)        
        
        #put into main sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.choiceProc)
        self.sizer.Add(self.btnSizer)
        self.SetSizerAndFit(self.sizer)
        
        self.proc=None
        
    def EvtProcChoice(self, event):
        name = event.GetString()
        
        if event.GetString() == 'Select a procedure':
            self.btnOK.Enable(False)
            self.proc=None
        else:
            self.btnOK.Enable(True)
            self.proc=event.GetString()  
                    
class ProcedurePage(wx.Panel):
    """A frame to represent a single procedure
    """
    def __init__(self, parent, proc):
        wx.Panel.__init__(self,parent)
        self.parent=parent       
        self.proc=proc
        
    def onPaint(self, evt=None):
        
        #must create a fresh drawing context each frame (not store one)
        pdc = wx.PaintDC(self)
        try:
            dc = wx.GCDC(pdc)
        except:
            dc = pdc
        
        for event in self.proc:
            self.drawEvent(event)
    def drawEvent(event):
        bitmap = event
class ProceduresNotebook(wx.aui.AuiNotebook):
    """A notebook that stores one or more procedures
    """
    def __init__(self, parent, id=-1):
        self.parent=parent
        wx.aui.AuiNotebook.__init__(self, parent, id)
        exp=self.parent.exp
        for procName in exp.procs:         
            self.addProcedurePage(procName, exp.procs[procName])
            
    def addProcedurePage(self, procName, proc):
        procPage = ProcedurePage(parent=self, proc=proc)
        self.AddPage(procPage, procName)
    
class ProcButtonsPanel(scrolled.ScrolledPanel):
    def __init__(self, parent, id=-1):
        """A panel that shows how the procedures will fit together
        """
        scrolled.ScrolledPanel.__init__(self,parent,id,size=(80,600))
        self.parent=parent    
        self.sizer=wx.BoxSizer(wx.VERTICAL)        
        
        # add a button for each type of event that can be added
        self.procButtons={}; self.objectFromID={}
        for eventType in eventTypes:
            img = parent.bitmaps[eventType]         
            btn = wx.BitmapButton(self, -1, img, (20, 20),
                           (img.GetWidth()+10, img.GetHeight()+10),
                           name=eventType)  
            self.objectFromID[btn.GetId()]=eventType
            self.Bind(wx.EVT_BUTTON, self.onObjectAdd,btn)  
            self.sizer.Add(btn, 0,wx.EXPAND|wx.ALIGN_CENTER )
            self.procButtons[eventType]=btn#store it for elsewhere
            
        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()
        
    def onObjectAdd(self,evt):
        objectName = self.objectFromID[evt.GetId()]
        newClassStr = 'Event'+objectName
        exec('newObj = ExperimentObjects.%s()' %newClassStr)
        dlg = DlgObjectProperties(parent=self.parent,
            title=objectName+' Properties',
            params = newObj.params)
        print newObj.params
        
class DlgObjectProperties(wx.Dialog):    
    def __init__(self,parent,title,params,fixed=[],
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT):
        style=style|wx.RESIZE_BORDER
        
        wx.Dialog.__init__(self, parent,-1,title,pos,size,style)
        
        self.params=params
        self.fixed=fixed
        self.inputFields = []
        self.inputFieldTypes= []
        self.inputFieldNames= []
        self.data = []
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        
        keys = self.params.keys()
        keys.sort()
        types=dict([])
        for field in keys:
            #DEBUG: print field, type(params[field])
            types[field] = type(self.params[field])
            if field in fixed:
                self.addFixedField(field,self.params[field])
            else:
                self.addField(field,self.params[field])
        #show it and collect data
        self.showAndGetData()
        if self.OK:
            for n,thisKey in enumerate(keys):
                self.params[thisKey]=self.data[n]
                
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
        
    def showAndGetData(self):
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
                if thisType in [tuple,list,float,int]:
                    #probably a tuple or list
                    exec("self.data.append("+thisVal+")")#evaluate it
                elif thisType==numpy.ndarray:
                    exec("self.data.append(numpy.array("+thisVal+"))")
                elif thisType==str:#a num array or string?
                    self.data.append(thisVal)
                else:
                    self.data.append(thisVal)
            self.OK=True
        else: 
            self.OK=False
        self.Destroy()
        
class BuilderFrame(wx.Frame):

    def __init__(self, parent, id=-1, title='PsychoPy Builder',
                 pos=wx.DefaultPosition, size=(800, 600),files=None,
                 style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        self.parent=parent
        
        #load icons for the various stimulus events 
        self.bitmaps={}
        for eventType in eventTypes:
            self.bitmaps[eventType]=wx.Bitmap("res//%s.png" %eventType.lower())        
        
        self._mgr = wx.aui.AuiManager(self)
        
        #create a default experiment (maybe an empty one instead)
        self.exp = ExperimentObjects.Experiment()
        self.exp.addProcedure('trial') #create the trial procedure
        self.exp.flow.addProcedure(self.exp.procs['trial'], pos=1)#add it to flow
        #adda loop to the flow as well
        trialInfo = [ {'ori':5, 'sf':1.5}, {'ori':2, 'sf':1.5},{'ori':5, 'sf':3}, ] 
        self.exp.flow.addLoop(
            ExperimentObjects.LoopHandler(name='trialLoop', loopType='rand', nReps=5, trialList = trialInfo),
            startPos=0.5, endPos=1.5,#specify positions relative to the
            )
        
        # create our panels
        self.flowPanel=FlowPanel(parent=self, size=(600,200))
        self.procPanel=ProceduresNotebook(self)
        self.procButtons=ProcButtonsPanel(self)
        # add the panes to the manager
        self._mgr.AddPane(self.procPanel,wx.CENTER, 'Procedures')
        self._mgr.AddPane(self.procButtons, wx.RIGHT)
        self._mgr.AddPane(self.flowPanel,wx.BOTTOM, 'Flow')

        # tell the manager to 'commit' all the changes just made
        self._mgr.Update()

        self.Bind(wx.EVT_CLOSE, self.OnClose)

    def OnClose(self, event):
        # deinitialize the frame manager
        self._mgr.UnInit()
        # delete the frame
        self.Destroy()


class BuilderApp(wx.App):
    def OnInit(self):
        if len(sys.argv)>1:
            if sys.argv[1]==__name__:
                args = sys.argv[2:] # program was excecuted as "python.exe PsychoPyIDE.py %1'
            else:
                args = sys.argv[1:] # program was excecuted as "PsychoPyIDE.py %1'
        else:
            args=[]
        self.frame = BuilderFrame(None, -1, 
                                      title="PsychoPy Experiment Builder",
                                      files = args)
                                     
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True
    def MacOpenFile(self,fileName):
        self.frame.setCurrentDoc(fileName) 

if __name__=='__main__':
    app = BuilderApp(0)
    app.MainLoop()