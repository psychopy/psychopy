from psychopy.gui import util
from psychopy.localization import _translate


class BaseDlg:
    """
    Base class for all psychopy.gui.Dialog classes. The methods described here are standard
    across Dialog classes, even though the backend will be completely different.
    """

    class BaseReadmoreCtrl:
        # current state of the ctrl - True = showing, False = hiding
        state = False
        # label for the ctrl, not including the arrow
        label = ""
        # list of fields connected to this ReadmoreCtrl
        linkedFields = []
        # Dlg object which this readme ctrl is connected to
        dlg = None

        @staticmethod
        def getLabelWithArrow(label, state=None):
            """
            Get specified label with an arrow matching the specified state.

            Parameters
            ----------
            label : str
                The label itself, without any arrow
            state : bool
                What state to append an arrow for
            """
            # choose an arrow according to state
            if state:
                arrow = "▾"
            else:
                arrow = "▸"

            return arrow + " " + label

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
            raise NotImplementedError()

        def onToggle(self, evt=None):
            """
            Toggle visibility of linked ctrls. Called on press.
            """
            # toggle state
            self.state = not self.state
            # update label
            self.setLabel(self.label, state=self.state)
            # show/hide ctrls
            self.showCtrls(self.state)

        def linkField(self, key):
            """
            Connect a field to this ReadmoreCtrl such that it's shown/hidden on toggle.
            """
            # add to array of linked ctrls
            if key not in self.linkedFields:
                self.linkedFields.append(key)

        def unlinkField(self, key):
            """
            Disconnect a field from this ReadmoreCtrl such that it's not longer shown/hidden on
            toggle.
            """
            # add to array of linked ctrls
            if key in self.linkedFields:
                self.linkedFields.remove(key)

        def showCtrls(self, show=True):
            """
            Show or hide the linked ctrls for this ReadmoreCtrl

            Parameters
            ----------
            show : bool
                Whether to show (True) or hide (False) linked ctrls.
            """
            for key in self.linkedFields:
                self.dlg.showField(key, show=show)

    labels = {}
    ctrls = {}
    requiredFields = []
    currentRow = 0
    # this should be overwritten in __init__ as a subclass of BaseReadmoreCtrl
    readmoreCtrl = None

    def addField(
            self, key, label=None, tip="", value="", flags=None, index=-1
    ):
        # if not given a label, use key
        if label is None:
            label = key
        # if no flags, use empty list
        if flags is None:
            flags = []

        # make ctrl
        self.labels[key], self.ctrls[key] = self.makeField(
            key, value=value, label=label, tip=tip, index=index
        )
        # show/hide field
        self.showField(key, "hid" not in flags)
        # enable/disable field
        self.enableField(key, "fix" not in flags)
        # set field as required
        self.setRequiredField(key, "req" in flags)
        # set field as config
        self.setConfigField(key, "cfg" in flags)

        # iterate row
        self.currentRow += 1

    def makeField(self, key, value="", label=None, tip="", index=-1):
        raise NotImplementedError()

    def showField(self, key, show=True):
        raise NotImplementedError()

    def enableField(self, key, enable=True):
        raise NotImplementedError()

    def setRequiredField(self, key, required=True):
        if required:
            # if required, add to required fields
            if key not in self.requiredFields:
                self.requiredFields.append(key)
        else:
            # if not required, remove from required fields
            if key in self.requiredFields:
                self.requiredFields.remove(key)

    def setConfigField(self, key, config=True):
        if config:
            # if config, add to config fields
            self.readmoreCtrl.linkField(key)
            # show/hide according to readmore toggle state
            self.showField(key, show=self.readmoreCtrl.state)
        else:
            # if not config, remove from config fields
            self.readmoreCtrl.unlinkField(key)

    def insertReadmoreCtrl(self, row=None):
        raise NotImplementedError()

    def display(self):
        raise NotImplementedError()

    @classmethod
    def fromDict(
            cls, dictionary, labels=None, tooltips=None,
            title=_translate('PsychoPy Dialog'),
            pos=None, size=None,
            screen=-1, alwaysOnTop=False
    ):
        """
        Create a new psychopy.gui.Dialog object from a dictionary.

        Parameters
        ----------
        dictionary : dict
            Dict with necessary information to create this dialog
        labels : dict
            Labels to use, against their corresponding keys
        tooltips : dict
            Tooltips to use, against their corresponding keys
        title : str
            Title to use on the title bar of the dialog
        pos : tuple[int{2}] or list[int{2}]
            Where on screen to position the dialog, use None to center
        size : tuple[int{2}] or list[int{2}]
            How big should the dialog start off as, use None to fit content
        screen : int
            Which screen to display the dialog on, use -1 for main display
        alwaysOnTop : bool
            If True, dialog will stay on top of all other windows

        Returns
        -------
        psychopy.gui.Dialog
            Handle of the created Dialog object.
        """
        # create object
        dlg = cls(
            title=title,
            pos=pos, size=size,
            screen=screen, alwaysOnTop=alwaysOnTop
        )

        # convert to a list of params
        params = util.makeDisplayParams(
            dictionary,
            labels=labels,
            tooltips=tooltips,
        )
        # iterate through params
        for param in params:
            if isinstance(param, dict):
                # add a field for each param
                dlg.addField(**param)
            elif param == "---":
                # if param is ---, make the readmore ctrl here
                dlg.insertReadmoreCtrl()
        # show
        dlg.display()


class BaseMessageDialog:
    # message to display if there's no prompt
    nullPrompt = _translate("No details provided. ('prompt' value not set).")
    # array to store icons against levels (should be overloaded by subclasses)
    icons = {
        'info': None,
        'warn': None,
        'critical': None,
        'about': None,
    }

    def display(self):
        raise NotImplementedError()

    @classmethod
    def info(cls, title=_translate("Information"), prompt=None):
        # make dlg
        dlg = cls(title=title, prompt=prompt, level="info")

        return dlg.display()

    @classmethod
    def warn(cls, title=_translate("Warning"), prompt=None):
        # make dlg
        dlg = cls(title=title, prompt=prompt, level="warn")

        return dlg.display()

    @classmethod
    def critical(cls, title=_translate("Critical"), prompt=None):
        # make dlg
        dlg = cls(title=title, prompt=prompt, level="critical")

        return dlg.display()

    @classmethod
    def about(cls, title=_translate("About Experiment"), prompt=None):
        # make dlg
        dlg = cls(title=title, prompt=prompt, level="about")

        return dlg.display()
