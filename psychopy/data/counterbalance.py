class Counterbalancer:
    def __init__(self, shelf, entry, conditions, autoLog=False):
        # store ref to shelf
        self.shelf = shelf
        # store entry name
        self.entry = entry
        # store conditions array
        self.conditions = conditions
        # placeholder values before querying shelf
        self.group = self.params = None
        # store autolog
        self.autoLog = autoLog

    @property
    def data(self):
        return self.shelf.data[self.entry]

    @property
    def finished(self):
        return all(val <= 0 for val in self.data.values())

    def allocateGroup(self):
        # get group assignment from shelf
        self.group = self.shelf.counterBalanceSelect(
            key=self.entry,
            groups=[row['group'] for row in self.conditions],
            groupSizes=[row['cap'] for row in self.conditions],
            groupWeights=[row['probability'] for row in self.conditions]
        )[0]
        # get params from matching row of conditions array
        for row in self.conditions:
            if row['group'] == self.group:
                self.params = row

        return self.group
