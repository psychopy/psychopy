#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from psychopy.app._psychopyApp import PsychoPyApp

@pytest.fixture(scope="session", autouse=True)
def pytest_namespace():
    app = PsychoPyApp(testMode=True, showSplash=False)
    return {'app': app}

@pytest.mark.usefixtures('pytest_namespace')
def pytest_sessionfinish(session, exitstatus):
    pytest.app.quit()
