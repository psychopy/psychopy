"""Load and play sounds (wraps pygame.mixer)
"""
import numpy, threading, time
from os import path 
from string import capitalize
from sys import platform, exit, stdout
from psychopy import event, core, log

try:
    import pyglet
    #if pyglet.version<'1.1': #pyglet.resource was new and new event dispatching model
        #print "\nYou need pyglet v1.1 or above to use sounds\n"
        #sys.exit(0)
    import pyglet.media.procedural
    import pyglet.media#, pyglet.resource
    import ctypes, math
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
    

if platform=='win32':
    mediaLocation="C:\\Windows\Media"
else:
    mediaLocation=""

if havePyglet:
    
    class _EventDispatchThread(threading.Thread):    
        """a thread that will periodically call to dispatch events
        """
        """I've tried doing this in a way that the thread was started and stopped repeatedly
        (so could be paused while a sound wasn't needed, but never made it work.
        see sound.py in SVNr85 for the attempt."""
        def __init__(self, pollingPeriod=0.005):
            threading.Thread.__init__ ( self )
            self.pollingPeriod=pollingPeriod
            self.running = -1
            core.runningThreads.append(self)
        def run(self):
            self.running=1
            #print 'thread started'
            while self.running:
                #print self.pollingPeriod
                pyglet.media.dispatch_events()
                time.sleep(self.pollingPeriod)#yeilds to other processes while sleeping
            #print 'thread stopped'
            self.running=-1#shows that it is fully stopped
        def stop(self):
            if self.running>0:
                self.running=0#make a request to stop on next entry
            core.runningThreads.remove(self)
        def setPollingPeriod(self, period):
            #print 'polling period is now:%.3f' %period
            self.pollingPeriod=period
            
    global _eventThread
    _eventThread = _EventDispatchThread(pollingPeriod=0.001)
    
    def setEventPollingPeriod(period):
        """For pylget contexts this sets the frequency that events controlling sound start and stop
        are processed in seconds.
        
        A long period (e.g. 0.1s) will allow more time to be spent on drawing functions and computations,
        whereas a very short time (e.g. 0.0001) will allow more precise starting/stopping of audio stimuli..
        
        Events will always be polled on every screen refresh anyway, and repeatedly during 
        calls to event.waitKeys() so this command has few effects on anything other than for very
        precise sounds.
        """
        global _eventThread
        _eventThread.setPollingPeriod(period)
    def stopEventPolling():    
        """Stop all polling of events in a pyglet context. Events will still be dispatched on every
        flip of a visual.Window (every 10-15ms depending on frame rate).
        
        The user can then dispatch events manually using 
        pyglet.event.dispatch_events()
        """
        global _eventThread
        _eventThread.stop()
    def startEventPolling():    
        """Restart automated event polling if it has been suspended.
        This call does nothing if the polling had been 
        """
        global _eventThread
        if _eventThread.stopping:
            _eventThread.start()
            
    class _pygletArrSound(pyglet.media.procedural.ProceduralSource):
        """
        Create a pyglet.StaticSource from a numpy array. 
        """
        def __init__(self, data, sample_rate=44100, sample_size=16):
            """Array data should be float (-+1.0)
            sample_size (16 or 8) determines the number of bits used for internal storage"""
            duration = data.shape[1]/float(sample_rate) #determine duration from data
            super(_pygletArrSound, self).__init__(duration,sample_rate, abs(sample_size))
            self.sample_rate = sample_rate
            if abs(sample_size)==8:          #ubyte
                self.allData = (data*127+127).astype(numpy.uint8)
            elif abs(sample_size) == 16:      #signed int16
                self.allData = (data*32767).astype(numpy.int16)
            #print "created pyglet sound"
        def _generate_data(self, bytes, offset):
            #print 'bps', self._bytes_per_sample, bytes
            if self._bytes_per_sample == 1:#ubyte
                start = offset
                samples = bytes
                data = (self.allData[:,start:(start+samples)]).ctypes#.data_as(ctypes.POINTER(ctypes.c_ubyte))
            else: #signed int16
                start = (offset >> 1)#half as many entries for same number of bytes
                samples = (bytes >> 1)
                data = (self.allData[:,start:(start+samples)]).ctypes#.data_as(ctypes.POINTER(ctypes.c_short))
            return data

    
