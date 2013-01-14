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

import numpy, time
from os import path
from string import capitalize
from sys import platform, exit, stdout
from psychopy import event, core, logging
from psychopy.constants import *

if platform=='win32':
    mediaLocation="C:\\Windows\Media"
else:
    mediaLocation=""

preferredAPI = ['pyo','pygame']
global audioAPI, Sound
Sound = None
audioAPI=None

try:
    import pyo
    havePyo = True
    pyoSndServerStarted = False
except ImportError:
    havePyo = False

if not havePyo:
    try:
        import pygame
        from pygame import mixer, sndarray
        havePygame=True
    except ImportError:
        havePygame=False
        raise "No sound library found - install either pyo or pygme"

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

        Often this is not needed byt the user - it is called implicitly during
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

class SoundPyo(_SoundBase):
    """Create a sound object, from one of MANY ways.
    """
    def __init__(self,value="C",secs=0.5,octave=4, stereo=True, sampleRate=44100, bits=16):
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
        global pyoSndServerStarted
        if pyoSndServerStarted==False:
            initPyo()
        self.sampleRate=sampleRate
        self.format = bits
        self.isStereo = stereo
        self.secs=secs

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
        self._snd.out()
        self.status=STARTED

    def _onEOS(self):
        #ToDo: is an EOS callback supported by pyo?
        self.status=FINISHED
        return True

    def stop(self):
        """Stops the sound immediately"""
        self._snd.stop()
        self.status=STOPPED

    def getDuration(self):
        """Return the duration of the sound file
        """
        return self._sndTable.getDur()

    def getVolume(self):
        """Returns the current volume of the sound (0.0:1.0)"""
        #ToDo : get volume for pyo
        return volume

    def setVolume(self,newVol):
        """Sets the current volume of the sound (0.0:1.0)"""
        #ToDo : set volume for pyo
        pass
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
        self._sndTable = pyo.SndTable(self.fileName)
        self._snd = pyo.Osc(self._sndTable, freq=self._sndTable.getRate())
        return True

    def _fromArray(self, thisArray):
        #ToDo: create a pyo sound from an array
        if self.isStereo:
            channels=2
        else:
            channels=1
        self._sndTable = pyo.DataTable(size=len(thisArray), init=thisArray.tolist(), chnls=channels)
        self._snd = pyo.Osc(self._sndTable, freq=self._sndTable.getRate())
        return True

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

def initPyo(rate=44100, stereo=True, buffer=256):
    """setup the pyo (sound) server
    """
    #subclass the pyo.Server so that we can insert a __del__ function that shuts it down
    class Server(pyo.Server):
        core=core #make libs class variables so they don't get deleted first
        logging=logging
        def __del__(self):
            self.stop()
            self.core.wait(0.5)#make sure enough time passes for the server to shutdown
            self.shutdown()
            self.logging.debug('pyo sound server shutdown')#this may never get printed

    #create the instance of the server
    pyoSndServer = Server(sr=rate, nchnls=2, buffersize=buffer, duplex=1).boot()

    core.wait(0.25)
    pyoSndServer.start()
    core.wait(0.25)
    logging.debug('pyo sound server started')
    logging.flush()
    global pyoSndServerStarted
    pyoSndServerStarted = True

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

