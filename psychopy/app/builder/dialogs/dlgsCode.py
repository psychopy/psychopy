#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Dialog classes for the Builder Code component
"""
import sys

import keyword
import wx
# import wx.lib.agw.aui as aui
from collections import OrderedDict
from psychopy.experiment.components.code import CodeComponent
from ..validators import WarningManager
from ...themes import handlers

from importlib.util import find_spec as loader
hasMetapensiero = loader("metapensiero") is not None

from .. import validators
from psychopy.localization import _translate
from psychopy.app.coder.codeEditorBase import BaseCodeEditor
from psychopy.experiment.py2js_transpiler import translatePythonToJavaScript


class DlgCodeComponentProperties(wx.Dialog):
    _style = (wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
              | wx.DIALOG_NO_PARENT)

    def __init__(self, frame, element, experiment,
                 helpUrl=None, suppressTitles=True, size=(1000,600),
                 style=_style, editing=False, depends=[],
                 timeout=None, type="Code",
                 openToPage=None):

        # translate title
        if "name" in element.params:
            title = element.params['name'].val + _translate(' Properties')
        elif "expName" in element.params:
            title = element.params['expName'].val + _translate(' Properties')
        else:
            title = "Properties"
        # get help url
        if hasattr(element, 'url'):
            helpUrl = element.url
        else:
            helpUrl = None

        wx.Dialog.__init__(self, None, -1, title,
                           size=size, style=style)
        self.SetTitle(title)  # use localized title
        # self.panel = wx.Panel(self)
        self.frame = frame
        self.app = frame.app
        self.helpUrl = helpUrl
        self.component = element
        self.params = element.params  # dict
        self.order = element.order
        self.title = title
        self.timeout = timeout
        self.codeBoxes = {}
        self.tabs = OrderedDict()

        if not editing and 'name' in self.params:
            # then we're adding a new component so ensure a valid name:
            makeValid = self.frame.exp.namespace.makeValid
            self.params['name'].val = makeValid(self.params['name'].val)

        self.codeNotebook = wx.Notebook(self)
        # in AUI notebook the labels are blurry on retina mac
        #   and the close-tab buttons are hard to kill
        #   self.codeNotebook = aui.AuiNotebook(self)
        # in FlatNoteBook the tab controls (left,right,close) are ugly on mac
        #   and also can't be killed

        for paramN, paramName in enumerate(self.order):
            param = self.params.get(paramName)
            if paramName == 'name':
                self.nameLabel = wx.StaticText(self, wx.ID_ANY,
                                               _translate(param.label))
                _style = wx.TE_PROCESS_ENTER | wx.TE_PROCESS_TAB
                self.componentName = wx.TextCtrl(self, wx.ID_ANY,
                                                 str(param.val),
                                                 style=_style)
                self.componentName.SetToolTip(wx.ToolTip(
                        _translate(param.hint)))
                self.componentName.SetValidator(validators.NameValidator())
                self.nameOKlabel = wx.StaticText(self, -1, '',
                                                 style=wx.ALIGN_RIGHT)
                self.nameOKlabel.SetForegroundColour(wx.RED)
            elif paramName == 'Code Type':
                # Create code type choice menu
                _codeTypes = self.params['Code Type'].allowedVals
                _selectedCodeType = self.params['Code Type'].val
                _selectedCodeTypeIndex = _codeTypes.index(_selectedCodeType)
                self.codeTypeMenu = wx.Choice(self, choices=_codeTypes)
                # If user does not have metapensiero but codetype is auto-js, revert to (Py?)
                if not hasMetapensiero and _selectedCodeType.lower() == 'auto->js':
                    _selectedCodeTypeIndex -= 1
                # Set selection to value stored in self params
                self.codeTypeMenu.SetSelection(_selectedCodeTypeIndex)
                self.codeTypeMenu.Bind(wx.EVT_CHOICE, self.onCodeChoice)
                self.codeTypeName = wx.StaticText(self, wx.ID_ANY,
                                                  _translate(param.label))
            elif paramName == 'disabled':
                # Create bool control to disable/enable component
                self.disableCtrl = wx.CheckBox(self, wx.ID_ANY, label=_translate('disabled'))
                self.disableCtrl.SetValue(bool(param.val))
            else:
                codeType = ["Py", "JS"]["JS" in paramName]  # Give CodeBox a code type
                tabName = paramName.replace("JS ", "")
                if tabName in self.tabs:
                    _panel = self.tabs[tabName]
                else:
                    _panel = wx.Panel(self.codeNotebook, wx.ID_ANY)
                    _panel.tabN = len(self.tabs)
                    _panel.app = self.app
                    self.tabs[tabName] = _panel
                # if openToPage refers to this page by name, convert to index
                if openToPage == paramName:
                    openToPage = _panel.tabN

                self.codeBoxes[paramName] = CodeBox(_panel, wx.ID_ANY,
                                                    pos=wx.DefaultPosition,
                                                    style=0,
                                                    prefs=self.app.prefs,
                                                    params=self.params,
                                                    codeType=codeType)
                self.codeBoxes[paramName].AddText(param.val)
                self.codeBoxes[paramName].Bind(wx.EVT_KEY_UP, self.onKeyUp)  # For real time translation

                if len(param.val.strip()) and hasattr(_panel, "tabN") and not isinstance(openToPage, str):
                    if openToPage is None or openToPage > _panel.tabN:
                        # index of first non-blank page
                        openToPage = _panel.tabN

        if self.helpUrl is not None:
            self.helpButton = wx.Button(self, wx.ID_HELP,
                                        _translate(" Help "))
            tip = _translate("Go to online help about this component")
            self.helpButton.SetToolTip(wx.ToolTip(tip))
        self.okButton = wx.Button(self, wx.ID_OK, _translate(" OK "))
        self.okButton.SetDefault()
        self.cancelButton = wx.Button(self, wx.ID_CANCEL,
                                      _translate(" Cancel "))
        self.warnings = WarningManager(self)  # to store warnings for all fields
        self.__do_layout()
        if openToPage is None:
            openToPage = 0
        self.codeNotebook.SetSelection(openToPage)
        self.Update()
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
        else:
            self.OK = False

    def readOnlyCodeBox(self, val=False):
        """
        Sets ReadOnly for JS code boxes.

        Parameters
        ----------
        val : bool
            True/False for ReadOnly/ReadWrite
        """
        for box in self.codeBoxes:
            if 'JS' in box:
                self.codeBoxes[box].SetReadOnly(val)

    def onKeyUp(self, event):
        """
        Translates Python to JS on EVT_KEY_UP event, if Code Type is Auto->JS.
        """
        if self.codeChoice[1].val.lower() != 'auto->js':
            return

        pythonCodeBox = event.GetEventObject()
        keys = list(self.codeBoxes.keys())
        vals = list(self.codeBoxes.values())
        codeBox = keys[vals.index(pythonCodeBox)]
        if 'JS' not in codeBox:
            self.runTranslation(codeBox)

        if event:
            event.Skip()

    @property
    def codeChoice(self):
        """
        Set code to Python, JS, Both, or Auto->JS for translation.

        Returns
        -------
        tuple :
            (previousCodeType, code type param)
        """
        param = self.params['Code Type']  # Update param with menu selection
        prevCodeType = param.val
        param.val = param.allowedVals[self.codeTypeMenu.GetSelection()]
        return prevCodeType, param

    def undoCodeTypeChoice(self, prevCodeType):
        """
        Return code type to previous selection.

        Parameters
        ----------
        prevCodeType: str
            Code Type
        """
        prevCodeTypeIndex = self.params['Code Type'].allowedVals.index(prevCodeType)
        self.codeTypeMenu.SetSelection(prevCodeTypeIndex)
        self.params['Code Type'].val = prevCodeType

    def onCodeChoice(self, event):
        """
        Set code to Python, JS, Both, or Auto->JS for translation.
        Calls translation and updates to visible windows
        """
        prevCodeType, param = self.codeChoice
        # If user doesn't have metapensiero and current choice is auto-js...
        if not hasMetapensiero and param.val.lower() == "auto->js" :
            # Throw up error dlg instructing to get metapensiero
            msg = _translate("\nPy to JS auto-translation requires the metapensiero library.\n"
                   "Available for Python 3.5+.\n")
            dlg = CodeOverwriteDialog(self, -1, _translate("Warning: requires the metapensiero library"), msg)
            dlg.ShowModal()
            # Revert to previous choice
            self.undoCodeTypeChoice(prevCodeType)
            return
        # Translate from previous language to new, make sure correct box is visible
        self.translateCode(event, prevCodeType, param.val)
        self.updateVisibleCode(event)

        if event:
            event.Skip()

    def translateCode(self, event, prevCodeType='', newCodeType=''):
        """
        For each code box, calls runTranslate to translate Python code to JavaScript.
        Overwrite warning given when previous code type (prevCodeType) is Py, JS, or Both,
        and when codeChangeDetected determines whether JS code has new additions

        Parameters
        ----------
        event : wx.Event
        prevCodeType : str
            Previous code type selected
        newCodeType : str
            New code type selected
        """
        # If new codetype is not auto-js, terminate function
        if not newCodeType.lower() == "auto->js":
            return
        # If code type has changed and previous code type isn't auto-js...
        if prevCodeType.lower() != 'auto->js' and self.codeChangeDetected():
            # Throw up a warning dlg to alert user of overwriting
            msg = _translate("\nAuto-JS translation will overwrite your existing JavaScript code.\n"
                   "Press OK to continue, or Cancel.\n")
            dlg = CodeOverwriteDialog(self, -1, _translate("Warning: Python to JavaScript Translation"), msg)
            retVal = dlg.ShowModal()
            # When window closes, if OK was not clicked revert to previous codetype
            if not retVal == wx.ID_OK:
                self.undoCodeTypeChoice(prevCodeType)
                return
        # For each codebox...
        for boxName in self.codeBoxes:
            # If it is not JS...
            if 'JS' not in boxName:
                # Translate to JS
                self.runTranslation(boxName)

        if event:
            event.Skip()

    def runTranslation(self, codeBox, codeChangeTest=False):
        """
        Runs Python to JS translation for single code box.
        Only receives Python code boxes.

        Parameters
        ----------
        codeBox : Str
            The name of the code box e.g., Begin Experiment
        codeChangeTest: bool
            Whether the translation is part of the overwrite test:
            i.e., is it safe to overwrite users new JS code

        Returns
        -------
        Return values only given if codeChangeTest is True.
            Returns translated JS code as str, or False if translation fails
        """
        jsCode = ''
        jsBox = codeBox.replace(' ', ' JS ')
        pythonCode = self.codeBoxes[codeBox].GetValue()
        self.readOnlyCodeBox(False)

        try:
            if pythonCode:
                jsCode = translatePythonToJavaScript(pythonCode, namespace=None)

            if codeChangeTest:
                return jsCode

            self.codeBoxes[jsBox].SetValue(jsCode)
        except Exception:  # Errors can be caught using alerts syntax checks
            if codeChangeTest:
                return False
            self.codeBoxes[jsBox].SetValue("/* Syntax Error: Fix Python code */")
        finally:
            self.readOnlyCodeBox(self.codeChoice[1].val.lower() == 'auto->js')

    def codeChangeDetected(self):
        """
        Compares current JS code with newly translated code for each tab.

        Returns
        -------
        bool
            True if current code differs from translated code, else False
        """
        for boxName in self.codeBoxes:
            if 'JS' not in boxName:
                newJS = self.runTranslation(boxName, True)
                currentJS = self.codeBoxes[boxName.replace(' ', ' JS ')].GetValue()

                if newJS == False or currentJS != newJS:
                    return True

        return False

    def updateVisibleCode(self, event=None):
        """
        Receives keyboard events and code menu choice events.
        On choice events, the code is stored for python or JS parameters,
        and written to panel depending on choice of code. The duplicate panel
        is shown/hidden depending on code choice. When duplicate is shown, Python and JS
        code are shown in codeBox(left panel) and codeBoxDup (right panel), respectively.
        """
        codeType = self.codeChoice[1].val

        for boxName in self.codeBoxes:
            self.readOnlyCodeBox(codeType.lower() == 'auto->js')
            # If type is both or autojs, show split codebox
            if codeType.lower() in ['both', 'auto->js']:
                self.codeBoxes[boxName].Show()
            # If type is JS, hide the non-JS box
            elif codeType == 'JS':
                if 'JS' in boxName:
                    self.codeBoxes[boxName].Show()
                else:
                    self.codeBoxes[boxName].Hide()
            # If type is Py, hide the JS box
            else:
                # user only wants Py code visible
                if 'JS' in boxName:
                    self.codeBoxes[boxName].Hide()
                else:
                    self.codeBoxes[boxName].Show()
        # Name codebox tabs
        for thisTabname in self.tabs:
            self.tabs[thisTabname].Layout()

        if event:
            event.Skip()

    def onEnter(self, evt=None, retval=wx.ID_OK):
        self.EndModal(retval)

    def checkName(self, event=None):
        """
        Issue a form validation on name change.
        """
        self.Validate()

    def __do_layout(self, show=False):
        self.updateVisibleCode()
        for tabName in self.tabs:
            pyName = tabName
            jsName = pyName.replace(" ", " JS ")
            panel = self.tabs[tabName]
            sizer = wx.BoxSizer(wx.HORIZONTAL)
            pyBox = self.codeBoxes[pyName]
            jsBox = self.codeBoxes[jsName]
            sizer.Add(pyBox, 1, wx.EXPAND, 2)
            sizer.Add(jsBox, 1, wx.EXPAND, 2)
            panel.SetSizer(sizer)
            tabLabel = _translate(tabName)
            # Add a visual indicator when tab contains code
            emptyCodeComp = CodeComponent('', '') # Spawn empty code component
            # If code tab is not empty and not the same as in empty code component, add an asterisk to tab name
            hasContents = self.params.get(pyName).val or self.params.get(jsName).val
            pyEmpty = self.params.get(pyName).val == emptyCodeComp.params.get(pyName).val
            jsEmpty = self.params.get(jsName).val == emptyCodeComp.params.get(jsName).val
            if hasContents and not (pyEmpty and jsEmpty):
                tabLabel += ' *'
            self.codeNotebook.AddPage(panel, tabLabel)

        nameSizer = wx.BoxSizer(wx.HORIZONTAL)
        nameSizer.Add(self.nameLabel, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)
        nameSizer.Add(self.componentName,
                      flag=wx.EXPAND | wx.ALL,
                      border=10, proportion=1)
        nameSizer.Add(self.nameOKlabel, 0, wx.ALL, 10)
        nameSizer.Add(self.codeTypeName,
                      flag=wx.TOP | wx.RIGHT, border=13, proportion=0)
        nameSizer.Add(self.codeTypeMenu, 0, wx.ALIGN_CENTER_VERTICAL, 0)
        nameSizer.Add(self.disableCtrl, flag=wx.ALL | wx.ALIGN_CENTER_VERTICAL, border=13)

        mainSizer = wx.BoxSizer(wx.VERTICAL)
        buttonSizer = wx.BoxSizer(wx.HORIZONTAL)
        mainSizer.Add(nameSizer)
        mainSizer.Add(self.codeNotebook, 1, wx.EXPAND | wx.ALL, 10)

        buttonSizer.Add(self.helpButton, 0,
                        wx.ALL | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL, 10)
        buttonSizer.AddStretchSpacer()
        # Add Okay and Cancel buttons
        if sys.platform == "win32":
            btns = [self.okButton, self.cancelButton]
        else:
            btns = [self.cancelButton, self.okButton]
        buttonSizer.Add(btns[0], 0,
                        wx.ALL | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
                        border=3)
        buttonSizer.Add(btns[1], 0,
                        wx.ALL | wx.RIGHT | wx.ALIGN_CENTER_VERTICAL,
                        border=3)

        mainSizer.Add(buttonSizer, 0, wx.ALL | wx.RIGHT | wx.EXPAND, 5)
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
            elif fieldName == 'Code Type':
                param.val = self.codeTypeMenu.GetStringSelection()
            elif fieldName == 'disabled':
                param.val = self.disableCtrl.GetValue()
            else:
                codeBox = self.codeBoxes[fieldName]
                param.val = codeBox.GetText()
        return self.params

    def helpButtonHandler(self, event):
        """Uses self.app.followLink() to self.helpUrl
        """
        self.app.followLink(url=self.helpUrl)


class CodeBox(BaseCodeEditor, handlers.ThemeMixin):
    # this comes mostly from the wxPython demo styledTextCtrl 2

    def __init__(self, parent, ID, prefs,
                 # set the viewer to be small, then it will increase with
                 # wx.aui control
                 pos=wx.DefaultPosition, size=wx.Size(100, 160),
                 style=0,
                 params=None,
                 codeType='Py'):

        BaseCodeEditor.__init__(self, parent, ID, pos, size, style)

        self.parent = parent
        self.app = parent.app
        self.prefs = prefs.coder
        self.appData = prefs.appData
        self.paths = prefs.paths
        self.params = params
        self.codeType = codeType
        lexers = {
            'Py': wx.stc.STC_LEX_PYTHON,
            'JS': wx.stc.STC_LEX_CPP,
            'txt': wx.stc.STC_LEX_CONTAINER
        }
        self.SetLexer(lexers[codeType])

        self.SetProperty("fold", "1")
        # 4 means 'tabs are bad'; 1 means 'flag inconsistency'
        self.SetProperty("tab.timmy.whinge.level", "4")
        self.SetViewWhiteSpace(self.appData['coder']['showWhitespace'])
        self.SetViewEOL(self.appData['coder']['showEOLs'])

        self.Bind(wx.stc.EVT_STC_MARGINCLICK, self.OnMarginClick)
        self.SetIndentationGuides(False)

        self.Bind(wx.EVT_KEY_DOWN, self.OnKeyPressed)

        # apply the theme to the lexer
        self._applyAppTheme()

    def OnKeyPressed(self, event):
        keyCode = event.GetKeyCode()
        _mods = event.GetModifiers()

        # Check combination keys
        if keyCode == ord('/') and wx.MOD_CONTROL == _mods:
            if self.params is not None:
                self.toggleCommentLines()
        elif keyCode == ord('V') and wx.MOD_CONTROL == _mods:
            self.Paste()
            return  # so that we don't reach the skip line at end

        if keyCode == wx.WXK_RETURN and not self.AutoCompActive():
            # process end of line and then do smart indentation
            event.Skip(False)
            self.CmdKeyExecute(wx.stc.STC_CMD_NEWLINE)
            if self.params is not None:
                self.smartIdentThisLine()
            return  # so that we don't reach the skip line at end

        event.Skip()

    def setStatus(self, status):
        if status == 'error':
            color = (255, 210, 210, 255)
        elif status == 'changed':
            color = (220, 220, 220, 255)
        else:
            color = (255, 255, 255, 255)
        self.StyleSetBackground(wx.stc.STC_STYLE_DEFAULT, color)
        self._applyAppTheme()

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

class CodeOverwriteDialog(wx.Dialog):
    def __init__(self, parent, ID, title,
                 msg='',
                 size=wx.DefaultSize,
                 pos=wx.DefaultPosition,
                 style=wx.DEFAULT_DIALOG_STYLE):

        wx.Dialog.__init__(self, parent, ID, title,
                           size=size, pos=pos, style=style)

        sizer = wx.BoxSizer(wx.VERTICAL)

        # Set warning Message
        msg = _translate(msg)

        warning = wx.StaticText(self, wx.ID_ANY, msg)
        warning.SetForegroundColour((200, 0, 0))
        sizer.Add(warning, 0, wx.ALIGN_CENTRE | wx.ALL, 5)

        # Set divider
        line = wx.StaticLine(self, wx.ID_ANY, size=(20, -1), style=wx.LI_HORIZONTAL)
        sizer.Add(line, 0, wx.GROW | wx.RIGHT | wx.TOP, 5)

        # Set buttons
        btnsizer = wx.StdDialogButtonSizer()

        btn = wx.Button(self, wx.ID_OK)
        btn.SetHelpText("The OK button completes the dialog")
        btn.SetDefault()
        btnsizer.AddButton(btn)

        btn = wx.Button(self, wx.ID_CANCEL)
        btn.SetHelpText("The Cancel button cancels the dialog. (Crazy, huh?)")
        btnsizer.AddButton(btn)
        btnsizer.Realize()

        sizer.Add(btnsizer, 0, wx.ALIGN_RIGHT | wx.ALL, 5)

        # Center and size
        self.CenterOnScreen()
        self.SetSizerAndFit(sizer)
