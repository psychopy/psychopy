'''
Module with component start and stop controls.
'''

import wx


class VariantPanel(wx.Panel):
    def __init__(self, parent, variants=[("NONE", "none", None)], value=None):
        super(VariantPanel, self).__init__(parent)
        self.variants = list(variants)
        self.label_indices = dict([(v[0], i) for i, v in enumerate(variants)])
        self.init_controls()
        self.SetValue(value)
        
    def init_controls(self):
        self.variant_field = wx.Choice(self, choices=[c[1] for c in self.variants])
        self.value_field = None
        self.init_sizer()
        self.init_events()
        self.update_variant(0)
    
    def init_sizer(self):
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.variant_field, flag=wx.EXPAND | wx.ALL, border=3)
        self.SetSizer(sizer)
    
    def init_events(self):
        self.Bind(wx.EVT_CHOICE, self.on_choice, self.variant_field)
    
    def update_variant(self, selection):
        if self.value_field is not None:
            self.GetSizer().Remove(self.value_field)
            self.value_field.Destroy()
            self.value_field = None
        value_class = self.variants[selection][2]
        if value_class is not None:
            self.value_field = value_class(self)
            self.GetSizer().Add(self.value_field, flag=wx.EXPAND | wx.ALL, border=3, proportion=1)
            self.GetSizer().Layout()
            
    def on_choice(self, event):
        self.update_variant(event.GetSelection())
    
    def SetValue(self, value):
        if value is None:
            self.variant_field.SetSelection(wx.NOT_FOUND)
            self.value_field.SetValue("")
        else:
            self.variant_field.SetSelection(self.label_indices[value["type"]])
            self.value_field.SetValue(str(value["value"]))
    
    def GetValue(self):
        return {"type": self.variants[self.variant_field.GetSelection()][0], "value": self.value_field.GetValue()}


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
        self.init_controls()
        self.SetValue(value)
    
    def init_controls(self):
        self.value_field = StartVariantPanel(self)
        self.estimation_label = wx.StaticText(self, label="expected start (s)")
        self.estimation_field = wx.TextCtrl(self)
        self.init_sizer()
    
    def init_sizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        estimation_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.value_field, flag=wx.EXPAND | wx.ALL, border=3, proportion=1)
        sizer.Add(estimation_sizer, flag=wx.EXPAND | wx.ALL, border=3, proportion=1)
        estimation_sizer.Add(self.estimation_label, flag=wx.EXPAND | wx.ALL, border=3)
        estimation_sizer.Add(self.estimation_field, flag=wx.EXPAND | wx.ALL, border=3, proportion=1)
        self.SetSizer(sizer)
    
    def GetValue(self):
        value = self.value_field.GetValue()
        value["estimation"] = self.estimation_field.GetValue()
        return value
    
    def SetValue(self, value):
        self.value = value
        self.value_field.SetValue(value)
        self.estimation_field.SetValue(value["estimation"])


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
        self.init_controls()
        self.SetValue(value)
    
    def init_controls(self):
        self.value_field = StopVariantPanel(self)
        self.estimation_label = wx.StaticText(self, label="expected duration (s)")
        self.estimation_field = wx.TextCtrl(self)
        self.init_sizer()
    
    def init_sizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        estimation_sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.value_field, flag=wx.EXPAND | wx.ALL, border=3, proportion=1)
        sizer.Add(estimation_sizer, flag=wx.EXPAND | wx.ALL, border=3, proportion=1)
        estimation_sizer.Add(self.estimation_label, flag=wx.EXPAND | wx.ALL, border=3)
        estimation_sizer.Add(self.estimation_field, flag=wx.EXPAND | wx.ALL, border=3, proportion=1)
        self.SetSizer(sizer)
    
    def GetValue(self):
        value = self.value_field.GetValue()
        value["estimation"] = self.estimation_field.GetValue()
        return value
    
    def SetValue(self, value):
        self.value = value
        self.value_field.SetValue(value)
        self.estimation_field.SetValue(value["estimation"])


if __name__ == "__main__":
    app = wx.App()
    mainWindow = wx.Dialog(None, title="ZUPA ZUPA ZUPA")
    
    mainSizer = wx.BoxSizer()
    mainSizer.Add(StartPanel(mainWindow), flag=wx.EXPAND | wx.ALL, border=8, proportion=1)
    mainWindow.SetSizer(mainSizer)
    
    mainWindow.Show()
    app.SetTopWindow(mainWindow)
    app.MainLoop()
