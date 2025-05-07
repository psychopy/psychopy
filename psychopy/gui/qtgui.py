#!/usr/bin/env python
# -*- coding: utf-8 -*-

# To build simple dialogues etc. (requires pyqt4)
#
#  Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import importlib
from psychopy import logging, data
from psychopy.tools.arraytools import IndexDict
from . import util

haveQt = False  # until we confirm otherwise
importOrder = ['PyQt6', 'PyQt5']

for libname in importOrder:
    try:
        importlib.import_module(f"{libname}.QtCore")
        haveQt = libname
        logging.debug(f"psychopy.gui is using {haveQt}")
        break
    except ModuleNotFoundError:
        pass

if not haveQt:
    # do the main import again not in a try...except to recreate error
    import PyQt6
elif haveQt == 'PyQt6':
    from PyQt6 import QtWidgets
    from PyQt6 import QtGui
    from PyQt6.QtCore import Qt
elif haveQt == 'PyQt5':
    from PyQt5 import QtWidgets
    from PyQt5 import QtGui
    from PyQt5.QtCore import Qt

from psychopy import logging
import numpy as np
import os
import sys
import json
from psychopy.localization import _translate


qtapp = QtWidgets.QApplication.instance()


def ensureQtApp():
    global qtapp
    # make sure there's a QApplication prior to showing a gui, e.g., for expInfo
    # dialog
    if qtapp is None:
        qtapp = QtWidgets.QApplication(sys.argv)
        qtapp.setStyle('Fusion')  # use this to avoid annoying PyQt bug with OK being greyed-out


wasMouseVisible = True


class ReadmoreCtrl(QtWidgets.QLabel):
    """
    A linked label which shows/hides a set of control on click.
    """
    def __init__(self, parent, label=""):
        QtWidgets.QLabel.__init__(self, parent)
        # set initial state and label
        self.state = False
        self.label = label
        self.updateLabel()
        # array to store linked ctrls
        self.linkedCtrls = []
        # bind onclick
        self.setOpenExternalLinks(False)
        self.linkActivated.connect(self.onToggle)

    def updateLabel(self):
        """
        Update label so that e.g. arrow matches current state.
        """
        # reset label to its own value to refresh
        self.setLabel(self.label)

    def setLabel(self, label=""):
        """
        Set the label of this ctrl (will append arrow and necessary HTML for a link)
        """
        # store label root
        self.label = label
        # choose an arrow according to state
        if self.state:
            arrow = "▾"
        else:
            arrow = "▸"
        # construct text to set
        text = f"<a href='.' style='color: black; text-decoration: none;'>{arrow} {label}</a>"
        # set label text
        self.setText(text)

    def onToggle(self, evt=None):
        """
        Toggle visibility of linked ctrls. Called on press.
        """
        # toggle state
        self.state = not self.state
        # show/hide linked ctrls according to state
        for ctrl in self.linkedCtrls:
            if self.state:
                ctrl.show()
            else:
                ctrl.hide()
        # update label
        self.updateLabel()
        # resize dlg
        self.parent().adjustSize()

    def linkCtrl(self, ctrl):
        """
        Connect a ctrl to this ReadmoreCtrl such that it's shown/hidden on toggle.
        """
        # add to array of linked ctrls
        self.linkedCtrls.append(ctrl)
        # show/hide according to own state
        if self.state:
            ctrl.show()
        else:
            ctrl.hide()
        # resize dlg
        self.parent().adjustSize()


