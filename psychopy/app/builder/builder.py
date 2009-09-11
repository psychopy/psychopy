# Part of the PsychoPy library
# Copyright (C) 2009 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import wx
import wx.lib.scrolledpanel as scrolled
import wx.aui
import sys, os, glob, copy, platform
import csv, numpy
from matplotlib import mlab
import experiment, components
from psychopy.app import stdOutRich, dialogs

canvasColour=[200,200,200]#in prefs? ;-)

class FlowPanel(wx.ScrolledWindow):
    def __init__(self, frame, id=-1):
        """A panel that shows how the routines will fit together
        """
        self.frame=frame
        self.app=frame.app
        self.dpi=self.app.dpi
        wx.ScrolledWindow.__init__(self, frame, id, (0, 0),size = (8*self.dpi,2*self.dpi))
        self.SetBackgroundColour(canvasColour)
        self.needUpdate=True
        self.maxWidth  = 14*self.dpi
        self.maxHeight = 3*self.dpi
        self.mousePos = None
        #if we're adding a loop or routine then add spots to timeline
        self.drawNearestRoutinePoint = True
        self.drawNearestLoopPoint = False
        self.pointsToDraw=[] #lists the x-vals of points to draw, eg loop locations

        # create a PseudoDC to record our drawing
        self.pdc = wx.PseudoDC()
        self.pen_cache = {}
        self.brush_cache = {}
        # vars for handling mouse clicks
        self.hitradius=5
        self.dragid = -1
        self.lastpos = (0,0)

        #for the context menu
        self.componentFromID={}#use the ID of the drawn icon to retrieve component (loop or routine)
        self.contextMenuItems=['remove']
        self.contextItemFromID={}; self.contextIDFromItem={}
        for item in self.contextMenuItems:
            id = wx.NewId()
            self.contextItemFromID[id] = item
            self.contextIDFromItem[item] = id

        self.btnSizer = wx.BoxSizer(wx.VERTICAL)
        self.btnInsertRoutine = wx.Button(self,-1,'Insert Routine')
        self.btnInsertLoop = wx.Button(self,-1,'Insert Loop')

        self.redrawFlow()

        #bind events
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)
        self.Bind(wx.EVT_BUTTON, self.onInsertRoutine,self.btnInsertRoutine)
        self.Bind(wx.EVT_BUTTON, self.onInsertLoop,self.btnInsertLoop)
        self.Bind(wx.EVT_PAINT, self.OnPaint)

        #self.SetAutoLayout(True)
        self.SetVirtualSize((self.maxWidth, self.maxHeight))
        self.SetScrollRate(self.dpi/4,self.dpi/4)

        self.btnSizer.Add(self.btnInsertRoutine)
        self.btnSizer.Add(self.btnInsertLoop)
        self.SetSizer(self.btnSizer)

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

    def onInsertRoutine(self, evt):
        """Someone pushed the insert routine button.
        Fetch the dialog
        """

        #add routine points to the timeline
        self.setDrawPoints('routines')
        self.redrawFlow()

        #bring up listbox to choose the routine to add and/or create a new one
        addRoutineDlg = DlgAddRoutineToFlow(frame=self.frame,
                    possPoints=self.pointsToDraw)
        if addRoutineDlg.ShowModal()==wx.ID_OK:
            newRoutine = self.frame.exp.routines[addRoutineDlg.routine]#fetch the routine with the returned name
            self.frame.exp.flow.addRoutine(newRoutine, addRoutineDlg.loc)
            self.frame.addToUndoStack("AddRoutine")

        #remove the points from the timeline
        self.setDrawPoints(None)
        self.redrawFlow()

    def onInsertLoop(self, evt):
        """Someone pushed the insert loop button.
        Fetch the dialog
        """

        #add routine points to the timeline
        self.setDrawPoints('loops')
        self.redrawFlow()

        #bring up listbox to choose the routine to add and/or create a new one
        loopDlg = DlgLoopProperties(frame=self.frame)

        if loopDlg.OK:
            handler=loopDlg.currentHandler
            exec("ends=numpy.%s" %handler.params['endPoints'])#creates a copy of endPoints as an array
            self.frame.exp.flow.addLoop(handler, startPos=ends[0], endPos=ends[1])
            self.frame.addToUndoStack("AddLoopToFlow")
        #remove the points from the timeline
        self.setDrawPoints(None)
        self.redrawFlow()

    def editLoopProperties(self, event=None, loop=None):
        if event:#we got here from a wx.button press (rather than our own drawn icons)
            loopName=event.EventObject.GetName()
            loop=self.routine.getLoopFromName(loopName)

        #add routine points to the timeline
        self.setDrawPoints('loops')
        self.redrawFlow()

        loopDlg = DlgLoopProperties(frame=self.frame,
            title=loop.params['name'].val+' Properties', loop=loop)
        if loopDlg.OK:
            if loopDlg.params['loopType'].val=='staircase': #['random','sequential','staircase']
                loop= loopDlg.stairHandler
            else:
                loop=loopDlg.trialHandler
            loop.params=loop.params
            self.frame.addToUndoStack("EditLoop")
        #remove the points from the timeline
        self.setDrawPoints(None)
        self.redrawFlow()

    def OnMouse(self, event):
        if event.LeftDown():
            x,y = self.ConvertEventCoords(event)
            icons = self.pdc.FindObjectsByBBox(x, y)
            if len(icons):
                comp=self.componentFromID[icons[0]]
                if comp.getType() in ['StairHandler', 'TrialHandler']:
                    self.editLoopProperties(loop=comp)
        elif event.RightDown():
            x,y = self.ConvertEventCoords(event)
            icons = self.pdc.FindObjectsByBBox(x, y)
            if len(icons):
                self._menuComponentID=icons[0]
                self.showContextMenu(self._menuComponentID,
                    xy=wx.Point(x+self.GetPosition()[0],y+self.GetPosition()[1]))
        elif event.Dragging() or event.LeftUp():
            if self.dragid != -1:
                pass
            if event.LeftUp():
                pass
    def showContextMenu(self, component, xy):
        menu = wx.Menu()
        for item in self.contextMenuItems:
            id = self.contextIDFromItem[item]
            menu.Append( id, item )
            wx.EVT_MENU( menu, id, self.onContextSelect )
        self.frame.PopupMenu( menu, xy )
        menu.Destroy() # destroy to avoid mem leak
    def onContextSelect(self, event):
        """Perform a given action on the component chosen
        """
        op = self.contextItemFromID[event.GetId()]
        component=self.componentFromID[self._menuComponentID]
        flow = self.frame.exp.flow
        if op=='remove':
            flow.removeComponent(component, id=self._menuComponentID)
            self.frame.addToUndoStack("removed %s from flow" %component.params['name'])
        self.redrawFlow()
        self._menuComponentID=None

    def OnPaint(self, event):
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.
        dc = wx.BufferedPaintDC(self)
        # use PrepateDC to set position correctly
        self.PrepareDC(dc)
        # we need to clear the dc BEFORE calling PrepareDC
        bg = wx.Brush(self.GetBackgroundColour())
        dc.SetBackground(bg)
        dc.Clear()
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

    def redrawFlow(self, evt=None):
        if not hasattr(self.frame, 'exp'):
            return#we haven't yet added an exp
        expFlow = self.frame.exp.flow #retrieve the current flow from the experiment
        pdc=self.pdc
        
        self.componentFromID={}#use the ID of the drawn icon to retrieve component (loop or routine)
        
        pdc.Clear()#clear the screen
        pdc.RemoveAll()#clear all objects (icon buttons)
        pdc.BeginDrawing()

        font = self.GetFont()

        #draw the main time line
        linePos = (1.8*self.dpi,1.4*self.dpi) #x value

        #step through components in flow
        currX=linePos[0]; gap=self.dpi/2
        pdc.DrawLine(x1=linePos[0]-gap,y1=linePos[1],x2=linePos[0],y2=linePos[1])
        self.loopInits = []#these will be entry indices
        self.loopTerms = []
        loopIDs=[]#index of the entry (of the loopInit) in the flow
        self.loops=[]#these will be copies of the actual loop obects
        self.gapMidPoints=[currX-gap/2]
        for n, entry in enumerate(expFlow):
            if entry.getType()=='LoopInitiator':
                loopIDs.append(n)
                self.loopInits.append(currX)
            if entry.getType()=='LoopTerminator':
                self.loops.append(entry.loop)
                self.loopTerms.append(currX)
            if entry.getType()=='Routine':
                currX = self.drawFlowRoutine(pdc,entry, id=n,pos=[currX,linePos[1]-30])
            self.gapMidPoints.append(currX+gap/2)
            pdc.SetPen(wx.Pen(wx.Colour(0,0,0, 255)))
            pdc.DrawLine(x1=currX,y1=linePos[1],x2=currX+gap,y2=linePos[1])
            currX+=gap

        #draw the loops second
        self.loopInits.reverse()#start with last initiator (paired with first terminator)
        for n, loopInit in enumerate(self.loopInits):
            name = self.loops[n].params['name'].val#name of the trialHandler/StairHandler
            self.drawLoop(pdc,name,self.loops[n],id=loopIDs[n],
                        startX=self.loopInits[n], endX=self.loopTerms[n],
                        base=linePos[1],height=linePos[1]-60-n*15)
            self.drawLoopStart(pdc,pos=[self.loopInits[n],linePos[1]])
            self.drawLoopEnd(pdc,pos=[self.loopTerms[n],linePos[1]])

        #draw all possible locations for routines
        for n, xPos in enumerate(self.pointsToDraw):
            font.SetPointSize(600/self.dpi)
            self.SetFont(font); pdc.SetFont(font)
            w,h = self.GetFullTextExtent(str(len(self.pointsToDraw)))[0:2]
            pdc.SetPen(wx.Pen(wx.Colour(0,0,0, 255)))
            pdc.SetBrush(wx.Brush(wx.Colour(0,0,0,255)))
            pdc.DrawCircle(xPos,linePos[1], w+2)
            pdc.SetTextForeground([255,255,255])
            pdc.DrawText(str(n), xPos-w/2, linePos[1]-h/2)

        pdc.EndDrawing()
        self.Refresh()#refresh the visible window after drawing (using OnPaint)

    def setDrawPoints(self, ptType, startPoint=None):
        """Set the points of 'routines', 'loops', or None
        """
        if ptType=='routines':
            self.pointsToDraw=self.gapMidPoints
        elif ptType=='loops':
            self.pointsToDraw=self.gapMidPoints
        else:
            self.pointsToDraw=[]
    def drawLoopEnd(self, dc, pos):
        #draws a spot that a loop will later attach to
        dc.SetBrush(wx.Brush(wx.Colour(0,0,0, 250)))
        dc.SetPen(wx.Pen(wx.Colour(0,0,0, 255)))
        dc.DrawPolygon([[5,5],[0,0],[-5,5]], pos[0],pos[1]-5)#points up
