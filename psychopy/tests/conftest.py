#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from psychopy.app._psychopyApp import PsychoPyApp

# def pytest_configure():
#     pytest.app = PsychoPyApp(testMode=True, showSplash=False)

@pytest.fixture(scope="session")
def getApp():
    app = PsychoPyApp(testMode=True, showSplash=False)
    yield app
    app.quit()
