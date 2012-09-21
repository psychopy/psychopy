from psychopy import makeMovies
from psychopy.tests import utils
import sys

def test_quicktime():

    if sys.platform!='darwin':
        utils.skip("Only OS X can make Quicktime movies")
    import numpy, time, os
    mov_name = "qtTest.mov"
    t0=time.time()
    m = makeMovies.QuicktimeMovie(mov_name)
    for frameN in range(10):
        arr=(numpy.random.random([640,480,3])*255).astype(numpy.uint8)
        m.addFrame(arr, 1)
        print '.',;os.sys.stdout.flush()
    m.save()
    print 'took %.2fs' %(time.time()-t0)
    os.unlink(mov_name)

if __name__=='__main__':
    testQuicktime()