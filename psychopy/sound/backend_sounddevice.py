import sys
import time

from psychopy import logging, exceptions
from psychopy.constants import (STARTED, PLAYING, PAUSED, FINISHED, STOPPED,
                                NOT_STARTED, FOREVER, AUTO, STEREO, MONO)
from psychopy.tools import attributetools
from ._base import _SoundBase

from psychopy.constants import NOT_STARTED, PLAYING, PAUSED, STOPPED, FINISHED
from psychopy import logging
import sounddevice as sd
import soundfile as sf

import numpy as np

logging.console.setLevel(logging.INFO)

END=-1
streams = {}

print("using SoundDevice with {}".format(sd.get_portaudio_version()[1]))
startTime = time.time()

def init():
    pass  # for compatibility with other backends

class SoundStream(object):
    def __init__(self, sampleRate, channels, blockSize, duplex=False):
        # initialise thread
        self.streams = []
        self.list = []
        # sound stream info
        self.sampleRate = sampleRate
        self.channels = channels
        self.duplex = duplex
        self.blockSize = blockSize
        self.sounds = []  # list of dicts for sounds currently playing
        self._sdStream = sd.OutputStream(samplerate=sampleRate, blocksize=self.blockSize,
                  latency = 'high', channels=channels, callback=self.callback)
        self._sdStream.start()
        self.device = self._sdStream.device
        self.latency = self._sdStream.latency
        self.cpu_load = self._sdStream.cpu_load
        self.frameN = 1
        self.takeTimeStamp = False
        self.frameTimes = range(5)  # DEBUGGING: store the last 5 callbacks
        self.lastFrameTime = time.time()

    def callback(self, toSpk, blockSize, timepoint, status):
        """This is a callback for the SoundDevice lib

        fromMic is data from the mic that can be extracted
        toSpk is a numpy array to be populated with data
        blockSize is the number of frames to be included each block
        timepoint has values:
            .currentTime
            .inputBufferAdcTime
            .outputBufferDacTime
        """
        if self.takeTimeStamp:
            logging.info("Entered callback: {} ms after last frame end"
                  .format((time.time()-self.lastFrameTime)*1000))
            logging.info("Entered callback: {} ms after sound start"
                  .format((time.time()-self.t0)*1000))
        t0 = time.time()
        self.frameN += 1
        toSpk *= 0  # it starts with the contents of the buffer before
        for soundN, thisSound in enumerate(self.sounds):
            dat = thisSound._nextBlock()  # fetch the next block of data
            if self.channels == 2:
                toSpk[:len(dat),:] += dat  # add to out stream
            else:
                toSpk[:len(dat),0] += dat  # add to out stream
            # check if that was a short block (sound is finished)
            if len(dat)<len(toSpk[:,:]):
                self.sounds.remove(thisSound)
                thisSound.status = FINISHED
            # check if that took a long time
            t1 = time.time()
            if (t1-t0)>0.001:
                logging.info("buffer_callback took {:.3f}ms that frame"
                             .format((t1-t0)*1000))
        self.frameTimes.pop(0)
        self.frameTimes.append(time.time()-self.lastFrameTime)
        self.lastFrameTime = time.time()
        if self.takeTimeStamp:
            logging.info("Callback durations: {}".format(self.frameTimes))
            logging.info("blocksize = {}".format(blockSize))
            self.takeTimeStamp = False

    def add(self, sound):
        self.t0 = time.time()
        self.sounds.append(sound)
        logging.info("took {} ms to add".format((time.time()-self.t0)*1000))

    def remove(self, sound):
        if sound in self.sounds:
            self.sounds.remove(sound)

    def __del__(self):
        print 'garbage_collected_soundDeviceStream'
        self._sdStream.stop()
        del self._sdStream
        sys.stdout.flush()


