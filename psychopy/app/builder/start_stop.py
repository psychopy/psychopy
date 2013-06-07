'''
Module with component start and stop controls.
'''

import wx


class VariantPanel(wx.Panel):
    def __init__(self, parent, variants=[("NONE", "none", None)], value=None):
        super(VariantPanel, self).__init__(parent)
        self.variants = list(variants)
        self.labelIndices = dict([(v[0], i) for i, v in enumerate(variants)])
        self.initControls()
        self.SetValue(value)
        
    def initControls(self):
        self.variantField = wx.Choice(self, choices=[c[1] for c in self.variants])
        self.valueField = None
        self.initSizer()
        self.initEvents()
        self.updateVariant(0)
    
    def initSizer(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.variantField, flag=wx.EXPAND | wx.ALL, border=3)
        self.SetSizer(sizer)
    
    def initEvents(self):
        self.Bind(wx.EVT_CHOICE, self.onChoice, self.variantField)
    
    def updateVariant(self, selection):
        if self.valueField is not None:
            self.GetSizer().Remove(self.valueField)
            self.valueField.Destroy()
            self.valueField = None
        valueClass = self.variants[selection][2]
        if valueClass is not None:
            self.valueField = valueClass(self)
            self.GetSizer().Add(self.valueField, flag=wx.EXPAND | wx.ALL, border=3, proportion=1)
            self.GetSizer().Layout()
            
    def onChoice(self, event):
        self.updateVariant(event.GetSelection())
    
    def SetValue(self, value):
        if value is None:
            self.variantField.SetSelection(wx.NOT_FOUND)
            self.valueField.SetValue("")
        else:
            self.variantField.SetSelection(self.labelIndices[value["type"]])
            self.valueField.SetValue(str(value["value"]))
    
    def GetValue(self):
        return {"type": self.variants[self.variantField.GetSelection()][0], "value": self.valueField.GetValue()}


class StartVariantPanel(VariantPanel):
    CHOICES = [
        ("time (s)", "time (s)", wx.TextCtrl),
        ("frame N", "frame N", wx.TextCtrl),
        ("condition", "condition", wx.TextCtrl),
        ("KEY_PRESS", "key press", wx.TextCtrl),
        ("MOUSE_CLOCK", "mouse click", wx.TextCtrl),
        ("COMPONENT_START", "component start", wx.TextCtrl),
        ("COMPONENT_FINISH", "component finish", wx.TextCtrl)
    ]
    
    def __init__(self, parent, value=None):
        super(StartVariantPanel, self).__init__(parent, self.CHOICES, value=value)
        

class StartPanel(wx.Panel):
    def __init__(self, parent, value=None):
        super(StartPanel, self).__init__(parent)
        self.initControls()
        self.SetValue(value)
    
    def initControls(self):
        self.valueField = StartVariantPanel(self)
        self.estimationLabel = wx.StaticText(self, label="expected start (s)")
        self.estimationField = wx.TextCtrl(self)
        self.initSizer()
    
    def initSizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        estimationSizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.valueField, flag=wx.EXPAND | wx.ALL, border=3, proportion=1)
        sizer.Add(estimationSizer, flag=wx.EXPAND | wx.ALL, border=3, proportion=1)
        estimationSizer.Add(self.estimationLabel, flag=wx.EXPAND | wx.ALL, border=3)
        estimationSizer.Add(self.estimationField, flag=wx.EXPAND | wx.ALL, border=3, proportion=1)
        self.SetSizer(sizer)
    
    def GetValue(self):
        value = self.valueField.GetValue()
        value["estimation"] = self.estimationField.GetValue()
        return value
    
    def SetValue(self, value):
        self.value = value
        self.valueField.SetValue(value)
        self.estimationField.SetValue(value["estimation"])


class StopVariantPanel(VariantPanel):
    CHOICES = [
        ("time (s)", "time (s)", wx.TextCtrl),
        ("frame", "frame", wx.TextCtrl),
        ("duration (s)", "duration (s)", wx.TextCtrl),
        ("duration (frames)", "duration (frames)", wx.TextCtrl),
        ("condition", "condition", wx.TextCtrl),
        ("KEY_PRESS", "key press", wx.TextCtrl),
        ("MOUSE_CLICK", "mouse click", wx.TextCtrl),
        ("COMPONENT_START", "component start", wx.TextCtrl),
        ("COMPONENT_FINISH", "component finish", wx.TextCtrl)
    ]
    
    def __init__(self, parent, value=None):
        super(StopVariantPanel, self).__init__(parent, variants=self.CHOICES, value=value)


class StopPanel(wx.Panel):
    def __init__(self, parent, value=None):
        super(StopPanel, self).__init__(parent)
        self.initControls()
        self.SetValue(value)
    
    def initControls(self):
        self.valueField = StopVariantPanel(self)
        self.estimationLabel = wx.StaticText(self, label="expected duration (s)")
        self.estimationField = wx.TextCtrl(self)
        self.initSizer()
    
    def initSizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        estimationSizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.valueField, flag=wx.EXPAND | wx.ALL, border=3, proportion=1)
        sizer.Add(estimationSizer, flag=wx.EXPAND | wx.ALL, border=3, proportion=1)
        estimationSizer.Add(self.estimationLabel, flag=wx.EXPAND | wx.ALL, border=3)
        estimationSizer.Add(self.estimationField, flag=wx.EXPAND | wx.ALL, border=3, proportion=1)
        self.SetSizer(sizer)
    
    def GetValue(self):
        value = self.valueField.GetValue()
        value["estimation"] = self.estimationField.GetValue()
        return value
    
    def SetValue(self, value):
        self.value = value
        self.valueField.SetValue(value)
        self.estimationField.SetValue(value["estimation"])


if __name__ == "__main__":
    app = wx.App()
    mainWindow = wx.Dialog(None, title="ZUPA ZUPA ZUPA")
    
    mainSizer = wx.BoxSizer()
    mainSizer.Add(StartPanel(mainWindow), flag=wx.EXPAND | wx.ALL, border=8, proportion=1)
    mainWindow.SetSizer(mainSizer)
    
    mainWindow.Show()
    app.SetTopWindow(mainWindow)
    app.MainLoop()
