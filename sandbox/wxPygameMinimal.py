
import pygame, wx, time

class Window:
    def __init__(self,
                 size = (600,600)):
        winSettings = pygame.OPENGL | pygame.DOUBLEBUF        
        pygame.init()
        self.win = pygame.display.set_mode(size,winSettings)
    def swapBuffer(self):
        pygame.display.flip()

    def close(self):
        pygame.display.quit()
        pygame.quit()
    
class MainFrame(wx.Frame):
    def __init__(self, parent, ID, title, files=[]):
        wx.Frame.__init__(self, parent, ID, title)
        wx.EVT_CLOSE(self, self.quit)
        
        #toolbar and button(s)
        self.toolbar = self.CreateToolBar( (wx.TB_HORIZONTAL
            | wx.NO_BORDER
            | wx.TB_FLAT))
        buttonSize=(16,16)
        self.toolbar.SetToolBitmapSize(buttonSize)
        run_bmp = wx.ArtProvider.GetBitmap(wx.ART_EXECUTABLE_FILE, wx.ART_TOOLBAR, buttonSize)
        self.toolbar.AddSimpleTool(101, run_bmp, "Run [F5]",  "Run current script")
        self.toolbar.Bind(wx.EVT_TOOL, self.runPygame, id=101)
        self.toolbar.Realize()
    def quit(self, event):
        self.Destroy()
    def runPygame(self, event):
        win = Window([200,200])
        win.swapBuffer()
        time.sleep(1)
        win.close()
class MyApp(wx.App):
    def OnInit(self):
        self.frame = MainFrame(None, -1, title="Test Pygame")        
        self.frame.Show(True)
        self.SetTopWindow(self.frame)
        return True
    
app = MyApp()
app.MainLoop()