#        dc.DrawPolygon([[5,0],[0,5],[-5,0]], pos[0],pos[1]-5)#points down
    def drawLoopStart(self, dc, pos):
        #draws a spot that a loop will later attach to
        dc.SetBrush(wx.Brush(wx.Colour(0,0,0, 250)))
        dc.SetPen(wx.Pen(wx.Colour(0,0,0, 255)))
#        dc.DrawPolygon([[5,5],[0,0],[-5,5]], pos[0],pos[1]-5)
        dc.DrawPolygon([[5,0],[0,5],[-5,0]], pos[0],pos[1]-5)
    def drawFlowRoutine(self,dc,routine,id, rgb=[200,50,50],pos=[0,0]):
        """Draw a box to show a routine on the timeline
        """
        name=routine.name
        font = self.GetFont()
        if platform.system()=='Darwin':
            font.SetPointSize(1400/self.dpi)
        else:
            font.SetPointSize(1000/self.dpi)
        r, g, b = rgb

        #get size based on text
        self.SetFont(font); dc.SetFont(font)
        w,h = self.GetFullTextExtent(name)[0:2]
        pad = 20
        #draw box
        rect = wx.Rect(pos[0], pos[1], w+pad,h+pad)
        endX = pos[0]+w+20
        #the edge should match the text
        dc.SetPen(wx.Pen(wx.Colour(r, g, b, wx.ALPHA_OPAQUE)))
        #for the fill, draw once in white near-opaque, then in transp colour
        dc.SetBrush(wx.Brush(wx.Colour(r,g*3,b*3,255)))
        dc.DrawRoundedRectangleRect(rect, 8)
        #draw text
        dc.SetTextForeground(rgb)
        dc.DrawText(name, pos[0]+pad/2, pos[1]+pad/2)
        
        self.componentFromID[id]=routine
        dc.SetId(id)
        #set the area for this component
        dc.SetIdBounds(id,rect)

        return endX
    def drawLoop(self,dc,name,loop,id, 
            startX,endX,
            base,height,rgb=[0,0,0]):
        xx = [endX,  endX,   endX,   endX-5, endX-10, startX+10,startX+5, startX, startX, startX]
        yy = [base,height+10,height+5,height, height, height,  height,  height+5, height+10, base]
        pts=[]
        r,g,b=rgb
        pad=8
        dc.SetPen(wx.Pen(wx.Colour(r, g, b, 200)))
        for n in range(len(xx)):
            pts.append([xx[n],yy[n]])
        dc.DrawSpline(pts)

        #add a name label that can be clicked on
        font = self.GetFont()
        if platform.system()=='Darwin':
            font.SetPointSize(800/self.dpi)
        else:
            font.SetPointSize(800/self.dpi)
        self.SetFont(font); dc.SetFont(font)
        #get size based on text
        w,h = self.GetFullTextExtent(name)[0:2]
        x = startX+(endX-startX)/2-w/2
        y = height-h/2

        #draw box
        rect = wx.Rect(x, y, w+pad,h+pad)
        #the edge should match the text
        dc.SetPen(wx.Pen(wx.Colour(r, g, b, 100)))
        #for the fill, draw once in white near-opaque, then in transp colour
        dc.SetBrush(wx.Brush(wx.Colour(canvasColour[0],canvasColour[1],canvasColour[2],250)))
        dc.DrawRoundedRectangleRect(rect, 8)
        #draw text
        dc.SetTextForeground([r,g,b])
        dc.DrawText(name, x+pad/2, y+pad/2)

        self.componentFromID[id]=loop
        dc.SetId(id)
        #set the area for this component
        dc.SetIdBounds(id,rect)

class DlgAddRoutineToFlow(wx.Dialog):
    def __init__(self, frame, possPoints, id=-1, title='Add a routine to the flow',
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE):
        wx.Dialog.__init__(self,frame,id,title,pos,size,style)
        self.frame=frame
        self.dpi=self.frame.app.dpi
        self.Center()
        # setup choices of routines
        routineChoices=self.frame.exp.routines.keys()
        if len(routineChoices)==0:
            routineChoices=['NO PROCEDURES EXIST']
        self.choiceRoutine=wx.ComboBox(parent=self,id=-1,value=routineChoices[0],
                            choices=routineChoices, style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.EvtRoutineChoice, self.choiceRoutine)

        #location choices
        ptStrings = []#convert possible points to strings
        for n, pt in enumerate(possPoints):
            ptStrings.append(str(n))
        self.choiceLoc=wx.ComboBox(parent=self,id=-1,value=ptStrings[0],
                            choices=ptStrings, style=wx.CB_READONLY)
        self.Bind(wx.EVT_COMBOBOX, self.EvtLocChoice, self.choiceLoc)

        #add OK, cancel
        self.btnSizer = wx.BoxSizer(wx.HORIZONTAL)
        self.btnOK = wx.Button(self, wx.ID_OK)
        if routineChoices==['NO PROCEDURES EXIST']:
            self.btnOK.Enable(False)
        self.btnCancel = wx.Button(self, wx.ID_CANCEL)
        self.btnSizer.Add(self.btnOK)
        self.btnSizer.Add(self.btnCancel)

        #put into main sizer
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.sizer.Add(self.choiceRoutine)
        self.sizer.Add(self.choiceLoc)
        self.sizer.Add(self.btnSizer)
        self.SetSizerAndFit(self.sizer)

        self.routine=routineChoices[0]
        self.loc=0

    def EvtRoutineChoice(self, event):
        name = event.GetString()
        self.routine=event.GetString()
    def EvtLocChoice(self, event):
        name = event.GetString()
        if event.GetString() == 'Select a location':
            self.btnOK.Enable(False)
            self.loc=None
        else:
            self.btnOK.Enable(True)
            self.loc=int(event.GetString())


