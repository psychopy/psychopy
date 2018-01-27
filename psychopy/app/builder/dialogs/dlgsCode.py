#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

"""Dialog classes for the Builder Code component
"""

from __future__ import absolute_import, division, print_function
from builtins import str

import keyword
import re
import wx
try:
    from wx.lib.agw import flatnotebook
except ImportError:  # was here wx<4.0:
    from wx.lib import flatnotebook

from .... import constants
from .. import validators
from psychopy.localization import _translate


class DlgCodeComponentProperties(wx.Dialog):
    _style = (wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
              | wx.DIALOG_NO_PARENT)

    def __init__(self, frame, title, params, order,
                 helpUrl=None, suppressTitles=True, size=wx.DefaultSize,
                 style=_style, editing=False, depends=[],
                 timeout=None):

        # translate title
        localizedTitle = title.replace(' Properties',
                                       _translate(' Properties'))
        wx.Dialog.__init__(self, None, -1, localizedTitle,
                           size=size, style=style)
        self.frame = frame
        self.app = frame.app
        self.helpUrl = helpUrl
        self.params = params  # dict
        self.order = order
        self.title = title
        self.timeout = timeout
        self.warningsDict = {}  # to store warnings for all fields
        # keep localized title to update dialog's properties later.
        self.localizedTitle = localizedTitle
        self.codeGuiElements = {}
        if not editing and 'name' in self.params:
            # then we're adding a new component so ensure a valid name:
            makeValid = self.frame.exp.namespace.makeValid
            self.params['name'].val = makeValid(params['name'].val)

        agwStyle = flatnotebook.FNB_NO_X_BUTTON
        if hasattr(flatnotebook, "FNB_NAV_BUTTONS_WHEN_NEEDED"):
            # not available in wxPython 2.8
            agwStyle |= flatnotebook.FNB_NAV_BUTTONS_WHEN_NEEDED
        if hasattr(flatnotebook, "FNB_NO_TAB_FOCUS"):
            # not available in wxPython 2.8.10
            agwStyle |= flatnotebook.FNB_NO_TAB_FOCUS
        self.codeSections = flatnotebook.FlatNotebook(self, wx.ID_ANY,
                                                      style=agwStyle)

        openToPage = 0
        for idx, pkey in enumerate(self.order):
            param = self.params.get(pkey)
            if pkey == 'name':
                self.nameLabel = wx.StaticText(self, wx.ID_ANY,
                                               _translate(param.label))
                _style = wx.TE_PROCESS_ENTER | wx.TE_PROCESS_TAB
                self.componentName = wx.TextCtrl(self, wx.ID_ANY,
                                                 str(param.val),
                                                 style=_style)
                self.componentName.SetToolTipString(
                        _translate(param.hint))
                self.componentName.SetValidator(validators.NameValidator())
                self.nameOKlabel = wx.StaticText(self, -1, '',
                                                 style=wx.ALIGN_RIGHT)
                self.nameOKlabel.SetForegroundColour(wx.RED)
            else:
                guikey = pkey.replace(' ', '_')
                _param = self.codeGuiElements.setdefault(guikey, dict())

                _section = wx.Panel(self.codeSections, wx.ID_ANY)
                _panel = _param.setdefault(guikey + '_panel', _section)
                _codeBox = _param.setdefault(guikey + '_codebox',
                                             CodeBox(_panel, wx.ID_ANY,
                                                     pos=wx.DefaultPosition,
                                                     style=0,
                                                     prefs=self.app.prefs))
                if len(param.val):
                    _codeBox.AddText(str(param.val))
                if len(param.val.strip()) and not openToPage:
                    # index of first non-blank page
                    openToPage = idx

        if self.helpUrl is not None:
            self.helpButton = wx.Button(self, wx.ID_HELP,
                                        _translate(" Help "))
            tip = _translate("Go to online help about this component")
            self.helpButton.SetToolTip(wx.ToolTip(tip))
        self.okButton = wx.Button(self, wx.ID_OK, _translate(" OK "))
        self.okButton.SetDefault()
        self.cancelButton = wx.Button(self, wx.ID_CANCEL,
                                      _translate(" Cancel "))
        self.__set_properties()
        self.__do_layout()
        self.codeSections.SetSelection(max(0, openToPage - 1))

        self.Bind(wx.EVT_BUTTON, self.helpButtonHandler, self.helpButton)

        if self.timeout:
            timeout = wx.CallLater(self.timeout, self.onEnter)
            timeout.Start()
        # do show and process return
        ret = self.ShowModal()

        if ret == wx.ID_OK:
            self.checkName()
            self.OK = True
            self.params = self.getParams()  # get new vals from dlg
            self.Validate()
            # TODO: check syntax of code from each code section tab??
        else:
            self.OK = False

    def onEnter(self, evt=None, retval=wx.ID_OK):
        self.EndModal(retval)

    def checkName(self, event=None):
        """
        Issue a form validation on name change.
        """
        self.Validate()

    def __set_properties(self):

        self.SetTitle(self.localizedTitle)  # use localized title
        self.SetSize((640, 480))

    def __do_layout(self):
        for paramName in self.order:
            if paramName.lower() != 'name':
                guikey = paramName.replace(' ', '_')
                paramGuiDict = self.codeGuiElements.get(guikey)
                asizer = paramGuiDict.setdefault(
                    guikey + '_sizer', wx.BoxSizer(wx.VERTICAL))
                asizer.Add(paramGuiDict.get(
                    guikey + '_codebox'), 1, wx.EXPAND, 0)
                paramGuiDict.get(guikey + '_panel').SetSizer(asizer)
                tabLabel = _translate(paramName)
                # Add a visual indicator when tab contains code
                if self.params.get(guikey.replace('_',' ')).val:
                    tabLabel += ' *'
                self.codeSections.AddPage(paramGuiDict.get(
                    guikey + '_panel'), tabLabel)

        nameSizer = wx.BoxSizer(wx.HORIZONTAL)
        nameSizer.Add(self.nameLabel, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)
        nameSizer.Add(self.componentName,
                      flag=wx.EXPAND | wx.ALL | wx.ALIGN_CENTER_VERTICAL,
                      border=10, proportion=1)
        nameSizer.Add(self.nameOKlabel, 0, wx.ALL, 10)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(nameSizer)
        mainSizer.Add(self.codeSections, 1, wx.EXPAND | wx.ALL, 10)
        buttonSizer.Add(self.helpButton, 0, wx.RIGHT, 10)
        buttonSizer.Add(self.okButton, 0, wx.LEFT, 10)
        buttonSizer.Add(self.cancelButton, 0, 0, 0)
        mainSizer.Add(buttonSizer, 0, wx.ALL | wx.ALIGN_RIGHT, 5)
        self.SetSizer(mainSizer)
        self.Layout()
        self.Center()

    def getParams(self):
        """retrieves data from any fields in self.codeGuiElements
        (populated during the __init__ function)

        The new data from the dlg get inserted back into the original params
        used in __init__ and are also returned from this method.
        """
        # get data from input fields
        for fieldName in self.params:
            param = self.params[fieldName]
            if fieldName == 'name':
                param.val = self.componentName.GetValue()
            else:
                guikey = fieldName.replace(' ', '_')
                codeBox = guikey + '_codebox'
                if guikey in self.codeGuiElements:
                    gkey = self.codeGuiElements.get(guikey)
                    param.val = gkey.get(codeBox).GetText()
        return self.params

    def helpButtonHandler(self, event):
        """Uses self.app.followLink() to self.helpUrl
        """
        self.app.followLink(url=self.helpUrl)


