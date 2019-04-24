#!/usr/bin/env python
# -*- coding: utf-8 -*-

# emacs: -*- mode: python-mode; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:

"""
py.test fixtures to create an instance of PsychoPyApp for testing
"""

from __future__ import print_function
import pytest

from psychopy.app import psychopyApp
from psychopy.app._psychopyApp import PsychoPyApp
from PIL import Image
Image.DEBUG = False

# def pytest_configure():
#     psychopyApp._called_from_test = True
#     psychopyApp._app = PsychoPyApp(testMode=True, showSplash=False)
#     # then use from psychopy import psychopyApp` to access _app
#
# def pytest_unconfigure():
#     with pytest.raises(SystemExit):
#         psychopyApp._app.quit()


if __name__ == '__main__':
    pytest.main()
