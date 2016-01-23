# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import

import wx
from wx.lib import platebtn, scrolledpanel
try:
    from wx.lib import flatnotebook
    from wx import aui
except:
    from wx.lib.agw import flatnotebook
    import wx.lib.agw.aui as aui # some versions of phoenix
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
import wx.stc

import sys, os, glob, copy, traceback
import codecs
import re
import numpy

try:
    _translate  # is the app-global text translation function defined?
except NameError:
    from .. import localization

from . import experiment, components
from .. import stdOutRich, dialogs
from psychopy import logging
from psychopy.tools.filetools import mergeFolder
from .dialogs import (DlgComponentProperties, DlgExperimentProperties,
                      DlgCodeComponentProperties)

from .flow import FlowPanel
from .utils import FileDropTarget, WindowFrozen


canvasColor = [200, 200, 200]  # in prefs? ;-)
routineTimeColor = wx.Colour(50, 100, 200, 200)
staticTimeColor = wx.Colour(200, 50, 50, 100)
nonSlipFill = wx.Colour(150, 200, 150, 255)
nonSlipEdge = wx.Colour(0, 100, 0, 255)
relTimeFill = wx.Colour(200, 150, 150, 255)
relTimeEdge = wx.Colour(200, 50, 50, 255)
routineFlowColor = wx.Colour(200, 150, 150, 255)
darkgrey = wx.Colour(65, 65, 65, 255)
white = wx.Colour(255, 255, 255, 255)
darkblue = wx.Colour(30, 30, 150, 255)
codeSyntaxOkay = wx.Colour(220, 250, 220, 255)  # light green

# regular expression to check for unescaped '$' to indicate code:
_unescapedDollarSign_re = re.compile(r"^\$|[^\\]\$")

# used for separation of internal vs display values:
_localized = {
    # Experiment info dialog:
        'Field': _translate('Field'), 'Default': _translate('Default'),
    # ComponentsPanel category labels:
        'Favorites': _translate('Favorites'), 'Stimuli': _translate('Stimuli'),
        'Responses': _translate('Responses'), 'Custom': _translate('Custom'), 'I/O': _translate('I/O')
    }


class RoutineCanvas(wx.ScrolledWindow):
    """Represents a single routine (used as page in RoutinesNotebook)"""
    def __init__(self, notebook, id=-1, routine=None):
        """This window is based heavily on the PseudoDC demo of wxPython
        """
        wx.ScrolledWindow.__init__(self, notebook, id, (0, 0), style=wx.SUNKEN_BORDER)

        self.SetBackgroundColour(canvasColor)
        self.notebook=notebook
        self.frame=notebook.frame
        self.app=self.frame.app
        self.dpi=self.app.dpi
        self.lines = []
        self.maxWidth  = 15*self.dpi
        self.maxHeight = 15*self.dpi
        self.x = self.y = 0
        self.curLine = []
        self.drawing = False
        self.drawSize = self.app.prefs.appData['routineSize']
        # auto-rescale based on number of components and window size looks jumpy
        # when switch between routines of diff drawing sizes
        self.iconSize = (24,24,48)[self.drawSize] # only 24, 48 so far
        self.fontBaseSize = (800,900,1000)[self.drawSize] # depends on OS?

        self.SetVirtualSize((self.maxWidth, self.maxHeight))
        self.SetScrollRate(self.dpi/4,self.dpi/4)

        self.routine=routine
        self.yPositions=None
        self.yPosTop=(25,40,60)[self.drawSize]
        self.componentStep=(25,32,50)[self.drawSize]#the step in Y between each component
        self.timeXposStart = (150,150,200)[self.drawSize]
        self.iconXpos = self.timeXposStart - self.iconSize*(1.3,1.5,1.5)[self.drawSize] #the left hand edge of the icons
        self.timeXposEnd = self.timeXposStart + 400 # onResize() overrides

        # create a PseudoDC to record our drawing
        self.pdc = wx.PseudoDC()
        self.pen_cache = {}
        self.brush_cache = {}
        # vars for handling mouse clicks
        self.dragid = -1
        self.lastpos = (0,0)
        self.componentFromID = {}#use the ID of the drawn icon to retrieve component name
        self.contextMenuItems = ['edit','remove','move to top','move up','move down','move to bottom']
        # labels are only for display, and allow localization
        self.contextMenuLabels = {'edit': _translate('edit'), 'remove': _translate('remove'),
                                 'move to top': _translate('move to top'), 'move up': _translate('move up'),
                                 'move down': _translate('move down'), 'move to bottom': _translate('move to bottom')}
        self.contextItemFromID = {}
        self.contextIDFromItem = {}
        for item in self.contextMenuItems:
            id = wx.NewId()
            self.contextItemFromID[id] = item
            self.contextIDFromItem[item] = id

        self.redrawRoutine()

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x:None)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)
        self.Bind(wx.EVT_SIZE, self.onResize)
        #self.SetDropTarget(FileDropTarget(builder = self.frame)) # crashes if drop on OSX

    def onResize(self, event):
        self.sizePix=event.GetSize()
        self.timeXposStart = (150,150,200)[self.drawSize]
        self.timeXposEnd = self.sizePix[0]-(60,80,100)[self.drawSize]
        self.redrawRoutine()#then redraw visible
    def ConvertEventCoords(self, event):
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        return (event.GetX() + (xView * xDelta),
            event.GetY() + (yView * yDelta))
    def OffsetRect(self, r):
        """Offset the rectangle, r, to appear in the given position in the window
        """
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        r.OffsetXY(-(xView*xDelta),-(yView*yDelta))

    def OnMouse(self, event):
        if event.LeftDown():
            x,y = self.ConvertEventCoords(event)
            icons = self.pdc.FindObjectsByBBox(x, y)
            if len(icons):
                self.editComponentProperties(component=self.componentFromID[icons[0]])
        elif event.RightDown():
            x,y = self.ConvertEventCoords(event)
            icons = self.pdc.FindObjectsByBBox(x, y)
            menuPos = event.GetPosition()
            if self.app.prefs.builder['topFlow']:
                menuPos[0] += self.frame.componentButtons.GetSize()[0]  # width of components panel
                menuPos[1] += self.frame.flowPanel.GetSize()[1]  # height of flow panel
            if len(icons):
                self._menuComponent=self.componentFromID[icons[0]]
                self.showContextMenu(self._menuComponent, xy=menuPos)
        elif event.Dragging() or event.LeftUp():
            if self.dragid != -1:
                pass
            if event.LeftUp():
                pass
    def showContextMenu(self, component, xy):
        menu = wx.Menu()
        for item in self.contextMenuItems:
            id = self.contextIDFromItem[item]
            menu.Append( id, self.contextMenuLabels[item] )
            wx.EVT_MENU( menu, id, self.onContextSelect )
        self.frame.PopupMenu( menu, xy )
        menu.Destroy() # destroy to avoid mem leak

    def onContextSelect(self, event):
        """Perform a given action on the component chosen
        """
        op = self.contextItemFromID[event.GetId()]
        component=self._menuComponent
        r = self.routine
        if op=='edit':
            self.editComponentProperties(component=component)
        elif op=='remove':
            r.removeComponent(component)
            self.frame.addToUndoStack("REMOVE `%s` from Routine" %(component.params['name'].val))
            self.frame.exp.namespace.remove(component.params['name'].val)
        elif op.startswith('move'):
            lastLoc=r.index(component)
            r.remove(component)
            if op=='move to top':
                r.insert(0, component)
            if op=='move up':
                r.insert(lastLoc-1, component)
            if op=='move down':
                r.insert(lastLoc+1, component)
            if op=='move to bottom':
                r.append(component)
            self.frame.addToUndoStack("MOVED `%s`" %component.params['name'].val)
        self.redrawRoutine()
        self._menuComponent=None
    def OnPaint(self, event):
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.
        dc = wx.GCDC(wx.BufferedPaintDC(self))
        # we need to clear the dc BEFORE calling PrepareDC
        bg = wx.Brush(self.GetBackgroundColour())
        dc.SetBackground(bg)
        dc.Clear()
        # use PrepareDC to set position correctly
        self.PrepareDC(dc)
        # create a clipping rect from our position and size
        # and the Update Region
        xv, yv = self.GetViewStart()
        dx, dy = self.GetScrollPixelsPerUnit()
        x, y   = (xv * dx, yv * dy)
        rgn = self.GetUpdateRegion()
        rgn.Offset(x,y)
        r = rgn.GetBox()
        # draw to the dc using the calculated clipping rect
        self.pdc.DrawToDCClipped(dc,r)

    def redrawRoutine(self):
        self.pdc.Clear()#clear the screen
        self.pdc.RemoveAll()#clear all objects (icon buttons)

        self.pdc.BeginDrawing()

        #work out where the component names and icons should be from name lengths
        self.setFontSize(self.fontBaseSize/self.dpi, self.pdc)
        longest = 0
        w = 50
        for comp in self.routine:
            name = comp.params['name'].val
            if len(name)>longest:
                longest=len(name)
                w = self.GetFullTextExtent(name)[0]
        self.timeXpos = w+(50,50,90)[self.drawSize]

        #separate components according to whether they are drawn in separate row
        rowComponents = []
        staticCompons = []
        for n, component in enumerate(self.routine):
            if component.type == 'Static':
                staticCompons.append(component)
            else:
                rowComponents.append(component)

        # draw static, time grid, normal (row) comp:
        yPos = self.yPosTop
        yPosBottom = yPos + len(rowComponents) * self.componentStep
        # draw any Static Components first (below the grid)
        for component in staticCompons:
            bottom = max(yPosBottom,self.GetSize()[1])
            self.drawStatic(self.pdc, component, yPos, bottom)
        self.drawTimeGrid(self.pdc,yPos,yPosBottom)
        #normal components, one per row
        for component in rowComponents:
            self.drawComponent(self.pdc, component, yPos)
            yPos+=self.componentStep

        self.SetVirtualSize((self.maxWidth, yPos+50))#the 50 allows space for labels below the time axis
        self.pdc.EndDrawing()
        self.Refresh()#refresh the visible window after drawing (using OnPaint)
    def getMaxTime(self):
        """Return the max time to be drawn in the window
        """
        maxTime, nonSlip = self.routine.getMaxTime()
        if self.routine.hasOnlyStaticComp():
            maxTime = int(maxTime) + 1.0
        return maxTime
    def drawTimeGrid(self, dc, yPosTop, yPosBottom, labelAbove=True):
        """Draws the grid of lines and labels the time axes
        """
        tMax=self.getMaxTime()*1.1
        xScale = self.getSecsPerPixel()
        xSt=self.timeXposStart
        xEnd=self.timeXposEnd

        #dc.SetId(wx.NewId())
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0, 150)))
        #draw horizontal lines on top and bottom
        dc.DrawLine(x1=xSt,y1=yPosTop,
                    x2=xEnd,y2=yPosTop)
        dc.DrawLine(x1=xSt,y1=yPosBottom,
                    x2=xEnd,y2=yPosBottom)
        #draw vertical time points
        unitSize = 10**numpy.ceil(numpy.log10(tMax*0.8))/10.0#gives roughly 1/10 the width, but in rounded to base 10 of 0.1,1,10...
        if tMax/unitSize < 3:
            unitSize = 10**numpy.ceil(numpy.log10(tMax*0.8))/50.0#gives units of 2 (0.2,2,20)
        elif tMax/unitSize < 6:
            unitSize = 10**numpy.ceil(numpy.log10(tMax*0.8))/20.0#gives units of 5 (0.5,5,50)
        for lineN in range(int(numpy.floor(tMax/unitSize))):
            dc.DrawLine(xSt+lineN*unitSize/xScale, yPosTop-4,#vertical line
                    xSt+lineN*unitSize/xScale, yPosBottom+4)
            dc.DrawText('%.2g' %(lineN*unitSize),xSt+lineN*unitSize/xScale-4,yPosTop-20)#label above
            if yPosBottom>300:#if bottom of grid is far away then draw labels here too
                dc.DrawText('%.2g' %(lineN*unitSize),xSt+lineN*unitSize/xScale-4,yPosBottom+10)#label below
        #add a label
        self.setFontSize(self.fontBaseSize/self.dpi, dc)
        dc.DrawText('t (sec)',xEnd+5,yPosTop-self.GetFullTextExtent('t')[1]/2.0)#y is y-half height of text
        # or draw bottom labels only if scrolling is turned on, virtual size > available size?
        if yPosBottom>300:#if bottom of grid is far away then draw labels there too
            dc.DrawText('t (sec)',xEnd+5,yPosBottom-self.GetFullTextExtent('t')[1]/2.0)#y is y-half height of text
    def setFontSize(self, size, dc):
        font = self.GetFont()
        font.SetPointSize(size)
        dc.SetFont(font)
    def drawStatic(self, dc, component, yPosTop, yPosBottom):
        """draw a static (ISI) component box"""
        #set an id for the region of this component (so it can act as a button)
        ##see if we created this already
        id=None
        for key in self.componentFromID.keys():
            if self.componentFromID[key]==component:
                id=key
        if not id: #then create one and add to the dict
            id = wx.NewId()
            self.componentFromID[id]=component
        dc.SetId(id)
        #deduce start and stop times if possible
        startTime, duration, nonSlipSafe = component.getStartAndDuration()
        # ensure static comps are clickable (even if $code start or duration)
        unknownTiming = False
        if startTime is None:
            startTime = 0
            unknownTiming = True
        if duration is None:
            duration = 0  # minimal extent ensured below
            unknownTiming = True
        #calculate rectangle for component
        xScale = self.getSecsPerPixel()
        dc.SetPen(wx.Pen(wx.Colour(200, 100, 100, 0), style=wx.TRANSPARENT))
        dc.SetBrush(wx.Brush(staticTimeColor))
        xSt = self.timeXposStart + startTime / xScale
        w = duration / xScale + 1  # +1 to compensate for border alpha=0 in dc.SetPen
        w = max(min(w, 10000), 2)  # ensure 2..10000 pixels
        h = yPosBottom-yPosTop
        # name label, position:
        name = component.params['name'].val  # "ISI"
        if unknownTiming:
            # flag it as not literally represented in time, e.g., $code duration
            name += ' ???'
        nameW, nameH = self.GetFullTextExtent(name)[0:2]
        x = xSt+w/2
        staticLabelTop = (0, 50, 60)[self.drawSize]
        y = staticLabelTop - nameH * 3
        fullRect = wx.Rect(x-20,y,nameW, nameH)
        #draw the rectangle, draw text on top:
        dc.DrawRectangle(xSt, yPosTop-nameH*4, w, h+nameH*5)
        dc.DrawText(name, x-nameW/2, y)
        fullRect.Union(wx.Rect(xSt, yPosTop, w, h))#update bounds to include time bar
        dc.SetIdBounds(id,fullRect)
    def drawComponent(self, dc, component, yPos):
        """Draw the timing of one component on the timeline"""
        #set an id for the region of this component (so it can act as a button)
        ##see if we created this already
        id=None
        for key in self.componentFromID.keys():
            if self.componentFromID[key]==component:
                id=key
        if not id: #then create one and add to the dict
            id = wx.NewId()
            self.componentFromID[id]=component
        dc.SetId(id)

        iconYOffset = (6,6,0)[self.drawSize]
        thisIcon = components.icons[component.getType()][str(self.iconSize)]#getType index 0 is main icon
        dc.DrawBitmap(thisIcon, self.iconXpos,yPos+iconYOffset, True)
        fullRect = wx.Rect(self.iconXpos, yPos, thisIcon.GetWidth(),thisIcon.GetHeight())

        self.setFontSize(self.fontBaseSize/self.dpi, dc)

        name = component.params['name'].val
        #get size based on text
        w,h = self.GetFullTextExtent(name)[0:2]
        #draw text
        x = self.iconXpos-self.dpi/10-w + (self.iconSize,self.iconSize,10)[self.drawSize]
        y = yPos+thisIcon.GetHeight()/2-h/2 + (5,5,-2)[self.drawSize]
        dc.DrawText(name, x-20, y)
        fullRect.Union(wx.Rect(x-20,y,w,h))

        #deduce start and stop times if possible
        startTime, duration, nonSlipSafe = component.getStartAndDuration()
        #draw entries on timeline (if they have some time definition)
        if startTime!=None and duration!=None:#then we can draw a sensible time bar!
            xScale = self.getSecsPerPixel()
            dc.SetPen(wx.Pen(wx.Colour(200, 100, 100, 0), style=wx.TRANSPARENT))
            dc.SetBrush(wx.Brush(routineTimeColor))
            hSize = (3.5,2.75,2)[self.drawSize]
            yOffset = (3,3,0)[self.drawSize]
            h = self.componentStep/hSize
            xSt = self.timeXposStart + startTime / xScale
            w = duration / xScale + 1
            if w > 10000:
                w = 10000 #limit width to 10000 pixels!
            if w < 2:
                w = 2  #make sure at least one pixel shows
            dc.DrawRectangle(xSt, y+yOffset, w,h )
            fullRect.Union(wx.Rect(xSt, y+yOffset, w,h ))#update bounds to include time bar
        dc.SetIdBounds(id,fullRect)

    def editComponentProperties(self, event=None, component=None):
        if event:  #we got here from a wx.button press (rather than our own drawn icons)
            componentName = event.EventObject.GetName()
            component = self.routine.getComponentFromName(componentName)
        #does this component have a help page?
        if hasattr(component, 'url'):
            helpUrl = component.url
        else:
            helpUrl = None
        old_name = component.params['name'].val
        #check current timing settings of component (if it changes we need to update views)
        timings = component.getStartAndDuration()
        #create the dialog
        if isinstance(component,components.code.CodeComponent):
            dlg = DlgCodeComponentProperties(frame=self.frame,
                title=component.params['name'].val+' Properties',
                params = component.params,
                order = component.order,
                helpUrl=helpUrl, editing=True)
        else:
            dlg = DlgComponentProperties(frame=self.frame,
                title=component.params['name'].val+' Properties',
                params = component.params,
                order = component.order,
                helpUrl=helpUrl, editing=True)
        if dlg.OK:
            if component.getStartAndDuration() != timings:
                self.redrawRoutine()#need to refresh timings section
                self.Refresh()#then redraw visible
                self.frame.flowPanel.draw()
