'''
Module implements WYSIWYG sketchpad for components.
'''

import wx
from wx import glcanvas
import OpenGL.GL as gl
import pygame.font
import numpy
import logging
from psychopy import preferences

class RoutinePreview(glcanvas.GLCanvas):
    def __init__(self, parent):
        super(RoutinePreview, self).__init__(parent)
        self.routine = []
        self.stimuli = None
        self.context = glcanvas.GLContext(self)
        self.gl_inited = False
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_PAINT, self.on_paint)

    def init_gl(self):
        gl.glClearColor(0.67, 0.67, 0.67, 0.0)
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glEnable(gl.GL_TEXTURE_2D)
        gl.glShadeModel(gl.GL_SMOOTH)
        self.gl_inited = True

    def on_size(self, event):
        if not self.context:
            self.context = glcanvas.GLContext(self)
        self.SetCurrent(self.context)
        size = self.GetClientSize()
        self.GetParent().setSize((size.width, size.height))
        gl.glViewport(0, 0, size.width, size.height)

    def on_paint(self, event):
        self.SetCurrent(self.context)
        if not self.gl_inited:
            self.init_gl()
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        if self.stimuli is None:
            self.generate_stimuli()
        self.draw_components()
        self.SwapBuffers()

    def draw_components(self):
        for stimulus in self.stimuli:
            stimulus.draw()

    def add_component(self, component):
        self.components.append(component)

    def generate_stimuli(self):
        self.stimuli = []
        for component in self.routine:
            if hasattr(component, "getStimulus"):
                self.SetCurrent(self.context)
                stimulus = component.getStimulus(self.GetParent())
                if stimulus is not None:
                    self.stimuli.append(stimulus)

    def update_routine(self, routine):
        self.routine = routine
        self.stimuli = None


class SketchpadWindow(wx.Dialog):
    def __init__(self, parent, routine):
        super(SketchpadWindow, self).__init__(parent, title="Routine preview")
        self.routine = routine
        self._haveShaders = False
        self.winType = "wxglcanvas"
        self.size = (128, 128)
        self.exp = parent.exp
        self.units = self.exp.settings.params["Units"].val
        if self.units == "use prefs":
            self.units = preferences.Preferences().general["units"]
        pygame.font.init()
        self.canvas = RoutinePreview(self)
        self.canvas.update_routine(self.routine)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(sizer)
        sizer.Add(self.canvas, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)
        sizer.Add(self.CreateButtonSizer(wx.OK), flag=wx.EXPAND | wx.ALL, border=8)
        self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)

    def setScale(self, units, font='dummyFont', prevScale=(1.0, 1.0)):
        if units=="norm":
            thisScale = numpy.array([1.0,1.0])
        elif units=="height":
            thisScale = numpy.array([2.0*self.size[1]/self.size[0],2.0])
        elif units in ["pix", "pixels"]:
            thisScale = 2.0/numpy.array(self.size)
        elif units=="cm":
            if (self.scrWidthCM in [0,None]) or (self.scrWidthPIX in [0, None]):
                logging.error('you didnt give me the width of the screen (pixels and cm). Check settings in MonitorCentre.')
            thisScale = (numpy.array([2.0,2.0])/self.size)/(float(self.scrWidthCM)/float(self.scrWidthPIX))
        elif units in ["deg", "degs"]:
            #windowPerDeg = winPerCM*CMperDEG
            #               = winPerCM              * tan(pi/180) * distance
            if (self.scrWidthCM in [0,None]) or (self.scrWidthPIX in [0, None]):
                logging.error('you didnt give me the width of the screen (pixels and cm). Check settings in MonitorCentre.')
            cmScale = (numpy.array([2.0,2.0])/self.size)/(float(self.scrWidthCM)/float(self.scrWidthPIX))
            thisScale = cmScale * 0.017455 * self.scrDistCM
        elif units=="stroke_font":
            thisScale = numpy.array([2*font.letterWidth,2*font.letterWidth]/self.size/38.0)
        #actually set the scale as appropriate
        thisScale = thisScale/numpy.asarray(prevScale)#allows undoing of a previous scaling procedure
        gl.glScalef(thisScale[0], thisScale[1], 1.0)
        return thisScale #just in case the user wants to know?!

    def setSize(self, size):
        self.size = size

    def onOK(self, event):
        pygame.font.quit()
        self.EndModal(0)


if __name__ == "__main__":
    app = wx.App()
    dialog = SketchpadWindow(None, [])
    dialog.Show()
    app.SetExitOnFrameDelete(True)
    app.SetTopWindow(dialog)
    app.MainLoop()
