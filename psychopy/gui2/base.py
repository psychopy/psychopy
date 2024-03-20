from psychopy.gui import util


class BaseDialog:
    """
    Base class for all psychopy.gui.Dialog classes. The methods described here are standard
    across Dialog classes, even though the backend will be completely different.
    """
    labels = {}
    ctrls = {}
    requiredFields = []
    currentRow = 0

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
        raise NotImplementedError()

    def display(self):
        raise NotImplementedError()

    @classmethod
    def fromDict(cls, dictionary, labels=None, tooltips=None):
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

        Returns
        -------
        psychopy.gui.Dialog
            Handle of the created Dialog object.
        """
        # create object
        dlg = cls()

        # convert to a list of params
        params = util.makeDisplayParams(
            dictionary,
            labels=labels,
            tooltips=tooltips,
        )
        # iterate through params
        for param in params:
            # add a field for each
            dlg.addField(**param)
        # show
        dlg.display()