#                self.frame.flowPanel.Refresh()
            elif component.params['name'].val != old_name:
                self.redrawRoutine() #need to refresh name
            self.frame.exp.namespace.remove(old_name)
            self.frame.exp.namespace.add(component.params['name'].val)
            self.frame.addToUndoStack("EDIT `%s`" %component.params['name'].val)

    def getSecsPerPixel(self):
        return float(self.getMaxTime())/(self.timeXposEnd-self.timeXposStart)

class RoutinesNotebook(aui.AuiNotebook):
    """A notebook that stores one or more routines
    """
    def __init__(self, frame, id=-1):
        self.frame=frame
        self.app=frame.app
        self.routineMaxSize = 2
        self.appData = self.app.prefs.appData
        aui.AuiNotebook.__init__(self, frame, id)

        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.onClosePane)
        if not hasattr(self.frame, 'exp'):
            return#we haven't yet added an exp
    def getCurrentRoutine(self):
        routinePage=self.getCurrentPage()
        if routinePage:
            return routinePage.routine
        else: #no routine page
            return None
    def setCurrentRoutine(self, routine):
        for ii in range(self.GetPageCount()):
            if routine is self.GetPage(ii).routine:
                self.SetSelection(ii)
    def getCurrentPage(self):
        if self.GetSelection()>=0:
            return self.GetPage(self.GetSelection())
        else:#there are no routine pages
            return None
    def addRoutinePage(self, routineName, routine):
