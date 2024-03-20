from psychopy.gui2.base import BaseDialog
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


class Dialog(QtWidgets.QDialog, BaseDialog):
    def __init__(
            self, title=_translate('PsychoPy Dialog'),
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
        self.scroller.setWidgetResizable(True)
        self.panel = QtWidgets.QWidget(self)
        self.scroller.setWidget(self.panel)
        self.border.addWidget(self.scroller, 1)
        # set maximum height from screen
        h = int(screenObj.size().height() * 0.8)
        self.setMaximumHeight(h)
        # setup ctrls sizer
        self.sizer = QtWidgets.QGridLayout()
        self.sizer.setSpacing(10)
        self.sizer.setColumnMinimumWidth(1, 250)
        self.panel.setLayout(self.sizer)

        # add okay and cancel buttons
        buttons = (
            QtWidgets.QDialogButtonBox.StandardButton.Ok |
            QtWidgets.QDialogButtonBox.StandardButton.Cancel
        )
        self.buttonBox = QtWidgets.QDialogButtonBox(buttons, parent=self)
        self.buttonBox.accepted.connect(self.accept)
        self.buttonBox.rejected.connect(self.reject)
        self.border.addWidget(self.buttonBox)

    def addTextField(self, name, value):
        ctrl = QtWidgets.QTextEdit(str(value), parent=self)
        self.sizer.addWidget(ctrl, self.currentRow, 1)
        self.resize(
            self.panel.sizeHint().width() + 12,
            self.panel.sizeHint().height()
        )

    def addLabel(self, key, label=None):
        # substitute label text for key if None
        if label is None:
            label = key
        # make label object
        lbl = QtWidgets.QLabel(label, parent=self.panel)
        # add to sizer
        self.sizer.addWidget(lbl, self.currentRow, 0)

        return lbl

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
            ctrl.setText(value)
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

    def setConfigField(self, key, config=True):
        pass

    def display(self):
        self.exec()
