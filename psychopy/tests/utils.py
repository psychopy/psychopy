import Image
from os.path import abspath, basename, dirname, isfile, join as pjoin
import os.path
import shutil
import numpy as np
from psychopy import logging

try:
    import pytest
    usePytest=True
except:
    import nose
    usePytest=False

if usePytest:
    from pytest import skip as _skip
else:
    logging.warning("pytest was not found. This is the recommended tool for testing in PsychoPy (rather than nose)")
    from nose.plugins.skip import SkipTest as _skip


# define the path where to find testing data
# so tests could be ran from any location
TESTS_PATH = abspath(dirname(__file__))
TESTS_DATA_PATH = pjoin(TESTS_PATH, 'data')
TESTS_FONT = pjoin(TESTS_DATA_PATH, 'DejaVuSerif.ttf')

def compareScreenshot(fileName, win, crit=5.0):
    """Compare the current back buffer of the given window with the file

    Screenshots are stored and compared against the files under path
    kept in TESTS_DATA_PATH.  Thus specify relative path to that
    directory
    """
    #if we start this from a folder below run.py the data folder won't be found
    fileName = pjoin(TESTS_DATA_PATH, fileName)
    #get the frame from the window
    win.getMovieFrame(buffer='back')
    frame=win.movieFrames[-1]
    win.movieFrames=[]
    #if the file exists run a test, if not save the file
    if not isfile(fileName):
        frame.save(fileName, optimize=1)
        skip("Created %s" % basename(fileName))
    else:
        expected = Image.open(fileName)
        expDat = np.array(expected.getdata())
        imgDat = np.array(frame.getdata())
        rms = (((imgDat-expDat)**2).sum()/len(imgDat))**0.5
        logging.warning('PsychoPyTests: RMS=%.3g at threshold=%3.g'
                  % (rms, crit))
        if rms>=crit:
            filenameLocal = fileName.replace('.png','_local.png')
            frame.save(filenameLocal, optimize=1)
            logging.warning('PsychoPyTests: Saving local copy into %s' % filenameLocal)
        assert rms<crit, \
            "RMS=%.3g at threshold=%.3g. Local copy in %s" % (rms, crit, filenameLocal)


def compareTextFiles(pathToActual, pathToCorrect):
    """Compare the text of two files, ignoring EOL differences, and save a copy if they differ
    """
    if not os.path.isfile(pathToCorrect):
        logging.warning('There was no comparison ("correct") file available, saving current file as the comparison:%s' %pathToCorrect)
        foundComparisonFile=False
        assert foundComparisonFile #deliberately raise an error to see the warning message
        return
    #we have the necessary file
    txtActual = open(pathToActual, 'r').read().replace('\r\n','\n')
    txtCorr = open(pathToCorrect, 'r').read().replace('\r\n','\n')
    if txtActual!=txtCorr:
        pathToLocal, ext = os.path.splitext(pathToCorrect)
        pathToLocal = pathToLocal+'_local'+ext
        shutil.copyfile(pathToActual,pathToLocal)
        logging.warning("txtActual!=txtCorr: Saving local copy to %s" %pathToLocal)
    assert txtActual==txtCorr, "txtActual!=txtCorr: Saving local copy to %s" %pathToLocal

def skip(msg=""):
    """Helper function to allow skipping of tests from either pytest or nose.
    Call this in test code rather than pytest.skip or nose SkipTest
    """
    if usePytest:
        _skip(msg)
    else:
        raise _skip(msg)