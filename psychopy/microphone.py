# -*- coding: utf-8 -*-
"""Audio capture and analysis using pyo"""

# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import division
import os, sys, shutil, time
import threading
import tempfile
from psychopy import core, logging
from psychopy.constants import NOT_STARTED
# import pyo is done within switchOn/Off to better encapsulate it, because it can be very slow
# don't want to delay 3 sec when importing microphone
# to make this work requires some trickiness with globals, not ideal

__author__ = 'Jeremy R. Gray'

ONSET_TIME_HERE = '!ONSET_TIME_HERE!'

global haveMic
haveMic = False # goes True in switchOn, if can import pyo

class _pyoRecordingThread(threading.Thread):
    """Class for internal thread to get an audio recording using pyo.
    
    used in switchOn():
        global _record
        _record = _RecordingThread(None)
    in SimpleAudioCapture.record() do:
        _record.rec(file, sec)
    and then ensure the appropriate delay (blocking, if any).
    
    Motivation: doing pyo Record from within a function worked most of the
    time, but failed catastrophically ~1% with a bus error / seg fault. Seemed
    to be due to a namespace issue. see pyo mailing list, 7 April 2012.
    """
    def __init__(self, file, sec=2):
        threading.Thread.__init__(self, None, '_pyoRecordingThread', None)
        self.running = False
        self.stopFlag = False
        self.sec = sec
        if file:
            self.file = file
            inputter = Input(chnl=0, mul=1)
            recorder = Record(inputter,
                            self.file,
                            chnls=2,
                            fileformat=0,
                            sampletype=0,
                            buffering=4)
            self.clean = Clean_objects(self.sec, recorder)
    def run(self):
        self.running = True
        self.clean.start()
        time.sleep(self.sec)
        self.running = False
    def rec(self, file, sec=2):
        self.__init__(file, sec)
        self.run()
    def stop(self):
        self.running = False
        self.stopFlag = True

class SimpleAudioCapture():
    """Capture a sound sample from the default sound input, and save to a file.
        
        Execution will block until the recording is finished.
        
        **Example**::
        
            from psychopy import microphone
            
            microphone.switchOn(sampleRate=16000) # do once when starting, can take 2-3s
            
            mic = microphone.SimpleAudioCapture()  # prepare to record; only one can be active
            mic.record(1)  # record for 1.000 seconds, save to a file
            mic.playback()
            savedFileName = mic.savedFile
            
            microphone.switchOff() # do once, at exit 
        
        Also see Builder Demo "voiceCapture"
            
        :Author: Jeremy R. Gray, March 2012
    """ 
    def __init__(self, name='mic', file='', saveDir=''):
        """
        :Parameters:
                name :
                    Stem for the output file, also used in logging.
                file :
                    optional file name to use; default = 'name-onsetTimeEpoch.wav'
                saveDir :
                    Directory to use for output .wav files.
                    If a saveDir is given, it will return 'saveDir/file'. 
                    If no saveDir, then return abspath(file)
        """
        self.name = name
        self.saveDir = saveDir
        if file:
            self.wavOutFilename = file
        else:
            self.wavOutFilename = os.path.join(self.saveDir, name + ONSET_TIME_HERE +'.wav')
        if not self.saveDir:
            self.wavOutFilename = os.path.abspath(self.wavOutFilename)

        self.onset = None # becomes onset time, used in filename
        self.savedFile = False # becomes saved file name
        self.status = NOT_STARTED # for Builder component
        
        # pyo server good to go? 
        if not serverCreated():
            raise AttributeError('pyo server not created')
        if not serverBooted():
            raise AttributeError('pyo server not booted')
        
        self.loggingId = self.__class__.__name__
        if self.name:
            self.loggingId += ' ' + self.name

    def __del__(self):
        pass
    def reset(self):
        """Restores to fresh state, ready to record again"""
        logging.exp('%s: resetting at %.3f' % (self.loggingId, time.time()))
        self.__del__()
        self.__init__(name=self.name, saveDir=self.saveDir)
    def record(self, sec, file='', block=True):
        """Capture sound input for duration <sec>, save to a file.
        
        Return the path/name to the new file. Uses onset time (epoch) as
        a meaningful identifier for filename and log.
        """
        self.duration = float(sec)
        self.onset = time.time() # note: report onset time in log, and use in filename
        logging.data('%s: Record: onset %.3f, capture %.3fs' %
                     (self.loggingId, self.onset, self.duration) )
        if not file:
            self.savedFile = self.wavOutFilename.replace(ONSET_TIME_HERE, '-%.3f' % self.onset)
        else:
            self.savedFile = os.path.abspath(file).strip('.wav')+'.wav'
            
        t0 = time.time()
        _record.rec(self.savedFile, self.duration)
        
        if block:
            time.sleep(self.duration - 0.0008) # Clean_objects() set-up takes ~0.0008s, for me
            logging.exp('%s: Record: stop. %.3f, capture %.3fs (est)' %
                     (self.loggingId, time.time(), time.time() - t0) )
        else:
            logging.exp('%s: Record: return immediately, no blocking' %
                     (self.loggingId) )

        return self.savedFile # filename, or None
        
    def playback(self):
        """Plays the saved .wav file which was just recorded
        """
        if not self.savedFile or not os.path.isfile(self.savedFile):
            msg = '%s: Playback requested but no saved file' % self.loggingId
            logging.error(msg)
            raise ValueError(msg)
    
        # prepare a player for this file:
        t0 = time.time()
        self.sfplayer = SfPlayer(self.savedFile, speed=1, loop=False)
        self.sfplayer2 = self.sfplayer.mix(2) # mix(2) -> 2 outputs -> 2 speakers
        self.sfplayer2.out()
        logging.exp('%s: Playback: prep %.3fs' % (self.loggingId, time.time()-t0))

        # play the file; sfplayer was created during record:
        t0 = time.time()
        self.sfplayer.play()
        time.sleep(self.duration) # set during record()
        t1 = time.time()

        logging.exp('%s: Playback: play %.3fs (est) %s' % (self.loggingId, t1-t0, self.savedFile))

