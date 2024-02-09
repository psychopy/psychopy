from psychopy import logging
from psychopy.tools.attributetools import attributeSetter


class CounterbalancerFinishedError(BaseException):
    """
    Exception raised when a Counterbalancer is finished and its onFinished method is set to "raise"
    """
    pass


class Counterbalancer:
    """
    Tool for getting a group assignment from the Shelf, and keeping track of which previous
    participants were assigned to which groups.

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
    nReps : int
        Number of (total) times the slots for each group need to be depleted for the shelf entry
        to be considered "finished". This sets the initial value for `reps` - each time the
        number of slots left for all groups reaches 0, if `reps` is more than 1, the slots are
        refilled and `reps` decreases by 1.
    autoLog : bool
        Whether to print to the log whenever an attribute of this object changes.
    """
    def __init__(
            self,
            shelf,
            entry,
            conditions,
            nReps=1,
            autoLog=False):
        # store autolog
        self.autoLog = autoLog
        # store ref to shelf
        self.shelf = shelf
        # store entry name
        self.entry = entry
        # store conditions array
        self.conditions = conditions
        # placeholder values before querying shelf
        self.group = None
        self.params = {}
        # store total nReps
        self.nReps = nReps
        # get remaining reps
        data = self.shelf.data.read()
        self.reps = data[self.entry].get("_reps", nReps)
        # update data for remaining in conditions
        self.updateRemaining()

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
            self.makeNewEntry()
        # filter out protected (_) entries
        data = {
            key: val
            for key, val in self.shelf.data[self.entry].items()
            if not str(key).startswith("_")
        }
        # return entry
        return data

    @attributeSetter
    def reps(self, value):
        """
        Set the number of repetitions remaining for this shelf entry. If reps > 0 when
        allocateGroups is called,

        Parameters
        ----------
        value : int
            Number of repetitions remaining
        """
        # make sure entry exists
        if self.entry not in self.shelf.data:
            self.makeNewEntry()
        # get entry
        entry = self.shelf.data[self.entry]
        # set value in entry
        entry['_reps'] = value
        # reapply entry to shelf
        self.shelf.data[self.entry] = entry
        # store value
        self.__dict__['reps'] = value

    def makeNewEntry(self):
        # create an entry with only reps
        self.shelf.data[self.entry] = {'_reps': self.nReps}
        # reset slots (to create groups)
        self.resetSlots()

    def resetSlots(self):
        # get entry
        entry = self.shelf.data[self.entry]
        # populate entry with groups and caps
        for row in self.conditions:
            entry[row['group']] = row['cap']
        # reapply entry to shelf
        self.shelf.data[self.entry] = entry

    @property
    def depleted(self):
        """
        Returns
        -------
        bool
            True if all participant counters are below 0, False otherwise.
        """
        return all(val <= 0 for val in self.data.values())

    @property
    def finished(self):
        """
        Returns
        -------
        bool
            True if all participant counters are at or below 0 and there are no repetitions left,
            False otherwise.
        """
        return self.depleted and self.reps <= 1

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

        if self.finished:
            # log warning
            msg = (f"All groups in shelf entry '{self.entry}' are now finished, with no "
                   f"repetitions remaining.")
            logging.warning(msg)

            # if onFinished is ignore, set group to None and params to blank
            self.group = None
            if len(self.conditions):
                self.params = {key: None for key in self.conditions[0]}
            else:
                self.params = {'group': None}

            return
        elif self.depleted:
            # if depleted but not finished, reset slots before choosing
            self.resetSlots()
            # decrement reps
            self.reps = self.reps - 1

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
        # update data for remaining in conditions
        self.updateRemaining()

        return self.group

    def updateRemaining(self):
        # get data just once
        data = self.data
        # store all remaining info in conditions array
        for row in self.conditions:
            row['remaining'] = data[str(row['group'])]
