#!/usr/bin/env python
# -*- coding: utf-8 -*-

# emacs: -*- mode: python-mode; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:

"""
py.test fixtures to create an instance of PsychoPyApp for testing
"""

import pytest
from pkg_resources import parse_version
import psychopy.app as app
from PIL import Image
Image.DEBUG = False

if parse_version(pytest.__version__) < parse_version('5'):
    class VersionError(Exception):
        pass
    raise VersionError("PsychoPy test suite requires pytest>=5.4")


# this method seems to work on at least Pytest 5.4+
@pytest.mark.needs_wx
@pytest.fixture(scope='session')
def get_app(request):

    # set_up
    app.startApp(showSplash=False, testMode=True)

    # yield, to let all tests within the scope run
    _app = app.getAppInstance()
    yield _app

    # teasr_down: then clear table at the end of the scope
    app.quitApp()



if __name__ == '__main__':
    pytest.main()
