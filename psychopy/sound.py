"""Load and play sounds

There are various APIs for this, none of which are perfect. By default PsychoPy will
look for and use, in this order: ['pygame','pyglet','pyaudio']
The API chosen will be stored as a string under::

    sound.audioAPI

and can be set using, e.g.::

    sound.setAudioAPI('pyglet')

pygame (must be version 1.8 or above):
    pros: The most robust of the API options so far - it works consistently on all platforms
    cons: needs an additional download, poor latencies

pyglet:
    pros: comes with enthought python and is already the main API for drawing in PsychoPy
    cons: complex model using event_dispatch, dodgy timing (just on win32?)

pyaudio:
    pros: relatively low-level wrapper around portAudio
    cons: needs another download, rather buggy.

"""
# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import numpy, threading, time
from os import path
from string import capitalize
from sys import platform, exit, stdout
from psychopy import event, core, logging
from psychopy.constants import *

if platform=='win32':
    mediaLocation="C:\\Windows\Media"
else:
    mediaLocation=""

preferredAPI = ['pygame','pyglet','pyaudio']
global audioAPI, Sound
Sound = None
audioAPI=None

try:
    import pyglet
    import pyglet.media.procedural
    pyglet.options['audio'] = ('silent')
    pyglet.options['debug_gl'] = False
    import pyglet.media#, pyglet.resource
    import ctypes, math
    havePyglet=True
except ImportError:
    havePyglet=False

try:
    import pygame
    from pygame import mixer, sndarray
    havePygame=True
except ImportError:
    havePygame=False

try:
    import pyaudio
    pa = pyaudio.PyAudio()
    havePyaudio=True
except ImportError:
    havePyaudio=False

