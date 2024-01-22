#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Conditions-file preview and mini-editor for the Builder
"""
import os
import sys
import pickle
import wx
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
from pkg_resources import parse_version

from psychopy import gui
from psychopy.experiment.utils import valid_var_re
from psychopy.data.utils import _nonalphanumeric_re
from psychopy.localization import _translate

darkblue = wx.Colour(30, 30, 150, 255)
darkgrey = wx.Colour(65, 65, 65, 255)
white = wx.Colour(255, 255, 255, 255)


class DlgConditions(wx.Dialog):
    """Given a file or conditions, present values in a grid; view, edit, save.

    Accepts file name, list of lists, or list-of-dict
    Designed around a conditionsFile, but potentially more general.

    Example usage: from builder.DlgLoopProperties.viewConditions()
    edit new empty .pkl file:
        gridGUI = builder.DlgConditions(parent=self) # create and present Dlg
    edit existing .pkl file, loading from file (also for .csv or .xlsx):
        gridGUI = builder.DlgConditions(fileName=self.conditionsFile,
                                    parent=self, title=fileName)
    preview existing .csv or .xlsx file that has been loaded -> conditions:
        gridGUI = builder.DlgConditions(conditions, parent=self,
                                    title=fileName, fixed=True)

    To add columns, an instance of this class will instantiate a new instance
    having one more column. Doing so makes the return value from the first
    instance's showModal() meaningless. In order to update things like
    fileName and conditions, values are set in the parent, and should not be
    set based on showModal retVal.

    Author: Jeremy Gray, 2011
        adjusted for wx 3.x: Dec 2015
    """

    def __init__(self, grid=None, fileName=False, parent=None, title='',
                 trim=True, fixed=False, hasHeader=True, gui=True,
                 extraRows=0, extraCols=0,
                 clean=True, pos=wx.DefaultPosition, preview=True,
                 _restore=None, size=wx.DefaultSize,
                 style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT):
        self.parent = parent  # gets the conditionsFile info
        if parent:
            self.helpUrl = self.parent.app.urls['builder.loops']
        # read data from file, if any:
        self.defaultFileName = 'conditions.pkl'
        self.newFile = True
        if _restore:
            self.newFile = _restore[0]
            self.fileName = _restore[1]
        if fileName:
            grid = self.load(fileName)
            if grid:
                self.fileName = fileName
                self.newFile = False
            if not title:
                f = os.path.abspath(fileName)
                f = f.rsplit(os.path.sep, 2)[1:]
                f = os.path.join(*f)  # eg, BART/trialTypes.xlsx
                title = f
        elif not grid:
            title = _translate('New (no file)')
        elif _restore:
            if not title:
                f = os.path.abspath(_restore[1])
                f = f.rsplit(os.path.sep, 2)[1:]
                f = os.path.join(*f)  # eg, BART/trialTypes.xlsx
                title = f
        elif not title:
            title = _translate('Conditions data (no file)')
        # if got here via addColumn:
        # convert from conditions dict format:
        if grid and type(grid) == list and type(grid[0]) == dict:
            conditions = grid[:]
            numCond, numParam = len(conditions), len(conditions[0])
            grid = [list(conditions[0].keys())]
            for i in range(numCond):
                row = list(conditions[i].values())
                grid.append(row)
            hasHeader = True  # keys of a dict are the header
        # ensure a sensible grid, or provide a basic default:
        if not grid or not len(grid) or not len(grid[0]):
            grid = [[self.colName(0)], [u'']]
            hasHeader = True
            extraRows += 5
            extraCols += 3
        self.grid = grid  # grid is list of lists
        self.fixed = bool(fixed)
        if self.fixed:
            extraRows = extraCols = 0
            trim = clean = confirm = False
        else:
            style = style | wx.RESIZE_BORDER
        self.pos = pos
        self.title = title
        try:
            self.madeApp = False
            wx.Dialog.__init__(self, None, -1, title, pos, size, style)
        except wx._core.PyNoAppError:  # only needed during development?
            self.madeApp = True
            global app
            if parse_version(wx.__version__) < parse_version('2.9'):
                app = wx.PySimpleApp()
            else:
                app = wx.App(False)
            wx.Dialog.__init__(self, None, -1, title, pos, size, style)
        self.trim = trim
        self.warning = ''  # updated to warn about eg, trailing whitespace
        if hasHeader and not len(grid) > 1 and not self.fixed:
            self.grid.append([])
        self.clean = bool(clean)
        self.typeChoices = ['None', 'str', 'utf-8', 'int', 'long', 'float',
                            'bool', 'list', 'tuple', 'array']
        # make all rows have same # cols, extending as needed or requested:
        longest = max([len(r) for r in self.grid]) + extraCols
        for row in self.grid:
            for i in range(len(row), longest):
                row.append(u'')  # None
        # self.header <== row of input param name fields
        self.hasHeader = bool(hasHeader)
        self.rows = min(len(self.grid), 30)  # max 30 rows displayed
        self.cols = len(self.grid[0])
        if wx.version()[0] == '2':
            # extra row for explicit type drop-down
            extraRow = int(not self.fixed)
            self.sizer = wx.FlexGridSizer(self.rows + extraRow,
                                          self.cols + 1,  # +1 for labels
                                          vgap=0, hgap=0)
        else:
            self.sizer = wx.FlexGridSizer(cols=self.cols + 1, vgap=0, hgap=0)
        # set length of input box as the longest in the column (bounded):
        self.colSizes = []
        for x in range(self.cols):
            _size = [len(str(self.grid[y][x])) for y in range(self.rows)]
            self.colSizes.append(max([4] + _size))
        self.colSizes = [min(20, max(10, x + 1)) * 8 + 30 for x in self.colSizes]
        self.inputTypes = []  # explicit, as selected by user
        self.inputFields = []  # values in fields
        self.data = []

        # make header label, if any:
        if self.hasHeader:
            rowLabel = wx.StaticText(self, -1, label=_translate('Params:'),
                                     size=(6 * 9, 20))
            rowLabel.SetForegroundColour(darkblue)
            self.addRow(0, rowLabel=rowLabel)
        # make type-selector drop-down:
        if not self.fixed:
            if sys.platform == 'darwin':
                self.SetWindowVariant(variant=wx.WINDOW_VARIANT_SMALL)
            labelBox = wx.BoxSizer(wx.VERTICAL)
            tx = wx.StaticText(self, -1, label=_translate('type:'),
                               size=(5 * 9, 20))
            tx.SetForegroundColour(darkgrey)
            labelBox.Add(tx, 1, flag=wx.ALIGN_RIGHT)
            labelBox.AddSpacer(5)  # vertical
            self.sizer.Add(labelBox, 1, flag=wx.ALIGN_RIGHT)
            row = int(self.hasHeader)  # row to use for type inference
            for col in range(self.cols):
                # make each selector:
                typeOpt = wx.Choice(self, choices=self.typeChoices)
                # set it to best guess about the column's type:
                firstType = str(type(self.grid[row][col])).split("'", 2)[1]
                if firstType == 'numpy.ndarray':
                    firstType = 'array'
                if firstType == 'unicode':
                    firstType = 'utf-8'
                typeOpt.SetStringSelection(str(firstType))
                self.inputTypes.append(typeOpt)
                self.sizer.Add(typeOpt, 1)
            if sys.platform == 'darwin':
                self.SetWindowVariant(variant=wx.WINDOW_VARIANT_NORMAL)
        # stash implicit types for setType:
        self.types = []  # implicit types
        row = int(self.hasHeader)  # which row to use for type inference
        for col in range(self.cols):
            firstType = str(type(self.grid[row][col])).split("'")[1]
            self.types.append(firstType)
        # add normal row:
        for row in range(int(self.hasHeader), self.rows):
            self.addRow(row)
        for r in range(extraRows):
            self.grid.append([u'' for i in range(self.cols)])
            self.rows = len(self.grid)
            self.addRow(self.rows - 1)
        # show the GUI:
        if gui:
            self.show()
            self.Destroy()
        if self.madeApp:
            del(self, app)

    def colName(self, c, prefix='param_'):
        # generates 702 excel-style column names, A ... ZZ, with prefix
        abc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'  # for A, ..., Z
        aabb = [''] + [ch for ch in abc]  # for Ax, ..., Zx
        return prefix + aabb[c // 26] + abc[c % 26]

    def addRow(self, row, rowLabel=None):
        """Add one row of info, either header (col names) or normal data

        Adds items sequentially; FlexGridSizer moves to next row automatically
        """
        labelBox = wx.BoxSizer(wx.HORIZONTAL)
        if not rowLabel:
            if sys.platform == 'darwin':
                self.SetWindowVariant(variant=wx.WINDOW_VARIANT_SMALL)
            label = _translate('cond %s:') % str(
                row + 1 - int(self.hasHeader)).zfill(2)
            rowLabel = wx.StaticText(self, -1, label=label)
            rowLabel.SetForegroundColour(darkgrey)
            if sys.platform == 'darwin':
                self.SetWindowVariant(variant=wx.WINDOW_VARIANT_NORMAL)
        labelBox.Add(rowLabel, 1, flag=wx.ALIGN_BOTTOM)
        self.sizer.Add(labelBox, 1, flag=wx.ALIGN_CENTER)
        lastRow = []
        for col in range(self.cols):
            # get the item, as unicode for display purposes:
            if len(str(self.grid[row][col])):  # want 0, for example
                item = str(self.grid[row][col])
            else:
                item = u''
            # make a textbox:
            field = ExpandoTextCtrl(
                self, -1, item, size=(self.colSizes[col], 20))
            field.Bind(EVT_ETC_LAYOUT_NEEDED, self.onNeedsResize)
            field.SetMaxHeight(100)  # ~ 5 lines
            if self.hasHeader and row == 0:
                # add a default column name (header) if none provided
                header = self.grid[0]
                if item.strip() == '':
                    c = col
                    while self.colName(c) in header:
                        c += 1
                    field.SetValue(self.colName(c))
                field.SetForegroundColour(darkblue)  # dark blue
                # or (self.parent and
                if not valid_var_re.match(field.GetValue()):
                    # self.parent.exp.namespace.exists(field.GetValue()) ):
                    # was always red when preview .xlsx file -- in
                    # namespace already is fine
                    if self.fixed:
                        field.SetForegroundColour("Red")
                field.SetToolTip(wx.ToolTip(_translate(
                    'Should be legal as a variable name (alphanumeric)')))
                field.Bind(wx.EVT_TEXT, self.checkName)
            elif self.fixed:
                field.SetForegroundColour(darkgrey)
                field.SetBackgroundColour(white)

            # warn about whitespace unless will be auto-removed. invisible,
            # probably spurious:
            if (self.fixed or not self.clean) and item != item.strip():
                field.SetForegroundColour('Red')
                # also used in show():
                self.warning = _translate('extra white-space')
                field.SetToolTip(wx.ToolTip(self.warning))
            if self.fixed:
                field.Disable()
            lastRow.append(field)
            self.sizer.Add(field, 1)
        self.inputFields.append(lastRow)
        if self.hasHeader and row == 0:
            self.header = lastRow

    def checkName(self, event=None, name=None):
        """check param name (missing, namespace conflict, legal var name)
        disable save, save-as if bad name
        """
        if self.parent:
            if event:
                msg, enable = self.parent._checkName(event=event)
            else:
                msg, enable = self.parent._checkName(name=name)
        else:
            if (name and not valid_var_re.match(name)
                    or not valid_var_re.match(event.GetString())):
                msg, enable = _translate(
                    "Name must be alphanumeric or _, no spaces"), False
            else:
                msg, enable = "", True
        self.tmpMsg.SetLabel(msg)
        if enable:
            self.OKbtn.Enable()
            self.SAVEAS.Enable()
        else:
            self.OKbtn.Disable()
            self.SAVEAS.Disable()

    def userAddRow(self, event=None):
        """handle user request to add another row: add to the FlexGridSizer
        """
        self.grid.append([u''] * self.cols)
        self.rows = len(self.grid)
        self.addRow(self.rows - 1)
        self.tmpMsg.SetLabel('')
        self.onNeedsResize()

    def userAddCol(self, event=None):
        """adds a column by recreating the Dlg with size +1 one column wider.
        relaunching loses the retVal from OK, so use parent.fileName instead
        """
        self.relaunch(extraCols=1, title=self.title)

    def relaunch(self, **kwargs):
        self.trim = False  # dont remove blank rows / cols that user added
        self.getData(True)
        currentData = self.data[:]
        # launch new Dlg, but only after bail out of current one:
        if hasattr(self, 'fileName'):
            fname = self.fileName
        else:
            fname = None
        wx.CallAfter(DlgConditions, currentData,
                     _restore=(self.newFile, fname),
                     parent=self.parent, **kwargs)
        # bail from current Dlg:
        # retVal here, first one goes to Builder, ignore
        self.EndModal(wx.ID_OK)
        # self.Destroy() # -> PyDeadObjectError, so already handled hopefully

    def getData(self, typeSelected=False):
        """gets data from inputFields (unicode), converts to desired type
        """
        if self.fixed:
            self.data = self.grid
            return
        elif typeSelected:  # get user-selected explicit types of the columns
            self.types = []
            for col in range(self.cols):
                selected = self.inputTypes[col].GetCurrentSelection()
                self.types.append(self.typeChoices[selected])
        # mark empty columns for later removal:
        if self.trim:
            start = int(self.hasHeader)  # name is not empty, so ignore
            for col in range(self.cols):
                if not ''.join([self.inputFields[row][col].GetValue()
                                for row in range(start, self.rows)]):
                    self.types[col] = 'None'  # col will be removed below
        # get the data:
        self.data = []
        for row in range(self.rows):
            lastRow = []
            # remove empty rows
            fieldVals = [self.inputFields[row][col].GetValue()
                         for col in range(self.cols)]
            if self.trim and not ''.join(fieldVals):
                continue
            for col in range(self.cols):
                thisType = self.types[col]
                # trim 'None' columns, including header name:
                if self.trim and thisType in ['None']:
                    continue
                thisVal = self.inputFields[row][col].GetValue()
                if self.clean:
                    thisVal = thisVal.lstrip().strip()
                if thisVal:  # and thisType in ['list', 'tuple', 'array']:
                    while len(thisVal) and thisVal[-1] in "]), ":
                        thisVal = thisVal[:-1]
                    while len(thisVal) and thisVal[0] in "[(, ":
                        thisVal = thisVal[1:]

                if thisType not in ['str', 'utf-8']:
                    thisVal = thisVal.replace('\n', '')
                else:
                    thisVal = repr(thisVal)  # handles quoting ', ", ''' etc
                # convert to requested type:
                try:
                    # todo: replace exec() with eval()
                    if self.hasHeader and row == 0:
                        # header always str
                        val = self.inputFields[row][col].GetValue()
                        lastRow.append(str(val))
                    elif thisType in ['float', 'int', 'long']:
                        exec("lastRow.append(" + thisType +
                             '(' + thisVal + "))")
                    elif thisType in ['list']:
                        thisVal = thisVal.lstrip('[').strip(']')
                        exec("lastRow.append(" + thisType +
                             '([' + thisVal + "]))")
                    elif thisType in ['tuple']:
                        thisVal = thisVal.lstrip('(').strip(')')
                        if thisVal:
                            exec("lastRow.append((" +
                                 thisVal.strip(',') + ",))")
                        else:
                            lastRow.append(tuple(()))
                    elif thisType in ['array']:
                        thisVal = thisVal.lstrip('[').strip(']')
                        exec("lastRow.append(numpy.array" +
                             '("[' + thisVal + ']"))')
                    elif thisType in ['utf-8', 'bool']:
                        if thisType == 'utf-8':
                            thisType = 'unicode'
                        exec("lastRow.append(" + thisType +
                             '(' + thisVal + '))')
                    elif thisType in ['str']:
                        exec("lastRow.append(str(" + thisVal + "))")
                    elif thisType in ['file']:
                        exec("lastRow.append(repr(" + thisVal + "))")
                    else:
                        exec("lastRow.append(" + str(thisVal) + ')')
                except ValueError as msg:
                    print('ValueError:', msg, '; using unicode')
                    exec("lastRow.append(" + str(thisVal) + ')')
                except NameError as msg:
                    print('NameError:', msg, '; using unicode')
                    exec("lastRow.append(" + repr(thisVal) + ')')
            self.data.append(lastRow)
        if self.trim:
            # the corresponding data have already been removed
            while 'None' in self.types:
                self.types.remove('None')
        return self.data[:]

    def preview(self, event=None):
        self.getData(typeSelected=True)
        # in theory, self.data is also ok, because fixed
        previewData = self.data[:]
        # is supposed to never change anything, but bugs would be very subtle
        DlgConditions(previewData, parent=self.parent,
                      title=_translate('PREVIEW'), fixed=True)

    def onNeedsResize(self, event=None):
        self.SetSizerAndFit(self.border)  # do outer-most sizer
        if self.pos is None:
            self.Center()

    def show(self):
        """called internally; to display, pass gui=True to init
        """
        # put things inside a border:
        if wx.version()[0] == '2':
            # data matrix on top, buttons below
            self.border = wx.FlexGridSizer(2, 1)
        elif wx.version()[0] == '3':
            self.border = wx.FlexGridSizer(4)
        else:
            self.border = wx.FlexGridSizer(4, 1, wx.Size(0,0))
        self.border.Add(self.sizer, proportion=1,
                        flag=wx.ALL | wx.EXPAND, border=8)

        # add a message area, buttons:
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        if sys.platform == 'darwin':
            self.SetWindowVariant(variant=wx.WINDOW_VARIANT_SMALL)
        if not self.fixed:
            # placeholder for possible messages / warnings:
            self.tmpMsg = wx.StaticText(
                self, -1, label='', size=(350, 15), style=wx.ALIGN_RIGHT)
            self.tmpMsg.SetForegroundColour('Red')
            if self.warning:
                self.tmpMsg.SetLabel(self.warning)
            buttons.Add(self.tmpMsg, flag=wx.ALIGN_CENTER)
            buttons.AddSpacer(8)
            self.border.Add(buttons, 1, flag=wx.BOTTOM |
                            wx.ALIGN_CENTER, border=8)
            buttons = wx.BoxSizer(wx.HORIZONTAL)
            ADDROW = wx.Button(self, -1, _translate("+cond."))
            tip = _translate('Add a condition (row); to delete a condition,'
                             ' delete all of its values.')
            ADDROW.SetToolTip(wx.ToolTip(tip))
            ADDROW.Bind(wx.EVT_BUTTON, self.userAddRow)
            buttons.Add(ADDROW)
            buttons.AddSpacer(4)
            ADDCOL = wx.Button(self, -1, _translate("+param"))
            tip = _translate('Add a parameter (column); to delete a param, '
                             'set its type to None, or delete all of its values.')
            ADDCOL.SetToolTip(wx.ToolTip(tip))
            ADDCOL.Bind(wx.EVT_BUTTON, self.userAddCol)
            buttons.Add(ADDCOL)
            buttons.AddSpacer(4)
            PREVIEW = wx.Button(self, -1, _translate("Preview"))
            tip = _translate("Show all values as they would appear after "
                             "saving to a file, without actually saving anything.")
            PREVIEW.SetToolTip(wx.ToolTip(tip))
            PREVIEW.Bind(wx.EVT_BUTTON, self.preview)
            buttons.Add(PREVIEW)
            buttons.AddSpacer(4)
            self.SAVEAS = wx.Button(self, wx.FD_SAVE, _translate("Save as"))
            self.SAVEAS.Bind(wx.EVT_BUTTON, self.saveAs)
            buttons.Add(self.SAVEAS)
            buttons.AddSpacer(8)
            self.border.Add(buttons, 1, flag=wx.BOTTOM |
                            wx.ALIGN_RIGHT, border=8)
        if sys.platform == 'darwin':
            self.SetWindowVariant(variant=wx.WINDOW_VARIANT_NORMAL)
        buttons = wx.StdDialogButtonSizer()
        # help button if we know the url
        if self.helpUrl and not self.fixed:
            helpBtn = wx.Button(self, wx.ID_HELP, _translate(" Help "))
            helpBtn.SetToolTip(wx.ToolTip(_translate("Go to online help")))
            helpBtn.Bind(wx.EVT_BUTTON, self.onHelp)
            buttons.Add(helpBtn, wx.ALIGN_CENTER | wx.ALL)
            buttons.AddSpacer(12)
        # Add Okay and Cancel buttons
        self.OKbtn = wx.Button(self, wx.ID_OK, _translate(" OK "))
        if not self.fixed:
            self.OKbtn.SetToolTip(wx.ToolTip(_translate('Save and exit')))
        self.OKbtn.Bind(wx.EVT_BUTTON, self.onOK)
        self.OKbtn.SetDefault()
        if not self.fixed:
            buttons.AddSpacer(4)
            CANCEL = wx.Button(self, wx.ID_CANCEL, _translate(" Cancel "))
            CANCEL.SetToolTip(wx.ToolTip(
                _translate('Exit, discard any edits')))
            buttons.Add(CANCEL)
        else:
            CANCEL = None

        if sys.platform == "win32":
            btns = [self.OKbtn, CANCEL]
        else:
            btns = [CANCEL, self.OKbtn]

        if not self.fixed:
            btns.remove(btns.index(CANCEL))

        buttons.AddMany(btns)
        buttons.AddSpacer(8)
        buttons.Realize()
        self.border.Add(buttons, 1, flag=wx.BOTTOM | wx.ALIGN_RIGHT, border=8)

        # finally, its show time:
        self.SetSizerAndFit(self.border)
        if self.pos is None:
            self.Center()
        if self.ShowModal() == wx.ID_OK:
            # set self.data and self.types, from fields
            self.getData(typeSelected=True)
            self.OK = True
        else:
            self.data = self.types = None
            self.OK = False
        self.Destroy()

    def onOK(self, event=None):
        if not self.fixed:
            if not self.save():
                return  # disallow OK if bad param names
        event.Skip()  # handle the OK button event

    def saveAs(self, event=None):
        """save, but allow user to give a new name
        """
        self.newFile = True  # trigger query for fileName
        self.save()
        self.relaunch()  # to update fileName in title

    def save(self, event=None):
        """save header + row x col data to a pickle file
        """
        self.getData(True)  # update self.data
        adjustedNames = False
        for i, paramName in enumerate(self.data[0]):
            newName = paramName
            # ensure its legal as a var name, including namespace check:
            if self.parent:
                msg, enable = self.parent._checkName(name=paramName)
                if msg:  # msg not empty means a namespace issue
                    newName = self.parent.exp.namespace.makeValid(
                        paramName, prefix='param')
                    adjustedNames = True
            elif not valid_var_re.match(paramName):
                msg, enable = _translate(
                    "Name must be alphanumeric or _, no spaces"), False
                newName = _nonalphanumeric_re.sub('_', newName)
                adjustedNames = True
            else:
                msg, enable = "", True
            # try to ensure its unique:
            while newName in self.data[0][:i]:
                adjustedNames = True
                newName += 'x'  # might create a namespace conflict?
            self.data[0][i] = newName
            self.header[i].SetValue(newName)  # displayed value
        if adjustedNames:
            self.tmpMsg.SetLabel(_translate(
                'Param name(s) adjusted to be legal. Look ok?'))
            return False
        if hasattr(self, 'fileName') and self.fileName:
            fname = self.fileName
        else:
            self.newFile = True
            fname = self.defaultFileName
        if self.newFile or not os.path.isfile(fname):
            fullPath = gui.fileSaveDlg(initFilePath=os.path.split(fname)[0],
                                       initFileName=os.path.basename(fname),
                                       allowed="Pickle files (*.pkl)|*.pkl")
        else:
            fullPath = fname
        if fullPath:  # None if user canceled
            if not fullPath.endswith('.pkl'):
                fullPath += '.pkl'
            f = open(fullPath, 'w')
            pickle.dump(self.data, f)
            f.close()
            self.fileName = fullPath
            self.newFile = False
            # ack, sometimes might want relative path
            if self.parent:
                self.parent.conditionsFile = fullPath
        return True

    def load(self, fileName=''):
        """read and return header + row x col data from a pickle file
        """
        if not fileName:
            fileName = self.defaultFileName
        if not os.path.isfile(fileName):
            _base = os.path.basename(fileName)
            fullPathList = gui.fileOpenDlg(tryFileName=_base,
                                           allowed="All files (*.*)|*.*")
            if fullPathList:
                fileName = fullPathList[0]  # wx.MULTIPLE -> list
        if os.path.isfile(fileName) and fileName.endswith('.pkl'):
            f = open(fileName, 'rb')
            # Converting newline characters.
            # 'b' is necessary in Python3 because byte object is
            # returned when file is opened in binary mode.
            buffer = f.read().replace(b'\r\n',b'\n').replace(b'\r',b'\n')
            contents = pickle.loads(buffer)
            f.close()
            if self.parent:
                self.parent.conditionsFile = fileName
            return contents
        elif not os.path.isfile(fileName):
            print('file %s not found' % fileName)
        else:
            print('only .pkl supported at the moment')

    def asConditions(self):
        """converts self.data into self.conditions for TrialHandler.

        returns conditions
        """
        if not self.data or not self.hasHeader:
            if hasattr(self, 'conditions') and self.conditions:
                return self.conditions
            return
        self.conditions = []
        keyList = self.data[0]  # header = keys of dict
        for row in self.data[1:]:
            condition = {}
            for col, key in enumerate(keyList):
                condition[key] = row[col]
            self.conditions.append(condition)
        return self.conditions

    def onHelp(self, event=None):
        """similar to self.app.followLink() to self.helpUrl, but only use url
        """
        wx.LaunchDefaultBrowser(self.helpUrl)
