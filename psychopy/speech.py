#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Speech processing and analysis."""

# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

__version__ = "2012.04.08 (threaded)"
__author__ = 'Jeremy R. Gray'
# with thanks to Lefteris Zafiris and his GPLv2 command-line perl script at
# https://github.com/zaf/asterisk-speech-recog

from psychopy import core, logging
from psychopy.constants import PSYCHOPY_USERAGENT
import os, sys, time
import urllib2
import json
import threading
import subprocess

# helper functions, avoid importing from psychopy:
haveCore = bool('core' in dir())
haveLogging = bool('logging' in dir())

def _wait(sec, delay=0.05):
    t0 = _getTime() # = OS-dependent time.time()
    while _getTime() < t0 + sec:
        time.sleep(delay)
        
def _shellCall(shellCmdList):
    """Call a single system command with arguments, return its stdout.
    """
    proc = subprocess.Popen(shellCmdList, stdin=subprocess.PIPE,
                            stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    stdoutData, stderrData = proc.communicate()
    del proc
    return stdoutData.strip(), stderrData.strip()

def _message(msg):
    pass
def _warn(msg):
    if haveLogging:
        logging.warn(msg)

if sys.platform != 'win32':
    _getTime = time.time
else:
    _getTime = time.clock
    
class SoundFormatNotSupported(StandardError):
    """Class to report an unsupported sound format"""
class SoundFileError(StandardError):
    """Class to report sound file failed to load"""
    
class _GSQueryThread(threading.Thread):
    """Internal thread class to send a sound file to google, stash the response.
    """
    def __init__(self, request):
        threading.Thread.__init__(self, None, 'GoogleSpeechQuery', None)
        
        # request is a previously established urllib2.request() obj, namely:
        # request = urllib2.Request(url, audio, header) at end of GoogleSpeech.__init__
        self.request = request
        
        # set vars and flags:
        self.t0 = None
        self.response = None
        self.duration = None
        self.stopflag = False
        self.running = False
        self.timedout = False
        self._reset()
    def _reset(self):
        # whether run() has been started, not thread start():
        self.started = False 
        # initialize data fields that will be exposed:
        self.confidence = None
        self.json = None
        self.raw = ''
        self.word = ''
        self.detailed = ''
        self.words = []
    def elapsed(self):
        # report duration depending on the state of the thread:
        if self.started is False:
            return None
        elif self.running:
            return _getTime() - self.t0
        else: # whether timed-out or not:
            return self.duration
    def _unpackRaw(self):
        # parse raw string response from google, expose via data fields (see _reset):
        self.json = json.load(self.raw)
        self.status = self.json['status']
        report = []
        for utter_list in self.json["hypotheses"]:
            for k in utter_list:
                report.append("%-10s : %s" % (k, utter_list[k]))
                if k == 'confidence':
                    self.conf = self.confidence = float(utter_list[k])
        for key in self.json:
            if key != "hypotheses":
                report.append("%-10s : %s" % (key, self.json[key]))
        self.detailed = '\n'.join(report)
        self.words = tuple([line.split(':')[1].lstrip() for line in report
                        if line.startswith('utterance')])
        if len(self.words):
            self.word = self.words[0]
        else:
            self.word = ''
    def run(self):
        self.t0 = _getTime() # before .running goes True
        self.running = True
        self.started = True
        self.duration = 0
        try:
            self.raw = urllib2.urlopen(self.request)
        except: # yeah, its the internet, stuff happens
            # maybe temporary HTTPError: HTTP Error 502: Bad Gateway
            try:
                self.raw = urllib2.urlopen(self.request)
            except StandardError as ex: # or maybe a dropped connection, etc
                _message(str(ex))
                _warn(str(ex))
                self.running = False # proceeds as if "timedout"
        self.duration = _getTime() - self.t0
        # if no one called .stop() in the meantime, unpack the data:
        if self.running: 
            self._unpackRaw()
            self.running = False
            self.timedout = False
        else:
            self.timedout = True
    def stop(self):
        self.running = False
        
class GoogleSpeech2Text():
    """Class for speech-recognition (voice to text), using google's public API.
    
        Google's speech API is currently free to use, and seems to work well.
        But the big caveat: Google could start charging for usage, and
        can change the API at any time including in the middle of an experiment.
        We'll try to patch psychopy in a timely manner, but there could still be some downtime.
        And there appear to be some other options (through MIT and CMU).
            
        :Examples:
        
        a) Always import and make an object; no data are available yet:
        
            >>> from speech import GoogleSpeech2Text
            >>> gs = GoogleSpeech2Text('speech_clip.wav') # set-up only
        
        b) Initiate a query and wait for response from google, or until the time-out limit is reached ("blocking" mode, easiest):
        
            >>> resp = gs.getResponse() # execution blocks here
            >>> print resp.word, resp.confidence
        
        c) Initiate a query but do not wait for a response ("thread" mode: no blocking, no timeout, more control). `running` will change to False when a response is received (or hang indefinitely if something goes wrong--so you might want to implement a time-out as well):
        
            >>> resp = gs.getThread() # returns immediately
            >>> while resp.running:
            ...     print '.', # displays dots while waiting
            ...     sys.stdout.flush()
            ...     time.sleep(0.1)
            >>> print resp.words
        
        d) Set-up with a different language for the same speech clip; you'll get a different response (possibly having UTF-8 characters):
        
            >>> gs = GoogleSpeech2Text('speech_clip.wav', lang='ja-JP')
            >>> resp = gs.getResponse()
        
        :Other examples:
        
            Coder demo / input / say_rgb -- be sure to read the text at the top of the file.
            The demo works better when run from the command-line than from the Coder.
        
        :Known limitations:
        
            a) Subject to the whims of google. b) Only tested with: Win XP-sp2,
            Mac 10.6.8 (python 2.6, 2.7).
        
        :Author: Jeremy R. Gray, with thanks to Lefteris Zafiris for his help
            and excellent command-line perl script at https://github.com/zaf/asterisk-speech-recog (GPLv2)
    
    """
    def __init__(self, file,
                 lang='en-US',
                 timeout=10,
                 samplingrate=16000,
                 flac_exe='C:\\Program Files\\FLAC\\flac.exe',
                 pro_filter=2,
                 quiet=True):
        """
            :Parameters:
            
                file : <required>
                    name of the speech file (.flac, .wav, or .spx) to process. wav files must be
                    converted to flac, and for this to work you need to have a flac
                    executable. spx format is speex-with-headerbyte (for google).
                lang :
                    presumed language of the speaker, default 'en-US'
                timeout :
                    seconds to wait before giving up, default 10
                samplingrate :
                    the sampling rate of the speech clip in Hz, either 16000 or 8000
                flac_exe :
                    **Windows only**: path to binary for converting wav to flac;
                    must be a string with **two back-slashes where you want one** to appear
                    (this does not display correctly in web documentation auto-build, above);
                    default is 'C:\\\\\\\\Program Files\\\\\\\\FLAC\\\\\\\\flac.exe'
                pro_filter :
                    profanity filter level to send to google
                quiet :
                    intermediate-process reporting detail; default True (non-verbose)
                 
        """
        # set up some key parameters:
        results = 5 # how many words wanted
        self.timeout = timeout
        useragent = PSYCHOPY_USERAGENT # not an option
        host = "www.google.com/speech-api/v1/recognize"
        if sys.platform == 'win32':
            FLAC_PATH = flac_exe
        else:
            # best not to do every time
            FLAC_PATH, _ = _shellCall(['/usr/bin/which', 'flac'])
        
        # determine file type, convert wav to flac if needed:
        ext = os.path.splitext(file)[1]
        if not os.path.isfile(file):
            raise IOError("Cannot find file: %s" % file)
        if ext not in ['.flac', '.spx', '.wav']:
            raise SoundFormatNotSupported("Unsupported filetype: %s\n" % ext)
        self.file = file
        if ext == ".flac":
            filetype = "x-flac"
        elif ext == ".spx":
            filetype = "x-speex-with-header-byte"
        elif ext == ".wav": # convert to .flac
            if not os.path.isfile(FLAC_PATH):
                sys.exit("failed to find flac")
            filetype = "x-flac"
            tmp = 'tmp_guess%.6f' % time.time()+'.flac'
            flac_cmd = [FLAC_PATH, "-8", "-f", "--totally-silent", "-o", tmp, file]
            _, se = _shellCall(flac_cmd)
            if se: _message(se)
            while not os.path.isfile(tmp): # just try again
                # ~2% incidence when recording for 1s, 650+ trials
                # never got two in a row; time.sleep() does not help
                _message('Failed to convert to tmp.flac; trying again')
                _, se = _shellCall(flac_cmd)
                if se: _message(se)
            file = tmp # note to self: ugly & confusing to switch up like this
        _message("Loading: %s as %s, audio/%s" % (self.file, lang, filetype))
        try:
            c = 0 # occasional error; time.sleep(.1) is not always enough; better slow than fail
            while not os.path.isfile(file) and c < 10:
                time.sleep(.1)
                c += 1
            audio = open(file, 'r+b').read()
        except:
            msg = "Can't read file %s from %s.\n" % (file, self.file)
            _warn(msg)
            raise SoundFileError(msg)
        finally:
            try: os.remove(tmp)
            except: pass
        
        # set up the https request:
        url = 'https://' + host + '?xjerr=1&' +\
              'client=psychopy2&' +\
              'lang=' + lang +'&'\
              'pfilter=%d' % pro_filter + '&'\
              'maxresults=%d' % results
        header = {'Content-Type' : 'audio/%s; rate=%d' % (filetype, samplingrate),
                  'User-Agent': useragent}
        try:
            self.request = urllib2.Request(url, audio, header)
        except: # try again before accepting defeat
            _warn("https request failed. trying again..." % (file, self.file))
            time.sleep(0.2)
            self.request = urllib2.Request(url, audio, header)
    def _removeThread(self, gsqthread):
        del core.runningThreads[core.runningThreads.index(gsqthread)]
    def getThread(self):
        """Launches a query to google in its own thread, no blocking no timeout.
        
        Returns a thread which will **eventually** (not immediately) have the speech
        data in its namespace; see getResponse.
        """
        gsqthread = _GSQueryThread(self.request)
        gsqthread.start()
        core.runningThreads.append(gsqthread)
        # this is the right idea, but need to .cancel() it when a response has come:
        #threading.Timer(self.timeout, self._removeThread, (gsqthread,)).start()
        _message("Sending:,")
        gsqthread.file = self.file
        while not gsqthread.running:
            _wait(0.001) # can return too quickly if thread is slow to start
        return gsqthread # word and time data will eventually be in the namespace
    
    def getResponse(self):
        """Calls getThread, and then polls the thread to see if there's been a response.
        
        Will time-out if no response within `timeout` seconds. Returns an object
        having the speech data in its namespace. If there's no
        match, generally the values will be `None` or `''`.
        
        :Namespace:
        
            .word :
                the best word
            .words :
                tuple of word-guesses returned by google
            .confidence :
                google's confidence about the best word
            .raw :
                the raw response from google (string)
            .json :
                the interpreted version of raw (from json.load(raw))
        """
        gsqthread = self.getThread()
        while gsqthread.elapsed() < self.timeout:
            time.sleep(0.1) # don't need precise timing to poll an http connection
            if not gsqthread.running:
                break
        if gsqthread.running: # timed out
            gsqthread.status = 408 # same as http code
        return gsqthread # word and time data are already in the namespace


if __name__ == "__main__":
    error = 0
    files = [f for f in sys.argv if f[-4:] in ['flac', '.spx', '.wav']]
    if len(sys.argv) == 1 or not len(files):
        sys.exit("Requires some sound file names as parameters: .flac, .wav, or .spx")
    
    print 'Options are ignored.'
    for file in files:
        goosp = GoogleSpeech2Text(file)
        #resp = goosp.getResponse() # blocks, will see no ... while resp.running
        resp = goosp.getThread() # non-blocking
        while resp.running and resp.elapsed() < 5: # timeout of 5 here
            print '.',
            sys.stdout.flush()
            time.sleep(0.1) # don't need precise timing to poll an http connection
        if resp.running: # timed out
            resp.status = 408
            resp.stop()
            _message('\nTimed out: %.3fs' % gsOptions.timeout)
        if resp.status:
            error = 1
        else:
            _message('\nReceived:,')
            print resp.words, resp.confidence
            _message('Required: %.3fs' % resp.duration)

    sys.exit(error)
