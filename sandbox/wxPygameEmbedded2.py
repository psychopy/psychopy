import os

import wx
import pygame, sys

class wxSDLWindow(wxFrame):
    def __init__(self, parent, id, title = 'SDL window', **options):
        options['style'] = wxDEFAULT_FRAME_STYLE | wxTRANSPARENT_WINDOW
        wxFrame.__init__(*(self, parent, id, title), **options)

        self._initialized = 0
        self._resized = 0
        self._surface = None
        self.__needsDrawing = 1

        EVT_IDLE(self, self.OnIdle)
        
    def OnIdle(self, ev):
        if not self._initialized or self._resized:
            if not self._initialized:
                # get the handle
                hwnd = self.GetHandle()
                
                os.environ['SDL_WINDOWID'] = str(hwnd)
                if sys.platform == 'win32':
                    os.environ['SDL_VIDEODRIVER'] = 'windib'
                
                pygame.init()
                
                EVT_SIZE(self, self.OnSize)
                self._initialized = 1
        else:
            self._resized = 0

        x,y = self.GetSizeTuple()
        self._surface = pygame.display.set_mode((x,y))

        if self.__needsDrawing:
            self.draw()

    def OnPaint(self, ev):
        self.__needsDrawing = 1

    def OnSize(self, ev):
        self._resized = 1
        ev.Skip()

    def draw(self):
        raise NotImplementedError('please define a .draw() method!')

    def getSurface(self):
        return self._surface


if __name__ == "__main__":

    class CircleWindow(wxSDLWindow):
        "draw a circle in a wxPython / PyGame window"
        def draw(self):
            surface = self.getSurface()
            if not surface is None:
                topcolor = 5
                bottomcolor = 100

                pygame.draw.circle(surface, (250,0,0), (100,100), 50)
                
                pygame.display.flip()

    def pygametest():
        app = wxPySimpleApp()
        sizeT = (640,480)
        w = CircleWindow(None, -1, size = sizeT)
        w.Show(1)
        app.MainLoop()

    pygametest()