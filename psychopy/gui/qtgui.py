from pathlib import Path

from psychopy.gui.base import BaseDlg, BaseMessageDialog
from psychopy.localization import _translate
# import the newest version of PyQt available
try:
    from PyQt6 import QtWidgets
    from PyQt6 import QtGui
    from PyQt6.QtCore import Qt
except ModuleNotFoundError:
    from PyQt5 import QtWidgets
    from PyQt5 import QtGui
    from PyQt5.QtCore import Qt


qtapp = QtWidgets.QApplication.instance()
if qtapp is None:
    qtapp = QtWidgets.QApplication([])
    qtapp.setStyle('Fusion')


class Dlg(QtWidgets.QDialog, BaseDlg):
    class ReadmoreCtrl(QtWidgets.QLabel, BaseDlg.BaseReadmoreCtrl):
        """
        A linked label which shows/hides a set of control on click.
        """

        def __init__(self, parent, dlg, label=""):
            QtWidgets.QLabel.__init__(self, parent)
            # store reference to dialog
            self.dlg = dlg
            # set initial label
            self.setLabel(label)
            # bind onclick
            self.setOpenExternalLinks(False)
            self.linkActivated.connect(self.onToggle)

        def setLabel(self, label, state=None):
            """
            Set the label of this ctrl (not including the arrow).

            Parameters
            ----------
            label : str
                The label itself, without any arrow
            state : bool
                What state to append an arrow for, use None to simply use the current state
            """
            # if not given a state, use current state
            if state is None:
                state = self.state
            # store label root
            self.label = label
            # get label with arrow
            label = self.getLabelWithArrow(label, state=state)
            # construct text to set
            text = f"<a href='.' style='color: black; text-decoration: none;'>{label}</a>"
            # set label text
            self.setText(text)

    def __init__(
            self, title=_translate('PsychoPy Dialog'),
            pos=None, size=None,
            screen=-1, alwaysOnTop=False
    ):
        QtWidgets.QDialog.__init__(self, None)
        # put on requested screen
        screenObj = qtapp.screens()[screen]
        self.setScreen(screenObj)
        # set title
        self.setWindowTitle(title)
        # set always stay on top
        if alwaysOnTop:
            self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint)
        # setup layout
        self.border = QtWidgets.QVBoxLayout()
        self.border.setSpacing(6)
        self.setLayout(self.border)
        # add label
        self.requiredMsg = QtWidgets.QLabel(
            text=_translate("Fields marked with an asterisk (*) are required."),
            parent=self
        )
        self.border.addWidget(self.requiredMsg)
        # setup ctrls panel
        self.scroller = QtWidgets.QScrollArea(self)
        self.scroller.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroller.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.scroller.setFrameStyle(QtWidgets.QFrame.Shape.NoFrame)
        self.scroller.setWidgetResizable(True)
        self.panel = QtWidgets.QWidget(self)
        self.scroller.setWidget(self.panel)
        self.border.addWidget(self.scroller, 1)
        # set maximum size from screen
        w = int(screenObj.size().width() * 0.8)
        h = int(screenObj.size().height() * 0.8)
        self.setMaximumSize(w, h)
        # resize if size given
        if size is not None:
            # make sure size is an array of 2
            if isinstance(size, (int, float)):
                size = [int(size)] * 2
            # set minimum size
            self.setMinimumSize(*size)
        else:
            # if no size given, use a nice minimum size
            self.setMinimumSize(384, 128)
        # reposition if pos given
        if pos is not None:
            # make sure pos is an array of 2
            if isinstance(pos, (int, float)):
                pos = [int(pos)] * 2
            self.move(*pos)
        # setup ctrls sizer
        self.sizer = QtWidgets.QGridLayout()
        self.sizer.setSpacing(6)
        self.panel.setLayout(self.sizer)
        # make readmorectrl (starts off hidden)
        self.readmoreCtrl = self.ReadmoreCtrl(
            self.panel, dlg=self, label=_translate("Configuration fields...")
        )
        self.readmoreCtrl.setVisible(False)

        # add okay and cancel buttons
        buttons = (
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonBox = QtWidgets.QDialogButtonBox(buttons, parent=self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.border.addWidget(self.buttonBox)

    def addLabel(self, key, label=None):
        # substitute label text for key if None
        if label is None:
            label = key
        # make label object
        lbl = QtWidgets.QLabel(label, parent=self.panel)
        # add to sizer
        self.sizer.addWidget(lbl, self.currentRow, 0)

        return lbl

    def insertReadmoreCtrl(self, row=None):
        # if row is None, use current row
        if row is None:
            row = self.currentRow
        # show readmore
        self.readmoreCtrl.setVisible(True)
        # add it to the sizer
        self.sizer.addWidget(self.readmoreCtrl, row, 0, 1, -1)
        # iterate row to account for the new item
        self.currentRow += 1

    def makeField(self, key, value="", label=None, tip="", index=-1):
        # make a label
        lbl = self.addLabel(key, label=label)
        # make ctrl
        if isinstance(value, (list, tuple)):
            # make a choice ctrl if value is a list
            ctrl = QtWidgets.QComboBox(self.panel)
            # set choices
            ctrl.addItems(value)
            # bind validation
            ctrl.currentTextChanged.connect(self.validate)
        elif isinstance(value, bool):
            # make a checkbox if value is a bool
            ctrl = QtWidgets.QCheckBox(self.panel)
            # set start value
            ctrl.setChecked(value)
            # bind validation
            ctrl.stateChanged.connect(self.validate)
        else:
            # otherwise, make a text ctrl
            ctrl = QtWidgets.QLineEdit(self.panel)
            # set start value
            ctrl.setText(str(value))
            # bind validation
            ctrl.textChanged.connect(self.validate)
        # add to sizer
        self.sizer.addWidget(ctrl, self.currentRow, 1)

        return lbl, ctrl

    def getRawFieldValue(self, key):
        # get ctrl
        ctrl = self.ctrls[key]
        # get value according to ctrl type
        if isinstance(ctrl, QtWidgets.QComboBox):
            return ctrl.currentText()
        elif isinstance(ctrl, QtWidgets.QCheckBox):
            return bool(ctrl.checkState().value)
        elif isinstance(ctrl, QtWidgets.QLineEdit):
            return ctrl.text()

    def showField(self, key, show=True):
        # show/hide label
        self.labels[key].setVisible(show)
        # show/hide ctrl
        self.ctrls[key].setVisible(show)

    def enableField(self, key, enable=True):
        # enable/disable ctrl
        self.ctrls[key].setEnabled(enable)

    def enableOK(self, enable=True):
        # get OK button
        btn = self.buttonBox.button(QtWidgets.QDialogButtonBox.StandardButton.Ok)
        # set enabled state
        btn.setEnabled(enable)

    def display(self):
        return self.exec()


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

    fdir = str(Path(initFilePath) / initFileName)
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

    if allowed is None:
        allowed = ("All files (*.*);;"
                   "PsychoPy Data (*.psydat);;"
                   "txt (*.txt *.dlm *.csv);;"
                   "pickled files (*.pickle *.pkl);;"
                   "shelved files (*.shelf)")
    fdir = str(Path(tryFilePath) / tryFileName)
    filesToOpen = QtWidgets.QFileDialog.getOpenFileNames(parent=None,
                                                         caption=prompt,
                                                         directory=fdir,
                                                         filter=allowed)
    if type(filesToOpen) == tuple:  # some versions(?) of PyQt return (files, filter)
        filesToOpen = filesToOpen[0]

    filesToOpen = [str(fpath) for fpath in filesToOpen
                   if Path(fpath).exists()]
    if len(filesToOpen) == 0:
        return None
    return filesToOpen


class MessageDlg(QtWidgets.QMessageBox, BaseMessageDialog):
    # array to store icons against levels
    icons = {
        'info': QtWidgets.QMessageBox.Icon.Information,
        'warn': QtWidgets.QMessageBox.Icon.Warning,
        'critical': QtWidgets.QMessageBox.Icon.Critical,
        'about': QtWidgets.QMessageBox.Icon.Information,
    }

    def __init__(
            self, title="", prompt=None, level="info"
    ):
        # check the level descriptor is okay
        assert level in self.icons, _translate(
            "{} is not a known level of MessageDlg, should be one of: {}"
        ).format(level, list(self.icons))
        # substitute null prompt
        if prompt is None:
            prompt = self.nullPrompt
        # make dialog
        QtWidgets.QMessageBox.__init__(
            self, None, title=title, text=prompt, icon=self.icons[level]
        )

    def display(self):
        return self.exec()
