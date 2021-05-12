#!/usr/bin/env python
# -*- coding: utf-8 -*-

# emacs: -*- mode: python-mode; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:

"""
py.test fixtures to create an instance of PsychoPyApp for testing
"""

import pytest
from packaging import version
from psychopy.app._psychopyApp import PsychoPyApp
from PIL import Image
Image.DEBUG = False

if version.parse(pytest.__version__) < version.parse('5'):
    class VersionError(Exception):
        pass
    raise VersionError("PsychoPy test suite requires pytest>=5.4")


# this method seems to work on at least Pytest 5.4+
@pytest.mark.needs_wx
@pytest.fixture(scope='session')
def get_app(request):

    # set_up
    PsychoPyApp._called_from_test = True  # NB class variable must be set
    _app = PsychoPyApp(testMode=True, showSplash=False)

    # yield, to let all tests within the scope run
    yield _app

    # teasr_down: then clear table at the end of the scope
    _app.quit()



if __name__ == '__main__':
    pytest.main()
