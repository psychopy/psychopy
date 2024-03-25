from psychopy.gui.base import BaseDlg, BaseMessageDialog
from psychopy.localization import _translate
from pathlib import Path
import wx, wx.lib.scrolledpanel


wxapp = wx.GetApp()
if wxapp is None:
    wxapp = wx.App()


class Dlg(wx.Dialog, BaseDlg):
    class ReadmoreCtrl(wx.Button, BaseDlg.BaseReadmoreCtrl):
        """
        A linked label which shows/hides a set of control on click.
        """

        def __init__(self, parent, dlg, label=""):
            wx.Button.__init__(
                self, parent, style=wx.BORDER_NONE | wx.BU_EXACTFIT | wx.BG_STYLE_TRANSPARENT
            )
            # store reference to dialog
            self.dlg = dlg
            # set initial label
            self.setLabel(label)
            # bind onclick
            self.Bind(wx.EVT_BUTTON, self.onToggle)

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
            text = self.getLabelWithArrow(label, state=state)
            # set label text
            self.SetLabel(text)

    def __init__(
            self, title=_translate('PsychoPy Dialog'),
            pos=None, size=None,
            screen=-1, alwaysOnTop=False
    ):
        wx.Dialog.__init__(self, None, style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER)
        # todo: wx doesn't seem to have a built in method to set screen, can we hack it?
        # set title
        self.SetTitle(title)
        # set always stay on top
        if alwaysOnTop:
            self.SetWindowStyle(wx.STAY_ON_TOP)
        # setup layout
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        # add label
        self.requiredMsg = wx.StaticText(
            self,
            label=_translate("Fields marked with an asterisk (*) are required.")
        )
        self.border.Add(self.requiredMsg, border=6, flag=wx.ALL | wx.EXPAND)
        # setup ctrls panel
        self.panel = wx.lib.scrolledpanel.ScrolledPanel(self)
        self.border.Add(self.panel, proportion=1, border=6, flag=wx.ALL | wx.EXPAND)
        # set maximum size from screen
        w = int(wx.GetDisplaySize()[0] * 0.8)
        h = int(wx.GetDisplaySize()[1] * 0.8)
        self.SetMaxSize(wx.Size(w, h))
        # resize if size given
        if size is not None:
            # make sure size is an array of 2
            if isinstance(size, (int, float)):
                size = [int(size)] * 2
            # set minimum size
            self.SetMinSize(*size)
        else:
            # if no size given, use a nice minimum size
            self.SetMinSize(wx.Size(384, 128))
        # reposition if pos given
        if pos is not None:
            # make sure pos is an array of 2
            if isinstance(pos, (int, float)):
                pos = [int(pos)] * 2
            self.SetPosition(*pos)
        else:
            self.Center()
        # setup ctrls sizer
        self.sizer = wx.GridBagSizer(vgap=3, hgap=6)
        self.sizer.SetEmptyCellSize((0, 0))
        self.panel.SetSizer(self.sizer)
        # make readmorectrl (starts off hidden)
        self.readmoreCtrl = self.ReadmoreCtrl(
            self.panel, dlg=self, label=_translate("Configuration fields...")
        )
        self.readmoreCtrl.Show(False)

        # add okay and cancel buttons
        buttons = wx.OK | wx.CANCEL
        self.buttonBox = self.CreateStdDialogButtonSizer(flags=buttons)
        self.border.Add(self.buttonBox, border=6, flag=wx.ALIGN_RIGHT | wx.ALL)

    def addLabel(self, key, label=None):
        # substitute label text for key if None
        if label is None:
            label = key
        # make label object
        lbl = wx.StaticText(self.panel, label=label)
        # add to sizer
        self.sizer.Add(lbl, pos=(self.currentRow, 0), flag=wx.ALIGN_CENTER_VERTICAL | wx.ALL)

        return lbl

    def insertReadmoreCtrl(self, row=None):
        # if row is None, use current row
        if row is None:
            row = self.currentRow
        # show readmore
        self.readmoreCtrl.Show(True)
        # add it to the sizer
        self.sizer.Add(
            self.readmoreCtrl, pos=(row, 0), span=(1, 2), flag=wx.EXPAND | wx.ALL
        )
        # iterate row to account for the new item
        self.currentRow += 1

    def makeField(self, key, value="", label=None, tip="", index=-1):
        # make a label
        lbl = self.addLabel(key, label=label)
        # make ctrl
        if isinstance(value, (list, tuple)):
            # make a choice ctrl if value is a list
            ctrl = wx.Choice(self.panel, choices=value)
            # bind to validator
            ctrl.Bind(wx.EVT_CHOICE, self.validate)
        elif isinstance(value, bool):
            # make a checkbox if value is a bool
            ctrl = wx.CheckBox(self.panel)
            ctrl.SetValue(value)
            # bind to validator
            ctrl.Bind(wx.EVT_CHECKBOX, self.validate)
        else:
            # otherwise, make a text ctrl
            ctrl = wx.TextCtrl(self.panel, value=str(value))
            # bind to validator
            ctrl.Bind(wx.EVT_TEXT, self.validate)
        # add to sizer
        self.sizer.Add(
            ctrl, pos=(self.currentRow, 1), border=6, flag=wx.EXPAND | wx.ALL
        )
        # if this is the first field, set growable on the ctrl column
        if self.currentRow == 1:
            self.sizer.AddGrowableCol(1, proportion=1)
        # update layout
        self.Layout()
        self.Fit()
        # figure out virtual size
        vsize = self.panel.GetBestVirtualSize()
        # if virtual size is greater than actual size, setup scrolling
        if self.GetSize()[1] < vsize[1]:
            self.SetSize(vsize)
            self.panel.SetupScrolling(scroll_x=False)

        return lbl, ctrl

    def getFieldValue(self, key):
        # get ctrl
        ctrl = self.ctrls[key]
        # get value according to ctrl type
        if isinstance(ctrl, wx.Choice):
            return ctrl.GetStringSelection()
        elif isinstance(ctrl, (wx.TextCtrl, wx.CheckBox)):
            return ctrl.GetValue()

    def showField(self, key, show=True):
        # show/hide label
        self.labels[key].Show(show)
        # show/hide ctrl
        self.ctrls[key].Show(show)
        # update layout
        self.Layout()

    def enableField(self, key, enable=True):
        # enable/disable ctrl
        self.ctrls[key].Enable(enable)

    def enableOK(self, enable=True):
        # get OK button
        btn = self.FindWindowById(wx.ID_OK)
        # set enabled state
        btn.Enable(enable=enable)

    def display(self):
        return self.ShowModal()


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
    app = wxapp
    dlg = wx.FileDialog(None, prompt, initFilePath,
                        initFileName, allowed, wx.FD_SAVE)
    if dlg.ShowModal() == wx.ID_OK:
        # get names of images and their directory
        outName = dlg.GetFilename()
        outPath = dlg.GetDirectory()
        dlg.Destroy()
        # tmpApp.Destroy()  # this causes an error message for some reason
        fullPath = Path(outPath) / outName
    else:
        fullPath = ""
    return str(fullPath)


def fileOpenDlg(tryFilePath="",
                tryFileName="",
                prompt=_translate("Select file(s) to open"),
                allowed=None):
    """
    A simple dialogue allowing read access to the file system.

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
    app = wxapp
    dlg = wx.FileDialog(None, prompt, tryFilePath, tryFileName, allowed,
                        wx.FD_OPEN | wx.FD_FILE_MUST_EXIST | wx.FD_MULTIPLE)
    if dlg.ShowModal() == wx.ID_OK:
        # get names of images and their directory
        fullPaths = dlg.GetPaths()
    else:
        fullPaths = None
    dlg.Destroy()
    return fullPaths


class MessageDlg(wx.MessageDialog, BaseMessageDialog):
    # array to store icons against levels
    icons = {
        'info': wx.ICON_INFORMATION,
        'warn': wx.ICON_WARNING,
        'critical': wx.ICON_ERROR,
        'about': wx.ICON_INFORMATION,
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
        wx.MessageDialog.__init__(
            self, None,  prompt, caption=title, style=self.icons[level]
        )

    def display(self):
        return self.ShowModal()