class RoutineCanvas(wx.ScrolledWindow):
    """Represents a single routine (used as page in RoutinesNotebook)"""
    def __init__(self, notebook, id=-1, routine=None):
        """This window is based heavily on the PseudoDC demo of wxPython
        """
        wx.ScrolledWindow.__init__(self, notebook, id, (0, 0), style=wx.SUNKEN_BORDER)

        self.SetBackgroundColour(canvasColour)
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

        self.SetVirtualSize((self.maxWidth, self.maxHeight))
        self.SetScrollRate(self.dpi/4,self.dpi/4)

        self.routine=routine
        self.yPositions=None
        self.yPosTop=60
        self.componentStep=50#the step in Y between each component
        self.iconXpos = 100 #the left hand edge of the icons
        self.timeXposStart = 200
        self.timeXposEnd = 600
        self.timeMax = 10

        # create a PseudoDC to record our drawing
        self.pdc = wx.PseudoDC()
        self.pen_cache = {}
        self.brush_cache = {}
        # vars for handling mouse clicks
        self.dragid = -1
        self.lastpos = (0,0)
        self.componentFromID={}#use the ID of the drawn icon to retrieve component name
        self.contextMenuItems=['edit','remove','move to top','move up','move down','move to bottom']
        self.contextItemFromID={}; self.contextIDFromItem={}
        for item in self.contextMenuItems:
            id = wx.NewId()
            self.contextItemFromID[id] = item
            self.contextIDFromItem[item] = id

        self.redrawRoutine()

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x:None)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)

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
            if len(icons):
                self._menuComponent=self.componentFromID[icons[0]]
                self.showContextMenu(self._menuComponent, xy=event.GetPosition())
        elif event.Dragging() or event.LeftUp():
            if self.dragid != -1:
                pass
            if event.LeftUp():
                pass
    def showContextMenu(self, component, xy):
        menu = wx.Menu()
        for item in self.contextMenuItems:
            id = self.contextIDFromItem[item]
            menu.Append( id, item )
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
            r.remove(component)
            self.frame.addToUndoStack("removed" + component.params['name'].val)
        elif op.startswith('move'):
            lastLoc=r.index(component)
            r.remove(component)
            if op=='move to top': r.insert(0, component)
            if op=='move up': r.insert(lastLoc-1, component)
            if op=='move down': r.insert(lastLoc+1, component)
            if op=='move to bottom': r.append(component)
            self.frame.addToUndoStack("moved" + component.params['name'].val)
        self.redrawRoutine()
        self._menuComponent=None
    def OnPaint(self, event):
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.
        dc = wx.BufferedPaintDC(self)
        # use PrepateDC to set position correctly
        self.PrepareDC(dc)
        # we need to clear the dc BEFORE calling PrepareDC
        bg = wx.Brush(self.GetBackgroundColour())
        dc.SetBackground(bg)
        dc.Clear()
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
        #draw timeline at bottom of page
        yPosBottom = self.yPosTop+len(self.routine)*self.componentStep
        self.drawTimeLine(self.pdc,self.yPosTop,yPosBottom)
        yPos = self.yPosTop

        for n, component in enumerate(self.routine):
            self.drawComponent(self.pdc, component, yPos)
            yPos+=self.componentStep

        self.SetVirtualSize((self.maxWidth, yPos))
        self.pdc.EndDrawing()
        self.Refresh()#refresh the visible window after drawing (using OnPaint)

    def drawTimeLine(self, dc, yPosTop, yPosBottom):
        xScale = self.getSecsPerPixel()
        xSt=self.timeXposStart
        xEnd=self.timeXposEnd
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0, 150)))
        dc.DrawLine(x1=xSt,y1=yPosTop,
                    x2=xEnd,y2=yPosTop)
        dc.DrawLine(x1=xSt,y1=yPosBottom,
                    x2=xEnd,y2=yPosBottom)
        for lineN in range(10):
            dc.DrawLine(xSt+lineN/xScale, yPosTop,
                    xSt+lineN/xScale, yPosBottom+2)
        #add a label
        font = self.GetFont()
        font.SetPointSize(1000/self.dpi)
        dc.SetFont(font)
        dc.DrawText('t (secs)',xEnd+5,
            yPosBottom-self.GetFullTextExtent('t')[1]/2.0)#y is y-half height of text
    def drawComponent(self, dc, component, yPos):
        """Draw the timing of one component on the timeline"""
        thisIcon = components.icons[component.getType()][0]#index 0 is main icon
        dc.DrawBitmap(thisIcon, self.iconXpos,yPos, True)

        font = self.GetFont()
        font.SetPointSize(1000/self.dpi)
        dc.SetFont(font)

        name = component.params['name'].val
        #get size based on text
        w,h = self.GetFullTextExtent(name)[0:2]
        #draw text
        x = self.iconXpos-self.dpi/10-w
        y = yPos+thisIcon.GetHeight()/2-h/2
        dc.DrawText(name, x-20, y)

        #draw entries on timeline
        xScale = self.getSecsPerPixel()
        dc.SetPen(wx.Pen(wx.Colour(200, 100, 100, 0)))
        #for the fill, draw once in white near-opaque, then in transp colour
        dc.SetBrush(wx.Brush(wx.Colour(200,100,100, 200)))
        h = self.componentStep/2
        exec("times=%s" %component.params['times'])
        if type(times[0]) in [int,float]:
            times=[times]
        for thisOcc in times:#each occasion/occurence
            st, end = thisOcc
            xSt = self.timeXposStart + st/xScale
            thisOccW = (end-st)/xScale
            if thisOccW<2: thisOccW=2#make sure at least one pixel shows
            dc.DrawRectangle(xSt, y, thisOccW,h )

        ##set an id for the region where the component.icon falls (so it can act as a button)
        #see if we created this already
        id=None
        for key in self.componentFromID.keys():
            if self.componentFromID[key]==component:
                id=key
        if not id: #then create one and add to the dict
            id = wx.NewId()
            self.componentFromID[id]=component
        dc.SetId(id)
        #set the area for this component
        r = wx.Rect(self.iconXpos, yPos, thisIcon.GetWidth(),thisIcon.GetHeight())
        dc.SetIdBounds(id,r)

    def editComponentProperties(self, event=None, component=None):
        if event:#we got here from a wx.button press (rather than our own drawn icons)
            componentName=event.EventObject.GetName()
            component=self.routine.getComponentFromName(componentName)

        dlg = DlgComponentProperties(frame=self.frame,
            title=component.params['name'].val+' Properties',
            params = component.params,
            order = component.order)
        if dlg.OK:
            self.redrawRoutine()#need to refresh timings section
            self.Refresh()#then redraw visible
            self.frame.addToUndoStack("edit %s" %component.params['name'])

    def getSecsPerPixel(self):
        return float(self.timeMax)/(self.timeXposEnd-self.timeXposStart)


class RoutinesNotebook(wx.aui.AuiNotebook):
    """A notebook that stores one or more routines
    """
    def __init__(self, frame, id=-1):
        self.frame=frame
        self.app=frame.app
        self.dpi=self.app.dpi
        wx.aui.AuiNotebook.__init__(self, frame, id)

        if not hasattr(self.frame, 'exp'):
            return#we haven't yet added an exp

        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.onClosePane, self)
    def getCurrentRoutine(self):
        routinePage=self.getCurrentPage()
        if routinePage:
            return routinePage.routine
        else: #no routine page
            return None
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
    def createNewRoutine(self):
        dlg = wx.TextEntryDialog(self, message="What is the name for the new Routine? (e.g. instr, trial, feedback)",
            caption='New Routine')
        exp = self.frame.exp
        if dlg.ShowModal() == wx.ID_OK:
            routineName=dlg.GetValue()
            exp.addRoutine(routineName)#add to the experiment
            self.addRoutinePage(routineName, exp.routines[routineName])#then to the notebook
            self.frame.addToUndoStack("created %s routine" %routineName)
        dlg.Destroy()
    def onClosePane(self, event=None):
        """Close the pane and remove the routine from the exp
        """
        #todo: check that the user really wants the routine deleted
        routine = self.GetPage(event.GetSelection()).routine
        #update experiment object and flow window (if this is being used)
        if routine.name in self.frame.exp.routines.keys():
            del self.frame.exp.routines[routine.name]
        if routine in self.frame.exp.flow:
            self.frame.exp.flow.remove(routine)
            self.frame.flowPanel.redrawFlow()
        self.frame.addToUndoStack("remove routine %" %routine.name)
    def redrawRoutines(self):
        """Removes all the routines, adds them back and sets current back to orig
        """
        currPage = self.GetSelection()
        self.removePages()
        for routineName in self.frame.exp.routines:
            self.addRoutinePage(routineName, self.frame.exp.routines[routineName])
        if currPage>-1:
            self.SetSelection(currPage)
class ComponentsPanel(scrolled.ScrolledPanel):
    def __init__(self, frame, id=-1):
        """A panel that shows how the routines will fit together
        """
        self.frame=frame
        self.app=frame.app
        self.dpi=self.app.dpi
        scrolled.ScrolledPanel.__init__(self,frame,id,size=(1*self.dpi,10*self.dpi))
        self.sizer=wx.BoxSizer(wx.VERTICAL)

        # add a button for each type of event that can be added
        self.componentButtons={}; self.componentFromID={}
        self.components=experiment.getAllComponents()
        for hiddenComp in self.frame.prefs['hiddenComponents']:
            del self.components[hiddenComp]
        del self.components['SettingsComponent']#also remove settings - that's in toolbar not components panel
        for thisName in self.components.keys():
            #NB thisComp is a class - we can't use its methods until it is an instance
            thisComp=self.components[thisName]
            thisIcon = components.icons[thisName][1]#index 1 is the 'add' icon
            shortName=thisName#but might be shortened below
            for redundant in ['component','Component']:
                if redundant in thisName: shortName=thisName.replace(redundant, "")
            btn = wx.BitmapButton(self, -1, thisIcon, (20, 20),
                           (thisIcon.GetWidth()+10, thisIcon.GetHeight()+10),
                           name=thisComp.__name__)
            self.componentFromID[btn.GetId()]=thisName
            self.Bind(wx.EVT_BUTTON, self.onComponentAdd,btn)
            self.sizer.Add(btn, 0,wx.EXPAND|wx.ALIGN_CENTER )
            self.componentButtons[thisName]=btn#store it for elsewhere

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()

    def onComponentAdd(self,evt):
        #get name of current routine
        currRoutinePage = self.frame.routinePanel.getCurrentPage()
        if not currRoutinePage:
            dialogs.MessageDialog(self,"Create a routine (Experiment menu) before adding components", 
                type='Info', title='Error').ShowModal()
            return False
        currRoutine = self.frame.routinePanel.getCurrentRoutine()
        #get component name
        newClassStr = self.componentFromID[evt.GetId()]
        componentName = newClassStr.replace('Component','')
        newCompClass = self.components[newClassStr]
        newComp = newCompClass(parentName=currRoutine.name, exp=self.frame.exp)
        #create component template
        dlg = DlgComponentProperties(frame=self.frame,
            title=componentName+' Properties',
            params = newComp.params,
            order = newComp.order)
        compName = newComp.params['name']
        if dlg.OK:
            currRoutine.addComponent(newComp)#add to the actual routing
            currRoutinePage.redrawRoutine()#update the routine's view with the new component too
#            currRoutinePage.Refresh()#done at the end of redrawRoutine
            self.frame.addToUndoStack("added %s to %s" %(compName, currRoutine.name))
        return True