class Dlg(QtWidgets.QDialog):
    """A simple dialogue box. You can add text or input boxes
    (sequentially) and then retrieve the values.

    see also the function *dlgFromDict* for an **even simpler** version

    **Example**

    .. code-block:: python

        from psychopy import gui

        myDlg = gui.Dlg(title="JWP's experiment")
        myDlg.addText('Subject info')
        myDlg.addField('Name:')
        myDlg.addField('Age:', 21)
        myDlg.addText('Experiment Info')
        myDlg.addField('Grating Ori:',45)
        myDlg.addField('Group:', choices=["Test", "Control"])
        ok_data = myDlg.show()  # show dialog and wait for OK or Cancel
        if myDlg.OK:  # or if ok_data is not None
            print(ok_data)
        else:
            print('user cancelled')

    """

    def __init__(self, title=_translate('PsychoPy Dialog'),
                 pos=None, size=None, style=None,
                 labelButtonOK=_translate(" OK "),
                 labelButtonCancel=_translate(" Cancel "),
                 screen=-1, alwaysOnTop=False):

        ensureQtApp()
        QtWidgets.QDialog.__init__(self, None)

        self.inputFields = []
        self.inputFieldTypes = {}
        self.inputFieldNames = []
        self.data = IndexDict()
        self.irow = 0
        self.pos = pos
        # QtWidgets.QToolTip.setFont(QtGui.QFont('SansSerif', 10))

        # set always stay on top
        if alwaysOnTop:
            if hasattr(Qt.WindowType, 'WindowStaysOnTopHint'):
                self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)

        # add buttons for OK and Cancel
        if hasattr(QtWidgets.QDialogButtonBox.StandardButton, 'Ok'):
            # PyQt6 upwards?
            okBtn = QtWidgets.QDialogButtonBox.StandardButton.Ok
            cancelBtn = QtWidgets.QDialogButtonBox.StandardButton.Cancel
        else:
            # e.g. PyQt5
            okBtn = QtWidgets.QDialogButtonBox.Ok
            cancelBtn = QtWidgets.QDialogButtonBox.Cancel
            
        self.buttonBox = QtWidgets.QDialogButtonBox(okBtn | cancelBtn, parent=self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        # store references to OK and CANCEL buttons
        self.okBtn = self.buttonBox.button(okBtn)
        self.cancelBtn = self.buttonBox.button(cancelBtn)

        if style:
            raise RuntimeWarning("Dlg does not currently support the "
                                 "style kwarg.")
        self.size = size

        if haveQt in ['PyQt5', 'PyQt6']:
            nScreens = len(qtapp.screens())
        else:
            nScreens = QtWidgets.QDesktopWidget().screenCount()
        self.screen = -1 if screen >= nScreens else screen
        # self.labelButtonOK = labelButtonOK
        # self.labelButtonCancel = labelButtonCancel

        self.layout = QtWidgets.QGridLayout()
        self.layout.setSpacing(10)
        self.layout.setColumnMinimumWidth(1, 250)

        # add placeholder for readmore control sizer
        self.readmore = None

        # add message about required fields (shown/hidden by validate)
        msg = _translate("Fields marked with an asterisk (*) are required.")
        self.requiredMsg = QtWidgets.QLabel(text=msg, parent=self)
        self.layout.addWidget(self.requiredMsg, 0, 0, 1, -1)
        self.irow += 1

        self.setLayout(self.layout)

        self.setWindowTitle(title)

    def addText(self, text, color='', isFieldLabel=False):
        textLabel = QtWidgets.QLabel(text, parent=self)

        if len(color):
            textLabel.setStyleSheet("color: {0};".format(color))

        if isFieldLabel is True:
            self.layout.addWidget(textLabel, self.irow, 0, 1, 1)
        else:
            self.layout.addWidget(textLabel, self.irow, 0, 1, 2)
            self.irow += 1

        return textLabel

    def addField(self, key, initial='', color='', choices=None, tip='',
                 required=False, enabled=True, label=None):
        """Adds a (labelled) input field to the dialogue box,
        optional text color and tooltip.

        If 'initial' is a bool, a checkbox will be created.
        If 'choices' is a list or tuple, a dropdown selector is created.
        Otherwise, a text line entry box is created.

        Returns a handle to the field (but not to the label).
        """
        # if not given a label, use key (sans-pipe syntax)
        if label is None:
            label, _ = util.parsePipeSyntax(key)

        self.inputFieldNames.append(label)
        if choices:
            self.inputFieldTypes[label] = str
        else:
            self.inputFieldTypes[label] = type(initial)
        if type(initial) == np.ndarray:
            initial = initial.tolist()

        # create label
        inputLabel = self.addText(label, color, isFieldLabel=True)

        # create input control
        if type(initial) == bool and not choices:
            self.data[key] = initial
            inputBox = QtWidgets.QCheckBox(parent=self)
            inputBox.setChecked(initial)

            def handleCheckboxChange(new_state):
                self.data[key] = inputBox.isChecked()
                msg = "handleCheckboxChange: inputFieldName={0}, checked={1}"
                logging.debug(msg.format(label, self.data[key]))

            inputBox.stateChanged.connect(handleCheckboxChange)
        elif not choices:
            self.data[key] = initial
            inputBox = QtWidgets.QLineEdit(str(initial), parent=self)

            def handleLineEditChange(new_text):
                ix = self.inputFields.index(inputBox)
                name = self.inputFieldNames[ix]
                thisType = self.inputFieldTypes[name]

                try:
                    if thisType in (str, bytes):
                        self.data[key] = str(new_text)
                    elif thisType == tuple:
                        jtext = "[" + str(new_text) + "]"
                        self.data[key] = json.loads(jtext)[0]
                    elif thisType == list:
                        jtext = "[" + str(new_text) + "]"
                        self.data[key] = json.loads(jtext)[0]
                    elif thisType == float:
                        self.data[key] = float(new_text)
                    elif thisType == int:
                        self.data[key] = int(new_text)
                    elif thisType == dict:
                        jtext = "[" + str(new_text) + "]"
                        self.data[key] = json.loads(jtext)[0]
                    elif thisType == np.ndarray:
                        self.data[key] = np.array(
                            json.loads("[" + str(new_text) + "]")[0])
                    else:
                        self.data[key] = new_text
                        msg = ("Unknown type in handleLineEditChange: "
                               "inputFieldName={0}, type={1}, value={2}")
                        logging.warning(msg.format(label, thisType,
                                                   self.data[ix]))
                    msg = ("handleLineEditChange: inputFieldName={0}, "
                           "type={1}, value={2}")
                    logging.debug(msg.format(label, thisType, self.data[key]))
                except Exception as e:
                    self.data[key] = str(new_text)
                    msg = ('Error in handleLineEditChange: inputFieldName='
                           '{0}, type={1}, value={2}, error={3}')
                    logging.error(msg.format(label, thisType, self.data[key],
                                             e))

                self.validate()

            inputBox.textEdited.connect(handleLineEditChange)
        else:
            inputBox = QtWidgets.QComboBox(parent=self)
            choices = list(choices)
            for i, option in enumerate(choices):
                inputBox.addItem(str(option))
                # inputBox.addItems([unicode(option) for option in choices])
                inputBox.setItemData(i, (option,))

            if (isinstance(initial, (int, int)) and
                    len(choices) > initial >= 0):
                pass
            elif initial in choices:
                initial = choices.index(initial)
            else:
                initial = 0
            inputBox.setCurrentIndex(initial)

            self.data[key] = choices[initial]

            def handleCurrentIndexChanged(new_index):
                ix = self.inputFields.index(inputBox)
                try:
                    self.data[key] = inputBox.itemData(new_index).toPyObject()[0]
                except AttributeError:
                    self.data[key] = inputBox.itemData(new_index)[0]
                msg = ("handleCurrentIndexChanged: inputFieldName={0}, "
                       "selected={1}, type: {2}")
                logging.debug(msg.format(label, self.data[key],
                                         type(self.data[key])))

            inputBox.currentIndexChanged.connect(handleCurrentIndexChanged)

        # set required (attribute is checked later by validate fcn)
        inputBox.required = required

        if color is not None and len(color):
            inputBox.setPalette(inputLabel.palette())
        if tip is not None and len(tip):
            inputBox.setToolTip(tip)
        inputBox.setEnabled(enabled)
        self.layout.addWidget(inputBox, self.irow, 1)

        # link to readmore ctrl if we're in one
        if self.readmore is not None:
            self.readmore.linkCtrl(inputBox)
            self.readmore.linkCtrl(inputLabel)

        self.inputFields.append(inputBox)  # store this to get data back on OK
        self.irow += 1

        return inputBox

    def addFixedField(self, key, label='', initial='', color='', choices=None,
                      tip=''):
        """Adds a field to the dialog box (like addField) but the field cannot
        be edited. e.g. Display experiment version.
        """
        return self.addField(
            key=key, label=label, initial=initial, color=color, choices=choices, tip=tip, 
            enabled=False
        )

    def addReadmoreCtrl(self):
        line = ReadmoreCtrl(self, label=_translate("Configuration fields..."))

        self.layout.addWidget(line, self.irow, 0, 1, 2)
        self.irow += 1

        self.enterReadmoreCtrl(line)

        return line

    def enterReadmoreCtrl(self, ctrl):
        self.readmore = ctrl

    def exitReadmoreCtrl(self):
        self.readmore = None

    def display(self):
        """Presents the dialog and waits for the user to press OK or CANCEL.

        If user presses OK button, function returns a list containing the
        updated values coming from each of the input fields created.
        Otherwise, None is returned.

        :return: self.data
        """
        return self.exec_()

    def validate(self):
        """
        Make sure that required fields have a value.
        """
        # start off assuming valid
        valid = True
        # start off assuming no required fields
        hasRequired = False
        # iterate through fields
        for field in self.inputFields:
            # if field isn't required, skip
            if not field.required:
                continue
            # if we got this far, we have a required field
            hasRequired = True
            # validation is only relevant for text fields, others have defaults
            if not isinstance(field, QtWidgets.QLineEdit):
                continue
            # check that we have text
            if not len(field.text()):
                valid = False
        # if not valid, disable OK button
        self.okBtn.setEnabled(valid)
        # show required message if we have any required fields
        if hasRequired:
            self.requiredMsg.show()
        else:
            self.requiredMsg.hide()

    def show(self):
        """Presents the dialog and waits for the user to press OK or CANCEL.

        If user presses OK button, function returns a list containing the
        updated values coming from each of the input fields created.
        Otherwise, None is returned.

        :return: self.data
        """
        #    NB
        #
        #    ** QDialog already has a show() method. So this method calls
        #       QDialog.show() and then exec_(). This seems to not cause issues
        #       but we need to keep an eye out for any in future.
        return self.display()

    def exec_(self):
        """Presents the dialog and waits for the user to press OK or CANCEL.

        If user presses OK button, function returns a list containing the
        updated values coming from each of the input fields created.
        Otherwise, None is returned.
        """

        self.layout.addWidget(self.buttonBox, self.irow, 0, 1, 2)

        if self.pos is None:
            # Center Dialog on appropriate screen
            frameGm = self.frameGeometry()
            if self.screen <= 0:
                qtscreen = QtGui.QGuiApplication.primaryScreen()
            else:
                qtscreen = self.screen
            centerPoint = qtscreen.availableGeometry().center()
            frameGm.moveCenter(centerPoint)
            self.move(frameGm.topLeft())
        else:
            self.move(self.pos[0], self.pos[1])
        QtWidgets.QDialog.show(self)
        self.raise_()
        self.activateWindow()
        if self.inputFields:
            self.inputFields[0].setFocus()

        self.OK = False
        if QtWidgets.QDialog.exec(self):  # == QtWidgets.QDialog.accepted:
            self.OK = True
            return self.data


class DlgFromDict(Dlg):
    """Creates a dialogue box that represents a dictionary of values.
    Any values changed by the user are change (in-place) by this
    dialogue box.

    Parameters
    ----------

    dictionary : dict
        A dictionary defining the input fields (keys) and pre-filled values
        (values) for the user dialog
        
    title : str
        The title of the dialog window

    labels : dict
        A dictionary defining labels (values) to be displayed instead of
        key strings (keys) defined in `dictionary`. Not all keys in
        `dictionary` need to be contained in labels.

    fixed : list
        A list of keys for which the values shall be displayed in non-editable
        fields
    
    order : list
        A list of keys defining the display order of keys in `dictionary`.
        If not all keys in `dictionary`` are contained in `order`, those
        will appear in random order after all ordered keys.

    tip : list
        A dictionary assigning tooltips to the keys

    screen : int
        Screen number where the Dialog is displayed. If -1, the Dialog will
        be displayed on the primary screen.

    sortKeys : bool
        A boolean flag indicating that keys are to be sorted alphabetically.

    copyDict : bool
        If False, modify `dictionary` in-place. If True, a copy of
        the dictionary is created, and the altered version (after
        user interaction) can be retrieved from
        :attr:~`psychopy.gui.DlgFromDict.dictionary`.
        
    labels : dict
        A dictionary defining labels (dict values) to be displayed instead of
        key strings (dict keys) defined in `dictionary`. Not all keys in
        `dictionary´ need to be contained in labels.

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

    def __init__(self, dictionary, title='', fixed=None, order=None,
                 tip=None, screen=-1, sortKeys=True, copyDict=False,
                 labels=None, show=True, alwaysOnTop=False):
        # Note: As of 2023.2.0, we do not allow sort_keys or copy_dict

        Dlg.__init__(self, title, screen=screen, alwaysOnTop=alwaysOnTop)

        if copyDict:
            self.dictionary = dictionary.copy()
        else:
            self.dictionary = dictionary
        # initialise storage attributes
        self._labels = []
        self._keys = []
        # convert to a list of params
        params = util.makeDisplayParams(
            self.dictionary,
            sortKeys=sortKeys,
            labels=labels,
            tooltips=tip,
            order=order,
            fixed=fixed
        )
        # make ctrls
        for param in params:
            # if param is the readmore button, add it and continue
            if param == "---":
                self.addReadmoreCtrl()
                continue
            # add asterisk to label if needed
            if "req" in param['flags'] and "*" not in param['label']:
                param['label'] += "*"
            # store attributes from this param
            self._labels.append(param['label'])
            self._keys.append(param['key'])
            # make ctrls
            if "hid" in param['flags']:
                # don't add anything if it's hidden
                pass
            elif "fix" in param['flags']:
                self.addFixedField(
                    param['key'],
                    label=param['label'],
                    initial=param['value'],
                    tip=param['tip']
                )
            elif isinstance(param['value'], (list, tuple)):
                self.addField(
                    param['key'],
                    choices=param['value'],
                    label=param['label'],
                    tip=param['tip'],
                    required="req" in param['flags']
                )
            else:
                self.addField(
                    param['key'],
                    initial=param['value'],
                    label=param['label'],
                    tip=param['tip'],
                    required="req" in param['flags']
                )

        # validate so the required message is shown/hidden as appropriate
        self.validate()

        if show:
            self.show()

    def show(self):
        """Display the dialog.
        """
        data = self.exec_()
        if data is not None:
            self.dictionary.update(data)
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
            a string to specify file filters.
            e.g. "Text files (\\*.txt) ;; Image files (\\*.bmp \\*.gif)"
            See https://www.riverbankcomputing.com/static/Docs/PyQt4/qfiledialog.html
            #getSaveFileName
            for further details

    If initFilePath or initFileName are empty or invalid then
    current path and empty names are used to start search.

    If user cancels the None is returned.
    """
    if allowed is None:
        allowed = ("All files (*.*);;"
                   "txt (*.txt);;"
                   "pickled files (*.pickle *.pkl);;"
                   "shelved files (*.shelf)")
    ensureQtApp()

    fdir = os.path.join(initFilePath, initFileName)
    pathOut = QtWidgets.QFileDialog.getSaveFileName(parent=None, caption=prompt,
                                              directory=fdir, filter=allowed)
    if type(pathOut) == tuple:  # some versions(?) of PyQt return (files, filter)
        pathOut = pathOut[0]

    if len(pathOut) == 0:
        return None
    return str(pathOut) or None


def fileOpenDlg(tryFilePath="",
                tryFileName="",
                prompt=_translate("Select file to open"),
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
            e.g. "Text files (\\*.txt) ;; Image files (\\*.bmp \\*.gif)"
            See https://www.riverbankcomputing.com/static/Docs/PyQt4/qfiledialog.html
            #getOpenFileNames
            for further details

    If tryFilePath or tryFileName are empty or invalid then
    current path and empty names are used to start search.

    If user cancels, then None is returned.
    """
    ensureQtApp()

    if allowed is None:
        allowed = ("All files (*.*);;"
                   "PsychoPy Data (*.psydat);;"
                   "txt (*.txt *.dlm *.csv);;"
                   "pickled files (*.pickle *.pkl);;"
                   "shelved files (*.shelf)")
    fdir = os.path.join(tryFilePath, tryFileName)
    filesToOpen = QtWidgets.QFileDialog.getOpenFileNames(parent=None,
                                                         caption=prompt,
                                                         directory=fdir,
                                                         filter=allowed)
    if type(filesToOpen) == tuple:  # some versions(?) of PyQt return (files, filter)
        filesToOpen = filesToOpen[0]

    filesToOpen = [str(fpath) for fpath in filesToOpen
                   if os.path.exists(fpath)]
    if len(filesToOpen) == 0:
        return None
    return filesToOpen


def infoDlg(title=_translate("Information"), prompt=None):
    ensureQtApp()
    _pr = _translate("No details provided. ('prompt' value not set).")
    QtWidgets.QMessageBox.information(None, title, prompt or _pr)


def warnDlg(title=_translate("Warning"), prompt=None):
    ensureQtApp()
    _pr = _translate("No details provided. ('prompt' value not set).")
    QtWidgets.QMessageBox.warning(None, title, prompt or _pr)


def criticalDlg(title=_translate("Critical"), prompt=None):
    ensureQtApp()
    _pr = _translate("No details provided. ('prompt' value not set).")
    QtWidgets.QMessageBox.critical(None, title, prompt or _pr)


def aboutDlg(title=_translate("About Experiment"), prompt=None):
    ensureQtApp()
    _pr = _translate("No details provided. ('prompt' value not set).")
    QtWidgets.QMessageBox.about(None, title, prompt or _pr)


# Psychopy pyglet window show / hide util functions


def hideWindow(win):
    global wasMouseVisible
    if win.winHandle._visible is True:
        wasMouseVisible = win.mouseVisible
        win.setMouseVisible(True, log=False)
        win.winHandle.minimize()


def showWindow(win):
    global wasMouseVisible
    if win.winHandle._visible is False:
        win.setMouseVisible(wasMouseVisible, log=False)
        win.winHandle.maximize()
        win.winHandle.set_visible(True)
        win.winHandle.activate()


if __name__ == '__main__':
    # Local manual test cases for dialog types....

    logging.console.setLevel(logging.DEBUG)

    # from psychopy import visual, event
    # Create, and hide, a full screen psychopy window
    # win = visual.Window([1024, 768],
    #                    fullscr=True,
    #                    allowGUI=False,
    #                    screen=0)
    # hideWindow(win)

    # Test base Dlg class

    dlg = Dlg()
    dlg.addText("This is a line of text", color="Red")
    dlg.addText("Second line of text")
    dlg.addField("A checkbox", initial=True, tip="Here is your checkbox tip!")
    dlg.addField("Another checkbox", initial=False, color="Blue")
    dlg.addFixedField("ReadOnly checkbox", initial=False, color="Blue",
                      tip="This field is readonly.")
    dlg.addField("A textline", initial="",
                 tip="Here is your <b>textline</b> tip!")
    dlg.addField("A Number:", initial=23, tip="This must be a number.")
    dlg.addField("A List:", initial=[0, 1, 2, 3, 4, 5, 6, 7, 8, 9],
                 tip="This must be a list.")
    dlg.addField("A ndarray:",
                 initial=np.asarray([0, 1, 2, 3, 4, 5, 6, 7, 8, 9]),
                 tip="This must be a numpy array.")
    dlg.addField("Another textline", initial="default text", color="Green")
    dlg.addFixedField("ReadOnly textline", initial="default text",
                      tip="This field is readonly.")
    dlg.addField("A dropdown", initial='B', choices=['A', 'B', 'C'],
                 tip="Here is your <b>dropdown</b> tip!")

    dlg.addField("Mixed type dropdown", initial=2,
                 choices=['A String', 1234567, [12.34, 56.78],
                          ('tuple element 0', 'tuple element 1'),
                          {'key1': 'val1', 'key2': 23}],
                 color="Red")

    dlg.addField("Yet Another dropdown", choices=[1, 2, 3])
    dlg.addFixedField("ReadOnly dropdown", initial=2,
                      choices=['R1', 'R2', 'R3'],
                      tip="This field is readonly.")
    ok_data = dlg.show()
    print(("Dlg ok_data:", ok_data))

    # Test Dict Dialog

    info = {'Observer*': 'jwp', 'GratingOri': 45,
            'ExpVersion': 1.1, 'Group': ['Test', 'Control']}
    dictDlg = DlgFromDict(dictionary=info, title='TestExperiment',
                          labels={'Group': 'Participant Group'},
                          fixed=['ExpVersion'])
    if dictDlg.OK:
        print(info)
    else:
        print('User Cancelled')

    # Test File Dialogs

    fileToSave = fileSaveDlg(initFileName='__init__.pyc')
    print(("fileToSave: [", fileToSave, "]", type(fileToSave)))

    fileToOpen = fileOpenDlg()
    print(("fileToOpen:", fileToOpen))

    # Test Alert Dialogs

    infoDlg(prompt="Some not important info for you.")

    warnDlg(prompt="Something non critical,\nbut worth mention,\noccurred.")

    _pr = "Oh boy, something really bad just happened:<br><b>{0}</b>"
    criticalDlg(title="RuntimeError",
                prompt=_pr.format(RuntimeError("A made up runtime error")))

    aboutDlg(prompt=u"My Experiment v. 1.0"
             u"<br>"
             u"Written by: Dr. John Doe"
             u"<br>"
             u"Created using <b>PsychoPy</b> © Copyright 2018, Jonathan Peirce")

    # Restore full screen psychopy window
    # showWindow(win)
    # win.flip()
    # from psychopy import event
    # event.waitKeys()

