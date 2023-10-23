from psychopy import logging


class CounterbalancerFinishedError(BaseException):
    """
    Exception raised when a Counterbalancer is finished and its onFinished method is set to "raise"
    """
    pass


class Counterbalancer:
    """
    Tool for getting a group assignment from the Shelf, and keeping track of which previous participants were assigned
    to which groups.

    Parameters
    ----------
    shelf : psychopy.data.shelf.Shelf
        Which shelf to draw data from?
    entry : str
        Name of the Shelf entry to use.
    conditions : list[dict]
        List of dicts indicating, for each group:
        - Its name
        - Max number of participants
        - [optional] Additional arbitrary parameters
    onFinished : str or function
        What to do when the participants remaining for all groups is 0. If given a function, will call that function,
        but can also be given one of the following as strings:
        - "raise" - Raise a CounterbalancerFinishedError when finished
        - "reset" - Reset participant counters for each group back to their starting values
        - "ignore" - Do nothing, simply continue with values at 0 and self.finished as True
    autoLog : bool
        Whether to print to the log whenever an attribute of this object changes.
    """
    def __init__(
            self,
            shelf,
            entry,
            conditions,
            onFinished="ignore",
            autoLog=False):
        # store ref to shelf
        self.shelf = shelf
        # store entry name
        self.entry = entry
        # store conditions array
        self.conditions = conditions
        # placeholder values before querying shelf
        self.group = None
        self.params = {}
        # set behaviour on finished
        self.onFinished = onFinished
        # store autolog
        self.autoLog = autoLog

    @property
    def data(self):
        """
        Returns
        -------
        dict
            Full Shelf data associated with this Counterbalancer. Returns as a dict, not a handle, so changing the
            value of Counterbalancer.data won't change the value on the Shelf.
        """
        # make sure entry exists
        if self.entry not in self.shelf.data:
            self.shelf.data[self.entry] = {}
        # return entry
        return self.shelf.data[self.entry]

    @property
    def finished(self):
        """
        Returns
        -------
        bool
            True if all participant counters are at or below 0, False otherwise.
        """
        return all(val <= 0 for val in self.data.values())

    @property
    def remaining(self):
        """
        Returns
        -------
        int
            How many participants are left for the currently chosen group?
        """
        if self.group is not None:
            return self.data[self.group]

    def allocateGroup(self):
        """
        Retrieve a group allocation from the Shelf and decrement the participant counter for that group.

        Returns
        -------
        str
            Name of the chosen group.
        """
        # handle behaviour on finished
        if self.finished:
            # log warning regardless
            msg = f"All groups in shelf entry '{self.entry}' are now finished."
            logging.warning(msg)

            if callable(self.onFinished):
                # if given a callable for onFinished, call it when finished
                self.onFinished()
            elif self.onFinished == "raise":
                # if onFinished is raise, raise an error when finished
                raise CounterbalancerFinishedError(msg)
            elif self.onFinished == "reset":
                # if onFinished is restart, reset caps for all groups
                data = self.data.copy()
                for row in self.conditions:
                    data[row['group']] = row['cap']
                self.shelf.data[self.entry] = data
            else:
                # if onFinished is ignore, set group to None and params to blank
                self.group = None
                if len(self.conditions):
                    self.params = {key: None for key in self.conditions[0]}
                else:
                    self.params = {'group': None}

        # get group assignment from shelf
        self.group = self.shelf.counterBalanceSelect(
            key=self.entry,
            groups=[row['group'] for row in self.conditions],
            groupSizes=[row['cap'] for row in self.conditions],
        )[0]

        # get params from matching row of conditions array
        for row in self.conditions:
            if row['group'] == self.group:
                self.params = row.copy()
        # pop group and cap from params
        for key in ("group", "cap"):
            if key in self.params:
                del self.params[key]

        return self.group
