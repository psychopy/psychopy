#!/usr/bin/env python
# -*- coding: utf-8 -*-

# To build simple dialogues etc. (requires pyqt4)
#
#  Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

haveQt = False  # until we confirm otherwise
importOrder = ['PyQt5', 'PyQt4']

for libname in importOrder:
    try:
        exec("import {}".format(libname))
        haveQt = libname
        break
    except ImportError:
        pass

if not haveQt:
    # do the main import again not in a try...except to recreate error
    exec("import {}".format(importOrder[0]))
elif haveQt == 'PyQt5':
    from PyQt5 import QtWidgets
    from PyQt5 import QtGui
    from PyQt5.QtCore import Qt
else:
    from PyQt4 import QtGui  
    QtWidgets = QtGui  # in qt4 these were all in one package
    from PyQt4.QtCore import Qt

from psychopy import logging
import numpy as np
import os
import sys
import json
from psychopy.localization import _translate

OK = QtWidgets.QDialogButtonBox.Ok

qtapp = QtWidgets.QApplication.instance()


def ensureQtApp():
    global qtapp
    # make sure there's a QApplication prior to showing a gui, e.g., for expInfo
    # dialog
    if qtapp is None:
        qtapp = QtWidgets.QApplication(sys.argv)
        qtapp.setStyle('Fusion')  # use this to avoid annoying PyQt bug with OK being greyed-out