#        routinePage = RoutinePage(parent=self, routine=routine)
        routinePage = RoutineCanvas(notebook=self, routine=routine)
        self.AddPage(routinePage, routineName)
    def removePages(self):
        for ii in range(self.GetPageCount()):
            currId = self.GetSelection()
            self.DeletePage(currId)
    def createNewRoutine(self, returnName=False):
        dlg = wx.TextEntryDialog(self, message=_translate("What is the name for the new Routine? (e.g. instr, trial, feedback)"),
            caption=_translate('New Routine'))
        exp = self.frame.exp
        routineName = None
        if dlg.ShowModal() == wx.ID_OK:
            routineName=dlg.GetValue()
            # silently auto-adjust the name to be valid, and register in the namespace:
            routineName = exp.namespace.makeValid(routineName, prefix='routine')
            exp.namespace.add(routineName) #add to the namespace
            exp.addRoutine(routineName)#add to the experiment
            self.addRoutinePage(routineName, exp.routines[routineName])#then to the notebook
            self.frame.addToUndoStack("NEW Routine `%s`" %routineName)
        dlg.Destroy()
        if returnName:
            return routineName
    def onClosePane(self, event=None):
        """Close the pane and remove the routine from the exp
        """
        routine = self.GetPage(event.GetSelection()).routine
        name=routine.name
        #update experiment object, namespace, and flow window (if this is being used)
        if name in self.frame.exp.routines.keys():
            # remove names of the routine and all its components from namespace
            for c in self.frame.exp.routines[name]:
                self.frame.exp.namespace.remove(c.params['name'].val)
            self.frame.exp.namespace.remove(self.frame.exp.routines[name].name)
            del self.frame.exp.routines[name]
        if routine in self.frame.exp.flow:
            self.frame.exp.flow.removeComponent(routine)
            self.frame.flowPanel.draw()
        self.frame.addToUndoStack("REMOVE Routine `%s`" %(name))
    def increaseSize(self, event=None):
        self.appData['routineSize'] = min(self.routineMaxSize, self.appData['routineSize'] + 1)
        with WindowFrozen(self):
            self.redrawRoutines()
    def decreaseSize(self, event=None):
        self.appData['routineSize'] = max(0, self.appData['routineSize'] - 1)
        with WindowFrozen(self):
            self.redrawRoutines()
    def redrawRoutines(self):
        """Removes all the routines, adds them back and sets current back to orig
        """
        currPage = self.GetSelection()
        self.removePages()
        displayOrder = sorted(self.frame.exp.routines.keys())  # alphabetical
        for routineName in displayOrder:
            self.addRoutinePage(routineName, self.frame.exp.routines[routineName])
        if currPage>-1:
            self.SetSelection(currPage)

class ComponentsPanel(scrolledpanel.ScrolledPanel):
    def __init__(self, frame, id=-1):
        """A panel that displays available components.
        """
        self.frame=frame
        self.app=frame.app
        self.dpi=self.app.dpi
        if self.app.prefs.app['largeIcons']:
            panelWidth = 3*48+50
        else:
            panelWidth = 3*24+50
        scrolledpanel.ScrolledPanel.__init__(self,frame,id,size=(panelWidth,10*self.dpi))
        self.sizer=wx.BoxSizer(wx.VERTICAL)
        self.components=experiment.getAllComponents(self.app.prefs.builder['componentsFolders'])
        categories = ['Favorites']
        categories.extend(components.getAllCategories(self.app.prefs.builder['componentsFolders']))
        #get rid of hidden components
        for hiddenComp in self.frame.prefs['hiddenComponents']:
            if hiddenComp in self.components:
                del self.components[hiddenComp]
        del self.components['SettingsComponent']#also remove settings - that's in toolbar not components panel
        #get favorites
        self.favorites = FavoriteComponents(componentsPanel=self)
        #create labels and sizers for each category
        self.componentFromID={}
        self.panels={}
        self.sizerList=[]#to keep track of the objects (sections and section labels) within the main sizer

        for categ in categories:
            if sys.platform.startswith('linux'): # Localized labels on PlateButton may be corrupted in Ubuntu.
                label = categ
            else:
                if categ in _localized.keys():
                    label = _localized[categ]
                else:
                    label = categ
            sectionBtn = platebtn.PlateButton(self,-1,label,
                style=platebtn.PB_STYLE_DROPARROW, name=categ)
            sectionBtn.Bind(wx.EVT_LEFT_DOWN, self.onSectionBtn) #mouse event must be bound like this
            sectionBtn.Bind(wx.EVT_RIGHT_DOWN, self.onSectionBtn) #mouse event must be bound like this
            if self.app.prefs.app['largeIcons']:
                self.panels[categ] = wx.FlexGridSizer(cols=1)
            else:
                self.panels[categ]=wx.FlexGridSizer(cols=2)
            self.sizer.Add(sectionBtn, flag=wx.EXPAND)
            self.sizerList.append(sectionBtn)
            self.sizer.Add(self.panels[categ], flag=wx.ALIGN_CENTER)
            self.sizerList.append(self.panels[categ])
        self.makeComponentButtons()
        self._rightClicked=None
        #start all except for Favorites collapsed
        for section in categories[1:]:
            self.toggleSection(self.panels[section])

        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)
        self.SetupScrolling()
        self.SetDropTarget(FileDropTarget(builder = self.frame))

    def on_resize(self, event):
        if self.app.prefs.app['largeIcons']:
            cols = self.GetClientSize()[0] / 58
        else:
            cols = self.GetClientSize()[0] / 34
        for category in self.panels.values():
            category.SetCols(max(1, cols))

    def makeFavoriteButtons(self):
        #add a copy of each favorite to that panel first
        for thisName in self.favorites.getFavorites():
            self.addComponentButton(thisName, self.panels['Favorites'])
    def makeComponentButtons(self):
        """Make all the components buttons, including a call to makeFavorite() buttons
        """
        self.makeFavoriteButtons()
        #then add another copy for each category that the component itself lists
        for thisName in self.components.keys():
            thisComp=self.components[thisName]
            #NB thisComp is a class - we can't use its methods/attribs until it is an instance
            for category in thisComp.categories:
                panel = self.panels[category]
                self.addComponentButton(thisName, panel)
    def addComponentButton(self, name, panel):
        """Create a component button and add it to a specific panel's sizer
        """
        thisComp=self.components[name]
        shortName=name
        for redundant in ['component','Component']:
            if redundant in name:
                shortName=name.replace(redundant, "")
        if self.app.prefs.app['largeIcons']:
            thisIcon = components.icons[name]['48add']#index 1 is the 'add' icon
        else:
            thisIcon = components.icons[name]['24add']#index 1 is the 'add' icon
        btn = wx.BitmapButton(self, -1, thisIcon,
                       size=(thisIcon.GetWidth()+10, thisIcon.GetHeight()+10),
                       name=thisComp.__name__)
        if name in components.tooltips:
            thisTip = components.tooltips[name]
        else:
            thisTip = shortName
        btn.SetToolTip(wx.ToolTip(thisTip))
        self.componentFromID[btn.GetId()]=name
        btn.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick) #use btn.bind instead of self.Bind in oder to trap event here
        self.Bind(wx.EVT_BUTTON, self.onClick, btn)
        panel.Add(btn, proportion=0, flag=wx.ALIGN_RIGHT)#,wx.EXPAND|wx.ALIGN_CENTER )

    def onSectionBtn(self,evt):
        if hasattr(evt,'GetString'):
            buttons = self.panels[evt.GetString()]
        else:
            btn = evt.GetEventObject()
            buttons = self.panels[btn.GetName()]
        self.toggleSection(buttons)
    def toggleSection(self, section):
        ii = self.sizerList.index(section)
        self.sizer.Show( ii, not self.sizer.IsShown(ii) ) #ie toggle this item
        self.sizer.Layout()
        self.SetupScrolling()
    def getIndexInSizer(self, obj, sizer):
        """Find index of an item within a sizer (to see if it's there or to toggle visibility)
        WX sizers don't (as of v2.8.11) have a way to find the index of their contents. This method helps
        get around that.
        """
        #if the obj is itself a sizer (e.g. within the main sizer then we can't even use
        #sizer.Children (as far as I can work out) so we keep a list to track the contents
        if sizer==self.sizer:#for the main sizer we kept track of everything with a list
            return self.sizerList.index(obj)
        else:
            #let's just hope the
            index = None
            for ii, child in enumerate(sizer.Children):
                if child.GetWindow()==obj:
                    index=ii
                    break
            return index
    def onRightClick(self, evt):
        btn = evt.GetEventObject()
        self._rightClicked = btn
        index = self.getIndexInSizer(btn, self.panels['Favorites'])
        if index is None:
            #not currently in favs
            msg = "Add to favorites"
            function = self.onAddToFavorites
        else:
            #is currently in favs
            msg = "Remove from favorites"
            function = self.onRemFromFavorites
        msgLocalized = {"Add to favorites": _translate("Add to favorites"),
                        "Remove from favorites": _translate("Remove from favorites")}
        menu = wx.Menu()
        id = wx.NewId()
        menu.Append(id, msgLocalized[msg] )
        wx.EVT_MENU(menu, id, function)
        #where to put the context menu
        x,y = evt.GetPosition()#this is position relative to object
        xBtn,yBtn = evt.GetEventObject().GetPosition()
        self.PopupMenu( menu, (x+xBtn, y+yBtn) )
        menu.Destroy() # destroy to avoid mem leak
    def onClick(self,evt):
        #get name of current routine
        currRoutinePage = self.frame.routinePanel.getCurrentPage()
        if not currRoutinePage:
            dialogs.MessageDialog(self,_translate("Create a routine (Experiment menu) before adding components"),
                type='Info', title=_translate('Error')).ShowModal()
            return False
        currRoutine = self.frame.routinePanel.getCurrentRoutine()
        #get component name
        newClassStr = self.componentFromID[evt.GetId()]
        componentName = newClassStr.replace('Component','')
        newCompClass = self.components[newClassStr]
        newComp = newCompClass(parentName=currRoutine.name, exp=self.frame.exp)
        #does this component have a help page?
        if hasattr(newComp, 'url'):
            helpUrl = newComp.url
        else:
            helpUrl = None
        #create component template
        if componentName=='Code':
            dlg = DlgCodeComponentProperties(frame=self.frame,
                title=componentName+' Properties',
                params=newComp.params,
                order=newComp.order,
                helpUrl=helpUrl)
        else:
            dlg = DlgComponentProperties(frame=self.frame,
                title=componentName+' Properties',
                params=newComp.params,
                order=newComp.order,
                helpUrl=helpUrl)

        compName = newComp.params['name']
        if dlg.OK:
            currRoutine.addComponent(newComp)#add to the actual routing
            namespace = self.frame.exp.namespace
            newComp.params['name'].val = namespace.makeValid(newComp.params['name'].val)
            namespace.add(newComp.params['name'].val)
            currRoutinePage.redrawRoutine()#update the routine's view with the new component too
            self.frame.addToUndoStack("ADD `%s` to `%s`" %(compName, currRoutine.name))
            wasNotInFavs = (not newClassStr in self.favorites.getFavorites())
            self.favorites.promoteComponent(newClassStr, 1)
            #was that promotion enough to be a favorite?
            if wasNotInFavs and newClassStr in self.favorites.getFavorites():
                self.addComponentButton(newClassStr, self.panels['Favorites'])
                self.sizer.Layout()
        return True

    def onAddToFavorites(self, evt=None, btn=None):
        if btn is None:
            btn = self._rightClicked
        if btn.Name not in self.favorites.getFavorites():#check we aren't duplicating
            self.favorites.makeFavorite(btn.Name)
            self.addComponentButton(btn.Name, self.panels['Favorites'])
        self.sizer.Layout()
        self._rightClicked = None

    def onRemFromFavorites(self, evt=None, btn=None):
        if btn is None:
            btn = self._rightClicked
        index = self.getIndexInSizer(btn,self.panels['Favorites'])
        if index is None:
            pass
        else:
            self.favorites.setLevel(btn.Name, -100)
            btn.Destroy()
        self.sizer.Layout()
        self._rightClicked = None

