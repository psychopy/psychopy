#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Defines the behavior of Psychopy's Builder view window
Part of the PsychoPy library
Copyright (C) 2018 Jonathan Peirce
Distributed under the terms of the GNU General Public License (GPL).
"""

from __future__ import absolute_import, division, print_function

from pkg_resources import parse_version
import wx
import wx.stc
from wx.lib import platebtn, scrolledpanel

try:
    from wx import aui
except ImportError:
    import wx.lib.agw.aui as aui  # some versions of phoenix
try:
    from wx.adv import PseudoDC
except ImportError:
    from wx import PseudoDC

if parse_version(wx.__version__) < parse_version('4.0.3'):
    wx.NewIdRef = wx.NewId

import sys
import os
import subprocess
import glob
import copy
import traceback
import codecs
import numpy

from psychopy.localization import _translate

from ... import experiment
from .. import stdOutRich, dialogs
from ..icons import getAllIcons
from psychopy import logging, constants, __version__
from psychopy.tools.filetools import mergeFolder
from .dialogs import (DlgComponentProperties, DlgExperimentProperties,
                      DlgCodeComponentProperties)
from .flow import FlowPanel
from ..utils import FileDropTarget, WindowFrozen
from psychopy.experiment import components

from psychopy.app import pavlovia_ui
from psychopy.projects import pavlovia

from psychopy.scripts import psyexpCompile


canvasColor = [200, 200, 200]  # in prefs? ;-)
routineTimeColor = wx.Colour(50, 100, 200, 200)
staticTimeColor = wx.Colour(200, 50, 50, 100)
disabledTimeColor = wx.Colour(127, 127, 127, 100)
nonSlipFill = wx.Colour(150, 200, 150, 255)
nonSlipEdge = wx.Colour(0, 100, 0, 255)
relTimeFill = wx.Colour(200, 150, 150, 255)
relTimeEdge = wx.Colour(200, 50, 50, 255)
routineFlowColor = wx.Colour(200, 150, 150, 255)
darkgrey = wx.Colour(65, 65, 65, 255)
white = wx.Colour(255, 255, 255, 255)
darkblue = wx.Colour(30, 30, 150, 255)
codeSyntaxOkay = wx.Colour(220, 250, 220, 255)  # light green

# _localized separates internal (functional) from displayed strings
# long form here allows poedit string discovery
_localized = {
    'Field': _translate('Field'),
    'Default': _translate('Default'),
    'Favorites': _translate('Favorites'),
    'Stimuli': _translate('Stimuli'),
    'Responses': _translate('Responses'),
    'Custom': _translate('Custom'),
    'I/O': _translate('I/O'),
    'Add to favorites': _translate('Add to favorites'),
    'Remove from favorites': _translate('Remove from favorites'),
    # contextMenuLabels
    'edit': _translate('edit'),
    'remove': _translate('remove'),
    'copy': _translate('copy'),
    'move to top': _translate('move to top'),
    'move up': _translate('move up'),
    'move down': _translate('move down'),
    'move to bottom': _translate('move to bottom')}


class RoutineCanvas(wx.ScrolledWindow):
    """Represents a single routine (used as page in RoutinesNotebook)"""

    def __init__(self, notebook, id=wx.ID_ANY, routine=None):
        """This window is based heavily on the PseudoDC demo of wxPython
        """
        wx.ScrolledWindow.__init__(
            self, notebook, id, (0, 0), style=wx.SUNKEN_BORDER)

        self.SetBackgroundColour(canvasColor)
        self.notebook = notebook
        self.frame = notebook.frame
        self.app = self.frame.app
        self.dpi = self.app.dpi
        self.lines = []
        self.maxWidth = 15 * self.dpi
        self.maxHeight = 15 * self.dpi
        self.x = self.y = 0
        self.curLine = []
        self.drawing = False
        self.drawSize = self.app.prefs.appData['routineSize']
        # auto-rescale based on number of components and window size is jumpy
        # when switch between routines of diff drawing sizes
        self.iconSize = (24, 24, 48)[self.drawSize]  # only 24, 48 so far
        self.fontBaseSize = (800, 900, 1000)[self.drawSize]  # depends on OS?

        self.SetVirtualSize((self.maxWidth, self.maxHeight))
        self.SetScrollRate(self.dpi / 4, self.dpi / 4)

        self.routine = routine
        self.yPositions = None
        self.yPosTop = (25, 40, 60)[self.drawSize]
        # the step in Y between each component
        self.componentStep = (25, 32, 50)[self.drawSize]
        self.timeXposStart = (150, 150, 200)[self.drawSize]
        # the left hand edge of the icons:
        _scale = (1.3, 1.5, 1.5)[self.drawSize]
        self.iconXpos = self.timeXposStart - self.iconSize * _scale
        self.timeXposEnd = self.timeXposStart + 400  # onResize() overrides

        # create a PseudoDC to record our drawing
        self.pdc = PseudoDC()
        self.pen_cache = {}
        self.brush_cache = {}
        # vars for handling mouse clicks
        self.dragid = -1
        self.lastpos = (0, 0)
        # use the ID of the drawn icon to retrieve component name:
        self.componentFromID = {}
        self.contextMenuItems = ['copy', 'edit', 'remove',
                                 'move to top', 'move up',
                                 'move down', 'move to bottom']
        # labels are only for display, and allow localization
        self.contextMenuLabels = {k: _localized[k]
                                  for k in self.contextMenuItems}
        self.contextItemFromID = {}
        self.contextIDFromItem = {}
        for item in self.contextMenuItems:
            id = wx.NewIdRef()
            self.contextItemFromID[id] = item
            self.contextIDFromItem[item] = id

        self.redrawRoutine()

        self.Bind(wx.EVT_PAINT, self.OnPaint)
        self.Bind(wx.EVT_ERASE_BACKGROUND, lambda x: None)
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)
        self.Bind(wx.EVT_SIZE, self.onResize)
        # crashes if drop on OSX:
        # self.SetDropTarget(FileDropTarget(builder = self.frame))

    def onResize(self, event):
        self.sizePix = event.GetSize()
        self.timeXposStart = (150, 150, 200)[self.drawSize]
        self.timeXposEnd = self.sizePix[0] - (60, 80, 100)[self.drawSize]
        self.redrawRoutine()  # then redraw visible

    def ConvertEventCoords(self, event):
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        return (event.GetX() + (xView * xDelta),
                event.GetY() + (yView * yDelta))

    def OffsetRect(self, r):
        """Offset the rectangle, r, to appear in the given pos in the window
        """
        xView, yView = self.GetViewStart()
        xDelta, yDelta = self.GetScrollPixelsPerUnit()
        r.OffsetXY(-(xView * xDelta), -(yView * yDelta))

    def OnMouse(self, event):
        if event.LeftDown():
            x, y = self.ConvertEventCoords(event)
            icons = self.pdc.FindObjectsByBBox(x, y)
            if len(icons):
                self.editComponentProperties(
                    component=self.componentFromID[icons[0]])
        elif event.RightDown():
            x, y = self.ConvertEventCoords(event)
            icons = self.pdc.FindObjectsByBBox(x, y)
            menuPos = event.GetPosition()
            if self.app.prefs.builder['topFlow']:
                # width of components panel
                menuPos[0] += self.frame.componentButtons.GetSize()[0]
                # height of flow panel
                menuPos[1] += self.frame.flowPanel.GetSize()[1]
            if len(icons):
                self._menuComponent = self.componentFromID[icons[0]]
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
            menu.Append(id, self.contextMenuLabels[item])
            menu.Bind(wx.EVT_MENU, self.onContextSelect, id=id)
        self.frame.PopupMenu(menu, xy)
        menu.Destroy()  # destroy to avoid mem leak

    def onContextSelect(self, event):
        """Perform a given action on the component chosen
        """
        op = self.contextItemFromID[event.GetId()]
        component = self._menuComponent
        r = self.routine
        if op == 'edit':
            self.editComponentProperties(component=component)
        elif op == 'copy':
            self.copyCompon(component=component)
        elif op == 'remove':
            r.removeComponent(component)
            self.frame.addToUndoStack(
                "REMOVE `%s` from Routine" % (component.params['name'].val))
            self.frame.exp.namespace.remove(component.params['name'].val)
        elif op.startswith('move'):
            lastLoc = r.index(component)
            r.remove(component)
            if op == 'move to top':
                r.insert(0, component)
            if op == 'move up':
                r.insert(lastLoc - 1, component)
            if op == 'move down':
                r.insert(lastLoc + 1, component)
            if op == 'move to bottom':
                r.append(component)
            self.frame.addToUndoStack("MOVED `%s`" %
                                      component.params['name'].val)
        self.redrawRoutine()
        self._menuComponent = None

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
        x, y = (xv * dx, yv * dy)
        rgn = self.GetUpdateRegion()
        rgn.Offset(x, y)
        r = rgn.GetBox()
        # draw to the dc using the calculated clipping rect
        self.pdc.DrawToDCClipped(dc, r)

    def redrawRoutine(self):
        self.pdc.Clear()  # clear the screen
        self.pdc.RemoveAll()  # clear all objects (icon buttons)

        # work out where the component names and icons should be from name
        # lengths
        self.setFontSize(self.fontBaseSize // self.dpi, self.pdc)
        longest = 0
        w = 50
        for comp in self.routine:
            name = comp.params['name'].val
            if len(name) > longest:
                longest = len(name)
                w = self.GetFullTextExtent(name)[0]
        self.timeXpos = w + (50, 50, 90)[self.drawSize]

        # separate components according to whether they are drawn in separate
        # row
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
            bottom = max(yPosBottom, self.GetSize()[1])
            self.drawStatic(self.pdc, component, yPos, bottom)
        self.drawTimeGrid(self.pdc, yPos, yPosBottom)
        # normal components, one per row
        for component in rowComponents:
            self.drawComponent(self.pdc, component, yPos)
            yPos += self.componentStep

        # the 50 allows space for labels below the time axis
        self.SetVirtualSize((self.maxWidth, yPos + 50))
        self.Refresh()  # refresh the visible window after drawing (OnPaint)

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
        tMax = self.getMaxTime() * 1.1
        xScale = self.getSecsPerPixel()
        xSt = self.timeXposStart
        xEnd = self.timeXposEnd

        # dc.SetId(wx.NewIdRef())
        dc.SetPen(wx.Pen(wx.Colour(0, 0, 0, 150)))
        # draw horizontal lines on top and bottom
        dc.DrawLine(x1=xSt, y1=yPosTop,
                    x2=xEnd, y2=yPosTop)
        dc.DrawLine(x1=xSt, y1=yPosBottom,
                    x2=xEnd, y2=yPosBottom)
        # draw vertical time points
        # gives roughly 1/10 the width, but in rounded to base 10 of
        # 0.1,1,10...
        unitSize = 10 ** numpy.ceil(numpy.log10(tMax * 0.8)) / 10.0
        if tMax / unitSize < 3:
            # gives units of 2 (0.2,2,20)
            unitSize = 10 ** numpy.ceil(numpy.log10(tMax * 0.8)) / 50.0
        elif tMax / unitSize < 6:
            # gives units of 5 (0.5,5,50)
            unitSize = 10 ** numpy.ceil(numpy.log10(tMax * 0.8)) / 20.0
        for lineN in range(int(numpy.floor((tMax / unitSize)))):
            # vertical line:
            dc.DrawLine(xSt + lineN * unitSize / xScale, yPosTop - 4,
                        xSt + lineN * unitSize / xScale, yPosBottom + 4)
            # label above:
            dc.DrawText('%.2g' % (lineN * unitSize), xSt + lineN *
                        unitSize / xScale - 4, yPosTop - 20)
            if yPosBottom > 300:
                # if bottom of grid is far away then draw labels here too
                dc.DrawText('%.2g' % (lineN * unitSize), xSt + lineN *
                            unitSize / xScale - 4, yPosBottom + 10)
        # add a label
        self.setFontSize(self.fontBaseSize // self.dpi, dc)
        # y is y-half height of text
        dc.DrawText('t (sec)', xEnd + 5,
                    yPosTop - self.GetFullTextExtent('t')[1] / 2.0)
        # or draw bottom labels only if scrolling is turned on, virtual size >
        # available size?
        if yPosBottom > 300:
            # if bottom of grid is far away then draw labels there too
            # y is y-half height of text
            dc.DrawText('t (sec)', xEnd + 5,
                        yPosBottom - self.GetFullTextExtent('t')[1] / 2.0)

    def setFontSize(self, size, dc):
        font = self.GetFont()
        font.SetPointSize(size)
        dc.SetFont(font)

    def drawStatic(self, dc, component, yPosTop, yPosBottom):
        """draw a static (ISI) component box"""
        # set an id for the region of this component (so it can
        # act as a button). see if we created this already.
        id = None
        for key in self.componentFromID:
            if self.componentFromID[key] == component:
                id = key
        if not id:  # then create one and add to the dict
            id = wx.NewIdRef()
            self.componentFromID[id] = component
        dc.SetId(id)
        # deduce start and stop times if possible
        startTime, duration, nonSlipSafe = component.getStartAndDuration()
        # ensure static comps are clickable (even if $code start or duration)
        unknownTiming = False
        if startTime is None:
            startTime = 0
            unknownTiming = True
        if duration is None:
            duration = 0  # minimal extent ensured below
            unknownTiming = True
        # calculate rectangle for component
        xScale = self.getSecsPerPixel()
        dc.SetPen(wx.Pen(wx.Colour(200, 100, 100, 0), style=wx.TRANSPARENT))

        if component.params['disabled'].val:
            dc.SetBrush(wx.Brush(disabledTimeColor))
        else:
            dc.SetBrush(wx.Brush(staticTimeColor))

        xSt = self.timeXposStart + startTime // xScale
        w = duration // xScale + 1  # +1 b/c border alpha=0 in dc.SetPen
        w = max(min(w, 10000), 2)  # ensure 2..10000 pixels
        h = yPosBottom - yPosTop
        # name label, position:
        name = component.params['name'].val  # "ISI"
        if unknownTiming:
            # flag it as not literally represented in time, e.g., $code
            # duration
            name += ' ???'
        nameW, nameH = self.GetFullTextExtent(name)[0:2]
        x = xSt + w // 2
        staticLabelTop = (0, 50, 60)[self.drawSize]
        y = staticLabelTop - nameH * 3
        fullRect = wx.Rect(x - 20, y, nameW, nameH)
        # draw the rectangle, draw text on top:
        dc.DrawRectangle(xSt, yPosTop - nameH * 4, w, h + nameH * 5)
        dc.DrawText(name, x - nameW // 2, y)
        # update bounds to include time bar
        fullRect.Union(wx.Rect(xSt, yPosTop, w, h))
        dc.SetIdBounds(id, fullRect)

    def drawComponent(self, dc, component, yPos):
        """Draw the timing of one component on the timeline"""
        # set an id for the region of this component (so it
        # can act as a button). see if we created this already
        id = None
        for key in self.componentFromID:
            if self.componentFromID[key] == component:
                id = key
        if not id:  # then create one and add to the dict
            id = wx.NewIdRef()
            self.componentFromID[id] = component
        dc.SetId(id)

        iconYOffset = (6, 6, 0)[self.drawSize]
        componIcons = getAllIcons(self.app.prefs.builder['componentsFolders'])
        thisIcon = componIcons[component.getType()]["{}".format(
            self.iconSize)]  # getType index 0 is main icon
        dc.DrawBitmap(thisIcon, self.iconXpos, yPos + iconYOffset, True)
        fullRect = wx.Rect(self.iconXpos, yPos,
                           thisIcon.GetWidth(), thisIcon.GetHeight())

        self.setFontSize(self.fontBaseSize // self.dpi, dc)

        name = component.params['name'].val
        # get size based on text
        w, h = self.GetFullTextExtent(name)[0:2]
        # draw text
        _base = (self.iconSize, self.iconSize, 10)[self.drawSize]
        x = self.iconXpos - self.dpi // 10 - w + _base
        _adjust = (5, 5, -2)[self.drawSize]
        y = yPos + thisIcon.GetHeight() // 2 - h // 2 + _adjust
        dc.DrawText(name, x - 20, y)
        fullRect.Union(wx.Rect(x - 20, y, w, h))

        # deduce start and stop times if possible
        startTime, duration, nonSlipSafe = component.getStartAndDuration()
        # draw entries on timeline (if they have some time definition)
        if startTime is not None and duration is not None:
            # then we can draw a sensible time bar!
            xScale = self.getSecsPerPixel()
            dc.SetPen(wx.Pen(wx.Colour(200, 100, 100, 0),
                             style=wx.TRANSPARENT))

            if component.params['disabled'].val:
                dc.SetBrush(wx.Brush(disabledTimeColor))
            else:
                dc.SetBrush(wx.Brush(routineTimeColor))

            hSize = (3.5, 2.75, 2)[self.drawSize]
            yOffset = (3, 3, 0)[self.drawSize]
            h = self.componentStep // hSize
            xSt = self.timeXposStart + startTime // xScale
            w = duration // xScale + 1
            if w > 10000:
                w = 10000  # limit width to 10000 pixels!
            if w < 2:
                w = 2  # make sure at least one pixel shows
            dc.DrawRectangle(xSt, y + yOffset, w, h)
            # update bounds to include time bar
            fullRect.Union(wx.Rect(xSt, y + yOffset, w, h))
        dc.SetIdBounds(id, fullRect)

    def copyCompon(self, event=None, component=None):
        """This is easy - just take a copy of the component into memory
        """
        self.app.copiedCompon = copy.deepcopy(component)

    def pasteCompon(self, event=None, component=None):
        if not self.app.copiedCompon:
            return -1  # not possible to paste if nothing copied
        exp = self.frame.exp
        origName = self.app.copiedCompon.params['name'].val
        defaultName = exp.namespace.makeValid(origName)
        msg = _translate('New name for copy of "%(copied)s"?  [%(default)s]')
        vals = {'copied': origName, 'default': defaultName}
        message = msg % vals
        dlg = wx.TextEntryDialog(self, message=message,
                                 caption=_translate('Paste Component'))
        if dlg.ShowModal() == wx.ID_OK:
            newName = dlg.GetValue()
            newCompon = copy.deepcopy(self.app.copiedCompon)
            if not newName:
                newName = defaultName
            newName = exp.namespace.makeValid(newName)
            newCompon.params['name'].val = newName
            if 'name' in dir(newCompon):
                newCompon.name = newName
            self.routine.addComponent(newCompon)
            # could do redrawRoutines but would be slower?
            self.redrawRoutine()
            self.frame.addToUndoStack("PASTE Component `%s`" % newName)
        dlg.Destroy()

    def editComponentProperties(self, event=None, component=None):
        # we got here from a wx.button press (rather than our own drawn icons)
        if event:
            componentName = event.EventObject.GetName()
            component = self.routine.getComponentFromName(componentName)
        # does this component have a help page?
        if hasattr(component, 'url'):
            helpUrl = component.url
        else:
            helpUrl = None
        old_name = component.params['name'].val
        old_disabled = component.params['disabled'].val
        # check current timing settings of component (if it changes we
        # need to update views)
        initialTimings = component.getStartAndDuration()
        # create the dialog
        if hasattr(component, 'type') and component.type.lower() == 'code':
            _Dlg = DlgCodeComponentProperties
        else:
            _Dlg = DlgComponentProperties
        dlg = _Dlg(frame=self.frame,
                   title=component.params['name'].val + ' Properties',
                   params=component.params,
                   order=component.order, helpUrl=helpUrl, editing=True,
                   depends=component.depends)
        if dlg.OK:
            if component.getStartAndDuration() != initialTimings:
                self.redrawRoutine()  # need to refresh timings section
                self.Refresh()  # then redraw visible
                self.frame.flowPanel.draw()
                # self.frame.flowPanel.Refresh()
            elif component.params['name'].val != old_name:
                self.redrawRoutine()  # need to refresh name
            elif component.params['disabled'].val != old_disabled:
                self.redrawRoutine()  # need to refresh color
            self.frame.exp.namespace.remove(old_name)
            self.frame.exp.namespace.add(component.params['name'].val)
            self.frame.addToUndoStack("EDIT `%s`" %
                                      component.params['name'].val)

    def getSecsPerPixel(self):
        pixels = float(self.timeXposEnd - self.timeXposStart)
        return self.getMaxTime() / pixels


class RoutinesNotebook(aui.AuiNotebook):
    """A notebook that stores one or more routines
    """

    def __init__(self, frame, id=-1):
        self.frame = frame
        self.app = frame.app
        self.routineMaxSize = 2
        self.appData = self.app.prefs.appData
        aui.AuiNotebook.__init__(self, frame, id)

        self.Bind(aui.EVT_AUINOTEBOOK_PAGE_CLOSE, self.onClosePane)
        if not hasattr(self.frame, 'exp'):
            return  # we haven't yet added an exp

    def getCurrentRoutine(self):
        routinePage = self.getCurrentPage()
        if routinePage:
            return routinePage.routine  # no routine page
        return None

    def setCurrentRoutine(self, routine):
        for ii in range(self.GetPageCount()):
            if routine is self.GetPage(ii).routine:
                self.SetSelection(ii)

    def getCurrentPage(self):
        if self.GetSelection() >= 0:
            return self.GetPage(self.GetSelection())
        return None

    def addRoutinePage(self, routineName, routine):
        #        routinePage = RoutinePage(parent=self, routine=routine)
        routinePage = RoutineCanvas(notebook=self, routine=routine)
        self.AddPage(routinePage, routineName)

    def renameRoutinePage(self, index, newName, ):
        self.SetPageText(index, newName)

    def removePages(self):
        for ii in range(self.GetPageCount()):
            currId = self.GetSelection()
            self.DeletePage(currId)

    def createNewRoutine(self, returnName=False):
        msg = _translate("What is the name for the new Routine? "
                         "(e.g. instr, trial, feedback)")
        dlg = wx.TextEntryDialog(self, message=msg,
                                 caption=_translate('New Routine'))
        exp = self.frame.exp
        routineName = None
        if dlg.ShowModal() == wx.ID_OK:
            routineName = dlg.GetValue()
            # silently auto-adjust the name to be valid, and register in the
            # namespace:
            routineName = exp.namespace.makeValid(
                routineName, prefix='routine')
            exp.namespace.add(routineName)  # add to the namespace
            exp.addRoutine(routineName)  # add to the experiment
            # then to the notebook:
            self.addRoutinePage(routineName, exp.routines[routineName])
            self.frame.addToUndoStack("NEW Routine `%s`" % routineName)
        dlg.Destroy()
        if returnName:
            return routineName

    def onClosePane(self, event=None):
        """Close the pane and remove the routine from the exp
        """
        routine = self.GetPage(event.GetSelection()).routine
        name = routine.name
        # update experiment object, namespace, and flow window (if this is
        # being used)
        if name in self.frame.exp.routines:
            # remove names of the routine and its components from namespace
            _nsp = self.frame.exp.namespace
            for c in self.frame.exp.routines[name]:
                _nsp.remove(c.params['name'].val)
            _nsp.remove(self.frame.exp.routines[name].name)
            del self.frame.exp.routines[name]
        if routine in self.frame.exp.flow:
            self.frame.exp.flow.removeComponent(routine)
            self.frame.flowPanel.draw()
        self.frame.addToUndoStack("REMOVE Routine `%s`" % (name))

    def increaseSize(self, event=None):
        self.appData['routineSize'] = min(
            self.routineMaxSize, self.appData['routineSize'] + 1)
        with WindowFrozen(self):
            self.redrawRoutines()

    def decreaseSize(self, event=None):
        self.appData['routineSize'] = max(0, self.appData['routineSize'] - 1)
        with WindowFrozen(self):
            self.redrawRoutines()

    def redrawRoutines(self):
        """Removes all the routines, adds them back (alphabetical order),
        sets current back to orig
        """
        currPage = self.GetSelection()
        self.removePages()
        displayOrder = sorted(self.frame.exp.routines.keys())  # alphabetical
        for routineName in displayOrder:
            self.addRoutinePage(
                routineName, self.frame.exp.routines[routineName])
        if currPage > -1:
            self.SetSelection(currPage)


class ComponentsPanel(scrolledpanel.ScrolledPanel):

    def __init__(self, frame, id=-1):
        """A panel that displays available components.
        """
        self.frame = frame
        self.app = frame.app
        self.dpi = self.app.dpi
        if self.app.prefs.app['largeIcons']:
            panelWidth = 3 * 48 + 50
        else:
            panelWidth = 3 * 24 + 50
        scrolledpanel.ScrolledPanel.__init__(
            self, frame, id, size=(panelWidth, 10 * self.dpi))
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.components = experiment.getAllComponents(
            self.app.prefs.builder['componentsFolders'])
        categories = ['Favorites']
        categories.extend(components.getAllCategories(
            self.app.prefs.builder['componentsFolders']))
        # get rid of hidden components
        for hiddenComp in self.frame.prefs['hiddenComponents']:
            if hiddenComp in self.components:
                del self.components[hiddenComp]
        # also remove settings - that's in toolbar not components panel
        del self.components['SettingsComponent']
        # get favorites
        self.favorites = FavoriteComponents(componentsPanel=self)
        # create labels and sizers for each category
        self.componentFromID = {}
        self.panels = {}
        # to keep track of the objects (sections and section labels)
        # within the main sizer
        self.sizerList = []

        for categ in categories:
            if categ in _localized:
                label = _localized[categ]
            else:
                label = categ
            _style = platebtn.PB_STYLE_DROPARROW
            sectionBtn = platebtn.PlateButton(self, -1, label,
                                              style=_style, name=categ)
            # mouse event must be bound like this
            sectionBtn.Bind(wx.EVT_LEFT_DOWN, self.onSectionBtn)
            # mouse event must be bound like this
            sectionBtn.Bind(wx.EVT_RIGHT_DOWN, self.onSectionBtn)
            if self.app.prefs.app['largeIcons']:
                self.panels[categ] = wx.FlexGridSizer(cols=1)
            else:
                self.panels[categ] = wx.FlexGridSizer(cols=2)
            self.sizer.Add(sectionBtn, flag=wx.EXPAND)
            self.sizerList.append(sectionBtn)
            self.sizer.Add(self.panels[categ], flag=wx.ALIGN_CENTER)
            self.sizerList.append(self.panels[categ])
        self.makeComponentButtons()
        self._rightClicked = None
        # start all except for Favorites collapsed
        for section in categories[1:]:
            self.toggleSection(self.panels[section])

        self.Bind(wx.EVT_SIZE, self.on_resize)
        self.SetSizer(self.sizer)
        self.SetAutoLayout(True)
        self.SetupScrolling()

    def on_resize(self, event):
        if self.app.prefs.app['largeIcons']:
            cols = self.GetClientSize()[0] // 58
        else:
            cols = self.GetClientSize()[0] // 34
        for category in list(self.panels.values()):
            category.SetCols(max(1, cols))

    def makeFavoriteButtons(self):
        # add a copy of each favorite to that panel first
        for thisName in self.favorites.getFavorites():
            self.addComponentButton(thisName, self.panels['Favorites'])

    def makeComponentButtons(self):
        """Make all the components buttons, including favorites
        """
        self.makeFavoriteButtons()
        # then add another copy for each category that the component itself
        # lists
        componentNames = list(self.components.keys())
        componentNames.sort()
        for thisName in componentNames:
            thisComp = self.components[thisName]
            # NB thisComp is a class - we can't use its methods/attribs until
            # it is an instance
            for category in thisComp.categories:
                panel = self.panels[category]
                self.addComponentButton(thisName, panel)

    def addComponentButton(self, name, panel):
        """Create a component button and add it to a specific panel's sizer
        """
        componIcons = getAllIcons(self.app.prefs.builder['componentsFolders'])
        thisComp = self.components[name]
        shortName = name
        for redundant in ['component', 'Component']:
            if redundant in name:
                shortName = name.replace(redundant, "")
        if self.app.prefs.app['largeIcons']:
            thisIcon = componIcons[name][
                '48add']  # index 1 is the 'add' icon
        else:
            thisIcon = componIcons[name][
                '24add']  # index 1 is the 'add' icon
        btn = wx.BitmapButton(self, -1, thisIcon,
                              size=(thisIcon.GetWidth() + 10,
                                    thisIcon.GetHeight() + 10),
                              name=thisComp.__name__)
        if name in components.tooltips:
            thisTip = components.tooltips[name]
        else:
            thisTip = shortName
        btn.SetToolTip(wx.ToolTip(thisTip))
        self.componentFromID[btn.GetId()] = name
        # use btn.bind instead of self.Bind in oder to trap event here
        btn.Bind(wx.EVT_RIGHT_DOWN, self.onRightClick)
        self.Bind(wx.EVT_BUTTON, self.onClick, btn)
        # ,wx.EXPAND|wx.ALIGN_CENTER )
        panel.Add(btn, proportion=0, flag=wx.ALIGN_RIGHT)

    def onSectionBtn(self, evt):
        if hasattr(evt, 'GetString'):
            buttons = self.panels[evt.GetString()]
        else:
            btn = evt.GetEventObject()
            buttons = self.panels[btn.GetName()]
        self.toggleSection(buttons)

    def toggleSection(self, section):
        ii = self.sizerList.index(section)
        self.sizer.Show(ii, not self.sizer.IsShown(ii))  # ie toggle this item
        self.sizer.Layout()
        self.SetupScrolling()

    def getIndexInSizer(self, obj, sizer):
        """Find index of an item within a sizer (to see if it's there
        or to toggle visibility)
        WX sizers don't (as of v2.8.11) have a way to find the index of
        their contents. This method helps get around that.
        """
        # if the obj is itself a sizer (e.g. within the main sizer then
        # we can't even use sizer.Children (as far as I can work out)
        # so we keep a list to track the contents.
        # for the main sizer we kept track of everything with a list:
        if sizer == self.sizer:
            return self.sizerList.index(obj)
        index = None
        for ii, child in enumerate(sizer.Children):
            if child.GetWindow() == obj:
                index = ii
                break
        return index

    def onRightClick(self, evt):
        """
        Defines rightclick behavior within builder view's
        components panel
        """
        btn = evt.GetEventObject()
        self._rightClicked = btn
        index = self.getIndexInSizer(btn, self.panels['Favorites'])
        if index is None:
            # not currently in favs
            msg = "Add to favorites"
            clickFunc = self.onAddToFavorites
        else:
            # is currently in favs
            msg = "Remove from favorites"
            clickFunc = self.onRemFromFavorites
        menu = wx.Menu()
        id = wx.NewIdRef()
        menu.Append(id, _localized[msg])
        menu.Bind(wx.EVT_MENU, clickFunc, id=id)
        # where to put the context menu
        x, y = evt.GetPosition()  # this is position relative to object
        xBtn, yBtn = evt.GetEventObject().GetPosition()
        self.PopupMenu(menu, (x + xBtn, y + yBtn))
        menu.Destroy()  # destroy to avoid mem leak

    def onClick(self, evt, timeout=None):
        """
        Defines left-click behavior for builder views components panel
        :param: evt can be a wx.Event OR a component class name (MouseComponent)
        """
        # get name of current routine
        currRoutinePage = self.frame.routinePanel.getCurrentPage()
        if not currRoutinePage:
            msg = _translate("Create a routine (Experiment menu) "
                             "before adding components")
            dialogs.MessageDialog(self, msg, type='Info',
                                  title=_translate('Error')).ShowModal()
            return False
        currRoutine = self.frame.routinePanel.getCurrentRoutine()
        # get component name
        if hasattr(evt, "GetId"):
            newClassStr = self.componentFromID[evt.GetId()]
        else:
            newClassStr = evt
        newCompClass = self.components[newClassStr]
        newComp = newCompClass(parentName=currRoutine.name,
                               exp=self.frame.exp)
        # does this component have a help page?
        if hasattr(newComp, 'url'):
            helpUrl = newComp.url
        else:
            helpUrl = None
        # create component template
        if newClassStr == 'CodeComponent':
            _Dlg = DlgCodeComponentProperties
        else:
            _Dlg = DlgComponentProperties
        dlg = _Dlg(frame=self.frame,
                   title='{} Properties'.format(newComp.params['name']),
                   params=newComp.params, order=newComp.order,
                   helpUrl=helpUrl,
                   depends=newComp.depends,
                   timeout=timeout)

        compName = newComp.params['name']
        if dlg.OK:
            currRoutine.addComponent(newComp)  # add to the actual routing
            namespace = self.frame.exp.namespace
            newComp.params['name'].val = namespace.makeValid(
                newComp.params['name'].val)
            namespace.add(newComp.params['name'].val)
            # update the routine's view with the new component too
            currRoutinePage.redrawRoutine()
            self.frame.addToUndoStack(
                "ADD `%s` to `%s`" % (compName, currRoutine.name))
            wasNotInFavs = (newClassStr not in self.favorites.getFavorites())
            self.favorites.promoteComponent(newClassStr, 1)
            # was that promotion enough to be a favorite?
            if wasNotInFavs and newClassStr in self.favorites.getFavorites():
                self.addComponentButton(newClassStr, self.panels['Favorites'])
                self.sizer.Layout()
        return True

    def onAddToFavorites(self, evt=None, btn=None):
        """Defines Add To Favorites Menu Behavior"""
        if btn is None:
            btn = self._rightClicked
        if btn.Name not in self.favorites.getFavorites():
            # check we aren't duplicating
            self.favorites.makeFavorite(btn.Name)
            self.addComponentButton(btn.Name, self.panels['Favorites'])
        self.sizer.Layout()
        self._rightClicked = None

    def onRemFromFavorites(self, evt=None, btn=None):
        """Defines Remove from Favorites Menu Behavior"""
        if btn is None:
            btn = self._rightClicked
        index = self.getIndexInSizer(btn, self.panels['Favorites'])
        if index is None:
            pass
        else:
            self.favorites.setLevel(btn.Name, -100)
            btn.Destroy()
        self.sizer.Layout()
        self._rightClicked = None


class FavoriteComponents(object):
    """Defines the Favorite Components Object class, meant for dealing with
    the user's frequently accessed components"""

    def __init__(self, componentsPanel, threshold=20, neutral=0):
        super(FavoriteComponents, self).__init__()
        self.threshold = 20
        self.neutral = 0
        self.panel = componentsPanel
        self.frame = componentsPanel.frame
        self.app = self.frame.app
        self.prefs = self.app.prefs
        self.currentLevels = self.prefs.appDataCfg['builder']['favComponents']
        self.setDefaults()

    def setDefaults(self):
        """Defines Default Favorite Components"""
        # set those that are favorites by default
        for comp in ('ImageComponent', 'KeyboardComponent',
                     'SoundComponent', 'TextComponent'):
            if comp not in self.currentLevels:
                self.currentLevels[comp] = self.threshold
        for comp in self.panel.components:
            if comp not in self.currentLevels:
                self.currentLevels[comp] = self.neutral

    def makeFavorite(self, compName):
        """Set the value of this component to an arbitrary high value (10000)
        """
        self.currentLevels[compName] = 10000

    def promoteComponent(self, compName, value=1):
        """Promote this component by a certain value (negative to demote)
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
        sortedVals = sorted(list(self.currentLevels.items()),
                            key=lambda x: x[1], reverse=True)
        favorites = []
        maxFav = self.prefs.builder['maxFavorites']
        for name, level in sortedVals:
            # this has been explicitly requested (or REALLY liked!)
            if level >= 10000:
                favorites.append(name)
            elif level >= self.threshold and len(favorites) < maxFav:
                favorites.append(name)
            else:
                # either we've run out of levels>10000 or exceeded maxFavs or
                # run out of level >= thresh
                break
        return favorites


class BuilderFrame(wx.Frame):
    """Defines construction of the Psychopy Builder Frame"""

    def __init__(self, parent, id=-1, title='PsychoPy (Experiment Builder)',
                 pos=wx.DefaultPosition, fileName=None, frameData=None,
                 style=wx.DEFAULT_FRAME_STYLE, app=None):

        if (fileName is not None) and (type(fileName) == bytes):
            fileName = fileName.decode(sys.getfilesystemencoding())

        self.app = app
        self.dpi = self.app.dpi
        # things the user doesn't set like winsize etc:
        self.appData = self.app.prefs.appData['builder']
        # things about the builder that the user can set:
        self.prefs = self.app.prefs.builder
        self.appPrefs = self.app.prefs.app
        self.paths = self.app.prefs.paths
        self.frameType = 'builder'
        self.filename = fileName
        self.htmlPath = None
        self.project = None  # type: pavlovia.PavloviaProject
        self.btnHandles = {}  # stores toolbar buttons so they can be altered

        if fileName in self.appData['frames']:
            self.frameData = self.appData['frames'][fileName]
        else:  # work out a new frame size/location
            dispW, dispH = self.app.getPrimaryDisplaySize()
            default = self.appData['defaultFrame']
            default['winW'] = int(dispW * 0.75)
            default['winH'] = int(dispH * 0.75)
            if default['winX'] + default['winW'] > dispW:
                default['winX'] = 5
            if default['winY'] + default['winH'] > dispH:
                default['winY'] = 5
            self.frameData = dict(self.appData['defaultFrame'])  # copy
            # increment default for next frame
            default['winX'] += 10
            default['winY'] += 10

        # we didn't have the key or the win was minimized / invalid
        if self.frameData['winH'] == 0 or self.frameData['winW'] == 0:
            self.frameData['winX'], self.frameData['winY'] = (0, 0)
        if self.frameData['winY'] < 20:
            self.frameData['winY'] = 20
        wx.Frame.__init__(self, parent=parent, id=id, title=title,
                          pos=(int(self.frameData['winX']), int(
                              self.frameData['winY'])),
                          size=(int(self.frameData['winW']), int(
                              self.frameData['winH'])),
                          style=style)
        self.Bind(wx.EVT_CLOSE, self.closeFrame)
        self.panel = wx.Panel(self)
        # create icon
        if sys.platform != 'darwin':
            # doesn't work on darwin and not necessary: handled by app bundle
            iconFile = os.path.join(self.paths['resources'], 'psychopy.ico')
            if os.path.isfile(iconFile):
                self.SetIcon(wx.Icon(iconFile, wx.BITMAP_TYPE_ICO))

        # create our panels
        self.flowPanel = FlowPanel(frame=self)
        self.routinePanel = RoutinesNotebook(self)
        self.componentButtons = ComponentsPanel(self)
        # menus and toolbars
        self.makeToolbar()
        self.makeMenus()
        self.CreateStatusBar()
        self.SetStatusText("")

        # setup universal shortcuts
        accelTable = self.app.makeAccelTable()
        self.SetAcceleratorTable(accelTable)

        # set stdout to correct output panel
        self.stdoutOrig = sys.stdout
        self.stderrOrig = sys.stderr
        self.stdoutFrame = stdOutRich.StdOutFrame(
            parent=self, app=self.app, size=(700, 300))

        # setup a default exp
        if fileName is not None and os.path.isfile(fileName):
            self.fileOpen(filename=fileName, closeCurrent=False)
        else:
            self.lastSavedCopy = None
            # don't try to close before opening
            self.fileNew(closeCurrent=False)
        self.updateReadme()

        # control the panes using aui manager
        self._mgr = aui.AuiManager(self)
        self._mgr.AddPane(self.routinePanel,
                          aui.AuiPaneInfo().
                          Name("Routines").Caption("Routines").
                          CloseButton(False).MaximizeButton(True).
                          CenterPane())  # 'center panes' expand
        self._mgr.AddPane(self.componentButtons,
                          aui.AuiPaneInfo().
                          Name("Components").Caption("Components").
                          RightDockable(True).LeftDockable(True).
                          CloseButton(False).
                          Right())
        self._mgr.AddPane(self.flowPanel,
                          aui.AuiPaneInfo().
                          Name("Flow").Caption("Flow").
                          BestSize((8 * self.dpi, 2 * self.dpi)).
                          RightDockable(True).LeftDockable(True).
                          CloseButton(False).
                          Bottom())
        if self.prefs['topFlow']:
            self._mgr.GetPane('Flow').Top()
            self._mgr.GetPane('Components').Left()
            self._mgr.GetPane('Routines').CenterPane()
        # tell the manager to 'commit' all the changes just made
        self._mgr.Update()
        # self.SetSizer(self.mainSizer)  # not necessary for aui type controls
        if self.frameData['auiPerspective']:
            self._mgr.LoadPerspective(self.frameData['auiPerspective'])
        self.SetMinSize(wx.Size(600, 400))  # min size for the whole window
        self.SetSize(
            (int(self.frameData['winW']), int(self.frameData['winH'])))
        self.SendSizeEvent()
        self._mgr.Update()

        # self.SetAutoLayout(True)
        self.Bind(wx.EVT_CLOSE, self.closeFrame)
        self.Bind(wx.EVT_END_PROCESS, self.onProcessEnded)

        self.app.trackFrame(self)
        self.SetDropTarget(FileDropTarget(targetFrame=self))

    def makeToolbar(self):
        """Produces Toolbar for the Builder Frame"""
        # ---toolbar---#000000#FFFFFF-----------------------------------------
        _style = wx.TB_HORIZONTAL | wx.NO_BORDER | wx.TB_FLAT
        self.toolbar = self.CreateToolBar(_style)

        if sys.platform == 'win32' or sys.platform.startswith('linux'):
            if self.appPrefs['largeIcons']:
                toolbarSize = 32
            else:
                toolbarSize = 16
        else:
            toolbarSize = 32  # mac: 16 either doesn't work, or looks bad
        self.toolbar.SetToolBitmapSize((toolbarSize, toolbarSize))
        rc = self.app.prefs.paths['resources']
        join = os.path.join
        PNG = wx.BITMAP_TYPE_PNG
        tbSize = toolbarSize
        newBmp = wx.Bitmap(join(rc, 'filenew%i.png' % tbSize), PNG)
        openBmp = wx.Bitmap(join(rc, 'fileopen%i.png' % tbSize), PNG)
        saveBmp = wx.Bitmap(join(rc, 'filesave%i.png' % tbSize), PNG)
        saveAsBmp = wx.Bitmap(join(rc, 'filesaveas%i.png' % tbSize), PNG)
        undoBmp = wx.Bitmap(join(rc, 'undo%i.png' % tbSize), PNG)
        redoBmp = wx.Bitmap(join(rc, 'redo%i.png' % tbSize), PNG)
        stopBmp = wx.Bitmap(join(rc, 'stop%i.png' % tbSize), PNG)
        runBmp = wx.Bitmap(join(rc, 'run%i.png' % tbSize), PNG)
        compileBmp = wx.Bitmap(join(rc, 'compile%i.png' % tbSize), PNG)
        settingsBmp = wx.Bitmap(join(rc, 'cogwindow%i.png' % tbSize), PNG)
        preferencesBmp = wx.Bitmap(join(rc, 'preferences%i.png' % tbSize),
                                   PNG)
        monitorsBmp = wx.Bitmap(join(rc, 'monitors%i.png' % tbSize), PNG)

        ctrlKey = 'Ctrl+'  # OS-dependent tool-tips
        if sys.platform == 'darwin':
            ctrlKey = 'Cmd+'
        tb = self.toolbar
        # keys are the keyboard keys, not the keys of the dict
        keys = {k: self.app.keys[k].replace('Ctrl+', ctrlKey)
                for k in self.app.keys}

        if 'phoenix' in wx.PlatformInfo:
            item = tb.AddTool(wx.ID_ANY,
                              _translate("New [%s]") % keys['new'],
                              newBmp,
                              _translate("Create new experiment file"))
        else:
            item = tb.AddSimpleTool(wx.ID_ANY,
                                    newBmp,
                                    _translate("New [%s]") % keys['new'],
                                    _translate("Create new experiment file"))
        tb.Bind(wx.EVT_TOOL, self.app.newBuilderFrame, item)

        if 'phoenix' in wx.PlatformInfo:
            item = tb.AddTool(wx.ID_ANY,
                              _translate("Open [%s]") % keys['open'],
                              openBmp,
                              _translate("Open an existing experiment file"))
        else:
            item = tb.AddSimpleTool(wx.ID_ANY,
                                    openBmp,
                                    _translate("Open [%s]") % keys['open'],
                                    _translate("Open an existing experiment file"))
        tb.Bind(wx.EVT_TOOL, self.fileOpen, item)

        if 'phoenix' in wx.PlatformInfo:
            self.bldrBtnSave = tb.AddTool(
                -1,
                _translate("Save [%s]") % keys['save'],
                saveBmp,
                _translate("Save current experiment file"))
        else:
            self.bldrBtnSave = tb.AddSimpleTool(
                -1,
                saveBmp,
                _translate("Save [%s]") % keys['save'],
                _translate("Save current experiment file"))
        self.toolbar.EnableTool(self.bldrBtnSave.Id, False)
        tb.Bind(wx.EVT_TOOL, self.fileSave, self.bldrBtnSave)

        if 'phoenix' in wx.PlatformInfo:
            item = tb.AddTool(
                wx.ID_ANY,
                _translate("Save As... [%s]") % keys['saveAs'],
                saveAsBmp,
                _translate("Save current experiment file as..."))
        else:
            item = tb.AddSimpleTool(
                wx.ID_ANY,
                saveAsBmp,
                _translate("Save As... [%s]") % keys['saveAs'],
                _translate("Save current experiment file as..."))
        tb.Bind(wx.EVT_TOOL, self.fileSaveAs, item)

        if 'phoenix' in wx.PlatformInfo:
            self.bldrBtnUndo = tb.AddTool(
                wx.ID_ANY,
                _translate("Undo [%s]") % keys['undo'],
                undoBmp,
                _translate("Undo last action"))
        else:
            self.bldrBtnUndo = tb.AddSimpleTool(
                wx.ID_ANY,
                undoBmp,
                _translate("Undo [%s]") % keys['undo'],
                _translate("Undo last action"))
        tb.Bind(wx.EVT_TOOL, self.undo, self.bldrBtnUndo)

        if 'phoenix' in wx.PlatformInfo:
            self.bldrBtnRedo = tb.AddTool(
                wx.ID_ANY,
                _translate("Redo [%s]") % keys['redo'],
                redoBmp,
                _translate("Redo last action"))
        else:
            self.bldrBtnRedo = tb.AddSimpleTool(
                wx.ID_ANY,
                redoBmp,
                _translate("Redo [%s]") % keys['redo'],
                _translate("Redo last action"))
        tb.Bind(wx.EVT_TOOL, self.redo, self.bldrBtnRedo)

        tb.AddSeparator()

        if 'phoenix' in wx.PlatformInfo:
            item = tb.AddTool(
                wx.ID_ANY,
                _translate("Monitor Center"),
                monitorsBmp,
                _translate("Monitor settings and calibration"))
        else:
            item = tb.AddSimpleTool(
                wx.ID_ANY,
                monitorsBmp,
                _translate("Monitor Center"),
                _translate("Monitor settings and calibration"))
        tb.Bind(wx.EVT_TOOL, self.app.openMonitorCenter, id=item.GetId())

        if 'phoenix' in wx.PlatformInfo:
            item = tb.AddTool(
                wx.ID_ANY,
                _translate("Experiment Settings"),
                settingsBmp,
                _translate("Experiment settings"))
        else:
            item = tb.AddSimpleTool(
                wx.ID_ANY,
                settingsBmp,
                _translate("Experiment Settings"),
                _translate("Experiment settings"))
        tb.Bind(wx.EVT_TOOL, self.setExperimentSettings, item)

        tb.AddSeparator()

        if 'phoenix' in wx.PlatformInfo:
            item = tb.AddTool(
                wx.ID_ANY,
                _translate("Compile Script [%s]") % keys['compileScript'],
                compileBmp,
                _translate("Compile to script"))
        else:
            item = tb.AddSimpleTool(
                wx.ID_ANY,
                compileBmp,
                _translate("Compile Script [%s]") % keys['compileScript'],
                _translate("Compile to script"))
        tb.Bind(wx.EVT_TOOL, self.compileScript, item)

        if 'phoenix' in wx.PlatformInfo:
            self.bldrBtnRun = tb.AddTool(
                wx.ID_ANY,
                _translate("Run [%s]") % keys['runScript'],
                runBmp,
                _translate("Run experiment"))
        else:
            self.bldrBtnRun = tb.AddSimpleTool(
                wx.ID_ANY,
                runBmp,
                _translate("Run [%s]") % keys['runScript'],
                _translate("Run experiment"))
        tb.Bind(wx.EVT_TOOL, self.runFile, self.bldrBtnRun)

        if 'phoenix' in wx.PlatformInfo:
            self.bldrBtnStop = tb.AddTool(
                wx.ID_ANY,
                _translate("Stop [%s]") % keys['stopScript'],
                stopBmp,
                _translate("Stop experiment"))
        else:
            self.bldrBtnStop = tb.AddSimpleTool(
                wx.ID_ANY,
                stopBmp,
                _translate("Stop [%s]") % keys['stopScript'],
                _translate("Stop experiment"))
        tb.Bind(wx.EVT_TOOL, self.stopFile, self.bldrBtnStop)
        self.toolbar.EnableTool(self.bldrBtnStop.Id, False)

        self.toolbar.AddSeparator()
        pavButtons = pavlovia_ui.toolbar.PavloviaButtons(self, toolbar=tb, tbSize=tbSize)
        pavButtons.addPavloviaTools()
        self.btnHandles.update(pavButtons.btnHandles)

        # Finished setup. Make it happen
        tb.Realize()

    def makeMenus(self):
        """
        Produces Menus for the Builder Frame
        """

        # ---Menus---#000000#FFFFFF-------------------------------------------
        menuBar = wx.MenuBar()
        # ---_file---#000000#FFFFFF-------------------------------------------
        self.fileMenu = wx.Menu()
        menuBar.Append(self.fileMenu, _translate('&File'))

        # create a file history submenu
        self.fileHistoryMaxFiles = 10
        self.fileHistory = wx.FileHistory(maxFiles=self.fileHistoryMaxFiles)
        self.recentFilesMenu = wx.Menu()
        self.fileHistory.UseMenu(self.recentFilesMenu)
        for filename in self.appData['fileHistory']:
            self.fileHistory.AddFileToHistory(filename)
        self.Bind(wx.EVT_MENU_RANGE, self.OnFileHistory,
                  id=wx.ID_FILE1, id2=wx.ID_FILE9)
        keys = self.app.keys
        menu = self.fileMenu
        menu.Append(
            wx.ID_NEW,
            _translate("&New\t%s") % keys['new'])
        menu.Append(
            wx.ID_OPEN,
            _translate("&Open...\t%s") % keys['open'])
        menu.AppendSubMenu(
            self.recentFilesMenu,
            _translate("Open &Recent"))
        menu.Append(
            wx.ID_SAVE,
            _translate("&Save\t%s") % keys['save'],
            _translate("Save current experiment file"))
        menu.Append(
            wx.ID_SAVEAS,
            _translate("Save &as...\t%s") % keys['saveAs'],
            _translate("Save current experiment file as..."))
        exportMenu = menu.Append(
            -1,
            _translate("Export HTML...\t%s") % keys['exportHTML'],
            _translate("Export experiment to html/javascript file"))
        menu.Append(
            wx.ID_CLOSE,
            _translate("&Close file\t%s") % keys['close'],
            _translate("Close current experiment"))
        self.Bind(wx.EVT_MENU, self.app.newBuilderFrame, id=wx.ID_NEW)
        self.Bind(wx.EVT_MENU, self.fileExport, id=exportMenu.GetId())
        self.Bind(wx.EVT_MENU, self.fileSave, id=wx.ID_SAVE)
        menu.Enable(wx.ID_SAVE, False)
        self.Bind(wx.EVT_MENU, self.fileSaveAs, id=wx.ID_SAVEAS)
        self.Bind(wx.EVT_MENU, self.fileOpen, id=wx.ID_OPEN)
        self.Bind(wx.EVT_MENU, self.commandCloseFrame, id=wx.ID_CLOSE)
        item = menu.Append(
            wx.ID_PREFERENCES,
            _translate("&Preferences\t%s") % keys['preferences'])
        self.Bind(wx.EVT_MENU, self.app.showPrefs, item)

        self.fileMenu.AppendSeparator()
        self.fileMenu.Append(wx.ID_EXIT,
                             _translate("&Quit\t%s") % keys['quit'],
                             _translate("Terminate the program"))
        self.Bind(wx.EVT_MENU, self.quit, id=wx.ID_EXIT)

        # ------------- edit ------------------------------------
        self.editMenu = wx.Menu()
        menuBar.Append(self.editMenu, _translate('&Edit'))
        menu = self.editMenu
        self._undoLabel = menu.Append(wx.ID_UNDO,
                                      _translate("Undo\t%s") % keys['undo'],
                                      _translate("Undo last action"),
                                      wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.undo, id=wx.ID_UNDO)
        self._redoLabel = menu.Append(wx.ID_REDO,
                                      _translate("Redo\t%s") % keys['redo'],
                                      _translate("Redo last action"),
                                      wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.redo, id=wx.ID_REDO)
        menu.Append(wx.ID_PASTE, _translate("&Paste\t%s") % keys['paste'])
        self.Bind(wx.EVT_MENU, self.paste, id=wx.ID_PASTE)

        # ---_tools ---#000000#FFFFFF-----------------------------------------
        self.toolsMenu = wx.Menu()
        menuBar.Append(self.toolsMenu, _translate('&Tools'))
        menu = self.toolsMenu
        item = menu.Append(wx.ID_ANY,
                           _translate("Monitor Center"),
                           _translate("To set information about your monitor"))
        self.Bind(wx.EVT_MENU, self.app.openMonitorCenter, item)

        item = menu.Append(wx.ID_ANY,
                           _translate("Compile\t%s") % keys['compileScript'],
                           _translate("Compile the exp to a script"))
        self.Bind(wx.EVT_MENU, self.compileScript, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("Run\t%s") % keys['runScript'],
                           _translate("Run the current script"))
        self.Bind(wx.EVT_MENU, self.runFile, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("Stop\t%s") % keys['stopScript'],
                           _translate("Abort the current script"))
        self.Bind(wx.EVT_MENU, self.stopFile, item)

        menu.AppendSeparator()
        item = menu.Append(wx.ID_ANY,
                           _translate("PsychoPy updates..."),
                           _translate("Update PsychoPy to the latest, or a "
                                      "specific, version"))
        self.Bind(wx.EVT_MENU, self.app.openUpdater, item)
        if hasattr(self.app, 'benchmarkWizard'):
            item = menu.Append(wx.ID_ANY,
                               _translate("Benchmark wizard"),
                               _translate("Check software & hardware, generate "
                                          "report"))
            self.Bind(wx.EVT_MENU, self.app.benchmarkWizard, item)

        # ---_view---#000000#FFFFFF-------------------------------------------
        self.viewMenu = wx.Menu()
        menuBar.Append(self.viewMenu, _translate('&View'))
        menu = self.viewMenu

        item = menu.Append(wx.ID_ANY,
                           _translate("&Open Coder view\t%s") % keys[
                               'switchToCoder'],
                           _translate("Open a new Coder view"))
        self.Bind(wx.EVT_MENU, self.app.showCoder, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("&Toggle readme\t%s") % self.app.keys[
                               'toggleReadme'],
                           _translate("Toggle Readme"))
        self.Bind(wx.EVT_MENU, self.toggleReadme, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("&Flow Larger\t%s") % self.app.keys[
                               'largerFlow'],
                           _translate("Larger flow items"))
        self.Bind(wx.EVT_MENU, self.flowPanel.increaseSize, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("&Flow Smaller\t%s") % self.app.keys[
                               'smallerFlow'],
                           _translate("Smaller flow items"))
        self.Bind(wx.EVT_MENU, self.flowPanel.decreaseSize, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("&Routine Larger\t%s") % keys[
                               'largerRoutine'],
                           _translate("Larger routine items"))
        self.Bind(wx.EVT_MENU, self.routinePanel.increaseSize, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("&Routine Smaller\t%s") % keys[
                               'smallerRoutine'],
                           _translate("Smaller routine items"))
        self.Bind(wx.EVT_MENU, self.routinePanel.decreaseSize, item)

        # ---_experiment---#000000#FFFFFF-------------------------------------
        self.expMenu = wx.Menu()
        menuBar.Append(self.expMenu, _translate('&Experiment'))
        menu = self.expMenu
        item = menu.Append(wx.ID_ANY,
                           _translate("&New Routine\t%s") % keys['newRoutine'],
                           _translate("Create a new routine (e.g. the trial "
                                      "definition)"))
        self.Bind(wx.EVT_MENU, self.addRoutine, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("&Copy Routine\t%s") % keys[
                               'copyRoutine'],
                           _translate("Copy the current routine so it can be "
                                      "used in another exp"),
                           wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onCopyRoutine, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("&Paste Routine\t%s") % keys[
                               'pasteRoutine'],
                           _translate("Paste the Routine into the current "
                                      "experiment"),
                           wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onPasteRoutine, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("&Rename Routine\t%s") % keys[
                               'renameRoutine'],
                           _translate("Change the name of this routine"))
        self.Bind(wx.EVT_MENU, self.renameRoutine, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("Paste Component\t%s") % keys[
                               'pasteCompon'],
                           _translate(
                               "Paste the Component at bottom of the current "
                               "Routine"),
                           wx.ITEM_NORMAL)
        self.Bind(wx.EVT_MENU, self.onPasteCompon, item)
        menu.AppendSeparator()

        item = menu.Append(wx.ID_ANY,
                           _translate("Insert Routine in Flow"),
                           _translate(
                               "Select one of your routines to be inserted"
                               " into the experiment flow"))
        self.Bind(wx.EVT_MENU, self.flowPanel.onInsertRoutine, item)
        item = menu.Append(wx.ID_ANY,
                           _translate("Insert Loop in Flow"),
                           _translate("Create a new loop in your flow window"))
        self.Bind(wx.EVT_MENU, self.flowPanel.insertLoop, item)

        # ---_demos---#000000#FFFFFF------------------------------------------
        # for demos we need a dict where the event ID will correspond to a
        # filename

        self.demosMenu = wx.Menu()
        # unpack demos option
        menu = self.demosMenu
        item = menu.Append(wx.ID_ANY,
                           _translate("&Unpack Demos..."),
                           _translate(
                               "Unpack demos to a writable location (so that"
                               " they can be run)"))
        self.Bind(wx.EVT_MENU, self.demosUnpack, item)
        menu.AppendSeparator()
        # add any demos that are found in the prefs['demosUnpacked'] folder
        self.updateDemosMenu()
        menuBar.Append(self.demosMenu, _translate('&Demos'))

        # ---_onlineStudies---#000000#FFFFFF-------------------------------------------
        self.pavloviaMenu = pavlovia_ui.menu.PavloviaMenu(parent=self)
        menuBar.Append(self.pavloviaMenu, _translate("Pavlovia.org"))

        # ---_help---#000000#FFFFFF-------------------------------------------
        self.helpMenu = wx.Menu()
        menuBar.Append(self.helpMenu, _translate('&Help'))
        menu = self.helpMenu

        item = menu.Append(wx.ID_ANY,
                           _translate("&PsychoPy Homepage"),
                           _translate("Go to the PsychoPy homepage"))
        self.Bind(wx.EVT_MENU, self.app.followLink, item)
        self.app.urls[item.GetId()] = self.app.urls['psychopyHome']
        item = menu.Append(wx.ID_ANY,
                           _translate("&PsychoPy Builder Help"),
                           _translate(
                               "Go to the online documentation for PsychoPy"
                               " Builder"))
        self.Bind(wx.EVT_MENU, self.app.followLink, item)
        self.app.urls[item.GetId()] = self.app.urls['builderHelp']

        menu.AppendSeparator()
        menu.Append(wx.ID_ABOUT, _translate(
            "&About..."), _translate("About PsychoPy"))
        self.Bind(wx.EVT_MENU, self.app.showAbout, id=wx.ID_ABOUT)

        menu.AppendSeparator()

        item = menu.Append(wx.ID_ANY,
                           _translate("&News..."),
                           _translate("News"))
        self.Bind(wx.EVT_MENU, self.app.showNews, id=item.GetId())

        self.SetMenuBar(menuBar)

    def commandCloseFrame(self, event):
        """Defines Builder Frame Closing Event"""
        self.Close()

    def closeFrame(self, event=None, checkSave=True):
        """Defines Frame closing behavior, such as checking for file
           saving"""
        # close file first (check for save) but no need to update view
        okToClose = self.fileClose(updateViews=False, checkSave=checkSave)

        if not okToClose:
            if hasattr(event, 'Veto'):
                event.Veto()
            return
        else:
            # as of wx3.0 the AUI manager needs to be uninitialised explicitly
            self._mgr.UnInit()
            # is it the last frame?
            lastFrame = len(self.app.getAllFrames()) == 1
            quitting = self.app.quitting
            if lastFrame and sys.platform != 'darwin' and not quitting:
                self.app.quit(event)
            else:
                self.app.forgetFrame(self)
                self.Destroy()  # required

    def quit(self, event=None):
        """quit the app
        """
        self.app.quit(event)

    def fileNew(self, event=None, closeCurrent=True):
        """Create a default experiment (maybe an empty one instead)
        """
        # Note: this is NOT the method called by the File>New menu item.
        # That calls app.newBuilderFrame() instead
        if closeCurrent:  # if no exp exists then don't try to close it
            if not self.fileClose(updateViews=False):
                # close the existing (and prompt for save if necess)
                return False
        self.filename = 'untitled.psyexp'
        self.exp = experiment.Experiment(prefs=self.app.prefs)
        defaultName = 'trial'
        # create the trial routine as an example
        self.exp.addRoutine(defaultName)
        self.exp.flow.addRoutine(
            self.exp.routines[defaultName], pos=1)  # add it to flow
        # add it to user's namespace
        self.exp.namespace.add(defaultName, self.exp.namespace.user)
        routine = self.exp.routines[defaultName]
        ## add an ISI component by default
        # components = self.componentButtons.components
        # Static = components['StaticComponent']
        # ISI = Static(self.exp, parentName=defaultName, name='ISI',
        #             startType='time (s)', startVal=0.0,
        #             stopType='duration (s)', stopVal=0.5)
        # routine.addComponent(ISI)
        self.resetUndoStack()
        self.setIsModified(False)
        self.updateAllViews()

    def fileOpen(self, event=None, filename=None, closeCurrent=True):
        """Open a FileDialog, then load the file if possible.
        """
        if filename is None:
            _wld = "PsychoPy experiments (*.psyexp)|*.psyexp|Any file (*.*)|*"
            dlg = wx.FileDialog(self, message=_translate("Open file ..."),
                                style=wx.FD_OPEN | wx.FD_FILE_MUST_EXIST,
                                wildcard=_translate(_wld))
            if dlg.ShowModal() != wx.ID_OK:
                return 0
            filename = dlg.GetPath()
        # did user try to open a script in Builder?
        if filename.endswith('.py'):
            self.app.showCoder()  # ensures that a coder window exists
            self.app.coder.setCurrentDoc(filename)
            self.app.coder.setFileModified(False)
            return
        with WindowFrozen(ctrl=self):
            # try to pause rendering until all panels updated
            if closeCurrent:
                if not self.fileClose(updateViews=False):
                    # close the existing (and prompt for save if necess)
                    return False
            self.exp = experiment.Experiment(prefs=self.app.prefs)
            try:
                self.exp.loadFromXML(filename)
            except Exception:
                print(u"Failed to load {}. Please send the following to"
                      u" the PsychoPy user list".format(filename))
                traceback.print_exc()
                logging.flush()
            self.resetUndoStack()
            self.setIsModified(False)
            self.filename = filename
            # routinePanel.addRoutinePage() is done in
            # routinePanel.redrawRoutines(), called by self.updateAllViews()
            # update the views
            self.updateAllViews()  # if frozen effect will be visible on thaw
        self.updateReadme()
        self.fileHistory.AddFileToHistory(filename)
        self.htmlPath = None  # so we won't accidentally save to other html exp
        try:
            self.project = pavlovia.getProject(filename)
        except Exception as e:  # failed for
            self.project = None
            print(e)

    def fileSave(self, event=None, filename=None):
        """Save file, revert to SaveAs if the file hasn't yet been saved
        """
        if filename is None:
            filename = self.filename
        if filename.startswith('untitled'):
            if not self.fileSaveAs(filename):
                return False  # the user cancelled during saveAs
        else:
            filename = self.exp.saveToXML(filename)
            self.fileHistory.AddFileToHistory(filename)
        self.setIsModified(False)
        # if export on save then we should have an html file to update
        if self._getExportPref('on save') and os.path.split(filename)[0]:
            self.filename = filename
            self.fileExport(htmlPath=self.htmlPath)
        return True

    def fileSaveAs(self, event=None, filename=None):
        """Defines Save File as Behavior
        """
        shortFilename = self.getShortFilename()
        expName = self.exp.getExpName()
        if (not expName) or (shortFilename == expName):
            usingDefaultName = True
        else:
            usingDefaultName = False
        if filename is None:
            filename = self.filename
        initPath, filename = os.path.split(filename)

        _w = "PsychoPy experiments (*.psyexp)|*.psyexp|Any file (*.*)|*"
        if sys.platform != 'darwin':
            _w += '.*'
        wildcard = _translate(_w)
        returnVal = False
        dlg = wx.FileDialog(
            self, message=_translate("Save file as ..."), defaultDir=initPath,
            defaultFile=filename, style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT,
            wildcard=wildcard)

        if dlg.ShowModal() == wx.ID_OK:
            newPath = dlg.GetPath()
            # update exp name
            # if user has not manually renamed experiment
            if usingDefaultName:
                newShortName = os.path.splitext(
                    os.path.split(newPath)[1])[0]
                self.exp.setExpName(newShortName)
            # actually save
            self.fileSave(event=None, filename=newPath)
            self.filename = newPath
            returnVal = 1

        try:  # this seems correct on PC, but not on mac
            dlg.destroy()
        except Exception:
            pass

        self.updateWindowTitle()
        return returnVal

    def fileExport(self, event=None, htmlPath=None):
        """Exports the script as an HTML file (PsychoJS library)
        """
        # get path if not given one
        expPath, expName = os.path.split(self.filename)
        if htmlPath is None and self.exp.settings.params['HTML path']:
            htmlPath = self._getHtmlPath(self.filename)

        # present dialog box
        if htmlPath:
            dlg = ExportFileDialog(self, wx.ID_ANY,
                                   title=_translate("Export HTML file"),
                                   filePath=htmlPath,
                                   exp=self.exp)
            export = dlg.exportOnSave
            if self.exp.settings.params['exportHTML'].val == 'manually':
                retVal = dlg.ShowModal()
                self.exp.settings.params['exportHTML'].val = export.GetString(export.GetCurrentSelection())
                if retVal != wx.ID_OK:  # User cancelled export
                    return False

            htmlPath = os.path.join(htmlPath, expName.replace('.psyexp', '.js'))
            # then save the actual script
            self.generateScript(experimentPath=htmlPath,
                                target="PsychoJS")

    def getShortFilename(self):
        """returns the filename without path or extension
        """
        return os.path.splitext(os.path.split(self.filename)[1])[0]

    def updateReadme(self):
        """Check whether there is a readme file in this folder and try to show
        """
        # create the frame if we don't have one yet
        if not hasattr(self, 'readmeFrame') or self.readmeFrame is None:
            self.readmeFrame = ReadmeFrame(parent=self)
        # look for a readme file
        if self.filename and self.filename != 'untitled.psyexp':
            dirname = os.path.dirname(self.filename)
            possibles = glob.glob(os.path.join(dirname, 'readme*'))
            if len(possibles) == 0:
                possibles = glob.glob(os.path.join(dirname, 'Readme*'))
                possibles.extend(glob.glob(os.path.join(dirname, 'README*')))
            # still haven't found a file so use default name
            if len(possibles) == 0:
                self.readmeFilename = os.path.join(
                    dirname, 'readme.txt')  # use this as our default
            else:
                self.readmeFilename = possibles[0]  # take the first one found
        else:
            self.readmeFilename = None
        self.readmeFrame.setFile(self.readmeFilename)
        content = self.readmeFrame.ctrl.GetValue()
        if content and self.prefs['alwaysShowReadme']:
            self.showReadme()

    def showReadme(self, evt=None, value=True):
        """Shows Readme file
        """
        if not self.readmeFrame.IsShown():
            self.readmeFrame.Show(value)

    def toggleReadme(self, evt=None):
        """Toggles visibility of Readme file
        """
        if self.readmeFrame is None:
            self.updateReadme()
            self.showReadme()
        else:
            self.readmeFrame.toggleVisible()

    def OnFileHistory(self, evt=None):
        """get the file based on the menu ID
        """
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
            msg = _translate('Experiment %s has changed. Save before '
                             'quitting?') % self.filename
            dlg = dialogs.MessageDialog(self, msg, type='Warning')
            resp = dlg.ShowModal()
            if resp == wx.ID_CANCEL:
                return False  # return, don't quit
            elif resp == wx.ID_YES:
                if not self.fileSave():
                    return False  # user might cancel during save
            elif resp == wx.ID_NO:
                pass  # don't save just quit
        return True

    def fileClose(self, event=None, checkSave=True, updateViews=True):
        """This is typically only called when the user x
        """
        if checkSave:
            ok = self.checkSave()
            if not ok:
                return False  # user cancelled
        if self.filename is None:
            frameData = self.appData['defaultFrame']
        else:
            frameData = dict(self.appData['defaultFrame'])
            self.appData['prevFiles'].append(self.filename)

            # get size and window layout info
        if self.IsIconized():
            self.Iconize(False)  # will return to normal mode to get size info
            frameData['state'] = 'normal'
        elif self.IsMaximized():
            # will briefly return to normal mode to get size info
            self.Maximize(False)
            frameData['state'] = 'maxim'
        else:
            frameData['state'] = 'normal'
        frameData['auiPerspective'] = self._mgr.SavePerspective()
        frameData['winW'], frameData['winH'] = self.GetSize()
        frameData['winX'], frameData['winY'] = self.GetPosition()

        # truncate history to the recent-most last N unique files, where
        # N = self.fileHistoryMaxFiles, as defined in makeMenus()
        for ii in range(self.fileHistory.GetCount()):
            self.appData['fileHistory'].append(
                self.fileHistory.GetHistoryFile(ii))
        # fileClose gets calls multiple times, so remove redundancy
        # while preserving order; end of the list is recent-most:
        tmp = []
        fhMax = self.fileHistoryMaxFiles
        for f in self.appData['fileHistory'][-3 * fhMax:]:
            if f not in tmp:
                tmp.append(f)
        self.appData['fileHistory'] = copy.copy(tmp[-fhMax:])

        # assign the data to this filename
        self.appData['frames'][self.filename] = frameData
        # save the display data only for those frames in the history:
        tmp2 = {}
        for f in self.appData['frames']:
            if f in self.appData['fileHistory']:
                tmp2[f] = self.appData['frames'][f]
        self.appData['frames'] = copy.copy(tmp2)

        # close self
        self.routinePanel.removePages()
        self.filename = 'untitled.psyexp'
        # add the current exp as the start point for undo:
        self.resetUndoStack()
        if updateViews:
            self.updateAllViews()
        return 1

    def updateAllViews(self):
        """Updates Flow Panel, Routine Panel, and Window Title simultaneously
        """
        self.flowPanel.draw()
        self.routinePanel.redrawRoutines()
        self.updateWindowTitle()

    def updateWindowTitle(self, newTitle=None):
        """Defines behavior to update window Title
        """
        if newTitle is None:
            shortName = os.path.split(self.filename)[-1]
            newTitle = '%s - PsychoPy Builder' % (shortName)
        self.SetTitle(newTitle)

    def setIsModified(self, newVal=None):
        """Sets current modified status and updates save icon accordingly.

        This method is called by the methods fileSave, undo, redo,
        addToUndoStack and it is usually preferably to call those
        than to call this directly.

        Call with ``newVal=None``, to only update the save icon(s)
        """
        if newVal is None:
            newVal = self.getIsModified()
        else:
            self.isModified = newVal
        self.toolbar.EnableTool(self.bldrBtnSave.Id, newVal)
        self.fileMenu.Enable(wx.ID_SAVE, newVal)

    def getIsModified(self):
        """Checks if changes were made"""
        return self.isModified

    def resetUndoStack(self):
        """Reset the undo stack. do *immediately after* creating a new exp.

        Implicitly calls addToUndoStack() using the current exp as the state
        """
        self.currentUndoLevel = 1  # 1 is current, 2 is back one setp...
        self.currentUndoStack = []
        self.addToUndoStack()
        self.updateUndoRedo()
        self.setIsModified(newVal=False)  # update save icon if needed

    def addToUndoStack(self, action="", state=None):
        """Add the given ``action`` to the currentUndoStack, associated
        with the @state@. ``state`` should be a copy of the exp
        from *immediately after* the action was taken.
        If no ``state`` is given the current state of the experiment is used.

        If we are at end of stack already then simply append the action.  If
        not (user has done an undo) then remove orphan actions and append.
        """
        if state is None:
            state = copy.deepcopy(self.exp)
        # remove actions from after the current level
        if self.currentUndoLevel > 1:
            self.currentUndoStack = self.currentUndoStack[
                                    :-(self.currentUndoLevel - 1)]
            self.currentUndoLevel = 1
        # append this action
        self.currentUndoStack.append({'action': action, 'state': state})
        self.setIsModified(newVal=True)  # update save icon if needed
        self.updateUndoRedo()

    def undo(self, event=None):
        """Step the exp back one level in the @currentUndoStack@ if possible,
        and update the windows.

        Returns the final undo level (1=current, >1 for further in past)
        or -1 if redo failed (probably can't undo)
        """
        if self.currentUndoLevel >= len(self.currentUndoStack):
            return -1  # can't undo
        self.currentUndoLevel += 1
        state = self.currentUndoStack[-self.currentUndoLevel]['state']
        self.exp = copy.deepcopy(state)
        self.updateAllViews()
        self.setIsModified(newVal=True)  # update save icon if needed
        self.updateUndoRedo()

        return self.currentUndoLevel

    def redo(self, event=None):
        """Step the exp up one level in the @currentUndoStack@ if possible,
        and update the windows.
        
        Returns the final undo level (0=current, >0 for further in past)
        or -1 if redo failed (probably can't redo)
        """
        if self.currentUndoLevel <= 1:
            return -1  # can't redo, we're already at latest state
        self.currentUndoLevel -= 1
        self.exp = copy.deepcopy(
            self.currentUndoStack[-self.currentUndoLevel]['state'])
        self.updateUndoRedo()
        self.updateAllViews()
        self.setIsModified(newVal=True)  # update save icon if needed
        return self.currentUndoLevel

    def paste(self, event=None):
        """This receives paste commands for all child dialog boxes as well
        """
        foc = self.FindFocus()
        if hasattr(foc, 'Paste'):
            foc.Paste()

    def updateUndoRedo(self):
        """Defines Undo and Redo commands for the window
        """
        undoLevel = self.currentUndoLevel
        # check undo
        if undoLevel >= len(self.currentUndoStack):
            # can't undo if we're at top of undo stack
            label = _translate("Undo\t%s") % self.app.keys['undo']
            enable = False
        else:
            action = self.currentUndoStack[-undoLevel]['action']
            txt = _translate("Undo %(action)s\t%(key)s")
            fmt = {'action': action, 'key': self.app.keys['undo']}
            label = txt % fmt
            enable = True
        self._undoLabel.SetItemLabel(label)
        self.toolbar.EnableTool(self.bldrBtnUndo.Id, enable)
        self.editMenu.Enable(wx.ID_UNDO, enable)

        # check redo
        if undoLevel == 1:
            label = _translate("Redo\t%s") % self.app.keys['redo']
            enable = False
        else:
            action = self.currentUndoStack[-undoLevel + 1]['action']
            txt = _translate("Redo %(action)s\t%(key)s")
            fmt = {'action': action, 'key': self.app.keys['redo']}
            label = txt % fmt
            enable = True
        self._redoLabel.SetItemLabel(label)
        self.toolbar.EnableTool(self.bldrBtnRedo.Id, enable)
        self.editMenu.Enable(wx.ID_REDO, enable)

    def demosUnpack(self, event=None):
        """Get a folder location from the user and unpack demos into it
        """
        # choose a dir to unpack in
        dlg = wx.DirDialog(parent=self, message=_translate(
            "Location to unpack demos"))
        if dlg.ShowModal() == wx.ID_OK:
            unpackFolder = dlg.GetPath()
        else:
            return -1  # user cancelled
        # ensure it's an empty dir:
        if os.listdir(unpackFolder) != []:
            unpackFolder = os.path.join(unpackFolder, 'PsychoPy3 Demos')
            if not os.path.isdir(unpackFolder):
                os.mkdir(unpackFolder)
        mergeFolder(os.path.join(self.paths['demos'], 'builder'),
                    unpackFolder)
        self.prefs['unpackedDemosDir'] = unpackFolder
        self.app.prefs.saveUserPrefs()
        self.updateDemosMenu()

    def demoLoad(self, event=None):
        """Defines Demo Loading Event
        """
        fileDir = self.demos[event.GetId()]
        files = glob.glob(os.path.join(fileDir, '*.psyexp'))
        if len(files) == 0:
            print("Found no psyexp files in %s" % fileDir)
        else:
            self.fileOpen(event=None, filename=files[0], closeCurrent=True)

    def updateDemosMenu(self):
        """Updates Demos menu as needed
        """
        unpacked = self.prefs['unpackedDemosDir']
        if not unpacked:
            return
        # list available demos
        demoList = sorted(glob.glob(os.path.join(unpacked, '*')))
        self.demos = {wx.NewIdRef(): demoList[n]
                      for n in range(len(demoList))}
        for thisID in self.demos:
            junk, shortname = os.path.split(self.demos[thisID])
            if (shortname.startswith('_') or
                    shortname.lower().startswith('readme.')):
                continue  # ignore 'private' or README files
            self.demosMenu.Append(thisID, shortname)
            self.Bind(wx.EVT_MENU, self.demoLoad, id=thisID)

    def runFile(self, event=None):
        """Gets absolute path of experiment so it can be stored with data at end of
           the experiment run
        """
        if not os.path.exists(self.filename):
            self.fileSave(self.filename)
        fullPath = self.filename.replace('.psyexp', '_lastrun.py')
        self.generateScript(fullPath)  # Build script based on current version selected

        try:
            self.stdoutFrame.getText()
        except Exception:
            self.stdoutFrame = stdOutRich.StdOutFrame(
                parent=self, app=self.app, size=(700, 300))

        # redirect standard streams to log window
        sys.stdout = self.stdoutFrame
        sys.stderr = self.stdoutFrame

        # provide a running... message
        print("\n" + (" Running: %s " % (fullPath)).center(80, "#"))
        self.stdoutFrame.lenLastRun = len(self.stdoutFrame.getText())

        # self is the parent (which will receive an event when the process ends)
        self.scriptProcess = wx.Process(self)
        self.scriptProcess.Redirect()  # builder will receive the stdout/stdin

        if sys.platform == 'win32':
            # the quotes allow file paths with spaces
            command = '"%s" -u "%s"' % (sys.executable, fullPath)
            # self.scriptProcessID = wx.Execute(command, wx.EXEC_ASYNC,
            #   self.scriptProcess)
            if hasattr(wx, "EXEC_NOHIDE"):
                _opts = wx.EXEC_ASYNC | wx.EXEC_NOHIDE  # that hid console!
            else:
                _opts = wx.EXEC_ASYNC | wx.EXEC_SHOW_CONSOLE
        else:
            # for unix this signifies a space in a filename
            fullPath = fullPath.replace(' ', '\ ')
            # for unix this signifies a space in a filename
            pythonExec = sys.executable.replace(' ', '\ ')
            # the quotes would break a unix system command
            command = '%s -u %s' % (pythonExec, fullPath)
            _opts = wx.EXEC_ASYNC | wx.EXEC_MAKE_GROUP_LEADER
        # launch the command
        self.scriptProcessID = wx.Execute(command, _opts, self.scriptProcess)
        self.toolbar.EnableTool(self.bldrBtnRun.Id, False)
        self.toolbar.EnableTool(self.bldrBtnStop.Id, True)

    def stopFile(self, event=None):
        """Kills script processes"""
        self.app.terminateHubProcess()
        # try to kill it gently first
        success = wx.Kill(self.scriptProcessID, wx.SIGTERM)
        if success[0] != wx.KILL_OK:
            wx.Kill(self.scriptProcessID, wx.SIGKILL)  # kill it aggressively

    def onProcessEnded(self, event=None):
        """The script/exp has finished running
        """
        self.toolbar.EnableTool(self.bldrBtnRun.Id, True)
        self.toolbar.EnableTool(self.bldrBtnStop.Id, False)
        # update the output window and show it
        text = u""
        if self.scriptProcess.IsInputAvailable():
            text += extractText(self.scriptProcess.GetInputStream())
        if self.scriptProcess.IsErrorAvailable():
            text += extractText(self.scriptProcess.GetErrorStream())
        if len(text):
            # if some text hadn't yet been written (possible?)
            self.stdoutFrame.write(text)
        if len(self.stdoutFrame.getText()) > self.stdoutFrame.lenLastRun:
            self.stdoutFrame.Show()
            self.stdoutFrame.Raise()

        # then return stdout to its org location
        sys.stdout = self.stdoutOrig
        sys.stderr = self.stderrOrig
        self.scriptProcess.Destroy()

    def onCopyRoutine(self, event=None):
        """copy the current routine from self.routinePanel
        to self.app.copiedRoutine
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
        origName = self.app.copiedRoutine.name
        defaultName = self.exp.namespace.makeValid(origName)
        msg = _translate('New name for copy of "%(copied)s"?  [%(default)s]')
        vals = {'copied': origName, 'default': defaultName}
        message = msg % vals
        dlg = wx.TextEntryDialog(self, message=message,
                                 caption=_translate('Paste Routine'))
        if dlg.ShowModal() == wx.ID_OK:
            routineName = dlg.GetValue()
            newRoutine = copy.deepcopy(self.app.copiedRoutine)
            if not routineName:
                routineName = defaultName
            newRoutine.name = self.exp.namespace.makeValid(routineName)
            newRoutine.params['name'] = newRoutine.name
            self.exp.namespace.add(newRoutine.name)
            # add to the experiment
            self.exp.addRoutine(newRoutine.name, newRoutine)
            for newComp in newRoutine:  # routine == list of components
                newName = self.exp.namespace.makeValid(newComp.params['name'])
                self.exp.namespace.add(newName)
                newComp.params['name'].val = newName
            # could do redrawRoutines but would be slower?
            self.routinePanel.addRoutinePage(newRoutine.name, newRoutine)
            self.addToUndoStack("PASTE Routine `%s`" % newRoutine.name)
        dlg.Destroy()

    def onPasteCompon(self, event=None):
        """
        Paste the copied Component (if there is one) into the current
        Routine
        """
        routinePage = self.routinePanel.getCurrentPage()
        routinePage.pasteCompon()

    def onURL(self, evt):
        """decompose the URL of a file and line number"""
        # "C:\Program Files\wxPython...\samples\hangman\hangman.py"
        filename = evt.GetString().split('"')[1]
        lineNumber = int(evt.GetString().split(',')[1][5:])
        self.app.showCoder()
        self.app.coder.gotoLine(filename, lineNumber)

    def setExperimentSettings(self, event=None, timeout=None):
        """Defines ability to save experiment settings
        """
        component = self.exp.settings
        # does this component have a help page?
        if hasattr(component, 'url'):
            helpUrl = component.url
        else:
            helpUrl = None
        title = '%s Properties' % self.exp.getExpName()
        dlg = DlgExperimentProperties(frame=self, title=title,
                                      params=component.params,
                                      helpUrl=helpUrl, order=component.order,
                                      timeout=timeout)
        if dlg.OK:
            self.addToUndoStack("EDIT experiment settings")
            self.setIsModified(True)

    def addRoutine(self, event=None):
        """Defines ability to add routine in the routine panel
        """
        self.routinePanel.createNewRoutine()

    def renameRoutine(self, name, event=None, returnName=True):
        """Defines ability to rename routine in the routine panel
        """
        # get notebook details
        currentRoutine = self.routinePanel.getCurrentPage()
        currentRoutineIndex = self.routinePanel.GetPageIndex(currentRoutine)
        routine = self.routinePanel.GetPage(
            self.routinePanel.GetSelection()).routine
        oldName = routine.name
        msg = _translate("What is the new name for the Routine?")
        dlg = wx.TextEntryDialog(self, message=msg, value=oldName,
                                 caption=_translate('Rename'))
        exp = self.exp
        if dlg.ShowModal() == wx.ID_OK:
            name = dlg.GetValue()
            # silently auto-adjust the name to be valid, and register in the
            # namespace:
            name = exp.namespace.makeValid(
                name, prefix='routine')
            if oldName in self.exp.routines:
                # Swap old with new names
                self.exp.routines[oldName].name = name
                self.exp.routines[name] = self.exp.routines.pop(oldName)
                for comp in self.exp.routines[name]:
                    comp.parentName = name
                self.exp.namespace.rename(oldName, name)
                self.routinePanel.renameRoutinePage(currentRoutineIndex, name)
                self.addToUndoStack("`RENAME Routine `%s`" % oldName)
                dlg.Destroy()
                self.flowPanel.draw()

    def compileScript(self, event=None):
        """Defines compile script button behavior"""
        fullPath = self.filename.replace('.psyexp', '.py')
        self.generateScript(fullPath)
        self.app.showCoder()  # make sure coder is visible
        self.app.coder.fileNew(filepath=fullPath)
        self.app.coder.fileReload(event=None, filename=fullPath)

    def generateScript(self, experimentPath, target="PsychoPy"):
        """Generates python script from the current builder experiment"""
        if self.getIsModified():
            ok = self.fileSave(experimentPath)
            if not ok:
                return  # save file before compiling script
        self.exp.expPath = os.path.abspath(experimentPath)

        # Compile script from command line using version
        compiler = 'psychopy.scripts.psyexpCompile'

        if sys.platform == 'win32':  # get name of executable
            pythonExec = sys.executable
        else:
            pythonExec = sys.executable.replace(' ', '\ ')

        if not constants.PY3:  # encode path in Python2
            filename = self.filename.encode(sys.getfilesystemencoding())
            experimentPath = experimentPath.encode(sys.getfilesystemencoding())
        else:
            filename = self.filename

        # run compile
        cmd = [pythonExec, '-m', compiler, filename,
               '-o', experimentPath]
        # if version is not specified then don't touch useVersion at all
        version = self.exp.settings.params['Use version'].val
        if version not in [None, 'None', '', __version__]:
            cmd.extend(['-v', version])
            logging.info(' '.join(cmd))
            out = subprocess.check_output(cmd)
            if len(out):
                out = out.decode('utf-8-sig').split('\n')
                [print(line) for line in out] # so that any errors messages in compile are printed
        else:
            psyexpCompile.compileScript(infile=self.exp, version=None, outfile=experimentPath)

    def _getHtmlPath(self, filename):
        expPath = os.path.split(filename)[0]
        if not os.path.isdir(expPath):
            retVal = self.fileSave()
            if retVal:
                return self._getHtmlPath(self.filename)
            else:
                return False
        htmlFolder = self.exp.settings.params['HTML path'].val
        htmlPath = os.path.join(expPath, htmlFolder)
        return htmlPath

    def _getExportPref(self, pref):
        """Returns True if pref matches exportHTML preference"""
        if pref.lower() not in [prefs.lower() for prefs in self.exp.settings.params['exportHTML'].allowedVals]:
            raise ValueError("'{}' is not an allowed value for {}".format(pref, 'exportHTML'))
        exportHtml = str(self.exp.settings.params['exportHTML'].val).lower()
        if exportHtml == pref.lower():
            return True

    def onPavloviaSync(self, evt=None):
        if self._getExportPref('on sync'):
            self.fileExport(htmlPath=self._getHtmlPath(self.filename))

        self.enablePavloviaButton(['pavloviaSync', 'pavloviaRun'], False)
        try:
            pavlovia_ui.syncProject(parent=self, project=self.project)
            pavlovia.knownProjects.save()  # update projects.json
        finally:
            self.enablePavloviaButton(['pavloviaSync', 'pavloviaRun'], True)

    def onPavloviaRun(self, evt=None):
        if self._getExportPref('on save'):
            self.fileSave()
            pavlovia_ui.syncProject(parent=self, project=self.project,
                                    closeFrameWhenDone=False)
        elif self._getExportPref('on sync'):
            self.fileExport(htmlPath=self._getHtmlPath(self.filename))
            pavlovia_ui.syncProject(parent=self, project=self.project,
                                    closeFrameWhenDone=False)
        elif self._getExportPref('manually'):
            # Check htmlpath and projects exists
            noHtmlFolder = not os.path.isdir(self._getHtmlPath(self.filename))
            noProject = not bool(pavlovia.getProject(self.filename))
            if noHtmlFolder:
                self.fileExport()
            if noProject or noHtmlFolder:
                pavlovia_ui.syncProject(parent=self, project=self.project,
                                        closeFrameWhenDone=False)

        if self.project:
            self.project.pavloviaStatus = 'ACTIVATED'
            url = "https://pavlovia.org/run/{}/html".format(self.project.id)
            wx.LaunchDefaultBrowser(url)

    def enablePavloviaButton(self, buttons, enable):
        """
        Enables or disables Pavlovia buttons.

        Parameters
        ----------
        name: string, list
            Takes single buttons 'pavloviaSync', 'pavloviaRun', 'pavloviaSearch', 'pavloviaUser',
            or multiple buttons in string 'pavloviaSync, pavloviaRun',
            or comma separated list of strings ['pavloviaSync', 'pavloviaRun', ...].
        enable: bool
            True enables and False disables the button
        """
        if isinstance(buttons, str):
            buttons = buttons.split(',')
        for button in buttons:
            self.toolbar.EnableTool(self.btnHandles[button.strip(' ')].GetId(), enable)

    def setPavloviaUser(self, user):
        # TODO: update user icon on button to user avatar
        pass

    @property
    def project(self):
        """A PavloviaProject object if one is known for this experiment
        """
        if 'project' in self.__dict__ and self.__dict__['project']:
            return self.__dict__['project']
        elif self.filename and pavlovia.getProject(self.filename):
            return pavlovia.getProject(self.filename)
        else:
            return None

    @project.setter
    def project(self, project):
        self.__dict__['project'] = project


class ReadmeFrame(wx.Frame):
    """Defines construction of the Readme Frame"""

    def __init__(self, parent):
        """
        A frame for presenting/loading/saving readme files
        """
        self.parent = parent
        title = "%s readme" % (parent.exp.name)
        self._fileLastModTime = None
        pos = wx.Point(parent.Position[0] + 80, parent.Position[1] + 80)
        _style = wx.DEFAULT_FRAME_STYLE | wx.FRAME_FLOAT_ON_PARENT
        wx.Frame.__init__(self, parent, title=title,
                          size=(600, 500), pos=pos, style=_style)
        self.Bind(wx.EVT_CLOSE, self.onClose)
        self.Hide()
        self.makeMenus()
        self.ctrl = wx.TextCtrl(self, style=wx.TE_MULTILINE)

    def onClose(self, evt=None):
        """
        Defines behavior on close of the Readme Frame
        """
        self.parent.readmeFrame = None
        self.Destroy()

    def makeMenus(self):
        """Produces menus for the Readme Frame"""

        # ---Menus---#000000#FFFFFF-------------------------------------------
        menuBar = wx.MenuBar()
        # ---_file---#000000#FFFFFF-------------------------------------------
        self.fileMenu = wx.Menu()
        menuBar.Append(self.fileMenu, _translate('&File'))
        menu = self.fileMenu
        keys = self.parent.app.keys
        menu.Append(wx.ID_SAVE, _translate("&Save\t%s") % keys['save'])
        menu.Append(wx.ID_CLOSE,
                    _translate("&Close readme\t%s") % keys['close'])
        item = menu.Append(-1,
                           _translate("&Toggle readme\t%s") % keys[
                               'toggleReadme'],
                           _translate("Toggle Readme"))
        self.Bind(wx.EVT_MENU, self.toggleVisible, item)
        self.Bind(wx.EVT_MENU, self.fileSave, id=wx.ID_SAVE)
        self.Bind(wx.EVT_MENU, self.toggleVisible, id=wx.ID_CLOSE)
        self.SetMenuBar(menuBar)

    def setFile(self, filename):
        """Sets the readme file found with current builder experiment"""
        self.filename = filename
        self.expName = self.parent.exp.getExpName()
        # check we can read
        if filename is None:  # check if we can write to the directory
            return False
        elif not os.path.exists(filename):
            self.filename = None
            return False
        elif not os.access(filename, os.R_OK):
            msg = "Found readme file (%s) no read permissions"
            logging.warning(msg % filename)
            return False
        # attempt to open
        try:
            f = codecs.open(filename, 'r', 'utf-8-sig')
        except IOError as err:
            msg = ("Found readme file for %s and appear to have"
                   " permissions, but can't open")
            logging.warning(msg % self.expName)
            logging.warning(err)
            return False
            # attempt to read
        try:
            readmeText = f.read().replace("\r\n", "\n")
        except Exception:
            msg = ("Opened readme file for %s it but failed to read it "
                   "(not text/unicode?)")
            logging.error(msg % self.expName)
            return False
        f.close()
        self._fileLastModTime = os.path.getmtime(filename)
        self.ctrl.SetValue(readmeText)
        self.SetTitle("%s readme (%s)" % (self.expName, filename))

    def fileSave(self, evt=None):
        """Defines save behavior for readme frame"""
        mtime = os.path.getmtime(self.filename)
        if self._fileLastModTime and mtime > self._fileLastModTime:
            logging.warning(
                'readme file has been changed by another programme?')
        txt = self.ctrl.GetValue()
        with codecs.open(self.filename, 'w', 'utf-8-sig') as f:
            f.write(txt)

    def toggleVisible(self, evt=None):
        """Defines visibility toggle for readme frame"""
        if self.IsShown():
            self.Hide()
        else:
            self.Show()


class ExportFileDialog(wx.Dialog):
    def __init__(self, parent, ID, title, size=wx.DefaultSize,
                 pos=wx.DefaultPosition, style=wx.DEFAULT_DIALOG_STYLE,
                 filePath=None, exp=None):
        wx.Dialog.__init__(self, parent, ID, title,
                           size=size, pos=pos, style=style)
        # Now continue with the normal construction of the dialog
        # contents
        self.exp = exp
        sizer = wx.BoxSizer(wx.VERTICAL)
        msg = _translate("Warning, HTML outputs are very new.\n"
                         "Treat with caution (CHECK YOUR EXPERIMENT)!")
        warning = wx.StaticText(self, wx.ID_ANY, msg)
        warning.SetForegroundColour((200, 0, 0))
        sizer.Add(warning, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        box = wx.BoxSizer(wx.HORIZONTAL)

        label = wx.StaticText(self, wx.ID_ANY, _translate("Filepath:"))
        box.Add(label, 0, wx.ALIGN_CENTRE | wx.ALL, 5)
        if len(filePath) > 70:
            filePath = filePath[:20] + "....." + filePath[-40:]
        self.filePath = wx.StaticText(self, wx.ID_ANY, filePath, size=(500, -1))
        box.Add(self.filePath, 1, wx.ALIGN_CENTRE | wx.ALL, 5)

        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        # Set save on export HTML choice
        box = wx.BoxSizer(wx.HORIZONTAL)
        choices = ['on Save', 'on Sync', 'manually']
        exportLabel = _translate("Select 'manually' to receive this alert when exporting HTML.\n"
                                 "Click 'OK' to export HTML, or click 'Cancel' to return.")
        self.exportOnSave = wx.Choice(self, wx.ID_ANY,
                                      size=wx.DefaultSize,
                                      choices=choices)
        self.exportOnSave.SetSelection(choices.index(self.exp.settings.params['exportHTML']))
        self.exportText = wx.StaticText(self, wx.ID_ANY, exportLabel)
        self.exportOnSave.SetHelpText(exportLabel)
        box.Add(self.exportOnSave, .5, wx.ALIGN_CENTRE | wx.ALL, 5)
        box.Add(self.exportText, 1, wx.ALIGN_CENTRE | wx.ALL, 5)

        sizer.Add(box, 0, wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        line = wx.StaticLine(self, wx.ID_ANY, size=(20, -1),
                             style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0,
                  wx.GROW | wx.ALIGN_CENTER_VERTICAL | wx.RIGHT | wx.TOP, 5)

        btnsizer = wx.StdDialogButtonSizer()

        btn = wx.Button(self, wx.ID_OK)
        btn.SetHelpText("The OK button completes the dialog")
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetHelpText("The Cancel button cancels the dialog. (Crazy, huh?)")
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_CENTER_VERTICAL | wx.ALL, 5)

        self.SetSizerAndFit(sizer)


def extractText(stream):
    """Take a byte stream (or any file object of type b?) and return

    :param stream: stream from wx.Process or any byte stream from a file
    :return: text converted to unicode ready for appending to wx text view
    """
    if constants.PY3:
        return stream.read().decode('utf-8')
    else:
        return stream.read()
