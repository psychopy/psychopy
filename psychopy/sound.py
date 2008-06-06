"""Load and play sounds (wraps pygame.mixer)
"""

try:
    import pyglet.media.procedural
    import pyglet.media
    havePyglet=True
except:
    havePyglet=False
    
try:
    import pygame
    from pygame import mixer, sndarray
    havePygame=True
except:
    havePygame=False
    
if havePygame:
    usePygame=True#change this when creating sounds if display is not initialised
else: usePygame=False    
    
import numpy
import logging #will be the psychopy.logging module
from os import path 
from string import capitalize

mediaLocation="C:\\Windows\Media"

if havePyglet:
    class _pygletArrSound(pyglet.media.procedural.ProceduralSource):
        """
        Create a pyglet.StaticSource from a numpy array. 
        """
        def __init__(self, data, sample_rate=44800, sample_size=16):
            """Array data should be float (-+1.0)
            sample_size (16 or 8) determines the number of bits used for internal storage"""
            duration = data.shape[1]/float(sample_rate) #determine duration from data
            super(_pygletArrSound, self).__init__(duration,sample_rate, sample_size)
            self.sample_rate = sample_rate
            
            if sample_size==8:          #ubyte
                self.allData = (data*127+127).astype(numpy.uint8)
            elif sample_size == 16:      #signed int16
                self.allData = (data*32767).astype(numpy.int16)
            print "create pyglet sound"
        def _generate_data(self, bytes, offset):
            if self._bytes_per_sample == 1:#ubyte
                start = offset
                samples = bytes
            else:			            #signed int16
                start = offset >> 1
                samples = bytes >> 1
            return (self.allData[start:(start+samples)]).tostring()   
    
def init(rate=44100, bits=-16, stereo=True, buffer=1024):
    """If you need a specific format for sounds you need to run this init
    function. Run this *before creating your visual.Window*.
    
    The format cannot be changed once initialised or once a Window has been created. 
    
    If a Sound object is created before this function is run it will be
    executed with default format (signed 16bit stereo at 44KHz).
    
    For more details see pygame help page for the mixer.
    """
    if stereo==True: stereoChans=2
    else:   stereoChans=0
    mixer.init(rate, bits, stereoChans, buffer) #defaults: 22050Hz, 16bit, stereo,
    setRate, setBits, setStereo = mixer.get_init()
    if setRate!=rate: 
        logging.warn('Requested sound sample rate was not poossible')
    if setBits!=bits:
        logging.warn('Requested sound depth (bits) was not possible')
    if setStereo!=1 and stereo==True: 
        logging.warn('Requested stereo setting was not possible')
    
