#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""To build simple dialogues etc. (requires wxPython)
"""

from psychopy import logging
import wx
import numpy
import os
from psychopy.localization import _translate
from packaging.version import Version

from psychopy.tools.arraytools import IndexDict

OK = wx.ID_OK

thisVer = Version(wx.__version__)

def ensureWxApp():
    # make sure there's a wxApp prior to showing a gui, e.g., for expInfo
    # dialog
    try:
        wx.Dialog(None, -1)  # not shown; FileDialog gives same exception
        return True
    except wx._core.PyNoAppError:
        if thisVer < Version('2.9'):
            return wx.PySimpleApp()
        elif thisVer >= Version('4.0') and thisVer < Version('4.1'):
            raise Exception(
                    "wx>=4.0 clashes with pyglet and making it unsafe "
                    "as a PsychoPy gui helper. Please install PyQt (4 or 5)"
                    " or wxPython3 instead.")
        else:
            return wx.App(False)


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
        myDlg.addField('Group:', choices=["Test", "Control"])
        myDlg.show()  # show dialog and wait for OK or Cancel
        if myDlg.OK:  # then the user pressed OK
            thisInfo = myDlg.data
            print(thisInfo)
        else:
            print('user cancelled')
    """

    def __init__(self, title=_translate('PsychoPy dialogue'),
                 pos=wx.DefaultPosition, size=wx.DefaultSize,
                 style=wx.DEFAULT_DIALOG_STYLE | wx.DIALOG_NO_PARENT,
                 labelButtonOK=_translate(" OK "),
                 labelButtonCancel=_translate(" Cancel ")):
        style = style | wx.RESIZE_BORDER
        global app  # avoid recreating for every gui
        if pos is None:
            pos = wx.DefaultPosition
        app = ensureWxApp()
        super().__init__(parent=None, id=-1, title=title, style=style, pos=pos)
        self.inputFields = []
        self.inputFieldTypes = []
        self.inputFieldNames = []
        self.data = []
        # prepare a frame in which to hold objects
        self.sizer = wx.BoxSizer(wx.VERTICAL)
        # self.addText('')  # insert some space at top of dialogue
        self.pos = pos
        self.labelButtonOK = labelButtonOK
        self.labelButtonCancel = labelButtonCancel

    def addText(self, text, color=''):
        # the horizontal extent can depend on the locale and font in use:
        font = self.GetFont()
        dc = wx.WindowDC(self)
        dc.SetFont(font)
        textWidth, textHeight = dc.GetTextExtent(text)
        textLength = wx.Size(textWidth + 50, textHeight)

        _style = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_CENTER_HORIZONTAL
        myTxt = wx.StaticText(self, -1, label=text, style=_style,
                              size=textLength)
        if len(color):
            myTxt.SetForegroundColour(color)
        self.sizer.Add(myTxt, 1, wx.ALIGN_CENTER)

    def addField(self, label='', initial='', color='', choices=None, tip=''):
        """Adds a (labelled) input field to the dialogue box, optional text
        color and tooltip. Returns a handle to the field (but not to the
        label). If choices is a list or tuple, it will create a dropdown
        selector.
        """
        self.inputFieldNames.append(label)
        if choices:
            self.inputFieldTypes.append(str)
        else:
            self.inputFieldTypes.append(type(initial))
        if type(initial) == numpy.ndarray:
            initial = initial.tolist()  # convert numpy arrays to lists
        container = wx.GridSizer(cols=2, vgap=0, hgap=10)
        # create label
        font = self.GetFont()
        dc = wx.WindowDC(self)
        dc.SetFont(font)
        labelWidth, labelHeight = dc.GetTextExtent(label)
        labelLength = wx.Size(labelWidth + 16, labelHeight)
        inputLabel = wx.StaticText(self, -1, label,
                                   size=labelLength,
                                   style=wx.ALIGN_RIGHT)
        if len(color):
            inputLabel.SetForegroundColour(color)
        _style = wx.ALIGN_CENTER_VERTICAL | wx.ALIGN_RIGHT
        container.Add(inputLabel, 1, _style)
        # create input control
        if type(initial) == bool:
            inputBox = wx.CheckBox(self, -1)
            inputBox.SetValue(initial)
        elif not choices:
            inputWidth, inputHeight = dc.GetTextExtent(str(initial))
            inputLength = wx.Size(max(50, inputWidth + 16),
                                  max(25, inputHeight + 8))
            inputBox = wx.TextCtrl(self, -1, str(initial),
                                   size=inputLength)
        else:
            inputBox = wx.Choice(self, -1,
                                 choices=[str(option)
                                          for option in list(choices)])
            # Somewhat dirty hack that allows us to treat the choice just like
            # an input box when retrieving the data
            inputBox.GetValue = inputBox.GetStringSelection
            initial = choices.index(initial) if initial in choices else 0
            inputBox.SetSelection(initial)
        if len(color):
            inputBox.SetForegroundColour(color)
        if len(tip):
            inputBox.SetToolTip(wx.ToolTip(tip))

        container.Add(inputBox, 1, wx.ALIGN_CENTER_VERTICAL)
        self.sizer.Add(container, 1, wx.ALIGN_CENTER)

        self.inputFields.append(inputBox)  # store this to get data back on OK
        return inputBox

    def addFixedField(self, label='', value='', tip=''):
        """Adds a field to the dialogue box (like addField) but the
        field cannot be edited. e.g. Display experiment version.
        tool-tips are disabled (by wx).
        """
        thisField = self.addField(label, value, color='Gray', tip=tip)
        # wx disables tooltips too; we pass them in anyway
        thisField.Disable()
        return thisField

    def display(self):
        """Presents the dialog and waits for the user to press OK or CANCEL.

        If user presses OK button, function returns a list containing the
        updated values coming from each of the input fields created.
        Otherwise, None is returned.

        :return: self.data
        """
        # add buttons for OK and Cancel
        buttons = self.CreateStdDialogButtonSizer(flags=wx.OK | wx.CANCEL)
        self.sizer.Add(buttons, 1, flag=wx.ALIGN_RIGHT, border=5)

        self.SetSizerAndFit(self.sizer)
        if self.pos is None:
            self.Center()
        if self.ShowModal() == wx.ID_OK:
            self.data = []
            # get data from input fields
            for n in range(len(self.inputFields)):
                thisName = self.inputFieldNames[n]
                thisVal = self.inputFields[n].GetValue()
                thisType = self.inputFieldTypes[n]
                # try to handle different types of input from strings
                logging.debug("%s: %s" % (self.inputFieldNames[n],
                                          str(thisVal)))
                if thisType in (tuple, list, float, int):
                    # probably a tuple or list
                    exec("self.data.append(" + thisVal + ")")  # evaluate it
                elif thisType == numpy.ndarray:
                    exec("self.data.append(numpy.array(" + thisVal + "))")
                elif thisType in (str, bool):
                    self.data.append(thisVal)
                else:
                    logging.warning('unknown type:' + self.inputFieldNames[n])
                    self.data.append(thisVal)
            self.OK = True
        else:
            self.OK = False
        self.Destroy()
        if self.OK:
            return self.data

    def show(self):
        """Presents the dialog and waits for the user to press either
        OK or CANCEL.

        When they do, dlg.OK will be set to True or False (according to
        which button they pressed. If OK==True then dlg.data will be
        populated with a list of values coming from each of the input
        fields created.
        """
        return self.display()