wasMouseVisible = True


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
                 screen=-1):

        ensureQtApp()
        QtWidgets.QDialog.__init__(self, None, Qt.WindowTitleHint)

        self.inputFields = []
        self.inputFieldTypes = {}
        self.inputFieldNames = []
        self.data = []
        self.irow = 0
        self.pos = pos
        # QtWidgets.QToolTip.setFont(QtGui.QFont('SansSerif', 10))

        # add buttons for OK and Cancel
        self.buttonBox = QtWidgets.QDialogButtonBox(Qt.Horizontal,
                                                    parent=self)
        self.okbutton = QtWidgets.QPushButton(labelButtonOK,
                                              parent=self)
        self.cancelbutton = QtWidgets.QPushButton(labelButtonCancel,
                                                  parent=self)
        self.buttonBox.addButton(self.okbutton,
                                 QtWidgets.QDialogButtonBox.ActionRole)
        self.buttonBox.addButton(self.cancelbutton,
                                 QtWidgets.QDialogButtonBox.ActionRole)
        self.okbutton.clicked.connect(self.accept)
        self.cancelbutton.clicked.connect(self.reject)

        if style:
            raise RuntimeWarning("Dlg does not currently support the "
                                 "style kwarg.")
        self.size = size

        if haveQt == 'PyQt5':
            nScreens = len(qtapp.screens())
        else:
            nScreens = QtWidgets.QDesktopWidget().screenCount()
        self.screen = -1 if screen >= nScreens else screen
        # self.labelButtonOK = labelButtonOK
        # self.labelButtonCancel = labelButtonCancel

        self.layout = QtWidgets.QGridLayout()
        self.layout.setColumnStretch(1, 1)
        self.layout.setSpacing(10)
        self.layout.setColumnMinimumWidth(1, 250)

        self.setLayout(self.layout)

        self.setWindowTitle(title)


    def addText(self, text, color='', isFieldLabel=False):
        textLabel = QtWidgets.QLabel(text, parent=self)

        if len(color):
            palette = QtGui.QPalette()
            palette.setColor(QtGui.QPalette.Foreground, QtGui.QColor(color))
            textLabel.setPalette(palette)

        if isFieldLabel is True:
            self.layout.addWidget(textLabel, self.irow, 0, 1, 1)
        else:
            self.layout.addWidget(textLabel, self.irow, 0, 1, 2)
            self.irow += 1

        return textLabel

    def addField(self, label='', initial='', color='', choices=None, tip='',
                 enabled=True):
        """Adds a (labelled) input field to the dialogue box,
        optional text color and tooltip.

        If 'initial' is a bool, a checkbox will be created.
        If 'choices' is a list or tuple, a dropdown selector is created.
        Otherwise, a text line entry box is created.

        Returns a handle to the field (but not to the label).
        """
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
            self.data.append(initial)
            inputBox = QtWidgets.QCheckBox(parent=self)
            inputBox.setChecked(initial)

            def handleCheckboxChange(new_state):
                ix = self.inputFields.index(inputBox)
                self.data[ix] = inputBox.isChecked()
                msg = "handleCheckboxChange: inputFieldName={0}, checked={1}"
                logging.debug(msg.format(label, self.data[ix]))

            inputBox.stateChanged.connect(handleCheckboxChange)
        elif not choices:
            self.data.append(initial)
            inputBox = QtWidgets.QLineEdit(str(initial), parent=self)

            def handleLineEditChange(new_text):
                ix = self.inputFields.index(inputBox)
                name = self.inputFieldNames[ix]
                thisType = self.inputFieldTypes[name]

                try:
                    if thisType in (str, bytes):
                        self.data[ix] = str(new_text)
                    elif thisType == tuple:
                        jtext = "[" + str(new_text) + "]"
                        self.data[ix] = json.loads(jtext)[0]
                    elif thisType == list:
                        jtext = "[" + str(new_text) + "]"
                        self.data[ix] = json.loads(jtext)[0]
                    elif thisType == float:
                        self.data[ix] = float(new_text)
                    elif thisType == int:
                        self.data[ix] = int(new_text)
                    elif thisType == dict:
                        jtext = "[" + str(new_text) + "]"
                        self.data[ix] = json.loads(jtext)[0]
                    elif thisType == np.ndarray:
                        self.data[ix] = np.array(
                            json.loads("[" + str(new_text) + "]")[0])
                    else:
                        self.data[ix] = new_text
                        msg = ("Unknown type in handleLineEditChange: "
                               "inputFieldName={0}, type={1}, value={2}")
                        logging.warning(msg.format(label, thisType,
                                                   self.data[ix]))
                    msg = ("handleLineEditChange: inputFieldName={0}, "
                           "type={1}, value={2}")
                    logging.debug(msg.format(label, thisType, self.data[ix]))
                except Exception as e:
                    self.data[ix] = str(new_text)
                    msg = ('Error in handleLineEditChange: inputFieldName='
                           '{0}, type={1}, value={2}, error={3}')
                    logging.error(msg.format(label, thisType, self.data[ix],
                                             e))

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

            self.data.append(choices[initial])

            def handleCurrentIndexChanged(new_index):
                ix = self.inputFields.index(inputBox)
                try:
                    self.data[ix] = inputBox.itemData(new_index).toPyObject()[0]
                except AttributeError:
                    self.data[ix] = inputBox.itemData(new_index)[0]
                msg = ("handleCurrentIndexChanged: inputFieldName={0}, "
                       "selected={1}, type: {2}")
                logging.debug(msg.format(label, self.data[ix],
                                         type(self.data[ix])))

            inputBox.currentIndexChanged.connect(handleCurrentIndexChanged)

        if len(color):
            inputBox.setPalette(inputLabel.palette())
        if len(tip):
            inputBox.setToolTip(tip)
        inputBox.setEnabled(enabled)
        self.layout.addWidget(inputBox, self.irow, 1)

        self.inputFields.append(inputBox)  # store this to get data back on OK
        self.irow += 1

        return inputBox

    def addFixedField(self, label='', initial='', color='', choices=None,
                      tip=''):
        """Adds a field to the dialog box (like addField) but the field cannot
        be edited. e.g. Display experiment version.
        """
        return self.addField(label, initial, color, choices, tip,
                             enabled=False)

    def display(self):
        """Presents the dialog and waits for the user to press OK or CANCEL.

        If user presses OK button, function returns a list containing the
        updated values coming from each of the input fields created.
        Otherwise, None is returned.

        :return: self.data
        """
        return self.exec_()

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
            desktop = QtWidgets.QApplication.desktop()
            qtscreen = self.screen
            if self.screen <= 0:
                qtscreen = desktop.primaryScreen()
            centerPoint = desktop.screenGeometry(qtscreen).center()
            frameGm.moveCenter(centerPoint)
            self.move(frameGm.topLeft())
        else:
            self.move(self.pos[0],self.pos[1])
        QtWidgets.QDialog.show(self)
        self.raise_()
        self.activateWindow()
        if self.inputFields:
            self.inputFields[0].setFocus()

        self.OK = False
        if QtWidgets.QDialog.exec_(self) == QtWidgets.QDialog.Accepted:
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
                 labels=None, show=True,
                 sort_keys=None, copy_dict=None):

        # We allowed for snake_case parameters in previous releases. This needs
        # to end soon.
        if sort_keys:
            sortKeys = sort_keys
            logging.warning("Parameter 'sort_keys' is deprecated. "
                            "Use 'sortKeys' instead.")

        if copy_dict:
            copyDict = copy_dict
            logging.warning("Parameter 'copy_dict' is deprecated. "
                            "Use 'copyDict' instead.")
        
        # We don't explicitly check for None identity
        # for backward-compatibility reasons.
        if not fixed:
            fixed = []
        if not order:
            order = []
        if not labels:
            labels = dict()
        if not tip:
            tip = dict()

        Dlg.__init__(self, title, screen=screen)

        if copyDict:
            self.dictionary = dictionary.copy()
        else:
            self.dictionary = dictionary

        self._keys = list(self.dictionary.keys())
        self._labels = labels

        if order:
            self._keys = list(order) + list(set(self._keys).difference(set(order)))
        elif sortKeys:
            self._keys.sort()

        for field in self._keys:
            label = labels[field] if field in labels else field
            tooltip = ''
            if field in tip:
                tooltip = tip[field]
            if field in fixed:
                self.addFixedField(label, self.dictionary[field], tip=tooltip)
            elif type(self.dictionary[field]) in [list, tuple]:
                self.addField(label, choices=self.dictionary[field],
                              tip=tooltip)
            else:
                self.addField(label, self.dictionary[field], tip=tooltip)

        if show:
            self.show()

    def show(self):
        """Display the dialog.
        """
        ok_data = self.exec_()
        if ok_data:
            for n, thisKey in enumerate(self._keys):
                if thisKey in self._labels:
                    labelKey = self._labels[thisKey]
                else:
                    labelKey = thisKey
                try:
                    self.dictionary[thisKey] = self.inputFieldTypes[labelKey](self.data[n])
                except ValueError:
                    self.dictionary[thisKey] = self.data[n]


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

    info = {'Observer': 'jwp', 'GratingOri': 45,
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