class _SoundBase:
    """Create a sound object, from one of many ways.
    """
    def __init__(self,value="C",secs=0.5,octave=4, sampleRate=44100, bits=16, name='', autoLog=True):
        """

        :parameters:
            value: can be a number, string or an array:
                * If it's a number between 37 and 32767 then a tone will be generated at that frequency in Hz.
                * It could be a string for a note ('A','Bfl','B','C','Csh'...). Then you may want to specify which octave as well
                * Or a string could represent a filename in the current location, or mediaLocation, or a full path combo
                * Or by giving an Nx2 numpy array of floats (-1:1) you can specify the sound yourself as a waveform

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
        self.name=name#only needed for autoLogging
        self.autoLog=autoLog
        self._snd=None
        self.setSound(value=value, secs=secs, octave=octave)

    def setSound(self, value, secs=0.5, octave=4):
        """Set the sound to be played.

        Often this is not needed by the user - it is called implicitly during
        initialisation.

        :parameters:

            value: can be a number, string or an array:
                * If it's a number between 37 and 32767 then a tone will be generated at that frequency in Hz.
                * It could be a string for a note ('A','Bfl','B','C','Csh'...). Then you may want to specify which octave as well
                * Or a string could represent a filename in the current location, or mediaLocation, or a full path combo
                * Or by giving an Nx2 numpy array of floats (-1:1) you can specify the sound yourself as a waveform

            secs: duration (only relevant if the value is a note name or a frequency value)

            octave: is only relevant if the value is a note name.
                Middle octave of a piano is 4. Most computers won't
                output sounds in the bottom octave (1) and the top
                octave (8) is generally painful
        """
        self._snd = None  # Re-init sound to ensure bad values will raise RuntimeError during setting
        
        try:#could be '440' meaning 440
            value = float(value)
        except:
            pass#this is a string that can't be a number

        if type(value) in [str, unicode]:
            #try to open the file
            OK = self._fromNoteName(value,secs,octave)
            #or use as a note name
            if not OK: self._fromFile(value)

        elif type(value)==float:
            #we've been asked for a particular Hz
            self._fromFreq(value, secs)

        elif type(value) in [list,numpy.ndarray]:
            #create a sound from the input array/list
            self._fromArray(value)
        if self._snd is None:
            raise RuntimeError, "I dont know how to make a "+value+" sound"
        self.status=NOT_STARTED

    def play(self, fromStart=True):
        """Starts playing the sound on an available channel.
        If no sound channels are available, it will not play and return None.

        This runs off a separate thread i.e. your code won't wait for the
        sound to finish before continuing. You need to use a
        psychopy.core.wait() command if you want things to pause.
        If you call play() whiles something is already playing the sounds will
        be played over each other.
        """
        pass #should be overridden

    def stop(self):
        """Stops the sound immediately"""
        pass #should be overridden

    def getDuration(self):
        pass #should be overridden

    def getVolume(self):
        """Returns the current volume of the sound (0.0:1.0)"""
        pass #should be overridden

    def setVolume(self,newVol):
        """Sets the current volume of the sound (0.0:1.0)"""
        pass #should be overridden
    def _fromFile(self, fileName):
        pass #should be overridden
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
            'Efl' : -6,
            'E' : -5,
            'F' : -4,
            'Fsh' : -3,
            'Gfl' : -3,
            'G' : -2,
            'Gsh' : -1,
            'Afl': -1,
            'A': 0,
            'Ash':+1,
            'Bfl': +1,
            'B': +2,
            'Bsh': +2,
            }
        if thisNote not in stepsFromA.keys():
            return False

        thisOctave = octave-4
        thisFreq = A * 2.0**(stepsFromA[thisNote]/12.0) * 2.0**thisOctave
        self._fromFreq(thisFreq, secs)

    def _fromFreq(self, thisFreq, secs):
        nSamples = int(secs*self.sampleRate)
        outArr = numpy.arange(0.0,1.0, 1.0/nSamples)
        outArr *= 2*numpy.pi*thisFreq*secs
        outArr = numpy.sin(outArr)
        self._fromArray(outArr)

    def _fromArray(self, thisArray):
        pass #should be overridden

class SoundPygame(_SoundBase):
    """Create a sound object, from one of many ways.

    :parameters:
        value: can be a number, string or an array:
            * If it's a number between 37 and 32767 then a tone will be generated at that frequency in Hz.
            * It could be a string for a note ('A','Bfl','B','C','Csh'...). Then you may want to specify which octave as well
            * Or a string could represent a filename in the current location, or mediaLocation, or a full path combo
            * Or by giving an Nx2 numpy array of floats (-1:1) you can specify the sound yourself as a waveform

        secs: duration (only relevant if the value is a note name or a frequency value)

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
    def __init__(self,value="C",secs=0.5,octave=4, sampleRate=44100, bits=16, name='', autoLog=True):
        """
        """
        self.name=name#only needed for autoLogging
        self.autoLog=autoLog
        #check initialisation
        if not mixer.get_init():
            pygame.mixer.init(sampleRate, -16, 2, 3072)

        inits = mixer.get_init()
        if inits is None:
            init()
            inits = mixer.get_init()
        self.sampleRate, self.format, self.isStereo = inits

        #try to create sound
        self._snd=None
        self.setSound(value=value, secs=secs, octave=octave)

    def play(self, fromStart=True):
        """Starts playing the sound on an available channel.
        If no sound channels are available, it will not play and return None.

        This runs off a separate thread i.e. your code won't wait for the
        sound to finish before continuing. You need to use a
        psychopy.core.wait() command if you want things to pause.
        If you call play() whiles something is already playing the sounds will
        be played over each other.
        """
        self._snd.play()
        self.status=STARTED
    def stop(self):
        """Stops the sound immediately"""
        self._snd.stop()
        self.status=STOPPED
    def fadeOut(self,mSecs):
        """fades out the sound (when playing) over mSecs.
        Don't know why you would do this in psychophysics but it's easy
        and fun to include as a possibility :)
        """
        self._snd.fadeout(mSecs)
        self.status=STOPPED
    def getDuration(self):
        """Get's the duration of the current sound in secs"""
        return self._snd.get_length()

    def getVolume(self):
        """Returns the current volume of the sound (0.0:1.0)"""
        return self._snd.get_volume()

    def setVolume(self,newVol):
        """Sets the current volume of the sound (0.0:1.0)"""
        self._snd.set_volume(newVol)

    def _fromFile(self, fileName):

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
        self._snd = mixer.Sound(self.fileName)
        return True

    def _fromArray(self, thisArray):
        global usePygame
        #get a mixer.Sound object from an array of floats (-1:1)

        #make stereo if mono
        if self.isStereo==2 and \
            (len(thisArray.shape)==1 or thisArray.shape[1]<2):
            tmp = numpy.ones((len(thisArray),2))
            tmp[:,0] = thisArray
            tmp[:,1] = thisArray
            thisArray = tmp

        #get the format right
        if self.format == -16:
            thisArray= (thisArray*2**15).astype(numpy.int16)
        elif self.format == 16:
            thisArray= ((thisArray+1)*2**15).astype(numpy.uint16)
        elif self.format == -8:
            thisArray= (thisArray*2**7).astype(numpy.Int8)
        elif self.format == 8:
            thisArray= ((thisArray+1)*2**7).astype(numpy.uint8)

        self._snd = sndarray.make_sound(thisArray)

        return True