class FavoriteComponents(object):

    def __init__(self, componentsPanel, threshold=20, neutral=0):
        self.threshold=20
        self.neutral=0
        self.panel = componentsPanel
        self.frame = componentsPanel.frame
        self.app = self.frame.app
        self.prefs = self.app.prefs
        self.currentLevels  = self.prefs.appDataCfg['builder']['favComponents']
        self.setDefaults()
    def setDefaults(self):
        #set those that are favorites by default
        for comp in ['ImageComponent','KeyboardComponent','SoundComponent','TextComponent']:
            if comp not in self.currentLevels.keys():
                self.currentLevels[comp]=self.threshold
        for comp in self.panel.components.keys():
            if comp not in self.currentLevels.keys():
                self.currentLevels[comp]=self.neutral

    def makeFavorite(self, compName):
        """Set the value of this component to an arbitrary high value (10000)
        """
        self.currentLevels[compName] = 10000
    def promoteComponent(self, compName, value=1):
        """Promote this component by a certain value (can be negative to demote)
        """
        self.currentLevels[compName] += value
    def setLevel(self, compName, value=0):
        """Set the level to neutral (0) favourite (20?) or banned (-1000?)
        """
        self.currentLevels[compName] = value
    def getFavorites(self):
        """Returns a list of favorite components. Each must have level greater
        than the threshold and there will be not more than
        max length prefs['builder']['maxFavorites']
        """
        sortedVals = sorted(self.currentLevels.items(), key=lambda x: x[1], reverse=True)
        favorites=[]
        for name, level in sortedVals:
            if level>=10000:#this has been explicitly requested (or REALLY liked!)
                favorites.append(name)
            elif level>=self.threshold and len(favorites)<self.prefs.builder['maxFavorites']:
                favorites.append(name)
            else:
                #either we've run out of levels>10000 or exceeded maxFavs or runout of level>=thresh
                break
        return favorites


