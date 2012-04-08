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
# idea: don't want to delay up to 3 sec when importing microphone
# downside: to make this work requires some trickiness with globals

__author__ = 'Jeremy R. Gray'

ONSET_TIME_HERE = '!ONSET_TIME_HERE!'

global haveMic
haveMic = False # goes True in switchOn, if can import pyo; goes False in switchOff

class _GlobalRecordingThread(threading.Thread):
    """Class for internal thread to get an audio recording using pyo, with greater stability.
    
    Never needed by end-users. Used internally in switchOn():
        global _theGlobalRecordingThread
        _theGlobalRecordingThread = _GlobalRecordingThread(None) # instantiate, global
    Then in SimpleAudioCapture.record(), do:
        _theGlobalRecordingThread.rec(file, sec)
    This sets recording parameters, starts recording, arranges for thread signaling
    The global thread never handles blocking; SimpleAudioCapture has to do that.
    
    Motivation: Doing pyo Record from within a function worked most of the time,
    but failed catastrophically ~1% of time with a bus error. Seemed to be due to
    a namespace scoping issue, which using globals seemed to fix; see pyo mailing
    list, 7 April 2012.
    """
    def __init__(self, file, sec=0):
        threading.Thread.__init__(self, None, '_pyoRecordingThread', None)
        self.running = False
        # hack to avoid occasional seg fault / bus-error, try 2-step:
        # 1) pass file=None to create a global thread; no recording or tmp file
        # 2) call self.rec(file, sec) to reinitialize with actual values to use, then start recording
        if file: # part of the hack to dodge occasional seg fault from pyo
            self.sec = sec
            self.file = file
            inputter = Input(chnl=0, mul=1)
            recorder = Record(inputter,
                            self.file,
                            chnls=2,
                            fileformat=0, # .wav
                            sampletype=0,
                            buffering=4)
            self.clean = Clean_objects(self.sec, recorder)
    def run(self):
        self.running = True
        core.runningThreads.append(self)
        self.clean.start() # launch the recording; this will record for duration self.sec regardless of blocking
        # don't core.wait() here; manage all blocking outside the thread
        threading.Timer(self.sec, self.stop, ()).start() # idea: set .running=False after delay; not tested
        threading.Timer(self.sec, self.remove, ()).start() # not tested
    def rec(self, file, sec):
        # part of the hack to dodge occasional seg fault from pyo
        self.__init__(file, sec)
        self.start() # calls self.run()
    def stop(self):
        self.running = False
    def remove(self):
        del core.runningThreads[core.runningThreads.index(self)]

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
        logging.exp('%s: resetting at %.3f' % (self.loggingId, core.getTime()))
        self.__del__()
        self.__init__(name=self.name, saveDir=self.saveDir)
    def record(self, sec, file='', block=True):
        """Capture sound input for duration <sec>, save to a file.
        
        Return the path/name to the new file. Uses onset time (epoch) as
        a meaningful identifier for filename and log.
        """
        while _theGlobalRecordingThread.running:
            pass # prevents start of recording until previous has finished; bad: get inf loop if previous record was not shut down cleanly!
        self.duration = float(sec)
        self.onset = core.getTime() # note: report onset time in log, and use in filename
        logging.data('%s: Record: onset %.3f, capture %.3fs' %
                     (self.loggingId, self.onset, self.duration) )
        if not file:
            self.savedFile = self.wavOutFilename.replace(ONSET_TIME_HERE, '-%.3f' % self.onset)
        else:
            self.savedFile = os.path.abspath(file).strip('.wav')+'.wav'
        
        t0 = core.getTime()
        _theGlobalRecordingThread.rec(self.savedFile, self.duration)
        
        if block:
            core.wait(self.duration - .0008) # .0008 fudge factor for better reporting
                # NOTE: the actual recording time is done by Clean_object in _recordingThread()
            logging.exp('%s: Record: stop. %.3f, capture %.3fs (est)' %
                     (self.loggingId, core.getTime(), core.getTime() - t0) )
        else:
            logging.exp('%s: Record: return immediately, no blocking' %
                     (self.loggingId) )

        return self.savedFile
    
    def playback(self):
        """Plays the saved .wav file which was just recorded
        """
        if not self.savedFile or not os.path.isfile(self.savedFile):
            msg = '%s: Playback requested but no saved file' % self.loggingId
            logging.error(msg)
            raise ValueError(msg)
    
        # prepare a player for this file:
        t0 = core.getTime()
        self.sfplayer = SfPlayer(self.savedFile, speed=1, loop=False)
        self.sfplayer2 = self.sfplayer.mix(2) # mix(2) -> 2 outputs -> 2 speakers
        self.sfplayer2.out()
        logging.exp('%s: Playback: prep %.3fs' % (self.loggingId, core.getTime()-t0))

        # play the file; sfplayer was created during record:
        t0 = core.getTime()
        self.sfplayer.play()
        core.wait(self.duration) # set during record()
        t1 = core.getTime()

        logging.exp('%s: Playback: play %.3fs (est) %s' % (self.loggingId, t1-t0, self.savedFile))

