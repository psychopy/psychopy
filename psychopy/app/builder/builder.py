# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import wx
from wx.lib import platebtn, scrolledpanel, flatnotebook
from wx.lib.expando import ExpandoTextCtrl, EVT_ETC_LAYOUT_NEEDED
import wx.aui, wx.stc
import sys, os, glob, copy, traceback
import keyword
import codecs
import re
import numpy
import experiment, components

try:
    _translate  # is the app-global text translation function defined?
except NameError:
    from psychopy.app import localization

from psychopy.app import stdOutRich, dialogs
from psychopy import data, logging, gui
from psychopy.tools.filetools import mergeFolder
import cPickle
from psychopy.app.builder.experiment import _valid_var_re, _nonalphanumeric_re
from psychopy.app.builder import validators

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
    # strings for all allowedVals (from all components) go here:
        'linear': _translate('linear'), 'nearest': _translate('nearest'),  # interpolation
        'rgb': 'rgb', 'dkl': 'dkl', 'lms': 'lms', 'hsv':'hsv',  # not translated
        'last key' : _translate('last key'), 'first key': _translate('first key'),
        'all keys': _translate('all keys'), 'nothing': _translate('nothing'),
        'last button' : _translate('last button'), 'first button': _translate('first button'),
        'all buttons': _translate('all buttons'),
        'final': _translate('final'), 'on click': _translate('on click'), 'every frame': _translate('every frame'),
        'never': _translate('never'),
        'from exp settings': _translate('from exp settings'), 'from prefs': _translate('from preferences'),
        'circle': _translate('circle'), 'square': _translate('square'),  # dots
        'direction': _translate('direction'), 'position': _translate('position'), 'walk': _translate('walk'),  # dots
        'same': _translate('same'), 'different': _translate('different'),  # dots
        'experiment': _translate('Experiment'),
        # startType & stopType:
        'time (s)': _translate('time (s)'), 'frame N': _translate('frame N'), 'condition': _translate('condition'),
        'duration (s)': _translate('duration (s)'), 'duration (frames)': _translate('duration (frames)'),
        # not translated:
        'pix': 'pix', 'deg': 'deg', 'cm': 'cm', 'norm': 'norm', 'height': 'height',
        '32': '32', '64': '64', '128': '128', '256': '256', '512': '512',  # tex resolution
        'routine': 'Routine',
    # strings for allowedUpdates:
        'constant': _translate('constant'),
        'set every repeat': _translate('set every repeat'),
        'set every frame': _translate('set every frame'),
    # strings for allowedVals in settings:
        'add': _translate('add'), 'avg': _translate('average'), # blend mode
        'use prefs': _translate('use preferences'),
    # logging level:
        'debug': _translate('debug'), 'info': _translate('info'), 'exp': _translate('exp'),
        'data': _translate('data'), 'warning': _translate('warning'), 'error': _translate('error'),
    # Experiment info dialog:
        'Field': _translate('Field'), 'Default': _translate('Default'),
    # ComponentsPanel category labels:
        'Favorites': _translate('Favorites'), 'Stimuli': _translate('Stimuli'),
        'Responses': _translate('Responses'), 'Custom': _translate('Custom'), 'I/O': _translate('I/O')
    }


class FileDropTarget(wx.FileDropTarget):
    """On Mac simply setting a handler for the EVT_DROP_FILES isn't enough.
    Need this too.
    """
    def __init__(self, builder):
        wx.FileDropTarget.__init__(self)
        self.builder = builder
    def OnDropFiles(self, x, y, filenames):
        logging.debug('PsychoPyBuilder: received dropped files: filenames')
        for filename in filenames:
            if filename.endswith('.psyexp'):
                self.builder.fileOpen(filename=filename)
            elif filename.lower().endswith('.py'):
                self.app.fileOpen(filename=filename)
            else:
                logging.warning('dropped file ignored: did not end in .psyexp')

class WindowFrozen(object):
    """
    Equivalent to wxWindowUpdateLocker.

    Usage::

        with WindowFrozen(wxControl):
          update multiple things
        #will automatically thaw here

    """
    def __init__(self, ctrl):
        self.ctrl = ctrl
    def __enter__(self):#started the with... statement
        if sys.platform == 'win32': #Freeze should not be called if platform is win32.
            return self.ctrl
        if self.ctrl is not None and wx.__version__[:3]<='2.8':#check it hasn't been deleted
            self.ctrl.Freeze()
        return self.ctrl
    def __exit__(self, exc_type, exc_val, exc_tb):#ended the with... statement
        if sys.platform == 'win32': #Thaw should not be called if platform is win32.
            return
        if self.ctrl is not None and self.ctrl.IsFrozen():#check it hasn't been deleted
            self.ctrl.Thaw()

class CodeBox(wx.stc.StyledTextCtrl):
    # this comes mostly from the wxPython demo styledTextCtrl 2
    def __init__(self, parent, ID, prefs,
                 pos=wx.DefaultPosition, size=wx.Size(100,160),#set the viewer to be small, then it will increase with wx.aui control
                 style=0):
        wx.stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)
        #JWP additions
        self.notebook=parent
        self.prefs = prefs
        self.UNSAVED=False
        self.filename=""
        self.fileModTime=None # for checking if the file was modified outside of CodeEditor
        self.AUTOCOMPLETE = True
        self.autoCompleteDict={}
        #self.analyseScript()  #no - analyse after loading so that window doesn't pause strangely
        self.locals = None #this will contain the local environment of the script
        self.prevWord=None
        #remove some annoying stc key commands
        self.CmdKeyClear(ord('['), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord(']'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('/'), wx.stc.STC_SCMOD_CTRL)
        self.CmdKeyClear(ord('/'), wx.stc.STC_SCMOD_CTRL|wx.stc.STC_SCMOD_SHIFT)

        self.SetLexer(wx.stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, " ".join(keyword.kwlist))

        self.SetProperty("fold", "1")
        self.SetProperty("tab.timmy.whinge.level", "4")#4 means 'tabs are bad'; 1 means 'flag inconsistency'
        self.SetMargins(0,0)
        self.SetUseTabs(False)
        self.SetTabWidth(4)
        self.SetIndent(4)
        self.SetViewWhiteSpace(self.prefs.appData['coder']['showWhitespace'])
        #self.SetBufferedDraw(False)
        self.SetViewEOL(False)
        self.SetEOLMode(wx.stc.STC_EOL_LF)
        self.SetUseAntiAliasing(True)
        #self.SetUseHorizontalScrollBar(True)
        #self.SetUseVerticalScrollBar(True)

        #self.SetEdgeMode(wx.stc.STC_EDGE_BACKGROUND)
        #self.SetEdgeMode(wx.stc.STC_EDGE_LINE)
        #self.SetEdgeColumn(78)

        # Setup a margin to hold fold markers
        self.SetMarginType(2, wx.stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, wx.stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 12)
        self.Bind(wx.stc.EVT_STC_MARGINCLICK, self.OnMarginClick)

        self.SetIndentationGuides(False)

        # Like a flattened tree control using square headers
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPEN,    wx.stc.STC_MARK_BOXMINUS,          "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDER,        wx.stc.STC_MARK_BOXPLUS,           "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERSUB,     wx.stc.STC_MARK_VLINE,             "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERTAIL,    wx.stc.STC_MARK_LCORNER,           "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEREND,     wx.stc.STC_MARK_BOXPLUSCONNECTED,  "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPENMID, wx.stc.STC_MARK_BOXMINUSCONNECTED, "white", "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERMIDTAIL, wx.stc.STC_MARK_TCORNER,           "white", "#808080")

        #self.DragAcceptFiles(True)
        #self.Bind(wx.EVT_DROP_FILES, self.coder.filesDropped)
        #self.Bind(wx.stc.EVT_STC_MODIFIED, self.onModified)
        ##self.Bind(wx.stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        #self.Bind(wx.stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        #self.Bind(wx.EVT_KEY_DOWN, self.OnKeyPressed)
        #self.SetDropTarget(FileDropTarget(coder = self.coder))

        self.setupStyles()

    def setupStyles(self):

        if wx.Platform == '__WXMSW__':
            faces = { 'size' : 10}
        elif wx.Platform == '__WXMAC__':
            faces = { 'size' : 14}
        else:
            faces = { 'size' : 12}
        if self.prefs.coder['codeFontSize']:
            faces['size'] = int(self.prefs.coder['codeFontSize'])
        faces['small']=faces['size']-2
        # Global default styles for all languages
        faces['code'] = self.prefs.coder['codeFont']#,'Arial']#use arial as backup
        faces['comment'] = self.prefs.coder['commentFont']#,'Arial']#use arial as backup
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,     "face:%(code)s,size:%(size)d" % faces)
        self.StyleClearAll()  # Reset all to be like the default

        # Global default styles for all languages
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,     "face:%(code)s,size:%(size)d" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER,  "back:#C0C0C0,face:%(code)s,size:%(small)d" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_CONTROLCHAR, "face:%(comment)s" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACELIGHT,  "fore:#FFFFFF,back:#0000FF,bold")
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACEBAD,    "fore:#000000,back:#FF0000,bold")

        # Python styles
        # Default
        self.StyleSetSpec(wx.stc.STC_P_DEFAULT, "fore:#000000,face:%(code)s,size:%(size)d" % faces)
        # Comments
        self.StyleSetSpec(wx.stc.STC_P_COMMENTLINE, "fore:#007F00,face:%(comment)s,size:%(size)d" % faces)
        # Number
        self.StyleSetSpec(wx.stc.STC_P_NUMBER, "fore:#007F7F,size:%(size)d" % faces)
        # String
        self.StyleSetSpec(wx.stc.STC_P_STRING, "fore:#7F007F,face:%(code)s,size:%(size)d" % faces)
        # Single quoted string
        self.StyleSetSpec(wx.stc.STC_P_CHARACTER, "fore:#7F007F,face:%(code)s,size:%(size)d" % faces)
        # Keyword
        self.StyleSetSpec(wx.stc.STC_P_WORD, "fore:#00007F,bold,size:%(size)d" % faces)
        # Triple quotes
        self.StyleSetSpec(wx.stc.STC_P_TRIPLE, "fore:#7F0000,size:%(size)d" % faces)
        # Triple double quotes
        self.StyleSetSpec(wx.stc.STC_P_TRIPLEDOUBLE, "fore:#7F0000,size:%(size)d" % faces)
        # Class name definition
        self.StyleSetSpec(wx.stc.STC_P_CLASSNAME, "fore:#0000FF,bold,underline,size:%(size)d" % faces)
        # Function or method name definition
        self.StyleSetSpec(wx.stc.STC_P_DEFNAME, "fore:#007F7F,bold,size:%(size)d" % faces)
        # Operators
        self.StyleSetSpec(wx.stc.STC_P_OPERATOR, "bold,size:%(size)d" % faces)
        # Identifiers
        self.StyleSetSpec(wx.stc.STC_P_IDENTIFIER, "fore:#000000,face:%(code)s,size:%(size)d" % faces)
        # Comment-blocks
        self.StyleSetSpec(wx.stc.STC_P_COMMENTBLOCK, "fore:#7F7F7F,size:%(size)d" % faces)
        # End of line where string is not closed
        self.StyleSetSpec(wx.stc.STC_P_STRINGEOL, "fore:#000000,face:%(code)s,back:#E0C0E0,eol,size:%(size)d" % faces)

        self.SetCaretForeground("BLUE")
    def setStatus(self, status):
        if status=='error':
            color=(255,210,210,255)
        elif status=='changed':
            color=(220,220,220,255)
        else:
            color=(255,255,255,255)
        self.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, color)
        self.setupStyles()#then reset fonts again on top of that color
    def OnMarginClick(self, evt):
        # fold and unfold as needed
        if evt.GetMargin() == 2:
            lineClicked = self.LineFromPosition(evt.GetPosition())

            if self.GetFoldLevel(lineClicked) & wx.stc.STC_FOLDLEVELHEADERFLAG:
                if evt.GetShift():
                    self.SetFoldExpanded(lineClicked, True)
                    self.Expand(lineClicked, True, True, 1)
                elif evt.GetControl():
                    if self.GetFoldExpanded(lineClicked):
                        self.SetFoldExpanded(lineClicked, False)
                        self.Expand(lineClicked, False, True, 0)
                    else:
                        self.SetFoldExpanded(lineClicked, True)
                        self.Expand(lineClicked, True, True, 100)
                else:
                    self.ToggleFold(lineClicked)

