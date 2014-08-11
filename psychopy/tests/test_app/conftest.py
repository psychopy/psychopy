# emacs: -*- mode: python-mode; py-indent-offset: 4; tab-width: 4; indent-tabs-mode: nil -*-
# ex: set sts=4 ts=4 sw=4 noet:

"""
py.test fixtures to create an instance of PsychoPyApp for testing
"""
from psychopy.app import psychopyApp

def pytest_configure(config):
    #print "D: CREATING APP"
    psychopyApp._called_from_test = True
    psychopyApp._app = psychopyApp.PsychoPyApp(testMode=True, showSplash=False)
    #print "D: CREATED APP"
    #del PsychoPyApp._called_from_test

def pytest_unconfigure(config):
    print "D: KILLING THE APP"
    psychopyApp._app.quit() # this currently uses sys.exit() which ends testing :-(
    #
    #print "D: SHUTTING DOWN APP"
    pass
