#!/usr/bin/env python
# -*- coding: utf-8 -*-

from psychopy.gui import setBackend
from psychopy.tests.test_gui.test_base import BaseDlgTest
import pytest


@pytest.mark.needs_wx
class TestQtDlg(BaseDlgTest):
    def setup_method(self):
        # set backend to PyQt
        setBackend("wxgui")
        # do base method setup
        self.base_setup_method()