# -*- coding: utf-8 -*-
"""Audio capture and analysis using pyo"""

# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import division
import os, sys, shutil, time
from psychopy import core, logging
from psychopy.constants import NOT_STARTED

# globals are intended to allow imports within the switchOn/Off functions:
global pyoServer, haveMic
global Server, Record, Input, Clean_objects, SfPlayer, serverCreated, serverBooted
global getVersion, pa_get_input_devices, pa_get_output_devices

def switchOn():
    global haveMic
    haveMic = False
    try:
        global Server, Record, Input, Clean_objects, SfPlayer, serverCreated, serverBooted
        from pyo import Server, Record, Input, Clean_objects, SfPlayer, serverCreated, serverBooted
        global getVersion, pa_get_input_devices, pa_get_output_devices
        from pyo import getVersion, pa_get_input_devices, pa_get_output_devices
        haveMic = True
    except ImportError:
        msg = 'Microphone class not available, needs pyo; see http://code.google.com/p/pyo/'
        logging.error(msg)
        raise ImportError(msg)
    
    global pyoServer
    pyoServer = Server(sr=44100, nchnls=2, duplex=1).boot()
    pyoServer.start()

def switchOff():
    if serverBooted():
        pyoServer.stop()
        time.sleep(.25)
    if serverCreated():
        pyoServer.shutdown()


class SimpleAudioCapture():
    """Basic sound capture to .wav file using pyo.
    
    Designed to capture a sample from the default sound input, and save to a file.
    Execution will block until the recording is finished.
    
    Example:
    
        mic = SimpleAudioCapture()  # prepare to record; cannot have more than one
        mic.record(1.)  # record for 1 second, save to a file
        mic.playback()
        savedFileName = mic.savedFile
    
    Also see Builder Demo "voiceCapture"
    
    Author:
        Jeremy R. Gray, March 2012
    """
    def __init__(self, name='mic', saveDir='', rate=44100):
        """
            name : stem for output file, used in logging
            saveDir : directory to use for output .wav files (relative); '' name only
            rate : sampling rate (Hz) = 44100 (not possible to change, for now)
            return 'savedDir / name + onset-time + .wav' if savedDir was specified
            return abspath(filename) if savedDir is '': 
        """
        self.name = name
        self.saveDir = saveDir
        self.rate = int(rate) # also makes Builder component easier

        self.wavOutFilename = os.path.join(self.saveDir, name + '!ONSET_TIME_HERE!.wav')
        if not self.saveDir:
            self.wavOutFilename = os.path.abspath(self.wavOutFilename)

        self.onset = None # becomes onset time, used in filename
        self.savedFile = False # becomes saved file name if save succeeds
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
        #try:
        #    del self.sfplayer, self.sfplayer2
        #except:
            pass
    def reset(self):
        """Restores to fresh state, ready to record again"""
        logging.exp('%s: resetting at %.3f' % (self.loggingId, time.time()))
        self.__del__()
        self.__init__(name=self.name, saveDir=self.saveDir, rate=self.rate)
    def record(self, sec):
        """Capture sound input for duration <sec>, save to a file.
        
        Return the path/name to the new file. Uses onset time (epoch) as
        a meaningful identifier for filename and log.
        """
        RECORD_SECONDS = float(sec)
        self.onset = time.time() # note: report onset time in log, and use in filename
        logging.data('%s: Record: onset %.3f, ask for %.3fs' %
                     (self.loggingId, self.onset, RECORD_SECONDS) )
        
        self.savedFile = self.wavOutFilename.replace('!ONSET_TIME_HERE!', '-%.3f' % self.onset)
        inputter = Input(chnl=0, mul=1) # chnl=[0,1] for stereo input
        t0 = time.time()
        # launch the recording, saving to file:
        recorder = Record(inputter,
                        self.savedFile,
                        chnls=2,
                        fileformat=0, # .wav format
                        sampletype=0,
                        buffering=4) # 4 is default
        # block during recording and clean up:
        clean = Clean_objects(RECORD_SECONDS, recorder) # set up to stop recording
        clean.start() # the timer starts now
        time.sleep(RECORD_SECONDS - 0.0008) # Clean_objects() set-up takes ~0.0008s, for me
        self.duration = time.time() - t0 # used in playback()
        
        # prepare a player for this file:
        self.sfplayer = SfPlayer(self.savedFile, speed=1, loop=False)
        self.sfplayer2 = self.sfplayer.mix(2) # mix(2) -> 2 outputs -> 2 speakers
        self.sfplayer2.out()
        
        logging.exp('%s: Record: stop. %.3f, capture %.3fs (est)' %
                     (self.loggingId, time.time(), self.duration) )
        
        return self.savedFile # filename, or None
        
    def playback(self):
        """Plays the saved .wav file which was just recorded"""
        if not self.savedFile or not os.path.isfile(self.savedFile):
            msg = '%s: Playback requested but no saved file' % self.loggingId
            logging.error(msg)
            raise ValueError(msg)
        
        # play the file; sfplayer was created during record:
        t0 = time.time()
        self.sfplayer.play()
        time.sleep(self.duration) # set during record()
        t1 = time.time()

        logging.exp('%s: Playback: played=%.3fs (est) %s' % (self.loggingId, t1-t0, self.savedFile))


if __name__ == '__main__':
    logging.console.setLevel(logging.DEBUG) # for command-line testing

    switchOn() # import pyo, create a server
    
    #pyo_version = '.'.join(map(str, getVersion()))
    #print pa_get_input_devices()
    #print pa_get_output_devices()
    print "\nsay something:",
    sys.stdout.flush()
    
    mic = SimpleAudioCapture()
    try:
        mic.record(1) # always saves
        print
        mic.playback()
        os.remove(mic.savedFile)
        mic.reset() # just to try it out
    finally:
        switchOff()    
