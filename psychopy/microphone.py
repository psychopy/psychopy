# -*- coding: utf-8 -*-
"""Audio capture and analysis"""

# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import division
import os, sys, shutil
from tempfile import mkdtemp
import numpy as np
import threading, time
from psychopy import core, logging
from psychopy.constants import NOT_STARTED

try:
    import pyaudio, wave, audioop
    haveMic = True
except:
    haveMic = False
    msg = 'Microphone class(es) not available; need pyaudio, audioop, wave'
    logging.error(msg)
    raise ImportError(msg)

def _stats(data):
    return audioop.rms(data, 2), audioop.cross(data, 2)


class SimpleAudioCapture():
    """Basic sound capture to .wav file using pyaudio.
    
    Designed to capture a sample from the default sound input, and save to a file.
    Execution will block until the recording is finished. Recording times are
    approximate, but aim to be within half a visual frame. A warning is generated
    if they go longer, and all are saved into the log file.
    
    Example:
    
        mic = SimpleAudioCapture()  # prepare to record; cannot have more than one
        mic.record(1.23)  # record for 1.23s, save to a file
        
        mic.playback()
        savedFileName = mic.savedFile
        loudness = mic.rms
        
        # plot all data against time in sec, based on sampling rate:
        d = np.frombuffer(mic.allData, np.int16)
        t = np.array([float(i)/mic.RATE for i in range(len(d))])
        pyplot.plot(t, d, 'k')
        pyplot.show() # or pyplot.savefig('plot.png')
    
    Also see Builder Demo "voiceCapture"
    
    Note:
    
        The first stream access is very slow (up to 1.1s read, 0.5s write), so this
        is automatically done on import. Subsequent access times are ~4 ms (if
        done immediately, might fall asleep again at some point).
    
    Author:
        Jeremy R. Gray, March 2012
    """
    def __init__(self, name='mic', saveDir='', rate=22050, chunk=150, warn=0.008):
        """
            name : stem for output file, used in logging
            saveDir : directory to use for output .wav files (relative); '' name only
            rate : sampling rate (Hz)
            chunk: sampling size
            warn : threshold in s at which to warn about a slow init or save
            return 'savedDir / name + onset-time + .wav' if savedDir was specified
            return abspath(filename) if savedDir is '': 
        """
        t0 = time.time()
        self.status = NOT_STARTED # for Builder component
        self.RATE = int(rate) # also makes Builder component easier
        self.FORMAT = pyaudio.paInt16
        self.width = 2 # for pyaudio.paInt16
        self.CHANNELS = 1 # mono
        self.chunk = chunk # smaller = more precise offset timing
        self.name = name
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(format=self.FORMAT, channels=self.CHANNELS,
                        rate=self.RATE, input=True, frames_per_buffer=self.chunk)
        self.initTimeReq = (time.time()-t0)
        self.warn = warn
        self.loggingId = self.__class__.__name__
        self.missCount = 0
        self.hitCount = 0
        self.rms = None
        if self.warn is False: # special value, only used during module import
            name = '_init_' # for logging
            logging.debug('%s %s: wake-up on import took %.3fs' % (
                            self.loggingId, name, self.initTimeReq) )
        if name: # add after module import
            self.loggingId += ' ' + name
        self.latency = self.stream.get_input_latency()
        if self.latency and warn:
            logging.warning('%s: non-zero input latency %.3f' %
                            (self.loggingId, self.latency))
        
        self.onset = None # becomes onset time, used in filename
        self.saveDir = saveDir
        self.wavOutFilename = os.path.join(self.saveDir, name + '!ONSET_TIME_HERE!.wav')
        if not saveDir:
            self.wavOutFilename = os.path.abspath(self.wavOutFilename)
        self.savedFile = False # becomes saved file name if save succeeds
        
        if warn: warnMsg = '= LONG, warning suppressed'
        else: warnMsg = ''
        if self.initTimeReq > 0.006 and warn:
            logging.warning('%s: init at %.3f, took %.3f SLOW %s' %
                            (self.loggingId, t0, self.initTimeReq, warnMsg) )
        elif self.warn:
            logging.exp('%s: init at %.3f, took %.3f' %
                        (self.loggingId, t0, self.initTimeReq) )
    def __del__(self):
        try: self._close()
        except: pass
    def _close(self):
        """clean up, can take 0.3s"""
        self.stream.close()
        self.pa.terminate()
        try: del self.stream # release access to system hardware?
        except: pass
        try: del self.pa
        except: pass
    def _rms(self, data):
        """return RMS of data, as a loudness index"""
        try:
            return audioop.rms(data, self.width)
        except:
            pass
    def _stream_read(self, chunk):
        """sometimes get IOError very quickly, so just try again asap
        needs more testing of how much info is lost when there's an IOError"""
        t0 = time.time()
        try:
            data = self.stream.read(chunk)
            self.hitCount += chunk
            return data
        except IOError: # eg: [Errno Input overflowed] -9981
            if time.time() - t0 < .001: # should base time on rate & chunk
                try:
                    data = self.stream.read(chunk)
                    self.hitCount += chunk
                    return data
                except IOError: # eg: [Errno Input overflowed] -9981
                    pass
        # count as a miss if second read is also bad, or if first took too long
        samples = int((time.time() - t0) / self.RATE)
        logging.data('%s: stream.read failed at %.3f; using "\\0\\0" * %d' %
                     (self.loggingId, time.time(), samples ) )
        self.missCount += samples
        return '\0\0' * samples
    def record(self, sec, save=True):
        """Capture sound input for sec as self.allData, optional save to a file.
        
        Default is to save and return the path/name. Uses onset time (epoch) as
        a meaningful identifier for filename and log.
        """
        t0 = time.time()
        self.RECORD_SECONDS = float(sec)
        self.onset = time.time() # note: report onset time in log, and use in filename
        if self.warn is not False:
            logging.exp('%s: record onset at %.3f (ask for %.3fs, chunksize %s)' %
                         (self.loggingId, self.onset, self.RECORD_SECONDS, self.chunk) )
        
        # record: idea = for loop for speed; while loop to catch the end more precisely:
        all = []
        t0 = time.time()
        numChunks = -1 + int(self.RECORD_SECONDS * self.RATE / self.chunk)
        for i in xrange( numChunks ):
            all.append(self._stream_read(self.chunk))    
        while time.time() <= t0 + self.RECORD_SECONDS: 
            all.append(self._stream_read(self.chunk))
        self.recordTime = time.time() - t0
        samples = self.missCount + self.hitCount
        
        self.allData = ''.join(all)
        
        if self.warn is not False:
            logging.exp('%s: record stop  at %.3f (capture %.3fs, %d samples)' %
                     (self.loggingId, time.time(), self.recordTime, samples) )
            self.rms = self._rms(self.allData)
            logging.data('%s: RMS = %d (%d samples, onset=%.3f)' %
                         (self.loggingId, self.rms, samples, self.onset) )
        
        if save:
            self._save(all) # set self.savedFile
        else:
            self.savedFile = None
        self._close()
        return self.savedFile # filename, or None
        
    def _save(self, all):
        """Write data to .wav, include onset epoch in file name; return the path/name."""
        t0 = time.time()
        filename = self.wavOutFilename.replace('!ONSET_TIME_HERE!', '-%.3f' % self.onset)
        try:
            wf = wave.open(filename, 'wb')
            wf.setnchannels(self.CHANNELS)
            wf.setsampwidth(self.pa.get_sample_size(self.FORMAT))
            wf.setframerate(self.RATE)
            wf.writeframes(''.join(all))
            wf.close()
            self.savedFile = filename
        except:
            logging.error('%s: failed to save file %s' % (self.loggingId, filename))
            return None
            
        self.saveTime = time.time() - t0
        if self.warn is False:
            logging.debug('%s: save to file took %.3f' % (self.loggingId, self.saveTime))
            return
        if self.saveTime > self.warn:
            logging.warning('%s: save to file took %.3f SLOW, file=%s' %
                            (self.loggingId, self.saveTime, filename))
        else:
            logging.exp('%s: save to file took %.3f, file=%s' %
                        (self.loggingId, self.saveTime, filename))
        return filename

    def playback(self):
        """Plays the saved .wav file"""
        
        if not self.savedFile or not os.path.isfile(self.savedFile):
            msg = '%s: playback requested but no saved file' % self.loggingId
            logging.error(msg)
            raise ValueError(msg)
        t0 = time.time()
        wf = wave.open(self.savedFile, 'rb')
        self.pa = pyaudio.PyAudio()
        self.stream = self.pa.open(
                format=self.pa.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(), rate=wf.getframerate(), output=True)
        
        # play stream:
        t1 = time.time()
        data = wf.readframes(self.chunk)
        while data != '':
            self.stream.write(data)
            data = wf.readframes(self.chunk)
        t2 = time.time()
        self._close() # can be 0.3s
        if self.warn is False:
            logging.debug('%s: playback: stream open=%.3f' % (self.loggingId, t1-t0))
        else:
            logging.exp('%s: playback: stream open=%.3f, play=%.3f' % (self.loggingId, t1-t0, t2-t1))

if __name__ == '__main__':
    logging.console.setLevel(logging.DEBUG)
    
# the first pyaudio stream access is very slow, so do it on module import:
_tmp = mkdtemp()
try:
    _tmpMic = SimpleAudioCapture(saveDir=_tmp, warn=False)
    _tmpRec = _tmpMic.record(sec=.001)
    _tmpMic.playback() # wake up the output as well
    del _tmpMic
finally:
    shutil.rmtree(_tmp)

if __name__ == '__main__':
    for i in range(1):  # to show timing stats for first and second pass
        mic = SimpleAudioCapture()
        print "say something:"
        sys.stdout.flush()
        mic.record(2, save=False) # record, no file but keeps .allData
        print _stats(mic.allData)
        
    