def switchOn(sampleRate=44100):
    """You need to switch on the microphone before use. Can take several seconds.
    """
    # imports from pyo, creates globals including pyoServer and pyoSamplingRate

    t0 = time.time()
    try:
        global Server, Record, Input, Clean_objects, SfPlayer, serverCreated, serverBooted
        from pyo import Server, Record, Input, Clean_objects, SfPlayer, serverCreated, serverBooted
        global getVersion, pa_get_input_devices, pa_get_output_devices
        from pyo import getVersion, pa_get_input_devices, pa_get_output_devices
        global haveMic
        haveMic = True
    except ImportError:
        msg = 'Microphone class not available, needs pyo; see http://code.google.com/p/pyo/'
        logging.error(msg)
        raise ImportError(msg)
    
    global pyoSamplingRate
    pyoSamplingRate = sampleRate
    global pyoServer
    if serverCreated():
        pyoServer.setSamplingRate(sampleRate)
        pyoServer.boot()
    else:
        pyoServer = Server(sr=sampleRate, nchnls=2, duplex=1).boot()
    pyoServer.start()

    global _record
    _record = _pyoRecordingThread(None) # used in SimpleAudioCapture.record()
    core.runningThreads.append(_record)
    
    logging.exp('%s: switch on (%dhz) took %.3fs' % (__file__.strip('.py'), sampleRate, time.time() - t0))
    
def switchOff():
    """Must explicitly switch off the microphone when done.
    """
    global haveMic
    haveMic = False
    t0 = time.time()
    global pyoServer, pyoSamplingRate
    if serverBooted():
        pyoServer.stop()
        time.sleep(.25) # give it a chance to stop before shutdown()
    if serverCreated():
        pyoServer.shutdown()
    global _record
    del core.runningThreads[core.runningThreads.index(_record)]
    del _record
    logging.exp('%s: switch off took %.3fs' % (__file__.strip('.py'), time.time() - t0))

if __name__ == '__main__':
    logging.console.setLevel(logging.DEBUG) # for command-line testing

    switchOn(sampleRate=16000) # import pyo, create a server
    try:
        mic = SimpleAudioCapture()
        '''for i in xrange(1000): # stability test
            print i, mic.record(1)
            os.remove(mic.savedFile)
        '''
        raw_input('\npress <return> to start: ')
        print "say something:",
        sys.stdout.flush()
        mic.record(1, block=False) # always saves
        print
        time.sleep(1)
        print 'record done; sleep 1s'
        sys.stdout.flush()
        time.sleep(1)
        print 'start playback',
        sys.stdout.flush()
        mic.playback()
        print 'end.', mic.savedFile
        os.remove(mic.savedFile)
        mic.reset()
        raw_input('<ret> for another: ')
        print "say something else:",
        sys.stdout.flush()
        mic.record(1, file='m', block=True)
        mic.playback()
        print mic.savedFile
        os.remove(mic.savedFile)
    finally:
        switchOff()