class ParamCtrls:
    def __init__(self, dlg, label, param, browse=False, noCtrls=False):
        """Create a set of ctrls for a particular Component Parameter, to be
        used in Component Properties dialogs. These need to be positioned
        by the calling dlg.

        e.g.::
            param = experiment.Param(val='boo', valType='str')
            ctrls=ParamCtrls(dlg=self, label=fieldName,param=param)
            self.paramCtrls[fieldName] = ctrls #keep track of them in the dlg
            self.sizer.Add(ctrls.nameCtrl, (self.currRow,0), (1,1),wx.ALIGN_RIGHT )
            self.sizer.Add(ctrls.valueCtrl, (self.currRow,1) )
            #these are optional (the parameter might be None)
            if ctrls.typeCtrl: self.sizer.Add(ctrls.typeCtrl, (self.currRow,2) )
            if ctrls.updateCtrl: self.sizer.Add(ctrls.updateCtrl, (self.currRow,3))

        If browse is True then a browseCtrl will be added (you need to bind events yourself)
        If noCtrls is True then no actual wx widgets are made, but attribute names are created
        """
        self.param = param
        self.dlg = dlg
        self.dpi=self.dlg.dpi
        self.valueWidth = self.dpi*3.5
        #param has the fields:
        #val, valType, allowedVals=[],allowedTypes=[], hint="", updates=None, allowedUpdates=None
        # we need the following
        self.nameCtrl = self.valueCtrl = self.typeCtrl = self.updateCtrl = None
        self.browseCtrl = None
        if noCtrls: return#we don't need to do any more

        if type(param.val)==numpy.ndarray:
            initial=initial.tolist() #convert numpy arrays to lists
        labelLength = wx.Size(self.dpi*2,self.dpi/3)#was 8*until v0.91.4
        self.nameCtrl = wx.StaticText(self.dlg,-1,label,size=labelLength,
                                        style=wx.ALIGN_RIGHT)

        if label=='text':
            #for text input we need a bigger (multiline) box
            self.valueCtrl = wx.TextCtrl(self.dlg,-1,str(param.val),
                style=wx.TE_MULTILINE,
                size=wx.Size(self.valueWidth,-1))
        elif param.valType=='bool':
            #only True or False - use a checkbox
             self.valueCtrl = wx.CheckBox(self.dlg, size = wx.Size(self.valueWidth,-1))
             self.valueCtrl.SetValue(param.val)
        elif len(param.allowedVals)>1:
            #there are limitted options - use a Choice control
            self.valueCtrl = wx.Choice(self.dlg, choices=param.allowedVals, size=wx.Size(self.valueWidth,-1))
            self.valueCtrl.SetStringSelection(unicode(param.val))
        else:
            #create the full set of ctrls
            self.valueCtrl = wx.TextCtrl(self.dlg,-1,str(param.val),
                        size=wx.Size(self.valueWidth,-1))

        self.valueCtrl.SetToolTipString(param.hint)

        #create the type control
        if len(param.allowedTypes)==0:
            pass
        else:
            self.typeCtrl = wx.Choice(self.dlg, choices=param.allowedTypes)
            self.typeCtrl.SetStringSelection(param.valType)
        if len(param.allowedTypes)==1:
            self.typeCtrl.Disable()#visible but can't be changed

        #create update control
        if param.allowedUpdates==None or len(param.allowedUpdates)==0:
            pass
        else:
            self.updateCtrl = wx.Choice(self.dlg, choices=param.allowedUpdates)
            self.updateCtrl.SetStringSelection(param.updates)
        if param.allowedUpdates!=None and len(param.allowedUpdates)==1:
            self.updateCtrl.Disable()#visible but can't be changed
        #create browse control
        if browse:
            self.browseCtrl = wx.Button(self.dlg, -1, "Browse...") #we don't need a label for this
    def _getCtrlValue(self, ctrl):
        """Retrieve the current value form the control (whatever type of ctrl it
        is, e.g. checkbox.GetValue, textctrl.GetStringSelection
        """
        """Different types of control have different methods for retrieving value.
        This function checks them all and returns the value or None.
        """
        if ctrl==None: return None
        elif hasattr(ctrl, 'GetValue'): #e.g. TextCtrl
            return ctrl.GetValue()
        elif hasattr(ctrl, 'GetStringSelection'): #for wx.Choice
            return ctrl.GetStringSelection()
        elif hasattr(ctrl, 'GetLabel'): #for wx.StaticText
            return ctrl.GetLabel()
        else:
            print "failed to retrieve the value for %s: %s" %(fieldName, ctrls.valueCtrl)
            return None
    def _setCtrlValue(self, ctrl, newVal):
        """Set the current value form the control (whatever type of ctrl it
        is, e.g. checkbox.SetValue, textctrl.SetStringSelection
        """
        """Different types of control have different methods for retrieving value.
        This function checks them all and returns the value or None.
        """
        if ctrl==None: return None
        elif hasattr(ctrl, 'SetValue'): #e.g. TextCtrl
            ctrl.SetValue(newVal)
        elif hasattr(ctrl, 'SetStringSelection'): #for wx.Choice
            ctrl.SetStringSelection(newVal)
        elif hasattr(ctrl, 'SetLabel'): #for wx.StaticText
            ctrl.SetLabel(newVal)
        else:
            print "failed to retrieve the value for %s: %s" %(fieldName, ctrls.valueCtrl)
    def getValue(self):
        """Get the current value of the value ctrl
        """
        return self._getCtrlValue(self.valueCtrl)
    def setValue(self, newVal):
        """Get the current value of the value ctrl
        """
        return self._setCtrlValue(self.valueCtrl, newVal)
    def getType(self):
        """Get the current value of the type ctrl
        """
        if self.typeCtrl:
            return self._getCtrlValue(self.typeCtrl)
    def getUpdates(self):
        """Get the current value of the updates ctrl
        """
        if self.updateCtrl:
            return self._getCtrlValue(self.updateCtrl)
class _BaseParamsDlg(wx.Dialog):
    def __init__(self,frame,title,params,order,suppressTitles=True,
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.TAB_TRAVERSAL):
        wx.Dialog.__init__(self, frame,-1,title,pos,size,style)
        self.frame=frame
        self.app=frame.app
        self.dpi=self.app.dpi
        self.Center()
        self.panel = wx.Panel(self, -1)
        self.params=params   #dict
        self.paramCtrls={}
        self.order=order
        self.data = []
        self.ctrlSizer= wx.GridBagSizer(vgap=2,hgap=2)
        self.currRow = 0
        self.nameOKlabel=None
        self.maxFieldLength = 10#max( len(str(self.params[x])) for x in keys )
        types=dict([])
        self.useUpdates=False#does the dlg need an 'updates' row (do any params use it?)

        #create a header row of titles
        if not suppressTitles:
            size=wx.Size(1.5*self.dpi,-1)
            self.ctrlSizer.Add(wx.StaticText(self,-1,'Parameter',size=size, style=wx.ALIGN_CENTER),(self.currRow,0))
            self.ctrlSizer.Add(wx.StaticText(self,-1,'Value',size=size, style=wx.ALIGN_CENTER),(self.currRow,1))
            #self.sizer.Add(wx.StaticText(self,-1,'Value Type',size=size, style=wx.ALIGN_CENTER),(self.currRow,3))
            self.ctrlSizer.Add(wx.StaticText(self,-1,'Updates',size=size, style=wx.ALIGN_CENTER),(self.currRow,2))
            self.currRow+=1
        self.ctrlSizer.Add(wx.StaticLine(self,-1), (self.currRow,0), (1,3))
        self.currRow+=1

        remaining = sorted(self.params.keys())
        #loop through the params with a prescribed order
        for fieldName in self.order:
            self.addParam(fieldName)
            remaining.remove(fieldName)
        #add any params that weren't specified in the order
        for fieldName in remaining:
            self.addParam(fieldName)
    def addParam(self,fieldName):
        param=self.params[fieldName]
        ctrls=ParamCtrls(dlg=self, label=fieldName,param=param)
        self.paramCtrls[fieldName] = ctrls
        if fieldName=='name':
            ctrls.valueCtrl.Bind(wx.EVT_TEXT, self.checkName)
        # self.valueCtrl = self.typeCtrl = self.updateCtrl
        self.ctrlSizer.Add(ctrls.nameCtrl, (self.currRow,0), (1,1),wx.ALIGN_RIGHT )
        self.ctrlSizer.Add(ctrls.valueCtrl, (self.currRow,1) )
        if ctrls.updateCtrl:
            self.ctrlSizer.Add(ctrls.updateCtrl, (self.currRow,2))
        if ctrls.typeCtrl:
            self.ctrlSizer.Add(ctrls.typeCtrl, (self.currRow,3) )
        self.currRow+=1
    def addText(self, text, size=None):
        if size==None:
            size = wx.Size(8*len(text)+16, 25)
        myTxt = wx.StaticText(self,-1,
                                label=text,
                                style=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL,
                                size=size)
        self.ctrlSizer.Add(myTxt,wx.EXPAND)#add to current row spanning entire
        return myTxt

    def show(self):
        """Adds an OK and cancel button, shows dialogue.

        This method returns wx.ID_OK (as from ShowModal), but also
        sets self.OK to be True or False
        """
        if 'name' in self.params.keys():
            if len(self.params['name'].val):
                nameInfo='Need a name'
            else: nameInfo=''
            self.nameOKlabel=wx.StaticText(self,-1,nameInfo,size=(300,25),
                                        style=wx.ALIGN_RIGHT)
            self.nameOKlabel.SetForegroundColour(wx.RED)
        #add buttons for OK and Cancel
        self.mainSizer=wx.BoxSizer(wx.VERTICAL)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.OKbtn = wx.Button(self, wx.ID_OK, " OK ")
        self.OKbtn.SetDefault()
        self.checkName()
        buttons.Add(self.OKbtn, 0, wx.ALL,border=3)
        CANCEL = wx.Button(self, wx.ID_CANCEL, " Cancel ")
        buttons.Add(CANCEL, 0, wx.ALL,border=3)

        #put it all together
        self.mainSizer.Add(self.ctrlSizer)
        if self.nameOKlabel: self.mainSizer.Add(self.nameOKlabel, wx.ALIGN_RIGHT)
        self.mainSizer.Add(buttons, flag=wx.ALIGN_RIGHT)
        self.SetSizerAndFit(self.mainSizer)

        #do show and process return
        retVal = self.ShowModal()
        if retVal== wx.ID_OK: self.OK=True
        else:  self.OK=False
        return wx.ID_OK

    def getParams(self):
        """retrieves data from any fields in self.paramCtrls
        (populated during the __init__ function)

        The new data from the dlg get inserted back into the original params
        used in __init__ and are also returned from this method.
        """
        #get data from input fields
        for fieldName in self.params.keys():
            param=self.params[fieldName]
            ctrls = self.paramCtrls[fieldName]#the various dlg ctrls for this param
            param.val = ctrls.getValue()
            if ctrls.typeCtrl: param.valType = ctrls.getType()
            if ctrls.updateCtrl: param.updates = ctrls.getUpdates()
        return self.params
    def checkName(self, event=None):
        if event: newName= event.GetString()
        elif hasattr(self, 'paramCtrls'): newName=self.paramCtrls['name'].getValue()
        elif hasattr(self, 'globalCtrls'): newName=self.globalCtrls['name'].getValue()
        if newName=='':
            self.nameOKlabel.SetLabel("Missing name")
            self.OKbtn.Disable()
        else:
            used=self.frame.exp.getUsedName(newName)
            if newName!=self.params['name'].val and used:
                self.nameOKlabel.SetLabel("Name '%s' is already used by a %s" %(newName, used))
                self.OKbtn.Disable()
            else:
                self.OKbtn.Enable()
                self.nameOKlabel.SetLabel("")
