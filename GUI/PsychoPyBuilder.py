import wx
import wx.aui
import sys
    
class FlowPanel(wx.Panel):
    def __init__(self, parent, id=-1):
        """A panel that shows how the procedures will fit together
        """
        wx.Panel.__init__(self,parent,size=(100,600))
        self.parent=parent    
        self.addProcBtn = wx.Button(self,-1,'AddProc') 
class Procedure(wx.Panel):
    """A frame to represent a single procedure
    """
    def __init__(self, parent, id=-1):
        wx.Panel.__init__(self,parent)
        self.parent=parent            
class ProceduresPanel(wx.aui.AuiNotebook):
    """A notebook that stores one or more procedures
    """
    def __init__(self, parent, id=-1):
        self.parent=parent
        wx.aui.AuiNotebook.__init__(self, parent, id,)
        self.addProcedure('first')
    def addProcedure(self, procName):
        text1 = Procedure(parent=self)
        self.AddPage(text1, procName)
    
class ProcButtonsPanel(wx.Panel):
    def __init__(self, parent, id=-1):
        """A panel that shows how the procedures will fit together
        """
        wx.Panel.__init__(self,parent,size=(100,600))
        self.parent=parent    
        self.sizer=wx.BoxSizer(wx.VERTICAL)
        
        textImg = wx.Bitmap("res//text.png")
        self.textBtn = wx.BitmapButton(self, -1, textImg, (20, 20),
                       (textImg.GetWidth()+10, textImg.GetHeight()+10),style=wx.NO_BORDER)
                       
        patchImg= wx.Bitmap("res//patch.png")
        self.patchBtn = wx.BitmapButton(self, -1, patchImg, (20, 20),
                       (patchImg.GetWidth()+10, patchImg.GetHeight()+10),style=wx.NO_BORDER)
                       
        mouseImg= wx.Bitmap("res//mouse.png")
        self.mouseBtn = wx.BitmapButton(self, -1, mouseImg, (20, 20),
                       (mouseImg.GetWidth()+10, mouseImg.GetHeight()+10),style=wx.NO_BORDER)
#        patchImg= wx.Bitmap("res//patch.png")
#        self.textBtn = wx.BitmapButton(self, -1, patchImg, (20, 20),
#                       (patchImg.GetWidth()+10, patchImg.GetHeight()+10))
#        patchImg= wx.Bitmap("res//patch.png")
#        self.textBtn = wx.BitmapButton(self, -1, patchImg, (20, 20),
#                       (patchImg.GetWidth()+10, patchImg.GetHeight()+10))
        
        self.sizer.Add(self.patchBtn, 0,wx.EXPAND|wx.ALIGN_CENTER )
        self.sizer.Add(self.textBtn, 0,wx.EXPAND|wx.ALIGN_CENTER)
        self.sizer.Add(self.mouseBtn, 0,wx.EXPAND|wx.ALIGN_CENTER)
        self.SetSizer(self.sizer)
class BuilderFrame(wx.Frame):

    def __init__(self, parent, id=-1, title='PsychoPy Builder',
                 pos=wx.DefaultPosition, size=(800, 600),files=None,
                 style=wx.DEFAULT_FRAME_STYLE):
        wx.Frame.__init__(self, parent, id, title, pos, size, style)
        self.parent=parent
        self._mgr = wx.aui.AuiManager(self)

        # create several text controls
        self.flowPanel=FlowPanel(parent=self)
        self.procPanel=ProceduresPanel(self)
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


class IDEApp(wx.App):
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
    app = IDEApp(0)
    app.MainLoop()