class SoundPyglet(_SoundBase):
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

        self.sampleRate=sampleRate
        self.format = bits
        self.isStereo = True
        self.secs=secs
        self._player=pyglet.media.ManagedSoundPlayer()

        #self._player._eos_action='pause'
        self._player._on_eos=self._onEOS

        #try to create sound
        self._snd=None
        self.setSound(value=value, secs=secs, octave=octave)

    def play(self, fromStart=True):
        """Starts playing the sound on an available channel.
        If no sound channels are available, it will not play and return None.

        This runs off a separate thread i.e. your code won't wait for the
        sound to finish before continuing. You need to use a
        psychopy.core.wait() command if you want things to pause.
        If you call play() whiles something is already playing the sounds will
        be played over each other.
        """
        self._player.play()
        pyglet.media.dispatch_events()
        self.status=STARTED

    def _onEOS(self):
        self._player._playing = False
        self._player._timestamp = self._player._sources[0].duration
        self._player.seek(0)
        self._player.queue(self._snd)
        self._player._fill_audio()
        self._player.dispatch_event('on_eos')
        self.status=FINISHED
        return True

    def stop(self):
        """Stops the sound immediately"""
        self._snd._stop()
        self.status=STOPPED

    def getDuration(self):
        s=self._snd
        if s.duration is not None:
            duration = s.duration
        else:
            duration = len(s._data)/float(s.audio_format.sample_rate)
            #data are in byte packets so scale for sample_size (probably 2bytes)
            duration = duration*8/s.audio_format.sample_size/s.audio_format.channels
        return duration

    def getVolume(self):
        """Returns the current volume of the sound (0.0:1.0)"""
        return self._player.volume

    def setVolume(self,newVol):
        """Sets the current volume of the sound (0.0:1.0)"""
        self._player._set_volume(newVol)
    def _fromFile(self, fileName):

        #try finding the file
        self.fileName=None
        for filePath in ['', mediaLocation]:
            if path.isfile(path.join(filePath,fileName)):
                self.fileName=path.join(filePath,fileName)
            elif path.isfile(path.join(filePath,fileName+'.wav')):
                self.fileName=path.join(filePath,fileName+'.wav')
        if self.fileName is None:
            return False

        self._snd = pyglet.media.load(self.fileName, streaming=False)
        #for files we need to find the length of the file and
        if self._snd.duration is not None: #will return none if not determined in the file
            self.secs=self._snd.duration
        #add to our player queue
        self._player.queue(self._snd)
        return True

    def _fromArray(self, thisArray):
        global _pygletArrSound
        #get a mixer.Sound object from an array of floats (-1:1)

        #make stereo if mono
        if self.isStereo and \
            (len(thisArray.shape)==1 or thisArray.shape[1]<2):
            tmp = numpy.ones((len(thisArray),2))
            tmp[:,0] = thisArray
            tmp[:,1] = thisArray
            thisArray = numpy.transpose(tmp)#pyglet wants the transpose

        #use pyglet
        self._snd = _pygletArrSound(data=thisArray, sample_rate=self.sampleRate, sample_size=-self.format)
        self._player.queue(self._snd)
        return True