class DlgLoopProperties(_BaseParamsDlg):
    def __init__(self,frame,title="Loop properties",loop=None,
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.RESIZE_BORDER):
        wx.Dialog.__init__(self, frame,-1,title,pos,size,style)
        self.frame=frame
        self.exp=frame.exp
        self.app=frame.app
        self.dpi=self.app.dpi
        self.params={}
        self.Center()
        self.panel = wx.Panel(self, -1)
        self.globalCtrls={}
        self.constantsCtrls={}
        self.staircaseCtrls={}
        self.data = []
        self.ctrlSizer= wx.BoxSizer(wx.VERTICAL)
        self.trialList=None
        self.trialListFile=None

        #create instances of the two loop types
        if loop==None:
            self.trialHandler=experiment.TrialHandler(exp=self.exp, name='trials',loopType='random',nReps=5,trialList=[]) #for 'random','sequential'
            self.stairHandler=experiment.StairHandler(exp=self.exp, name='trials', nReps=50, nReversals=None,
                stepSizes='[0.8,0.8,0.4,0.4,0.2]', stepType='log', startVal=0.5) #for staircases
            self.currentType='random'
            self.currentHandler=self.trialHandler
        elif loop.type=='TrialHandler':
            self.trialList=loop.params['trialList'].val
            self.trialLIstFile=loop.params['trialListFile'].val
            self.trialHandler = self.currentHandler = loop
            self.currentType=loop.params['loopType']#could be 'random' or 'sequential'
            self.stairHandler=experiment.StairHandler(exp=self.exp, name='trials', nReps=50, nReversals=None,
                stepSizes='[0.8,0.8,0.4,0.4,0.2]', stepType='log', startVal=0.5) #for staircases
        elif loop.type=='StairHandler':
            self.stairHandler = self.currentHandler = loop
            self.currentType='staircase'
            experiment.TrialHandler(exp=self.exp, name=paramsInit['name'],loopType='random',nReps=5,trialList=[]) #for 'random','sequential'
        self.params['name']=self.currentHandler.params['name']

        self.makeGlobalCtrls()
        self.makeStaircaseCtrls()
        self.makeConstantsCtrls()#the controls for Method of Constants
        self.setCtrls(self.currentType)

        #show dialog and get most of the data
        self.show()
        if self.OK:
            self.params = self.getParams()
            #convert endPoints from str to list
            exec("self.params['endPoints'].val = %s" %self.params['endPoints'].val)
            #then sort the list so the endpoints are in correct order
            self.params['endPoints'].val.sort()
            
        #make sure we set this back regardless of whether OK
        #otherwise it will be left as a summary string, not a trialList
        if self.currentHandler.params.has_key('trialListFile'):
            self.currentHandler.params['trialList'].val=self.trialList

    def makeGlobalCtrls(self):
        for fieldName in ['name','loopType','endPoints']:
            container=wx.BoxSizer(wx.HORIZONTAL)#to put them in
            self.globalCtrls[fieldName] = ctrls = ParamCtrls(self, fieldName, self.currentHandler.params[fieldName])
            container.AddMany( (ctrls.nameCtrl, ctrls.valueCtrl))
            self.ctrlSizer.Add(container)

        self.globalCtrls['name'].valueCtrl.Bind(wx.EVT_TEXT, self.checkName)
        self.Bind(wx.EVT_CHOICE, self.onTypeChanged, self.globalCtrls['loopType'].valueCtrl)

    def makeConstantsCtrls(self):
        #a list of controls for the random/sequential versions
        #that can be hidden or shown
        handler=self.trialHandler
        #loop through the params
        keys = handler.params.keys()
        #add trialList stuff to the *end*
        if 'trialList' in keys:
            keys.remove('trialList')
            keys.insert(-1,'trialList')
        if 'trialListFile' in keys:
            keys.remove('trialListFile')
            keys.insert(-1,'trialListFile')
        #then step through them
        for fieldName in keys:
            if fieldName in self.globalCtrls.keys():
                #these have already been made and inserted into sizer
                ctrls=self.globalCtrls[fieldName]
            elif fieldName=='trialListFile':
                container=wx.BoxSizer(wx.HORIZONTAL)
                ctrls=ParamCtrls(self, fieldName, handler.params[fieldName], browse=True)
                self.Bind(wx.EVT_BUTTON, self.onBrowseTrialsFile,ctrls.browseCtrl)
                container.AddMany((ctrls.nameCtrl, ctrls.valueCtrl, ctrls.browseCtrl))
                self.ctrlSizer.Add(container)
            elif fieldName=='trialList':
                if handler.params.has_key('trialList'):
                    text=self.getTrialsSummary(handler.params['trialList'].val)
                else:
                    text = """No parameters set (select a .csv file above)"""
                ctrls = ParamCtrls(self, 'trialList',text,noCtrls=True)#we'll create our own widgets
                size = wx.Size(350, 50)
                ctrls.valueCtrl = self.addText(text, size)#NB this automatically adds to self.ctrlSizer
                #self.ctrlSizer.Add(ctrls.valueCtrl)
            else: #normal text entry field
                container=wx.BoxSizer(wx.HORIZONTAL)
                ctrls=ParamCtrls(self, fieldName, handler.params[fieldName])
                container.AddMany((ctrls.nameCtrl, ctrls.valueCtrl))
                self.ctrlSizer.Add(container)
            #store info about the field
            self.constantsCtrls[fieldName] = ctrls
    def makeStaircaseCtrls(self):
        """Setup the controls for a StairHandler"""
        handler=self.stairHandler
        #loop through the params
        for fieldName in handler.params.keys():
            if fieldName in self.globalCtrls.keys():
                #these have already been made and inserted into sizer
                ctrls=self.globalCtrls[fieldName]
            else: #normal text entry field
                container=wx.BoxSizer(wx.HORIZONTAL)
                ctrls=ParamCtrls(self, fieldName, handler.params[fieldName])
                container.AddMany((ctrls.nameCtrl, ctrls.valueCtrl))
                self.ctrlSizer.Add(container)
            #store info about the field
            self.staircaseCtrls[fieldName] = ctrls

    def getAbbriev(self, longStr, n=30):
        """for a filename (or any string actually), give the first
        5 characters, an ellipsis and then n of the final characters"""
        if len(longStr)>20:
            return longStr[0:10]+'...'+longStr[(-n+10):]
        else: return longStr
    def getTrialsSummary(self, trialList):
        if type(trialList)==list and len(trialList)>0:
            return '%i trial types, with %i parameters\n%s' \
                %(len(trialList),len(trialList[0]), trialList[0].keys())
        else:
            return "No parameters set"
    def importTrialTypes(self, fileName):
        """Import the trial data from fileName to generate a list of dicts.
        Insert this immediately into self.trialList
        """
        #use csv import library to fetch the fieldNames
        f = open(fileName,'rU')#the U converts lineendings to os.linesep
        #lines = f.read().split(os.linesep)#csv module is temperamental with line endings
        reader = csv.reader(f)#.split(os.linesep))
        fieldNames = reader.next()
        #use matplotlib to import data and intelligently check for data types
        #all data in one column will be given a single type (e.g. if one cell is string, all will be set to string)
        trialsArr = mlab.csv2rec(f)
        f.close()
        #convert the record array into a list of dicts
        trialList = []
        for trialN, trialType in enumerate(trialsArr):
            thisTrial ={}
            for fieldN, fieldName in enumerate(fieldNames):
                val = trialsArr[trialN][fieldN]
                #if it looks like a list, convert it
                if type(val)==numpy.string_ and val.startswith('[') and val.endswith(']'):
                    exec('val=%s' %val)
                thisTrial[fieldName] = val
            trialList.append(thisTrial)
        self.trialList=trialList
    def setCtrls(self, ctrlType):
        #choose the ctrls to show/hide
        if ctrlType=='staircase':
            self.currentHandler = self.stairHandler
            self.currentCtrls = self.staircaseCtrls
            toHideCtrls = self.constantsCtrls
        else:
            self.currentHandler = self.trialHandler
            self.currentCtrls = self.constantsCtrls
            toHideCtrls = self.staircaseCtrls
        #hide them
        for paramName in toHideCtrls.keys():
            ctrls = toHideCtrls[paramName]
            if ctrls.nameCtrl: ctrls.nameCtrl.Hide()
            if ctrls.valueCtrl: ctrls.valueCtrl.Hide()
            if ctrls.browseCtrl: ctrls.browseCtrl.Hide()
        #show them
        for paramName in self.currentCtrls.keys():
            ctrls = self.currentCtrls[paramName]
            if ctrls.nameCtrl: ctrls.nameCtrl.Show()
            if ctrls.valueCtrl: ctrls.valueCtrl.Show()
            if ctrls.browseCtrl: ctrls.browseCtrl.Show()
        self.ctrlSizer.Layout()
        self.Fit()
        self.Refresh()
    def onTypeChanged(self, evt=None):
        newType = evt.GetString()
        if newType==self.currentType:
            return
        self.setCtrls(newType)
    def onBrowseTrialsFile(self, event):
        dlg = wx.FileDialog(
            self, message="Open file ...", style=wx.OPEN
            )
        if dlg.ShowModal() == wx.ID_OK:
            newPath = dlg.GetPath()
            self.trialListFile = newPath
            self.importTrialTypes(newPath)
            self.constantsCtrls['trialListFile'].setValue(self.getAbbriev(newPath))
            self.constantsCtrls['trialList'].setValue(self.getTrialsSummary(self.trialList))
    def getParams(self):
        """retrieves data and re-inserts it into the handler and returns those handler params
        """
        #get data from input fields
        for fieldName in self.currentHandler.params.keys():
            param=self.currentHandler.params[fieldName]
            ctrls = self.currentCtrls[fieldName]#the various dlg ctrls for this param
            param.val = ctrls.getValue()#from _baseParamsDlg (handles diff control types)
            if ctrls.typeCtrl: param.valType = ctrls.getType()
            if ctrls.updateCtrl: param.updates = ctrls.getUpdates()
        return self.currentHandler.params
