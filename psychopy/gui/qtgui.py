from psychopy.gui.base import BaseDlg
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
        # set a nice looking minimum size
        self.setMinimumSize(384, 128)
        # resize if size given
        if size is not None:
            # make sure size is an array of 2
            if isinstance(size, (int, float)):
                size = [int(size)] * 2
            # do resize
            self.resize(*size)
        # reposition if pos given
        if pos is not None:
            # make sure pos is an array of 2
            if isinstance(pos, (int, float)):
                pos = [int(pos)] * 2
            self.move(*pos)
        # setup ctrls sizer
        self.sizer = QtWidgets.QGridLayout()
        self.sizer.setSpacing(10)
        self.sizer.setColumnMinimumWidth(1, 250)
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
        elif isinstance(value, bool):
            # make a checkbox if value is a bool
            ctrl = QtWidgets.QCheckBox(self.panel)
            # set start value
            ctrl.setChecked(value)
        else:
            # otherwise, make a text ctrl
            ctrl = QtWidgets.QLineEdit(self.panel)
            # set start value
            ctrl.setText(str(value))
        # add to sizer
        self.sizer.addWidget(ctrl, self.currentRow, 1)

        return lbl, ctrl

    def showField(self, key, show=True):
        # show/hide label
        self.labels[key].setVisible(show)
        # show/hide ctrl
        self.ctrls[key].setVisible(show)

    def enableField(self, key, enable=True):
        # enable/disable ctrl
        self.ctrls[key].setEnabled(enable)

    def display(self):
        self.exec()