class SoundDeviceSound(_SoundBase):
    """Play a variety of sounds using the new SoundDevice library
    """
    def __init__(self, value="C", secs=0.5, octave=4, stereo=AUTO,
                 volume=1.0, loops=0,
                 sampleRate=44100, blockSize=128,
                 bufferSize=-1,
                 hamming=True, start=0, stop=-1,
                 name='', autoLog=True):
        """
        :param value: note name ("C","Bfl"), filename or frequency (Hz)
        :param secs: duration (for synthesised tones)
        :param octave: which octave to use for note names (4 is middle)
        :param stereo: 'auto', True or False
                        to force sounds to a particular mode
        :param volume: float 0-1
        :param loops: number of loops to play (-1=forever, 0=single repeat)
        :param sampleRate: sample rate for synthesized tones
        :param blockSize: the size of the buffer on the sound card
                         (small for low latency, large for stability)
        :param bufferSize: integer to control streaming/buffering
                           - -1 means store all
                           - 0 (no buffer) means stream from disk
                           - potentially we could buffer a few secs(!?)
        :param hamming: boolean (True to smooth the onset/offset)
        :param start: for sound files this controls the start of sound snippet
        :param stop: for sound files this controls the end of sound snippet
        :param name: string for logging purposes
        :param autoLog: whether to automatically log every change
        """
        self.sound = value
        self.name = name
        self.secs = secs  # for any synthesised sounds (notesand freqs)
        self.octave = octave  # for note name sounds
        self.stereo = stereo  # TODO: force to something? currently always auto
        self.loops = loops  # TODO: should we loop this sound?
        self.hamming = hamming  # TODO: add hamming option
        self.start = start  # for files
        self.stop = stop  # for files specify thesection to be played
        self.blockSize = blockSize  # can be per-sound unlike other backends
        self.frameN = 0
        self.sampleRate = sampleRate
        self.channels = None
        self.duplex = None
        self.autoLog = autoLog
        self.streamLabel = ""
        self.sourceType = 'unknown'  # set to be file, array or freq
        # setSound (determines sound type)
        self.setSound(value)
        self.status = NOT_STARTED

    def setSound(self, value):
        """Set the sound to be played.

        Often this is not needed by the user - it is called implicitly during
        initialisation.

        :parameters:

            value: can be a number, string or an array:
                * If it's a number between 37 and 32767 then a tone will
                  be generated at that frequency in Hz.
                * It could be a string for a note ('A', 'Bfl', 'B', 'C',
                  'Csh'. ...). Then you may want to specify which octave.
                * Or a string could represent a filename in the current
                  location, or mediaLocation, or a full path combo
                * Or by giving an Nx2 numpy array of floats (-1:1) you can
                  specify the sound yourself as a waveform

            secs: duration (only relevant if the value is a note name or
                a frequency value)

            octave: is only relevant if the value is a note name.
                Middle octave of a piano is 4. Most computers won't
                output sounds in the bottom octave (1) and the top
                octave (8) is generally painful
        """
        # start with the base class method
        _SoundBase.setSound(self, value)
        # then check we have an approp stream open
        label = self.streamLabel = ("{}_{}_{}"
                .format(self.sampleRate, self.channels, self.blockSize))
        if label not in streams:
            streams[self.streamLabel] = SoundStream(
                    sampleRate=self.sampleRate,
                    channels=self.channels,
                    blockSize=self.blockSize,
                    )

    def _setSndFromFile(self, filename):
        self.soundFile = f = sf.SoundFile(filename)
        self.sourceType = 'file'
        self.sampleRate = f.samplerate
        self.channels = f.channels
        self.t = 0

    def _setSndFromFreq(self, freq, secs, hamming):
        self.freq = freq
        self.secs = secs
        self.sourceType = 'freq'
        self.t = 0
        if hamming:
            logging.warning(
                "Hamming smoothing not yet implemented for SoundDeviceSound."
                )

    def _setSndFromArray(self, array):
        pass
        # TODO: sound from array not implemented yet

    def setVolume(self, value):
        """Sets the volume (multiplies with the sound)
        """
        self.volume = value

    def play(self):
        """Start the sound playing
        """
        self.status = PLAYING
        streams[self.streamLabel].takeTimeStamp = True
        streams[self.streamLabel].add(self)

    def pause(self):
        """Stop the sound but play will continue from here if needed
        """
        self.status = PAUSED
        streams[self.streamLabel].remove(self)

    def stop(self):
        """Stop the sound and return to beginning
        """
        streams[self.streamLabel].remove(self)
        self.seek(0)
        self.status = STOPPED

    def _nextBlock(self):
        if self.sourceType == 'file':
            block = self.soundFile.read(self.blockSize)
            # TODO: check if we already finished using soundfile?
        elif self.sourceType == 'freq':
            startT = self.t
            stopT = self.t+self.blockSize/float(self.sampleRate)
            xx = np.linspace(
                start=startT*self.freq*2*np.pi,
                stop=stopT*self.freq*2*np.pi,
                num=self.blockSize, endpoint=False
                )
            block = np.sin(xx)
            # if run beyond our desired t then set to zeros
            if stopT>self.secs:
                tRange = np.linspace(startT, stopT,
                                     num=self.blockSize, endpoint=False)
                block[tRange>self.secs] == 0
                # and inform our EOS function that we finished
                self._EOS()
        self.t += self.blockSize/float(self.sampleRate)
        return block

    def seek(self, t):
        self.soundFile.seek(t)
        self.t = t

    def _EOS(self):
        """Function called on End Of Stream
        """
        streams[self.streamLabel].remove(self)
        self.status = FINISHED

    @property
    def stream(self):
        """Read-only property returns the the stream on which the sound
        will be played
        """
        important to
        return streams[self.streamLabel]

if __name__ == '__main__':
    snd = SoundDeviceSound(sound='tone440.wav', blockSize=512)
    sd.sleep(3000)

    snd.play()
    sd.sleep(2000)
    logging.info('done')
    logging.flush()