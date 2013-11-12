'''
Module with component start and stop controls.
'''

import wx


class VariantPanel(wx.Panel):
    def __init__(self, parent, variants=[("NONE", "none", None)], value=None):
        super(VariantPanel, self).__init__(parent)
        self.valueHint = ""
        self.variants = list(variants)
        self.variant = None
        self.labelIndices = dict([(v[0], i) for i, v in enumerate(variants)])
        self.initControls()
        self.SetValue(value)
        
    def initControls(self):
        self.variantField = wx.Choice(self, choices=[c[1] for c in self.variants])
        self.valueFields = {}
        self.initSizer()
        self.initEvents()
    
    def initSizer(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.variantField, flag=wx.EXPAND | wx.ALL, border=3)
        self.SetSizer(sizer)
    
    def initEvents(self):
        self.Bind(wx.EVT_CHOICE, self.onChoice, self.variantField)
    
    def updateVariant(self, selection):
        if self.variant in self.valueFields:
            self.valueFields[self.variant].Hide()
        self.variant = selection
        if self.variant not in self.valueFields:
            valueClass = self.variants[selection][2]
            if valueClass is not None:
                self.valueFields[self.variant] = valueClass(self)
                self.valueFields[self.variant].SetToolTipString(self.valueHint)
                self.GetSizer().Add(self.valueFields[self.variant], flag=wx.EXPAND | wx.ALL, border=3, proportion=1)
                self.GetSizer().Layout()
        if self.variant in self.valueFields:
            self.valueFields[self.variant].Show()
            
    def onChoice(self, event):
        self.updateVariant(event.GetSelection())
    
    def SetValue(self, value):
        if value is None:
            self.updateVariant(0)
            self.variantField.SetSelection(0)
        else:
            self.updateVariant(self.labelIndices[value["type"]])
            self.variantField.SetSelection(self.variant)
            self.valueFields[self.variant].SetValue(str(value["value"]))
    
    def GetValue(self):
        return {"type": self.variants[self.variant][0], "value": self.valueFields[self.variant].GetValue()}
    
    def setToolTips(self, hints):
        self.valueHint = hints['value']
        for field in self.valueFields.values():
            field.SetToolTipString(self.valueHint)
        self.variantField.SetToolTipString(hints['type'])


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
        self.value = value
        self.initControls()
    
    def initControls(self):
        self.valueField = StartVariantPanel(self, value=self.value)
        self.estimationLabel = wx.StaticText(self, label="expected start (s)")
        self.estimationField = wx.TextCtrl(self, value=self.value['estimation'])
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

    def setToolTips(self, hints):
        self.valueField.setToolTips(hints)
        self.estimationField.SetToolTipString(hints['estimation'])


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
        self.estimationField.SetValue(str(value["estimation"]))
    
    def setToolTips(self, hints):
        self.valueField.setToolTips(hints)
        self.estimationField.SetToolTipString(hints['estimation'])
