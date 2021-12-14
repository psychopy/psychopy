class SortTerm:
    def __init__(self, value,
                 aLabel=None, dLabel=None,
                 ascending=False):
        # Substitute labels
        if aLabel is None:
            aLabel = value
        if dLabel is None:
            dLabel = value
        # Store details
        self.value = value
        self.ascending = ascending
        self._aLabel = aLabel
        self._dLabel = dLabel

    @property
    def label(self):
        if self.ascending:
            return self._aLabel
        else:
            return self._dLabel

    def __str__(self):
        if self.ascending:
            return self.value + "+"
        else:
            return self.value + "-"

    def __eq__(self, other):
        if not isinstance(other, self.__class__):
            return False
        return self.value == other.value