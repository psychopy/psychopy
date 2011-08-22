"""To build simple dialogues etc. (requires wxPython)
"""
# Part of the PsychoPy library
# Copyright (C) 2011 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).
from psychopy import log
#from wxPython import wx
import wx
import numpy
import string, os
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
import cPickle, re

OK = wx.ID_OK

_valid_var_re = re.compile(r"^[a-zA-Z_][\w]*$")  # filter for legal var names

class Dlg(wx.Dialog):
    """A simple dialogue box. You can add text or input boxes 
    (sequentially) and then retrieve the values.
    
    see also the function *dlgFromDict* for an **even simpler** version
    
    **Example:**    ::
        
        from psychopy import gui
        
        myDlg = gui.Dlg(title="JWP's experiment")
        myDlg.addText('Subject info')
        myDlg.addField('Name:')
        myDlg.addField('Age:', 21)
        myDlg.addText('Experiment Info')
        myDlg.addField('Grating Ori:',45)
        myDlg.show()#show dialog and wait for OK or Cancel
        if gui.OK:#then the user pressed OK
            thisInfo = myDlg.data
            print thisInfo
        else: print 'user cancelled'
    """
    def __init__(self,title='PsychoPy dialogue',
            pos=None, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT):
        style=style|wx.RESIZE_BORDER
        try:
            wx.Dialog.__init__(self, None,-1,title,pos,size,style)
        except:
            global app
            app = wx.PySimpleApp()
            wx.Dialog.__init__(self, None,-1,title,pos,size,style)
        self.inputFields = []
        self.inputFieldTypes= []
        self.inputFieldNames= []
        self.data = []
        #prepare a frame in which to hold objects
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        #self.addText('')#insert some space at top of dialogue
        if pos==None:
            self.Center()
    def addText(self, text, color=''):
        textLength = wx.Size(8*len(text)+16, 25)
        myTxt = wx.StaticText(self,-1,
                                label=text,
                                style=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL,
                                size=textLength)
        if len(color): myTxt.SetForegroundColour(color)
        self.sizer.Add(myTxt,1,wx.ALIGN_CENTER)
        
    def addField(self, label='', initial='', color='', tip=''):
        """
        Adds a (labelled) input field to the dialogue box, optional text color
        and tooltip. Returns a handle to the field (but not to the label).
        """
        self.inputFieldNames.append(label)
        self.inputFieldTypes.append(type(initial))
        if type(initial)==numpy.ndarray:
            initial=initial.tolist() #convert numpy arrays to lists
        container=wx.GridSizer(cols=2, hgap=10)
        #create label
        labelLength = wx.Size(9*len(label)+16,25)#was 8*until v0.91.4
        inputLabel = wx.StaticText(self,-1,label,
                                        size=labelLength,
                                        style=wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        if len(color): inputLabel.SetForegroundColour(color)
        container.Add(inputLabel, 1, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_RIGHT)
        #create input control
        if type(initial)==bool:
            inputBox = wx.CheckBox(self, -1)
            inputBox.SetValue(initial)
        else:
            inputLength = wx.Size(max(50, 5*len(unicode(initial))+16), 25)
            inputBox = wx.TextCtrl(self,-1,unicode(initial),size=inputLength)
        if len(color): inputBox.SetForegroundColour(color)
        if len(tip): inputBox.SetToolTip(wx.ToolTip(tip))
        
        container.Add(inputBox,1, wx.ALIGN_CENTER_VERTICAL)
        self.sizer.Add(container, 1, wx.ALIGN_CENTER)
        
        self.inputFields.append(inputBox)#store this to get data back on OK
        return inputBox
    
    def addFixedField(self,label='',value='',tip=''):
        """Adds a field to the dialogue box (like addField) but the field cannot
        be edited. e.g. Display experiment version. tool-tips are disabled (by wx).
        """
        thisField = self.addField(label,value,color='Gray',tip=tip)
        thisField.Disable() # wx disables tooltips too; we pass them in anyway
        return thisField
        
    def show(self):
        """Presents the dialog and waits for the user to press either OK or CANCEL.
        
        This function returns nothing.
        
        When they do, dlg.OK will be set to True or False (according to which
        button they pressed. If OK==True then dlg.data will be populated with a 
        list of values coming from each of the input fields created. 
        """
        #add buttons for OK and Cancel
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        OK = wx.Button(self, wx.ID_OK, " OK ")
        OK.SetDefault()
        buttons.Add(OK)
        CANCEL = wx.Button(self, wx.ID_CANCEL, " Cancel ")
        buttons.Add(CANCEL)
        self.sizer.Add(buttons,1,flag=wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM,border=5)
        
        self.SetSizerAndFit(self.sizer)
        if self.ShowModal() == wx.ID_OK:
            self.data=[]
            #get data from input fields
            for n in range(len(self.inputFields)):
                thisName = self.inputFieldNames[n]
                thisVal = self.inputFields[n].GetValue()
                thisType= self.inputFieldTypes[n]
                #try to handle different types of input from strings
                log.debug("%s: %s" %(self.inputFieldNames[n], unicode(thisVal)))
                if thisType in [tuple,list,float,int]:
                    #probably a tuple or list
                    exec("self.data.append("+thisVal+")")#evaluate it
                elif thisType==numpy.ndarray:
                    exec("self.data.append(numpy.array("+thisVal+"))")
                elif thisType in [str,unicode,bool]:
                    self.data.append(thisVal)
                else:
                    log.warning('unknown type:'+self.inputFieldNames[n])
                    self.data.append(thisVal)
            self.OK=True
        else: 
            self.OK=False
        self.Destroy()
        #    global app
        #self.myApp.Exit()
       


class DlgFromDict(Dlg):
    """Creates a dialogue box that represents a dictionary of values.
    Any values changed by the user are change (in-place) by this 
    dialogue box.
    e.g.: 
    
    ::
    
        info = {'Observer':'jwp', 'GratingOri':45, 'ExpVersion': 1.1}
        infoDlg = gui.DlgFromDict(dictionary=info, title='TestExperiment', fixed=['ExpVersion'])
        if infoDlg.OK:
            print info
        else: print 'User Cancelled'
        
    In the code above, the contents of *info* will be updated to the values
    returned by the dialogue box. 
    
    If the user cancels (rather than pressing OK),
    then the dictionary remains unchanged. If you want to check whether
    the user hit OK, then check whether DlgFromDict.OK equals
    True or False
    
    See GUI.py for a usage demo, including order and tip (tooltip).
    """
    def __init__(self, dictionary, title='',fixed=[], order=[], tip={}):
        Dlg.__init__(self, title)
        self.dictionary=dictionary
        keys = self.dictionary.keys()
        keys.sort()
        if len(order):
            keys = order + list(set(keys).difference(set(order)))
        types=dict([])
        for field in keys:
            #DEBUG: print field, type(dictionary[field])
            types[field] = type(self.dictionary[field])
            tooltip = ''
            if field in tip.keys(): tooltip = tip[field]
            if field in fixed:
                self.addFixedField(field,self.dictionary[field], tip=tooltip)
            else:
                self.addField(field,self.dictionary[field], tip=tooltip)
        #show it and collect data
        #tmp= wx.PySimpleApp()#this should have been done by Dlg ?
        self.show()
        if self.OK:
            for n,thisKey in enumerate(keys):
                self.dictionary[thisKey]=self.data[n]
        
class ConditionsDlg(wx.Dialog):
    """Given a file or conditions, present values in a grid; view, edit, save.
    
    Accepts file name, list of lists, or list-of-dict
    Designed around a conditionsFile, but potentially more general.
    
    Example usage: from builder.DlgLoopProperties.viewConditions()
    edit new empty .pkl file:
        gridGUI = gui.ConditionsDlg(parent=self) # create and present Dlg
    edit existing .pkl file, loading from file:
        gridGUI = gui.ConditionsDlg(fileName=self.conditionsFile,
                                    parent=self, title=fileName)
    preview existing .csv or .xlsx file that has already been loaded -> conditions:
        gridGUI = gui.ConditionsDlg(conditions, parent=self, 
                                    title=fileName, fixed=True)
    
    Maybe this class should be in builder.py, not in gui.py
    
    To add columns, an instance of this class will instantiate a new instance
    having one more column. Doing so makes the return value from the first instance's
    showModal() meaningless. In order to update things like fileName and conditions,
    values are set in the parent, and should not be set based on showModal retVal.
    
    Author: Jeremy Gray, 2011
    """
    def __init__(self, grid=None, fileName=False, parent=None, title='',
            trim=True, fixed=False, header=True, gui=True, extraRows=0, extraCols=0,
            clean=True, pos=None, preview=True,
            _restore=None, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT):
        self.parent = parent # gets the conditionsFile info
        self.helpUrl = 'http://www.psychopy.org/builder/flow.html#loops'
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
                f = f.rsplit(os.path.sep,2)[1:]
                f = os.path.join(*f) # eg, BART/trialTypes.xlsx
                title = f
        elif not grid:
            title = 'New (no file)'
        elif _restore:
            if not title:
                f = os.path.abspath(_restore[1])
                f = f.rsplit(os.path.sep,2)[1:]
                f = os.path.join(*f) # eg, BART/trialTypes.xlsx
                title = f
        elif not title:
            title = 'Conditions data (no file)'
        # if got here via addColumn:
        # convert from conditions dict format:
        if grid and type(grid) == list and type(grid[0]) == dict:
            conditions = grid[:]
            numCond, numParam = len(conditions), len(conditions[0])
            grid = [conditions[0].keys()]
            for i in xrange(numCond):
                row = conditions[i].values()
                grid.append(row)
            header=True # keys of a dict are the header
        # ensure a sensible grid, or provide a basic default:
        if not grid or not len(grid) or not len(grid[0]):
            grid = [[self.colName(0)], [u'']]
            header = True
            extraRows += 5
            extraCols += 3
        self.grid = grid # grid is list of lists
        self.fixed = bool(fixed)
        if self.fixed:
            extraRows = extraCols = 0
            trim = clean = confirm = False
        else:
            style = style|wx.RESIZE_BORDER
        self.pos = pos
        self.title = title
        try:
            self.madeApp = False
            wx.Dialog.__init__(self, None,-1,title,pos,size,style)
        except: # only needed during development?
            self.madeApp = True
            global app
            app = wx.PySimpleApp()
            wx.Dialog.__init__(self, None,-1,title,pos,size,style)
        self.trim = trim
        self.warning = '' # updated to warn about eg, trailing whitespace
        if header and not len(grid) > 1 and not self.fixed:
            self.grid.append([])
        self.clean = bool(clean)
        self.typeChoices = ['None', 'str', 'utf-8', 'int', 'long', 'float',
                            'bool', 'list', 'tuple', 'array']
        # make all rows have same # cols, extending as needed or requested:
        longest = max([len(r) for r in self.grid]) + extraCols
        for row in self.grid:
            for i in range(len(row),longest):
                row.append(u'') # None
        self.hasHeader = bool(header)
        self.rows = min(len(self.grid), 30) # max 30 rows displayed
        self.cols = len(self.grid[0])
        extraRow = int(not self.fixed) # extra row for explicit type drop-down
        self.sizer = wx.FlexGridSizer(self.rows+extraRow, self.cols+1, # +1 for condition labels
                                      vgap=0, hgap=0) 
        # set length of input box as the longest in the column (bounded):
        self.colSizes = []
        for x in range(self.cols):
            self.colSizes.append( max([4] +
                [len(unicode(self.grid[y][x])) for y in range(self.rows)]) )
        self.colSizes = map(lambda x: min(20, max(9, x+1)) * 8.5, self.colSizes)
        self.inputTypes = [] # explicit, as selected by user via type-selector
        self.inputFields = [] # values in fields
        self.data = []
        
        # make header label, if any:
        if self.hasHeader:
            rowLabel = wx.StaticText(self,-1,label='Params:', size=(6*9, 20))
            rowLabel.SetForegroundColour(wx.Color(30,30,150,255))
            self.addRow(0, rowLabel=rowLabel)
        # make type-selector drop-down:
        if not self.fixed:
            self.SetWindowVariant(variant=wx.WINDOW_VARIANT_SMALL) # mac only
            labelBox = wx.BoxSizer(wx.VERTICAL)
            tx = wx.StaticText(self,-1,label='type:', size=(5*9,20))
            tx.SetForegroundColour('Gray')
            labelBox.Add(tx,1,flag=wx.ALIGN_RIGHT)
            labelBox.AddSpacer(5) # vertical
            self.sizer.Add(labelBox,1,flag=wx.ALIGN_RIGHT)
            row = int(self.hasHeader) # row to use for type inference
            for col in range(self.cols):
                # make each selector:
                typeOpt = wx.Choice(self, choices=self.typeChoices)
                # set it to best guess about the column's type:
                firstType = str(type(self.grid[row][col])).split("'",2)[1]
                if firstType=='numpy.ndarray':
                    firstType = 'array'
                if firstType=='unicode':
                    firstType = 'utf-8'
                typeOpt.SetStringSelection(str(firstType))
                self.inputTypes.append(typeOpt)
                self.sizer.Add(typeOpt, 1)
            self.SetWindowVariant(variant=wx.WINDOW_VARIANT_NORMAL)
        # stash implicit types for setType:
        self.types = [] # implicit types
        row = int(self.hasHeader) # which row to use for type inference
        for col in range(self.cols):
            firstType = str(type(self.grid[row][col])).split("'")[1]
            self.types.append(firstType)
        # add normal row:
        for row in range(int(self.hasHeader), self.rows):
            self.addRow(row)
        for r in range(extraRows):
            self.grid.append([ u'' for i in range(self.cols)])
            self.rows = len(self.grid)
            self.addRow(self.rows-1)
        # show the GUI:
        if gui:
            self.show()
            self.Destroy()
        if self.madeApp:
            del(self, app)

    def colName(self, c, prefix='param_'):
        # generates 702 excel-style column names, A ... ZZ, with prefix
        abc = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ' # for A, ..., Z
        aabb = [''] + [ch for ch in abc] # for Ax, ..., Zx
        return prefix + aabb[c//26] + abc[c%26]
    def addRow(self, row, rowLabel=None):
        """Add one row of info, either header (col names) or normal data
        
        Adds items sequentially; FlexGridSizer moves to next row automatically
        """
        labelBox = wx.BoxSizer(wx.HORIZONTAL)
        if not rowLabel:
            self.SetWindowVariant(variant=wx.WINDOW_VARIANT_SMALL)
            label = 'cond %s:'%str(row+1-int(self.hasHeader)).zfill(2)
            rowLabel = wx.StaticText(self, -1, label=label)
            rowLabel.SetForegroundColour('Gray')
            self.SetWindowVariant(variant=wx.WINDOW_VARIANT_NORMAL)
        labelBox.Add(rowLabel, 1, flag=wx.ALIGN_RIGHT|wx.ALIGN_BOTTOM)
        self.sizer.Add(labelBox, 1, flag=wx.ALIGN_CENTER)
        lastRow = []
        for col in range(self.cols):
            # get the item, as unicode for display purposes:
            if len(unicode(self.grid[row][col])): # want 0, for example
                item = unicode(self.grid[row][col])
            else:
                item = u''
            # make a textbox:
            field = ExpandoTextCtrl(self, -1, item, size=(self.colSizes[col],20))
            field.Bind(EVT_ETC_LAYOUT_NEEDED, self.onNeedsResize)
            field.SetMaxHeight(100) # ~ 5 lines
            if self.hasHeader and row==0:
                # add a default column name (header) if none provided
                header = self.grid[0]
                if item.strip() == '':
                    c = col
                    while self.colName(c) in header:
                        c += 1
                    field.SetValue(self.colName(c))
                if not _valid_var_re.match(field.GetValue()) or (self.parent and
                        self.parent.exp.namespace.exists(field.GetValue()) ):
                    field.SetForegroundColour("Red")
                else:
                    field.SetForegroundColour((30,30,150)) #dark blue
                field.SetToolTip(wx.ToolTip('Should be legal as a variable name (alphanumeric)'))
                field.Bind(wx.EVT_TEXT, self.checkName)
            elif self.fixed:
                field.SetForegroundColour('Gray')

            # warn about whitespace unless will be auto-removed. invisible, probably spurious:
            if (self.fixed or not self.clean) and item != item.lstrip().strip():
                field.SetForegroundColour('Red')
                self.warning = 'extra white-space' # also used in show()
                field.SetToolTip(wx.ToolTip(self.warning))
            if self.fixed:
                field.Disable()
            lastRow.append(field)
            self.sizer.Add(field, 1)
        self.inputFields.append(lastRow)
        if self.hasHeader and row==0:
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
            if (name and not _valid_var_re.match(name)
                or not _valid_var_re.match(event.GetString()) ):
                msg, enable = "Name must be alpha-numeric or _, no spaces", False
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
        """handle user request to add another row: just add to the FlexGridSizer
        """
        self.grid.append([ u''] * self.cols)
        self.rows = len(self.grid)
        self.addRow(self.rows-1)
        self.tmpMsg.SetLabel('')
        self.onNeedsResize()
    def userAddCol(self, event=None):
        """adds a column by recreating the Dlg with a wider size one more column
        relaunch loses the retVal from OK, so use parent.fileName not OK for exit status
        """
        self.relaunch(kwargs={'extraCols':1, 'title':self.title})
    def relaunch(self, kwargs={}):
        self.trim = False # avoid removing blank rows / cols that user has added
        self.getData(True)
        currentData = self.data[:]
        # launch new Dlg, but only after bail out of current one:
        if hasattr(self, 'fileName'): fname = self.fileName
        else: fname = None
        wx.CallAfter(ConditionsDlg, currentData, _restore=(self.newFile,fname),
                     parent=self.parent, **kwargs)
        # bail from current Dlg:
        self.EndModal(wx.ID_OK) # retVal here, first one goes to Builder, ignore
        #self.Destroy() # -> PyDeadObjectError, so already handled hopefully
    def getData(self, typeSelected=False):
        """gets data from inputFields (unicode), converts to desired type
        """
        if self.fixed:
            self.data = self.grid
            return
        elif typeSelected: # get user-selected explicit types of the columns
            self.types = []
            for col in range(self.cols):
                selected = self.inputTypes[col].GetCurrentSelection()
                self.types.append(self.typeChoices[selected])
        # mark empty columns for later removal:
        if self.trim:
            start = int(self.hasHeader) # name is not empty, so ignore
            for col in range(self.cols):
                if not ''.join([self.inputFields[row][col].GetValue()
                                for row in range(start, self.rows)]):
                    self.types[col] = 'None' # col will be removed below
        # get the data:
        self.data = []
        for row in range(self.rows):
            lastRow = []
            # remove empty rows
            if self.trim and not ''.join([self.inputFields[row][col].GetValue()
                                          for col in range(self.cols)]):
                continue
            for col in range(self.cols):
                thisType = self.types[col]
                # trim 'None' columns, including header name:
                if self.trim and thisType in ['None']:
                    continue
                thisVal = self.inputFields[row][col].GetValue()
                if self.clean:
                    thisVal = thisVal.lstrip().strip()
                if thisVal:# and thisType in ['list', 'tuple', 'array']:
                    while len(thisVal) and thisVal[-1] in "]), ":
                        thisVal = thisVal[:-1]
                    while len(thisVal) and thisVal[0] in "[(, ":
                        thisVal = thisVal[1:]
                
                if thisType not in ['str', 'utf-8']:
                    thisVal = thisVal.replace('\n', '')
                else:
                    thisVal = repr(thisVal) # handles quoting ', ", ''' etc
                # convert to requested type:
                try:
                    if self.hasHeader and row==0:
                        lastRow.append(str(self.inputFields[row][col].GetValue())) # header always str
                    elif thisType in ['float','int', 'long']:
                        exec("lastRow.append("+thisType+'('+thisVal+"))")
                    elif thisType in ['list']:
                        thisVal = thisVal.lstrip('[').strip(']')
                        exec("lastRow.append("+thisType+'(['+thisVal+"]))")
                    elif thisType in ['tuple']:
                        thisVal = thisVal.lstrip('(').strip(')')
                        if thisVal:
                            exec("lastRow.append(("+thisVal.strip(',')+",))")
                        else:
                            lastRow.append(tuple(()))
                    elif thisType in ['array']:
                        thisVal = thisVal.lstrip('[').strip(']')
                        exec("lastRow.append(numpy.array"+'("['+thisVal+']"))')
                    elif thisType in ['utf-8', 'bool']:
                        if thisType=='utf-8': thisType='unicode'
                        exec("lastRow.append("+thisType+'('+thisVal+'))')
                    elif thisType in ['str']:
                        exec("lastRow.append(str("+thisVal+"))")
                    elif thisType in ['file']:
                        exec("lastRow.append(repr("+thisVal+"))")
                    else: #if thisType in ['NoneType']:
                        #assert False, 'programer error, unknown type: '+thisType
                        exec("lastRow.append("+unicode(thisVal)+')')
                except ValueError, msg:
                    print 'ValueError:', msg, '; using unicode'
                    exec("lastRow.append("+unicode(thisVal)+')')
                except NameError, msg:
                    print 'NameError:', msg, '; using unicode'
                    exec("lastRow.append("+repr(thisVal)+')')
            self.data.append(lastRow)
        if self.trim:
            # the corresponding data have already been removed
            while 'None' in self.types:
                self.types.remove('None')
        return self.data[:]
    
    def preview(self,event=None):
        self.getData(typeSelected=True)
        previewData = self.data[:] # in theory, self.data is also ok, because fixed
            # is supposed to never change anything, but bugs would be very subtle
        ConditionsDlg(previewData, parent=self.parent, title='PREVIEW', fixed=True)
    def onNeedsResize(self, event=None):
        self.SetSizerAndFit(self.border) # do outer-most sizer
        if self.pos==None: self.Center()
    def show(self):
        """called internally; to display, pass gui=True to init
        """
        # put things inside a border:
        self.border = wx.FlexGridSizer(2,1) # data matrix on top, buttons below
        self.border.Add(self.sizer, proportion=1, flag=wx.ALL|wx.EXPAND, border=8)
        
        # add a message area, buttons:
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        self.SetWindowVariant(variant=wx.WINDOW_VARIANT_SMALL)
        if not self.fixed:
            # placeholder for possible messages / warnings:
            self.tmpMsg = wx.StaticText(self, -1, label='', size=(300,15), style=wx.ALIGN_RIGHT)
            self.tmpMsg.SetForegroundColour('Red')
            if self.warning:
                self.tmpMsg.SetLabel(self.warning)
            buttons.Add(self.tmpMsg, flag=wx.ALIGN_CENTER)
            self.border.Add(buttons,1,flag=wx.BOTTOM|wx.ALIGN_CENTER, border=8)
            buttons = wx.BoxSizer(wx.HORIZONTAL)
            ADDROW = wx.Button(self, -1, "+cond.", size=(55,15)) # good size for mac, SMALL
            ADDROW.SetToolTip(wx.ToolTip('Add a condition (row); to delete a condition, delete all of its values.'))
            ADDROW.Bind(wx.EVT_BUTTON, self.userAddRow)
            buttons.Add(ADDROW)
            buttons.AddSpacer(4)
            ADDCOL = wx.Button(self, -1, "+param", size=(60,15))
            ADDCOL.SetToolTip(wx.ToolTip('Add a parameter (column); to delete a param, set its type to None, or delete all of its values.'))
            ADDCOL.Bind(wx.EVT_BUTTON, self.userAddCol)
            buttons.Add(ADDCOL)
            buttons.AddSpacer(4)
            PREVIEW = wx.Button(self, -1, "Preview")
            PREVIEW.SetToolTip(wx.ToolTip("Show all values as they would appear after saving to a file, without actually saving anything."))
            PREVIEW.Bind(wx.EVT_BUTTON, self.preview)
            buttons.Add(PREVIEW)
            buttons.AddSpacer(4)
            self.SAVEAS = wx.Button(self, wx.SAVE, "Save as")
            self.SAVEAS.Bind(wx.EVT_BUTTON, self.saveAs)
            buttons.Add(self.SAVEAS)
            buttons.AddSpacer(8)
            self.border.Add(buttons,1,flag=wx.BOTTOM|wx.ALIGN_RIGHT, border=8)
            buttons = wx.BoxSizer(wx.HORIZONTAL) # second line
        self.SetWindowVariant(variant=wx.WINDOW_VARIANT_NORMAL)
        buttons = wx.BoxSizer(wx.HORIZONTAL) # another line
        #help button if we know the url
        if self.helpUrl and not self.fixed:
            helpBtn = wx.Button(self, wx.ID_HELP)
            helpBtn.SetToolTip(wx.ToolTip("Go to online help"))
            helpBtn.Bind(wx.EVT_BUTTON, self.onHelp)
            buttons.Add(helpBtn, wx.ALIGN_LEFT|wx.ALL)
            buttons.AddSpacer(12)
        self.OKbtn = wx.Button(self, wx.ID_OK, " OK ")
        if not self.fixed:
            self.OKbtn.SetToolTip(wx.ToolTip('Save and exit'))
        self.OKbtn.Bind(wx.EVT_BUTTON, self.onOK)
        self.OKbtn.SetDefault()
        buttons.Add(self.OKbtn)
        if not self.fixed:
            buttons.AddSpacer(4)
            CANCEL = wx.Button(self, wx.ID_CANCEL, " Cancel ")
            CANCEL.SetToolTip(wx.ToolTip('Exit, discard any edits'))
            buttons.Add(CANCEL)
        buttons.AddSpacer(8)
        self.border.Add(buttons,1,flag=wx.BOTTOM|wx.ALIGN_RIGHT, border=8)
        
        # finally, its show time:
        self.SetSizerAndFit(self.border)
        if self.pos==None: self.Center()
        if self.ShowModal() == wx.ID_OK:
            self.getData(typeSelected=True) # set self.data and self.types, from fields
            self.OK = True
        else: 
            self.data = self.types = None
            self.OK = False
        self.Destroy()
    def onOK(self, event=None):
        if not self.fixed:
            if not self.save():
                return # disallow OK if bad param names
        event.Skip() # handle the OK button event
    def saveAs(self, event=None):
        """save, but allow user to give a new name
        """
        self.newFile = True # trigger query for fileName
        self.save()
        self.relaunch() # to update fileName in title
    def save(self, event=None):
        """save header + row x col data to a pickle file
        """
        self.getData(True) # update self.data
        adjustedNames = False
        for i, paramName in enumerate(self.data[0]):
            newName = paramName
            # ensure its legal as a var name, including namespace check:
            if self.parent:
                msg, enable = self.parent._checkName(name=paramName)
                if msg: # msg not empty means a namespace issue
                    newName = self.parent.exp.namespace.makeValid(paramName, prefix='param')
                    adjustedNames = True
            elif not _valid_var_re.match(paramName):
                msg, enable = "Name must be alpha-numeric or _, no spaces", False
                newName = self.parent.exp.namespace.makeValid(paramName)
                adjustedNames = True
            else:
                msg, enable = "", True
            # try to ensure its unique:
            while newName in self.data[0][:i]:
                adjustedNames = True
                newName += 'x' # unlikely to create a namespace conflict, but could happen
            self.data[0][i] = newName
            self.header[i].SetValue(newName) # displayed value
        if adjustedNames:
            self.tmpMsg.SetLabel('Param name(s) were adjusted. Look ok?')
            return False
        if hasattr(self, 'fileName') and self.fileName:
            fname = self.fileName
        else:
            self.newFile = True
            fname = self.defaultFileName
        if self.newFile or not os.path.isfile(fname):
            fullPath = fileSaveDlg(initFilePath=os.path.split(fname)[0],
                initFileName=os.path.basename(fname),
                        allowed="Pickle files *.pkl")
        else:
            fullPath = fname
        if fullPath: # None if user canceled
            if not fullPath.endswith('.pkl'):
                fullPath += '.pkl'
            f = open(fullPath, 'w')
            cPickle.dump(self.data, f)
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
            fullPathList = fileOpenDlg(tryFileName=os.path.basename(fileName),
                            allowed="All files (*.*)|*.*")
            if fullPathList:
                fileName = fullPathList[0] # wx.MULTIPLE -> list
        if os.path.isfile(fileName) and fileName.endswith('.pkl'):
            f = open(fileName)
            contents = cPickle.load(f)
            f.close()
            if self.parent:
                self.parent.conditionsFile = fileName
            return contents
        elif not os.path.isfile(fileName):
            print 'file %s not found' % fileName
        else:
            print 'only .pkl supported at the moment'
    def asConditions(self):
        """converts self.data into self.conditions for TrialHandler, returns conditions
        """
        if not self.data or not self.hasHeader:
            if hasattr(self, 'conditions') and self.conditions:
                return self.conditions
            return
        self.conditions = []
        keyList = self.data[0] # header = keys of dict
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
        
def fileSaveDlg(initFilePath="", initFileName="", 
                prompt="Select file to save", allowed=None):
    """A simple dialogue allowing access to the file system.
    (Useful in case you collect an hour of data and then try to 
    save to a non-existent directory!!)
    
    :parameters:
        initFilePath: string
            default file path on which to open the dialog
        initFilePath: string
            default file name, as suggested file
        prompt: string (default "Select file to open")
            can be set to custom prompts
        allowed: string
            a string to specify file filters. 
            e.g. "BMP files (*.bmp)|*.bmp|GIF files (*.gif)|*.gif"
            See http://www.wxpython.org/docs/api/wx.FileDialog-class.html for further details
            
    If initFilePath or initFileName are empty or invalid then
    current path and empty names are used to start search.
    
    If user cancels the None is returned.
    """
    if allowed==None:
        allowed = "All files (*.*)|*.*"  #\
            #"txt (*.txt)|*.txt" \
            #"pickled files (*.pickle, *.pkl)|*.pickle" \
            #"shelved files (*.shelf)|*.shelf"
    try:
        dlg = wx.FileDialog(None,prompt, 
                          initFilePath, initFileName, allowed, wx.SAVE)
    except:
        tmpApp = wx.PySimpleApp()
        dlg = wx.FileDialog(None,prompt, 
                          initFilePath, initFileName, allowed, wx.SAVE)
    if dlg.ShowModal() == OK:
        #get names of images and their directory
        outName = dlg.GetFilename()
        outPath = dlg.GetDirectory()
        dlg.Destroy()
        #tmpApp.Destroy() #this causes an error message for some reason
        fullPath = os.path.join(outPath, outName)
    else: fullPath = None
    return fullPath

def fileOpenDlg(tryFilePath="",
                tryFileName="",
                prompt="Select file to open",
                allowed=None):
    """A simple dialogue allowing access to the file system.
    (Useful in case you collect an hour of data and then try to 
    save to a non-existent directory!!)
    
    :parameters:
        tryFilePath: string
            default file path on which to open the dialog
        tryFilePath: string
            default file name, as suggested file
        prompt: string (default "Select file to open")
            can be set to custom prompts
        allowed: string (available since v1.62.01)
            a string to specify file filters. 
            e.g. "BMP files (*.bmp)|*.bmp|GIF files (*.gif)|*.gif"
            See http://www.wxpython.org/docs/api/wx.FileDialog-class.html for further details
            
    If tryFilePath or tryFileName are empty or invalid then
    current path and empty names are used to start search.
    
    If user cancels, then None is returned.
    """
    if allowed==None:
        allowed = "PsychoPy Data (*.psydat)|*.psydat|"\
            "txt (*.txt,*.dlm,*.csv)|*.txt;*.dlm;*.csv|" \
            "pickled files (*.pickle, *.pkl)|*.pickle|" \
            "shelved files (*.shelf)|*.shelf|" \
            "All files (*.*)|*.*"
    try:
        dlg = wx.FileDialog(None, prompt,
                          tryFilePath, tryFileName, allowed, wx.OPEN|wx.FILE_MUST_EXIST|wx.MULTIPLE)
    except:
        tmpApp = wx.PySimpleApp()
        dlg = wx.FileDialog(None, prompt,
                          tryFilePath, tryFileName, allowed, wx.OPEN|wx.FILE_MUST_EXIST|wx.MULTIPLE)
    if dlg.ShowModal() == OK:
        #get names of images and their directory
        fullPaths = dlg.GetPaths()
    else: fullPaths = None
    dlg.Destroy()
    return fullPaths