class SoundPyaudio(_SoundBase):
    """Create a sound object, from one of MANY ways.
    """
    def __init__(self,value="C",secs=0.5,octave=4,
                    sampleRate=44100, bits=16):
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
            Middle octave of a piano is 4. NB On most computers you can't hear
            sound_snds in the bottom octave (1) and the top
            octave (8) is generally painful

        sampleRate(=44100)

        bits(=16): 8 or 16
        """
        global mediaLocation

        if not havePyglet or not havePyaudio:
            raise ImportError, "pyglet and pyaudio are both needed for this type of sound"
        self.offsetSamples = -1
        self.bits = bits
        self.sampleRate = sampleRate
        self.channels=2
        self.finished=False
        self.chunkSize=2048# 1024 gives buffer underuns on OSX (even at 22kHz)
        self.volume = 1.0

        self.rawData = None
        self._thread = PyAudioThread(self, pollingPeriod=0.01)
        self._thread.start()

        #try to create sound
        self._snd=None
        self.setSound(value=value, secs=secs, octave=octave)

        if self.bits==16: paFormat = pyaudio.paInt16
        elif self.bits==8: paFormat = pyaudio.paInt8
        else: raise TypeError, "Sounds must be 8, 16bit"
        self._stream = pa.open(format = paFormat,
                channels = self.channels,
                rate = self.sampleRate,
                input = False, output=True)

    def play(self, startPos = 0):
        """Starts playing the sound.

        startPos detremines where the sound begins (in secs)
        """
        self.finished=False
        self.setOffset(startPos)
        self._fillBuffer()#to get the first sample on its way

    def setOffset(self, secs):
        #self._snd._seek(0)
        self.offsetSamples = secs*self.sampleRate

    def stop(self):
        """Stops the sound immediately"""
        self.offsetSamples=-1

    def getDuration(self):
        s=self._snd
        if s.duration is not None:
            duration = s.duration
        else:
            duration = len(s._data)/float(s.audio_format.sample_rate)
            #data are in byte packets so scale for sample_size (probably 2bytes)
            duration = duration*8/s.audio_format.sample_size/s.audio_format.channels
        return duration

    def getVolume(self):
        """Returns the current volume of the sound (0.0:1.0)"""
        return self.volume

    def setVolume(self,newVol):
        """Sets the current volume of the sound (0.0:1.0)"""
        self.volume = newVol
    def _fromFile(self, fileName):
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
        self._snd = pyglet.media.load(self.fileName, streaming=False)
        #convert to an array with int8 or int16
        if self.bits==16:
            sndArr = numpy.fromstring(self._snd._data,dtype=numpy.int16)
        elif self.bits==8:
            sndArr = numpy.fromstring(self._snd._data,dtype=numpy.uint8)
            #pyaudio want signed ints so convert unit8 to int8
            sndArr = (sndArr.astype(numpy.int16)-128).astype(int8)
        sndArr.shape= [len(sndArr)/self.channels, self.channels]
        #create the sound buffer from this array
        self._fromArray(sndArr)
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
        if self.bits==16:
            self._fromArray( (outArr*32767).astype(numpy.int16) )
        if self.bits==8:
            self._fromArray( (outArr*127.5-0.5).astype(numpy.int8) )#the minus 1 gives range -128:127

    def _fromArray(self, thisArray):
        """Expects an array that is already of the correct format (int8 or int16).
        Will create a second channel if only one is provided.
        """
        #make stereo if mono
        if self.channels==2 and \
            (len(thisArray.shape)==1 or thisArray.shape[1]<2):
                thisArray.shape = [len(thisArray),1]
                thisArray = thisArray.repeat(2,1)#create the second channel
        self.rawData = thisArray
        return True

    def _fillBuffer(self):
        """a function that can be called repeatedly to provide more data to the
        stream"""

        #NB chunkSize and getRemainingBytes() both refer to the number of bytes
        #(not samples) IN EACH CHANNEL (not in total)
        #ie. represent half the total number of bytes for a stereo source

        if self.offsetSamples==-1 or self.finished:
            print 'finishedPlaying', self.offsetSamples, self.finished
            #sound is not playing yet, just return
            return

        #get the appropriate data from the array
        if self.bits == 8:#ubyte
            start = self.offsetSamples
            end = self.offsetSamples+self.chunkSize#either the chunk or the last sample
        elif self.bits==16: #signed int16
            start = self.offsetSamples >> 1#half as many entries for same number of bytes
            end = (self.offsetSamples+ self.chunkSize) >> 1

        #check if we have that many samples
        if end>self.rawData.shape[0]:
            end = self.rawData.shape[0]
            print 'end, shape', end, self.rawData.shape[0]
            self.finished=True#flag that this must be the last sample
        #update next offset position
        self.offsetSamples+=self.chunkSize

        thisChunk = (self.volume*self.rawData[start:end,:])
        print start, end, self.rawData.shape, thisChunk.shape
        data=thisChunk.tostring()
        # play stream
        if len(data)==0:
            self.finished=True
            return

        #cwrite the data to the stream
        self._stream.write(data)


def initPyaudio():
    """
    define a thread for pyaudio event pumping (needed to fill buffers)
    """
    class PyAudioThread(threading.Thread):
        """a thread class to allow PyAudio sounds to play asynchronously"""
        def __init__(self, sound, pollingPeriod):
            threading.Thread.__init__ ( self )
            self.setDaemon(True)
            self.sound = sound
            self.pollingPeriod=pollingPeriod
            self.running = -1
        def run(self):
            self.running=1
            while self.running:
                #do the data read
                self.sound._fillBuffer()
                time.sleep(self.pollingPeriod)#yields to other processes while sleeping
            self.running=-1 #shows that it is fully stopped
        def stop(self):
            if self.running>0:
                self.running=0 #make a request to stop on next entry
        def setPollingPeriod(self, period):
            self.pollingPeriod=period

def initPyglet():
    """
    define a thread for pyglet event pumping (needed to fill buffers)
    """
    evtDispatchLock = threading.Lock()
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
        def setPollingPeriod(self, period):
            #print 'polling period is now:%.3f' %period
            self.pollingPeriod=period


    global _eventThread, _pygletArrSound
    if platform=='win32':
        _eventThread = _EventDispatchThread(pollingPeriod=0.01)
    else:
        _eventThread = _EventDispatchThread(pollingPeriod=0.001)#Mac seem to be able to use a shorter refresh safely

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
        def __init__(self, data, sample_rate=22050, sample_size=16):
            """Array data should be float (-+1.0)
            sample_size (16 or 8) determines the number of bits used for internal storage"""
            duration = data.shape[1]/float(sample_rate) #determine duration from data
            super(_pygletArrSound, self).__init__(duration,sample_rate, abs(sample_size))
            self.sample_rate = sample_rate
            self.sample_size=sample_size
            if abs(sample_size)==8:          #ubyte
                self.allData = (data*127+127).astype(numpy.uint8)
            elif abs(sample_size) == 16:      #signed int16
                self.allData = (data*32767).astype(numpy.int16)

        def _generate_data(self, bytes, offset, volume=1.0):
            #print 'bps', self._bytes_per_sample, bytes
            if self.sample_size == 8:#ubyte
                start = offset
                samples = bytes
            else: #signed int16
                start = (offset >> 1)#half as many entries for same number of bytes
                samples = (bytes >> 1)
            return (self.allData[:,start:(start+samples)]).ctypes

def initPygame(rate=22050, bits=16, stereo=True, buffer=1024):
    """If you need a specific format for sounds you need to run this init
    function. Run this *before creating your visual.Window*.

    The format cannot be changed once initialised or once a Window has been created.

    If a Sound object is created before this function is run it will be
    executed with default format (signed 16bit stereo at 22KHz).

    For more details see pygame help page for the mixer.
    """
    if stereo==True: stereoChans=2
    else:   stereoChans=0
    if bits==16: bits=-16 #for pygame bits are signed for 16bit, signified by the minus
    mixer.init(rate, bits, stereoChans, buffer) #defaults: 22050Hz, 16bit, stereo,
    sndarray.use_arraytype("numpy")
    setRate, setBits, setStereo = mixer.get_init()
    if setRate!=rate:
        logging.warn('Requested sound sample rate was not poossible')
    if setBits!=bits:
        logging.warn('Requested sound depth (bits) was not possible')
    if setStereo!=2 and stereo==True:
        logging.warn('Requested stereo setting was not possible')


def setAudioAPI(api):
    """Change the API used for the presentation of sounds

        usage:
            setAudioAPI(api)

        where:
            api is one of 'pygame','pyglet', pyaudio'

    """
    global audioAPI, Sound
    exec('haveThis=have%s' %api.title())
    if haveThis:
        audioAPI=api
        exec('init%s()' %(API.title()))
        exec('thisSound= Sound%s' %(API.title()))
        Sound= thisSound
    return haveThis

#initialise it and keep track
for API in preferredAPI:
    if setAudioAPI(API):
        audioAPI=API
        break#we found one so stop looking
if audioAPI is None:
    logging.error('No audio API found. Try installing pygame 1.8+')

