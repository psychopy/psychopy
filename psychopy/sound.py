"""Load and play sounds

By default PsychoPy will try to use the following Libs, in this order, for
sound reproduction but you can alter the order in preferences>general>audioLib:
    ['pygame', 'pyo']
If the lib is `pyo` then there is also a choice of the underlying sound driver.
Under OSX this is currently set to use coreaudio (rather than portaudio) and on
windows it will attempt to use an ASIO-based driver if found and fall back to
DirectSound if not. These settings are not currently configurable but let the
team know if you need that.

The sound lib and driver (if lib==pyo) being used will be stored as::
    `psychopy.sound.audioLib`

For control of bitrate and buffer size you can call psychopy.sound.init before
creating your first Sound object::

    from psychopy import sound
    sound.init(rate=44100, stereo=True, buffer=128)
    s1 = sound.Sound('ding.wav')

pyo (a wrapper for portaudio and coreaudio):
    pros: low latency where drivers support it (on windows you may want to fetch ASIO4ALL)
    cons: new in PsychoPy 1.76.00

pygame (must be version 1.8 or above):
    pros: The most robust of the API options so far - it works consistently on all platforms
    cons: needs an additional download, poor latencies

"""
# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import numpy, time, sys
from os import path
from string import capitalize
from sys import platform, exit, stdout
from psychopy import event, core, logging, preferences
from psychopy.constants import *

if platform=='win32':
    mediaLocation="C:\\Windows\Media"
else:
    mediaLocation=""

global audioLib, Sound, init
global pyoSndServer
pyoSndServer=None
Sound = None
audioLib=None

prefs = preferences.Preferences()
for thisLibName in prefs.general['audioLib']:
    try:
        if thisLibName=='pyo':
            import pyo
            havePyo = True
        elif thisLibName=='pygame':
            import pygame
            from pygame import mixer, sndarray
        else:
            raise ValueError("Audio lib options are currently only 'pyo' or 'pygame', not '%'" %thisLibName)
    except:
        logging.warning('%s audio lib was requested but not loaded: %s' %(thisLibName, sys.exc_info()[1]))
        continue #to try next audio lib
    #if we got this far we were sucessful in loading the lib
    audioLib=thisLibName
    break

