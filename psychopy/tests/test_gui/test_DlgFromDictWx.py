#!/usr/bin/env python
# -*- coding: utf-8 -*-

from collections import OrderedDict
from psychopy.gui.wxgui import DlgFromDict


class TestDlgFromDictWx():
    def setup(self):
        self.d = dict(
            participant='000',
            handedness=['r', 'l'],
            exp_type=['foo', 'bar'],
            exp_version='2017-01-02')

        self.od = OrderedDict(
            [('participant', '000'),
             ('handedness', ['r', 'l']),
             ('exp_type', ['foo', 'bar']),
             ('exp_version', '2017-01-02')])

        self.title = 'Experiment'

    def test_title(self):
        dlg = DlgFromDict(self.d, title=self.title, show=False)
        assert dlg.Title == self.title

    def test_sort_keys_true(self):
        dlg = DlgFromDict(self.d, sort_keys=True, show=False)
        keys = self.d.copy().keys()
        keys.sort()
        assert keys == dlg._keys

    def test_sort_keys_false(self):
        dlg = DlgFromDict(self.d, sort_keys=False, show=False)
        keys = self.d.copy().keys()
        assert keys == dlg._keys

    def test_copy_dict_true(self):
        dlg = DlgFromDict(self.d, copy_dict=True, show=False)
        assert self.d is not dlg.dictionary

    def test_copy_dict_false(self):
        dlg = DlgFromDict(self.d, copy_dict=False, show=False)
        assert self.d is dlg.dictionary

    def test_order_list(self):
        order = ['exp_type', 'participant', 'handedness', 'exp_version']
        # Be certain we will actually request a different order
        # further down.
        assert order != self.od.keys()

        dlg = DlgFromDict(self.od, order=order, show=False)
        assert dlg.inputFieldNames == order

    def test_order_tuple(self):
        order = ('exp_type', 'participant', 'handedness', 'exp_version')
        # Be certain we will actually request a different order
        # further down.
        assert list(order) != self.od.keys()

        dlg = DlgFromDict(self.od, order=order, show=False)
        assert dlg.inputFieldNames == list(order)


if __name__ == '__main__':
    import pytest
    pytest.main()