class DlgFromDict(Dlg):
    """Creates a dialogue box that represents a dictionary of values.
    Any values changed by the user are change (in-place) by this
    dialogue box.

    Parameters
    ----------

    sortKeys : bool
        Whether the dictionary keys should be ordered alphabetically
        for displaying.

    copyDict : bool
        If False, modify ``dictionary`` in-place. If True, a copy of
        the dictionary is created, and the altered version (after
        user interaction) can be retrieved from
        :attr:~`psychopy.gui.DlgFromDict.dictionary`.

    show : bool
        Whether to immediately display the dialog upon instantiation.
         If False, it can be displayed at a later time by calling
         its `show()` method.

    e.g.:

    ::

        info = {'Observer':'jwp', 'GratingOri':45,
                'ExpVersion': 1.1, 'Group': ['Test', 'Control']}
        infoDlg = gui.DlgFromDict(dictionary=info,
                    title='TestExperiment', fixed=['ExpVersion'])
        if infoDlg.OK:
            print(info)
        else:
            print('User Cancelled')

    In the code above, the contents of *info* will be updated to the values
    returned by the dialogue box.

    If the user cancels (rather than pressing OK),
    then the dictionary remains unchanged. If you want to check whether
    the user hit OK, then check whether DlgFromDict.OK equals
    True or False

    See GUI.py for a usage demo, including order and tip (tooltip).
    """

    def __init__(self, dictionary, title='', fixed=None, order=None, tip=None,
                 sortKeys=True, copyDict=False, show=True,
                 sort_keys=None, copy_dict=None):
        # We don't explicitly check for None identity
        # for backward-compatibility reasons.
        if not fixed:
            fixed = []
        if not order:
            order = []
        if not tip:
            tip = dict()

        # app = ensureWxApp() done by Dlg
        super().__init__(title)

        self.copyDict = copyDict
        self.originalDictionary = dictionary
        self.dictionary = IndexDict(dictionary)

        self._keys = list(self.dictionary.keys())

        if sortKeys:
            self._keys.sort()
        if order:
            self._keys = list(order) + list(set(self._keys).difference(set(order)))

        types = dict()

        for field in self._keys:
            types[field] = type(self.dictionary[field])
            tooltip = ''
            if field in tip:
                tooltip = tip[field]
            if field in fixed:
                self.addFixedField(field, self.dictionary[field], tip=tooltip)
            elif type(self.dictionary[field]) in [list, tuple]:
                self.addField(field, choices=self.dictionary[field],
                              tip=tooltip)
            else:
                self.addField(field, self.dictionary[field], tip=tooltip)

        if show:
            self.show()

    def show(self):
        """Display the dialog.
        """
        super().show()
        if self.OK:
            for n, thisKey in enumerate(self._keys):
                self.dictionary[thisKey] = self.data[n]
            # if not copying dict, set values in-place
            if not self.copyDict:
                self.originalDictionary[thisKey] = self.data[thisKey]
            
            return self.dictionary


