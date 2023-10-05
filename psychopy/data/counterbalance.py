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

    def allocateGroup(self):
        # get group assignment from shelf
        self.group = self.shelf.counterBalanceSelect(
            key=self.entry,
            groups=[row['group'] for row in self.conditions],
            groupSizes=[row['cap'] for row in self.conditions],
        )
        # get params from matching row of conditions array
        for row in self.conditions:
            if row['group'] == self.group:
                self.params = row

        return self.group
