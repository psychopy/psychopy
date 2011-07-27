# Part of the PsychoPy library
# Copyright (C) 2011 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import wx
from wx.lib import platebtn, scrolledpanel
#from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
#import wx.lib.agw.aquabutton as AB
import wx.aui
import sys, os, glob, copy, platform, shutil, traceback
import py_compile, codecs
import csv, numpy
import experiment, components
from psychopy.app import stdOutRich, dialogs
from psychopy import data, log, misc
import re
from psychopy.constants import *

inf = FOREVER #see constants.py
canvasColor=[200,200,200]#in prefs? ;-)

class FileDropTarget(wx.FileDropTarget):
    """On Mac simply setting a handler for the EVT_DROP_FILES isn't enough.
    Need this too.
    """
    def __init__(self, builder):
        wx.FileDropTarget.__init__(self)
        self.builder = builder
    def OnDropFiles(self, x, y, filenames):
        log.debug('PsychoPyBuilder: received dropped files: filenames')
        for filename in filenames:
            self.builder.fileOpen(filename=filename)

class FlowPanel(wx.ScrolledWindow):
    def __init__(self, frame, id=-1):
        """A panel that shows how the routines will fit together
        """
        self.frame=frame
        self.app=frame.app
        self.dpi=self.app.dpi
        wx.ScrolledWindow.__init__(self, frame, id, (0, 0),size = wx.Size(8*self.dpi,3*self.dpi), style=wx.HSCROLL|wx.VSCROLL)
        self.SetBackgroundColour(canvasColor)
        self.needUpdate=True
        self.maxWidth  = 50*self.dpi
        self.maxHeight = 2*self.dpi
        self.mousePos = None
        #if we're adding a loop or routine then add spots to timeline
        self.drawNearestRoutinePoint = True
        self.drawNearestLoopPoint = False
        self.pointsToDraw=[] #lists the x-vals of points to draw, eg loop locations

        #self.SetAutoLayout(True)
        self.SetScrollRate(self.dpi/4,self.dpi/4)

        # create a PseudoDC to record our drawing
        self.pdc = wx.PseudoDC()
        self.pen_cache = {}
        self.brush_cache = {}
        # vars for handling mouse clicks
        self.hitradius=5
        self.dragid = -1
        self.entryPointPosList = []
        self.entryPointIDlist = []
        self.mode = 'normal'#can also be 'loopPoint1','loopPoint2','routinePoint'
        self.insertingRoutine=""

        #for the context menu
        self.componentFromID={}#use the ID of the drawn icon to retrieve component (loop or routine)
        self.contextMenuItems=['remove']
        self.contextItemFromID={}; self.contextIDFromItem={}
        for item in self.contextMenuItems:
            id = wx.NewId()
            self.contextItemFromID[id] = item
            self.contextIDFromItem[item] = id

        #self.btnInsertRoutine = wx.Button(self,-1,'Insert Routine', pos=(10,10))
        #self.btnInsertLoop = wx.Button(self,-1,'Insert Loop', pos=(10,30))
        self.btnInsertRoutine = platebtn.PlateButton(self,-1,'Insert Routine', pos=(10,10))
        self.btnInsertLoop = platebtn.PlateButton(self,-1,'Insert Loop', pos=(10,30))
        self.btnQuitInsert = platebtn.PlateButton(self,-1,'  cancel insert  ', pos=(10,50))
        self.labelTextGray = {'normal': wx.Color(150,150,150, 20),'hlight':wx.Color(150,150,150, 20)}
        self.labelTextRed = {'normal': wx.Color(250,10,10, 250),'hlight':wx.Color(250,10,10, 250)}
        self.btnQuitInsert.SetLabelColor(**self.labelTextGray)
        self.btnNewRoutine = platebtn.PlateButton(self,-1,'New Routine', pos=(10,80))
        if self.app.prefs.app['debugMode']:
            self.btnViewNamespace = platebtn.PlateButton(self,-1,'dump name-space', pos=(10,110))

        self.draw()

        #bind events
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)
        self.Bind(wx.EVT_BUTTON, self.onInsertRoutine,self.btnInsertRoutine)
        self.Bind(wx.EVT_BUTTON, self.setLoopPoint1,self.btnInsertLoop)
        self.Bind(wx.EVT_BUTTON, self.frame.addRoutine, self.btnNewRoutine)
        self.Bind(wx.EVT_BUTTON, self.clearMode, self.btnQuitInsert)
        if self.app.prefs.app['debugMode']:
            self.Bind(wx.EVT_BUTTON, self.dumpNamespace, self.btnViewNamespace)
        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.SetDropTarget(FileDropTarget(builder = self.frame))
        
        idClear = wx.NewId()
        self.Bind(wx.EVT_MENU, self.clearMode, id=idClear )
        aTable = wx.AcceleratorTable([
                              (wx.ACCEL_NORMAL, wx.WXK_ESCAPE, idClear)
                              ])
        self.SetAcceleratorTable(aTable)
    def clearMode(self, event=None):
        """If we were in middle of doing something (like inserting routine) then
        end it, allowing user to cancel
        """
        self.mode='normal'
        self.insertingRoutine=None
        for id in self.entryPointIDlist:
            self.pdc.RemoveId(id)
        self.entryPointPosList = []
        self.entryPointIDlist = []
        self.draw()
        self.frame.SetStatusText("")
        self.btnQuitInsert.SetLabel('  cancel insert  ')
        self.btnQuitInsert.SetLabelColor(**self.labelTextGray)
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
        """For when the insert Routine button is pressed - bring up dialog and
        present insertion point on flow line.
        see self.insertRoutine() for further info
        """
        self.frame.SetStatusText("Select a Routine to insert (Esc to exit)")
        menu = wx.Menu()
        self.routinesFromID={}
        for routine in self.frame.exp.routines:
            id = wx.NewId()
            menu.Append( id, routine )
            self.routinesFromID[id]=routine
            wx.EVT_MENU( menu, id, self.onInsertRoutineSelect )
        btnPos = self.btnInsertRoutine.GetRect()
        menuPos = (btnPos[0], btnPos[1]+btnPos[3])
        self.PopupMenu( menu, menuPos )
        menu.Bind(wx.EVT_MENU_CLOSE, self.clearMode)
        menu.Destroy() # destroy to avoid mem leak
    def onInsertRoutineSelect(self,event):
        """User has selected a routine to be entered so bring up the entrypoint marker
        and await mouse button press.
        see self.insertRoutine() for further info
        """
        self.mode='routine'
        self.btnQuitInsert.SetLabel('CANCEL Insert')
        self.btnQuitInsert.SetLabelColor(**self.labelTextRed)
        self.frame.SetStatusText('Click where you want to insert the Routine, or CANCEL insert.')
        self.insertingRoutine = self.routinesFromID[event.GetId()]
        x = self.getNearestGapPoint(0)
        self.drawEntryPoints([x])
    def insertRoutine(self, ii):
        """Insert a routine into the Flow having determined its name and location

        onInsertRoutine() the button has been pressed so present menu
        onInsertRoutineSelect() user selected the name so present entry points
        OnMouse() user has selected a point on the timeline to insert entry

        """
        self.frame.exp.flow.addRoutine(self.frame.exp.routines[self.insertingRoutine], ii)
        self.frame.addToUndoStack("AddRoutine")
        #reset flow drawing (remove entry point)
        self.clearMode()

    def setLoopPoint1(self, evt=None):
        """Someone pushed the insert loop button.
        Fetch the dialog
        """
        self.mode='loopPoint1'
        self.frame.SetStatusText('Click where you want the loop to start/end, or CANCEL insert.')
        self.btnQuitInsert.SetLabel('CANCEL Insert')
        self.btnQuitInsert.SetLabelColor(**self.labelTextRed)
        x = self.getNearestGapPoint(0)
        self.drawEntryPoints([x])
    def setLoopPoint2(self, evt=None):
        """Someone pushed the insert loop button.
        Fetch the dialog
        """
        self.mode='loopPoint2'
        self.frame.SetStatusText('Click the other start/end for the loop')
        x = self.getNearestGapPoint(wx.GetMousePosition()[0]-self.GetScreenPosition()[0],
            exclude=[self.entryPointPosList[0]])#exclude point 1
        self.drawEntryPoints([self.entryPointPosList[0], x])

    def insertLoop(self, evt=None):
        #bring up listbox to choose the routine to add and/or create a new one
        loopDlg = DlgLoopProperties(frame=self.frame,
            helpUrl = self.app.urls['builder.loops'])
        startII = self.gapMidPoints.index(min(self.entryPointPosList))
        endII = self.gapMidPoints.index(max(self.entryPointPosList))
        if loopDlg.OK:
            handler=loopDlg.currentHandler
            self.frame.exp.flow.addLoop(handler,
                startPos=startII, endPos=endII)
            self.frame.addToUndoStack("AddLoopToFlow")
        self.clearMode()
        self.draw()
    def dumpNamespace(self, evt=None):
        nsu = self.frame.exp.namespace.user
        if len(nsu) == 0:
            print "______________________\n <namespace is empty>"
            return
        nsu.sort()
        m = min(20, 2 + max([len(n) for n in nsu]))  # 2+len of longest word, or 20
        fmt = "%-"+str(m)+"s"  # format string: each word padded to longest
        nsu = map(lambda x: fmt % x, nsu)
        c = min(6, max(2, len(nsu)//4))  # number of columns, 2 - 6
        while len(nsu) % c: nsu += [' '] # avoid index errors later
        r = len(nsu) // c  # number of rows
        print '_' * c * m
        for i in range(r):
            print ' '+''.join([nsu[i+j*r] for j in range(c)])  # typially to coder output
        collisions = self.frame.exp.namespace.get_collisions()
        if collisions:
            print "*** collisions ***: %s" % str(collisions)
    def editLoopProperties(self, event=None, loop=None):
        if event:#we got here from a wx.button press (rather than our own drawn icons)
            loopName=event.EventObject.GetName()
            loop=self.routine.getLoopFromName(loopName)

        #add routine points to the timeline
        self.setDrawPoints('loops')
        self.draw()

        loopDlg = DlgLoopProperties(frame=self.frame,
            title=loop.params['name'].val+' Properties', loop=loop)
        if loopDlg.OK:
            if loopDlg.params['loopType'].val=='staircase': #['random','sequential','staircase']
                loop= loopDlg.stairHandler
            if loopDlg.params['loopType'].val=='interleaved stairs':
                loop= loopDlg.multiStairHandler
            else:
                loop=loopDlg.trialHandler
            loop.params=loop.params
            self.frame.addToUndoStack("Edit Loop")
        #remove the points from the timeline
        self.setDrawPoints(None)
        self.draw()

    def OnMouse(self, event):
        x,y = self.ConvertEventCoords(event)
        if self.mode=='normal':
            if event.LeftDown():
                icons = self.pdc.FindObjectsByBBox(x, y)
                for thisIcon in icons:#might intersect several and only one has a callback
                    if thisIcon in self.componentFromID:
                        comp=self.componentFromID[thisIcon]
                        if comp.getType() in ['StairHandler', 'TrialHandler']:
                            self.editLoopProperties(loop=comp)
                        if comp.getType() == 'Routine':
                            self.frame.routinePanel.setCurrentRoutine(routine=comp)
            elif event.RightDown():
                icons = self.pdc.FindObjectsByBBox(x, y)
                comp=None
                for thisIcon in icons:#might intersect several and only one has a callback
                    if thisIcon in self.componentFromID:
                        #loop through comps looking for Routine, or a Loop if no routine
                        thisComp=self.componentFromID[thisIcon]
                        if thisComp.getType() in ['StairHandler', 'TrialHandler']:
                            comp=thisComp#use this if we don't find a routine
                            icon=thisIcon
                        if thisComp.getType() == 'Routine':
                            comp=thisComp
                            icon=thisIcon
                            break#we've found a Routine so stop looking
                try:
                    self._menuComponentID=icon
                    self.showContextMenu(self._menuComponentID,
                        xy=wx.Point(x+self.GetPosition()[0],y+self.GetPosition()[1]))
                except UnboundLocalError:
                    pass # right click but not on an icon
        elif self.mode=='routine':
            if event.LeftDown():
                self.insertRoutine(ii=self.gapMidPoints.index(self.entryPointPosList[0]))
            else:#move spot if needed
                point = self.getNearestGapPoint(mouseX=x)
                self.drawEntryPoints([point])
        elif self.mode=='loopPoint1':
            if event.LeftDown():
                self.setLoopPoint2()
            else:#move spot if needed
                point = self.getNearestGapPoint(mouseX=x)
                self.drawEntryPoints([point])
        elif self.mode=='loopPoint2':
            if event.LeftDown():
                self.insertLoop()
            else:#move spot if needed
                point = self.getNearestGapPoint(mouseX=x)
                self.drawEntryPoints([self.entryPointPosList[0], point])
    def getNearestGapPoint(self, mouseX, exclude=[]):
        d=1000000000
        nearest=None
        for point in self.gapMidPoints:
            if point in exclude: continue
            if (point-mouseX)**2 < d:
                d=(point-mouseX)**2
                nearest=point
        return nearest
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
            # remove name from namespace only if its a loop (which exists only in the flow)
            if component.type in ['TrialHandler', 'StairHandler']:
                trialListFile = component.params['trialListFile'].val
                if trialListFile:
                    _, fieldNames = data.importTrialList(trialListFile, returnFieldNames=True)
                    for fname in fieldNames:
                        self.frame.exp.namespace.remove(fname)
                self.frame.exp.namespace.remove(component.params['name'].val)
            flow.removeComponent(component, id=self._menuComponentID)
            self.frame.addToUndoStack("removed %s from flow" %component.params['name'])
        if op=='rename':
            print 'rename is not implemented yet'
            #if component is a loop: DlgLoopProperties
            #elif comonent is a routine: DlgRoutineProperties
        self.draw()
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

    def draw(self, evt=None):
        """This is the main function for drawing the Flow panel.
        It should be called whenever something changes in the exp.

        This then makes calls to other drawing functions, like drawEntryPoints...
        """
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
        self.linePos = (2.5*self.dpi,0.5*self.dpi) #x,y of start
        dLoopToBaseLine=40
        dBetweenLoops = 25
        gap=self.dpi/2#gap (X) between entries in the flow

        #guess virtual size; nRoutines wide by nLoops high
        #make bigger than needed and shrink later
        nRoutines = len(expFlow)
        nLoops = 0
        for entry in expFlow:
            if entry.getType()=='LoopInitiator': nLoops+=1
        self.SetVirtualSize(size=(nRoutines*self.dpi*2, nLoops*dBetweenLoops+dLoopToBaseLine*3))

        #step through components in flow
        currX=self.linePos[0]
        lineId=wx.NewId()
        pdc.DrawLine(x1=self.linePos[0]-gap,y1=self.linePos[1],x2=self.linePos[0],y2=self.linePos[1])
        self.loops={}#NB the loop is itself the key!? and the value is further info about it
        nestLevel=0
        self.gapMidPoints=[currX-gap/2]
        for ii, entry in enumerate(expFlow):
            if entry.getType()=='LoopInitiator':
                self.loops[entry.loop]={'init':currX,'nest':nestLevel, 'id':ii}#NB the loop is itself the dict key!?
                nestLevel+=1#start of loop so increment level of nesting
            elif entry.getType()=='LoopTerminator':
                self.loops[entry.loop]['term']=currX #NB the loop is itself the dict key!
                nestLevel-=1#end of loop so decrement level of nesting
            elif entry.getType()=='Routine':
                currX = self.drawFlowRoutine(pdc,entry, id=ii,pos=[currX,self.linePos[1]-10])
            self.gapMidPoints.append(currX+gap/2)
            pdc.SetId(lineId)
            pdc.SetPen(wx.Pen(wx.Color(0,0,0, 255)))
            pdc.DrawLine(x1=currX,y1=self.linePos[1],x2=currX+gap,y2=self.linePos[1])
            currX+=gap
        lineRect = wx.Rect(self.linePos[0]-2, self.linePos[1]-2, currX-self.linePos[0]+2, 4)
        pdc.SetIdBounds(lineId,lineRect)

        #draw the loops second
        maxHeight = 0
        for thisLoop in self.loops.keys():
            thisInit = self.loops[thisLoop]['init']
            thisTerm = self.loops[thisLoop]['term']
            thisNest = len(self.loops.keys())-1-self.loops[thisLoop]['nest']
            thisId = self.loops[thisLoop]['id']
            name = thisLoop.params['name'].val#name of the trialHandler/StairHandler
            height = self.linePos[1]+dLoopToBaseLine + thisNest*dBetweenLoops
            self.drawLoop(pdc,name,thisLoop,id=thisId,
                        startX=thisInit, endX=thisTerm,
                        base=self.linePos[1],height=height,
                        downwards=True)
            self.drawLoopStart(pdc,pos=[thisInit,self.linePos[1]], downwards=True)
            self.drawLoopEnd(pdc,pos=[thisTerm,self.linePos[1]], downwards=True)
            if height>maxHeight: maxHeight=height

        self.SetVirtualSize(size=(currX+100, maxHeight+50))
        #draw all possible locations for routines DEPRECATED SINCE 1.62 because not drawing those
        #for n, xPos in enumerate(self.pointsToDraw):
        #   font.SetPointSize(600/self.dpi)
        #   self.SetFont(font); pdc.SetFont(font)
        #   w,h = self.GetFullTextExtent(str(len(self.pointsToDraw)))[0:2]
        #   pdc.SetPen(wx.Pen(wx.Color(0,0,0, 255)))
        #   pdc.SetBrush(wx.Brush(wx.Color(0,0,0,255)))
        #   pdc.DrawCircle(xPos,self.linePos[1], w+2)
        #   pdc.SetTextForeground([255,255,255])
        #   pdc.DrawText(str(n), xPos-w/2, self.linePos[1]-h/2)

        pdc.EndDrawing()
        self.Refresh()#refresh the visible window after drawing (using OnPaint)
    def drawEntryPoints(self, posList):
        for n, pos in enumerate(posList):
            if n>=len(self.entryPointPosList):
                #draw for first time
                id = wx.NewId()
                self.entryPointIDlist.append(id)
                self.pdc.SetId(id)
                self.pdc.SetBrush(wx.Brush(wx.Color(0,0,0,255)))
                self.pdc.DrawCircle(pos,self.linePos[1], 5)
                r = self.pdc.GetIdBounds(id)
                self.OffsetRect(r)
                self.RefreshRect(r, False)
            elif pos == self.entryPointPosList[n]:
                pass#nothing to see here, move along please :-)
            else:
                #move to new position
                dx = pos-self.entryPointPosList[n]
                dy = 0
                r = self.pdc.GetIdBounds(self.entryPointIDlist[n])
                self.pdc.TranslateId(self.entryPointIDlist[n], dx, dy)
                r2 = self.pdc.GetIdBounds(self.entryPointIDlist[n])
                rectToRedraw = r.Union(r2)#combine old and new locations to get redraw area
                rectToRedraw.Inflate(4,4)
                self.OffsetRect(rectToRedraw)
                self.RefreshRect(rectToRedraw, False)

        self.entryPointPosList=posList
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
    def drawLoopEnd(self, dc, pos, downwards=True):
        #draws a spot that a loop will later attach to
        tmpId = wx.NewId()
        dc.SetId(tmpId)
        dc.SetBrush(wx.Brush(wx.Color(0,0,0, 250)))
        dc.SetPen(wx.Pen(wx.Color(0,0,0, 255)))
        if downwards:
            dc.DrawPolygon([[5,0],[0,5],[-5,0]], pos[0],pos[1])#points down
        else:
            dc.DrawPolygon([[5,5],[0,0],[-5,5]], pos[0],pos[1]-5)#points up
        dc.SetIdBounds(tmpId,wx.Rect(pos[0]-5,pos[1]-5,10,10))
    def drawLoopStart(self, dc, pos, downwards=True):
        #draws a spot that a loop will later attach to
        tmpId = wx.NewId()
        dc.SetId(tmpId)
        dc.SetBrush(wx.Brush(wx.Color(0,0,0, 250)))
        dc.SetPen(wx.Pen(wx.Color(0,0,0, 255)))
        if downwards:
            dc.DrawPolygon([[5,5],[0,0],[-5,5]], pos[0],pos[1])#points up
        else:
            dc.DrawPolygon([[5,0],[0,5],[-5,0]], pos[0],pos[1]-5)#points down
        dc.SetIdBounds(tmpId,wx.Rect(pos[0]-5,pos[1]-5,10,10))
    def drawFlowRoutine(self,dc,routine,id, rgb=[200,50,50],pos=[0,0]):
        """Draw a box to show a routine on the timeline
        """
        name=routine.name
        dc.SetId(id)
        font = self.GetFont()
        if sys.platform=='darwin':
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
        dc.SetPen(wx.Pen(wx.Color(r, g, b, wx.ALPHA_OPAQUE)))
        #for the fill, draw once in white near-opaque, then in transp color
        dc.SetBrush(wx.Brush(wx.Color(r,g*3,b*3,255)))
        dc.DrawRoundedRectangleRect(rect, 8)
        #draw text
        dc.SetTextForeground(rgb)
        dc.DrawText(name, pos[0]+pad/2, pos[1]+pad/2)

        self.componentFromID[id]=routine
        #set the area for this component
        dc.SetIdBounds(id,rect)

        return endX
#        tbtn = AB.AquaButton(self, id, pos=pos, label=name)
#        tbtn.Bind(wx.EVT_BUTTON, self.onBtn)
#        print tbtn.GetBackgroundColour()

#        print dir(tbtn)
#        print tbtn.GetRect()
#        rect = tbtn.GetRect()
#        return rect[0]+rect[2]+20
#    def onBtn(self, event):
#        print 'evt:', self.componentFromID[event.GetId()].name
#        print '\nobj:', dir(event.GetEventObject())
    def drawLoop(self,dc,name,loop,id,
            startX,endX,
            base,height,rgb=[0,0,0], downwards=True):
        if downwards: up=-1
        else: up=+1

        #draw loop itself
        tmpId = wx.NewId()
        dc.SetId(tmpId)
        curve=10 #extra distance, in both h and w caused by curve
        xx = [endX,  endX,   endX,   endX-curve/2, endX-curve, startX+curve,startX+curve/2, startX, startX, startX]
        yy = [base,height+curve*up,height+curve*up/2,height, height, height,  height,  height+curve*up/2, height+curve*up, base]
        pts=[]
        r,g,b=rgb
        pad=8
        dc.SetPen(wx.Pen(wx.Color(r, g, b, 200)))
        for n in range(len(xx)):
            pts.append([xx[n],yy[n]])
        dc.DrawSpline(pts)
        area = wx.Rect(min(xx), min(yy), max(xx)-min(xx), max(yy)-min(yy))
        dc.SetIdBounds(tmpId, area)

        #add a name label that can be clicked on
        if self.frame.app.prefs.builder['showLoopInfoInFlow']:
            name += ': '+str(loop.params['nReps'].val)+'x, '+str(loop.params['loopType'].val)
        dc.SetId(id)
        font = self.GetFont()
        if sys.platform=='darwin':
            font.SetPointSize(800/self.dpi)
        else:
            font.SetPointSize(800/self.dpi)
        self.SetFont(font); dc.SetFont(font)
        #get size based on text
        w,h = self.GetFullTextExtent(name)[0:2]
        x = startX+(endX-startX)/2-w/2
        y = (height-h/2)

        #draw box
        rect = wx.Rect(x, y, w+pad,h+pad)
        #the edge should match the text
        dc.SetPen(wx.Pen(wx.Color(r, g, b, 100)))
        #for the fill, draw once in white near-opaque, then in transp color
        dc.SetBrush(wx.Brush(wx.Color(canvasColor[0],canvasColor[1],canvasColor[2],250)))
        dc.DrawRoundedRectangleRect(rect, 8)
        #draw text
        dc.SetTextForeground([r,g,b])
        dc.DrawText(name, x+pad/2, y+pad/2)

        self.componentFromID[id]=loop
        #set the area for this component
        dc.SetIdBounds(id,rect)

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

        self.SetVirtualSize((self.maxWidth, self.maxHeight))
        self.SetScrollRate(self.dpi/4,self.dpi/4)

        self.routine=routine
        self.yPositions=None
        self.yPosTop=60
        self.componentStep=50#the step in Y between each component
        self.iconXpos = 100 #the left hand edge of the icons
        self.timeXposStart = 200
        self.timeXposEnd = 600

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
        self.Bind(wx.EVT_SIZE, self.onResize)
        self.SetDropTarget(FileDropTarget(builder = self.frame))

    def onResize(self, event):
        self.sizePix=event.GetSize()
        self.timeXposStart = 200
        self.timeXposEnd = self.sizePix[0]-100
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
            self.frame.exp.namespace.remove(component.params['name'].val)
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

        #work out where the component names and icons should be from name lengths
        self.setFontSize(1000/self.dpi, self.pdc)
        longest=0; w=50
        for comp in self.routine:
            name = comp.params['name'].val
            if len(name)>longest:
                longest=len(name)
                w = self.GetFullTextExtent(name)[0]
        self.iconXpos = w+50
        self.timeXpos = w+90

        #draw timeline at bottom of page
        yPosBottom = self.yPosTop+len(self.routine)*self.componentStep
        self.drawTimeGrid(self.pdc,self.yPosTop,yPosBottom)
        yPos = self.yPosTop

        for n, component in enumerate(self.routine):
            self.drawComponent(self.pdc, component, yPos)
            yPos+=self.componentStep

        self.SetVirtualSize((self.maxWidth, yPos+50))#the 50 allows space for labels below the time axis
        self.pdc.EndDrawing()
        self.Refresh()#refresh the visible window after drawing (using OnPaint)

    def drawTimeGrid(self, dc, yPosTop, yPosBottom, labelAbove=True):
        """Draws the grid of lines and labels the time axes
        """
        tMax=self.getMaxTime()*1.1
        xScale = self.getSecsPerPixel()
        xSt=self.timeXposStart
        xEnd=self.timeXposEnd
        dc.SetPen(wx.Pen(wx.Color(0, 0, 0, 150)))
        #draw horizontal lines on top and bottom
        dc.DrawLine(x1=xSt,y1=yPosTop,
                    x2=xEnd,y2=yPosTop)
        dc.DrawLine(x1=xSt,y1=yPosBottom,
                    x2=xEnd,y2=yPosBottom)
        #draw vertical time points
        unitSize = 10**numpy.ceil(numpy.log10(tMax*0.8))/10.0#gives roughly 1/10 the width, but in rounded to base 10 of 0.1,1,10...
        if tMax/unitSize<3: unitSize = 10**numpy.ceil(numpy.log10(tMax*0.8))/50.0#gives units of 2 (0.2,2,20)
        elif tMax/unitSize<6: unitSize = 10**numpy.ceil(numpy.log10(tMax*0.8))/20.0#gives units of 5 (0.5,5,50)
        for lineN in range(int(numpy.floor(tMax/unitSize))):
            dc.DrawLine(xSt+lineN*unitSize/xScale, yPosTop-4,#vertical line
                    xSt+lineN*unitSize/xScale, yPosBottom+4)
            dc.DrawText('%.2g' %(lineN*unitSize),xSt+lineN*unitSize/xScale,yPosTop-20)#label above
            if yPosBottom>300:#if bottom of grid is far away then draw labels here too
                dc.DrawText('%.2g' %(lineN*unitSize),xSt+lineN*unitSize/xScale,yPosBottom+10)#label below
        #add a label
        self.setFontSize(1000/self.dpi, dc)
        dc.DrawText('t (sec)',xEnd+5,yPosTop-self.GetFullTextExtent('t')[1]/2.0)#y is y-half height of text
        if yPosBottom>300:#if bottom of grid is far away then draw labels here too
            dc.DrawText('t (sec)',xEnd+5,yPosBottom-self.GetFullTextExtent('t')[1]/2.0)#y is y-half height of text
    def setFontSize(self, size, dc):
        font = self.GetFont()
        font.SetPointSize(size)
        dc.SetFont(font)
    def drawComponent(self, dc, component, yPos):
        """Draw the timing of one component on the timeline"""

        #set an id for the region of this comonent (so it can act as a button)
        ##see if we created this already
        id=None
        for key in self.componentFromID.keys():
            if self.componentFromID[key]==component:
                id=key
        if not id: #then create one and add to the dict
            id = wx.NewId()
            self.componentFromID[id]=component
        dc.SetId(id)

        thisIcon = components.icons[component.getType()][0]#index 0 is main icon
        dc.DrawBitmap(thisIcon, self.iconXpos,yPos, True)
        fullRect = wx.Rect(self.iconXpos, yPos, thisIcon.GetWidth(),thisIcon.GetHeight())

        self.setFontSize(1000/self.dpi, dc)

        name = component.params['name'].val
        #get size based on text
        w,h = self.GetFullTextExtent(name)[0:2]
        #draw text
        x = self.iconXpos-self.dpi/10-w
        y = yPos+thisIcon.GetHeight()/2-h/2
        dc.DrawText(name, x-20, y)
        fullRect.Union(wx.Rect(x-20,y,w,h))

        #draw entries on timeline (if they have some time definition)
        if 'startType' in component.params.keys():
            startType=component.params['startType'].val
            stopType=component.params['stopType'].val

            #deduce a start time (s) if possible
            if startType=='time (s)' and canBeNumeric(component.params['startVal'].val):
                startTime=float(component.params['startVal'].val)
            #user has given a time estimate
            elif canBeNumeric(component.params['startEstim'].val):
                startTime=float(component.params['startEstim'].val)
            else: startTime=None

            #deduce duration (s) if possible. Duration used because box needs width
            if component.params['stopVal'].val in ['','-1','None']:
                duration=inf#infinite duration
            elif stopType=='time (s)' and canBeNumeric(component.params['stopVal'].val):
                duration=float(component.params['stopVal'].val)-startTime
            elif stopType=='duration (s)' and canBeNumeric(component.params['stopVal'].val):
                duration=float(component.params['stopVal'].val)
            elif canBeNumeric(component.params['durationEstim'].val):
                duration=float(component.params['durationEstim'].val)
            else:
                duration=None

            if startTime!=None and duration!=None:#then we can draw a sensible time bar!
                xScale = self.getSecsPerPixel()
                dc.SetPen(wx.Pen(wx.Color(200, 100, 100, 0)))
                dc.SetBrush(wx.Brush(wx.Color(200,100,100, 200)))
                h = self.componentStep/2
                xSt = self.timeXposStart + startTime/xScale
                w = duration/xScale
                if w>10000: w=10000#limit width to 10000 pixels!
                if w<2: w=2#make sure at least one pixel shows
                dc.DrawRectangle(xSt, y, w,h )
                fullRect.Union(wx.Rect(xSt, y, w,h ))#update bounds to include time bar
        dc.SetIdBounds(id,fullRect)

    def editComponentProperties(self, event=None, component=None):
        if event:#we got here from a wx.button press (rather than our own drawn icons)
            componentName=event.EventObject.GetName()
            component=self.routine.getComponentFromName(componentName)
        #does this component have a help page?
        if hasattr(component, 'url'):helpUrl=component.url
        else:helpUrl=None
        old_name = component.params['name'].val
        #create the dialog
        dlg = DlgComponentProperties(frame=self.frame,
            title=component.params['name'].val+' Properties',
            params = component.params,
            order = component.order,
            helpUrl=helpUrl, editing=True)
        if dlg.OK:
            self.redrawRoutine()#need to refresh timings section
            self.Refresh()#then redraw visible
            self.frame.exp.namespace.remove(old_name)
            self.frame.exp.namespace.add(component.params['name'].val)
            self.frame.addToUndoStack("edit %s" %component.params['name'])

    def getSecsPerPixel(self):
        return float(self.getMaxTime())/(self.timeXposEnd-self.timeXposStart)
    def getMaxTime(self):
        """What the last (predetermined) stimulus time to be presented. If
        there are no components or they have code-based times then will default
        to 10secs
        """
        maxTime=0
        for n, component in enumerate(self.routine):
            try:exec('thisT=%(startTime)s+%(duration)s' %component.params)
            except:thisT=0
            maxTime=max(maxTime,thisT)
        if maxTime==0:#if there are no components
            maxTime=10
        return maxTime
class RoutinesNotebook(wx.aui.AuiNotebook):
    """A notebook that stores one or more routines
    """
    def __init__(self, frame, id=-1):
        self.frame=frame
        self.app=frame.app
        self.dpi=self.app.dpi
        wx.aui.AuiNotebook.__init__(self, frame, id)

        self.Bind(wx.aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.onClosePane)
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
    def createNewRoutine(self):
        dlg = wx.TextEntryDialog(self, message="What is the name for the new Routine? (e.g. instr, trial, feedback)",
            caption='New Routine')
        exp = self.frame.exp
        if dlg.ShowModal() == wx.ID_OK:
            routineName=dlg.GetValue()
            # silently auto-adjust the name to be valid, and register in the namespace:
            routineName = exp.namespace.make_valid(routineName, prefix='routine')
            exp.namespace.add(routineName) #add to the namespace
            exp.addRoutine(routineName)#add to the experiment
            self.addRoutinePage(routineName, exp.routines[routineName])#then to the notebook
            self.frame.addToUndoStack("created %s routine" %routineName)
        dlg.Destroy()
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
        self.frame.addToUndoStack("remove routine %s" %(name))
    def redrawRoutines(self):
        """Removes all the routines, adds them back and sets current back to orig
        """
        currPage = self.GetSelection()
        self.removePages()
        for routineName in self.frame.exp.routines:
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
        scrolledpanel.ScrolledPanel.__init__(self,frame,id,size=(1.1*self.dpi,10*self.dpi))
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
            if thisName in components.tooltips:
                thisTip = components.tooltips[thisName]
            else:
                thisTip = shortName
            btn.SetToolTip(wx.ToolTip(thisTip))
            self.componentFromID[btn.GetId()]=thisName
            self.Bind(wx.EVT_BUTTON, self.onComponentAdd,btn)
            self.sizer.Add(btn, 0,wx.EXPAND|wx.ALIGN_CENTER )
            self.componentButtons[thisName]=btn#store it for elsewhere

        self.SetSizer(self.sizer)
        self.SetAutoLayout(1)
        self.SetupScrolling()
        self.SetDropTarget(FileDropTarget(builder = self.frame))

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
        #does this component have a help page?
        if hasattr(newComp, 'url'):helpUrl=newComp.url
        else:
            helpUrl=None
        #create component template
        dlg = DlgComponentProperties(frame=self.frame,
            title=componentName+' Properties',
            params = newComp.params,
            order = newComp.order,
            helpUrl=helpUrl)

        compName = newComp.params['name']
        if dlg.OK:
            currRoutine.addComponent(newComp)#add to the actual routing
            namespace = self.frame.exp.namespace
            newComp.params['name'].val = namespace.make_valid(newComp.params['name'].val)
            namespace.add(newComp.params['name'].val)
            currRoutinePage.redrawRoutine()#update the routine's view with the new component too
#            currRoutinePage.Refresh()#done at the end of redrawRoutine
            self.frame.addToUndoStack("added %s to %s" %(compName, currRoutine.name))
        return True
class ParamCtrls:
    def __init__(self, dlg, label, param, browse=False, noCtrls=False, advanced=False):
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
        if advanced: parent=self.dlg.advPanel.GetPane()
        else: parent=self.dlg
        #param has the fields:
        #val, valType, allowedVals=[],allowedTypes=[], hint="", updates=None, allowedUpdates=None
        # we need the following
        self.nameCtrl = self.valueCtrl = self.typeCtrl = self.updateCtrl = None
        self.browseCtrl = None
        if noCtrls: return#we don't need to do any more

        if type(param.val)==numpy.ndarray:
            initial=initial.tolist() #convert numpy arrays to lists
        labelLength = wx.Size(self.dpi*2,self.dpi/3)#was 8*until v0.91.4
        self.nameCtrl = wx.StaticText(parent,-1,label,size=labelLength,
                                        style=wx.ALIGN_RIGHT)

        if label in ['text', 'customize_everything']:
            #for text input we need a bigger (multiline) box
            self.valueCtrl = wx.TextCtrl(parent,-1,unicode(param.val),
                style=wx.TE_MULTILINE,
                size=wx.Size(self.valueWidth,-1))
            if label == 'text':
                self.valueCtrl.SetFocus()
            #expando seems like a nice idea - but probs with pasting in text and with resizing
            #self.valueCtrl = ExpandoTextCtrl(parent,-1,str(param.val),
            #    style=wx.TE_MULTILINE,
            #    size=wx.Size(500,-1))
            #self.valueCtrl.SetMaxHeight(500)

        elif label in ['Begin Experiment', 'Begin Routine', 'Each Frame', 'End Routine', 'End Experiment']:
            #code input fields one day change these to wx.stc fields?
            self.valueCtrl = wx.TextCtrl(parent,-1,unicode(param.val),
                style=wx.TE_MULTILINE,
                size=wx.Size(self.valueWidth,-1))
        elif param.valType=='bool':
            #only True or False - use a checkbox
             self.valueCtrl = wx.CheckBox(parent, size = wx.Size(self.valueWidth,-1))
             self.valueCtrl.SetValue(param.val)
        elif len(param.allowedVals)>1:
            #there are limitted options - use a Choice control
            self.valueCtrl = wx.Choice(parent, choices=param.allowedVals, size=wx.Size(self.valueWidth,-1))
            self.valueCtrl.SetStringSelection(unicode(param.val))
        else:
            #create the full set of ctrls
            self.valueCtrl = wx.TextCtrl(parent,-1,unicode(param.val),
                        size=wx.Size(self.valueWidth,-1))
            if label in ['allowedKeys', 'image', 'movie', 'scaleDescription', 'sound', 'Begin Routine']:
                self.valueCtrl.SetFocus()
        self.valueCtrl.SetToolTipString(param.hint)

        #create the type control
        if len(param.allowedTypes)==0:
            pass
        else:
            self.typeCtrl = wx.Choice(parent, choices=param.allowedTypes)
            self.typeCtrl.SetStringSelection(param.valType)
        if len(param.allowedTypes)==1:
            self.typeCtrl.Disable()#visible but can't be changed

        #create update control
        if param.allowedUpdates==None or len(param.allowedUpdates)==0:
            pass
        else:
            self.updateCtrl = wx.Choice(parent, choices=param.allowedUpdates)
            self.updateCtrl.SetStringSelection(param.updates)
        if param.allowedUpdates!=None and len(param.allowedUpdates)==1:
            self.updateCtrl.Disable()#visible but can't be changed
        #create browse control
        if browse:
            self.browseCtrl = wx.Button(parent, -1, "Browse...") #we don't need a label for this
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
    def setVisible(self, newVal=True):
        self.valueCtrl.Show(newVal)
        self.nameCtrl.Show(newVal)
        if self.updateCtrl: self.updateCtrl.Show(newVal)
        if self.typeCtrl: self.typeCtrl.Show(newVal)

class _BaseParamsDlg(wx.Dialog):
    def __init__(self,frame,title,params,order,
            helpUrl=None, suppressTitles=True,
            showAdvanced=False,
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.TAB_TRAVERSAL,editing=False):
        wx.Dialog.__init__(self, frame,-1,title,pos,size,style)
        self.frame=frame
        self.app=frame.app
        self.dpi=self.app.dpi
        self.helpUrl=helpUrl
        self.Center()
        self.panel = wx.Panel(self, -1)
        self.params=params   #dict
        self.title = title
        if not editing and title != 'Experiment Settings':
            # then we're adding a new component, so provide a known-valid name:
            self.params['name'].val = self.frame.exp.namespace.make_valid(params['name'].val)
        self.paramCtrls={}
        self.showAdvanced=showAdvanced
        self.order=order
        self.data = []
        self.ctrlSizer= wx.GridBagSizer(vgap=2,hgap=2)
        self.ctrlSizer.AddGrowableCol(1)#valueCtrl column
        self.currRow = 0
        self.advCtrlSizer= wx.GridBagSizer(vgap=2,hgap=2)
        self.advCurrRow = 0
        self.nameOKlabel=None
        self.maxFieldLength = 10#max( len(str(self.params[x])) for x in keys )
        types=dict([])
        self.useUpdates=False#does the dlg need an 'updates' row (do any params use it?)
        self.timeParams=['startType','startVal','stopType','stopVal']

        #create a header row of titles
        if not suppressTitles:
            size=wx.Size(1.5*self.dpi,-1)
            self.ctrlSizer.Add(wx.StaticText(self,-1,'Parameter',size=size, style=wx.ALIGN_CENTER),(self.currRow,0))
            self.ctrlSizer.Add(wx.StaticText(self,-1,'Value',size=size, style=wx.ALIGN_CENTER),(self.currRow,1))
            #self.sizer.Add(wx.StaticText(self,-1,'Value Type',size=size, style=wx.ALIGN_CENTER),(self.currRow,3))
            self.ctrlSizer.Add(wx.StaticText(self,-1,'Updates',size=size, style=wx.ALIGN_CENTER),(self.currRow,2))
            self.currRow+=1
            self.ctrlSizer.Add(
                wx.StaticLine(self, size=wx.Size(100,20)),
                (self.currRow,0),(1,2), wx.ALIGN_CENTER|wx.EXPAND)
        self.currRow+=1

        #get all params and sort
        remaining = sorted(self.params.keys())
        #check for advanced params
        if 'advancedParams' in self.params.keys():
            self.advParams=self.params['advancedParams']
            remaining.remove('advancedParams')
        else:self.advParams=[]

        #start with the name (always)
        if 'name' in remaining:
            self.addParam('name')
            remaining.remove('name')
            if 'name' in self.order:
                self.order.remove('name')
#            self.currRow+=1
        #add start/stop info
        if 'startType' in remaining:
            remaining = self.addStartStopCtrls(remaining=remaining)
            #self.ctrlSizer.Add(
            #    wx.StaticLine(self, size=wx.Size(100,10)),
            #    (self.currRow,0),(1,3), wx.ALIGN_CENTER|wx.EXPAND)
            self.currRow+=1#an extra row to create space (staticLine didn't look right)
        #loop through the prescribed order (the most important?)
        for fieldName in self.order:
            if fieldName in self.advParams:continue#skip advanced params
            self.addParam(fieldName)
            remaining.remove(fieldName)
        #add any params that weren't specified in the order
        for fieldName in remaining:
            if fieldName not in self.advParams:
                self.addParam(fieldName)
        #add advanced params if needed
        if len(self.advParams)>0:
            self.addAdvancedTab()
            for fieldName in self.advParams:
                self.addParam(fieldName, advanced=True)

        # contextual menu:
        self.contextMenuItems=['color picker']
        self.contextItemFromID={}; self.contextIDFromItem={}
        for item in self.contextMenuItems:
            id = wx.NewId()
            self.contextItemFromID[id] = item
            self.contextIDFromItem[item] = id
    def addStartStopCtrls(self,remaining):
        """Add controls for startType, startVal, stopType, stopVal
        remaining refers to
        """
        sizer=self.ctrlSizer
        parent=self
        currRow = self.currRow

        ##Start point
        startTypeParam = self.params['startType']
        startValParam = self.params['startVal']
        #create label
        label = wx.StaticText(self,-1,'start', style=wx.ALIGN_CENTER)
        labelEstim = wx.StaticText(self,-1,'expected start (s)', style=wx.ALIGN_CENTER)
        labelEstim.SetForegroundColour('gray')
        #the method to be used to interpret this start/stop
        self.startTypeCtrl = wx.Choice(parent, choices=startTypeParam.allowedVals)
        self.startTypeCtrl.SetStringSelection(startTypeParam.val)
        #the value to be used as the start/stop
        self.startValCtrl = wx.TextCtrl(parent,-1,unicode(startValParam.val))
        self.startValCtrl.SetToolTipString(self.params['startVal'].hint)
        #the value to estimate start/stop if not numeric
        self.startEstimCtrl = wx.TextCtrl(parent,-1,unicode(self.params['startEstim'].val))
        self.startEstimCtrl.SetToolTipString(self.params['startEstim'].hint)
        #add the controls to a new line
        startSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        startSizer.Add(self.startTypeCtrl)
        startSizer.Add(self.startValCtrl, 1,flag=wx.EXPAND)
        startEstimSizer=wx.BoxSizer(orient=wx.HORIZONTAL)
        startEstimSizer.Add(labelEstim)
        startEstimSizer.Add(self.startEstimCtrl)
        startAllCrtlSizer = wx.BoxSizer(orient=wx.VERTICAL)
        startAllCrtlSizer.Add(startSizer,flag=wx.EXPAND)
        startAllCrtlSizer.Add(startEstimSizer, flag=wx.ALIGN_RIGHT)
        self.ctrlSizer.Add(label, (self.currRow,0),(1,1),wx.ALIGN_RIGHT)
        #add our new row
        self.ctrlSizer.Add(startAllCrtlSizer,(self.currRow,1),(1,1),flag=wx.EXPAND)
        self.currRow+=1
        remaining.remove('startType')
        remaining.remove('startVal')
        remaining.remove('startEstim')

        ##Stop point
        stopTypeParam = self.params['stopType']
        stopValParam = self.params['stopVal']
        #create label
        label = wx.StaticText(self,-1,'stop', style=wx.ALIGN_CENTER)
        labelEstim = wx.StaticText(self,-1,'expected duration (s)', style=wx.ALIGN_CENTER)
        labelEstim.SetForegroundColour('gray')
        #the method to be used to interpret this start/stop
        self.stopTypeCtrl = wx.Choice(parent, choices=stopTypeParam.allowedVals)
        self.stopTypeCtrl.SetStringSelection(stopTypeParam.val)
        #the value to be used as the start/stop
        self.stopValCtrl = wx.TextCtrl(parent,-1,unicode(stopValParam.val))
        self.stopValCtrl.SetToolTipString(self.params['stopVal'].hint)
        #the value to estimate start/stop if not numeric
        self.durationEstimCtrl = wx.TextCtrl(parent,-1,unicode(self.params['durationEstim'].val))
        self.durationEstimCtrl.SetToolTipString(self.params['durationEstim'].hint)
        #add the controls to a new line
        stopSizer = wx.BoxSizer(orient=wx.HORIZONTAL)
        stopSizer.Add(self.stopTypeCtrl)
        stopSizer.Add(self.stopValCtrl, 1,flag=wx.EXPAND)
        stopEstimSizer=wx.BoxSizer(orient=wx.HORIZONTAL)
        stopEstimSizer.Add(labelEstim)
        stopEstimSizer.Add(self.durationEstimCtrl)
        stopAllCrtlSizer = wx.BoxSizer(orient=wx.VERTICAL)
        stopAllCrtlSizer.Add(stopSizer,flag=wx.EXPAND)
        stopAllCrtlSizer.Add(stopEstimSizer, flag=wx.ALIGN_RIGHT)
        self.ctrlSizer.Add(label, (self.currRow,0),(1,1),wx.ALIGN_RIGHT)
        #add our new row
        self.ctrlSizer.Add(stopAllCrtlSizer,(self.currRow,1),(1,1),flag=wx.EXPAND)
        self.currRow+=1
        remaining.remove('stopType')
        remaining.remove('stopVal')
        remaining.remove('durationEstim')

        return remaining

    def addParam(self,fieldName, advanced=False):
        """Add a parameter to the basic sizer
        """
        if advanced:
            sizer=self.advCtrlSizer
            parent=self.advPanel.GetPane()
            currRow = self.advCurrRow
        else:
            sizer=self.ctrlSizer
            parent=self
            currRow = self.currRow
        param=self.params[fieldName]
        ctrls=ParamCtrls(dlg=self, label=fieldName,param=param, advanced=advanced)
        self.paramCtrls[fieldName] = ctrls
        if fieldName=='name':
            ctrls.valueCtrl.Bind(wx.EVT_TEXT, self.checkName)
        # self.valueCtrl = self.typeCtrl = self.updateCtrl
        sizer.Add(ctrls.nameCtrl, (currRow,0), (1,1),wx.ALIGN_RIGHT )
        sizer.Add(ctrls.valueCtrl, (currRow,1) , flag=wx.EXPAND)
        if ctrls.updateCtrl:
            sizer.Add(ctrls.updateCtrl, (currRow,2))
        if ctrls.typeCtrl:
            sizer.Add(ctrls.typeCtrl, (currRow,3) )
        if fieldName=='text':
            self.ctrlSizer.AddGrowableRow(currRow)#doesn't seem to work though
            #self.Bind(EVT_ETC_LAYOUT_NEEDED, self.onNewTextSize, ctrls.valueCtrl)
        if fieldName in ['color']: # eventually: 'fillColor', 'lineColor'
            ctrls.valueCtrl.Bind(wx.EVT_RIGHT_DOWN, self.onMouseRight)
        #increment row number
        if advanced: self.advCurrRow+=1
        else:self.currRow+=1
    def onMouseRight(self, event):
        # Apr 2011: so far, only the color field catches mouse events. the code below assumes
        # that is the case, but it would be more general to get the fieldName based on its position
            # -> get which self.paramCtrl[fieldName]
            # e.g., from Flow panel get which component:
            #component=self.componentFromID[self._menuComponentID]
        fieldName = 'color'
        x, y = self.ClientToScreen(event.GetPosition()) # panel's pos relative to its frame
        x2, y2 = self.frame.GetPosition() # frame's pos in whole window
        #x3, y3 magic numbers might be platform-specific; these work for me on mac 10.6 and ubuntu 10
        x3 = 80 # should be: width of left-most (label) column
        y3 = 0  # size of the normal params panel if fieldName is in the adv param panel
        if self.showAdvanced and fieldName in self.advParams:
            y3 = 18 * (1 + len(self.params) - len(self.advParams))
        self.paramCtrls[fieldName].valueCtrl.SetFocus() # later replace existing text with new color
        if self.title == 'Experiment Settings': # total kludge, but puts it in about the right spot
            y += 130 # I think its y that is not set right for Exp Settings window
        self.showContextMenu(-1, xy=wx.Point(x - x2 + x3, y - y2 + y3 + 85))
    def showContextMenu(self, component, xy):
        menu = wx.Menu()
        for item in self.contextMenuItems:
            id = self.contextIDFromItem[item]
            menu.Append( id, item )
            wx.EVT_MENU( menu, id, self.onContextSelect )
        self.frame.PopupMenu( menu, xy )
        menu.Destroy() # destroy to avoid mem leak
    def onContextSelect(self, event):
        """Perform a given action on the field chosen
        """
        op = self.contextItemFromID[event.GetId()]
        if op=='color picker':
            rgb = self.app.colorPicker(None) # str, remapped to -1..+1
            self.paramCtrls['color'].valueCtrl.Clear()
            self.paramCtrls['color'].valueCtrl.WriteText('$'+rgb) # $ flag as code
            ii = self.paramCtrls['colorSpace'].valueCtrl.FindString('rgb')
            self.paramCtrls['colorSpace'].valueCtrl.SetSelection(ii)
            # add to undo stack?
    def onNewTextSize(self, event):
        self.Fit()#for ExpandoTextCtrl this is needed

    def addText(self, text, size=None):
        if size==None:
            size = wx.Size(8*len(text)+16, 25)
        myTxt = wx.StaticText(self,-1,
                                label=text,
                                style=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL,
                                size=size)
        self.ctrlSizer.Add(myTxt,wx.EXPAND)#add to current row spanning entire
        return myTxt
    def addAdvancedTab(self):
        self.advPanel = wx.CollapsiblePane(self, label='Show Advanced')
        self.Bind(wx.EVT_COLLAPSIBLEPANE_CHANGED, self.onToggleAdvanced, self.advPanel)
        pane = self.advPanel.GetPane()
        pane.SetSizer(self.advCtrlSizer)
        self.advPanel.Collapse(not self.showAdvanced)
    def onToggleAdvanced(self, event=None):
        if self.advPanel.IsExpanded():
            self.advPanel.SetLabel('Hide Advanced')
            self.showAdvanced=True
        else:
            self.advPanel.SetLabel('Show Advanced')
            self.showAdvanced=False
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
        buttons = wx.StdDialogButtonSizer()
        #help button if we know the url
        if self.helpUrl!=None:
            helpBtn = wx.Button(self, wx.ID_HELP)
            helpBtn.SetHelpText("Get help about this component")
            helpBtn.Bind(wx.EVT_BUTTON, self.onHelp)
            buttons.Add(helpBtn, wx.ALIGN_LEFT|wx.ALL,border=3)
        self.OKbtn = wx.Button(self, wx.ID_OK, " OK ")
        self.OKbtn.SetDefault()
        self.checkName()
        buttons.Add(self.OKbtn, 0, wx.ALL,border=3)
        CANCEL = wx.Button(self, wx.ID_CANCEL, " Cancel ")
        buttons.Add(CANCEL, 0, wx.ALL,border=3)
        buttons.Realize()
        #put it all together
        self.mainSizer.Add(self.ctrlSizer,flag=wx.GROW)#add main controls
        if hasattr(self, 'advParams') and len(self.advParams)>0:#add advanced controls
            self.mainSizer.Add(self.advPanel,0,flag=wx.GROW|wx.ALL,border=5)
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
            if fieldName=='advancedParams':
                pass
            elif fieldName=='startType':
                param.val = self.startTypeCtrl.GetStringSelection()
            elif fieldName=='stopType':
                param.val = self.stopTypeCtrl.GetStringSelection()
            elif fieldName=='startVal':
                param.val = self.startValCtrl.GetValue()
            elif fieldName=='stopVal':
                param.val = self.stopValCtrl.GetValue()
            elif fieldName=='startEstim':
                param.val = self.startEstimCtrl.GetValue()
            elif fieldName=='durationEstim':
                param.val = self.durationEstimCtrl.GetValue()
            else:
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
            namespace = self.frame.exp.namespace
            used = namespace.exists(newName)
            same_as_old_name = bool(newName == self.params['name'].val)
            if used and not same_as_old_name:
                self.nameOKlabel.SetLabel("Name is already used by a %s" % used)
                self.OKbtn.Disable()
            elif not namespace.is_valid(newName): # as var name:
                self.nameOKlabel.SetLabel("Name must be alpha-numeric or _, no spaces")
                self.OKbtn.Disable()
            elif namespace.is_possibly_derivable(newName): # warn but allow, chances are good that its actually ok
                self.OKbtn.Enable()
                self.nameOKlabel.SetLabel("safer to avoid this, these, continue, or Clock in name")
            else:
                self.OKbtn.Enable()
                self.nameOKlabel.SetLabel("")
    def onHelp(self, event=None):
        """Uses self.app.followLink() to self.helpUrl
        """
        self.app.followLink(url=self.helpUrl)

class DlgLoopProperties(_BaseParamsDlg):
    def __init__(self,frame,title="Loop properties",loop=None,
            helpUrl=None,
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.RESIZE_BORDER):
        wx.Dialog.__init__(self, frame,-1,title,pos,size,style)
        self.helpUrl=helpUrl
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
        self.multiStairCtrls={}
        self.currentCtrls={}
        self.data = []
        self.ctrlSizer= wx.BoxSizer(wx.VERTICAL)
        self.trialList=None
        self.trialListFile=None

        #create a valid new name; save old name in case we need to revert
        default_name = 'trials'
        old_name = default_name
        if loop:
            old_name = loop.params['name'].val
        namespace = frame.exp.namespace
        new_name = namespace.make_valid(old_name)
        #create default instances of the diff loop types
        self.trialHandler=experiment.TrialHandler(exp=self.exp, name=new_name,
            loopType='random',nReps=5,trialList=[]) #for 'random','sequential'
        self.stairHandler=experiment.StairHandler(exp=self.exp, name=new_name,
            nReps=50, nReversals='',
            stepSizes='[0.8,0.8,0.4,0.4,0.2]', stepType='log', startVal=0.5) #for staircases
        self.multiStairHandler=experiment.MultiStairHandler(exp=self.exp, name=new_name,
            nReps=50, stairType='simple', switchStairs='random',
            conditions=[], conditionsFile='')
        #replace defaults with the loop we were given
        if loop==None:
            self.currentType='random'
            self.currentHandler=self.trialHandler
        elif loop.type=='TrialHandler':
            self.trialList=loop.params['trialList'].val
            self.trialListFile=loop.params['trialListFile'].val
            self.trialHandler = self.currentHandler = loop
            self.currentType=loop.params['loopType']#could be 'random' or 'sequential'
        elif loop.type=='StairHandler':
            self.stairHandler = self.currentHandler = loop
            self.currentType='staircase'
        elif loop.type=='MultiStairHandler':
            self.multiStairHandler = self.currentHandler = loop
            self.currentType='interleaved staircase'
        elif loop.type=='QuestHandler':
            pass # what to do for quest?
        self.params['name']=self.currentHandler.params['name']

        self.makeGlobalCtrls()
        self.makeStaircaseCtrls()
        self.makeConstantsCtrls()#the controls for Method of Constants
        self.makeMultiStairCtrls()
        self.setCtrls(self.currentType)

        #show dialog and get most of the data
        self.show()
        if self.OK:
            self.params = self.getParams()
            #convert endPoints from str to list
            exec("self.params['endPoints'].val = %s" %self.params['endPoints'].val)
            #then sort the list so the endpoints are in correct order
            self.params['endPoints'].val.sort()
            if loop:
                namespace.remove(old_name)
            namespace.add(self.params['name'].val)
        else:
            if loop!=None:#if we had a loop during init then revert to its old name
                loop.params['name'].val = old_name

        #make sure we set this back regardless of whether OK
        #otherwise it will be left as a summary string, not a trialList
        if self.currentHandler.params.has_key('trialListFile'):
            self.currentHandler.params['trialList'].val=self.trialList

    def makeGlobalCtrls(self):
        for fieldName in ['name','loopType']:
            container=wx.BoxSizer(wx.HORIZONTAL)#to put them in
            self.globalCtrls[fieldName] = ctrls = ParamCtrls(self, fieldName,
                self.currentHandler.params[fieldName])
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
            if fieldName=='endPoints':continue#this was deprecated in v1.62.00
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
                    text = """No parameters set (select a file above)"""
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

    def makeMultiStairCtrls(self):
        #a list of controls for the random/sequential versions
        #that can be hidden or shown
        handler=self.multiStairHandler
        #loop through the params
        keys = handler.params.keys()
        #add trialList stuff to the *end*
        if 'conditions' in keys:
            keys.remove('conditions')
            keys.insert(-1,'conditions')
        if 'conditionsFile' in keys:
            keys.remove('conditionsFile')
            keys.insert(-1,'conditionsFile')
        #then step through them
        for fieldName in keys:
            if fieldName=='endPoints':continue#this was deprecated in v1.62.00
            if fieldName in self.globalCtrls.keys():
                #these have already been made and inserted into sizer
                ctrls=self.globalCtrls[fieldName]
            elif fieldName=='conditionsFile':
                container=wx.BoxSizer(wx.HORIZONTAL)
                ctrls=ParamCtrls(self, fieldName, handler.params[fieldName], browse=True)
                self.Bind(wx.EVT_BUTTON, self.onBrowseTrialsFile,ctrls.browseCtrl)
                container.AddMany((ctrls.nameCtrl, ctrls.valueCtrl, ctrls.browseCtrl))
                self.ctrlSizer.Add(container)
            elif fieldName=='conditions':
                if handler.params.has_key('conditions'):
                    text=self.getTrialsSummary(handler.params['conditions'].val)
                else:
                    text = """No parameters set (select a file above)"""
                ctrls = ParamCtrls(self, 'conditions',text,noCtrls=True)#we'll create our own widgets
                size = wx.Size(350, 50)
                ctrls.valueCtrl = self.addText(text, size)#NB this automatically adds to self.ctrlSizer
                #self.ctrlSizer.Add(ctrls.valueCtrl)
            else: #normal text entry field
                container=wx.BoxSizer(wx.HORIZONTAL)
                ctrls=ParamCtrls(self, fieldName, handler.params[fieldName])
                container.AddMany((ctrls.nameCtrl, ctrls.valueCtrl))
                self.ctrlSizer.Add(container)
            #store info about the field
            self.multiStairCtrls[fieldName] = ctrls
    def makeStaircaseCtrls(self):
        """Setup the controls for a StairHandler"""
        handler=self.stairHandler
        #loop through the params
        for fieldName in handler.params.keys():
            if fieldName=='endPoints':continue#this was deprecated in v1.62.00
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
            #get attr names (trialList[0].keys() inserts u'name' and u' is annoying for novice)
            paramStr = "["
            for param in trialList[0].keys():
                paramStr += (unicode(param)+', ')
            paramStr = paramStr[:-2]+"]"#remove final comma and add ]
            #generate summary info
            return '%i trial types, with %i parameters\n%s' \
                %(len(trialList),len(trialList[0]), paramStr)
        else:
            return "No parameters set"
    def setCtrls(self, ctrlType):
        #create a list of ctrls to hide
        toHide = self.currentCtrls.values()
        if len(toHide)==0:
            toHide.extend(self.staircaseCtrls.values())
            toHide.extend(self.multiStairCtrls.values())
            toHide.extend(self.constantsCtrls.values())
        #choose the ctrls to show/hide
        if ctrlType=='staircase':
            self.currentHandler = self.stairHandler
            toShow = self.staircaseCtrls
        elif ctrlType=='interleaved staircase':
            self.currentHandler = self.multiStairHandler
            toShow = self.multiStairCtrls
        else:
            self.currentHandler = self.trialHandler
            toShow = self.constantsCtrls
        #hide them
        for ctrls in toHide:
            if ctrls.nameCtrl: ctrls.nameCtrl.Hide()
            if ctrls.valueCtrl: ctrls.valueCtrl.Hide()
            if ctrls.browseCtrl: ctrls.browseCtrl.Hide()
        #show them
        for paramName in toShow.keys():
            ctrls=toShow[paramName]
            if ctrls.nameCtrl: ctrls.nameCtrl.Show()
            if ctrls.valueCtrl: ctrls.valueCtrl.Show()
            if ctrls.browseCtrl: ctrls.browseCtrl.Show()
        self.currentCtrls=toShow
        self.ctrlSizer.Layout()
        self.Fit()
        self.Refresh()
    def onTypeChanged(self, evt=None):
        newType = evt.GetString()
        if newType==self.currentType:
            return
        self.setCtrls(newType)
    def onBrowseTrialsFile(self, event):
        expFolder,expName = os.path.split(self.frame.filename)
        dlg = wx.FileDialog(
            self, message="Open file ...", style=wx.OPEN, defaultDir=expFolder,
            )
        if dlg.ShowModal() == wx.ID_OK:
            newPath = _relpath(dlg.GetPath(), expFolder)
            self.trialListFile = newPath
            try:
                self.trialList, fieldNames = data.importTrialList(dlg.GetPath(), returnFieldNames=True)
            except ImportError, msg:
                self.constantsCtrls['trialList'].setValue(
                    'Bad condition name(s) in file:\n'+str(msg).replace(':','\n')+
                    '.\n[Edit in the file, try again.]')
                self.trialListFile = self.trialList = ''
                log.error('Rejected bad condition name in trialList file: %s' % str(msg).split(':')[0])
                return

            badNames = ''
            if len(fieldNames):
                for fname in fieldNames:
                    if self.exp.namespace.exists(fname): # or not self.exp.namespace.is_valid(fname):
                        badNames += fname+' '
            if badNames:
                self.constantsCtrls['trialList'].setValue(
                    'Bad condition name(s) in file:\n'+badNames[:-1]+
                    '\n[Duplicate name(s). Edit file, try again.]')
                log.error('Rejected bad condition names in trialList file: %s' % badNames[:-1])
                self.trialListFile = self.trialList = ''
                return
            self.exp.namespace.add(fieldNames)

            if 'conditionsFile' in self.currentCtrls.keys():
                self.constantsCtrls['conditionsFile'].setValue(self.getAbbriev(newPath))
                self.constantsCtrls['conditions'].setValue(self.getTrialsSummary(self.trialList))
            else:
                self.constantsCtrls['trialListFile'].setValue(self.getAbbriev(newPath))
                self.constantsCtrls['trialList'].setValue(self.getTrialsSummary(self.trialList))
    def getParams(self):
        """Retrieves data and re-inserts it into the handler and returns those handler params
        """
        #get data from input fields
        for fieldName in self.currentHandler.params.keys():
            if fieldName=='endPoints':continue#this was deprecated in v1.62.00
            param=self.currentHandler.params[fieldName]
            if fieldName in ['trialListFile', 'conditionsFile']:
                param.val=self.trialListFile#not the value from ctrl - that was abbrieviated
            else:#most other fields
                ctrls = self.currentCtrls[fieldName]#the various dlg ctrls for this param
                param.val = ctrls.getValue()#from _baseParamsDlg (handles diff control types)
                if ctrls.typeCtrl: param.valType = ctrls.getType()
                if ctrls.updateCtrl: param.updates = ctrls.getUpdates()
        return self.currentHandler.params

class DlgComponentProperties(_BaseParamsDlg):
    def __init__(self,frame,title,params,order,
            helpUrl=None, suppressTitles=True,
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT,
            editing=False):
        style=style|wx.RESIZE_BORDER
        _BaseParamsDlg.__init__(self,frame,title,params,order,
                                helpUrl=helpUrl,
                                pos=pos,size=size,style=style,
                                editing=editing)
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
        """store correct has been checked/unchecked. Show or hide the correctAns field accordingly"""
        if self.paramCtrls['storeCorrect'].valueCtrl.GetValue():
            self.paramCtrls['correctAns'].valueCtrl.Show()
            self.paramCtrls['correctAns'].nameCtrl.Show()
            #self.paramCtrls['correctAns'].typeCtrl.Show()
            #self.paramCtrls['correctAns'].updateCtrl.Show()
        else:
            self.paramCtrls['correctAns'].valueCtrl.Hide()
            self.paramCtrls['correctAns'].nameCtrl.Hide()
            #self.paramCtrls['correctAns'].typeCtrl.Hide()
            #self.paramCtrls['correctAns'].updateCtrl.Hide()
        self.ctrlSizer.Layout()
        self.Fit()
        self.Refresh()

class DlgExperimentProperties(_BaseParamsDlg):
    def __init__(self,frame,title,params,order,suppressTitles=False,
            pos=wx.DefaultPosition, size=wx.DefaultSize,helpUrl=None,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT):
        style=style|wx.RESIZE_BORDER
        _BaseParamsDlg.__init__(self,frame,'Experiment Settings',params,order,
                                pos=pos,size=size,style=style,helpUrl=helpUrl)
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
        """store correct has been checked/unchecked. Show or hide the correctAns field accordingly"""
        if self.paramCtrls['Full-screen window'].valueCtrl.GetValue():
            #get screen size for requested display
            num_displays = wx.Display.GetCount()
            if int(self.paramCtrls['Screen'].valueCtrl.GetValue())>num_displays:
                log.error("User requested non-existent screen")
            else:
                screenN=int(self.paramCtrls['Screen'].valueCtrl.GetValue())-1
            size=list(wx.Display(screenN).GetGeometry()[2:])
            #set vals and disable changes
            self.paramCtrls['Window size (pixels)'].valueCtrl.SetValue(unicode(size))
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
        #add buttons for help, OK and Cancel
        self.mainSizer=wx.BoxSizer(wx.VERTICAL)
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        if self.helpUrl!=None:
            helpBtn = wx.Button(self, wx.ID_HELP)
            helpBtn.SetHelpText("Get help about this component")
            helpBtn.Bind(wx.EVT_BUTTON, self.onHelp)
            buttons.Add(helpBtn, 0, wx.ALIGN_RIGHT|wx.ALL,border=3)
        self.OKbtn = wx.Button(self, wx.ID_OK, " OK ")
        self.OKbtn.SetDefault()
        buttons.Add(self.OKbtn, 0, wx.ALIGN_RIGHT|wx.ALL,border=3)
        CANCEL = wx.Button(self, wx.ID_CANCEL, " Cancel ")
        buttons.Add(CANCEL, 0, wx.ALIGN_RIGHT|wx.ALL,border=3)

        self.mainSizer.Add(self.ctrlSizer)
        self.mainSizer.Add(buttons, flag=wx.ALIGN_RIGHT)
        self.SetSizerAndFit(self.mainSizer)
        #do show and process return
        retVal = self.ShowModal()
        if retVal== wx.ID_OK: self.OK=True
        else:  self.OK=False
        return wx.ID_OK

class BuilderFrame(wx.Frame):
    def __init__(self, parent, id=-1, title='PsychoPy (Experiment Builder)',
                 pos=wx.DefaultPosition, fileName=None,frameData=None,
                 style=wx.DEFAULT_FRAME_STYLE, app=None):

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
        wx.Frame.__init__(self, parent=parent, id=id, title=title,
                            pos=(int(self.frameData['winX']), int(self.frameData['winY'])),
                            size=(int(self.frameData['winW']),int(self.frameData['winH'])),
                            style=style)

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

        #
        self.stdoutOrig = sys.stdout
        self.stderrOrig = sys.stderr
        self.stdoutFrame=stdOutRich.StdOutFrame(parent=self, app=self.app, size=(700,300))

        #setup a default exp
        if fileName!=None and os.path.isfile(fileName):
            self.fileOpen(filename=fileName, closeCurrent=False)
        else:
            self.lastSavedCopy=None
            self.fileNew(closeCurrent=False)#don't try to close before opening

        #control the panes using aui manager
        self._mgr = wx.aui.AuiManager(self)
        if self.prefs['topFlow']:
            self._mgr.AddPane(self.flowPanel,
                              wx.aui.AuiPaneInfo().
                              Name("Flow").Caption("Flow").BestSize((8*self.dpi,2*self.dpi)).
                              RightDockable(True).LeftDockable(True).CloseButton(False).
                              Top())
            self._mgr.AddPane(self.componentButtons, wx.aui.AuiPaneInfo().
                              Name("Components").Caption("Components").
                              RightDockable(True).LeftDockable(True).CloseButton(False).
                              Left())
            self._mgr.AddPane(self.routinePanel, wx.aui.AuiPaneInfo().
                              Name("Routines").Caption("Routines").
                              CenterPane(). #'center panes' expand to fill space
                              CloseButton(False).MaximizeButton(True))
        else:
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

        if sys.platform=='win32' or sys.platform.startswith('linux') or float(wx.version()[:3]) >= 2.8:
            if self.appPrefs['largeIcons']: toolbarSize=32
            else: toolbarSize=16
        else:
            toolbarSize=32 #size 16 doesn't work on mac wx; does work with wx.version() == '2.8.7.1 (mac-unicode)'
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
        #colorpicker_bmp = wx.Bitmap(os.path.join(self.app.prefs.paths['resources'], 'color%i.png' %toolbarSize), wx.BITMAP_TYPE_PNG)

        ctrlKey = 'Ctrl+'  # show key-bindings in tool-tips in an OS-dependent way
        if sys.platform == 'darwin': ctrlKey = 'Cmd+'
        self.toolbar.AddSimpleTool(self.IDs.tbFileNew, new_bmp, ("New [%s]" %self.app.keys['new']).replace('Ctrl+', ctrlKey), "Create new python file")
        self.toolbar.Bind(wx.EVT_TOOL, self.app.newBuilderFrame, id=self.IDs.tbFileNew)
        self.toolbar.AddSimpleTool(self.IDs.tbFileOpen, open_bmp, ("Open [%s]" %self.app.keys['open']).replace('Ctrl+', ctrlKey), "Open an existing file")
        self.toolbar.Bind(wx.EVT_TOOL, self.fileOpen, id=self.IDs.tbFileOpen)
        self.toolbar.AddSimpleTool(self.IDs.tbFileSave, save_bmp, ("Save [%s]" %self.app.keys['save']).replace('Ctrl+', ctrlKey),  "Save current file")
        self.toolbar.EnableTool(self.IDs.tbFileSave, False)
        self.toolbar.Bind(wx.EVT_TOOL, self.fileSave, id=self.IDs.tbFileSave)
        self.toolbar.AddSimpleTool(self.IDs.tbFileSaveAs, saveAs_bmp, ("Save As... [%s]" %self.app.keys['saveAs']).replace('Ctrl+', ctrlKey), "Save current python file as...")
        self.toolbar.Bind(wx.EVT_TOOL, self.fileSaveAs, id=self.IDs.tbFileSaveAs)
        self.toolbar.AddSimpleTool(self.IDs.tbUndo, undo_bmp, ("Undo [%s]" %self.app.keys['undo']).replace('Ctrl+', ctrlKey), "Undo last action")
        self.toolbar.Bind(wx.EVT_TOOL, self.undo, id=self.IDs.tbUndo)
        self.toolbar.AddSimpleTool(self.IDs.tbRedo, redo_bmp, ("Redo [%s]" %self.app.keys['redo']).replace('Ctrl+', ctrlKey),  "Redo last action")
        self.toolbar.Bind(wx.EVT_TOOL, self.redo, id=self.IDs.tbRedo)
        self.toolbar.AddSeparator()
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(self.IDs.tbPreferences, preferences_bmp, "Preferences",  "Application preferences")
        self.toolbar.Bind(wx.EVT_TOOL, self.app.showPrefs, id=self.IDs.tbPreferences)
        self.toolbar.AddSimpleTool(self.IDs.tbMonitorCenter, monitors_bmp, "Monitor Center",  "Monitor settings and calibration")
        self.toolbar.Bind(wx.EVT_TOOL, self.app.openMonitorCenter, id=self.IDs.tbMonitorCenter)
        #self.toolbar.AddSimpleTool(self.IDs.tbColorPicker, colorpicker_bmp, "Color Picker",  "Color Picker")
        #self.toolbar.Bind(wx.EVT_TOOL, self.app.colorPicker, id=self.IDs.tbColorPicker)
        self.toolbar.AddSeparator()
        self.toolbar.AddSeparator()
        self.toolbar.AddSimpleTool(self.IDs.tbExpSettings, settings_bmp, "Experiment Settings",  "Settings for this exp")
        self.toolbar.Bind(wx.EVT_TOOL, self.setExperimentSettings, id=self.IDs.tbExpSettings)
        self.toolbar.AddSimpleTool(self.IDs.tbCompile, compile_bmp, ("Compile Script [%s]" %self.app.keys['compileScript']).replace('Ctrl+', ctrlKey),  "Compile to script")
        self.toolbar.Bind(wx.EVT_TOOL, self.compileScript, id=self.IDs.tbCompile)
        self.toolbar.AddSimpleTool(self.IDs.tbRun, run_bmp, ("Run [%s]" %self.app.keys['runScript']).replace('Ctrl+', ctrlKey),  "Run experiment")
        self.toolbar.Bind(wx.EVT_TOOL, self.runFile, id=self.IDs.tbRun)
        self.toolbar.AddSimpleTool(self.IDs.tbStop, stop_bmp, ("Stop [%s]" %self.app.keys['stopScript']).replace('Ctrl+', ctrlKey),  "Stop experiment")
        self.toolbar.Bind(wx.EVT_TOOL, self.stopFile, id=self.IDs.tbStop)
        self.toolbar.EnableTool(self.IDs.tbStop,False)
        self.toolbar.Realize()

    def makeMenus(self):
        #---Menus---#000000#FFFFFF--------------------------------------------------
        menuBar = wx.MenuBar()
        #---_file---#000000#FFFFFF--------------------------------------------------
        self.fileMenu = wx.Menu()
        menuBar.Append(self.fileMenu, '&File')

        #create a file history submenu
        self.fileHistory = wx.FileHistory(maxFiles=10)
        self.recentFilesMenu = wx.Menu()
        self.fileHistory.UseMenu(self.recentFilesMenu)
        for filename in self.appData['fileHistory']: self.fileHistory.AddFileToHistory(filename)
        self.Bind(
            wx.EVT_MENU_RANGE, self.OnFileHistory, id=wx.ID_FILE1, id2=wx.ID_FILE9
            )

        self.fileMenu.Append(wx.ID_NEW,     "&New\t%s" %self.app.keys['new'])
        self.fileMenu.Append(wx.ID_OPEN,    "&Open...\t%s" %self.app.keys['open'])
        self.fileMenu.AppendSubMenu(self.recentFilesMenu,"Open &Recent")
        self.fileMenu.Append(wx.ID_SAVE,    "&Save\t%s" %self.app.keys['save'])
        self.fileMenu.Append(wx.ID_SAVEAS,  "Save &as...\t%s" %self.app.keys['saveAs'])
        self.fileMenu.Append(wx.ID_CLOSE,   "&Close file\t%s" %self.app.keys['close'])
        wx.EVT_MENU(self, wx.ID_NEW,  self.app.newBuilderFrame)
        wx.EVT_MENU(self, wx.ID_OPEN,  self.fileOpen)
        wx.EVT_MENU(self, wx.ID_SAVE,  self.fileSave)
        self.fileMenu.Enable(wx.ID_SAVE, False)
        wx.EVT_MENU(self, wx.ID_SAVEAS,  self.fileSaveAs)
        wx.EVT_MENU(self, wx.ID_CLOSE,  self.closeFrame)
        item = self.fileMenu.Append(wx.ID_PREFERENCES, text = "&Preferences")
        self.Bind(wx.EVT_MENU, self.app.showPrefs, item)
        #-------------quit
        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(wx.ID_EXIT, "&Quit\t%s" %self.app.keys['quit'], "Terminate the program")
        wx.EVT_MENU(self, wx.ID_EXIT, self.quit)

        self.editMenu = wx.Menu()
        menuBar.Append(self.editMenu, '&Edit')
        self.editMenu.Append(wx.ID_UNDO, "Undo\t%s" %self.app.keys['undo'], "Undo last action", wx.ITEM_NORMAL)
        wx.EVT_MENU(self, wx.ID_UNDO,  self.undo)
        self.editMenu.Append(wx.ID_REDO, "Redo\t%s" %self.app.keys['redo'], "Redo last action", wx.ITEM_NORMAL)
        wx.EVT_MENU(self, wx.ID_REDO,  self.redo)

        #---_tools---#000000#FFFFFF--------------------------------------------------
        self.toolsMenu = wx.Menu()
        menuBar.Append(self.toolsMenu, '&Tools')
        self.toolsMenu.Append(self.IDs.monitorCenter, "Monitor Center", "To set information about your monitor")
        wx.EVT_MENU(self, self.IDs.monitorCenter,  self.app.openMonitorCenter)

        self.toolsMenu.Append(self.IDs.compileScript, "Compile\t%s" %self.app.keys['compileScript'], "Compile the exp to a script")
        wx.EVT_MENU(self, self.IDs.compileScript,  self.compileScript)
        self.toolsMenu.Append(self.IDs.runFile, "Run\t%s" %self.app.keys['runScript'], "Run the current script")
        wx.EVT_MENU(self, self.IDs.runFile,  self.runFile)
        self.toolsMenu.Append(self.IDs.stopFile, "Stop\t%s" %self.app.keys['stopScript'], "Abort the current script")
        wx.EVT_MENU(self, self.IDs.stopFile,  self.stopFile)

        self.toolsMenu.AppendSeparator()
        self.toolsMenu.Append(self.IDs.openUpdater, "PsychoPy updates...", "Update PsychoPy to the latest, or a specific, version")
        wx.EVT_MENU(self, self.IDs.openUpdater,  self.app.openUpdater)

        #---_view---#000000#FFFFFF--------------------------------------------------
        self.viewMenu = wx.Menu()
        menuBar.Append(self.viewMenu, '&View')
        self.viewMenu.Append(self.IDs.openCoderView, "&Open Coder view\t%s" %self.app.keys['switchToCoder'], "Open a new Coder view")
        wx.EVT_MENU(self, self.IDs.openCoderView,  self.app.showCoder)

        #---_experiment---#000000#FFFFFF--------------------------------------------------
        self.expMenu = wx.Menu()
        menuBar.Append(self.expMenu, '&Experiment')
        self.expMenu.Append(self.IDs.newRoutine, "&New Routine\t%s" %self.app.keys['newRoutine'], "Create a new routine (e.g. the trial definition)")
        wx.EVT_MENU(self, self.IDs.newRoutine,  self.addRoutine)
        self.expMenu.Append(self.IDs.copyRoutine, "&Copy Routine\t%s" %self.app.keys['copyRoutine'], "Copy the current routine so it can be used in another exp", wx.ITEM_NORMAL)
        wx.EVT_MENU(self, self.IDs.copyRoutine,  self.onCopyRoutine)
        self.expMenu.Append(self.IDs.pasteRoutine, "&Paste Routine\t%s" %self.app.keys['pasteRoutine'], "Paste the Routine into the current experiment", wx.ITEM_NORMAL)
        wx.EVT_MENU(self, self.IDs.pasteRoutine,  self.onPasteRoutine)
        self.expMenu.AppendSeparator()

        self.expMenu.Append(self.IDs.addRoutineToFlow, "Insert Routine in Flow", "Select one of your routines to be inserted into the experiment flow")
        wx.EVT_MENU(self, self.IDs.addRoutineToFlow,  self.flowPanel.onInsertRoutine)
        self.expMenu.Append(self.IDs.addLoopToFlow, "Insert Loop in Flow", "Create a new loop in your flow window")
        wx.EVT_MENU(self, self.IDs.addLoopToFlow,  self.flowPanel.insertLoop)

        #---_demos---#000000#FFFFFF--------------------------------------------------
        #for demos we need a dict where the event ID will correspond to a filename

        self.demosMenu = wx.Menu()
        #unpack demos option
        self.demosMenu.Append(self.IDs.builderDemosUnpack, "&Unpack Demos...",
            "Unpack demos to a writable location (so that they can be run)")
        wx.EVT_MENU(self, self.IDs.builderDemosUnpack, self.demosUnpack)
        self.demosMenu.AppendSeparator()
        self.demosMenuUpdate()#add any demos that are found in the prefs['demosUnpacked'] folder
        menuBar.Append(self.demosMenu, '&Demos')

        #---_help---#000000#FFFFFF--------------------------------------------------
        self.helpMenu = wx.Menu()
        menuBar.Append(self.helpMenu, '&Help')
        self.helpMenu.Append(self.IDs.psychopyHome, "&PsychoPy Homepage", "Go to the PsychoPy homepage")
        wx.EVT_MENU(self, self.IDs.psychopyHome, self.app.followLink)
        self.helpMenu.Append(self.IDs.builderHelp, "&PsychoPy Builder Help", "Go to the online documentation for PsychoPy Builder")
        wx.EVT_MENU(self, self.IDs.builderHelp, self.app.followLink)

        self.helpMenu.AppendSeparator()
        self.helpMenu.Append(self.IDs.about, "&About...", "About PsychoPy")
        wx.EVT_MENU(self, self.IDs.about, self.app.showAbout)

        self.SetMenuBar(menuBar)

    def closeFrame(self, event=None, checkSave=True):

        if self.app.coder==None and sys.platform!='darwin':
            if not self.app.quitting:
                self.app.quit()
                return#app.quit() will have closed the frame already

        if checkSave:
            ok=self.checkSave()
            if not ok: return False
        if self.filename==None:
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
        for ii in range(self.fileHistory.GetCount()):
            self.appData['fileHistory'].append(self.fileHistory.GetHistoryFile(ii))

        #assign the data to this filename
        self.appData['frames'][self.filename] = frameData
        self.app.allFrames.remove(self)
        self.app.builderFrames.remove(self)
        #close window
        self.Destroy()
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
        self.exp = experiment.Experiment(prefs=self.app.prefs)
        default_routine = 'trial'
        self.exp.addRoutine(default_routine) #create the trial routine as an example
        self.exp.flow.addRoutine(self.exp.routines[default_routine], pos=1)#add it to flow
        self.exp.namespace.add(default_routine, self.exp.namespace.user) # add it to user's namespace
        self.resetUndoStack()
        self.setIsModified(False)
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
        self.exp = experiment.Experiment(prefs=self.app.prefs)
        try:
            self.exp.loadFromXML(filename)
        except Exception, err:
            print "Failed to load %s. Please send the following to the PsychoPy user list" %filename
            traceback.print_exc()
            log.flush()
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
            # if the file already exists, query whether it should be overwritten (default = yes)
            dlg2 = dialogs.MessageDialog(self,
                        message="File '%s' already exists.\n    OK to overwrite?" % (newPath),
                        type='Warning')
            if not os.path.exists(newPath) or dlg2.ShowModal() == wx.ID_YES:
                shortName = os.path.splitext(os.path.split(newPath)[1])[0]
                self.exp.setExpName(shortName)
                #actually save
                self.fileSave(event=None, filename=newPath)
                self.filename = newPath
                returnVal = 1
                try: dlg2.destroy()
                except: pass
            else:
                print "'Save-as' canceled; existing file NOT overwritten.\n"
        try: #this seems correct on PC, but not on mac
            dlg.destroy()
        except:
            pass
        self.updateWindowTitle()
        return returnVal
    def OnFileHistory(self, evt=None):
        # get the file based on the menu ID
        fileNum = evt.GetId() - wx.ID_FILE1
        path = self.fileHistory.GetHistoryFile(fileNum)
        self.setCurrentDoc(path)#load the file
        # add it back to the history so it will be moved up the list
        self.fileHistory.AddFileToHistory(path)
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
        self.flowPanel.draw()
        self.routinePanel.redrawRoutines()
        self.updateWindowTitle()
    def updateWindowTitle(self, newTitle=None):
        if newTitle==None:
            shortName = os.path.split(self.filename)[-1]
            newTitle='%s - PsychoPy Builder' %(shortName)
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
    def demosUnpack(self, event=None):
        """Get a folder location from the user and unpack demos into it
        """
        #choose a dir to unpack in
        dlg = wx.DirDialog(parent=self, message="Location to unpack demos")
        if dlg.ShowModal()==wx.ID_OK:
            unpackFolder = dlg.GetPath()
        else:
            return -1#user cancelled
        # ensure it's an empty dir:
        if os.listdir(unpackFolder) != []:
            unpackFolder = os.path.join(unpackFolder, 'PsychoPy2 Demos')
            if not os.path.isdir(unpackFolder):
                os.mkdir(unpackFolder)
        misc.mergeFolder(os.path.join(self.paths['demos'], 'builder'), unpackFolder)
        self.prefs['unpackedDemosDir']=unpackFolder
        self.app.prefs.saveUserPrefs()
        self.demosMenuUpdate()
    def demoLoad(self, event=None):
        fileDir = self.demos[event.GetId()]
        files = glob.glob(os.path.join(fileDir,'*.psyexp'))
        if len(files)==0:
            print "Found no psyexp files in %s" %fileDir
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
        #get abs path of expereiment so it can be stored with data at end of exp
        expPath = self.filename
        if expPath==None or expPath.startswith('untitled'):
            ok = self.fileSave()
            if not ok: return#save file before compiling script
        expPath = os.path.abspath(expPath)
        #make new pathname for script file
        fullPath = self.filename.replace('.psyexp','_lastrun.py')
        script = self.exp.writeScript(expPath=expPath)

        #set the directory and add to path
        folder, scriptName = os.path.split(fullPath)
        if len(folder)>0: os.chdir(folder)#otherwise this is unsaved 'untitled.psyexp'
        f = codecs.open(fullPath, 'w', 'utf-8')
        f.write(script.getvalue())
        f.close()
        try:
            self.stdoutFrame.getText()
        except:
            self.stdoutFrame=stdOutRich.StdOutFrame(parent=self, app=self.app, size=(700,300))

        sys.stdout = self.stdoutFrame
        sys.stderr = self.stdoutFrame

        #provide a running... message
        print "\n"+(" Running: %s " %(fullPath)).center(80,"#")
        self.stdoutFrame.lenLastRun = len(self.stdoutFrame.getText())

        self.scriptProcess=wx.Process(self) #self is the parent (which will receive an event when the process ends)
        self.scriptProcess.Redirect()#builder will receive the stdout/stdin

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
        if len(text):self.stdoutFrame.write(text) #if some text hadn't yet been written (possible?)
        if len(self.stdoutFrame.getText())>self.stdoutFrame.lenLastRun:
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
        if self.app.copiedRoutine == None: return -1
        defaultName = self.exp.namespace.make_valid(self.app.copiedRoutine.name)
        message = 'New name for copy of "%s"?  [%s]' % (self.app.copiedRoutine.name, defaultName)
        dlg = wx.TextEntryDialog(self, message=message, caption='Paste Routine')
        if dlg.ShowModal() == wx.ID_OK:
            routineName=dlg.GetValue()
            newRoutine = copy.deepcopy(self.app.copiedRoutine)
            if not routineName:
                routineName = defaultName
            newRoutine.name = self.exp.namespace.make_valid(routineName)
            self.exp.namespace.add(newRoutine.name)
            self.exp.addRoutine(newRoutine.name, newRoutine)#add to the experiment
            for newComp in newRoutine: # routine == list of components
                newName = self.exp.namespace.make_valid(newComp.params['name'])
                self.exp.namespace.add(newName)
                newComp.params['name'].val = newName
            self.routinePanel.addRoutinePage(newRoutine.name, newRoutine)#could do redrawRoutines but would be slower?
            self.addToUndoStack("paste Routine %s" % newRoutine.name)
        dlg.Destroy()
    def onURL(self, evt):
        """decompose the URL of a file and line number"""
        # "C:\\Program Files\\wxPython2.8 Docs and Demos\\samples\\hangman\\hangman.py", line 21,
        filename = evt.GetString().split('"')[1]
        lineNumber = int(evt.GetString().split(',')[1][5:])
        self.app.coder.gotoLine(filename,lineNumber)
        self.app.showCoder()
    def compileScript(self, event=None):
        script = self.exp.writeScript(expPath=None)#leave the experiment path blank
        name = os.path.splitext(self.filename)[0]+".py"#remove .psyexp and add .py
        self.app.showCoder()#make sure coder is visible
        self.app.coder.fileNew(filepath=name)
        self.app.coder.currentDoc.SetText(script.getvalue())
    def setExperimentSettings(self,event=None):
        component=self.exp.settings
        #does this component have a help page?
        if hasattr(component, 'url'):helpUrl=component.url
        else:helpUrl=None
        dlg = DlgExperimentProperties(frame=self,
            title='%s Properties' %self.exp.name,
            params = component.params,helpUrl=helpUrl,
            order = component.order)
        if dlg.OK:
            self.addToUndoStack("edit experiment settings")
            self.setIsModified(True)
    def addRoutine(self, event=None):
        self.routinePanel.createNewRoutine()

def appDataToFrames(prefs):
    """Takes the standard PsychoPy prefs and returns a list of appData dictionaries, for the Builder frames.
    (Needed because prefs stores a dict of lists, but we need a list of dicts)
    """
    dat = prefs.appData['builder']
def framesToAppData(prefs):
    pass
def canBeNumeric(inStr):
    """Determines whether the input can be converted to a float
    (using a try: float(instr))
    """
    try:
        float(inStr)
        return True
    except:
        return False
def _relpath(path, start='.'):
    """This code is based on os.path.repath in the Python 2.6 distribution,
    included here for compatibility with Python 2.5"""

    if not path:
        raise ValueError("no path specified")

    start_list = os.path.abspath(start).split(os.path.sep)
    path_list = os.path.abspath(path).split(os.path.sep)

    # Work out how much of the filepath is shared by start and path.
    i = len(os.path.commonprefix([start_list, path_list]))

    rel_list = ['..'] * (len(start_list)-i) + path_list[i:]
    if not rel_list:
        return curdir
    return os.path.join(*rel_list)
