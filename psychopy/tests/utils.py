import Image
import nose
import os
import numpy as np
import OpenGL

def compareScreenshot(fileName, win, crit=5.0):
    """Compare the current back buffer of the given window with the file 
    """
    #if we start this from a folder below run.py the data folder won't be found 
    if not os.path.isdir(os.path.split(fileName)[0]):
        fileName = os.path.join('..',fileName)
    #if the file exists run a test, if not save the file 
    if not os.path.isfile(fileName):
        saveImage=True
    else:saveImage=False
    #get the frame from the window
    win.getMovieFrame(buffer='back')
    frame=win.movieFrames[-1]
    win.movieFrames=[]
    if saveImage:
        frame.save(fileName, optimize=1)
        raise nose.plugins.skip.SkipTest, "Created %s" % os.path.basename(fileName)
    else:
        expected=Image.open(fileName)
        expDat = np.array(expected.getdata())
        imgDat = np.array(frame.getdata())
        rms = (((imgDat-expDat)**2).sum()/len(imgDat))**0.5
        print 'RMS:', rms
        if rms>=crit:
            filenameLocal = fileName.replace('.png','_local.png')
            frame.save(filenameLocal, optimize=1)
            print "** Saved copy of actual frame to %s **" %filenameLocal
        assert rms<crit
        