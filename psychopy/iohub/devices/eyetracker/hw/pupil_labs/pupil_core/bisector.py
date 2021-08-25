# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import numpy as np


class DatumNotFoundError(ValueError):
    pass


class ImmutableBisector:
    """Stores data with associated timestamps, both sorted by the timestamp."""

    def __init__(self, data=(), time=()):
        if len(data) != len(time):
            raise ValueError(
                "Each element in `data` requires a corresponding timestamp in `time`"
            )
        elif not len(data):
            self._data = np.array([], dtype=object)
            self._time = np.array([])
        else:
            self._data = np.asarray(data, dtype=object)
            self._time = np.asarray(time)

            # Find correct order once and reorder both lists in-place
            sorted_indices = np.argsort(self._time)
            self._data = self._data[sorted_indices]
            self._time = self._time[sorted_indices]

    @property
    def timestamps(self):
        return self._time

    def copy(self):
        new_instance = type(self)()
        new_instance._data = self._data.copy()
        new_instance._time = self._time.copy()
        return new_instance

    def find_datum_by_timestamp(self, timestamp):
        """
        :param timestamp: timestamp to extract.
        :return: datum that is matching
        :raises: ValueError if no matching datum is found
        """
        found_index = np.searchsorted(self._time, timestamp)
        try:
            d, t = self[found_index]
        except IndexError:
            raise DatumNotFoundError

        if t == timestamp:
            return d
        else:
            raise DatumNotFoundError

    def __getitem__(self, key):
        return self._data[key], self._time[key]

    def __len__(self):
        assert len(self._data) == len(self._time)
        return len(self._data)

    def __iter__(self):
        return iter(zip(self._data, self._time))

    def __bool__(self):
        return bool(len(self._data))


class MutableBisector(ImmutableBisector):
    def insert(self, datum, timestamp):
        insert_index = np.searchsorted(self._time, timestamp)
        self._data = np.insert(self._data, insert_index, datum)
        self._time = np.insert(self._time, insert_index, timestamp)

    def delete(self, index):
        self._data = np.delete(self._data, index)
        self._time = np.delete(self._time, index)