if audioLib==None:
    logging.warning('No audio lib could be loaded. Sounds will not be available.')

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

    def setSound(self, value, secs=0.5, octave=4, log=True):
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
        #did we succeed?
        if self._snd is None:
            raise RuntimeError, "I dont know how to make a "+value+" sound"
        else:
            if log and self.autoLog:
                logging.exp("Set %s sound=%s" %(self.name, value), obj=self)
            self.status=NOT_STARTED

    def play(self, fromStart=True, log=True):
        """Starts playing the sound on an available channel.
        If no sound channels are available, it will not play and return None.

        This runs off a separate thread i.e. your code won't wait for the
        sound to finish before continuing. You need to use a
        psychopy.core.wait() command if you want things to pause.
        If you call play() whiles something is already playing the sounds will
        be played over each other.
        """
        pass #should be overridden

    def stop(self, log=True):
        """Stops the sound immediately"""
        pass #should be overridden

    def getDuration(self):
        pass #should be overridden

    def getVolume(self):
        """Returns the current volume of the sound (0.0:1.0)"""
        pass #should be overridden

    def setVolume(self,newVol, log=True):
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

        sampleRate(=44100): If a sound has already been created or if the

        bits(=16):  Pygame uses the same bit depth for all sounds once initialised
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

    def play(self, fromStart=True, log=True):
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
        if log and self.autoLog:
            logging.exp("Sound %s started" %(self.name), obj=self)
    def stop(self, log=True):
        """Stops the sound immediately"""
        self._snd.stop()
        self.status=STOPPED
        if log and self.autoLog:
            logging.exp("Sound %s stopped" %(self.name), obj=self)
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

    def setVolume(self,newVol, log=True):
        """Sets the current volume of the sound (0.0:1.0)"""
        self._snd.set_volume(newVol)
        if log and self.autoLog:
            logging.exp("Set Sound %s volume=%.3f" %(self.name, newVol), obj=self)

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
    def __init__(self,value="C",secs=0.5,octave=4, stereo=True, sampleRate=44100, bits=16, name='', autoLog=True):
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

        sampleRate(=44100): if the psychopy.sound.init() function has been called
            or if another sound has already been created then this argument will be
            ignored and the previous setting will be used

        bits: has no effect for the pyo backend
        """
        global pyoSndServer
        if pyoSndServer==None:
            initPyo(rate=sampleRate)

        self.sampleRate=pyoSndServer.getSamplingRate()
        self.format = bits
        self.isStereo = stereo
        self.secs=secs
        self.autoLog=autoLog
        self.name=name

        #try to create sound
        self._snd=None
        self.setSound(value=value, secs=secs, octave=octave)

    def play(self, fromStart=True, log=True):
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
        if log and self.autoLog:
            logging.exp("Sound %s started" %(self.name), obj=self)

    def _onEOS(self):
        #ToDo: is an EOS callback supported by pyo?
        self.status=FINISHED
        return True

    def stop(self, log=True):
        """Stops the sound immediately"""
        self._snd.stop()
        self.status=STOPPED
        if log and self.autoLog:
            logging.exp("Sound %s stopped" %(self.name), obj=self)

    def getDuration(self):
        """Return the duration of the sound file
        """
        return self._sndTable.getDur()

    def getVolume(self):
        """Returns the current volume of the sound (0.0:1.0)"""
        #ToDo : get volume for pyo
        return volume

    def setVolume(self,newVol, log=True):
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
        self._snd = pyo.TableRead(self._sndTable, freq=self._sndTable.getRate(), loop=0)
        return True

    def _fromArray(self, thisArray):
        #ToDo: create a pyo sound from an array
        if self.isStereo:
            channels=2
        else:
            channels=1
        self._sndTable = pyo.DataTable(size=len(thisArray), init=thisArray.tolist(), chnls=channels)
        self._snd = pyo.TableRead(self._sndTable, freq=self._sndTable.getRate(), loop=0)
        return True

def initPygame(rate=22050, bits=16, stereo=True, buffer=1024):
    """If you need a specific format for sounds you need to run this init
    function. Run this *before creating your visual.Window*.

    The format cannot be changed once initialised or once a Window has been created.

    If a Sound object is created before this function is run it will be
    executed with default format (signed 16bit stereo at 22KHz).

    For more details see pygame help page for the mixer.
    """
    global Sound, audioDriver
    Sound = SoundPygame
    audioDriver='n/a'
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

def _bestDriver(devNames, devIDs):
    """Find ASIO or Windows sound drivers
    """
    if platform=='win32':
        preferredDrivers = ['Primary Sound','ASIO',] #primary sound= DirectSound
    elif platform=='darwin':
        preferredDrivers = ['coreaudio','portaudio']
    else:
        preferredDrivers = ['portaudio']

    outputID=None
    audioDriver=None
    for prefDriver in preferredDrivers:
        if prefDriver.lower()=='directsound':
            prefDriver = 'Primary Sound'
        #look for that driver in available devices
        for devN, devString in enumerate(devNames):
            if prefDriver in devString:
                audioDriver=devString
                outputID=devIDs[devN]
                return audioDriver, outputID #we found an asio driver don'w look for others

def initPyo(rate=44100, stereo=True, buffer=128):
    """setup the pyo (sound) server
    """
    global pyoSndServer, Sound, audioDriver
    Sound = SoundPyo
    #subclass the pyo.Server so that we can insert a __del__ function that shuts it down
    class Server(pyo.Server):
        core=core #make libs class variables so they don't get deleted first
        logging=logging
        def __del__(self):
            self.stop()
            self.core.wait(0.5)#make sure enough time passes for the server to shutdown
            self.shutdown()
            self.core.wait(0.5)#make sure enough time passes for the server to shutdown
            self.logging.debug('pyo sound server shutdown')#this may never get printed

    #check if we already have a server and kill it
    if hasattr(pyoSndServer,'shutdown'):
        #this doesn't appear to work!
        pyoSndServer.stop()
        core.wait(0.5)#make sure enough time passes for the server to shutdown
        pyoSndServer.shutdown()
        pyoSndServer.reinit(sr=rate, nchnls=2, buffersize=buffer, duplex=1, audio='coreaudio')
        pyoSndServer.boot()
    else:
        #create the instance of the server
        if platform=='darwin':
            audioLib=audioDriver='coreaudio'#portaudio had longer latencies than coreaudio when JWP tested (Jan 2013)
        else:
            audioLib='portaudio'
        #in win32 we need to check for a valid device
        if platform=='win32':
            #check for valid output (speakers)
            devNames, devIDs=pyo.pa_get_output_devices()
            audioDriver,outputID=_bestDriver(devNames, devIDs)
            if outputID:
                logging.info('Using sound driver: %s (ID=%i)' %(audioDriver, outputID))
            else:
                logging.warning('No audio outputs found (no speakers connected?')
                return -1
            #check for valid input (mic)
            devNames, devIDs = pyo.pa_get_input_devices()
            junk, inputID=_bestDriver(devNames, devIDs)
            if inputID:
                duplex=True
            else:
                duplex=False
        else:#for other platforms set duplex to True
            duplex=True
        pyoSndServer = Server(sr=rate, nchnls=2, buffersize=buffer, audio=audioLib,duplex=duplex)
        pyoSndServer.setVerbosity(1)
        if platform=='win32':
            pyoSndServer.setOutputDevice(outputID)
            if inputID:
                pyoSndServer.setInputDevice(inputID)
        #do other config here as needed (setDuplex? setOutputDevice?)
        pyoSndServer.boot()
    core.wait(0.5)#wait for server to boot before starting te sound stream
    pyoSndServer.start()
    logging.debug('pyo sound server started')
    logging.flush()

def setaudioLib(api):
    """DEPCRECATED: please use preferences>general>audioLib to determine which audio lib to use"""
    raise

#initialise it and keep track
if audioLib is None:
    logging.error('No audio API found. Try installing pygame 1.8+')
elif audioLib=='pyo':
    init=initPyo
    Sound=SoundPyo
elif audioLib=='pygame':
    init=initPygame
    Sound=SoundPygame

