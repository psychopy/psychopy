import wx
"""This is for general purpose dialogs, not related to particular functionality
"""

class MessageDialog(wx.Dialog):
    """For some reason the wx builtin message dialog has some issues on Mac OSX
    (buttons don't always work) so we need to use this instead.
    """
    def __init__(self,parent=None,message='',type='Warning', title=None):
        if title==None: title=type
        wx.Dialog.__init__(self,parent,-1,title=title)
        sizer=wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self,-1,message),flag=wx.ALL,border=15)
        #add buttons
        btnSizer=wx.BoxSizer(wx.HORIZONTAL)
        if type=='Warning':#we need Yes,No,Cancel
            self.yesBtn=wx.Button(self,wx.ID_YES,'Yes')
            self.yesBtn.SetDefault()
            self.cancelBtn=wx.Button(self,wx.ID_CANCEL,'Cancel')
            self.noBtn=wx.Button(self,wx.ID_NO,'No')
            self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_CANCEL)
            self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_YES)
            self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_NO)
            btnSizer.Add(self.noBtn, wx.ALIGN_LEFT)
            btnSizer.Add((60, 20), 0, wx.EXPAND)
            btnSizer.Add(self.cancelBtn, wx.ALIGN_RIGHT)
            btnSizer.Add((5, 20), 0)
            btnSizer.Add(self.yesBtn, wx.ALIGN_RIGHT)
        elif type=='Info':#just an OK button
            self.okBtn=wx.Button(self,wx.ID_OK,'OK')
            self.okBtn.SetDefault()
            self.Bind(wx.EVT_BUTTON, self.onButton, id=wx.ID_OK)
            btnSizer.Add(self.okBtn, wx.ALIGN_RIGHT)
        #configure sizers and fit
        sizer.Add(btnSizer,flag=wx.ALIGN_RIGHT|wx.ALL,border=5)
        self.Center()
        self.SetSizerAndFit(sizer)
    def onButton(self,event):
        self.EndModal(event.GetId())
        