def switchOn(sampleRate=44100):
    """You need to switch on the microphone before use. Can take several seconds.
    """
    # imports from pyo, creates globals pyoServer and _theGlobalRecordingThread

    t0 = core.getTime()
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
    
    global pyoServer
    if serverCreated():
        pyoServer.setSamplingRate(sampleRate)
        pyoServer.boot()
    else:
        pyoServer = Server(sr=sampleRate, nchnls=2, duplex=1).boot()
    pyoServer.start()
    
    global _theGlobalRecordingThread  # idea: use a global var for better pyo stability
    _theGlobalRecordingThread = _GlobalRecordingThread(None) # instantiate, no temp file
    
    logging.exp('%s: switch on (%dhz) took %.3fs' % (__file__.strip('.py'), sampleRate, core.getTime() - t0))
    
def switchOff():
    """Must explicitly switch off the microphone when done to avoid a seg fault.
    """
    t0 = core.getTime()
    
    global haveMic
    haveMic = False
    
    global _theGlobalRecordingThread
    del _theGlobalRecordingThread
    
    global pyoServer
    if serverBooted():
        pyoServer.stop()
        core.wait(.25) # give it a chance to stop before shutdown(), avoid seg fault
    if serverCreated():
        pyoServer.shutdown()
    
    logging.exp('%s: switch off took %.3fs' % (__file__.strip('.py'), core.getTime() - t0))

if __name__ == '__main__':
    print ('\nMicrophone command-line testing\n')
    core.checkPygletDuringWait = False # don't dispatch events during a wait
    logging.console.setLevel(logging.DEBUG)
    switchOn()
    switchOff()
    switchOn(16000) # import pyo, create a server
    print ('\nsuccessful switchOn, Off, and back On.')
    try:
        mic = SimpleAudioCapture()
        if len(sys.argv) > 1: # stability test using argv[1] iterations
            for i in xrange(int(sys.argv[1])): 
                print i, mic.record(.5)
                os.remove(mic.savedFile)
        else: # interactive playback test
            testDuration = 2
            raw_input('testing record and playback, press <return> to start: ')
            print "say something:",
            sys.stdout.flush()
            mic.record(testDuration, block=False) # block False returns immediately
            core.wait(testDuration) # you need testDuration in record and core.wait
            print
            print 'record done; sleeping 1s'
            sys.stdout.flush()
            core.wait(1)
            print 'start playback ',
            sys.stdout.flush()
            mic.playback()
            print 'end.', mic.savedFile
            sys.stdout.flush()
            os.remove(mic.savedFile)
            mic.reset()
            raw_input('<ret> for another: ')
            print "say something else:",
            sys.stdout.flush()
            mic.record(testDuration, file='m') # block=True by default; here use explicit file name
            
            mic.playback()
            print mic.savedFile
            os.remove(mic.savedFile)
    finally:
        switchOff()
