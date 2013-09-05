import wx
import IPython.gui.wx.ipython_view

class ShellFrame(wx.Frame):
    def __init__(self, parent, ID, title, files=[], app=None):
        self.app = app
        self.frameType='shell'
        self.appData = self.app.prefs.appData['coder']#things the user doesn't set like winsize etc
        self.prefs = self.app.prefs.coder#things about the coder that get set
        self.appPrefs = self.app.prefs.app
        self.paths = self.app.prefs.paths
        self.IDs = self.app.IDs
        
        wx.Frame.__init__(self, parent, ID, title,
                         size=((600,400)))
        self.sizer = wx.BoxSizer()
        
        self.ipython = IPython.gui.wx.ipython_view.IPShellWidget(parent=self, 
            background_color='WHITE',
            )
        #turn off threading - interferes with pygame thread
        self.ipython.options['threading']['value']='False'
        self.ipython.IP.set_threading(False)
        self.ipython.threading_option.SetValue(False)
        #allow a write fmethod for the window
        self.ipython.cout.write = self.ipython.text_ctrl.write
        self.ipython.write = self.ipython.text_ctrl.write
        
        #set background to white
        self.ipython.options['background_color']['value']='WHITE'#this setting isn't used by __init__ apparently
        self.ipython.text_ctrl.setBackgroundColor(self.ipython.options['background_color']['value'])
        self.ipython.background_option.SetValue(True)
        self.ipython.updateOptionTracker('background_color',
                                 self.ipython.options['background_color']['value'])
        #scintilla autocompletion method
        self.ipython.completion_option.SetValue(True)
        self.ipython.options['completion']['value']='STC'
        self.ipython.text_ctrl.setCompletionMethod(self.ipython.options['completion']['value'])
        self.ipython.updateOptionTracker('completion',
                                 self.ipython.options['completion']['value'])
        self.ipython.text_ctrl.SetFocus()
        
        self.sizer.Add(self.ipython,0,wx.EXPAND)
        self.SendSizeEvent()
        
        self.SetSizerAndFit(self.sizer)
        self.SetAutoLayout(1)