class DlgComponentProperties(_BaseParamsDlg):
    def __init__(self,frame,title,params,order,suppressTitles=True,
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT):
        style=style|wx.RESIZE_BORDER
        _BaseParamsDlg.__init__(self,frame,title,params,order,
                                pos=pos,size=size,style=style)
        self.frame=frame
        self.app=frame.app
        self.dpi=self.app.dpi

        #for input devices:
        if 'storeCorrect' in self.params:
            self.onStoreCorrectChange(event=None)#do this just to set the initial values to be
            self.Bind(wx.EVT_CHECKBOX, self.onStoreCorrectChange, self.paramCtrls['storeCorrect'].valueCtrl)

        #for all components
        self.show()
        if self.OK:
            self.params = self.getParams()#get new vals from dlg
        self.Destroy()
    def onStoreCorrectChange(self,event=None):
        """store correct has been checked/unchecked. Show or hide the correctIf field accordingly"""
        if self.paramCtrls['storeCorrect'].valueCtrl.GetValue():
            self.paramCtrls['correctIf'].valueCtrl.Show()
            self.paramCtrls['correctIf'].nameCtrl.Show()
            #self.paramCtrls['correctIf'].typeCtrl.Show()
            #self.paramCtrls['correctIf'].updateCtrl.Show()
        else:
            self.paramCtrls['correctIf'].valueCtrl.Hide()
            self.paramCtrls['correctIf'].nameCtrl.Hide()
            #self.paramCtrls['correctIf'].typeCtrl.Hide()
            #self.paramCtrls['correctIf'].updateCtrl.Hide()
        self.ctrlSizer.Layout()
        self.Fit()
        self.Refresh()

class DlgExperimentProperties(_BaseParamsDlg):
    def __init__(self,frame,title,params,order,suppressTitles=False,
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT):
        style=style|wx.RESIZE_BORDER
        _BaseParamsDlg.__init__(self,frame,title,params,order,
                                pos=pos,size=size,style=style)
        self.frame=frame
        self.app=frame.app
        self.dpi=self.app.dpi

        #for input devices:
        self.onFullScrChange(event=None)#do this just to set the initial values to be
        self.Bind(wx.EVT_CHECKBOX, self.onFullScrChange, self.paramCtrls['Full-screen window'].valueCtrl)

        #for all components
        self.show()
        if self.OK:
            self.params = self.getParams()#get new vals from dlg
        self.Destroy()
    def onFullScrChange(self,event=None):
        """store correct has been checked/unchecked. Show or hide the correctIf field accordingly"""
        if self.paramCtrls['Full-screen window'].valueCtrl.GetValue():
            self.paramCtrls['Window size (pixels)'].valueCtrl.Disable()
            self.paramCtrls['Window size (pixels)'].nameCtrl.Disable()
        else:
            self.paramCtrls['Window size (pixels)'].valueCtrl.Enable()
            self.paramCtrls['Window size (pixels)'].nameCtrl.Enable()
        self.ctrlSizer.Layout()
        self.Fit()
        self.Refresh()

    def show(self):
        """Adds an OK and cancel button, shows dialogue.

        This method returns wx.ID_OK (as from ShowModal), but also
        sets self.OK to be True or False
        """
        #add buttons for OK and Cancel
        self.mainSizer=wx.BoxSizer(wx.VERTICAL)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.OKbtn = wx.Button(self, wx.ID_OK, " OK ")
        self.OKbtn.SetDefault()
        buttons.Add(self.OKbtn, 0, wx.ALL,border=3)
        CANCEL = wx.Button(self, wx.ID_CANCEL, " Cancel ")
        buttons.Add(CANCEL, 0, wx.ALL,border=3)

        self.mainSizer.Add(self.ctrlSizer)
        self.mainSizer.Add(buttons, wx.ALIGN_RIGHT)
        self.SetSizerAndFit(self.mainSizer)
        #do show and process return
        retVal = self.ShowModal()
        if retVal== wx.ID_OK: self.OK=True
        else:  self.OK=False
        return wx.ID_OK