class CodeBox(wx.stc.StyledTextCtrl):
    # this comes mostly from the wxPython demo styledTextCtrl 2

    def __init__(self, parent, ID, prefs,
                 # set the viewer to be small, then it will increase with
                 # wx.aui control
                 pos=wx.DefaultPosition, size=wx.Size(100, 160),
                 style=0):
        wx.stc.StyledTextCtrl.__init__(self, parent, ID, pos, size, style)
        # JWP additions
        self.notebook = parent
        self.prefs = prefs
        self.UNSAVED = False
        self.filename = ""
        self.fileModTime = None  # check if file modified outside CodeEditor
        self.AUTOCOMPLETE = True
        self.autoCompleteDict = {}
        # self.analyseScript()  # no - analyse after loading so that window
        # doesn't pause strangely
        self.locals = None  # will contain the local environment of the script
        self.prevWord = None
        # remove some annoying stc key commands
        CTRL = wx.stc.STC_SCMOD_CTRL
        self.CmdKeyClear(ord('['), CTRL)
        self.CmdKeyClear(ord(']'), CTRL)
        self.CmdKeyClear(ord('/'), CTRL)
        self.CmdKeyClear(ord('/'), CTRL | wx.stc.STC_SCMOD_SHIFT)

        self.SetLexer(wx.stc.STC_LEX_PYTHON)
        self.SetKeyWords(0, " ".join(keyword.kwlist))

        self.SetProperty("fold", "1")
        # 4 means 'tabs are bad'; 1 means 'flag inconsistency'
        self.SetProperty("tab.timmy.whinge.level", "4")
        self.SetMargins(0, 0)
        self.SetUseTabs(False)
        self.SetTabWidth(4)
        self.SetIndent(4)
        self.SetViewWhiteSpace(self.prefs.appData['coder']['showWhitespace'])
        self.SetBufferedDraw(False)
        self.SetViewEOL(False)
        self.SetEOLMode(wx.stc.STC_EOL_LF)
        # self.SetUseHorizontalScrollBar(True)
        # self.SetUseVerticalScrollBar(True)

        # self.SetEdgeMode(wx.stc.STC_EDGE_BACKGROUND)
        # self.SetEdgeMode(wx.stc.STC_EDGE_LINE)
        # self.SetEdgeColumn(78)

        # Setup a margin to hold fold markers
        self.SetMarginType(2, wx.stc.STC_MARGIN_SYMBOL)
        self.SetMarginMask(2, wx.stc.STC_MASK_FOLDERS)
        self.SetMarginSensitive(2, True)
        self.SetMarginWidth(2, 12)
        self.Bind(wx.stc.EVT_STC_MARGINCLICK, self.OnMarginClick)

        self.SetIndentationGuides(False)

        # Like a flattened tree control using square headers
        white = "white"
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPEN,
                          wx.stc.STC_MARK_BOXMINUS, white, "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDER,
                          wx.stc.STC_MARK_BOXPLUS, white, "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERSUB,
                          wx.stc.STC_MARK_VLINE, white, "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERTAIL,
                          wx.stc.STC_MARK_LCORNER, white, "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEREND,
                          wx.stc.STC_MARK_BOXPLUSCONNECTED, white, "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDEROPENMID,
                          wx.stc.STC_MARK_BOXMINUSCONNECTED, white, "#808080")
        self.MarkerDefine(wx.stc.STC_MARKNUM_FOLDERMIDTAIL,
                          wx.stc.STC_MARK_TCORNER, white, "#808080")

        # self.DragAcceptFiles(True)
        # self.Bind(wx.EVT_DROP_FILES, self.coder.filesDropped)
        # self.Bind(wx.stc.EVT_STC_MODIFIED, self.onModified)
        # # self.Bind(wx.stc.EVT_STC_UPDATEUI, self.OnUpdateUI)
        # self.Bind(wx.stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        # self.Bind(wx.EVT_KEY_DOWN, self.OnKeyPressed)
        # self.SetDropTarget(FileDropTarget(coder = self.coder))

        self.setupStyles()

    def setupStyles(self):

        if wx.Platform == '__WXMSW__':
            faces = {'size': 10}
        elif wx.Platform == '__WXMAC__':
            faces = {'size': 14}
        else:
            faces = {'size': 12}
        if self.prefs.coder['codeFontSize']:
            faces['size'] = int(self.prefs.coder['codeFontSize'])
        faces['small'] = faces['size'] - 2
        # Global default styles for all languages
        # ,'Arial']  # use arial as backup
        faces['code'] = self.prefs.coder['codeFont']
        # ,'Arial']  # use arial as backup
        faces['comment'] = self.prefs.coder['commentFont']
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,
                          "face:%(code)s,size:%(size)d" % faces)
        self.StyleClearAll()  # Reset all to be like the default

        # Global default styles for all languages
        self.StyleSetSpec(wx.stc.STC_STYLE_DEFAULT,
                          "face:%(code)s,size:%(size)d" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_LINENUMBER,
                          "back:#C0C0C0,face:%(code)s,size:%(small)d" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_CONTROLCHAR,
                          "face:%(comment)s" % faces)
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACELIGHT,
                          "fore:#FFFFFF,back:#0000FF,bold")
        self.StyleSetSpec(wx.stc.STC_STYLE_BRACEBAD,
                          "fore:#000000,back:#FF0000,bold")

        # Python styles
        # Default
        self.StyleSetSpec(wx.stc.STC_P_DEFAULT,
                          "fore:#000000,face:%(code)s,size:%(size)d" % faces)
        # Comments
        spec = "fore:#007F00,face:%(comment)s,size:%(size)d"
        self.StyleSetSpec(wx.stc.STC_P_COMMENTLINE, spec % faces)
        # Number
        self.StyleSetSpec(wx.stc.STC_P_NUMBER,
                          "fore:#007F7F,size:%(size)d" % faces)
        # String
        self.StyleSetSpec(wx.stc.STC_P_STRING,
                          "fore:#7F007F,face:%(code)s,size:%(size)d" % faces)
        # Single quoted string
        self.StyleSetSpec(wx.stc.STC_P_CHARACTER,
                          "fore:#7F007F,face:%(code)s,size:%(size)d" % faces)
        # Keyword
        self.StyleSetSpec(wx.stc.STC_P_WORD,
                          "fore:#00007F,bold,size:%(size)d" % faces)
        # Triple quotes
        self.StyleSetSpec(wx.stc.STC_P_TRIPLE,
                          "fore:#7F0000,size:%(size)d" % faces)
        # Triple double quotes
        self.StyleSetSpec(wx.stc.STC_P_TRIPLEDOUBLE,
                          "fore:#7F0000,size:%(size)d" % faces)
        # Class name definition
        self.StyleSetSpec(wx.stc.STC_P_CLASSNAME,
                          "fore:#0000FF,bold,underline,size:%(size)d" % faces)
        # Function or method name definition
        self.StyleSetSpec(wx.stc.STC_P_DEFNAME,
                          "fore:#007F7F,bold,size:%(size)d" % faces)
        # Operators
        self.StyleSetSpec(wx.stc.STC_P_OPERATOR, "bold,size:%(size)d" % faces)
        # Identifiers
        self.StyleSetSpec(wx.stc.STC_P_IDENTIFIER,
                          "fore:#000000,face:%(code)s,size:%(size)d" % faces)
        # Comment-blocks
        self.StyleSetSpec(wx.stc.STC_P_COMMENTBLOCK,
                          "fore:#7F7F7F,size:%(size)d" % faces)
        # End of line where string is not closed
        spec = "fore:#000000,face:%(code)s,back:#E0C0E0,eol,size:%(size)d"
        self.StyleSetSpec(wx.stc.STC_P_STRINGEOL, spec % faces)

        self.SetCaretForeground("BLUE")

    def setStatus(self, status):
        if status == 'error':
            color = (255, 210, 210, 255)
        elif status == 'changed':
            color = (220, 220, 220, 255)
        else:
            color = (255, 255, 255, 255)
        self.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, color)
        self.setupStyles()  # then reset fonts again on top of that color

    def OnMarginClick(self, evt):
        # fold and unfold as needed
        if evt.GetMargin() == 2:
            lineClicked = self.LineFromPosition(evt.GetPosition())

            _flag = wx.stc.STC_FOLDLEVELHEADERFLAG
            if self.GetFoldLevel(lineClicked) & _flag:
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

    def Paste(self, event=None):
        dataObj = wx.TextDataObject()
        clip = wx.Clipboard().Get()
        clip.Open()
        success = clip.GetData(dataObj)
        clip.Close()
        if success:
            txt = dataObj.GetText()
            if not constants.PY3:
                try:
                    # if we can decode/encode to utf-8 then all is good
                    txt.decode('utf-8')
                except:
                    # if not then wx conversion broke so get raw data instead
                    txt = dataObj.GetDataHere()
            self.ReplaceSelection(txt)

