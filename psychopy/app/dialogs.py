#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""This is for general purpose dialogs/widgets, not particular functionality

MessageDialog:
    a drop-in replacement for wx message dialog (which was buggy on mac)
GlobSizer:
    built on top of GridBagSizer but with ability to add/remove
    rows. Needed for the ListWidget
ListWidget:
    takes a list of dictionaries (with identical fields) and allows
    the user to add/remove entries. e.g. expInfo control
"""

import wx
from wx.lib.newevent import NewEvent

from psychopy import logging
from psychopy.localization import _translate
from pkg_resources import parse_version


class MessageDialog(wx.Dialog):
    """For some reason the wx built-in message dialog has issues on macOS
    (buttons don't always work) so we need to use this instead.
    """

    def __init__(self, parent=None, message='', type='Warning', title=None,
                 timeout=None):
        # select and localize a title
        if not title:
            title = type
        labels = {'Warning': _translate('Warning'),
                  'Info': _translate('Info'),
                  'Query': _translate('Query')}
        try:
            label = labels[title]
        except Exception:
            label = title
        wx.Dialog.__init__(self, parent, -1, title=label)
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(wx.StaticText(self, -1, message), flag=wx.ALL, border=15)
        # add buttons
        if type == 'Warning':  # we need Yes,No,Cancel
            btnSizer = self.CreateStdDialogButtonSizer(flags=wx.YES | wx.NO | wx.CANCEL)
        elif type == 'Query':  # we need Yes,No
            btnSizer = self.CreateStdDialogButtonSizer(flags=wx.YES | wx.NO)
        elif type == 'Info':  # just an OK button
            btnSizer = self.CreateStdDialogButtonSizer(flags=wx.OK)
        else:
            raise NotImplementedError('Message type %s unknown' % type)
        for btn in btnSizer.GetChildren():
            if hasattr(btn.Window, "Bind"):
                btn.Window.Bind(wx.EVT_BUTTON, self.onButton)
        # configure sizers and fit
        sizer.Add(btnSizer,
                  flag=wx.ALL | wx.EXPAND, border=5)
        self.Center()
        self.SetSizerAndFit(sizer)
        self.timeout = timeout

    def onButton(self, event):
        self.EndModal(event.GetId())

    def onEscape(self, event):
        self.EndModal(wx.ID_CANCEL)

    def onEnter(self, event=None):
        self.EndModal(wx.ID_OK)

    def ShowModal(self):
        if self.timeout:
            timeout = wx.CallLater(self.timeout, self.onEnter)
            timeout.Start()
        return wx.Dialog.ShowModal(self)

# Event for GlobSizer-----------------------------------------------------
(GBSizerExLayoutEvent, EVT_GBSIZEREX_LAYOUT) = NewEvent()


class RichMessageDialog(wx.Dialog):
    def __init__(
            self,
            parent=None,
            message="",
            title="",
            size=(600, 500),
            style=wx.RESIZE_BORDER
    ):
        from psychopy.app.utils import MarkdownCtrl
        # initialise dialog
        wx.Dialog.__init__(
            self, parent,
            title=title,
            size=size,
            style=style
        )
        # setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.EXPAND | wx.ALL)
        # add markdown ctrl
        self.ctrl = MarkdownCtrl(
            self, value=message, style=wx.TE_READONLY
        )
        self.sizer.Add(self.ctrl, border=6, proportion=1, flag=wx.EXPAND | wx.ALL)
        # add OK button
        self.btns = self.CreateStdDialogButtonSizer(flags=wx.OK)
        self.border.Add(self.btns, border=12, flag=wx.EXPAND | wx.ALL)


class GlobSizer(wx.GridBagSizer):
    """This is a GridBagSizer that supports adding/removing/inserting rows and
    columns. It was found online, with not clear use license (public domain?).
    Appears to have been written by e.a.tacao <at> estadao.com.br
    """

    def __init__(self, *args, **kwargs):
        self.win = kwargs.pop("win", None)
        # This is here because we need to be able to find out whether a
        # row/col is growable. We also override the AddGrowableRow/Col and
        # RemoveGrowableRow/Col methods, as well as create new methods to
        # handle growable row/cols.
        self.growableRows = {}
        self.growableCols = {}
        wx.GridBagSizer.__init__(self, *args, **kwargs)

    def _resetSpan(self):
        # Unspans all spanned items; returns a reference to objects.
        objs = {}
        for item in self.GetChildren():
            span = item.GetSpan().Get()
            if span != (1, 1):
                objs[item.GetWindow()] = span
                item.SetSpan((1, 1))
        return objs

    def _setSpan(self, objs):
        # Respans all items containing the given objects.
        for obj, span in list(objs.items()):
            if obj:
                self.FindItem(obj).SetSpan(span)

    def GetClassName(self):
        return "GlobSizer"

    def GetAttributes(self):
        gap = self.GetGap()
        ecs = self.GetEmptyCellSize().Get()
        grows = self.GetGrowableRows()
        gcols = self.GetGrowableCols()
        return (gap, ecs, grows, gcols)

    def SetAttributes(self, attrs):
        gap, ecs, grows, gcols = attrs
        self.SetGap(gap)
        self.SetEmptyCellSize(ecs)
        [self.AddGrowableRow(row) for row in grows]
        [self.AddGrowableCol(col) for col in gcols]

    def Layout(self):
        wx.GridBagSizer.Layout(self)
        if self.win:
            wx.PostEvent(self.win, GBSizerExLayoutEvent(val=True))

    def SetGap(self, gap=(0, 0)):
        v, h = gap
        self.SetVGap(v)
        self.SetHGap(h)

    def GetGap(self):
        return self.GetVGap(), self.GetHGap()

    def AddGrowableRow(self, *args, **kwargs):
        idx = kwargs.get("idx", args[0])
        if not self.IsRowGrowable(idx):
            proportion = kwargs.get("proportion", (args + (0,))[1])
            self.growableRows[idx] = proportion
            wx.GridBagSizer.AddGrowableRow(self, idx, proportion)

    def AddGrowableCol(self, *args, **kwargs):
        idx = kwargs.get("idx", args[0])
        if not self.IsColGrowable(idx):
            proportion = kwargs.get("proportion", (args + (0,))[1])
            self.growableCols[idx] = proportion
            wx.GridBagSizer.AddGrowableCol(self, idx, proportion)

    def RemoveGrowableRow(self, idx):
        if self.IsRowGrowable(idx):
            del self.growableRows[idx]
            wx.GridBagSizer.RemoveGrowableRow(self, idx)

    def RemoveGrowableCol(self, idx):
        if self.IsColGrowable(idx):
            del self.growableCols[idx]
            wx.GridBagSizer.RemoveGrowableCol(self, idx)

    def IsRowGrowable(self, idx):
        return idx in self.growableRows

    def IsColGrowable(self, idx):
        return idx in self.growableCols

    def GetGrowableRows(self):
        grows = list(self.growableRows.keys())
        grows.sort()
        return grows

    def GetGrowableCols(self):
        gcols = list(self.growableCols.keys())
        gcols.sort()
        return gcols

    def FindUnspannedItemAtPosition(self, *args, **kwargs):
        # FindItemAtPosition(r, c) will return a valid spanned item
        # even if (r, c) is not its top-left position. This method will only
        # return a valid item (spanned or not*) if the position passed is the
        # top-left. (*As for unspanned items, obviously it'll always return a
        # valid item).
        item = self.FindItemAtPosition(*args, **kwargs)
        if item:
            if item.GetSpan().Get() > (1, 1):
                if item.GetPos() == kwargs.get("pos", args[0]):
                    r = item
                else:
                    r = None
            else:
                r = item
        else:
            r = None
        return r

    def GetItemPositions(self, *args, **kwargs):
        # Returns all positions occupied by a spanned item, as GetItemPosition
        # only returns its top-left position.
        row, col = self.GetItemPosition(*args, **kwargs).Get()
        rspan, cspan = self.GetItemSpan(*args, **kwargs).Get()
        return [(row + r, col + c)
                for r, c in [(r, c) for r in range(0, rspan)
                             for c in range(0, cspan)]]

    def InsertRow(self, row):
        # As for the vertically spanned objects in the given row,
        # we'll need to respan them later with an increased row span
        # (increased by 1 row).
        # 1. Get a reference of the vertically spanned objects on this row and
        #    their span, incrementing their row span by 1.
        _update_span = {}
        for c in range(0, self.GetCols()):
            item = self.FindItemAtPosition((row, c))
            if item:
                rs, cs = item.GetSpan().Get()
                if rs > 1 and item.GetPos().GetRow() != row:
                    _update_span[item.GetWindow()] = (rs + 1, cs)
        # 2. Unspan all objects.
        objs = self._resetSpan()
        # 3. Shift rows down.
        self.ShiftRowsDown(row)
        # 4. Respan all objects.
        objs.update(_update_span)
        self._setSpan(objs)
        # 5. Update references to growable rows.
        grows = list(self.growableRows.keys())
        for r in grows:
            if r >= row:
                self.RemoveGrowableRow(r)
                self.AddGrowableRow(r + 1)

    def InsertCol(self, col):
        # As for the horizontally spanned objects in the given col,
        # we'll need to respan them later with an increased col span
        # (increased by 1 col).
        # 1. Get a reference of the horizontally spanned objects on this col
        #    and their span, incrementing their col span by 1.
        _update_span = {}
        for r in range(0, self.GetRows()):
            item = self.FindItemAtPosition((r, col))
            if item:
                rs, cs = item.GetSpan().Get()
                if cs > 1 and item.GetPos().GetCol() != col:
                    _update_span[item.GetWindow()] = (rs, cs + 1)
        # 2. Unspan all objects.
        objs = self._resetSpan()
        # 3. Shift cols right.
        self.ShiftColsRight(col)
        # 4. Respan all objects.
        objs.update(_update_span)
        self._setSpan(objs)
        # 5. Update references to growable cols.
        gcols = list(self.growableCols.keys())
        for c in gcols:
            if c >= col:
                self.RemoveGrowableCol(c)
                self.AddGrowableCol(c + 1)

    def DeleteRow(self, row):
        """Deletes an entire row, destroying its objects (if any).
        """
        # As for the vertically spanned objects in the given row,
        # we'll need to move them somewhere safe (so that their objects
        # won't be destroyed as we destroy the row itself) and respan
        # them later with a reduced row span (decreased by 1 row).
        # 1. Get a reference of the vertically spanned objects on this row and
        #    their span, decrementing their row span by 1.
        _update_span = {}
        for c in range(0, self.GetCols()):
            item = self.FindItemAtPosition((row, c))
            if item:
                rs, cs = item.GetSpan().Get()
                if rs > 1:
                    _update_span[item.GetWindow()] = (rs - 1, cs)
        # 2. Unspan all objects.
        objs = self._resetSpan()
        # 3. Move the _update_span objects to an adjacent row somewhere safe.
        for obj in _update_span:
            item = self.FindItem(obj)
            org_r, org_c = item.GetPos().Get()
            if org_r == row:
                item.SetPos((org_r + 1, org_c))
        # 4. Destroy all objects on this row.
        for c in range(0, self.GetCols()):
            item = self.FindItemAtPosition((row, c))
            if item:
                obj = item.GetWindow()
                self.Detach(obj)
                obj.Destroy()
        # 5. Shift rows up.
        self.ShiftRowsUp(row + 1)
        # 6. Respan all objects.
        objs.update(_update_span)
        self._setSpan(objs)
        # 7. Update references to growable rows.
        grows = list(self.growableRows.keys())
        for r in grows:
            if r >= row:
                self.RemoveGrowableRow(r)
                if r > row:
                    self.AddGrowableRow(r - 1)

    def DeleteCol(self, col):
        """Deletes an entire col, destroying its objects (if any)."""
        # As for the horizontally spanned objects in the given col,
        # we'll need to move them somewhere safe (so that their objects
        # won't be destroyed as we destroy the row itself) and respan
        # them later with a reduced col span (decreased by 1 col).
        # 1. Get a reference of the horizontally spanned objects on this col
        #    and their span, decrementing their col span by 1.
        _update_span = {}
        for r in range(0, self.GetRows()):
            item = self.FindItemAtPosition((r, col))
            if item:
                rs, cs = item.GetSpan().Get()
                if cs > 1:
                    _update_span[item.GetWindow()] = (rs, cs - 1)
        # 2. Unspan all objects.
        objs = self._resetSpan()
        # 3. Move the _update_span objects to an adjacent col somewhere safe.
        for obj in _update_span:
            item = self.FindItem(obj)
            org_r, org_c = item.GetPos().Get()
            if org_c == col:
                item.SetPos((org_r, org_c + 1))
        # 4. Destroy all objects on this col.
        for r in range(0, self.GetRows()):
            item = self.FindItemAtPosition((r, col))
            if item:
                obj = item.GetWindow()
                self.Detach(obj)
                obj.Destroy()
        # 5. Shift cols left.
        self.ShiftColsLeft(col + 1)
        # 6. Respan all objects.
        objs.update(_update_span)
        self._setSpan(objs)
        # 7. Update references to growable cols.
        gcols = list(self.growableCols.keys())
        for c in gcols:
            if c >= col:
                self.RemoveGrowableCol(c)
                if c > col:
                    self.AddGrowableCol(c - 1)

    def ShiftRowsUp(self, startRow, endRow=None, startCol=None,
                    endCol=None):
        if endCol is None:
            endCol = self.GetCols()
        else:
            endCol += 1
        if endRow is None:
            endRow = self.GetRows()
        else:
            endRow += 1
        if startCol is None:
            startCol = 0
        for c in range(startCol, endCol):
            for r in range(startRow, endRow):
                item = self.FindItemAtPosition((r, c))
                if item:
                    w = item.GetWindow()
                    if w:
                        self.SetItemPosition(w, (r - 1, c))
                        w.Refresh()

    def ShiftRowsDown(self, startRow, endRow=None, startCol=None,
                      endCol=None):

        if endCol is None:
            endCol = self.GetCols()
        else:
            endCol += 1
        if endRow is None:
            endRow = self.GetRows()
        else:
            endRow += 1
        if startCol is None:
            startCol = 0
        for c in range(startCol, endCol):
            for r in range(endRow, startRow, -1):
                item = self.FindItemAtPosition((r, c))
                if item:
                    w = item.GetWindow()
                    if w:
                        self.SetItemPosition(w, (r + 1, c))
                        w.Refresh()

    def ShiftColsLeft(self, startCol, endCol=None, startRow=None,
                      endRow=None):
        if endCol is None:
            endCol = self.GetCols()
        else:
            endCol += 1
        if endRow is None:
            endRow = self.GetRows()
        else:
            endRow += 1
        if startRow is None:
            startRow = 0
        for r in range(startRow, endRow):
            for c in range(startCol, endCol):
                item = self.FindItemAtPosition((r, c))
                if item:
                    w = item.GetWindow()
                    if w:
                        self.SetItemPosition(w, (r, c - 1))
                        w.Refresh()

    def ShiftColsRight(self, startCol, endCol=None, startRow=None,
                       endRow=None):
        if endCol is None:
            endCol = self.GetCols()
        else:
            endCol += 1
        if endRow is None:
            endRow = self.GetRows()
        else:
            endRow += 1
        if startRow is None:
            startRow = 0
        for r in range(startRow, endRow):
            for c in range(endCol, startCol - 1, -1):
                item = self.FindItemAtPosition((r, c))
                if item:
                    w = item.GetWindow()
                    if w:
                        self.SetItemPosition(w, (r, c + 1))
                        w.Refresh()

    def DeleteEmptyRows(self):
        rows2delete = []
        for r in range(0, self.GetRows()):
            f = True
            for c in range(0, self.GetCols()):
                if self.FindItemAtPosition((r, c)) is not None:
                    f = False
            if f:
                rows2delete.append(r)
        for i in range(0, len(rows2delete)):
            self.ShiftRowsUp(rows2delete[i] + 1)
            rows2delete = [x - 1 for x in rows2delete]

    def DeleteEmptyCols(self):
        cols2delete = []
        for c in range(0, self.GetCols()):
            f = True
            for r in range(0, self.GetRows()):
                if self.FindItemAtPosition((r, c)) is not None:
                    f = False
            if f:
                cols2delete.append(c)
        for i in range(0, len(cols2delete)):
            self.ShiftColsLeft(cols2delete[i] + 1)
            cols2delete = [x - 1 for x in cols2delete]

    def Insert(self, *args, **kwargs):
        # Uses the API for the Add method, plus a kwarg named shiftDirection,
        # which controls whether rows should be shifted down (shiftDirection =
        # wx.VERTICAL) or left (shiftDirection = wx.HORIZONTAL).
        #
        # That kwarg is just a hint and won't force shifting; shifting
        # will only take place if the position passed is already occupied by
        # another control.
        #
        pos = kwargs.get("pos", args[1])
        shiftDirection = kwargs.pop("shiftDirection", wx.VERTICAL)
        if not self.FindItemAtPosition(pos):
            self.Add(*args, **kwargs)
        else:
            objs = self._resetSpan()
            r, c = pos
            if shiftDirection == wx.HORIZONTAL:
                self.ShiftColsRight(c, startRow=r, endRow=r)
            else:
                self.ShiftRowsDown(r, startCol=c, endCol=c)
            self.Add(*args, **kwargs)
            self._setSpan(objs)
        self.Layout()


class ListWidget(GlobSizer):
    """A widget for handling a list of dicts of identical structure.
    Has one row per entry and a +/- buttons at end to add/insert/remove from
    the list
    """

    def __init__(self, parent, value=None, order=None):
        """value should be a list of dictionaries with identical field names

        order should be used to specify the order in which the fields appear
        (left to right)
        """
        GlobSizer.__init__(self, hgap=2, vgap=2)
        self.parent = parent
        if value is None:
            value = [{'Field': "", 'Default': ""}]
        self.value = value
        if type(value) != list:
            msg = 'The initial value for a ListWidget must be a list of dicts'
            raise AttributeError(msg)
        # sort fieldNames using order information where possible
        allNames = list(self.value[0].keys())
        self.fieldNames = []
        if order is None:
            order = []
        for name in order:
            if name not in allNames:
                msg = ('psychopy.dialogs.ListWidget was given a field name '
                       '`%s` in order that was not in the dictionary')
                logging.error(msg % name)
                continue
            allNames.remove(name)
            self.fieldNames.append(name)
        # extend list by the remaining (no explicit order)
        self.fieldNames.extend(allNames)
        # set up controls
        self.createGrid()
        self.AddGrowableCol(0)
        self.AddGrowableCol(1)

    def createGrid(self):
        row = 0
        if len(self.fieldNames) > 0:
            for col, field in enumerate(self.fieldNames):
                self.Add(wx.StaticText(self.parent, -1, label=_translate(field)),
                         (row, col), flag=wx.ALL)
            for entry in self.value:
                row += 1
                self.addEntryCtrls(row, entry)
        self.Layout()

    def addEntryCtrls(self, row, entry):
        for col, field in enumerate(self.fieldNames):
            c = wx.TextCtrl(self.parent, -1, str(entry[field]))
            self.Add(c, (row, col), flag=wx.ALL | wx.EXPAND)
        plusBtn = wx.Button(self.parent, -1, '+', style=wx.BU_EXACTFIT)
        self.Add(plusBtn, (row, col + 1), flag=wx.ALL)
        plusBtn.Bind(wx.EVT_BUTTON, self.onAddElement)
        minusBtn = wx.Button(self.parent, -1, '-', style=wx.BU_EXACTFIT)
        self.Add(minusBtn, (row, col + 2), flag=wx.ALL)
        minusBtn.Bind(wx.EVT_BUTTON, self.onRemoveElement)

    def onAddElement(self, event):
        """The plus button has been pressed
        """
        btn = self.FindItem(event.GetEventObject())
        row, col = btn.GetPos()
        self.InsertRow(row)
        newEntry = {}
        for fieldName in self.fieldNames:
            newEntry[fieldName] = ""
        self.addEntryCtrls(row + 1, newEntry)
        self.Layout()
        self.parent.Fit()

    def onRemoveElement(self, event=None):
        """Called when the minus button is pressed.
        """
        btn = self.FindItem(event.GetEventObject())
        row, col = btn.GetPos()
        self.DeleteRow(row)
        self.Layout()
        self.parent.Fit()

    def getListOfDicts(self):
        """Retrieve the current list of dicts from the grid
        """
        currValue = []
        # skipping the first row (headers)
        for rowN in range(self.GetRows())[1:]:
            thisEntry = {}
            for colN, fieldName in enumerate(self.fieldNames):
                ctrl = self.FindItemAtPosition((rowN, colN)).GetWindow()
                thisEntry[fieldName] = ctrl.GetValue()
            currValue.append(thisEntry)
        return currValue

    def getValue(self):
        """
        Return value as a dict so it's label-agnostic.

        Returns
        -------
        dict
            key:value pairs represented by the two columns of this ctrl
        """
        currValue = {}
        # skipping the first row (headers)
        for rowN in range(self.GetRows())[1:]:
            keyCtrl = self.FindItemAtPosition((rowN, 0)).GetWindow()
            valCtrl = self.FindItemAtPosition((rowN, 1)).GetWindow()
            currValue[keyCtrl.GetValue()] = valCtrl.GetValue()
        return currValue

    def GetValue(self):
        """Provided for compatibility with other wx controls. Returns the
        current value of the list of dictionaries represented in the grid
        """
        return self.getListOfDicts()

    def SetValidator(self, validator):
        # Set Validator on every applicable child element
        for child in self.Children:
            if hasattr(child.Window, "SetValidator"):
                child.Window.SetValidator(validator)

    def Validate(self):
        # Call Validate on every applicable child element
        for child in self.Children:
            if hasattr(child.Window, "Validate"):
                child.Window.Validate()


if __name__ == '__main__':
    if parse_version(wx.__version__) < parse_version('2.9'):
        app = wx.PySimpleApp()
    else:
        app = wx.App(False)
    dlg = wx.Dialog(None)
    init = [{'Field': 'Participant', 'Default': ''},
            {'Field': 'Session', 'Default': '001'}]
    listCtrl = ListWidget(dlg, value=init, order=['Field', 'Default'])
    dlg.SetSizerAndFit(listCtrl)
    dlg.ShowModal()