class BuilderFrame(wx.Frame):

    def __init__(self, parent, id=-1, title='PsychoPy (Experiment Builder)',
                 pos=wx.DefaultPosition, files=None,
                 style=wx.DEFAULT_FRAME_STYLE, app=None):
                 
        self.app=app
        self.dpi=self.app.dpi
        self.appData = self.app.prefs.appData['builder']#things the user doesn't set like winsize etc
        self.prefs = self.app.prefs.builder#things about the coder that get set
        self.appPrefs = self.app.prefs.app
        self.paths = self.app.prefs.paths
        self.IDs = self.app.IDs
        
        if self.appData['winH']==0 or self.appData['winW']==0:#we didn't have the key or the win was minimized/invalid
            self.appData['winH'], self.appData['winW'] =wx.DefaultSize
            self.appData['winX'],self.appData['winY'] =wx.DefaultPosition
        wx.Frame.__init__(self, parent, id, title, (self.appData['winX'], self.appData['winY']),
                         size=(self.appData['winW'],self.appData['winH']),
                         style=style)

        self.panel = wx.Panel(self)

        # create our panels
        self.flowPanel=FlowPanel(frame=self)
        self.routinePanel=RoutinesNotebook(self)
        self.componentButtons=ComponentsPanel(self)
        #menus and toolbars
        self.makeToolbar()
        self.makeMenus()

        #
        self.stdoutOrig = sys.stdout
        self.stderrOrig = sys.stderr
        self.stdoutFrame=stdOutRich.StdOutFrame(parent=self, app=self.app, size=(700,300))

        #setup a blank exp
        if self.prefs['reloadPrevExp'] and os.path.isfile(self.appData['prevFile']):
            self.fileOpen(filename=self.appData['prevFile'], closeCurrent=False)
        else:
            self.lastSavedCopy=None
            self.fileNew(closeCurrent=False)#don't try to close before opening
            self.exp.addRoutine('trial') #create the trial routine as an example
            self.exp.flow.addRoutine(self.exp.routines['trial'], pos=1)#add it to flow
            self.updateAllViews()
            self.resetUndoStack() #so that the above 2 changes don't show up as undo-able
            self.setIsModified(False)

        #control the panes using aui manager
        self._mgr = wx.aui.AuiManager(self)
        self._mgr.AddPane(self.routinePanel, wx.aui.AuiPaneInfo().
                          Name("Routines").Caption("Routines").
                          CenterPane(). #'center panes' expand to fill space
                          CloseButton(False).MaximizeButton(True))
        self._mgr.AddPane(self.componentButtons, wx.aui.AuiPaneInfo().
                          Name("Components").Caption("Components").
                          RightDockable(True).LeftDockable(True).CloseButton(False).
                          Right())
        self._mgr.AddPane(self.flowPanel, 
                          wx.aui.AuiPaneInfo().
                          Name("Flow").Caption("Flow").BestSize((8*self.dpi,2*self.dpi)).
                          RightDockable(True).LeftDockable(True).CloseButton(False).
                          Bottom())
        #tell the manager to 'commit' all the changes just made
        self._mgr.Update()
        
        #self.SetSizer(self.mainSizer)#not necessary for aui type controls
        if self.appData['auiPerspective']:
            self._mgr.LoadPerspective(self.appData['auiPerspective'])
        self.SetMinSize(wx.Size(800, 600)) #min size for the whole window
        self.Fit()
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
            if self.appPrefs['largeIcons']: toolbarSize=32
            else: toolbarSize=16
        else:
            toolbarSize=32 #size 16 doesn't work on mac wx
        self.toolbar.SetToolBitmapSize((toolbarSize,toolbarSize))
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

        self.toolbar.AddSimpleTool(self.IDs.tbFileNew, new_bmp, "New [%s]" %self.app.keys.new, "Create new python file")
        self.toolbar.Bind(wx.EVT_TOOL, self.fileNew, id=self.IDs.tbFileNew)
        self.toolbar.AddSimpleTool(self.IDs.tbFileOpen, open_bmp, "Open [%s]" %self.app.keys.open, "Open an existing file'")
        self.toolbar.Bind(wx.EVT_TOOL, self.fileOpen, id=self.IDs.tbFileOpen)
        self.toolbar.AddSimpleTool(self.IDs.tbFileSave, save_bmp, "Save [%s]" %self.app.keys.save,  "Save current file")
        self.toolbar.EnableTool(self.IDs.tbFileSave, False)
        self.toolbar.Bind(wx.EVT_TOOL, self.fileSave, id=self.IDs.tbFileSave)
        self.toolbar.AddSimpleTool(self.IDs.tbFileSaveAs, saveAs_bmp, "Save As... [%s]" %self.app.keys.saveAs, "Save current python file as...")
        self.toolbar.Bind(wx.EVT_TOOL, self.fileSaveAs, id=self.IDs.tbFileSaveAs)
        self.toolbar.AddSimpleTool(self.IDs.tbUndo, undo_bmp, "Undo [%s]" %self.app.keys.undo, "Undo last action")
        self.toolbar.Bind(wx.EVT_TOOL, self.undo, id=self.IDs.tbUndo)
        self.toolbar.AddSimpleTool(self.IDs.tbRedo, redo_bmp, "Redo [%s]" %self.app.keys.redo,  "Redo last action")
        self.toolbar.Bind(wx.EVT_TOOL, self.redo, id=self.IDs.tbRedo)
        self.toolbar.AddSeparator()
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(self.IDs.tbPreferences, preferences_bmp, "Preferences",  "Application preferences")
        self.toolbar.Bind(wx.EVT_TOOL, self.app.showPrefs, id=self.IDs.tbPreferences)
        self.toolbar.AddSimpleTool(self.IDs.tbMonitorCenter, monitors_bmp, "Monitor Center",  "Monitor settings and calibration")
        self.toolbar.Bind(wx.EVT_TOOL, self.app.openMonitorCenter, id=self.IDs.tbMonitorCenter)
        self.toolbar.AddSeparator()
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(self.IDs.tbExpSettings, settings_bmp, "Experiment Settings",  "Settings for this exp")
        self.toolbar.Bind(wx.EVT_TOOL, self.setExperimentSettings, id=self.IDs.tbExpSettings)
        self.toolbar.AddSimpleTool(self.IDs.tbCompile, compile_bmp, "Compile Script [%s]" %self.app.keys.compileScript,  "Compile to script")
        self.toolbar.Bind(wx.EVT_TOOL, self.compileScript, id=self.IDs.tbCompile)
        self.toolbar.AddSimpleTool(self.IDs.tbRun, run_bmp, "Run/t%s" %self.app.keys.runScript,  "Run experiment")
        self.toolbar.Bind(wx.EVT_TOOL, self.runFile, id=self.IDs.tbRun)
        self.toolbar.AddSimpleTool(self.IDs.tbStop, stop_bmp, "Stop/t%s" %self.app.keys.stopScript,  "Stop experiment")
        self.toolbar.Bind(wx.EVT_TOOL, self.stopFile, id=self.IDs.tbStop)
        self.toolbar.EnableTool(self.IDs.tbStop,False)
        self.toolbar.Realize()

    def makeMenus(self):
        #---Menus---#000000#FFFFFF--------------------------------------------------
        menuBar = wx.MenuBar()
        #---_file---#000000#FFFFFF--------------------------------------------------
        self.fileMenu = wx.Menu()
        menuBar.Append(self.fileMenu, '&File')
        self.fileMenu.Append(wx.ID_NEW,     "&New\t%s" %self.app.keys.new)
        self.fileMenu.Append(wx.ID_OPEN,    "&Open...\t%s" %self.app.keys.open)
        self.fileMenu.Append(wx.ID_SAVE,    "&Save\t%s" %self.app.keys.save)
        self.fileMenu.Append(wx.ID_SAVEAS,  "Save &as...\t%s" %self.app.keys.saveAs)
        self.fileMenu.Append(wx.ID_CLOSE,   "&Close file\t%s" %self.app.keys.close)
        wx.EVT_MENU(self, wx.ID_NEW,  self.fileNew)
        wx.EVT_MENU(self, wx.ID_OPEN,  self.fileOpen)
        wx.EVT_MENU(self, wx.ID_SAVE,  self.fileSave)
        self.fileMenu.Enable(wx.ID_SAVE, False)
        wx.EVT_MENU(self, wx.ID_SAVEAS,  self.fileSaveAs)
        wx.EVT_MENU(self, wx.ID_CLOSE,  self.closeFrame)
        item = self.fileMenu.Append(wx.ID_PREFERENCES, text = "&Preferences")
        self.Bind(wx.EVT_MENU, self.app.showPrefs, item)
        #-------------quit
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(wx.ID_EXIT, "&Quit\t%s" %self.app.keys.quit, "Terminate the program")
        wx.EVT_MENU(self, wx.ID_EXIT, self.quit)

        self.editMenu = wx.Menu()
        menuBar.Append(self.editMenu, '&Edit')
        self.editMenu.Append(wx.ID_UNDO, "Undo\t%s" %self.app.keys.undo, "Undo last action", wx.ITEM_NORMAL)
        wx.EVT_MENU(self, wx.ID_UNDO,  self.undo)
        self.editMenu.Append(wx.ID_REDO, "Redo\t%s" %self.app.keys.redo, "Redo last action", wx.ITEM_NORMAL)
        wx.EVT_MENU(self, wx.ID_REDO,  self.redo)

        #---_tools---#000000#FFFFFF--------------------------------------------------
        self.toolsMenu = wx.Menu()
        menuBar.Append(self.toolsMenu, '&Tools')
        self.toolsMenu.Append(self.IDs.monitorCenter, "Monitor Center", "To set information about your monitor")
        wx.EVT_MENU(self, self.IDs.monitorCenter,  self.app.openMonitorCenter)

        self.toolsMenu.Append(self.IDs.compileScript, "Compile\t%s" %self.app.keys.compileScript, "Compile the exp to a script")
        wx.EVT_MENU(self, self.IDs.compileScript,  self.compileScript)
        self.toolsMenu.Append(self.IDs.runFile, "Run\t%s" %self.app.keys.runScript, "Run the current script")
        wx.EVT_MENU(self, self.IDs.runFile,  self.runFile)
        self.toolsMenu.Append(self.IDs.stopFile, "Stop\t%s" %self.app.keys.stopScript, "Abort the current script")
        wx.EVT_MENU(self, self.IDs.stopFile,  self.stopFile)

        #---_view---#000000#FFFFFF--------------------------------------------------
        self.viewMenu = wx.Menu()
        menuBar.Append(self.viewMenu, '&View')
        self.viewMenu.Append(self.IDs.openCoderView, "&Open Coder view\t%s" %self.app.keys.switchToCoder, "Open a new Coder view")
        wx.EVT_MENU(self, self.IDs.openCoderView,  self.app.showCoder)

        #---_experiment---#000000#FFFFFF--------------------------------------------------
        self.expMenu = wx.Menu()
        menuBar.Append(self.expMenu, '&Experiment')
        self.expMenu.Append(self.IDs.newRoutine, "New Routine", "Create a new routine (e.g. the trial definition)")
        wx.EVT_MENU(self, self.IDs.newRoutine,  self.addRoutine)
        self.expMenu.AppendSeparator()

        self.expMenu.Append(self.IDs.addRoutineToFlow, "Insert Routine in Flow", "Select one of your routines to be inserted into the experiment flow")
        wx.EVT_MENU(self, self.IDs.addRoutineToFlow,  self.flowPanel.onInsertRoutine)
        self.expMenu.Append(self.IDs.addLoopToFlow, "Insert Loop in Flow", "Create a new loop in your flow window")
        wx.EVT_MENU(self, self.IDs.addLoopToFlow,  self.flowPanel.onInsertLoop)

        #---_demos---#000000#FFFFFF--------------------------------------------------
        #for demos we need a dict where the event ID will correspond to a filename
        demoList = glob.glob(os.path.join(self.app.prefs.paths['demos'],'*.psyexp'))
        #demoList = glob.glob(os.path.join(appDir,'..','demos','*.py'))
        ID_DEMOS = \
            map(lambda _makeID: wx.NewId(), range(len(demoList)))
        self.demos={}
        for n in range(len(demoList)):
            self.demos[ID_DEMOS[n]] = demoList[n]
        self.demosMenu = wx.Menu()
        #menuBar.Append(self.demosMenu, '&Demos')
        for thisID in ID_DEMOS:
            junk, shortname = os.path.split(self.demos[thisID])
            self.demosMenu.Append(thisID, shortname)
            wx.EVT_MENU(self, thisID, self.loadDemo)

        #---_help---#000000#FFFFFF--------------------------------------------------
        self.helpMenu = wx.Menu()
        menuBar.Append(self.helpMenu, '&Help')
        self.helpMenu.Append(self.IDs.psychopyHome, "&PsychoPy Homepage", "Go to the PsychoPy homepage")
        wx.EVT_MENU(self, self.IDs.psychopyHome, self.app.followLink)
        self.helpMenu.Append(self.IDs.psychopyTutorial, "&PsychoPy Tutorial", "Go to the online PsychoPy tutorial")
        wx.EVT_MENU(self, self.IDs.psychopyTutorial, self.app.followLink)

        self.helpMenu.AppendSeparator()
        self.helpMenu.Append(self.IDs.about, "&About...", "About PsychoPy")
        wx.EVT_MENU(self, self.IDs.about, self.app.showAbout)

        self.demosMenu
        self.helpMenu.AppendSubMenu(self.demosMenu, 'PsychoPy Demos')
        self.SetMenuBar(menuBar)
    def closeFrame(self, event=None, checkSave=True):

        if self.app.coder==None and platform.system()!='Darwin':
            if not self.app.quitting: 
                self.app.quit()
                return#app.quit() will have closed the frame already

        if checkSave:
            ok=self.checkSave()
            if not ok: return False
        self.appData['prevFile']=self.filename
        
        #get size and window layout info
        if self.IsIconized():
            self.Iconize(False)#will return to normal mode to get size info
            self.appData['state']='normal'
        elif self.IsMaximized():
            self.Maximize(False)#will briefly return to normal mode to get size info
            self.appData['state']='maxim'
        else:
            self.appData['state']='normal'
        self.appData['auiPerspective'] = self._mgr.SavePerspective()
        self.appData['winW'], self.appData['winH']=self.GetSize()
        self.appData['winX'], self.appData['winY']=self.GetPosition() 
        if sys.platform=='darwin':
            self.appData['winH'] -= 39#for some reason mac wxpython <=2.8 gets this wrong (toolbar?)
        
        self.Destroy()
        self.app.builder=None
        return 1#indicates that check was successful
    def quit(self, event=None):
        """quit the app"""
        self.app.quit()
    def fileNew(self, event=None, closeCurrent=True):
        """Create a default experiment (maybe an empty one instead)"""
        # check whether existing file is modified
        if closeCurrent: #if no exp exists then don't try to close it
            if not self.fileClose(): return False #close the existing (and prompt for save if necess)
        self.filename='untitled.psyexp'
        self.exp = experiment.Experiment()
        self.resetUndoStack()
        self.updateAllViews()
    def fileOpen(self, event=None, filename=None, closeCurrent=True):
        """Open a FileDialog, then load the file if possible.
        """
        if filename==None:
            dlg = wx.FileDialog(
                self, message="Open file ...", style=wx.OPEN,
                wildcard="PsychoPy experiments (*.psyexp)|*.psyexp|Any file (*.*)|*",
                )

            if dlg.ShowModal() != wx.ID_OK:
                return 0
            filename = dlg.GetPath()
        if closeCurrent:
            if not self.fileClose(): return False #close the existing (and prompt for save if necess)
        self.exp = experiment.Experiment()
        self.exp.loadFromXML(filename)
        self.resetUndoStack()
        self.setIsModified(False)
        self.filename = filename
        #load routines
        for thisRoutineName in self.exp.routines.keys():
            routine = self.exp.routines[thisRoutineName]
            self.routinePanel.addRoutinePage(thisRoutineName, routine)
        #update the views
        self.updateAllViews()
    def fileSave(self,event=None, filename=None):
        """Save file, revert to SaveAs if the file hasn't yet been saved
        """
        if filename==None:
            filename = self.filename
        if filename.startswith('untitled'):
            if not self.fileSaveAs(filename):
                return False #the user cancelled during saveAs
        else:
            self.exp.saveToXML(filename)
        self.setIsModified(False)
        return True
    def fileSaveAs(self,event=None, filename=None):
        """
        """
        if filename==None: filename = self.filename
        initPath, filename = os.path.split(filename)

        os.getcwd()
        if sys.platform=='darwin':
            wildcard="PsychoPy experiments (*.psyexp)|*.psyexp|Any file (*.*)|*"
        else:
            wildcard="PsychoPy experiments (*.psyexp)|*.psyexp|Any file (*.*)|*.*"
        returnVal=False
        dlg = wx.FileDialog(
            self, message="Save file as ...", defaultDir=initPath,
            defaultFile=filename, style=wx.SAVE, wildcard=wildcard)
        if dlg.ShowModal() == wx.ID_OK:
            newPath = dlg.GetPath()
            #update exp name
            shortName = os.path.splitext(os.path.split(newPath)[1])[0]
            self.exp.setExpName(shortName)
            #actually save
            self.fileSave(event=None, filename=newPath)
            self.filename = newPath
            returnVal = 1
        try: #this seems correct on PC, but not on mac
            dlg.destroy()
        except:
            pass
        self.updateWindowTitle()
        return returnVal
    def checkSave(self):
        """Check whether we need to save before quitting
        """
        if hasattr(self, 'isModified') and self.isModified:
            dlg = dialogs.MessageDialog(self,'Experiment has changed. Save before quitting?', type='Warning')
            resp = dlg.ShowModal()
            dlg.Destroy()
            if resp  == wx.ID_CANCEL: return False #return, don't quit
            elif resp == wx.ID_YES: 
                if not self.fileSave(): return False #user might cancel during save
            elif resp == wx.ID_NO: pass #don't save just quit
        return 1
    def fileClose(self, event=None, checkSave=True):
        """Not currently used? Frame is closed rather than file"""
        if checkSave:
            ok = self.checkSave()
            if not ok: return False#user cancelled
        #close self
        self.routinePanel.removePages()
        self.filename = 'untitled.psyexp'
        self.resetUndoStack()#will add the current exp as the start point for undo
        self.updateAllViews()
        return 1
    def updateAllViews(self):
        self.flowPanel.redrawFlow()
        self.routinePanel.redrawRoutines()
        self.updateWindowTitle()
    def updateWindowTitle(self, newTitle=None):
        if newTitle==None:
            shortName = os.path.split(self.filename)[-1]
            newTitle='PsychoPy (Experiment Builder) - %s' %(shortName)
        self.SetTitle(newTitle)
    def setIsModified(self, newVal=None):
        """Sets current modified status and updates save icon accordingly.

        This method is called by the methods fileSave, undo, redo, addToUndoStack
        and it is usually preferably to call those than to call this directly.

        Call with ``newVal=None``, to only update the save icon(s)
        """
        if newVal==None:
            newVal= self.getIsModified()
        else: self.isModified=newVal
