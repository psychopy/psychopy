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
from psychopy.app.builder import components

class AbstractTool(object):
    def __init__(self, window):
        self.start_pos = None
        self.stop_pos = None
        self.active = False
        self.window = window
    
    def start(self, pos):
        self.start_pos = pos
        self.active = True
    
    def stop(self, pos):
        self.stop_pos = pos
        self.active = False
    
    def update(self, pos):
        pass


class VisualTool(AbstractTool):
    def start(self, pos):
        super(VisualTool, self).start(pos)
        self.dc = wx.WindowDC(self.window)
        self.blit_w, self.blit_h = self.dc.GetSize()
        self.window.temp_dc.Blit(0, 0, self.blit_w, self.blit_h, self.dc, 0, 0)

    def visualize(self, pos, dc):
        raise NotImplementedError("Abstract method visualize not implemented")

    def update(self, pos):
        super(VisualTool, self).update(pos)
        dc = wx.BufferedDC(wx.WindowDC(self.window))
        dc.BeginDrawing()
        dc.Blit(0, 0, self.blit_w, self.blit_h, self.window.temp_dc, 0, 0)
        self.visualize(pos, dc)
        dc.EndDrawing()


class ExtentVisualTool(VisualTool):
    def visualize(self, pos, dc):
        x, y = self.start_pos[0], self.start_pos[1]
        w, h = pos[0] - x, pos[1] - y
        dc.SetBackgroundMode(wx.TRANSPARENT)
        self.draw_extent((x, y), (w, h), dc)
    
    def draw_extent(self, (x, y), (w, h), dc):
        raise NotImplementedError("Abstract method draw_extent not implemented")
    
    def extent_to_norm(self):
        start_pos = numpy.array(self.start_pos, float)
        stop_pos = numpy.array(self.stop_pos, float)
        size = numpy.array(self.window.GetSize(), float)
        offset = numpy.array([-1.0, 1.0])
        pos = offset + [1, -1] * (stop_pos + start_pos) / size
        size = 2.0 * (stop_pos - start_pos) / size
        return pos.tolist(), size.tolist()


class EllipseTool(ExtentVisualTool):
    def draw_extent(self, (x, y), (w, h), dc):
        dc.DrawEllipse(x, y, w, h)
        
    def stop(self, pos):
        super(EllipseTool, self).stop(pos)
        component_class = components.getAllComponents()["BasicShapeComponent"]
        pos, size = self.extent_to_norm()
        component = component_class(
            self.window.routine.exp, self.window.routine.name, units='norm', pos=pos, size=size,
            shape="ellipse")
        return component


class RectangleTool(ExtentVisualTool):
    def draw_extent(self, (x, y), (w, h), dc):
        dc.DrawRectangle(x, y, w, h)

    def stop(self, pos):
        super(RectangleTool, self).stop(pos)
        component_class = components.getAllComponents()["BasicShapeComponent"]
        pos, size = self.extent_to_norm()
        component = component_class(
            self.window.routine.exp, self.window.routine.name, units='norm', pos=pos, size=size,
            shape="rectangle")
        return component

class ArrowTool(ExtentVisualTool):
    def draw_extent(self, (x1, y1), (w, h), dc):
        x2, y2 = x1 + w, y1 + h
        a = numpy.arctan2(h, w)
        b = numpy.pi * 0.8
        l = numpy.array((x2, y2), float) + numpy.array((numpy.cos(a - b), numpy.sin(a - b)), float) * 30.0
        r = numpy.array((x2, y2), float) + numpy.array((numpy.cos(a + b), numpy.sin(a + b)), float) * 30.0
        dc.DrawLine(x1, y1, x2, y2)
        dc.DrawLine(x2, y2, l[0], l[1])
        dc.DrawLine(x2, y2, r[0], r[1])

    def stop(self, pos):
        super(ArrowTool, self).stop(pos)
        component_class = components.getAllComponents()["BasicShapeComponent"]
        pos, size = self.extent_to_norm()
        component = component_class(
            self.window.routine.exp, self.window.routine.name, units='norm', pos=pos, size=size,
            shape="arrow")
        return component