class BuilderFrame(wx.Frame):
    def __init__(self, parent, id=-1, title='PsychoPy (Experiment Builder)',
                 pos=wx.DefaultPosition, fileName=None,frameData=None,
                 style=wx.DEFAULT_FRAME_STYLE, app=None):

        if fileName is not None:
            fileName = fileName.decode(sys.getfilesystemencoding())

        self.app=app
        self.dpi=self.app.dpi
        self.appData = self.app.prefs.appData['builder']#things the user doesn't set like winsize etc
        self.prefs = self.app.prefs.builder#things about the coder that get set
        self.appPrefs = self.app.prefs.app
        self.paths = self.app.prefs.paths
        self.IDs = self.app.IDs
        self.frameType='builder'
        self.filename = fileName

        if fileName in self.appData['frames'].keys():
            self.frameData = self.appData['frames'][fileName]
        else:#work out a new frame size/location
            dispW,dispH = self.app.getPrimaryDisplaySize()
            default=self.appData['defaultFrame']
            default['winW'], default['winH'],  = int(dispW*0.75), int(dispH*0.75)
            if default['winX']+default['winW']>dispW:
                default['winX']=5
            if default['winY']+default['winH']>dispH:
                default['winY']=5
            self.frameData = dict(self.appData['defaultFrame'])#take a copy
            #increment default for next frame
            default['winX']+=10
            default['winY']+=10

        if self.frameData['winH']==0 or self.frameData['winW']==0:#we didn't have the key or the win was minimized/invalid

            self.frameData['winX'], self.frameData['winY'] = (0,0)
            usingDefaultSize=True
        else:
            usingDefaultSize=False
        if self.frameData['winY'] < 20:
            self.frameData['winY'] = 20
        wx.Frame.__init__(self, parent=parent, id=id, title=title,
                            pos=(int(self.frameData['winX']), int(self.frameData['winY'])),
                            size=(int(self.frameData['winW']),int(self.frameData['winH'])),
                            style=style)
        self.Bind(wx.EVT_CLOSE, self.closeFrame)
        self.panel = wx.Panel(self)
        #create icon
        if sys.platform=='darwin':
            pass#doesn't work and not necessary - handled by application bundle
        else:
            iconFile = os.path.join(self.paths['resources'], 'psychopy.ico')
            if os.path.isfile(iconFile):
                self.SetIcon(wx.Icon(iconFile, wx.BITMAP_TYPE_ICO))

        # create our panels
        self.flowPanel=FlowPanel(frame=self)
        self.routinePanel=RoutinesNotebook(self)
        self.componentButtons=ComponentsPanel(self)
        #menus and toolbars
        self.makeToolbar()
        self.makeMenus()
        self.CreateStatusBar()
        self.SetStatusText("")

        #setup universal shortcuts
        accelTable = self.app.makeAccelTable()
        self.SetAcceleratorTable(accelTable)

        #set stdout to correct output panel
        self.stdoutOrig = sys.stdout
        self.stderrOrig = sys.stderr
        self.stdoutFrame=stdOutRich.StdOutFrame(parent=self, app=self.app, size=(700,300))

        #setup a default exp
        if fileName!=None and os.path.isfile(fileName):
            self.fileOpen(filename=fileName, closeCurrent=False)
        else:
            self.lastSavedCopy=None
            self.fileNew(closeCurrent=False)#don't try to close before opening
        self.updateReadme()

        #control the panes using aui manager
        self._mgr = aui.AuiManager(self)
        if self.prefs['topFlow']:
            self._mgr.AddPane(self.flowPanel,
                              aui.AuiPaneInfo().
                              Name("Flow").Caption("Flow").BestSize((8*self.dpi,2*self.dpi)).
                              RightDockable(True).LeftDockable(True).CloseButton(False).
                              Top())
            self._mgr.AddPane(self.componentButtons, aui.AuiPaneInfo().
                              Name("Components").Caption("Components").
                              RightDockable(True).LeftDockable(True).CloseButton(False).
                              Left())
            self._mgr.AddPane(self.routinePanel, aui.AuiPaneInfo().
                              Name("Routines").Caption("Routines").
                              CenterPane(). #'center panes' expand to fill space
                              CloseButton(False).MaximizeButton(True))
        else:
            self._mgr.AddPane(self.routinePanel, aui.AuiPaneInfo().
                              Name("Routines").Caption("Routines").
                              CenterPane(). #'center panes' expand to fill space
                              CloseButton(False).MaximizeButton(True))
            self._mgr.AddPane(self.componentButtons, aui.AuiPaneInfo().
                              Name("Components").Caption("Components").
                              RightDockable(True).LeftDockable(True).CloseButton(False).
                              Right())
            self._mgr.AddPane(self.flowPanel,
                              aui.AuiPaneInfo().
                              Name("Flow").Caption("Flow").BestSize((8*self.dpi,2*self.dpi)).
                              RightDockable(True).LeftDockable(True).CloseButton(False).
                              Bottom())
        #tell the manager to 'commit' all the changes just made
        self._mgr.Update()
        #self.SetSizer(self.mainSizer)#not necessary for aui type controls
        if self.frameData['auiPerspective']:
            self._mgr.LoadPerspective(self.frameData['auiPerspective'])
        self.SetMinSize(wx.Size(600, 400)) #min size for the whole window
        self.SetSize((int(self.frameData['winW']),int(self.frameData['winH'])))
        self.SendSizeEvent()
        self._mgr.Update()

        #self.SetAutoLayout(True)
        self.Bind(wx.EVT_CLOSE, self.closeFrame)
        self.Bind(wx.EVT_END_PROCESS, self.onProcessEnded)
    def makeToolbar(self):
        #---toolbar---#000000#FFFFFF----------------------------------------------
        self.toolbar = self.CreateToolBar( (wx.TB_HORIZONTAL
            | wx.NO_BORDER
            | wx.TB_FLAT))

        if sys.platform=='win32' or sys.platform.startswith('linux'):
            if self.appPrefs['largeIcons']:
                toolbarSize = 32
            else:
                toolbarSize = 16
        else:
            toolbarSize = 32  # mac: 16 either doesn't work, or looks really bad with wx3
        self.toolbar.SetToolBitmapSize((toolbarSize,toolbarSize))
        new_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'filenew%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        open_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'fileopen%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        save_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'filesave%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        saveAs_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'filesaveas%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        undo_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'undo%i.png' %toolbarSize),wx.BITMAP_TYPE_PNG)
        redo_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'redo%i.png' %toolbarSize),wx.BITMAP_TYPE_PNG)
        stop_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'stop%i.png' %toolbarSize),wx.BITMAP_TYPE_PNG)
        run_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'run%i.png' %toolbarSize),wx.BITMAP_TYPE_PNG)
        compile_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'compile%i.png' %toolbarSize),wx.BITMAP_TYPE_PNG)
        settings_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'settingsExp%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        preferences_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'preferences%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        monitors_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'monitors%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)
        #colorpicker_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'color%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)

        ctrlKey = 'Ctrl+'  # show key-bindings in tool-tips in an OS-dependent way
        if sys.platform == 'darwin':
            ctrlKey = 'Cmd+'
        self.toolbar.AddSimpleTool(self.IDs.tbFileNew, new_bmp, (_translate("New [%s]") %self.app.keys['new']).replace('Ctrl+', ctrlKey), _translate("Create new experiment file"))
        self.toolbar.Bind(wx.EVT_TOOL, self.app.newBuilderFrame, id=self.IDs.tbFileNew)
        self.toolbar.AddSimpleTool(self.IDs.tbFileOpen, open_bmp, (_translate("Open [%s]") %self.app.keys['open']).replace('Ctrl+', ctrlKey), _translate("Open an existing experiment file"))
        self.toolbar.Bind(wx.EVT_TOOL, self.fileOpen, id=self.IDs.tbFileOpen)
        self.toolbar.AddSimpleTool(self.IDs.tbFileSave, save_bmp, (_translate("Save [%s]") %self.app.keys['save']).replace('Ctrl+', ctrlKey),  _translate("Save current experiment file"))
        self.toolbar.EnableTool(self.IDs.tbFileSave, False)
        self.toolbar.Bind(wx.EVT_TOOL, self.fileSave, id=self.IDs.tbFileSave)
        self.toolbar.AddSimpleTool(self.IDs.tbFileSaveAs, saveAs_bmp, (_translate("Save As... [%s]") %self.app.keys['saveAs']).replace('Ctrl+', ctrlKey), _translate("Save current experiment file as..."))
        self.toolbar.Bind(wx.EVT_TOOL, self.fileSaveAs, id=self.IDs.tbFileSaveAs)
        self.toolbar.AddSimpleTool(self.IDs.tbUndo, undo_bmp, (_translate("Undo [%s]") %self.app.keys['undo']).replace('Ctrl+', ctrlKey), _translate("Undo last action"))
        self.toolbar.Bind(wx.EVT_TOOL, self.undo, id=self.IDs.tbUndo)
        self.toolbar.AddSimpleTool(self.IDs.tbRedo, redo_bmp, (_translate("Redo [%s]") %self.app.keys['redo']).replace('Ctrl+', ctrlKey),  _translate("Redo last action"))
        self.toolbar.Bind(wx.EVT_TOOL, self.redo, id=self.IDs.tbRedo)
        self.toolbar.AddSeparator()
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(self.IDs.tbPreferences, preferences_bmp, _translate("Preferences"),  _translate("Application preferences"))
        self.toolbar.Bind(wx.EVT_TOOL, self.app.showPrefs, id=self.IDs.tbPreferences)
        self.toolbar.AddSimpleTool(self.IDs.tbMonitorCenter, monitors_bmp, _translate("Monitor Center"),  _translate("Monitor settings and calibration"))
        self.toolbar.Bind(wx.EVT_TOOL, self.app.openMonitorCenter, id=self.IDs.tbMonitorCenter)
        #self.toolbar.AddSimpleTool(self.IDs.tbColorPicker, colorpicker_bmp, "Color Picker",  "Color Picker")
        #self.toolbar.Bind(wx.EVT_TOOL, self.app.colorPicker, id=self.IDs.tbColorPicker)
        self.toolbar.AddSeparator()
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(self.IDs.tbExpSettings, settings_bmp, _translate("Experiment Settings"),  _translate("Settings for this exp"))
        self.toolbar.Bind(wx.EVT_TOOL, self.setExperimentSettings, id=self.IDs.tbExpSettings)
        self.toolbar.AddSimpleTool(self.IDs.tbCompile, compile_bmp, (_translate("Compile Script [%s]") % self.app.keys['compileScript']).replace('Ctrl+', ctrlKey),  _translate("Compile to script"))
        self.toolbar.Bind(wx.EVT_TOOL, self.compileScript, id=self.IDs.tbCompile)
        self.toolbar.AddSimpleTool(self.IDs.tbRun, run_bmp, (_translate("Run [%s]") %self.app.keys['runScript']).replace('Ctrl+', ctrlKey),  _translate("Run experiment"))
        self.toolbar.Bind(wx.EVT_TOOL, self.runFile, id=self.IDs.tbRun)
        self.toolbar.AddSimpleTool(self.IDs.tbStop, stop_bmp, (_translate("Stop [%s]") %self.app.keys['stopScript']).replace('Ctrl+', ctrlKey),  _translate("Stop experiment"))
        self.toolbar.Bind(wx.EVT_TOOL, self.stopFile, id=self.IDs.tbStop)
        self.toolbar.EnableTool(self.IDs.tbStop,False)
        self.toolbar.Realize()

    def makeMenus(self):
        """ IDs are from app.wxIDs"""

        #---Menus---#000000#FFFFFF--------------------------------------------------
        menuBar = wx.MenuBar()
        #---_file---#000000#FFFFFF--------------------------------------------------
        self.fileMenu = wx.Menu()
        menuBar.Append(self.fileMenu, _translate('&File'))

        #create a file history submenu
        self.fileHistoryMaxFiles = 10
        self.fileHistory = wx.FileHistory(maxFiles=self.fileHistoryMaxFiles)
        self.recentFilesMenu = wx.Menu()
        self.fileHistory.UseMenu(self.recentFilesMenu)
        for filename in self.appData['fileHistory']:
            self.fileHistory.AddFileToHistory(filename)
        self.Bind(
            wx.EVT_MENU_RANGE, self.OnFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9
            )

        self.fileMenu.Append(wx.ID_NEW,     _translate("&New\t%s") %self.app.keys['new'])
        self.fileMenu.Append(wx.ID_OPEN,    _translate("&Open...\t%s") %self.app.keys['open'])
        self.fileMenu.AppendSubMenu(self.recentFilesMenu,_translate("Open &Recent"))
        self.fileMenu.Append(wx.ID_SAVE,    _translate("&Save\t%s") %self.app.keys['save'],  _translate("Save current experiment file"))
        self.fileMenu.Append(wx.ID_SAVEAS,  _translate("Save &as...\t%s") %self.app.keys['saveAs'], _translate("Save current experiment file as..."))
        self.fileMenu.Append(wx.ID_CLOSE,   _translate("&Close file\t%s") %self.app.keys['close'], _translate("Close current experiment"))
        wx.EVT_MENU(self, wx.ID_NEW,  self.app.newBuilderFrame)
        wx.EVT_MENU(self, wx.ID_OPEN,  self.fileOpen)
        wx.EVT_MENU(self, wx.ID_SAVE,  self.fileSave)
        self.fileMenu.Enable(wx.ID_SAVE, False)
        wx.EVT_MENU(self, wx.ID_SAVEAS,  self.fileSaveAs)
        wx.EVT_MENU(self, wx.ID_CLOSE,  self.commandCloseFrame)
        item = self.fileMenu.Append(wx.ID_PREFERENCES, text = _translate("&Preferences\t%s") %self.app.keys['preferences'])
        self.Bind(wx.EVT_MENU, self.app.showPrefs, item)
        #-------------quit
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(wx.ID_EXIT, _translate("&Quit\t%s") %self.app.keys['quit'], _translate("Terminate the program"))
        wx.EVT_MENU(self, wx.ID_EXIT, self.quit)

        self.editMenu = wx.Menu()
        menuBar.Append(self.editMenu, _translate('&Edit'))
        self._undoLabel = self.editMenu.Append(wx.ID_UNDO, _translate("Undo\t%s") %self.app.keys['undo'], _translate("Undo last action"), wx.ITEM_NORMAL)
        wx.EVT_MENU(self, wx.ID_UNDO,  self.undo)
        self._redoLabel = self.editMenu.Append(wx.ID_REDO, _translate("Redo\t%s") %self.app.keys['redo'], _translate("Redo last action"), wx.ITEM_NORMAL)
        wx.EVT_MENU(self, wx.ID_REDO,  self.redo)

        #---_tools---#000000#FFFFFF--------------------------------------------------
        self.toolsMenu = wx.Menu()
        menuBar.Append(self.toolsMenu, _translate('&Tools'))
        self.toolsMenu.Append(self.IDs.monitorCenter, _translate("Monitor Center"), _translate("To set information about your monitor"))
        wx.EVT_MENU(self, self.IDs.monitorCenter,  self.app.openMonitorCenter)

        self.toolsMenu.Append(self.IDs.compileScript, _translate("Compile\t%s") %self.app.keys['compileScript'], _translate("Compile the exp to a script"))
        wx.EVT_MENU(self, self.IDs.compileScript,  self.compileScript)
        self.toolsMenu.Append(self.IDs.runFile, _translate("Run\t%s") %self.app.keys['runScript'], _translate("Run the current script"))
        wx.EVT_MENU(self, self.IDs.runFile,  self.runFile)
        self.toolsMenu.Append(self.IDs.stopFile, _translate("Stop\t%s") %self.app.keys['stopScript'], _translate("Abort the current script"))
        wx.EVT_MENU(self, self.IDs.stopFile,  self.stopFile)

        self.toolsMenu.AppendSeparator()
        self.toolsMenu.Append(self.IDs.openUpdater, _translate("PsychoPy updates..."), _translate("Update PsychoPy to the latest, or a specific, version"))
        wx.EVT_MENU(self, self.IDs.openUpdater,  self.app.openUpdater)
        if hasattr(self.app, 'benchmarkWizard'):
            self.toolsMenu.Append(self.IDs.benchmarkWizard, _translate("Benchmark wizard"), _translate("Check software & hardware, generate report"))
            wx.EVT_MENU(self, self.IDs.benchmarkWizard,  self.app.benchmarkWizard)

        #---_view---#000000#FFFFFF--------------------------------------------------
        self.viewMenu = wx.Menu()
        menuBar.Append(self.viewMenu, _translate('&View'))
        self.viewMenu.Append(self.IDs.openCoderView, _translate("&Open Coder view\t%s") %self.app.keys['switchToCoder'], _translate("Open a new Coder view"))
        wx.EVT_MENU(self, self.IDs.openCoderView,  self.app.showCoder)
        self.viewMenu.Append(self.IDs.toggleReadme, _translate("&Toggle readme\t%s") %self.app.keys['toggleReadme'], _translate("Toggle Readme"))
        wx.EVT_MENU(self, self.IDs.toggleReadme,  self.toggleReadme)
        self.viewMenu.Append(self.IDs.tbIncrFlowSize, _translate("&Flow Larger\t%s") %self.app.keys['largerFlow'], _translate("Larger flow items"))
        wx.EVT_MENU(self, self.IDs.tbIncrFlowSize, self.flowPanel.increaseSize)
        self.viewMenu.Append(self.IDs.tbDecrFlowSize, _translate("&Flow Smaller\t%s") %self.app.keys['smallerFlow'], _translate("Smaller flow items"))
        wx.EVT_MENU(self, self.IDs.tbDecrFlowSize, self.flowPanel.decreaseSize)
        self.viewMenu.Append(self.IDs.tbIncrRoutineSize, _translate("&Routine Larger\t%s") %self.app.keys['largerRoutine'], _translate("Larger routine items"))
        wx.EVT_MENU(self, self.IDs.tbIncrRoutineSize, self.routinePanel.increaseSize)
        self.viewMenu.Append(self.IDs.tbDecrRoutineSize, _translate("&Routine Smaller\t%s") %self.app.keys['smallerRoutine'], _translate("Smaller routine items"))
        wx.EVT_MENU(self, self.IDs.tbDecrRoutineSize, self.routinePanel.decreaseSize)


        #---_experiment---#000000#FFFFFF--------------------------------------------------
        self.expMenu = wx.Menu()
        menuBar.Append(self.expMenu, _translate('&Experiment'))
        self.expMenu.Append(self.IDs.newRoutine, _translate("&New Routine\t%s") %self.app.keys['newRoutine'], _translate("Create a new routine (e.g. the trial definition)"))
        wx.EVT_MENU(self, self.IDs.newRoutine,  self.addRoutine)
        self.expMenu.Append(self.IDs.copyRoutine, _translate("&Copy Routine\t%s") %self.app.keys['copyRoutine'], _translate("Copy the current routine so it can be used in another exp"), wx.ITEM_NORMAL)
        wx.EVT_MENU(self, self.IDs.copyRoutine,  self.onCopyRoutine)
        self.expMenu.Append(self.IDs.pasteRoutine, _translate("&Paste Routine\t%s") %self.app.keys['pasteRoutine'], _translate("Paste the Routine into the current experiment"), wx.ITEM_NORMAL)
        wx.EVT_MENU(self, self.IDs.pasteRoutine,  self.onPasteRoutine)
        self.expMenu.AppendSeparator()

        self.expMenu.Append(self.IDs.addRoutineToFlow, _translate("Insert Routine in Flow"), _translate("Select one of your routines to be inserted into the experiment flow"))
        wx.EVT_MENU(self, self.IDs.addRoutineToFlow,  self.flowPanel.onInsertRoutine)
        self.expMenu.Append(self.IDs.addLoopToFlow, _translate("Insert Loop in Flow"), _translate("Create a new loop in your flow window"))
        wx.EVT_MENU(self, self.IDs.addLoopToFlow,  self.flowPanel.insertLoop)

        #---_demos---#000000#FFFFFF--------------------------------------------------
        #for demos we need a dict where the event ID will correspond to a filename

        self.demosMenu = wx.Menu()
        #unpack demos option
        self.demosMenu.Append(self.IDs.builderDemosUnpack, _translate("&Unpack Demos..."),
            _translate("Unpack demos to a writable location (so that they can be run)"))
        wx.EVT_MENU(self, self.IDs.builderDemosUnpack, self.demosUnpack)
        self.demosMenu.AppendSeparator()
        self.demosMenuUpdate()#add any demos that are found in the prefs['demosUnpacked'] folder
        menuBar.Append(self.demosMenu, _translate('&Demos'))

        #---_help---#000000#FFFFFF--------------------------------------------------
        self.helpMenu = wx.Menu()
        menuBar.Append(self.helpMenu, _translate('&Help'))
        self.helpMenu.Append(self.IDs.psychopyHome, _translate("&PsychoPy Homepage"), _translate("Go to the PsychoPy homepage"))
        wx.EVT_MENU(self, self.IDs.psychopyHome, self.app.followLink)
        self.helpMenu.Append(self.IDs.builderHelp, _translate("&PsychoPy Builder Help"), _translate("Go to the online documentation for PsychoPy Builder"))
        wx.EVT_MENU(self, self.IDs.builderHelp, self.app.followLink)

        self.helpMenu.AppendSeparator()
        self.helpMenu.Append(wx.ID_ABOUT, _translate("&About..."), _translate("About PsychoPy"))
        wx.EVT_MENU(self, wx.ID_ABOUT, self.app.showAbout)

        self.SetMenuBar(menuBar)


    def commandCloseFrame(self, event):
        self.Close()

    def closeFrame(self, event=None, checkSave=True):
        okToClose = self.fileClose(updateViews=False, checkSave=checkSave)#close file first (check for save) but no need to update view

        if not okToClose:
            if hasattr(event, 'Veto'):
                event.Veto()
            return
        else:
            self._mgr.UnInit()#as of wx3.0 the AUI manager needs to be uninitialised explicitly
            # is it the last frame?
            if len(wx.GetApp().allFrames) == 1 and sys.platform != 'darwin' and not wx.GetApp().quitting:
                wx.GetApp().quit(event)
            else:
                self.app.allFrames.remove(self)
                self.app.builderFrames.remove(self)
                self.Destroy() # required

    def quit(self, event=None):
        """quit the app"""
        self.app.quit(event)
    def fileNew(self, event=None, closeCurrent=True):
        """Create a default experiment (maybe an empty one instead)"""
        #Note: this is NOT the method called by the File>New menu item. That calls app.newBuilderFrame() instead
        if closeCurrent: #if no exp exists then don't try to close it
            if not self.fileClose(updateViews=False):
                return False #close the existing (and prompt for save if necess)
        self.filename='untitled.psyexp'
        self.exp = experiment.Experiment(prefs=self.app.prefs)
        defaultName = 'trial'
        self.exp.addRoutine(defaultName) #create the trial routine as an example
        self.exp.flow.addRoutine(self.exp.routines[defaultName], pos=1)#add it to flow
        self.exp.namespace.add(defaultName, self.exp.namespace.user) # add it to user's namespace
        routine = self.exp.routines[defaultName]
        #add an ISI component by default
        components = self.componentButtons.components
        ISI = components['StaticComponent'](self.exp, parentName=defaultName, name='ISI',
                startType='time (s)', startVal=0.0,
                stopType='duration (s)', stopVal=0.5)
        routine.addComponent(ISI)
        self.resetUndoStack()
        self.setIsModified(False)
        self.updateAllViews()
    def fileOpen(self, event=None, filename=None, closeCurrent=True):
        """Open a FileDialog, then load the file if possible.
        """
        if filename is None:
            dlg = wx.FileDialog(self, message=_translate("Open file ..."), style=wx.FD_OPEN|wx.FD_FILE_MUST_EXIST,
                wildcard=_translate("PsychoPy experiments (*.psyexp)|*.psyexp|Any file (*.*)|*"))
            if dlg.ShowModal() != wx.ID_OK:
                return 0
            filename = dlg.GetPath()
        #did user try to open a script in Builder?
        if filename.endswith('.py'):
            self.app.showCoder(fileList=[filename])
            return
        #NB this requires Python 2.5 to work because of with... statement
        with WindowFrozen(ctrl=self):#try to pause rendering until all panels updated
            if closeCurrent:
                if not self.fileClose(updateViews=False):
                    return False #close the existing (and prompt for save if necess)
            self.exp = experiment.Experiment(prefs=self.app.prefs)
            try:
                self.exp.loadFromXML(filename)
            except Exception:
                print("Failed to load %s. Please send the following to the PsychoPy user list" %filename)
                traceback.print_exc()
                logging.flush()
            self.resetUndoStack()
            self.setIsModified(False)
            self.filename = filename
            #routinePanel.addRoutinePage() is done in routinePanel.redrawRoutines(), as called by self.updateAllViews()
            #update the views
            self.updateAllViews()#if frozen effect will be visible on thaw
        self.updateReadme()
        self.fileHistory.AddFileToHistory(filename)

    def fileSave(self,event=None, filename=None):
        """Save file, revert to SaveAs if the file hasn't yet been saved
        """
        if filename is None:
            filename = self.filename
        if filename.startswith('untitled'):
            if not self.fileSaveAs(filename):
                return False #the user cancelled during saveAs
        else:
            self.fileHistory.AddFileToHistory(filename)
            self.exp.saveToXML(filename)
        self.setIsModified(False)
        return True

    def fileSaveAs(self,event=None, filename=None):
        """
        """
        shortFilename = self.getShortFilename()
        expName = self.exp.getExpName()
        if (not expName) or (shortFilename==expName):
            usingDefaultName=True
        else:
            usingDefaultName=False
        if filename is None:
            filename = self.filename
        initPath, filename = os.path.split(filename)

        os.getcwd()
        if sys.platform=='darwin':
            wildcard=_translate("PsychoPy experiments (*.psyexp)|*.psyexp|Any file (*.*)|*")
        else:
            wildcard=_translate("PsychoPy experiments (*.psyexp)|*.psyexp|Any file (*.*)|*.*")
        returnVal=False
        dlg = wx.FileDialog(
            self, message=_translate("Save file as ..."), defaultDir=initPath,
            defaultFile=filename, style=wx.SAVE, wildcard=wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            newPath = dlg.GetPath()
            #update exp name
            # if the file already exists, query whether it should be overwritten (default = yes)
            okToSave=True
            if os.path.exists(newPath):
                dlg2 = dialogs.MessageDialog(self,
                            message=_translate("File '%s' already exists.\n    OK to overwrite?") % (newPath),
                            type='Warning')
                ok = dlg2.ShowModal()
                if ok != wx.ID_YES:
                    okToSave = False
                try:
                    dlg2.destroy()
                except:
                    pass
            if okToSave:
                #if user has not manually renamed experiment
                if usingDefaultName:
                    newShortName = os.path.splitext(os.path.split(newPath)[1])[0]
                    self.exp.setExpName(newShortName)
                #actually save
                self.fileSave(event=None, filename=newPath)
                self.filename = newPath
                returnVal = 1
            else:
                print("'Save-as' canceled; existing file NOT overwritten.\n")
        try: #this seems correct on PC, but not on mac
            dlg.destroy()
        except:
            pass
        self.updateWindowTitle()
        return returnVal

    def getShortFilename(self):
        """returns the filename without path or extension
        """
        return os.path.splitext(os.path.split(self.filename)[1])[0]

    def updateReadme(self):
        """Check whether there is a readme file in this folder and try to show it"""
        #create the frame if we don't have one yet
        if not hasattr(self, 'readmeFrame') or self.readmeFrame is None:
            self.readmeFrame=ReadmeFrame(parent=self)
        #look for a readme file
        if self.filename and self.filename!='untitled.psyexp':
            dirname = os.path.dirname(self.filename)
            possibles = glob.glob(os.path.join(dirname,'readme*'))
            if len(possibles)==0:
                possibles = glob.glob(os.path.join(dirname,'Readme*'))
                possibles.extend(glob.glob(os.path.join(dirname,'README*')))
            #still haven't found a file so use default name
            if len(possibles)==0:
                self.readmeFilename=os.path.join(dirname,'readme.txt')#use this as our default
            else:
                self.readmeFilename = possibles[0]#take the first one found
        else:
            self.readmeFilename=None
        self.readmeFrame.setFile(self.readmeFilename)
        if self.readmeFrame.ctrl.GetValue() and self.prefs['alwaysShowReadme']:
            self.showReadme()
    def showReadme(self, evt=None, value=True):
        if not self.readmeFrame.IsShown():
            self.readmeFrame.Show(value)
    def toggleReadme(self, evt=None):
        if self.readmeFrame is None:
           self.updateReadme()
           self.showReadme()
        else:
           self.readmeFrame.toggleVisible()

    def OnFileHistory(self, evt=None):
        # get the file based on the menu ID
        fileNum = evt.GetId() - wx.ID_FILE1
        path = self.fileHistory.GetHistoryFile(fileNum)
        self.fileOpen(filename=path)
        # add it back to the history so it will be moved up the list
        self.fileHistory.AddFileToHistory(path)

    def checkSave(self):
        """Check whether we need to save before quitting
        """
        if hasattr(self, 'isModified') and self.isModified:
            self.Show(True)
            self.Raise()
            self.app.SetTopWindow(self)
            message = _translate('Experiment %s has changed. Save before quitting?') % self.filename
            dlg = dialogs.MessageDialog(self, message, type='Warning')
            resp = dlg.ShowModal()
            if resp == wx.ID_CANCEL:
                return False #return, don't quit
            elif resp == wx.ID_YES:
                if not self.fileSave():
                    return False #user might cancel during save
            elif resp == wx.ID_NO:
                pass #don't save just quit
        return True

    def fileClose(self, event=None, checkSave=True, updateViews=True):
        """This is typically only called when the user x"""
        if checkSave:
            ok = self.checkSave()
            if not ok:
                return False  #user cancelled
        if self.filename is None:
            frameData=self.appData['defaultFrame']
        else:
            frameData = dict(self.appData['defaultFrame'])
            self.appData['prevFiles'].append(self.filename)

            #get size and window layout info
        if self.IsIconized():
            self.Iconize(False)#will return to normal mode to get size info
            frameData['state']='normal'
        elif self.IsMaximized():
            self.Maximize(False)#will briefly return to normal mode to get size info
            frameData['state']='maxim'
        else:
            frameData['state']='normal'
        frameData['auiPerspective'] = self._mgr.SavePerspective()
        frameData['winW'], frameData['winH']=self.GetSize()
        frameData['winX'], frameData['winY']=self.GetPosition()

        # truncate history to the recent-most last N unique files, where
        # N = self.fileHistoryMaxFiles, as defined in makeMenus()
        for ii in range(self.fileHistory.GetCount()):
            self.appData['fileHistory'].append(self.fileHistory.GetHistoryFile(ii))
        # fileClose gets calls multiple times, so remove redundancy while preserving order,
        # end of the list is recent-most:
        tmp = []
        for f in self.appData['fileHistory'][-3 * self.fileHistoryMaxFiles:]:
            if not f in tmp:
                tmp.append(f)
        self.appData['fileHistory'] = copy.copy(tmp[-self.fileHistoryMaxFiles:])

        #assign the data to this filename
        self.appData['frames'][self.filename] = frameData
        # save the display data only for those frames in the history:
        tmp2 = {}
        for f in self.appData['frames'].keys():
            if f in self.appData['fileHistory']:
                tmp2[f] = self.appData['frames'][f]
        self.appData['frames'] = copy.copy(tmp2)

        #close self
        self.routinePanel.removePages()
        self.filename = 'untitled.psyexp'
        self.resetUndoStack()#will add the current exp as the start point for undo
        if updateViews:
            self.updateAllViews()
        return 1
    def updateAllViews(self):
        self.flowPanel.draw()
        self.routinePanel.redrawRoutines()
        self.updateWindowTitle()
    def updateWindowTitle(self, newTitle=None):
        if newTitle is None:
            shortName = os.path.split(self.filename)[-1]
            newTitle='%s - PsychoPy Builder' %(shortName)
        self.SetTitle(newTitle)
    def setIsModified(self, newVal=None):
        """Sets current modified status and updates save icon accordingly.

        This method is called by the methods fileSave, undo, redo, addToUndoStack
        and it is usually preferably to call those than to call this directly.

        Call with ``newVal=None``, to only update the save icon(s)
        """
        if newVal is None:
            newVal= self.getIsModified()
        else:
            self.isModified=newVal
        self.toolbar.EnableTool(self.IDs.tbFileSave, newVal)
        self.fileMenu.Enable(wx.ID_SAVE, newVal)
    def getIsModified(self):
        return self.isModified
    def resetUndoStack(self):
        """Reset the undo stack. e.g. do this *immediately after* creating a new exp.

        Will implicitly call addToUndoStack() using the current exp as the state
        """
        self.currentUndoLevel=1#1 is current, 2 is back one setp...
        self.currentUndoStack=[]
        self.addToUndoStack()
        self.updateUndoRedo()
        self.setIsModified(newVal=False)#update save icon if needed
    def addToUndoStack(self, action="", state=None):
        """Add the given ``action`` to the currentUndoStack, associated with the @state@.
        ``state`` should be a copy of the exp from *immediately after* the action was taken.
        If no ``state`` is given the current state of the experiment is used.

        If we are at end of stack already then simply append the action.
        If not (user has done an undo) then remove orphan actions and then append.
        """
        if state is None:
            state=copy.deepcopy(self.exp)
        #remove actions from after the current level
        if self.currentUndoLevel>1:
            self.currentUndoStack = self.currentUndoStack[:-(self.currentUndoLevel-1)]
            self.currentUndoLevel=1
        #append this action
        self.currentUndoStack.append({'action':action,'state':state})
        self.setIsModified(newVal=True)#update save icon if needed
        self.updateUndoRedo()

    def undo(self, event=None):
        """Step the exp back one level in the @currentUndoStack@ if possible,
        and update the windows

        Returns the final undo level (1=current, >1 for further in past)
        or -1 if redo failed (probably can't undo)
        """
        if (self.currentUndoLevel)>=len(self.currentUndoStack):
            return -1#can't undo
        self.currentUndoLevel+=1
        self.exp = copy.deepcopy(self.currentUndoStack[-self.currentUndoLevel]['state'])
        self.updateAllViews()
        self.setIsModified(newVal=True)#update save icon if needed
        self.updateUndoRedo()
        # return
        return self.currentUndoLevel
    def redo(self, event=None):
        """Step the exp up one level in the @currentUndoStack@ if possible,
        and update the windows

        Returns the final undo level (0=current, >0 for further in past)
        or -1 if redo failed (probably can't redo)
        """
        if self.currentUndoLevel<=1:
            return -1#can't redo, we're already at latest state
        self.currentUndoLevel-=1
        self.exp = copy.deepcopy(self.currentUndoStack[-self.currentUndoLevel]['state'])
        self.updateUndoRedo()
        self.updateAllViews()
        self.setIsModified(newVal=True)#update save icon if needed
        return self.currentUndoLevel
    def updateUndoRedo(self):
        #check undo
        if (self.currentUndoLevel)>=len(self.currentUndoStack):
            # can't undo if we're at top of undo stack
            label = _translate("Undo\t%s") %(self.app.keys['undo'])
            enable = False
        else:
            action = self.currentUndoStack[-self.currentUndoLevel]['action']
            label = _translate("Undo %(action)s\t%(key)s") % {'action':action, 'key':self.app.keys['undo']}
            enable = True
        self._undoLabel.SetText(label)
        self.toolbar.EnableTool(self.IDs.tbUndo,enable)
        self.editMenu.Enable(wx.ID_UNDO,enable)
        # check redo
        if self.currentUndoLevel==1:
            label = _translate("Redo\t%s") %(self.app.keys['redo'])
            enable = False
        else:
            action = self.currentUndoStack[-self.currentUndoLevel+1]['action']
            label = _translate("Redo %(action)s\t%(key)s") % {'action':action, 'key':self.app.keys['redo']}
            enable = True
        self._redoLabel.SetText(label)
        self.toolbar.EnableTool(self.IDs.tbRedo,enable)
        self.editMenu.Enable(wx.ID_REDO,enable)

    def demosUnpack(self, event=None):
        """Get a folder location from the user and unpack demos into it
        """
        #choose a dir to unpack in
        dlg = wx.DirDialog(parent=self, message=_translate("Location to unpack demos"))
        if dlg.ShowModal()==wx.ID_OK:
            unpackFolder = dlg.GetPath()
        else:
            return -1#user cancelled
        # ensure it's an empty dir:
        if os.listdir(unpackFolder) != []:
            unpackFolder = os.path.join(unpackFolder, 'PsychoPy2 Demos')
            if not os.path.isdir(unpackFolder):
                os.mkdir(unpackFolder)
        mergeFolder(os.path.join(self.paths['demos'], 'builder'), unpackFolder)
        self.prefs['unpackedDemosDir']=unpackFolder
        self.app.prefs.saveUserPrefs()
        self.demosMenuUpdate()
    def demoLoad(self, event=None):
        fileDir = self.demos[event.GetId()]
        files = glob.glob(os.path.join(fileDir,'*.psyexp'))
        if len(files)==0:
            print("Found no psyexp files in %s" %fileDir)
        else:
            self.fileOpen(event=None, filename=files[0], closeCurrent=True)
    def demosMenuUpdate(self):
        #list available demos
        if len(self.prefs['unpackedDemosDir'])==0:
            return
        demoList = glob.glob(os.path.join(self.prefs['unpackedDemosDir'],'*'))
        demoList.sort(key=lambda entry: entry.lower)
        ID_DEMOS = \
            map(lambda _makeID: wx.NewId(), range(len(demoList)))
        self.demos={}
        for n in range(len(demoList)):
            self.demos[ID_DEMOS[n]] = demoList[n]
        for thisID in ID_DEMOS:
            junk, shortname = os.path.split(self.demos[thisID])
            if shortname.startswith('_') or shortname.lower().startswith('readme.'):
                continue #ignore 'private' or README files
            self.demosMenu.Append(thisID, shortname)
            wx.EVT_MENU(self, thisID, self.demoLoad)
    def runFile(self, event=None):
        #get abs path of experiment so it can be stored with data at end of exp
        expPath = self.filename
        if expPath is None or expPath.startswith('untitled'):
            ok = self.fileSave()
            if not ok:
                return  # save file before compiling script
        self.exp.expPath = os.path.abspath(expPath)
        #make new pathname for script file
        fullPath = self.filename.replace('.psyexp','_lastrun.py')

        script = self.generateScript(self.exp.expPath)
        if not script:
            return

        f = codecs.open(fullPath, 'w', 'utf-8')
        f.write(script.getvalue())
        f.close()
        try:
            self.stdoutFrame.getText()
        except:
            self.stdoutFrame=stdOutRich.StdOutFrame(parent=self, app=self.app, size=(700,300))

        # redirect standard streams to log window
        sys.stdout = self.stdoutFrame
        sys.stderr = self.stdoutFrame

        #provide a running... message
        print("\n"+(" Running: %s " %(fullPath)).center(80,"#"))
        self.stdoutFrame.lenLastRun = len(self.stdoutFrame.getText())

        self.scriptProcess=wx.Process(self) #self is the parent (which will receive an event when the process ends)
        self.scriptProcess.Redirect()#builder will receive the stdout/stdin

        if sys.platform=='win32':
            command = '"%s" -u "%s"' %(sys.executable, fullPath)# the quotes allow file paths with spaces
            #self.scriptProcessID = wx.Execute(command, wx.EXEC_ASYNC, self.scriptProcess)
            self.scriptProcessID = wx.Execute(command, wx.EXEC_ASYNC| wx.EXEC_NOHIDE, self.scriptProcess)
        else:
            fullPath= fullPath.replace(' ','\ ')#for unix this signifies a space in a filename
            pythonExec = sys.executable.replace(' ','\ ')#for unix this signifies a space in a filename
            command = '%s -u %s' %(pythonExec, fullPath)# the quotes would break a unix system command
            self.scriptProcessID = wx.Execute(command, wx.EXEC_ASYNC| wx.EXEC_MAKE_GROUP_LEADER, self.scriptProcess)
        self.toolbar.EnableTool(self.IDs.tbRun,False)
        self.toolbar.EnableTool(self.IDs.tbStop,True)
    def stopFile(self, event=None):
        self.app.terminateHubProcess()
        success = wx.Kill(self.scriptProcessID,wx.SIGTERM) #try to kill it gently first
        if success[0] != wx.KILL_OK:
            wx.Kill(self.scriptProcessID,wx.SIGKILL) #kill it aggressively
        self.onProcessEnded(event=None)
    def onProcessEnded(self, event=None):
        """The script/exp has finished running
        """
        self.toolbar.EnableTool(self.IDs.tbRun,True)
        self.toolbar.EnableTool(self.IDs.tbStop,False)
        #update the output window and show it
        text=""
        if self.scriptProcess.IsInputAvailable():
            stream = self.scriptProcess.GetInputStream()
            text += stream.read()
        if self.scriptProcess.IsErrorAvailable():
            stream = self.scriptProcess.GetErrorStream()
            text += stream.read()
        if len(text):
            self.stdoutFrame.write(text) #if some text hadn't yet been written (possible?)
        if len(self.stdoutFrame.getText()) > self.stdoutFrame.lenLastRun:
            self.stdoutFrame.Show()
            self.stdoutFrame.Raise()

        #provide a finished... message
        msg = "\n"+" Finished ".center(80,"#")#80 chars padded with #

        #then return stdout to its org location
        sys.stdout=self.stdoutOrig
        sys.stderr=self.stderrOrig
    def onCopyRoutine(self, event=None):
        """copy the current routine from self.routinePanel to self.app.copiedRoutine
        """
        r = copy.deepcopy(self.routinePanel.getCurrentRoutine())
        if r is not None:
            self.app.copiedRoutine = r
    def onPasteRoutine(self, event=None):
        """Paste the current routine from self.app.copiedRoutine to a new page
        in self.routinePanel after promting for a new name
        """
        if self.app.copiedRoutine is None:
            return -1
        defaultName = self.exp.namespace.makeValid(self.app.copiedRoutine.name)
        message = _translate('New name for copy of "%(copied)s"?  [%(default)s]') % {'copied':self.app.copiedRoutine.name, 'default':defaultName}
        dlg = wx.TextEntryDialog(self, message=message, caption=_translate('Paste Routine'))
        if dlg.ShowModal() == wx.ID_OK:
            routineName=dlg.GetValue()
            newRoutine = copy.deepcopy(self.app.copiedRoutine)
            if not routineName:
                routineName = defaultName
            newRoutine.name = self.exp.namespace.makeValid(routineName)
            newRoutine.params['name'] = newRoutine.name
            self.exp.namespace.add(newRoutine.name)
            self.exp.addRoutine(newRoutine.name, newRoutine)#add to the experiment
            for newComp in newRoutine: # routine == list of components
                newName = self.exp.namespace.makeValid(newComp.params['name'])
                self.exp.namespace.add(newName)
                newComp.params['name'].val = newName
            self.routinePanel.addRoutinePage(newRoutine.name, newRoutine)#could do redrawRoutines but would be slower?
            self.addToUndoStack("PASTE Routine `%s`" % newRoutine.name)
        dlg.Destroy()
    def onURL(self, evt):
        """decompose the URL of a file and line number"""
        # "C:\\Program Files\\wxPython2.8 Docs and Demos\\samples\\hangman\\hangman.py", line 21,
        filename = evt.GetString().split('"')[1]
        lineNumber = int(evt.GetString().split(',')[1][5:])
        self.app.showCoder()
        self.app.coder.gotoLine(filename,lineNumber)
    def compileScript(self, event=None):
        script = self.generateScript(None) #leave the experiment path blank
        if not script:
           return
        name = os.path.splitext(self.filename)[0]+".py"#remove .psyexp and add .py
        self.app.showCoder()#make sure coder is visible
        self.app.coder.fileNew(filepath=name)
        self.app.coder.currentDoc.SetText(script.getvalue())
    def setExperimentSettings(self,event=None):
        component=self.exp.settings
        #does this component have a help page?
        if hasattr(component, 'url'):
            helpUrl = component.url
        else:
            helpUrl = None
        dlg = DlgExperimentProperties(frame=self,
            title='%s Properties' %self.exp.getExpName(),
            params=component.params, helpUrl=helpUrl,
            order=component.order)
        if dlg.OK:
            self.addToUndoStack("EDIT experiment settings")
            self.setIsModified(True)
    def addRoutine(self, event=None):
        self.routinePanel.createNewRoutine()

    def generateScript(self, experimentPath):
        if self.app.prefs.app['debugMode']:
            return self.exp.writeScript(expPath=experimentPath)
            # getting the track-back is very helpful when debugging the app
        try:
            script = self.exp.writeScript(expPath=experimentPath)
        except Exception as e:
            try:
                self.stdoutFrame.getText()
            except:
                self.stdoutFrame=stdOutRich.StdOutFrame(parent=self, app=self.app, size=(700, 300))
            self.stdoutFrame.write("Error when generating experiment script:\n")
            self.stdoutFrame.write(str(e) + "\n")
            self.stdoutFrame.Show()
            self.stdoutFrame.Raise()
            return None
        return script


class ReadmeFrame(wx.Frame):
    def __init__(self, parent):
        """
        A frame for presenting/loading/saving readme files
        """
        self.parent=parent
        title="%s readme" %(parent.exp.name)
        self._fileLastModTime=None
        pos=wx.Point(parent.Position[0]+80, parent.Position[1]+80 )
        wx.Frame.__init__(self, parent, title=title, size=(600,500),pos=pos,
            style=wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Hide()
        self.makeMenus()
        self.ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE)
    def onClose(self, evt=None):
        self.parent.readmeFrame = None
        self.Destroy()
    def makeMenus(self):
        """ IDs are from app.wxIDs"""

        #---Menus---#000000#FFFFFF--------------------------------------------------
        menuBar = wx.MenuBar()
        #---_file---#000000#FFFFFF--------------------------------------------------
        self.fileMenu = wx.Menu()
        menuBar.Append(self.fileMenu, _translate('&File'))
        self.fileMenu.Append(wx.ID_SAVE,    _translate("&Save\t%s") %self.parent.app.keys['save'])
        self.fileMenu.Append(wx.ID_CLOSE,   _translate("&Close readme\t%s") %self.parent.app.keys['close'])
        self.fileMenu.Append(self.parent.IDs.toggleReadme, _translate("&Toggle readme\t%s") %self.parent.app.keys['toggleReadme'], _translate("Toggle Readme"))
        wx.EVT_MENU(self, self.parent.IDs.toggleReadme,  self.toggleVisible)
        wx.EVT_MENU(self, wx.ID_SAVE,  self.fileSave)
        wx.EVT_MENU(self, wx.ID_CLOSE,  self.toggleVisible)
        self.SetMenuBar(menuBar)
    def setFile(self, filename):
        self.filename=filename
        self.expName = self.parent.exp.getExpName()
        #check we can read
        if filename is None:#check if we can write to the directory
            return False
        elif not os.path.exists(filename):
            self.filename = None
            return False
        elif not os.access(filename, os.R_OK):
            logging.warning("Found readme file (%s) no read permissions" %filename)
            return False
        #attempt to open
        try:
            f=codecs.open(filename, 'r', 'utf-8')
        except IOError as err:
            logging.warning("Found readme file for %s and appear to have permissions, but can't open" %self.expName)
            logging.warning(err)
            return False
            #attempt to read
        try:
            readmeText=f.read().replace("\r\n", "\n")
        except:
            logging.error("Opened readme file for %s it but failed to read it (not text/unicode?)" %self.expName)
            return False
        f.close()
        self._fileLastModTime=os.path.getmtime(filename)
        self.ctrl.SetValue(readmeText)
        self.SetTitle("%s readme (%s)" %(self.expName, filename))
    def fileSave(self, evt=None):
        if self._fileLastModTime and os.path.getmtime(self.filename)>self._fileLastModTime:
            logging.warning('readme file has been changed by another programme?')
        txt = self.ctrl.GetValue()
        f = codecs.open(self.filename, 'w', 'utf-8')
        f.write(txt)
        f.close()
    def toggleVisible(self, evt=None):
        if self.IsShown():
            self.Hide()
        else:
            self.Show()

def appDataToFrames(prefs):
    """Takes the standard PsychoPy prefs and returns a list of appData dictionaries, for the Builder frames.
    (Needed because prefs stores a dict of lists, but we need a list of dicts)
    """
    dat = prefs.appData['builder']
def framesToAppData(prefs):
    pass
def _relpath(path, start='.'):
    """This code is based on os.path.relpath in the Python 2.6 distribution,
    included here for compatibility with Python 2.5"""

    if not path:
        raise ValueError("no path specified")

    start_list = os.path.abspath(start).split(os.path.sep)
    path_list = os.path.abspath(path).split(os.path.sep)

    # Work out how much of the filepath is shared by start and path.
    i = len(os.path.commonprefix([start_list, path_list]))

    rel_list = ['..'] * (len(start_list)-i) + path_list[i:]
    if not rel_list:
        return path
    return os.path.join(*rel_list)