class Sound:
    """Create a sound object, from one of MANY ways.
    """
    def __init__(self,value="C",secs=0.5,octave=4, sampleRate=44800, bits=-16):
        """
        value: can be a number, string or an array.
        
            If it's a number between 37 and 32767 then a tone will be generated at
            that frequency in Hz.
            -----------------------------
            It could be a string for a note ('A','Bfl','B','C','Csh'...) 
            - you may want to specify which octave as well
            -----------------------------
            Or a string could represent a filename in the current
            location, or mediaLocation, or a full path combo
            -----------------------------
            Or by giving an Nx2 numpy array of floats (-1:1) you 
            can specify the sound yourself as a waveform
            
        secs: is only relevant if the value is a note name or
            a frequency value
            
        octave: is only relevant if the value is a note name.
            Middle octave of a piano is 4. Most computers won't
            output sounds in the bottom octave (1) and the top
            octave (8) is generally painful
            
        sampleRate(=44800): only used for sounds using pyglet. Pygame uses the same
            sample rate for all sounds (once initialised) 
        
        bits(=16): Only 8- and 16-bits supported so far.
            Only used for sounds using pyglet. Pygame uses the same
            sample rate for all sounds (once initialised) 
        """
        global mediaLocation, usePygame
        #check initialisation of the 
        if (usePygame and mixer.get_init()) or not havePyglet:
            inits = mixer.get_init()
            if inits is None:
                init()
                inits = mixer.get_init()                
            self.sampleRate, self.format, self.isStereo = inits
        else:
            usePygame=False
            self.sampleRate=sampleRate
            self.format = bits
            self.isStereo = True
        
        #try to determine what the sound is
        self._snd=None
        if type(value) is str:
            #try to open the file
            OK = self._fromNoteName(value,secs,octave)
            #or use as a note name
            if not OK: self._fromFile(value)
            
        elif type(value) in [float,int]:
            #we've been asked for a particular Hz
            self._fromFreq(value, secs)
            
        elif type(value) in [list,numpy.ndarray]:
            #create a sound from the input array/list
            self._fromArray(value)
        if self._snd is None:
            raise RuntimeError, "I dont know how to make a "+value+" sound"
            
    def play(self):
        """Starts playing the sound on an available channel. 
        If no sound channels are available, it will not play and return None. 

        This runs off a separate thread i.e. your code won't wait for the
        sound to finish before continuing. You need to use a 
        psychopy.core.wait() command if you want things to pause.
        If you call play() whiles something is already playing the sounds will
        be played over each other.
        """
        self._snd.play()
        
    def stop(self):
        """Stops the sound immediately"""
        self._snd.stop()
        
    def fadeOut(self,mSecs):
        """fades out the sound (when playing) over mSecs.
        Don't know why you would do this in psychophysics but it's easy
        and fun to include as a possibility :)
        """
        self._snd.fadeout(mSecs)
        
    def getVolume(self):
        """Returns the current volume of the sound (0.0:1.0)"""
        return self._snd.get_volume()
    
    def setVolume(self,newVol):
        """Sets the current volume of the sound (0.0:1.0)"""
        self._snd.set_volume(newVol)
    def _fromFile(self, fileName):
        global usePygame
        
        #try finding the file
        self.fileName=None
        for filePath in ['', mediaLocation]:
            if path.isfile(path.join(filePath,fileName)):
                self.fileName=path.join(filePath,fileName)
            elif path.isfile(path.join(filePath,fileName+'.wav')):
                self.fileName=path.join(filePath,fileName+'.wav')
        if self.fileName is None:
            return False
        
        #load the file
        if usePygame:
            self._snd = mixer.Sound(self.fileName)
        else:
            self._snd = pyglet.media.load(self.fileName, streaming=False)
        return True
    def _fromNoteName(self, name, secs, octave):		
        #get a mixer.Sound object from an note name
        A=440.0
        thisNote=capitalize(name)
        stepsFromA = {
            'C' : -9,
            'Csh' : -8,
            'Dfl' : -8,
            'D' : -7,
            'Dsh' : -6,
            'E' : -5,
            'F' : -4,
            'Fsh' : -3,
            'G' : -2,
            'Gsh' : -1,
            'A': 0,
            'Ash':+1,
            'Bfl': +1,
            'B': +2,
            }
        if thisNote not in stepsFromA.keys():
            return False
        
        thisOctave = octave-4		
        thisFreq = A * 2.0**(stepsFromA[thisNote]/12.0) * 2.0**thisOctave
        self._fromFreq(thisFreq, secs)
        
    def _fromFreq(self, thisFreq, secs):
        #get a mixer.Sound object from a frequency
        nSamples = int(secs*self.sampleRate)
        outArr = numpy.arange(0.0,1.0, 1.0/nSamples)
        outArr *= 2*numpy.pi*thisFreq*secs
        outArr = numpy.sin(outArr)
        self._fromArray(outArr)
    
    def _fromArray(self, thisArray):
        global usePygame
        #get a mixer.Sound object from an array of floats (-1:1)
        
        #make stereo if mono
        if self.isStereo and \
            (len(thisArray.shape)==1 or thisArray.shape[1]<2):
            tmp = numpy.ones((len(thisArray),2))
            tmp[:,0] = thisArray
            tmp[:,1] = thisArray
            if usePygame: 
                thisArray = tmp
            else:
                thisArray = numpy.transpose(tmp)#pyglet wants the transpose
        
        if usePygame:
            #get the format right
            if self.format == -16: 
                thisArray= (thisArray*2**15).astype(numpy.int16)
            elif self.format == 16: 
                thisArray= ((thisArray+1)*2**15).astype(numpy.uint16)
            elif self.format == -8: 
                thisArray= (thisArray*2**7).astype(numpy.Int8)
            elif self.format == 8: 
                thisArray= ((thisArray+1)*2**7).astype(numpy.uint8)
    
                
            try:
                import Numeric
            except:
                logging.error('Numeric (as well as numpy) is currently needed for playing pygame sounds')
                self._snd=None
                return -1
            self._snd = sndarray.make_sound(Numeric.array(thisArray))
            
        else:
            #use pyglet
            self._snd = _pygletArrSound(thisArray, sample_rate=self.sampleRate, sample_size=self.format)
        return True

        