class GratingTool(ExtentVisualTool):
    def draw_extent(self, (x, y), (w, h), dc):
        dc.DrawEllipse(x, y, w, h)
    
    def stop(self, pos):
        super(GratingTool, self).stop(pos)
        component_class = components.grating.GratingComponent
        pos, size = self.extent_to_norm()
        component = component_class(
            self.window.routine.exp, self.window.routine.name, units='norm', pos=pos, size=size, mask='gauss')
        return component


class ImageTool(ExtentVisualTool):
    def draw_extent(self, (x, y), (w, h), dc):
        dc.DrawRectangle(x, y, w, h)
    
    def stop(self, pos):
        super(ImageTool, self).stop(pos)
        pos, size = self.extent_to_norm()
        component = components.image.ImageComponent(
            self.window.routine.exp, self.window.routine.name, units='norm', pos=pos, size=size)
        return component


class TextTool(AbstractTool):
    def stop_pos_to_norm(self):
        stop_pos = numpy.array(self.stop_pos, float)
        size = numpy.array(self.window.GetSize(), float)
        offset = numpy.array([-1.0, 1.0])
        pos = offset + [2, -2] * (stop_pos) / size
        return pos.tolist()
    
    def stop(self, pos):
        super(TextTool, self).stop(pos)
        pos = self.stop_pos_to_norm()
        component = components.text.TextComponent(
            self.window.routine.exp, self.window.routine.name, units='norm', pos=pos, text='Hello!')
        return component


class ToolHandler(object):
    @staticmethod
    def stringify_params(component):
        for key in component.params.keys():
            if key in ['order', 'advancedParams']:
                continue
            component.params[key].val = str(component.params[key].val)
    
    def __init__(self, routine, frame):
        self.routine = routine
        self.frame = frame
        self.tool = None

    def set_tool(self, tool):
        self.tool = tool

    def start(self, pos):
        if self.tool:
            self.tool.start(pos)
            return True
        else:
            return False

    def stop(self, pos):
        component = self.tool.stop(pos)
        self.routine.addComponent(component)
        self.frame.routinePanel.getCurrentPage().redrawRoutine()
        self.stringify_params(component) #fix for inconsistent param typing
        return component

    def update(self, pos):
        self.tool.update(pos)


class RoutinePreview(glcanvas.GLCanvas):
    def __init__(self, parent, tool_handler):
        super(RoutinePreview, self).__init__(parent)
        self.routine = []
        self.stimuli = None
        self.context = glcanvas.GLContext(self)
        self.gl_inited = False
        self.tool_handler = tool_handler
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_LEFT_DOWN, self.start_tool)
        #self.Bind(wx.EVT_LEFT_UP, self.stop_tool)

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
        width, height = self.GetSize()
        self.temp_bitmap = wx.EmptyBitmap(width, height)
        self.temp_dc = wx.MemoryDC(self.temp_bitmap)

    def on_paint(self, event):
        self.SetCurrent(self.context)
        if not self.gl_inited:
            self.init_gl()
        gl.glClear(gl.GL_COLOR_BUFFER_BIT)
        if self.stimuli is None:
            self.generate_stimuli()
        self.draw_components()
        self.SwapBuffers()
    
    def start_tool(self, event):
        pos = (event.GetX(), event.GetY())
        if self.tool_handler.start(pos):
            self.Bind(wx.EVT_LEFT_UP, self.stop_tool)
            self.Bind(wx.EVT_MOTION, self.update_tool)

    def stop_tool(self, event):
        self.Unbind(wx.EVT_LEFT_UP)
        self.Unbind(wx.EVT_MOTION)
        pos = (event.GetX(), event.GetY())
        component = self.tool_handler.stop(pos)
        if component:
            self.add_stimulus(component)
            self.Refresh()

    def update_tool(self, event):
        pos = (event.GetX(), event.GetY())
        self.tool_handler.update(pos)

    def draw_components(self):
        for stimulus in self.stimuli:
            stimulus.draw()

    def add_component(self, component):
        self.components.append(component)

    def add_stimulus(self, component):
        self.SetCurrent(self.context)
        stimulus = component.getStimulus(self.GetParent())
        if stimulus is not None:
            self.stimuli.append(stimulus)

    def generate_stimuli(self):
        self.stimuli = []
        for component in self.routine:
            if hasattr(component, "getStimulus"):
                self.add_stimulus(component)

    def update_routine(self, routine):
        self.routine = routine
        self.stimuli = None
    
    def set_tool(self, tool_class):
        if tool_class:
            self.tool = tool_class(self)
        else:
            self.tool = None