def init(rate=44100, bits=16, stereo=True, buffer=1024):
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
        log.warn('Requested sound sample rate was not poossible')
    if setBits!=bits:
        log.warn('Requested sound depth (bits) was not possible')
    if setStereo!=1 and stereo==True: 
        log.warn('Requested stereo setting was not possible')
    
class Sound:
    """Create a sound object, from one of MANY ways.
    """
    def __init__(self,value="C",secs=0.5,octave=4, sampleRate=44100, bits=16):
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
            
        sampleRate(=44100): only used for sounds using pyglet. Pygame uses one rate for all sounds
            sample rate for all sounds (once initialised) 
        
        bits(=16): Only 8- and 16-bits supported so far.
            Only used for sounds using pyglet. Pygame uses the same
            sample rate for all sounds (once initialised) 
        """
        global mediaLocation, usePygame, _eventThread
        #check initialisation
        if havePygame and (mixer.get_init() is not None):
            usePygame=True
        elif havePyglet:
            #we have pyglet and no pygame window so use pyglet
            usePygame=False
        else:
            log.error("Neither pygame, nor pyglet could be loaded for playing sounds")
        
        if usePygame:
            inits = mixer.get_init()
            if inits is None:
                init()
                inits = mixer.get_init()                
            self.sampleRate, self.format, self.isStereo = inits
            print "using pygame sound"
        else:
            usePygame=False
            self.sampleRate=sampleRate
            self.format = bits
            self.isStereo = True
            self.secs=secs
            self._player=pyglet.media.ManagedSoundPlayer()
            self._player._eos_action='pause'
            self._player._on_eos=self._onEOS
            if _eventThread.running<=0: _eventThread.start() #start the thread if needed
            
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
            
    def play(self, fromStart=True):
        """Starts playing the sound on an available channel. 
        If no sound channels are available, it will not play and return None. 

        This runs off a separate thread i.e. your code won't wait for the
        sound to finish before continuing. You need to use a 
        psychopy.core.wait() command if you want things to pause.
        If you call play() whiles something is already playing the sounds will
        be played over each other.
        """
        global usePygame
        if usePygame:
            self._snd.play()
        else:
            self._player.play()

    def _onEOS(self):
        #self._snd._seek(0)#reset the sound
        self._player._playing = False
        self._player._timestamp = self._player._sources[0].duration
        self._player.seek(0)
        self._player.queue(self._snd)
        self._player._fill_audio()
        self._player.dispatch_event('on_eos')
        return True
        
    def stop(self):
        """Stops the sound immediately"""
        global usePygame
        if usePygame:
            self._snd.stop()
        else:
            self._player._playing = False
            self._player._timestamp = self._player._sources[0].duration
            self._player.seek(0)
            self._player.queue(self._snd)
            self._player._fill_audio()
            
    #def fadeOut(self,mSecs):
        #"""fades out the sound (when playing) over mSecs.
        #Don't know why you would do this in psychophysics but it's easy
        #and fun to include as a possibility :)
        #"""
        #self._snd.fadeout(mSecs)
        
    def getVolume(self):
        """Returns the current volume of the sound (0.0:1.0)"""
        global usePygame
        if usePygame:
            return self._snd.get_volume()
        else:
            return self._player.volume
    
    def setVolume(self,newVol):
        """Sets the current volume of the sound (0.0:1.0)"""
        global usePygame
        if usePygame:
            self._snd.set_volume(newVol)
        else:
            self._player._set_volume(newVol)
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
            #for files we need to find the length of the file and 
            if self._snd.duration is not None: #will return none if not determined in the file
                self.secs=self._snd.duration
            #add to our player queue
            self._player.queue(self._snd)
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
                log.error('Numeric (as well as numpy) is currently needed for playing pygame sounds')
                self._snd=None
                return -1
            self._snd = sndarray.make_sound(Numeric.array(thisArray))
            
        else:
            #use pyglet
            self._snd = _pygletArrSound(data=thisArray, sample_rate=self.sampleRate, sample_size=-self.format)
            self._player.queue(self._snd)
        return True

        