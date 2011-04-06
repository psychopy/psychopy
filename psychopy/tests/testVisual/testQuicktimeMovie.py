from psychopy import makeMovies

def testQuicktime():
    import numpy, time, os
    t0=time.time()
    m = makeMovies.QuicktimeMovie("qtTest.mov")
    for frameN in range(10):
        arr=(numpy.random.random([640,480,3])*255).astype(numpy.uint8)
        m.addFrame(arr, 1)
        print '.',;os.sys.stdout.flush()
    m.save()
    print 'took %.2fs' %(time.time()-t0)
    
if __name__=='__main__':
    testQuicktime()