class CodeComponentDialog(wx.Dialog):
    def __init__(self,frame,title,params,order,
            helpUrl=None, suppressTitles=True,size=wx.DefaultSize,
            style=(wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
                            | wx.THICK_FRAME | wx.DIALOG_NO_PARENT),
            editing=False):

        # translate title
        localizedTitle = title.replace(' Properties',_translate(' Properties'))

        wx.Dialog.__init__(self, frame,-1,localizedTitle,size=size,style=style)
        self.frame=frame
        self.app=frame.app
        self.helpUrl=helpUrl
        self.params=params   #dict
        self.order=order
        self.title = title
        self.localizedTitle = localizedTitle # keep localized title to update dialog's properties later.
        self.code_gui_elements={}
        if not editing and 'name' in self.params.keys():
            # then we're adding a new component, so provide a known-valid name:
            self.params['name'].val = self.frame.exp.namespace.makeValid(params['name'].val)


        agwStyle = flatnotebook.FNB_NO_X_BUTTON
        if hasattr(flatnotebook, "FNB_NAV_BUTTONS_WHEN_NEEDED"):
            # not available in wxPython 2.8
            agwStyle |= flatnotebook.FNB_NAV_BUTTONS_WHEN_NEEDED
        if hasattr(flatnotebook, "FNB_NO_TAB_FOCUS"):
            # not available in wxPython 2.8.10
            agwStyle |= flatnotebook.FNB_NO_TAB_FOCUS
        self.code_sections = flatnotebook.FlatNotebook(self, wx.ID_ANY,
            style = agwStyle)

        openToPage = 0
        for i, pkey in enumerate(self.order):
            param=self.params.get(pkey)
            if pkey == 'name':
                self.name_label = wx.StaticText(self, wx.ID_ANY,param.label)
                self.component_name = wx.TextCtrl(self,
                                 wx.ID_ANY,
                                 unicode(param.val),
                                 style=wx.TE_PROCESS_ENTER | wx.TE_PROCESS_TAB)
                self.component_name.SetToolTipString(param.hint)
                self.component_name.SetValidator(validators.NameValidator())
                self.nameOKlabel=wx.StaticText(self,-1,'',
                                            style=wx.ALIGN_RIGHT)
                self.nameOKlabel.SetForegroundColour(wx.RED)
            else:
                guikey=pkey.replace(' ','_')
                param_gui_elements=self.code_gui_elements.setdefault(guikey,
                                                                     dict())

                panel_element=param_gui_elements.setdefault(guikey+'_panel',
                                       wx.Panel(self.code_sections, wx.ID_ANY))
                code_box=param_gui_elements.setdefault(guikey+'_codebox',
                                              CodeBox(panel_element,
                                                    wx.ID_ANY,
                                                    pos=wx.DefaultPosition,
                                                    style=0,
                                                    prefs=self.app.prefs))
                if len(param.val):
                    code_box.AddText(unicode(param.val))
                if len(param.val.strip()) and not openToPage:
                        openToPage = i  # first non-blank page

        if self.helpUrl!=None:
            self.help_button = wx.Button(self, wx.ID_HELP, _translate(" Help "))
            self.help_button.SetToolTip(wx.ToolTip(_translate("Go to online help about this component")))
        self.ok_button = wx.Button(self, wx.ID_OK, _translate(" OK "))
        self.ok_button.SetDefault()
        self.cancel_button = wx.Button(self, wx.ID_CANCEL, _translate(" Cancel "))

        self.__set_properties()
        self.__do_layout()
        self.code_sections.SetSelection(max(0, openToPage - 1))

        self.Bind(wx.EVT_BUTTON, self.helpButtonHandler, self.help_button)

        #do show and process return
        ret=self.ShowModal()

        if ret == wx.ID_OK:
            self.checkName()
            self.OK=True
            self.params = self.getParams()#get new vals from dlg
            self.Validate()
            # TODO: Should code from each code section tab have syntax checked??
        else:
            self.OK=False

    def checkName(self, event=None):
        """
        Issue a form validation on name change.
        """
        self.Validate()

    def __set_properties(self):

        self.SetTitle(self.localizedTitle) # use localized title
        self.SetSize((640, 480))

    def __do_layout(self):
        for param_name in self.order:
             if param_name.lower() != 'name':
                guikey=param_name.replace(' ','_')
                param_gui_dict=self.code_gui_elements.get(guikey)
                asizer=param_gui_dict.setdefault(guikey+'_sizer',wx.BoxSizer(wx.VERTICAL))
                asizer.Add(param_gui_dict.get(guikey+'_codebox'), 1, wx.EXPAND, 0)
                param_gui_dict.get(guikey+'_panel').SetSizer(asizer)
                self.code_sections.AddPage(param_gui_dict.get(guikey+'_panel'), _translate(param_name))

        name_sizer = wx.BoxSizer(wx.HORIZONTAL)
        name_sizer.Add(self.name_label, 0, wx.ALL, 10)
        name_sizer.Add(self.component_name, 0,  wx.BOTTOM | wx.TOP, 10)
        name_sizer.Add(self.nameOKlabel, 0,  wx.ALL, 10)

        sizer_1 = wx.BoxSizer(wx.VERTICAL)
        sizer_2 = wx.BoxSizer(wx.HORIZONTAL)
        sizer_1.Add(name_sizer)
        sizer_1.Add(self.code_sections, 1, wx.EXPAND |wx.ALL, 10)
        sizer_2.Add(self.help_button, 0, wx.RIGHT, 10)
        sizer_2.Add(self.ok_button, 0, wx.LEFT, 10)
        sizer_2.Add(self.cancel_button, 0, 0, 0)
        sizer_1.Add(sizer_2, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        self.SetSizer(sizer_1)
        self.Layout()
        self.Center()

    def getParams(self):
        """retrieves data from any fields in self.code_gui_elements
        (populated during the __init__ function)

        The new data from the dlg get inserted back into the original params
        used in __init__ and are also returned from this method.
        """
        #get data from input fields
        for fieldName in self.params.keys():
            param=self.params[fieldName]
            if fieldName=='name':
                param.val = self.component_name.GetValue()
            else:
                guikey=fieldName.replace(' ','_')
                cb_gui_el=guikey+'_codebox'
                if guikey in self.code_gui_elements:

                    param.val=self.code_gui_elements.get(guikey).get(cb_gui_el).GetText()
        return self.params

    def helpButtonHandler(self, event):
        """Uses self.app.followLink() to self.helpUrl
        """
        self.app.followLink(url=self.helpUrl)

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
        #self.drawNearestRoutinePoint = True
        #self.drawNearestLoopPoint = False
        self.pointsToDraw=[] #lists the x-vals of points to draw, eg loop locations
        self.appData = self.app.prefs.appData # for flowSize, showLoopInfoInFlow

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
        self.componentFromID = {}#use the ID of the drawn icon to retrieve component (loop or routine)
        self.contextMenuLabels = {'remove': _translate('remove')}
        self.contextMenuItems = ['remove']
        self.contextItemFromID = {}
        self.contextIDFromItem = {}
        for item in self.contextMenuItems:
            id = wx.NewId()
            self.contextItemFromID[id] = item
            self.contextIDFromItem[item] = id

        #self.btnInsertRoutine = wx.Button(self,-1,'Insert Routine', pos=(10,10))
        #self.btnInsertLoop = wx.Button(self,-1,'Insert Loop', pos=(10,30))
        if sys.platform.startswith('linux'): # Localized labels on PlateButton may be corrupted in Ubuntu.
            labelRoutine = 'Insert Routine '
            labelLoop = 'Insert Loop     '
        else:
            labelRoutine = _translate('Insert Routine ')
            labelLoop = _translate('Insert Loop     ')
        self.btnInsertRoutine = platebtn.PlateButton(self,-1,labelRoutine, pos=(10,10))
        self.btnInsertLoop = platebtn.PlateButton(self,-1,labelLoop, pos=(10,30)) #spaces give size for CANCEL

        self.labelTextRed = {'normal': wx.Colour(250,10,10, 250),'hlight':wx.Colour(250,10,10, 250)}
        self.labelTextBlack = {'normal': wx.Colour(0,0,0, 250),'hlight':wx.Colour(250,250,250, 250)}

        # use self.appData['flowSize'] to index a tuple to get a specific value, eg: (4,6,8)[self.appData['flowSize']]
        self.flowMaxSize = 2 # upper limit on increaseSize

        self.draw()

        #bind events
        self.Bind(wx.EVT_MOUSE_EVENTS, self.OnMouse)
        self.Bind(wx.EVT_BUTTON, self.onInsertRoutine,self.btnInsertRoutine)
        self.Bind(wx.EVT_BUTTON, self.setLoopPoint1,self.btnInsertLoop)
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
        self.gapsExcluded=[]
        self.draw()
        self.frame.SetStatusText("")
        if sys.platform.startswith('linux'): # Localized labels on PlateButton may be corrupted in Ubuntu.
            self.btnInsertRoutine.SetLabel('Insert Routine')
            self.btnInsertLoop.SetLabel('Insert Loop')
        else:
            self.btnInsertRoutine.SetLabel(_translate('Insert Routine'))
            self.btnInsertLoop.SetLabel(_translate('Insert Loop'))
        self.btnInsertRoutine.SetLabelColor(**self.labelTextBlack)
        self.btnInsertLoop.SetLabelColor(**self.labelTextBlack)
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
        if self.mode.startswith('loopPoint'):
            self.clearMode()
        elif self.mode == 'routine': # clicked again with label now being "Cancel..."
            self.clearMode()
            return
        self.frame.SetStatusText(_translate("Select a Routine to insert (Esc to exit)"))
        menu = wx.Menu()
        self.routinesFromID={}
        id = wx.NewId()
        menu.Append(id, '(new)')
        self.routinesFromID[id] = '(new)'
        wx.EVT_MENU(menu, id, self.insertNewRoutine)
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
    def insertNewRoutine(self, event):
        """selecting (new) is a short-cut for: make new routine, insert it into the flow
        """
        newRoutine = self.frame.routinePanel.createNewRoutine(returnName=True)
        if newRoutine:
            self.routinesFromID[event.GetId()] = newRoutine
            self.onInsertRoutineSelect(event)
        else:
            self.clearMode()
    def onInsertRoutineSelect(self,event):
        """User has selected a routine to be entered so bring up the entrypoint marker
        and await mouse button press.
        see self.insertRoutine() for further info
        """
        self.mode='routine'
        if sys.platform.startswith('linux'): # Localized labels on PlateButton may be corrupted in Ubuntu.
            self.btnInsertRoutine.SetLabel('CANCEL Insert')
        else:
            self.btnInsertRoutine.SetLabel(_translate('CANCEL Insert'))
        self.btnInsertRoutine.SetLabelColor(**self.labelTextRed)
        self.frame.SetStatusText(_translate('Click where you want to insert the Routine, or CANCEL insert.'))
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
        self.frame.addToUndoStack("ADD Routine `%s`" %self.frame.exp.routines[self.insertingRoutine].name)
        #reset flow drawing (remove entry point)
        self.clearMode()

    def setLoopPoint1(self, evt=None):
        """Someone pushed the insert loop button.
        Fetch the dialog
        """
        if self.mode == 'routine':
            self.clearMode()
        elif self.mode.startswith('loopPoint'): # clicked again, label is "Cancel..."
            self.clearMode()
            return
        if sys.platform.startswith('linux'): # Localized labels on PlateButton may be corrupted in Ubuntu.
            self.btnInsertLoop.SetLabel('CANCEL insert')
        else:
            self.btnInsertLoop.SetLabel(_translate('CANCEL insert'))
        self.btnInsertLoop.SetLabelColor(**self.labelTextRed)
        self.mode='loopPoint1'
        self.frame.SetStatusText(_translate('Click where you want the loop to start/end, or CANCEL insert.'))
        x = self.getNearestGapPoint(0)
        self.drawEntryPoints([x])
    def setLoopPoint2(self, evt=None):
        """We've got the location of the first point, waiting to get the second
        """
        self.mode='loopPoint2'
        self.frame.SetStatusText(_translate('Click the other end for the loop'))
        thisPos = self.entryPointPosList[0]
        self.gapsExcluded=[thisPos]
        self.gapsExcluded.extend(self.getGapPointsCrossingStreams(thisPos))
        #is there more than one available point
        x = self.getNearestGapPoint(wx.GetMousePosition()[0]-self.GetScreenPosition()[0],
            exclude=self.gapsExcluded)#exclude point 1, and
        self.drawEntryPoints([self.entryPointPosList[0], x])
        nAvailableGaps= len(self.gapMidPoints)-len(self.gapsExcluded)
        if nAvailableGaps==1:
            self.insertLoop()#there's only one place - go ahead and insert it
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
            self.frame.addToUndoStack("ADD Loop `%s` to Flow" %handler.params['name'].val)
        self.clearMode()
        self.draw()
    def increaseSize(self, event=None):
        if self.appData['flowSize'] == self.flowMaxSize:
            self.appData['showLoopInfoInFlow'] = True
        self.appData['flowSize'] = min(self.flowMaxSize, self.appData['flowSize'] + 1)
        self.clearMode() #redraws
    def decreaseSize(self, event=None):
        if self.appData['flowSize'] == 0:
            self.appData['showLoopInfoInFlow'] = False
        self.appData['flowSize'] = max(0, self.appData['flowSize'] - 1)
        self.clearMode() # redraws
    def editLoopProperties(self, event=None, loop=None):
        #add routine points to the timeline
        self.setDrawPoints('loops')
        self.draw()
        if 'conditions' in loop.params.keys():
            condOrig = loop.params['conditions'].val
            condFileOrig = loop.params['conditionsFile'].val
        loopDlg = DlgLoopProperties(frame=self.frame,
            helpUrl = self.app.urls['builder.loops'],
            title=loop.params['name'].val+' Properties', loop=loop)
        if loopDlg.OK:
            prevLoop=loop
            if loopDlg.params['loopType'].val=='staircase':
                loop= loopDlg.stairHandler
            elif loopDlg.params['loopType'].val=='interleaved staircases':
                loop= loopDlg.multiStairHandler
            else:
                loop=loopDlg.trialHandler #['random','sequential', 'fullRandom', ]
            #if the loop is a whole new class then we can't just update the params
            if loop.getType()!=prevLoop.getType():
                #get indices for start and stop points of prev loop
                flow = self.frame.exp.flow
                startII = flow.index(prevLoop.initiator) #find the index of the initiator
                endII = flow.index(prevLoop.terminator)-1 #minus one because initiator will have been deleted
                #remove old loop completely
                flow.removeComponent(prevLoop)
                #finally insert the new loop
                flow.addLoop(loop, startII, endII)
            self.frame.addToUndoStack("EDIT Loop `%s`" %(loop.params['name'].val))
        elif 'conditions' in loop.params.keys():
            loop.params['conditions'].val = condOrig
            loop.params['conditionsFile'].val = condFileOrig
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
                        if comp.getType() in ['StairHandler', 'TrialHandler', 'MultiStairHandler']:
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
                        if thisComp.getType() in ['StairHandler', 'TrialHandler', 'MultiStairHandler']:
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
                    # right click but not on an icon
                    self.Refresh() # might as well do something
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
                point = self.getNearestGapPoint(mouseX=x, exclude=self.gapsExcluded)
                self.drawEntryPoints([self.entryPointPosList[0], point])
    def getNearestGapPoint(self, mouseX, exclude=[]):
        """Get gap that is nearest to a particular mouse location
        """
        d=1000000000
        nearest=None
        for point in self.gapMidPoints:
            if point in exclude:
                continue
            if (point-mouseX)**2 < d:
                d=(point-mouseX)**2
                nearest=point
        return nearest
    def getGapPointsCrossingStreams(self,gapPoint):
        """For a given gap point, identify the gap points that are
        excluded by crossing a loop line
        """
        gapArray=numpy.array(self.gapMidPoints)
        nestLevels=numpy.array(self.gapNestLevels)
        thisLevel=nestLevels[gapArray==gapPoint]
        invalidGaps= (gapArray[nestLevels!=thisLevel]).tolist()
        return invalidGaps
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
        #get ID
        op = self.contextItemFromID[event.GetId()]
        compID=self._menuComponentID #the ID is also the index to the element in the flow list
        flow = self.frame.exp.flow
        component=flow[compID]
        #if we have a Loop Initiator, remove the whole loop
        if component.getType()=='LoopInitiator':
            component = component.loop
        if op=='remove':
            self.removeComponent(component, compID)
            self.frame.addToUndoStack("REMOVE `%s` from Flow" %component.params['name'])
        if op=='rename':
            print 'rename is not implemented yet'
            #if component is a loop: DlgLoopProperties
            #elif component is a routine: DlgRoutineProperties
        self.draw()
        self._menuComponentID=None
    def removeComponent(self, component, compID):
        """Remove either a Routine or a Loop from the Flow
        """
        flow=self.frame.exp.flow
        if component.getType()=='Routine':
            #check whether this will cause a collapsed loop
            #prev and next elements on flow are a loop init/end
            prevIsLoop=nextIsLoop=False
            if compID>0:#there is at least one preceding
                prevIsLoop = (flow[compID-1]).getType()=='LoopInitiator'
            if len(flow)>(compID+1):#there is at least one more compon
                nextIsLoop = (flow[compID+1]).getType()=='LoopTerminator'
            if prevIsLoop and nextIsLoop:
                loop=flow[compID+1].loop#because flow[compID+1] is a terminator
                warnDlg = dialogs.MessageDialog(parent=self.frame,
                    message=_translate('The "%s" Loop is about to be deleted as well (by collapsing). OK to proceed?') %loop.params['name'],
                    type='Warning', title=_translate('Impending Loop collapse'))
                resp=warnDlg.ShowModal()
                if resp in [wx.ID_CANCEL, wx.ID_NO]:
                    return#abort
                elif resp==wx.ID_YES:
                    #make some recursive calls to this same method until success
                    self.removeComponent(loop, compID )#remove the loop first
                    self.removeComponent(component, compID-1)#because the loop has been removed ID is now one less
                    return #because we would have done the removal in final successful call
        # remove name from namespace only if it's a loop (which exists only in the flow)
        elif 'conditionsFile' in component.params.keys():
            conditionsFile = component.params['conditionsFile'].val
            if conditionsFile and conditionsFile not in ['None','']:
                try:
                    trialList, fieldNames = data.importConditions(conditionsFile, returnFieldNames=True)
                    for fname in fieldNames:
                        self.frame.exp.namespace.remove(fname)
                except:
                    logging.debug("Conditions file %s couldn't be found so names not removed from namespace" % conditionsFile)
            self.frame.exp.namespace.remove(component.params['name'].val)
        #perform the actual removal
        flow.removeComponent(component, id=compID)

    def OnPaint(self, event):
        # Create a buffered paint DC.  It will create the real
        # wx.PaintDC and then blit the bitmap to it when dc is
        # deleted.
        dc = wx.GCDC(wx.BufferedPaintDC(self))
        # use PrepareDC to set position correctly
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
        gap = self.dpi / (6, 4, 2) [self.appData['flowSize']]
        dLoopToBaseLine = (15, 25, 43) [self.appData['flowSize']]
        dBetweenLoops = (20, 24, 30) [self.appData['flowSize']]

        #guess virtual size; nRoutines wide by nLoops high
        #make bigger than needed and shrink later
        nRoutines = len(expFlow)
        nLoops = 0
        for entry in expFlow:
            if entry.getType()=='LoopInitiator':
                nLoops += 1
        self.SetVirtualSize(size=(nRoutines*self.dpi*2, nLoops*dBetweenLoops+dLoopToBaseLine*3))

        #step through components in flow, get spacing info from text size, etc
        currX=self.linePos[0]
        lineId=wx.NewId()
        pdc.DrawLine(x1=self.linePos[0]-gap,y1=self.linePos[1],x2=self.linePos[0],y2=self.linePos[1])
        self.loops={}#NB the loop is itself the key!? and the value is further info about it
        nestLevel=0
        maxNestLevel=0
        self.gapMidPoints=[currX-gap/2]
        self.gapNestLevels=[0]
        for ii, entry in enumerate(expFlow):
            if entry.getType()=='LoopInitiator':
                self.loops[entry.loop]={'init':currX,'nest':nestLevel, 'id':ii}#NB the loop is itself the dict key!?
                nestLevel+=1#start of loop so increment level of nesting
                maxNestLevel = max(nestLevel, maxNestLevel)
            elif entry.getType()=='LoopTerminator':
                self.loops[entry.loop]['term']=currX #NB the loop is itself the dict key!
                nestLevel-=1#end of loop so decrement level of nesting
            elif entry.getType()=='Routine':
                # just get currX based on text size, don't draw anything yet:
                currX = self.drawFlowRoutine(pdc,entry, id=ii,pos=[currX,self.linePos[1]-10], draw=False)
            self.gapMidPoints.append(currX+gap/2)
            self.gapNestLevels.append(nestLevel)
            pdc.SetId(lineId)
            pdc.SetPen(wx.Pen(wx.Colour(0,0,0, 255)))
            pdc.DrawLine(x1=currX,y1=self.linePos[1],x2=currX+gap,y2=self.linePos[1])
            currX+=gap
        lineRect = wx.Rect(self.linePos[0]-2, self.linePos[1]-2, currX-self.linePos[0]+2, 4)
        pdc.SetIdBounds(lineId,lineRect)

        # draw the loops first:
        maxHeight = 0
        for thisLoop in self.loops:
            thisInit = self.loops[thisLoop]['init']
            thisTerm = self.loops[thisLoop]['term']
            thisNest = maxNestLevel-self.loops[thisLoop]['nest']-1
            thisId = self.loops[thisLoop]['id']
            height = self.linePos[1]+dLoopToBaseLine + thisNest*dBetweenLoops
            self.drawLoop(pdc,thisLoop,id=thisId,
                        startX=thisInit, endX=thisTerm,
                        base=self.linePos[1],height=height)
            self.drawLoopStart(pdc,pos=[thisInit,self.linePos[1]])
            self.drawLoopEnd(pdc,pos=[thisTerm,self.linePos[1]])
            if height > maxHeight:
                maxHeight=height

        # draw routines second (over loop lines):
        currX=self.linePos[0]
        for ii, entry in enumerate(expFlow):
            if entry.getType()=='Routine':
                currX = self.drawFlowRoutine(pdc,entry, id=ii,pos=[currX,self.linePos[1]-10])
            pdc.SetPen(wx.Pen(wx.Colour(0,0,0, 255)))
            pdc.DrawLine(x1=currX,y1=self.linePos[1],x2=currX+gap,y2=self.linePos[1])
            currX += gap

        self.SetVirtualSize(size=(currX+100, maxHeight+50))

        #draw all possible locations for routines DEPRECATED SINCE 1.62 because not drawing those
        #for n, xPos in enumerate(self.pointsToDraw):
        #   font.SetPointSize(600/self.dpi)
        #   self.SetFont(font); pdc.SetFont(font)
        #   w,h = self.GetFullTextExtent(str(len(self.pointsToDraw)))[0:2]
        #   pdc.SetPen(wx.Pen(wx.Colour(0,0,0, 255)))
        #   pdc.SetBrush(wx.Brush(wx.Colour(0,0,0,255)))
        #   pdc.DrawCircle(xPos,self.linePos[1], w+2)
        #   pdc.SetTextForeground([255,255,255])
        #   pdc.DrawText(str(n), xPos-w/2, self.linePos[1]-h/2)

        self.drawLineStart(pdc, (self.linePos[0]-gap,self.linePos[1]))
        self.drawLineEnd(pdc, (currX, self.linePos[1]))

        pdc.EndDrawing()
        self.Refresh()#refresh the visible window after drawing (using OnPaint)
    def drawEntryPoints(self, posList):
        ptSize = (3,4,5)[self.appData['flowSize']]
        for n, pos in enumerate(posList):
            if n>=len(self.entryPointPosList):
                #draw for first time
                id = wx.NewId()
                self.entryPointIDlist.append(id)
                self.pdc.SetId(id)
                self.pdc.SetBrush(wx.Brush(wx.Colour(0,0,0,255)))
                self.pdc.DrawCircle(pos,self.linePos[1], ptSize)
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
    def drawLineStart(self, dc, pos):
        #draw bar at start of timeline; circle looked bad, offset vertically
        ptSize = (3,3,4)[self.appData['flowSize']]
        dc.SetBrush(wx.Brush(wx.Colour(0,0,0, 255)))
        dc.SetPen(wx.Pen(wx.Colour(0,0,0, 255)))
        dc.DrawPolygon([[0,-ptSize],[1,-ptSize],[1,ptSize], [0,ptSize]], pos[0],pos[1])
    def drawLineEnd(self, dc, pos):
        #draws arrow at end of timeline
        #tmpId = wx.NewId()
        #dc.SetId(tmpId)
        dc.SetBrush(wx.Brush(wx.Colour(0,0,0, 255)))
        dc.SetPen(wx.Pen(wx.Colour(0,0,0, 255)))
        dc.DrawPolygon([[0,-3],[5,0],[0,3]], pos[0],pos[1])
        #dc.SetIdBounds(tmpId,wx.Rect(pos[0],pos[1]+3,5,6))
    def drawLoopEnd(self, dc, pos, downwards=True):
        # define the right side of a loop but draw nothing
        # idea: might want a wxID for grabbing and relocating the loop endpoint
        tmpId = wx.NewId()
        dc.SetId(tmpId)
        #dc.SetBrush(wx.Brush(wx.Colour(0,0,0, 250)))
        #dc.SetPen(wx.Pen(wx.Colour(0,0,0, 255)))
        size = (3,4,5)[self.appData['flowSize']]
        #if downwards: dc.DrawPolygon([[size,0],[0,size],[-size,0]], pos[0],pos[1]+2*size)#points down
        #else: dc.DrawPolygon([[size,size],[0,0],[-size,size]], pos[0],pos[1]-3*size)#points up
        dc.SetIdBounds(tmpId,wx.Rect(pos[0]-size,pos[1]-size,2*size,2*size))
        return
    def drawLoopStart(self, dc, pos, downwards=True):
        # draws direction arrow on left side of a loop
        tmpId = wx.NewId()
        dc.SetId(tmpId)
        dc.SetBrush(wx.Brush(wx.Colour(0,0,0, 250)))
        dc.SetPen(wx.Pen(wx.Colour(0,0,0, 255)))
        size = (3,4,5)[self.appData['flowSize']]
        offset = (3,2,0)[self.appData['flowSize']]
        if downwards:
            dc.DrawPolygon([[size,size],[0,0],[-size,size]], pos[0],pos[1]+3*size-offset)#points up
        else:
            dc.DrawPolygon([[size,0],[0,size],[-size,0]], pos[0],pos[1]-4*size)#points down
        dc.SetIdBounds(tmpId,wx.Rect(pos[0]-size,pos[1]-size,2*size,2*size))

    def drawFlowRoutine(self,dc,routine,id,pos=[0,0], draw=True):
        """Draw a box to show a routine on the timeline
        draw=False is for a dry-run, esp to compute and return size information without drawing or setting a pdc ID
        """
        name = routine.name
        if self.appData['flowSize']==0 and len(name) > 5:
            name = ' '+name[:4]+'..'
        else:
            name = ' '+name+' '
        if draw:
            dc.SetId(id)
        font = self.GetFont()
        if sys.platform=='darwin':
            fontSizeDelta = (9,6,0)[self.appData['flowSize']]
            font.SetPointSize(1400/self.dpi-fontSizeDelta)
        elif sys.platform.startswith('linux'):
            fontSizeDelta = (6,4,0)[self.appData['flowSize']]
            font.SetPointSize(1400/self.dpi-fontSizeDelta)
        else:
            fontSizeDelta = (8,4,0)[self.appData['flowSize']]
            font.SetPointSize(1000/self.dpi-fontSizeDelta)

        maxTime, nonSlip = routine.getMaxTime()
        if nonSlip:
            rgbFill=nonSlipFill
            rgbEdge=nonSlipEdge
        else:
            rgbFill=relTimeFill
            rgbEdge=relTimeEdge

        #get size based on text
        self.SetFont(font)
        if draw: dc.SetFont(font)
        w,h = self.GetFullTextExtent(name)[0:2]
        pad = (5,10,20)[self.appData['flowSize']]
        #draw box
        pos[1] += 2-self.appData['flowSize']
        rect = wx.Rect(pos[0], pos[1], w+pad,h+pad)
        endX = pos[0]+w+pad
        #the edge should match the text
        if draw:
            dc.SetPen(wx.Pen(wx.Colour(rgbEdge[0],rgbEdge[1],rgbEdge[2], wx.ALPHA_OPAQUE)))
            dc.SetBrush(wx.Brush(rgbFill))
            dc.DrawRoundedRectangleRect(rect, (4,6,8)[self.appData['flowSize']])
            #draw text
            dc.SetTextForeground(rgbEdge)
            dc.DrawLabel(name, rect, alignment = wx.ALIGN_CENTRE)
            if nonSlip and self.appData['flowSize']!=0:
                font.SetPointSize(font.GetPointSize()*0.6)
                dc.SetFont(font)
                dc.DrawLabel("(%.2fs)" %maxTime,
                    rect, alignment = wx.ALIGN_CENTRE|wx.ALIGN_BOTTOM)

            self.componentFromID[id]=routine
            #set the area for this component
            dc.SetIdBounds(id,rect)

        return endX

    def drawLoop(self,dc,loop,id, startX,endX,
            base,height,rgb=[0,0,0], downwards=True):
        if downwards: up=-1
        else: up=+1

        #draw loop itself, as transparent rect with curved corners
        tmpId = wx.NewId()
        dc.SetId(tmpId)
        curve = (6, 11, 15)[self.appData['flowSize']] #extra distance, in both h and w for curve
        yy = [base,height+curve*up,height+curve*up/2,height] # for area
        r,g,b=rgb
        dc.SetPen(wx.Pen(wx.Colour(r, g, b, 200)))
        vertOffset=0 # 1 is interesting too
        area = wx.Rect(startX, base+vertOffset, endX-startX, max(yy)-min(yy))
        dc.SetBrush(wx.Brush(wx.Colour(0,0,0,0),style=wx.TRANSPARENT)) # transparent
        dc.DrawRoundedRectangleRect(area, curve) # draws outline
        dc.SetIdBounds(tmpId, area)

        #add a name label, loop info, except at smallest size
        name = loop.params['name'].val
        if self.appData['showLoopInfoInFlow'] and not self.appData['flowSize']==0:
            if 'conditions' in loop.params.keys() and loop.params['conditions'].val:
                xnumTrials = 'x'+str(len(loop.params['conditions'].val))
            else: xnumTrials = ''
            name += '  ('+str(loop.params['nReps'].val)+xnumTrials
            abbrev = ['', {'random': 'rand.', 'sequential': 'sequ.', 'fullRandom':'f-ran.',
                      'staircase': 'stair.', 'interleaved staircases': "int-str."},
                      {'random': 'random', 'sequential': 'sequential', 'fullRandom':'fullRandom',
                      'staircase': 'staircase', 'interleaved staircases': "interl'vd stairs"}]
            name += ' '+abbrev[self.appData['flowSize']][loop.params['loopType'].val]+')'
        if self.appData['flowSize']==0:
            if len(name) > 9:
                name = ' '+name[:8]+'..'
            else: name = ' '+name[:9]
        else:
            name = ' '+name+' '

        dc.SetId(id)
        font = self.GetFont()
        if sys.platform=='darwin':
            basePtSize = (650,750,900)[self.appData['flowSize']]
        elif sys.platform.startswith('linux'):
            basePtSize = (750,850,1000)[self.appData['flowSize']]
        else:
            basePtSize = (700,750,800)[self.appData['flowSize']]
        font.SetPointSize(basePtSize/self.dpi)
        self.SetFont(font)
        dc.SetFont(font)

        #get size based on text
        pad = (5,8,10)[self.appData['flowSize']]
        w,h = self.GetFullTextExtent(name)[0:2]
        x = startX+(endX-startX)/2-w/2-pad/2
        y = (height-h/2)

        #draw box
        rect = wx.Rect(x, y, w+pad,h+pad)
        #the edge should match the text
        dc.SetPen(wx.Pen(wx.Colour(r, g, b, 100)))
        #try to make the loop fill brighter than the background canvas:
        dc.SetBrush(wx.Brush(wx.Colour(235,235,235, 250)))

        dc.DrawRoundedRectangleRect(rect, (4,6,8)[self.appData['flowSize']])
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
            dlg = CodeComponentDialog(frame=self.frame,
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

class RoutinesNotebook(wx.aui.AuiNotebook):
    """A notebook that stores one or more routines
    """
    def __init__(self, frame, id=-1):
        self.frame=frame
        self.app=frame.app
        self.routineMaxSize = 2
        self.appData = self.app.prefs.appData
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
        self.components=components.getAllComponents()
        self.components=experiment.getAllComponents(self.app.prefs.builder['componentsFolders'])
        categories = ['Favorites']
        categories.extend(components.getAllCategories())
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
                label = _localized[categ]
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
            dlg = CodeComponentDialog(frame=self.frame,
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

class ParamCtrls:
    def __init__(self, dlg, label, param, parent, fieldName,
                 browse=False, noCtrls=False, advanced=False, appPrefs=None):
        """Create a set of ctrls for a particular Component Parameter, to be
        used in Component Properties dialogs. These need to be positioned
        by the calling dlg.

        e.g.::

            param = experiment.Param(val='boo', valType='str')
            ctrls=ParamCtrls(dlg=self, label=fieldName,param=param)
            self.paramCtrls[fieldName] = ctrls #keep track of them in the dlg
            sizer.Add(ctrls.nameCtrl, (currRow,0), (1,1),wx.ALIGN_RIGHT )
            sizer.Add(ctrls.valueCtrl, (currRow,1) )
            #these are optional (the parameter might be None)
            if ctrls.typeCtrl: sizer.Add(ctrls.typeCtrl, (currRow,2) )
            if ctrls.updateCtrl: sizer.Add(ctrls.updateCtrl, (currRow,3))

        If browse is True then a browseCtrl will be added (you need to bind events yourself)
        If noCtrls is True then no actual wx widgets are made, but attribute names are created

        `fieldName`'s value is always in en_US, and never for display, whereas `label`
        is only for display and can be translated or tweaked (e.g., add '$').
        Component._localized.keys() are `fieldName`s, and .values() are `label`s.
        """
        self.param = param
        self.dlg = dlg
        self.dpi=self.dlg.dpi
        self.valueWidth = self.dpi*3.5
        #try to find the experiment
        self.exp=None
        tryForExp = self.dlg
        while self.exp is None:
            if hasattr(tryForExp,'frame'):
                self.exp=tryForExp.frame.exp
            else:
                try:
                    tryForExp=tryForExp.parent#try going up a level
                except:
                    tryForExp.parent

        #param has the fields:
        #val, valType, allowedVals=[],allowedTypes=[], hint="", updates=None, allowedUpdates=None
        # we need the following
        self.nameCtrl = self.valueCtrl = self.typeCtrl = self.updateCtrl = None
        self.browseCtrl = None
        if noCtrls:
            return  # we don't need to do any more

        if type(param.val)==numpy.ndarray:
            initial=param.val.tolist() #convert numpy arrays to lists
        #labelLength = wx.Size(self.dpi*2,self.dpi*2/3)#was 8*until v0.91.4
        if param.valType == 'code' and fieldName not in ['name', 'Experiment info']:
            label += ' $'
        self.nameCtrl = wx.StaticText(parent,-1,label,size=None,style=wx.ALIGN_RIGHT)

        if fieldName in ['text', 'customize_everything']:
            #for text input we need a bigger (multiline) box
            if fieldName == 'customize_everything':
                sx,sy = 300,400
            else:
                sx,sy = 100, 100
            self.valueCtrl = CodeBox(parent,-1,
                 pos=wx.DefaultPosition, size=wx.Size(sx,sy),#set the viewer to be small, then it will increase with wx.aui control
                 style=0, prefs=appPrefs)
            if len(param.val):
                self.valueCtrl.AddText(unicode(param.val))
            if fieldName == 'text':
                self.valueCtrl.SetFocus()
        elif fieldName == 'Experiment info':
            #for expInfo convert from a string to the list-of-dicts
            val = self.expInfoToListWidget(param.val)
            self.valueCtrl = dialogs.ListWidget(parent, val, order=['Field','Default'])
        elif param.valType=='extendedCode':
            self.valueCtrl = CodeBox(parent,-1,
                 pos=wx.DefaultPosition, size=wx.Size(100,100),#set the viewer to be small, then it will increase with wx.aui control
                 style=0, prefs=appPrefs)
            if len(param.val):
                self.valueCtrl.AddText(unicode(param.val))
            #code input fields one day change these to wx.stc fields?
            #self.valueCtrl = wx.TextCtrl(parent,-1,unicode(param.val),
            #    style=wx.TE_MULTILINE,
            #    size=wx.Size(self.valueWidth*2,160))
        elif param.valType=='bool':
            #only True or False - use a checkbox
             self.valueCtrl = wx.CheckBox(parent, size = wx.Size(self.valueWidth,-1))
             self.valueCtrl.SetValue(param.val)
        elif len(param.allowedVals)>1:
            #there are limited options - use a Choice control
            # use localized text or fall through to non-localized,
            # for future-proofing, parallel-port addresses, etc:
            choiceLabels = []
            for val in param.allowedVals:
                try:
                    choiceLabels.append(_localized[val])
                except KeyError:
                    choiceLabels.append(val)
            self.valueCtrl = wx.Choice(parent, choices=choiceLabels, size=wx.Size(self.valueWidth,-1))
            # stash original non-localized choices:
            self.valueCtrl._choices = copy.copy(param.allowedVals)
            # set display to the localized version of the currently selected value:
            try:
                index = param.allowedVals.index(param.val)
            except:
                logging.warn("%r was given as parameter %r but it isn't in "
                    "the list of allowed values %s. Reverting to use %r for this Component" %(param.val, fieldName, param.allowedVals, param.allowedVals[0]))
                logging.flush()
                index=0
            self.valueCtrl.SetSelection(index)
        else:
            #create the full set of ctrls
            val = unicode(param.val)
            if fieldName == 'conditionsFile':
                val = getAbbrev(val)
            self.valueCtrl = wx.TextCtrl(parent,-1,val,size=wx.Size(self.valueWidth,-1))
            # focus seems to get reset elsewhere, try "git grep -n SetFocus"
            if fieldName in ['allowedKeys', 'image', 'movie', 'scaleDescription', 'sound', 'Begin Routine']:
                self.valueCtrl.SetFocus()
        self.valueCtrl.SetToolTipString(param.hint)
        if len(param.allowedVals)==1 or param.readOnly:
            self.valueCtrl.Disable()#visible but can't be changed

        # add a NameValidator to name valueCtrl
        if fieldName == "name":
            self.valueCtrl.SetValidator(validators.NameValidator())

        #create the type control
        if len(param.allowedTypes):
            # are there any components with non-empty allowedTypes?
            self.typeCtrl = wx.Choice(parent, choices=param.allowedTypes)
            self.typeCtrl._choices = copy.copy(param.allowedTypes)
            index = param.allowedTypes.index(param.valType)
            self.typeCtrl.SetSelection(index)
            if len(param.allowedTypes)==1:
                self.typeCtrl.Disable()#visible but can't be changed

        #create update control
        if param.allowedUpdates is None or len(param.allowedUpdates)==0:
            pass
        else:
            #updates = display-only version of allowed updates
            updateLabels = [_localized[upd] for upd in param.allowedUpdates]
            #allowedUpdates = extend version of allowed updates that includes "set during:static period"
            allowedUpdates = copy.copy(param.allowedUpdates)
            for routineName, routine in self.exp.routines.items():
                for static in routine.getStatics():
                    updateLabels.append(_translate("set during: %(routineName)s.%(staticName)s") % {'routineName':routineName, 'staticName':static.params['name']})
                    allowedUpdates.append("set during: %(routineName)s.%(staticName)s" % {'routineName':routineName, 'staticName':static.params['name']})
            self.updateCtrl = wx.Choice(parent, choices=updateLabels)
            # stash non-localized choices to allow retrieval by index:
            self.updateCtrl._choices = copy.copy(allowedUpdates)
            # get index of the currently set update value, set display:
            index = allowedUpdates.index(param.updates)
            self.updateCtrl.SetSelection(index)  # set by integer index, not string value

        if param.allowedUpdates!=None and len(param.allowedUpdates)==1:
            self.updateCtrl.Disable()#visible but can't be changed
        #create browse control
        if browse:
            self.browseCtrl = wx.Button(parent, -1, _translate("Browse...")) #we don't need a label for this
    def _getCtrlValue(self, ctrl):
        """Retrieve the current value form the control (whatever type of ctrl it
        is, e.g. checkbox.GetValue, choice.GetSelection)
        Different types of control have different methods for retrieving value.
        This function checks them all and returns the value or None.

        .. note::
            Don't use GetStringSelection() here to avoid that translated value
            is returned. Instead, use GetSelection() to get index of selection
            and get untranslated value from _choices attribute.
        """
        if ctrl is None:
            return None
        elif hasattr(ctrl,'GetText'):
            return ctrl.GetText()
        elif hasattr(ctrl, 'GetValue'): #e.g. TextCtrl
            val = ctrl.GetValue()
            if isinstance(self.valueCtrl, dialogs.ListWidget):
                val = self.expInfoFromListWidget(val)
            return val
        elif hasattr(ctrl, 'GetSelection'): #for wx.Choice
            # _choices is defined during __init__ for all wx.Choice() ctrls
            # NOTE: add untranslated value to _choices if _choices[ctrl.GetSelection()] fails.
            return ctrl._choices[ctrl.GetSelection()]
        elif hasattr(ctrl, 'GetLabel'): #for wx.StaticText
            return ctrl.GetLabel()
        else:
            print "failed to retrieve the value for %s" %(ctrl)
            return None
    def _setCtrlValue(self, ctrl, newVal):
        """Set the current value of the control (whatever type of ctrl it
        is, e.g. checkbox.SetValue, choice.SetSelection)
        Different types of control have different methods for retrieving value.
        This function checks them all and returns the value or None.

        .. note::
            Don't use SetStringSelection() here to avoid using tranlated
            value.  Instead, get index of the value using _choices attribute
            and use SetSelection() to set the value.
        """
        if ctrl is None:
            return None
        elif hasattr(ctrl, 'SetValue'): #e.g. TextCtrl
            ctrl.SetValue(newVal)
        elif hasattr(ctrl, 'SetSelection'): #for wx.Choice
            # _choices = list of non-localized strings, set during __init__
            # NOTE: add untranslated value to _choices if _choices.index(newVal) fails.
            index = ctrl._choices.index(newVal)
            # set the display to the localized version of the string:
            ctrl.SetSelection(index)
        elif hasattr(ctrl, 'SetLabel'): #for wx.StaticText
            ctrl.SetLabel(newVal)
        else:
            print "failed to retrieve the value for %s" %(ctrl)
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
        if self.updateCtrl:
            self.updateCtrl.Show(newVal)
        if self.typeCtrl:
            self.typeCtrl.Show(newVal)
    def expInfoToListWidget(self, expInfoStr):
        """Takes a string describing a dictionary and turns it into a format
        that the ListWidget can receive (list of dicts of Field:'', Default:'')
        """
        expInfo = eval(expInfoStr)
        listOfDicts = []
        for field, default in expInfo.items():
            listOfDicts.append({'Field':field, 'Default':default})
        return listOfDicts
    def expInfoFromListWidget(self, listOfDicts):
        """Creates a string representation of a dict from a list of field/default
        values.
        """
        expInfo = {}
        for field in listOfDicts:
            expInfo[field['Field']] = field['Default']
        expInfoStr = repr(expInfo)
        return expInfoStr

class _BaseParamsDlg(wx.Dialog):
    def __init__(self,frame,title,params,order,
            helpUrl=None, suppressTitles=True,
            showAdvanced=False,
            size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.TAB_TRAVERSAL,editing=False):

        # translate title
        if ' Properties' in title: # Components and Loops
            localizedTitle = title.replace(' Properties',_translate(' Properties'))
        else:
            localizedTitle = _translate(title)

        wx.Dialog.__init__(self, frame,-1,localizedTitle,size=size,style=style) #use translated title for display
        self.frame=frame
        self.app=frame.app
        self.dpi=self.app.dpi
        self.helpUrl=helpUrl
        self.params=params   #dict
        self.title = title
        if not editing and title != 'Experiment Settings' and 'name' in self.params.keys():
            # then we're adding a new component, so provide a known-valid name:
            self.params['name'].val = self.frame.exp.namespace.makeValid(params['name'].val)
        self.paramCtrls={}
        self.suppressTitles = suppressTitles
        self.showAdvanced=showAdvanced
        self.order=order
        self.data = []
        self.nameOKlabel=None
        self.maxFieldLength = 10#max( len(str(self.params[x])) for x in keys )
        self.timeParams=['startType','startVal','stopType','stopVal']
        self.codeFieldNameFromID = {}
        self.codeIDFromFieldName = {}
        self.panels = []# a list of all panels in the ctrl to be traversed by validator

        # for switching font to signal code:
        self.codeFaceName = 'Courier New'  # get another monospace if not available
        # need font size for STCs:
        if wx.Platform == '__WXMSW__':
            self.faceSize = 10
        elif wx.Platform == '__WXMAC__':
            self.faceSize = 14
        else:
            self.faceSize = 12

        #organise the param names by category
        categs = {'Basic':[]}
        for thisName in sorted(self.params):
            thisParam = self.params[thisName]
            if type(thisParam)==list:
                continue#not really a param as such
            thisCateg = thisParam.categ
            if thisCateg not in categs:
                categs[thisCateg] = [thisName]
            else:
                categs[thisCateg].append(thisName)
        if not categs['Basic']: #there were no entries of this categ so delete it
            del categs['Basic']

        #create main sizer
        self.mainSizer=wx.BoxSizer(wx.VERTICAL)
        agwStyle = flatnotebook.FNB_NO_X_BUTTON
        if hasattr(flatnotebook, "FNB_NAV_BUTTONS_WHEN_NEEDED"):
            # not available in wxPython 2.8
            agwStyle |= flatnotebook.FNB_NAV_BUTTONS_WHEN_NEEDED
        if hasattr(flatnotebook, "FNB_NO_TAB_FOCUS"):
            # not available in wxPython 2.8.10
            agwStyle |= flatnotebook.FNB_NO_TAB_FOCUS
        self.ctrls = flatnotebook.FlatNotebook(self, style = agwStyle)
        self.mainSizer.Add(self.ctrls, flag=wx.EXPAND|wx.ALL)#add main controls
        categNames = sorted(categs)
        if 'Basic' in categNames:
            #move it to be the first category we see
            categNames.insert(0, categNames.pop(categNames.index('Basic')))
        # move into _localized after merge branches:
        categLabel = {'Basic': _translate('Basic'), 'Data': _translate('Data'), 'Screen': _translate('Screen'),
                      'Dots': _translate('Dots'), 'Grating': _translate('Grating'),
                      'Advanced': _translate('Advanced'), 'Custom': _translate('Custom')}
        for categName in categNames:
            theseParams = categs[categName]
            page = wx.Panel(self.ctrls, -1)
            ctrls = self.addCategoryOfParams(theseParams, parent=page)
            page.SetSizer(ctrls)
            if categName in categLabel.keys():
                cat = categLabel[categName]
            else:
                cat = categName
            self.ctrls.AddPage(page, cat)
            self.panels.append(page) #so the validator finds this set of controls
            if 'customize_everything' in self.params.keys():
                if self.params['customize_everything'].val.strip():
                    # set focus to the custom panel, because custom will trump others
                    page.SetFocus()
                    self.ctrls.SetSelection(self.ctrls.GetPageCount()-1)
            else:
                self.ctrls.GetPage(0).SetFocus()
                self.ctrls.SetSelection(0)
                if hasattr(self, 'paramCtrls'):
                    if 'name' in self.paramCtrls:
                        self.paramCtrls['name'].valueCtrl.SetFocus()
                    if 'expName' in self.paramCtrls:# ExperimentSettings has expName instead
                        self.paramCtrls['expName'].valueCtrl.SetFocus()
    def addCategoryOfParams(self, paramNames, parent):
        """Add all the params for a single category (after its tab has been created)
        """
        #create the sizers to fit the params and set row to zero
        sizer= wx.GridBagSizer(vgap=2,hgap=2)
        sizer.AddGrowableCol(0)#valueCtrl column
        currRow = 0
        self.useUpdates=False#does the dlg need an 'updates' row (do any params use it?)

        #create a header row of titles
        if not self.suppressTitles:
            size=wx.Size(1.5*self.dpi,-1)
            sizer.Add(wx.StaticText(parent,-1,'Parameter',size=size, style=wx.ALIGN_CENTER),(currRow,0))
            sizer.Add(wx.StaticText(parent,-1,'Value',size=size, style=wx.ALIGN_CENTER),(currRow,1))
            #self.sizer.Add(wx.StaticText(self,-1,'Value Type',size=size, style=wx.ALIGN_CENTER),(currRow,3))
            sizer.Add(wx.StaticText(parent,-1,'Updates',size=size, style=wx.ALIGN_CENTER),(currRow,2))
            currRow+=1
            sizer.Add(
                wx.StaticLine(parent, size=wx.Size(100,20)),
                (currRow,0),(1,2), wx.ALIGN_CENTER|wx.EXPAND)
        currRow+=1

        #get all params and sort
        remaining = copy.copy(paramNames)

        #start with the name (always)
        if 'name' in remaining:
            self.addParam('name', parent, sizer, currRow)
            currRow += 1
            remaining.remove('name')
            if 'name' in self.order:
                self.order.remove('name')
            currRow+=1
        #add start/stop info
        if 'startType' in remaining:
            remaining, currRow = self.addStartStopCtrls(remaining, parent, sizer, currRow)
        currRow += 1
        #loop through the prescribed order (the most important?)
        for fieldName in self.order:
            if fieldName not in paramNames:
                continue#skip advanced params
            self.addParam(fieldName, parent, sizer, currRow, valType=self.params[fieldName].valType)
            currRow += 1
            remaining.remove(fieldName)
        #add any params that weren't specified in the order
        for fieldName in remaining:
            self.addParam(fieldName, parent, sizer, currRow, valType=self.params[fieldName].valType)
            currRow += 1
        return sizer

    def addStartStopCtrls(self,remaining, parent, sizer, currRow):
        """Add controls for startType, startVal, stopType, stopVal
        remaining refers to
        """
        ##Start point
        startTypeParam = self.params['startType']
        startValParam = self.params['startVal']
        #create label
        label = wx.StaticText(parent,-1,_translate('Start'), style=wx.ALIGN_CENTER)
        labelEstim = wx.StaticText(parent,-1,_translate('Expected start (s)'), style=wx.ALIGN_CENTER)
        labelEstim.SetForegroundColour('gray')
        #the method to be used to interpret this start/stop
        self.startTypeCtrl = wx.Choice(parent, choices=map(_translate,startTypeParam.allowedVals))
        self.startTypeCtrl.SetStringSelection(_translate(startTypeParam.val))
        self.startTypeCtrl.SetToolTipString(self.params['startType'].hint)
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
        startEstimSizer.Add(labelEstim, flag = wx.ALIGN_CENTRE_VERTICAL|wx.ALIGN_LEFT)
        startEstimSizer.Add(self.startEstimCtrl, flag = wx.ALIGN_BOTTOM)
        startAllCrtlSizer = wx.BoxSizer(orient=wx.VERTICAL)
        startAllCrtlSizer.Add(startSizer,flag=wx.EXPAND)
        startAllCrtlSizer.Add(startEstimSizer, flag=wx.ALIGN_RIGHT)
        sizer.Add(label, (currRow,0),(1,1),wx.ALIGN_RIGHT)
        #add our new row
        sizer.Add(startAllCrtlSizer,(currRow,1),(1,1),flag=wx.EXPAND)
        currRow+=1
        remaining.remove('startType')
        remaining.remove('startVal')
        remaining.remove('startEstim')

        ##Stop point
        stopTypeParam = self.params['stopType']
        stopValParam = self.params['stopVal']
        #create label
        label = wx.StaticText(parent,-1,_translate('Stop'), style=wx.ALIGN_CENTER)
        labelEstim = wx.StaticText(parent,-1,_translate('Expected duration (s)'), style=wx.ALIGN_CENTER)
        labelEstim.SetForegroundColour('gray')
        #the method to be used to interpret this start/stop
        self.stopTypeCtrl = wx.Choice(parent, choices=map(_translate,stopTypeParam.allowedVals))
        self.stopTypeCtrl.SetStringSelection(_translate(stopTypeParam.val))
        self.stopTypeCtrl.SetToolTipString(self.params['stopType'].hint)
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
        stopEstimSizer.Add(labelEstim, flag = wx.ALIGN_CENTRE_VERTICAL)
        stopEstimSizer.Add(self.durationEstimCtrl, flag = wx.ALIGN_CENTRE_VERTICAL)
        stopAllCrtlSizer = wx.BoxSizer(orient=wx.VERTICAL)
        stopAllCrtlSizer.Add(stopSizer,flag=wx.EXPAND)
        stopAllCrtlSizer.Add(stopEstimSizer, flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL)
        sizer.Add(label, (currRow,0),(1,1),wx.ALIGN_RIGHT)
        #add our new row
        sizer.Add(stopAllCrtlSizer,(currRow,1),(1,1),flag=wx.EXPAND)
        currRow+=1
        remaining.remove('stopType')
        remaining.remove('stopVal')
        remaining.remove('durationEstim')

        # use monospace font to signal code:
        self.checkCodeWanted(self.startValCtrl)
        self.startValCtrl.Bind(wx.EVT_KEY_UP, self.checkCodeWanted)
        self.checkCodeWanted(self.stopValCtrl)
        self.stopValCtrl.Bind(wx.EVT_KEY_UP, self.checkCodeWanted)

        return remaining, currRow

    def addParam(self,fieldName, parent, sizer, currRow, advanced=False, valType=None):
        """Add a parameter to the basic sizer
        """
        param=self.params[fieldName]
        if param.label not in [None, '']:
            label=param.label
        else:
            label=fieldName
        ctrls=ParamCtrls(dlg=self, parent=parent, label=label, fieldName=fieldName,
                         param=param, advanced=advanced, appPrefs=self.app.prefs)
        self.paramCtrls[fieldName] = ctrls
        if fieldName=='name':
            ctrls.valueCtrl.Bind(wx.EVT_TEXT, self.checkName)
            ctrls.valueCtrl.SetFocus()
        # self.valueCtrl = self.typeCtrl = self.updateCtrl
        sizer.Add(ctrls.nameCtrl, (currRow,0), border=5,
            flag=wx.ALIGN_RIGHT|wx.ALIGN_CENTRE_VERTICAL|wx.LEFT|wx.RIGHT)
        sizer.Add(ctrls.valueCtrl, (currRow,1), border=5,
            flag=wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL | wx.ALL)
        if ctrls.updateCtrl:
            sizer.Add(ctrls.updateCtrl, (currRow,2))
        if ctrls.typeCtrl:
            sizer.Add(ctrls.typeCtrl, (currRow,3) )
        if fieldName in ['text']:
            sizer.AddGrowableRow(currRow)#doesn't seem to work though
            #self.Bind(EVT_ETC_LAYOUT_NEEDED, self.onNewTextSize, ctrls.valueCtrl)
        elif fieldName in ['color', 'fillColor', 'lineColor']:
            ctrls.valueCtrl.Bind(wx.EVT_RIGHT_DOWN, self.launchColorPicker)
        elif valType == 'extendedCode':
            sizer.AddGrowableRow(currRow)#doesn't seem to work though
            ctrls.valueCtrl.Bind(wx.EVT_KEY_DOWN, self.onTextEventCode)
        elif fieldName=='Monitor':
            ctrls.valueCtrl.Bind(wx.EVT_RIGHT_DOWN, self.openMonitorCenter)

        # use monospace font to signal code:
        if fieldName != 'name' and hasattr(ctrls.valueCtrl, 'GetFont'):
            if self.params[fieldName].valType == 'code':
                ctrls.valueCtrl.SetFont(self.app._codeFont)
            elif self.params[fieldName].valType == 'str':
                ctrls.valueCtrl.Bind(wx.EVT_KEY_UP, self.checkCodeWanted)
                try:
                    self.checkCodeWanted(ctrls.valueCtrl)
                except:
                    pass

    def openMonitorCenter(self,event):
        self.app.openMonitorCenter(event)
        self.paramCtrls['Monitor'].valueCtrl.SetFocus()
        # need to delay until the user closes the monitor center
        #self.paramCtrls['Monitor'].valueCtrl.Clear()
        #if wx.TheClipboard.Open():
        #    dataObject = wx.TextDataObject()
        #    if wx.TheClipboard.GetData(dataObject):
        #        self.paramCtrls['Monitor'].valueCtrl.WriteText(dataObject.GetText())
        #    wx.TheClipboard.Close()
    def launchColorPicker(self, event):
        # bring up a colorPicker
        rgb = self.app.colorPicker(None) # str, remapped to -1..+1
        self.paramCtrls['color'].valueCtrl.SetFocus()
        self.paramCtrls['color'].valueCtrl.Clear()
        self.paramCtrls['color'].valueCtrl.WriteText('$'+rgb) # $ flag as code
        ii = self.paramCtrls['colorSpace'].valueCtrl.FindString('rgb')
        self.paramCtrls['colorSpace'].valueCtrl.SetSelection(ii)

    def onNewTextSize(self, event):
        self.Fit()#for ExpandoTextCtrl this is needed

    def show(self):
        """Adds an OK and cancel button, shows dialogue.

        This method returns wx.ID_OK (as from ShowModal), but also
        sets self.OK to be True or False
        """
        #add a label to check name
        if 'name' in self.params.keys():
            #if len(self.params['name'].val):
            #    nameInfo=''
            #else:
            #    nameInfo='Need a name'
            nameInfo = ''
            self.nameOKlabel=wx.StaticText(self,-1,nameInfo,size=(300,25),
                                        style=wx.ALIGN_CENTRE)
            self.nameOKlabel.SetForegroundColour(wx.RED)
            self.mainSizer.Add(self.nameOKlabel, wx.ALIGN_CENTRE|wx.EXPAND)
        #add buttons for OK and Cancel
        buttons = wx.StdDialogButtonSizer()
        #help button if we know the url
        if self.helpUrl!=None:
            helpBtn = wx.Button(self, wx.ID_HELP, _translate(" Help "))
            helpBtn.SetToolTip(wx.ToolTip(_translate("Go to online help about this component")))
            helpBtn.Bind(wx.EVT_BUTTON, self.onHelp)
            buttons.Add(helpBtn, 0, wx.ALIGN_LEFT|wx.ALL,border=3)
            buttons.AddSpacer(12)
        self.OKbtn = wx.Button(self, wx.ID_OK, _translate(" OK "))
        # intercept OK button if a loop dialog, in case file name was edited:
        if type(self) == DlgLoopProperties:
            self.OKbtn.Bind(wx.EVT_BUTTON, self.onOK)
        self.OKbtn.SetDefault()

        self.checkName() # disables OKbtn if bad name
        buttons.Add(self.OKbtn, 0, wx.ALL,border=3)
        CANCEL = wx.Button(self, wx.ID_CANCEL, _translate(" Cancel "))
        buttons.Add(CANCEL, 0, wx.ALL,border=3)
        buttons.Realize()
        #add to sizer
        self.mainSizer.Add(buttons, flag=wx.ALIGN_RIGHT)
        border = wx.BoxSizer(wx.VERTICAL)
        border.Add(self.mainSizer, flag=wx.ALL|wx.EXPAND, border=8)
        self.SetSizerAndFit(border)
        #move the position to be v near the top of screen and to the right of the left-most edge of builder
        builderPos = self.frame.GetPosition()
        self.SetPosition((builderPos[0]+200,20))

        #self.paramCtrls['name'].valueCtrl.SetFocus()
        #do show and process return
        retVal = self.ShowModal()
        if retVal== wx.ID_OK:
            self.OK=True
        else:
            self.OK=False
        return wx.ID_OK

    def Validate(self, *args, **kwargs):
        """
        Validate form data and disable OK button if validation fails.
        """
        valid = super(_BaseParamsDlg, self).Validate(*args, **kwargs)
        #also validate each page in the ctrls notebook
        for thisPanel in self.panels:
            stillValid = thisPanel.Validate()
            valid = valid and stillValid
        if valid:
            self.OKbtn.Enable()
        else:
            self.OKbtn.Disable()
        return valid

    def onOK(self, event=None):
        """
        Handler for OK button which should validate dialog contents.
        """
        valid = self.Validate()
        if not valid:
            return
        event.Skip()

    def onTextEventCode(self, event=None):
        """process text events for code components: change color to grey
        """
        codeBox = event.GetEventObject()
        textBeforeThisKey = codeBox.GetText()
        keyCode = event.GetKeyCode()
        pos = event.GetPosition()
        if keyCode<256 and keyCode not in [10,13]: # ord(10)='\n', ord(13)='\l'
            #new line is trigger to check syntax
            codeBox.setStatus('changed')
        elif keyCode in [10,13] and len(textBeforeThisKey) and textBeforeThisKey[-1] != ':':
            # ... but skip the check if end of line is colon ord(58)=':'
            self._setNameColor(self._testCompile(codeBox))
        event.Skip()
    def _testCompile(self, ctrl, mode='exec'):
        """checks whether code.val is legal python syntax, returns error status

        mode = 'exec' (statement or expr) or 'eval' (expr only)
        """
        if hasattr(ctrl,'GetText'):
            val = ctrl.GetText()
        elif hasattr(ctrl, 'GetValue'):  #e.g. TextCtrl
            val = ctrl.GetValue()
        else:
            raise ValueError, 'Unknown type of ctrl in _testCompile: %s' %(type(ctrl))
        try:
            compile(val, '', mode)
            syntaxOk = True
            ctrl.setStatus('OK')
        except SyntaxError:
            ctrl.setStatus('error')
            syntaxOk = False
        return syntaxOk

    def checkCodeSyntax(self, event=None):
        """Checks syntax for whole code component by code box, sets box bg-color.
        """
        if hasattr(event, 'GetEventObject'):
            codeBox = event.GetEventObject()
        elif hasattr(event,'GetText'):
            codeBox = event #we were given the control itself, not an event
        else:
            raise ValueError('checkCodeSyntax received unexpected event object (%s). Should be a wx.Event or a CodeBox' %type(event))
        text = codeBox.GetText()
        if not text.strip(): # if basically empty
            codeBox.SetBackgroundColour(white)
            return # skip test
        goodSyntax = self._testCompile(codeBox) # test syntax
        #not quite every dialog has a name (e.g. settings) but if so then set its color
        if 'name' in self.paramCtrls:
            self._setNameColor(goodSyntax)
    def _setNameColor(self, goodSyntax):
        if goodSyntax:
            self.paramCtrls['name'].valueCtrl.SetBackgroundColour(codeSyntaxOkay)
            self.nameOKlabel.SetLabel("")
        else:
            self.paramCtrls['name'].valueCtrl.SetBackgroundColour(white)
            self.nameOKlabel.SetLabel('syntax error')

    def checkCodeWanted(self, event=None):
        """check whether a $ is present (if so, set the display font)
        """
        if hasattr(event, 'GetEventObject'):
            strBox = event.GetEventObject()
        elif hasattr(event, 'GetValue'):
            strBox = event  # we were given the control itself, not an event
        else:
            raise ValueError('checkCodeWanted received unexpected event object (%s).')
        try:
            val = strBox.GetValue()
            stc = False
        except:
            if not hasattr(strBox, 'GetText'):  # eg, wx.Choice control
                if hasattr(event, 'Skip'):
                    event.Skip()
                return
            val = strBox.GetText()
            stc = True  # might be StyledTextCtrl

        # set display font based on presence of $ (without \$)?
        font = strBox.GetFont()
        if _unescapedDollarSign_re.search(val):
            strBox.SetFont(self.app._codeFont)
        else:
            strBox.SetFont(self.app._mainFont)

        if hasattr(event, 'Skip'):
            event.Skip()

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
                param.val = self.params['startType'].allowedVals[self.startTypeCtrl.GetCurrentSelection()]
            elif fieldName=='stopType':
                param.val = self.params['stopType'].allowedVals[self.stopTypeCtrl.GetCurrentSelection()]
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
                if ctrls.typeCtrl:
                    param.valType = ctrls.getType()
                if ctrls.updateCtrl:
                    #may also need to update a static
                    updates = ctrls.getUpdates()
                    if param.updates != updates:
                        self._updateStaticUpdates(fieldName, param.updates, updates)
                        param.updates=updates
        return self.params
    def _updateStaticUpdates(self, fieldName, updates, newUpdates):
        """If the old/new updates ctrl is using a Static component then we
        need to remove/add the component name to the appropriate static
        """
        exp = self.frame.exp
        compName = self.params['name'].val
        if hasattr(updates, 'startswith') and "during:" in updates:
            updates = updates.split(': ')[1] #remove the part that says 'during'
            origRoutine, origStatic =  updates.split('.')
            if exp.routines[origRoutine].getComponentFromName(origStatic) != None:
                exp.routines[origRoutine].getComponentFromName(origStatic).remComponentUpdate(
                    origRoutine, compName, fieldName)
        if hasattr(newUpdates, 'startswith') and "during:" in newUpdates:
            newUpdates = newUpdates.split(': ')[1] #remove the part that says 'during'
            newRoutine, newStatic =  newUpdates.split('.')
            exp.routines[newRoutine].getComponentFromName(newStatic).addComponentUpdate(
                newRoutine, compName, fieldName)
    def _checkName(self, event=None, name=None):
        """checks namespace, return error-msg (str), enable (bool)
        """
        if event:
            newName = event.GetString()
        elif name:
            newName = name
        elif hasattr(self, 'paramCtrls'):
            newName=self.paramCtrls['name'].getValue()
        elif hasattr(self, 'globalCtrls'):
            newName=self.globalCtrls['name'].getValue()
        if newName=='':
            return _translate("Missing name"), False
        else:
            namespace = self.frame.exp.namespace
            used = namespace.exists(newName)
            same_as_old_name = bool(newName == self.params['name'].val)
            if used and not same_as_old_name:
                return _translate("That name is in use (it's a %s). Try another name.") % namespace._localized(used), False
            elif not namespace.isValid(newName): # valid as a var name
                return _translate("Name must be alpha-numeric or _, no spaces"), False
            elif namespace.isPossiblyDerivable(newName): # warn but allow, chances are good that its actually ok
                msg = namespace.isPossiblyDerivable(newName)
                return namespace._localized(msg), True
            else:
                return "", True
    def checkName(self, event=None):
        """
        Issue a form validation on name change.
        """
        self.Validate()

    def onHelp(self, event=None):
        """Uses self.app.followLink() to self.helpUrl
        """
        self.app.followLink(url=self.helpUrl)

class DlgLoopProperties(_BaseParamsDlg):
    def __init__(self,frame,title="Loop Properties",loop=None,
            helpUrl=None,
            pos=wx.DefaultPosition, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT|wx.RESIZE_BORDER):
        # translate title
        localizedTitle = title.replace(' Properties',_translate(' Properties'))

        wx.Dialog.__init__(self, frame,-1,localizedTitle,pos,size,style) # use localized title
        self.helpUrl=helpUrl
        self.frame=frame
        self.exp=frame.exp
        self.app=frame.app
        self.dpi=self.app.dpi
        self.params={}
        self.panel = wx.Panel(self, -1)
        self.globalCtrls={}
        self.constantsCtrls={}
        self.staircaseCtrls={}
        self.multiStairCtrls={}
        self.currentCtrls={}
        self.data = []
        self.mainSizer= wx.BoxSizer(wx.VERTICAL)
        self.conditions=None
        self.conditionsFile=None
        #create a valid new name; save old name in case we need to revert
        defaultName = 'trials'
        oldLoopName = defaultName
        if loop:
            oldLoopName = loop.params['name'].val
        namespace = frame.exp.namespace
        new_name = namespace.makeValid(oldLoopName)
        #create default instances of the diff loop types
        self.trialHandler=experiment.TrialHandler(exp=self.exp, name=new_name,
            loopType='random',nReps=5,conditions=[]) #for 'random','sequential', 'fullRandom'
        self.stairHandler=experiment.StairHandler(exp=self.exp, name=new_name,
            nReps=50, nReversals='',
            stepSizes='[0.8,0.8,0.4,0.4,0.2]', stepType='log', startVal=0.5) #for staircases
        self.multiStairHandler=experiment.MultiStairHandler(exp=self.exp, name=new_name,
            nReps=50, stairType='simple', switchStairs='random',
            conditions=[], conditionsFile='')
        #replace defaults with the loop we were given
        if loop is None:
            self.currentType='random'
            self.currentHandler=self.trialHandler
        elif loop.type=='TrialHandler':
            self.conditions=loop.params['conditions'].val
            self.conditionsFile=loop.params['conditionsFile'].val
            self.trialHandler = self.currentHandler = loop
            self.currentType=loop.params['loopType'].val #could be 'random', 'sequential', 'fullRandom'
        elif loop.type=='StairHandler':
            self.stairHandler = self.currentHandler = loop
            self.currentType='staircase'
        elif loop.type=='MultiStairHandler':
            self.conditions=loop.params['conditions'].val
            self.conditionsFile=loop.params['conditionsFile'].val
            self.multiStairHandler = self.currentHandler = loop
            self.currentType='interleaved staircases'
        elif loop.type=='QuestHandler':
            pass # what to do for quest?
        self.params['name']=self.currentHandler.params['name']
        self.globalPanel = self.makeGlobalCtrls()
        self.stairPanel = self.makeStaircaseCtrls()
        self.constantsPanel = self.makeConstantsCtrls()#the controls for Method of Constants
        self.multiStairPanel = self.makeMultiStairCtrls()
        self.mainSizer.Add(self.globalPanel, border=5, flag=wx.ALL|wx.ALIGN_CENTRE)
        self.mainSizer.Add(wx.StaticLine(self), border=5, flag=wx.ALL|wx.EXPAND)
        self.mainSizer.Add(self.stairPanel, border=5, flag=wx.ALL|wx.ALIGN_CENTRE)
        self.mainSizer.Add(self.constantsPanel, border=5, flag=wx.ALL|wx.ALIGN_CENTRE)
        self.mainSizer.Add(self.multiStairPanel, border=5, flag=wx.ALL|wx.ALIGN_CENTRE)
        self.setCtrls(self.currentType)
        # create a list of panels in the dialog, for the validator to step through
        self.panels = [self.globalPanel, self.stairPanel, self.constantsPanel, self.multiStairPanel]


        #show dialog and get most of the data
        self.show()
        if self.OK:
            self.params = self.getParams()
            #convert endPoints from str to list
            exec("self.params['endPoints'].val = %s" %self.params['endPoints'].val)
            #then sort the list so the endpoints are in correct order
            self.params['endPoints'].val.sort()
            if loop: # editing an existing loop
                namespace.remove(oldLoopName)
            namespace.add(self.params['name'].val)
            # don't always have a conditionsFile
            if hasattr(self, 'condNamesInFile'):
                namespace.add(self.condNamesInFile)
            if hasattr(self, 'duplCondNames'):
                namespace.remove(self.duplCondNames)
        else:
            if loop!=None:#if we had a loop during init then revert to its old name
                loop.params['name'].val = oldLoopName

        #make sure we set this back regardless of whether OK
        #otherwise it will be left as a summary string, not a conditions
        if 'conditionsFile' in self.currentHandler.params:
            self.currentHandler.params['conditions'].val=self.conditions

    def makeGlobalCtrls(self):
        panel = wx.Panel(parent=self)
        panelSizer = wx.GridBagSizer(5,5)
        panel.SetSizer(panelSizer)
        row=0
        for fieldName in ['name','loopType','isTrials']:
            try:
                label = self.currentHandler.params[fieldName].label
            except:
                label = fieldName
            self.globalCtrls[fieldName] = ctrls = ParamCtrls(dlg=self, parent=panel,
                label=label,fieldName=fieldName,
                param=self.currentHandler.params[fieldName])
            panelSizer.Add(ctrls.nameCtrl, [row, 0], border=1,
                flag=wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL | wx.ALL)
            panelSizer.Add(ctrls.valueCtrl, [row, 1], border=1,
                flag=wx.EXPAND | wx.ALIGN_CENTRE_VERTICAL | wx.ALL)
            row += 1

        self.globalCtrls['name'].valueCtrl.Bind(wx.EVT_TEXT, self.checkName)
        self.Bind(wx.EVT_CHOICE, self.onTypeChanged, self.globalCtrls['loopType'].valueCtrl)
        return panel

    def makeConstantsCtrls(self):
        #a list of controls for the random/sequential versions
        #that can be hidden or shown
        handler=self.trialHandler
        #loop through the params
        keys = handler.params.keys()
        panel = wx.Panel(parent=self)
        panelSizer = wx.GridBagSizer(5,5)
        panel.SetSizer(panelSizer)
        row=0
        #add conditions stuff to the *end*
        if 'conditionsFile' in keys:
            keys.remove('conditionsFile')
            keys.append('conditionsFile')
        if 'conditions' in keys:
            keys.remove('conditions')
            keys.append('conditions')
        #then step through them
        for fieldName in keys:
            #try and get alternative "label" for the parameter
            try:
                label = self.currentHandler.params[fieldName].label
                if not label: #it might exist but be empty
                    label = fieldName
            except:
                label = fieldName
            #handle special cases
            if fieldName=='endPoints':
                continue#this was deprecated in v1.62.00
            if fieldName in self.globalCtrls:
                #these have already been made and inserted into sizer
                ctrls=self.globalCtrls[fieldName]
            elif fieldName=='conditionsFile':
                ctrls=ParamCtrls(dlg=self, parent=panel, label=label,fieldName=fieldName,
                    param=handler.params[fieldName], browse=True)
                self.Bind(wx.EVT_BUTTON, self.onBrowseTrialsFile,ctrls.browseCtrl)
                ctrls.valueCtrl.Bind(wx.EVT_RIGHT_DOWN, self.viewConditions)
                panelSizer.Add(ctrls.nameCtrl, [row, 0])
                panelSizer.Add(ctrls.valueCtrl, [row, 1])
                panelSizer.Add(ctrls.browseCtrl, [row, 2])
                row += 1
            elif fieldName=='conditions':
                if 'conditions' in handler.params:
                    text=self.getTrialsSummary(handler.params['conditions'].val)
                else:
                    text = _translate("No parameters set")
                ctrls = ParamCtrls(dlg=self, parent=panel, label=label, fieldName=fieldName,
                    param=text, noCtrls=True)#we'll create our own widgets
                size = wx.Size(350, 50)
                ctrls.valueCtrl = wx.StaticText(panel, label=text, size=size, style=wx.ALIGN_CENTER)
                panelSizer.Add(ctrls.valueCtrl, (row, 0), span=(1,3), flag=wx.ALIGN_CENTER)
                row += 1
            else: #normal text entry field
                ctrls=ParamCtrls(dlg=self, parent=panel, label=label,fieldName=fieldName,
                    param=handler.params[fieldName])
                panelSizer.Add(ctrls.nameCtrl, [row, 0])
                panelSizer.Add(ctrls.valueCtrl, [row, 1])
                row += 1
            #store info about the field
            self.constantsCtrls[fieldName] = ctrls
        return panel

    def makeMultiStairCtrls(self):
        #a list of controls for the random/sequential versions
        panel = wx.Panel(parent=self)
        panelSizer = wx.GridBagSizer(5,5)
        panel.SetSizer(panelSizer)
        row=0
        #that can be hidden or shown
        handler=self.multiStairHandler
        #loop through the params
        keys = handler.params.keys()
        #add conditions stuff to the *end*
        #add conditions stuff to the *end*
        if 'conditionsFile' in keys:
            keys.remove('conditionsFile')
            keys.append('conditionsFile')
        if 'conditions' in keys:
            keys.remove('conditions')
            keys.append('conditions')
        #then step through them
        for fieldName in keys:
            #try and get alternative "label" for the parameter
            try:
                label = handler.params[fieldName].label
                if not label: #it might exist but be empty
                    label = fieldName
            except:
                label = fieldName
            #handle special cases
            if fieldName=='endPoints':
                continue  #this was deprecated in v1.62.00
            if fieldName in self.globalCtrls:
                #these have already been made and inserted into sizer
                ctrls=self.globalCtrls[fieldName]
            elif fieldName=='conditionsFile':
                ctrls=ParamCtrls(dlg=self, parent=panel, label=label, fieldName=fieldName,
                    param=handler.params[fieldName], browse=True)
                self.Bind(wx.EVT_BUTTON, self.onBrowseTrialsFile,ctrls.browseCtrl)
                panelSizer.Add(ctrls.nameCtrl, [row, 0])
                panelSizer.Add(ctrls.valueCtrl, [row, 1])
                panelSizer.Add(ctrls.browseCtrl, [row, 2])
                row += 1
            elif fieldName=='conditions':
                if 'conditions' in handler.params:
                    text=self.getTrialsSummary(handler.params['conditions'].val)
                else:
                    text = _translate("No parameters set (select a file above)")
                ctrls = ParamCtrls(dlg=self, parent=panel, label=label, fieldName=fieldName,
                    param=text, noCtrls=True)#we'll create our own widgets
                size = wx.Size(350, 50)
                ctrls.valueCtrl = wx.StaticText(panel, label=text, size=size, style=wx.ALIGN_CENTER)
                panelSizer.Add(ctrls.valueCtrl, (row, 0), span=(1,3), flag=wx.ALIGN_CENTER)
                row += 1
            else: #normal text entry field
                ctrls=ParamCtrls(dlg=self, parent=panel, label=label, fieldName=fieldName,
                    param=handler.params[fieldName])
                panelSizer.Add(ctrls.nameCtrl, [row, 0])
                panelSizer.Add(ctrls.valueCtrl, [row, 1])
                row += 1
            #store info about the field
            self.multiStairCtrls[fieldName] = ctrls
        return panel

    def makeStaircaseCtrls(self):
        """Setup the controls for a StairHandler"""
        panel = wx.Panel(parent=self)
        panelSizer = wx.GridBagSizer(5,5)
        panel.SetSizer(panelSizer)
        row=0
        handler=self.stairHandler
        #loop through the params
        for fieldName in handler.params:
            #try and get alternative "label" for the parameter
            try:
                label = handler.params[fieldName].label
                if not label: #it might exist but be empty
                    label = fieldName
            except:
                label = fieldName
            #handle special cases
            if fieldName=='endPoints':
                continue#this was deprecated in v1.62.00
            if fieldName in self.globalCtrls:
                #these have already been made and inserted into sizer
                ctrls=self.globalCtrls[fieldName]
            else: #normal text entry field
                ctrls=ParamCtrls(dlg=self, parent=panel, label=label, fieldName=fieldName,
                    param=handler.params[fieldName])
                panelSizer.Add(ctrls.nameCtrl, [row, 0])
                panelSizer.Add(ctrls.valueCtrl, [row, 1])
                row += 1
            #store info about the field
            self.staircaseCtrls[fieldName] = ctrls
        return panel
    def getTrialsSummary(self, conditions):
        if type(conditions)==list and len(conditions)>0:
            #get attr names (conditions[0].keys() inserts u'name' and u' is annoying for novice)
            paramStr = "["
            for param in conditions[0]:
                paramStr += (unicode(param)+', ')
            paramStr = paramStr[:-2]+"]"#remove final comma and add ]
            #generate summary info
            return _translate('%(nCondition)i conditions, with %(nParam)i parameters\n%(paramStr)s') \
                % {'nCondition':len(conditions), 'nParam':len(conditions[0]), 'paramStr':paramStr}
        else:
            if self.conditionsFile and not os.path.isfile(self.conditionsFile):
                return  _translate("No parameters set (conditionsFile not found)")
            return _translate("No parameters set")
    def viewConditions(self, event):
        """ display Condition x Parameter values from within a file
        make new if no self.conditionsFile is set
        """
        self.refreshConditions()
        conditions = self.conditions # list of dict
        if self.conditionsFile:
            # get name + dir, like BART/trialTypes.xlsx
            fileName = os.path.abspath(self.conditionsFile)
            fileName = fileName.rsplit(os.path.sep,2)[1:]
            fileName = os.path.join(*fileName)
            if fileName.endswith('.pkl'):
                # edit existing .pkl file, loading from file
                gridGUI = DlgConditions(fileName=self.conditionsFile,
                                            parent=self, title=fileName)
            else:
                # preview existing .csv or .xlsx file that has already been loaded -> conditions
                # better to reload file, get fieldOrder as well
                gridGUI = DlgConditions(conditions, parent=self,
                                        title=fileName, fixed=True)
        else: # edit new empty .pkl file
            gridGUI = DlgConditions(parent=self)
            # should not check return value, its meaningless
            if gridGUI.OK:
                self.conditions = gridGUI.asConditions()
                if hasattr(gridGUI, 'fileName'):
                    self.conditionsFile = gridGUI.fileName
        self.currentHandler.params['conditionsFile'].val = self.conditionsFile
        if 'conditionsFile' in self.currentCtrls.keys(): # as set via DlgConditions
            valCtrl = self.currentCtrls['conditionsFile'].valueCtrl
            valCtrl.Clear()
            valCtrl.WriteText(getAbbrev(self.conditionsFile))
        # still need to do namespace and internal updates (see end of onBrowseTrialsFile)

    def setCtrls(self, ctrlType):
        #choose the ctrls to show/hide
        if ctrlType=='staircase':
            self.currentHandler = self.stairHandler
            self.stairPanel.Show()
            self.constantsPanel.Hide()
            self.multiStairPanel.Hide()
            self.currentCtrls = self.staircaseCtrls
        elif ctrlType=='interleaved staircases':
            self.currentHandler = self.multiStairHandler
            self.stairPanel.Hide()
            self.constantsPanel.Hide()
            self.multiStairPanel.Show()
            self.currentCtrls = self.multiStairCtrls
        else:
            self.currentHandler = self.trialHandler
            self.stairPanel.Hide()
            self.constantsPanel.Show()
            self.multiStairPanel.Hide()
            self.currentCtrls = self.constantsCtrls
        self.currentType=ctrlType
        #redo layout
        self.mainSizer.Layout()
        self.Fit()
        self.Refresh()
    def onTypeChanged(self, evt=None):
        newType = evt.GetString()
        if newType==self.currentType:
            return
        self.setCtrls(newType)
    def onBrowseTrialsFile(self, event):
        self.conditionsFileOrig = self.conditionsFile
        self.conditionsOrig = self.conditions
        expFolder,expName = os.path.split(self.frame.filename)
        dlg = wx.FileDialog(self, message=_translate("Open file ..."), style=wx.OPEN,
                            defaultDir=expFolder)
        if dlg.ShowModal() == wx.ID_OK:
            newFullPath = dlg.GetPath()
            if self.conditionsFile:
                oldFullPath = os.path.abspath(os.path.join(expFolder, self.conditionsFile))
                isSameFilePathAndName = (newFullPath==oldFullPath)
            else:
                isSameFilePathAndName = False
            newPath = _relpath(newFullPath, expFolder)
            self.conditionsFile = newPath
            needUpdate = False
            try:
                self.conditions, self.condNamesInFile = data.importConditions(dlg.GetPath(),
                                                        returnFieldNames=True)
                needUpdate = True
            except ImportError, msg:
                msg = str(msg)
                if msg.startswith('Could not open'):
                    self.currentCtrls['conditions'].setValue(_translate('Could not read conditions from:\n') + newFullPath.split(os.path.sep)[-1])
                    logging.error('Could not open as a conditions file: %s' % newFullPath)
                else:
                    m2 = msg.replace('Conditions file ', '')
                    dlgErr = dialogs.MessageDialog(parent=self.frame,
                        message=m2.replace(': ', os.linesep * 2), type='Info',
                        title=_translate('Configuration error in conditions file')).ShowModal()
                    self.currentCtrls['conditions'].setValue(
                        _translate('Bad condition name(s) in file:\n') + newFullPath.split(os.path.sep)[-1])
                    logging.error('Rejected bad condition name(s) in file: %s' % newFullPath)
                self.conditionsFile = self.conditionsFileOrig
                self.conditions = self.conditionsOrig
                return # no update or display changes
            duplCondNames = []
            if len(self.condNamesInFile):
                for condName in self.condNamesInFile:
                    if self.exp.namespace.exists(condName):
                        duplCondNames.append(condName)
            # abbrev long strings to better fit in the dialog:
            duplCondNamesStr = ' '.join(duplCondNames)[:42]
            if len(duplCondNamesStr)==42:
                duplCondNamesStr = duplCondNamesStr[:39]+'...'
            if len(duplCondNames):
                if isSameFilePathAndName:
                    logging.info('Assuming reloading file: same filename and duplicate condition names in file: %s' % self.conditionsFile)
                else:
                    self.currentCtrls['conditionsFile'].setValue(getAbbrev(newPath))
                    self.currentCtrls['conditions'].setValue(
                        'Warning: Condition names conflict with existing:\n['+duplCondNamesStr+
                        ']\nProceed anyway? (= safe if these are in old file)')
                    logging.warning('Duplicate condition names, different conditions file: %s' % duplCondNamesStr)
            # stash condition names but don't add to namespace yet, user can still cancel
            self.duplCondNames = duplCondNames # add after self.show() in __init__

            if needUpdate or 'conditionsFile' in self.currentCtrls.keys() and not duplCondNames:
                self.currentCtrls['conditionsFile'].setValue(getAbbrev(newPath))
                self.currentCtrls['conditions'].setValue(self.getTrialsSummary(self.conditions))

    def getParams(self):
        """Retrieves data and re-inserts it into the handler and returns those handler params
        """
        #get data from input fields
        for fieldName in self.currentHandler.params.keys():
            if fieldName == 'endPoints':
                continue  #this was deprecated in v1.62.00
            param = self.currentHandler.params[fieldName]
            if fieldName in ['conditionsFile']:
                param.val = self.conditionsFile  #not the value from ctrl - that was abbreviated
                # see onOK() for partial handling = check for '...'
            else:#most other fields
                ctrls = self.currentCtrls[fieldName]#the various dlg ctrls for this param
                param.val = ctrls.getValue()#from _baseParamsDlg (handles diff control types)
                if ctrls.typeCtrl:
                    param.valType = ctrls.getType()
                if ctrls.updateCtrl:
                    param.updates = ctrls.getUpdates()
        return self.currentHandler.params
    def refreshConditions(self):
        """user might have manually edited the conditionsFile name, which in turn
        affects self.conditions and namespace. its harder to handle changes to
        long names that have been abbrev()'d, so skip them (names containing '...').
        """
        val = self.currentCtrls['conditionsFile'].valueCtrl.GetValue()
        if val.find('...')==-1 and self.conditionsFile != val:
            self.conditionsFile = val
            if self.conditions:
                self.exp.namespace.remove(self.conditions[0].keys())
            if os.path.isfile(self.conditionsFile):
                try:
                    self.conditions = data.importConditions(self.conditionsFile)
                    self.currentCtrls['conditions'].setValue(self.getTrialsSummary(self.conditions))
                except ImportError, msg:
                    self.currentCtrls['conditions'].setValue(
                        _translate('Badly formed condition name(s) in file:\n')+str(msg).replace(':','\n')+
                        _translate('.\nNeed to be legal as var name; edit file, try again.'))
                    self.conditions = ''
                    logging.error('Rejected bad condition name in conditions file: %s' % str(msg).split(':')[0])
            else:
                self.conditions = None
                self.currentCtrls['conditions'].setValue(_translate("No parameters set (conditionsFile not found)"))
        else:
            logging.debug('DlgLoop: could not determine if a condition filename was edited')
            #self.currentCtrls['conditions'] could be misleading at this point
    def onOK(self, event=None):
        # intercept OK in case user deletes or edits the filename manually
        if 'conditionsFile' in self.currentCtrls.keys():
            self.refreshConditions()
        event.Skip() # do the OK button press

class DlgComponentProperties(_BaseParamsDlg):
    def __init__(self,frame,title,params,order,
            helpUrl=None, suppressTitles=True,size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT,
            editing=False):
        style=style|wx.RESIZE_BORDER
        _BaseParamsDlg.__init__(self,frame,title,params,order,
                                helpUrl=helpUrl,size=size,style=style,
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
        self.mainSizer.Layout()
        self.Fit()
        self.Refresh()

class DlgExperimentProperties(_BaseParamsDlg):
    def __init__(self,frame,title,params,order,suppressTitles=False,
            size=wx.DefaultSize,helpUrl=None,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT):
        style=style|wx.RESIZE_BORDER
        _BaseParamsDlg.__init__(self,frame,'Experiment Settings',params,order,
                                size=size,style=style,helpUrl=helpUrl)
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
        """full-screen has been checked/unchecked. Show or hide the window size field accordingly"""
        if self.paramCtrls['Full-screen window'].valueCtrl.GetValue():
            #get screen size for requested display
            num_displays = wx.Display.GetCount()
            if int(self.paramCtrls['Screen'].valueCtrl.GetValue())>num_displays:
                logging.error("User requested non-existent screen")
                screenN=0
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
        self.mainSizer.Layout()
        self.Fit()
        self.Refresh()

    def show(self):
        """Adds an OK and cancel button, shows dialogue.

        This method returns wx.ID_OK (as from ShowModal), but also
        sets self.OK to be True or False
        """
        #add buttons for help, OK and Cancel
        self.mainSizer=wx.BoxSizer(wx.VERTICAL)
        buttons = wx.StdDialogButtonSizer()
        if self.helpUrl!=None:
            helpBtn = wx.Button(self, wx.ID_HELP, _translate(" Help "))
            helpBtn.SetHelpText(_translate("Get help about this component"))
            helpBtn.Bind(wx.EVT_BUTTON, self.onHelp)
            buttons.Add(helpBtn, 0, wx.ALIGN_RIGHT|wx.ALL,border=3)
        self.OKbtn = wx.Button(self, wx.ID_OK, _translate(" OK "))
        self.OKbtn.SetDefault()
        buttons.Add(self.OKbtn, 0, wx.ALIGN_RIGHT|wx.ALL,border=3)
        CANCEL = wx.Button(self, wx.ID_CANCEL, _translate(" Cancel "))
        buttons.Add(CANCEL, 0, wx.ALIGN_RIGHT|wx.ALL,border=3)

        buttons.Realize()
        self.ctrls.Fit()
        self.mainSizer.Add(self.ctrls)
        self.mainSizer.Add(buttons, flag=wx.ALIGN_RIGHT)
        self.SetSizerAndFit(self.mainSizer)

        #move the position to be v near the top of screen and to the right of the left-most edge of builder
        builderPos = self.frame.GetPosition()
        self.SetPosition((builderPos[0]+200,20))

        #do show and process return
        retVal = self.ShowModal()
        if retVal== wx.ID_OK: self.OK=True
        else:  self.OK=False
        return wx.ID_OK

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
    preview existing .csv or .xlsx file that has already been loaded -> conditions:
        gridGUI = builder.DlgConditions(conditions, parent=self,
                                    title=fileName, fixed=True)

    To add columns, an instance of this class will instantiate a new instance
    having one more column. Doing so makes the return value from the first instance's
    showModal() meaningless. In order to update things like fileName and conditions,
    values are set in the parent, and should not be set based on showModal retVal.

    Author: Jeremy Gray, 2011
    """
    def __init__(self, grid=None, fileName=False, parent=None, title='',
            trim=True, fixed=False, hasHeader=True, gui=True, extraRows=0, extraCols=0,
            clean=True, pos=None, preview=True,
            _restore=None, size=wx.DefaultSize,
            style=wx.DEFAULT_DIALOG_STYLE|wx.DIALOG_NO_PARENT):
        self.parent = parent # gets the conditionsFile info
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
                f = f.rsplit(os.path.sep,2)[1:]
                f = os.path.join(*f) # eg, BART/trialTypes.xlsx
                title = f
        elif not grid:
            title = _translate('New (no file)')
        elif _restore:
            if not title:
                f = os.path.abspath(_restore[1])
                f = f.rsplit(os.path.sep,2)[1:]
                f = os.path.join(*f) # eg, BART/trialTypes.xlsx
                title = f
        elif not title:
            title = _translate('Conditions data (no file)')
        # if got here via addColumn:
        # convert from conditions dict format:
        if grid and type(grid) == list and type(grid[0]) == dict:
            conditions = grid[:]
            numCond, numParam = len(conditions), len(conditions[0])
            grid = [conditions[0].keys()]
            for i in xrange(numCond):
                row = conditions[i].values()
                grid.append(row)
            hasHeader=True # keys of a dict are the header
        # ensure a sensible grid, or provide a basic default:
        if not grid or not len(grid) or not len(grid[0]):
            grid = [[self.colName(0)], [u'']]
            hasHeader = True
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
        except wx._core.PyNoAppError: # only needed during development?
            self.madeApp = True
            global app
            if wx.version() < '2.9':
                app = wx.PySimpleApp()
            else:
                app = wx.App(False)
            wx.Dialog.__init__(self, None,-1,title,pos,size,style)
        self.trim = trim
        self.warning = '' # updated to warn about eg, trailing whitespace
        if hasHeader and not len(grid) > 1 and not self.fixed:
            self.grid.append([])
        self.clean = bool(clean)
        self.typeChoices = ['None', 'str', 'utf-8', 'int', 'long', 'float',
                            'bool', 'list', 'tuple', 'array']
        # make all rows have same # cols, extending as needed or requested:
        longest = max([len(r) for r in self.grid]) + extraCols
        for row in self.grid:
            for i in range(len(row),longest):
                row.append(u'') # None
        self.hasHeader = bool(hasHeader) # self.header <== row of input param name fields
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
        self.colSizes = map(lambda x: min(20, max(10, x+1)) * 8 + 30, self.colSizes)
        self.inputTypes = [] # explicit, as selected by user via type-selector
        self.inputFields = [] # values in fields
        self.data = []

        # make header label, if any:
        if self.hasHeader:
            rowLabel = wx.StaticText(self,-1,label=_translate('Params:'), size=(6*9, 20))
            rowLabel.SetForegroundColour(darkblue)
            self.addRow(0, rowLabel=rowLabel)
        # make type-selector drop-down:
        if not self.fixed:
            if sys.platform == 'darwin':
                self.SetWindowVariant(variant=wx.WINDOW_VARIANT_SMALL)
            labelBox = wx.BoxSizer(wx.VERTICAL)
            tx = wx.StaticText(self,-1,label=_translate('type:'), size=(5*9,20))
            tx.SetForegroundColour(darkgrey)
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
            if sys.platform == 'darwin':
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
            if sys.platform == 'darwin':
                self.SetWindowVariant(variant=wx.WINDOW_VARIANT_SMALL)
            label = _translate('cond %s:')%str(row+1-int(self.hasHeader)).zfill(2)
            rowLabel = wx.StaticText(self, -1, label=label)
            rowLabel.SetForegroundColour(darkgrey)
            if sys.platform == 'darwin':
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
                field.SetForegroundColour(darkblue) #dark blue
                if not _valid_var_re.match(field.GetValue()): #or (self.parent and
                            #self.parent.exp.namespace.exists(field.GetValue()) ):
                            # was always red when preview .xlsx file -- in namespace already is fine
                    if self.fixed:
                        field.SetForegroundColour("Red")
                field.SetToolTip(wx.ToolTip(_translate('Should be legal as a variable name (alphanumeric)')))
                field.Bind(wx.EVT_TEXT, self.checkName)
            elif self.fixed:
                field.SetForegroundColour(darkgrey)
                field.SetBackgroundColour(white)

            # warn about whitespace unless will be auto-removed. invisible, probably spurious:
            if (self.fixed or not self.clean) and item != item.lstrip().strip():
                field.SetForegroundColour('Red')
                self.warning = _translate('extra white-space') # also used in show()
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
                msg, enable = _translate("Name must be alpha-numeric or _, no spaces"), False
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
        if hasattr(self, 'fileName'):
            fname = self.fileName
        else:
            fname = None
        wx.CallAfter(DlgConditions, currentData, _restore=(self.newFile,fname),
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
                        if thisType=='utf-8':
                            thisType='unicode'
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
        DlgConditions(previewData, parent=self.parent, title=_translate('PREVIEW'), fixed=True)
    def onNeedsResize(self, event=None):
        self.SetSizerAndFit(self.border) # do outer-most sizer
        if self.pos is None:
            self.Center()
    def show(self):
        """called internally; to display, pass gui=True to init
        """
        # put things inside a border:
        self.border = wx.FlexGridSizer(2,1) # data matrix on top, buttons below
        self.border.Add(self.sizer, proportion=1, flag=wx.ALL|wx.EXPAND, border=8)

        # add a message area, buttons:
        buttons = wx.BoxSizer(wx.HORIZONTAL)
        if sys.platform == 'darwin':
            self.SetWindowVariant(variant=wx.WINDOW_VARIANT_SMALL)
        if not self.fixed:
            # placeholder for possible messages / warnings:
            self.tmpMsg = wx.StaticText(self, -1, label='', size=(350,15), style=wx.ALIGN_RIGHT)
            self.tmpMsg.SetForegroundColour('Red')
            if self.warning:
                self.tmpMsg.SetLabel(self.warning)
            buttons.Add(self.tmpMsg, flag=wx.ALIGN_CENTER)
            buttons.AddSpacer(8)
            self.border.Add(buttons,1,flag=wx.BOTTOM|wx.ALIGN_CENTER, border=8)
            buttons = wx.BoxSizer(wx.HORIZONTAL)
            ADDROW = wx.Button(self, -1, _translate("+cond."))
            ADDROW.SetToolTip(wx.ToolTip(_translate('Add a condition (row); to delete a condition, delete all of its values.')))
            ADDROW.Bind(wx.EVT_BUTTON, self.userAddRow)
            buttons.Add(ADDROW)
            buttons.AddSpacer(4)
            ADDCOL = wx.Button(self, -1, _translate("+param"))
            ADDCOL.SetToolTip(wx.ToolTip(_translate('Add a parameter (column); to delete a param, set its type to None, or delete all of its values.')))
            ADDCOL.Bind(wx.EVT_BUTTON, self.userAddCol)
            buttons.Add(ADDCOL)
            buttons.AddSpacer(4)
            PREVIEW = wx.Button(self, -1, _translate("Preview"))
            PREVIEW.SetToolTip(wx.ToolTip(_translate("Show all values as they would appear after saving to a file, without actually saving anything.")))
            PREVIEW.Bind(wx.EVT_BUTTON, self.preview)
            buttons.Add(PREVIEW)
            buttons.AddSpacer(4)
            self.SAVEAS = wx.Button(self, wx.SAVE, _translate("Save as"))
            self.SAVEAS.Bind(wx.EVT_BUTTON, self.saveAs)
            buttons.Add(self.SAVEAS)
            buttons.AddSpacer(8)
            self.border.Add(buttons,1,flag=wx.BOTTOM|wx.ALIGN_RIGHT, border=8)
        if sys.platform == 'darwin':
            self.SetWindowVariant(variant=wx.WINDOW_VARIANT_NORMAL)
        buttons = wx.StdDialogButtonSizer()
        #help button if we know the url
        if self.helpUrl and not self.fixed:
            helpBtn = wx.Button(self, wx.ID_HELP, _translate(" Help "))
            helpBtn.SetToolTip(wx.ToolTip(_translate("Go to online help")))
            helpBtn.Bind(wx.EVT_BUTTON, self.onHelp)
            buttons.Add(helpBtn, wx.ALIGN_LEFT|wx.ALL)
            buttons.AddSpacer(12)
        self.OKbtn = wx.Button(self, wx.ID_OK, _translate(" OK "))
        if not self.fixed:
            self.OKbtn.SetToolTip(wx.ToolTip(_translate('Save and exit')))
        self.OKbtn.Bind(wx.EVT_BUTTON, self.onOK)
        self.OKbtn.SetDefault()
        buttons.Add(self.OKbtn)
        if not self.fixed:
            buttons.AddSpacer(4)
            CANCEL = wx.Button(self, wx.ID_CANCEL, _translate(" Cancel "))
            CANCEL.SetToolTip(wx.ToolTip(_translate('Exit, discard any edits')))
            buttons.Add(CANCEL)
        buttons.AddSpacer(8)
        buttons.Realize()
        self.border.Add(buttons,1,flag=wx.BOTTOM|wx.ALIGN_RIGHT, border=8)

        # finally, its show time:
        self.SetSizerAndFit(self.border)
        if self.pos is None:
            self.Center()
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
                msg, enable = _translate("Name must be alpha-numeric or _, no spaces"), False
                newName = _nonalphanumeric_re.sub('_', newName)
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
            self.tmpMsg.SetLabel(_translate('Param name(s) adjusted to be legal. Look ok?'))
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
            fullPathList = gui.fileOpenDlg(tryFileName=os.path.basename(fileName),
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
            except Exception, err:
                print "Failed to load %s. Please send the following to the PsychoPy user list" %filename
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
                print "'Save-as' canceled; existing file NOT overwritten.\n"
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
        print "\n"+(" Running: %s " %(fullPath)).center(80,"#")
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
        except IOError, err:
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
def getAbbrev(longStr, n=30):
    """for a filename (or any string actually), give the first
    10 characters, an ellipsis and then n-10 of the final characters"""
    if len(longStr)>35:
        return longStr[0:10]+'...'+longStr[(-n+10):]
    else:
        return longStr
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