class SidePanel(wx.Panel):
    """
    Panel used in sketchpad window. Displays component list or component properties.
    """
    def __init__(self, parent):
        super(SidePanel, self).__init__(parent)
        self.SetSizer(wx.BoxSizer())
        self.list_panel = ComponentListPanel(self)
        self.GetSizer().Add(self.list_panel)


class PropertiesPanel(wx.Panel):
    """
    Panel used in sketchpad window. Displays component properties.
    """
    pass


class ComponentListPanel(wx.Panel):
    """
    Panel used in sketchpad window. Display component list
    """
    def __init__(self, parent):
        super(ComponentListPanel, self).__init__(parent)
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        self.visible_list_label = wx.StaticText(self, label="Visible Components")
        self.GetSizer().Add(self.visible_list_label)


class SketchpadWindow(wx.Dialog):
    def __init__(self, parent, routine):
        super(SketchpadWindow, self).__init__(parent, title="Sketchy Pad", size=(880, 540))
        self.routine = routine
        self._haveShaders = False
        self.winType = "wxglcanvas"
        self.size = (128, 128)
        self.exp = parent.exp
        self.units = self.exp.settings.params["Units"].val
        if self.units == "use prefs":
            self.units = preferences.Preferences().general["units"]
        pygame.font.init()
        self.current_tool = None
        self.canvas = RoutinePreview(self, ToolHandler(self.routine, self.GetParent()))
        self.canvas.update_routine(self.routine)
        sizer = wx.BoxSizer(wx.VERTICAL)
        self.workspaceSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.SetSizer(sizer)
        self.init_toolbar()
        sizer.Add(self.toolbar, flag=wx.EXPAND)
        sizer.Add(self.workspaceSizer, proportion=1, flag=wx.EXPAND | wx.ALL, border=8)
        self.workspaceSizer.Add(self.canvas, proportion=3, flag=wx.EXPAND)
        #self.workspaceSizer.Add(SidePanel(self), proportion=1, flag=wx.EXPAND)
        
        sizer.Add(self.CreateButtonSizer(wx.OK), flag=wx.EXPAND | wx.ALL, border=8)
        self.Bind(wx.EVT_BUTTON, self.onOK, id=wx.ID_OK)

    def ellipse_tool_event(self, event):
        print "ellipse"
    
    def untoggle_current_tool(self):
        self.toolbar.ToggleTool(self.current_tool, False)
        self.current_tool = None
    
    def toggle_current_tool(self):
        self.toolbar.ToggleTool(self.current_tool, True)
    
    def toggle_tool_event(self, event):
        if self.current_tool == event.GetId():
            self.untoggle_current_tool()
            self.canvas.set_tool(None)
        else:
            if self.current_tool:
                self.untoggle_current_tool()
            self.current_tool = event.GetId()
            self.toggle_current_tool()
            tool_class = self.toolbar.GetToolClientData(event.GetId())
            self.canvas.tool_handler.set_tool(tool_class(self.canvas))

    def init_toolbar(self):
        TOOLS = [
            ("Ellipse", "Draw ellipse", "sketchpad-ellipse", EllipseTool),
            ("Rectangle", "Draw rectangle", "sketchpad-rectangle", RectangleTool),
            ("Arrow", "Draw arrow", "sketchpad-arrow", ArrowTool),
            (),
            ("Grating", "Add grating component", "components-GratingComponent", GratingTool),
            ("Image", "Add image component", "components-ImageComponent", ImageTool),
            ("Text","Add text component", "components-TextComponent", TextTool)
        ]
        self.toolbar = wx.ToolBar(self)
        for tool in TOOLS:
            if tool == ():
                self.toolbar.AddSeparator()
            else:
                label, hint, art_id, tool_class = tool
                bitmap = wx.ArtProvider.GetBitmap(art_id, wx.ART_TOOLBAR)
                self.toolbar.AddLabelTool(-1, label, bitmap, wx.NullBitmap, wx.ITEM_CHECK, hint, clientData=tool_class)
        self.toolbar.Bind(wx.EVT_TOOL, self.toggle_tool_event)
        self.toolbar.Realize()

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
    
    def logOnFlip(self, *args, **kwargs):
        pass

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
