#attempt using pygame
#
#progess: Movie module doesn't exist?
#
#from psychopy import *
from pygame import movie

class MovieStim:
    def __init__(self, filename):
        self.filename = filename
        self.file = open(filename, 'rb')
        self.demuxer=None #set this in initVideo 
        self.videoDecoder = None #set this in initVideo 
        self.format = filename.split( '.' )[ -1 ].lower()#the file extension is the format
        self.frameNum= -1
        self.params = None
        
        self.movie = movie.Movie(self.filename)
        
    def next(self):
        d= self.rawFrames.pop( 0 )
        vfr= self.vc.decode( d[ 1 ] )
        
myMovie = MovieStim(filename='myMovie.mpeg')
pass