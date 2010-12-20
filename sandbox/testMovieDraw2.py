from pymedia.video import ext_codecs, vcodec
import pymedia.muxer as muxer
#from psychopy import *
from pygame import movie

class MovieStim:
    def __init__(self, filename):
        self.filename = filename
        self.demuxer=None #set this in initVideo 
        self.videoDecoder = None #set this in initVideo 
        self.format = filename.split( '.' )[ -1 ].lower()#the file extension is the format
        self.frameNum= -1
        self.params = None
        self.codec= 'mpeg1video'
        
        #get all the frames from file
        f = open(filename, 'rb')
        self.rawData = f.read()
        f.close()
        
        self.initVideo()

    
    def initVideo(self):
        dm= muxer.Demuxer( self.format )
        
        #try to get multiple streams of a multiplexed file
        junk = dm.parse( self.rawData[30000] )
        if len(dm.streams)==0:
                #set bitrate
                if self.codec== 'mpeg1video':
                    bitrate= 2700000
                else:
                    bitrate= 9800000
                self.params= { \
                    'type': 0,
                    'gop_size': 12,
                    'frame_rate_base': 125,
                    'max_b_frames': 0,
                    'width': 800,
                    'height': 600,
                    'frame_rate': 3125,
                    'deinterlace': 0,
                    'bitrate': bitrate,
                    'id': vcodec.getCodecID( self.codec )
                    }
        elif len(dm.streams)==1:
            self.params = dm.streams[0]
        else:
            #loop through to find the first video stream in the file
            for vindex in xrange( len( dm.streams )):
                if dm.streams[ vindex ][ 'type' ]== muxer.CODEC_TYPE_VIDEO:
                  self.params= dm.streams[ vindex ] 
                  break
        
        print self.params
        
        try:
            # Set the initial sound delay to 0 for now
      
            # It defines initial offset from video in the beginning of the stream
      
            self.initADelta= -1
            self.seekADelta= 0
            # Setting up the HW video codec
      
            self.vc= ext_codecs.Decoder( self.params ) 
        except:
            self.vc= vcodec.Decoder( self.params )
            try:
              # Fall back to SW video codec
      
              self.vc= vcodec.Decoder( self.params )
            except:
              traceback.print_exc()
              self.err.append( sys.exc_info()[1] )
        
    def next(self):
        d= self.rawFrames.pop( 0 )
        vfr= self.vc.decode( d[ 1 ] )
        
#myMovie = MovieStim(filename='')
myMovie = MovieStim(filename='MVI_2860.avi')
dir()