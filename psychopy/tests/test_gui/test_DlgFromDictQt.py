#!/usr/bin/env python
# -*- coding: utf-8 -*-

from builtins import object
from collections import OrderedDict
from psychopy.gui.qtgui import DlgFromDict
import pytest

@pytest.mark.usefixtures('pytest_namespace')
class TestDlgFromDictQt(object):
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
        assert dlg.windowTitle() == self.title

    def test_sort_keys_true(self):
        dlg = DlgFromDict(self.d, sort_keys=True, show=False)
        keys = list(self.d.copy().keys())
        keys.sort()
        assert keys == dlg._keys

    def test_sort_keys_false(self):
        dlg = DlgFromDict(self.d, sort_keys=False, show=False)
        keys = list(self.d.copy().keys())
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
        assert order != list(self.od.keys())

        dlg = DlgFromDict(self.od, order=order, show=False)
        assert dlg.inputFieldNames == order

    def test_order_tuple(self):
        order = ('exp_type', 'participant', 'handedness', 'exp_version')
        # Be certain we will actually request a different order
        # further down.
        assert list(order) != list(self.od.keys())

        dlg = DlgFromDict(self.od, order=order, show=False)
        assert dlg.inputFieldNames == list(order)

    def test_fixed(self):
        fixed = 'exp_version'
        dlg = DlgFromDict(self.d, fixed=fixed, show=False)
        field = dlg.inputFields[dlg.inputFieldNames.index(fixed)]
        assert field.isEnabled() is False

    def test_tooltips(self):
        tip = dict(participant='Tooltip')
        dlg = DlgFromDict(self.d, tip=tip, show=False)
        field = dlg.inputFields[dlg.inputFieldNames.index('participant')]
        assert field.toolTip() == tip['participant']

if __name__ == '__main__':
    import pytest
    pytest.main()