#        elif newVal==False:
#            self.lastSavedCopy=copy.copy(self.exp)
#            print 'made new copy of exp'
#        #then update buttons/menus
#        if newVal:
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
        self.enableUndo(False)
        self.enableRedo(False)
        self.setIsModified(newVal=False)#update save icon if needed
    def addToUndoStack(self, action="", state=None):
        """Add the given ``action`` to the currentUndoStack, associated with the @state@.
        ``state`` should be a copy of the exp from *immediately after* the action was taken.
        If no ``state`` is given the current state of the experiment is used.

        If we are at end of stack already then simply append the action.
        If not (user has done an undo) then remove orphan actions and then append.
        """
        if state==None:
            state=copy.deepcopy(self.exp)
        #remove actions from after the current level
#        print 'before stack=', self.currentUndoStack
        if self.currentUndoLevel>1:
            self.currentUndoStack = self.currentUndoStack[:-(self.currentUndoLevel-1)]
            self.currentUndoLevel=1
        #append this action
        self.currentUndoStack.append({'action':action,'state':state})
        self.enableUndo(True)
        self.setIsModified(newVal=True)#update save icon if needed
#        print 'after stack=', self.currentUndoStack
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
        #set undo redo buttons
        self.enableRedo(True)#if we've undone, then redo must be possible
        if (self.currentUndoLevel)==len(self.currentUndoStack):
            self.enableUndo(False)
        self.updateAllViews()
        self.setIsModified(newVal=True)#update save icon if needed
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
        #set undo redo buttons
        self.enableUndo(True)#if we've redone then undo must be possible
        if self.currentUndoLevel==1:
            self.enableRedo(False)
        self.updateAllViews()
        self.setIsModified(newVal=True)#update save icon if needed
        # return
        return self.currentUndoLevel
    def enableRedo(self,enable=True):
        self.toolbar.EnableTool(self.IDs.tbRedo,enable)
        self.editMenu.Enable(wx.ID_REDO,enable)
    def enableUndo(self,enable=True):
        self.toolbar.EnableTool(self.IDs.tbUndo,enable)
        self.editMenu.Enable(wx.ID_UNDO,enable)
    def loadDemo(self, event=None):
        #todo: loadDemo
        pass
    def runFile(self, event=None):
        script = self.exp.writeScript()
        fullPath = self.filename.replace('.psyexp','_lastrun.py')
        path, scriptName = os.path.split(fullPath)
        shortName, ext = os.path.splitext(scriptName)

        #set the directory and add to path
        if len(path)>0: os.chdir(path)#otherwise this is unsaved 'untitled.psyexp'
        f = open(fullPath, 'w')
        f.write(script.getvalue())
        f.close()

        sys.stdout = self.stdoutFrame
        sys.stderr = self.stdoutFrame

        self.scriptProcess=wx.Process(self) #self is the parent (which will receive an event when the process ends)
        self.scriptProcess.Redirect()#builder will receive the stdout/stdin
        self.stdoutFrame

        if sys.platform=='win32':
            command = '"%s" -u "%s"' %(sys.executable, fullPath)# the quotes allow file paths with spaces
            #self.scriptProcessID = wx.Execute(command, wx.EXEC_ASYNC, self.scriptProcess)
            self.scriptProcessID = wx.Execute(command, wx.EXEC_ASYNC| wx.EXEC_NOHIDE, self.scriptProcess)
        else:
            fullPath= fullPath.replace(' ','\ ')#for unix this signifis a space in a filename
            command = '%s -u %s' %(sys.executable, fullPath)# the quotes would break a unix system command
            self.scriptProcessID = wx.Execute(command, wx.EXEC_ASYNC| wx.EXEC_MAKE_GROUP_LEADER, self.scriptProcess)
        self.toolbar.EnableTool(self.IDs.tbRun,False)
        self.toolbar.EnableTool(self.IDs.tbStop,True)
    def stopFile(self, event=None):
        success = wx.Kill(self.scriptProcessID,wx.SIGTERM) #try to kill it gently first
        if success[0] != wx.KILL_OK:
            wx.Kill(self.scriptProcessID,wx.SIGKILL) #kill it aggressively
        self.processEnded(event=None)
    def onProcessEnded(self, event=None):
        """The script/exp has finished running
        """
        self.toolbar.EnableTool(self.IDs.tbRun,True)
        self.toolbar.EnableTool(self.IDs.tbStop,False)
        #update the output window and show it
        text=""
        if self.scriptProcess.IsInputAvailable():
            stream = self.scriptProcess.GetInputStream()
            text.append(stream.read())
        if self.scriptProcess.IsErrorAvailable():
            stream = self.scriptProcess.GetErrorStream()
            text.append(stream.read())
        if len(text):
            self.stdoutFrame.write(text)
            self.stdoutFrame.Show()
            self.stdoutFrame.Raise()
        #then return stdout to its org location
        sys.stdout=self.stdoutOrig
        sys.stderr=self.stderrOrig
    def onURL(self, evt):
        """decompose the URL of a file and line number"""
        # "C:\\Program Files\\wxPython2.8 Docs and Demos\\samples\\hangman\\hangman.py", line 21,
        filename = evt.GetString().split('"')[1]
        lineNumber = int(evt.GetString().split(',')[1][5:])
        self.app.coder.gotoLine(filename,lineNumber)
        self.app.showCoder()
    def compileScript(self, event=None):
        script = self.exp.writeScript()
        name = os.path.splitext(self.filename)[0]+".py"#remove .psyexp and add .py
        self.app.showCoder()#make sure coder is visible
        self.app.coder.fileNew(filepath=name)
        self.app.coder.currentDoc.SetText(script.getvalue())
    def setExperimentSettings(self,event=None):
        component=self.exp.settings
        dlg = DlgExperimentProperties(frame=self,
            title='%s Properties' %self.exp.name,
            params = component.params,
            order = component.order)
        if dlg.OK:
            self.addToUndoStack("edit experiment settings")
            self.setIsModified(True)
    def addRoutine(self, event=None):
        self.routinePanel.createNewRoutine()
