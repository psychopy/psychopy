import os, Image, numpy, glob, tempfile
import QTKit, AppKit

qtCodecQuality= {
  'lossless':   0x00000400,
  'max':        0x000003FF,
  'high':       0x00000300,
  'normal':     0x00000200,
  'low':        0x00000100,
  'min':        0x00000000,
}

class Movie(object):
    def __init__(self, filename, fps=30, rotate90=False):
        self.frameN = 1
        self.filename = filename
        self.movie = None
        self.fps = fps
        self.rotate90=rotate90
        self._movTmpFileName=None#we need a physical temp file to build the frames up?
    def addFrame(self, frame, duration=1):
        """Add a frame to the movie, from an image filename (anything that PIL can read)
        
        :Parameters:
            
            frame: can be;
                
                - an image filename (including path)
                - a numpy array
                - a PIL image
                - a `psychopy.visual.Window` movie frame (from win.getMovieFrame())
            
            duration: the length of time this frame should be displayed (in units of frame)
                
        """
        if self.movie is None:
            self._movTmpFileName=os.path.join(tempfile.gettempdir(), 'psychopyTmp.mov')#could this line fail if no permissions?
            #self._movTmpFileName='tmpMov'#this is handy if we want to inspect the temp file
            self.movie, err=QTKit.QTMovie.alloc().initToWritableFile_error_(self._movTmpFileName)#
            if err is not None:
                print str(err)
            self.movie.setEditable_(True)
        frameAttrs =  {QTKit.QTAddImageCodecType:'jpeg',# see QTKitdefines.h for compression options. These affect the size of the temp file
                                QTKit.QTAddImageCodecQuality:qtCodecQuality['max']}
        duration = QTKit.QTMakeTime(duration,self.fps)
        #for image filenames load file
        if type(frame)==str and os.path.isfile(frame):
            img = AppKit.NSImage.alloc().initByReferencingFile_(frame)
            self.movie.addImage_forDuration_withAttributes_(img, duration, frameAttrs)
        else:
            #can't seem to make this work to remove the need writing tmp.png files for each frame
            #            imgBuff=StringIO.StringIO()#a fake buffer to store the image (like tmpfile without disk access)
            #            pilIm = Image.fromarray(frame)#.save(imgBuff, 'png')
            #            img = NSImage.alloc().initWithContentsOfFile_(imgBuff)
            #                or:
            #            img = NSImage.alloc().initWithData_(AppKit.NSData.dataWithData_(frame.data))
            handle, tmpFileName=tempfile.mkstemp('.psychopyTmp.png')#could this line fail if no permissions?
            Image.fromarray(frame).save(tmpFileName)
            img = AppKit.NSImage.alloc().initByReferencingFile_(tmpFileName)
            self.movie.addImage_forDuration_withAttributes_(img, duration, frameAttrs)
            
            self.frameN += 1
            del img
        
    def save(self):
        self.movie.writeToFile_withAttributes_(self.filename,
            {QTKit.QTMovieFlatten:False})#if True then there is no inter-frame compression            
        #self.movie.updateMovieFile()#this doesn't use QTExport settings and you end up with large files (uncompressed in time)
    def __del__(self):
        """Remove any tmp files if possible (including any from previous runs that garbage collection wasn't able to collect)
        """
        tmpFolder=tempfile.gettempdir()
        files=[self._movTmpFileName]
        files.extend(glob.glob(os.path.join(tmpFolder,'*.psychopyTmpFrame')))
        for thisFile in files:
            print thisFile
            pass#os.remove(thisFile)
        
def test():
    import numpy, time
    t0=time.time()
    m = Movie("qtTest.mov")
    for frameN in range(10):
        arr=(numpy.random.random([640,480,3])*255).astype(numpy.uint8)
        m.addFrame(arr, 1)
        print '.',;os.sys.stdout.flush()
    m.save()
    print 'took %.2fs' %(time.time()-t0)
    
if __name__=='__main__':
    test()