def fileSaveDlg(initFilePath="", initFileName="",
                prompt=_translate("Select file to save"),
                allowed=None):
    """A simple dialogue allowing write access to the file system.
    (Useful in case you collect an hour of data and then try to
    save to a non-existent directory!!)

    :parameters:

        initFilePath: string
            default file path on which to open the dialog

        initFileName: string
            default file name, as suggested file

        prompt: string (default "Select file to open")
            can be set to custom prompts

        allowed: string
            A string to specify file filters.
            e.g. "BMP files (*.bmp)|*.bmp|GIF files (*.gif)|*.gif"
            See https://docs.wxpython.org/wx.FileDialog.html
            for further details

    If initFilePath or initFileName are empty or invalid then
    current path and empty names are used to start search.

    If user cancels the None is returned.
    """
    if allowed is None:
        allowed = "All files (*.*)|*.*"
        # "txt (*.txt)|*.txt"
        # "pickled files (*.pickle, *.pkl)|*.pickle"
        # "shelved files (*.shelf)|*.shelf"
    global app  # avoid recreating for every gui
    app = ensureWxApp()
    dlg = wx.FileDialog(None, prompt, initFilePath,
                        initFileName, allowed, wx.FD_SAVE)
    if dlg.ShowModal() == OK:
        # get names of images and their directory
        outName = dlg.GetFilename()
        outPath = dlg.GetDirectory()
        dlg.Destroy()
        # tmpApp.Destroy()  # this causes an error message for some reason
        fullPath = os.path.join(outPath, outName)
    else:
        fullPath = None
    return fullPath


def fileOpenDlg(tryFilePath="",
                tryFileName="",
                prompt=_translate("Select file(s) to open"),
                allowed=None):
    """A simple dialogue allowing read access to the file system.

    :parameters:
        tryFilePath: string
            default file path on which to open the dialog
        tryFileName: string
            default file name, as suggested file
        prompt: string (default "Select file to open")
            can be set to custom prompts
        allowed: string (available since v1.62.01)
            a string to specify file filters.
            e.g. "BMP files (*.bmp)|*.bmp|GIF files (*.gif)|*.gif"
            See https://docs.wxpython.org/wx.FileDialog.html
            for further details

    If tryFilePath or tryFileName are empty or invalid then
    current path and empty names are used to start search.

    If user cancels, then None is returned.
    """
    if allowed is None:
        allowed = ("PsychoPy Data (*.psydat)|*.psydat|"
                   "txt (*.txt,*.dlm,*.csv)|*.txt;*.dlm;*.csv|"
                   "pickled files (*.pickle, *.pkl)|*.pickle|"
                   "shelved files (*.shelf)|*.shelf|"
                   "All files (*.*)|*.*")
    global app  # avoid recreating for every gui
    app = ensureWxApp()
    dlg = wx.FileDialog(None, prompt, tryFilePath, tryFileName, allowed,
                        wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
    if dlg.ShowModal() == OK:
        # get names of images and their directory
        fullPaths = dlg.GetPaths()
    else:
        fullPaths = None
    dlg.Destroy()
    return fullPaths
