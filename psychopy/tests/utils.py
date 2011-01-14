import Image
import nose
import os
import numpy as np
import OpenGL

def compareScreenshot(fileName, win, crit=0.1):
    """Compare the current front buffer of the given window with the file 
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
    else:
        expected=Image.open(fileName)
        expDat = np.array(expected.getdata())
        imgDat = np.array(frame.getdata())
        rms = (((imgDat-expDat)**2).sum()/len(imgDat))**0.5
        print 'RMS:', rms
        assert rms<crit
        