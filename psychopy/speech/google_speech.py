#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Convert speech to text using Google's speech recognition API, threaded.

    Python adaptation of Lefteris Zafiris' <zaf.000@gmail.com> GPLv2 perl script
    (from https://github.com/zaf/asterisk-speech-recog)
    as a class, with thread option.
    
    Supports:
    1. Command line usage: see --help
    
    2. Python import:
    a) blocking mode (wait for response from google)
        >>> from google_speech import GoogleSpeech, gsOptions
        >>> gs = GoogleSpeech('speech_clip.wav')
        >>> resp = gs.getResponse() # waits until receive a response, or it times out
        >>> print resp.word, resp.confidence
    
    b) threaded mode (no blocking, no timeout)
        >>> from google_speech import GoogleSpeech, gsOptions
        >>> gs = GoogleSpeech('speech_clip.wav')
        >>> resp = gs.getThread() # returns immediately; no data until .running goes False
        >>> while resp.running:
        ...     time.sleep(0.1) # or do something useful
        >>> print resp.words
    
    c) using a different language, such as
      current default locale setting:
        >>> import locale
        >>> locale.setlocale(locale.LC_ALL,'') # current default
        >>> gsOptions.lang = locale.getlocale()[0]
        >>> gs = GoogleSpeech('speech_clip.wav', gsOptions)
    
      or Japanese:
        >>> gsOptions.lang = 'ja_JP'
        >>> gs = GoogleSpeech('speech_clip.wav', gsOptions)
    
    Defaults: 4 words, 16kHz, quiet=True, https, userAgent = psychopy, timeout 10s
    
    Only tested with: Win XP sp2 (python 2.6), Mac 10.6.8 (python 2.7)
"""

__version__ = "2012.04.06 (threaded)"
__author__ = 'Jeremy R. Gray'

#from psychopy import core, logging
import os, sys, time
import urllib2
import json
from optparse import OptionParser
import threading
import subprocess

# helper functions, avoid importing from psychopy:
haveCore = bool('core' in dir())

def _wait(sec, delay=0.05):
    t0 = _getTime()
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
    if not gsOptions.quiet:
        if msg.endswith(','):
            print msg.strip(','),
        else:
            print msg
        sys.stdout.flush()

def _parse_options():
    """Parse gsOptions, create version and help options."""
    parser = OptionParser(
        version = __version__,
        usage = """\n\n  Speech recognition using google speech API.

  1. Command line:
     $ python %s [options] sound-file [sound-file(s)]
  where sound-files are flac, wav, or speex (with headerbyte) format.
  wav files need flac to be installed for conversion (e.g., /usr/local/bin/flac)
    
  2. As a python import:
     $ python
     >>> from %s import GoogleSpeech, gsOptions
     >>> gsOptions.lang = 'en-UK'
     >>> gs = GoogleSpeech('speech_clip.wav', gsOptions)
     >>> resp = gs.getResponse()
     >>> print resp.words""" % (sys.argv[0], __file__.strip('.py').lstrip(os.sep)) )

    parser.add_option("-l", dest='lang', default='en-US',
                help="language to expect, e.g., en-US, en-UK, ja-JP")
    parser.add_option("-r", type='int', dest='samplingrate', default=16000,
                help="sampling rate in Hz of the sound file [16000, 8000]")
    parser.add_option("-t", type='int', dest='timeout', default=10,
                help="time to wait before returning, max seconds")
    parser.add_option("-p", type='string', dest='flac',
                default='C:\\Program Files\\FLAC\\flac.exe',
                help="for Windows: specify the path to flac")
    parser.add_option("-f", dest="pro_filter", type='int', default=2,
                help="filter profanity")
    parser.add_option("-v", action="store_false", dest="quiet", default=True,
                help="verbose")
    opt, _ = parser.parse_args()
    if not opt.samplingrate in [16000, 8000]:
        opt.samplingrate = 16000
    opt.timeout = min(opt.timeout, 30)
    return opt

global gsOptions
# more trickiness than I'd like, but does default opts for import + command-line
gsOptions = _parse_options()

if sys.platform != 'win32':
    FLAC_PATH, _ = _shellCall(['/usr/bin/which', 'flac'])
    _getTime = time.time
else:
    FLAC_PATH = gsOptions.flac
    _getTime = time.clock
    
class SoundFormatNotSupported(StandardError):
    """Class to report an unsupported sound format"""
class SoundFileError(StandardError):
    """Class to report sound file failed to load"""
    
class _GSQueryThread(threading.Thread):
    """Class thread to send a sound file to google, stash the response.
    """
    def __init__(self, request):
        threading.Thread.__init__(self, None, 'GoogleSpeechQuery', None)
        self.request = request
        self.t0 = None
        self.response = None
        self.duration = None
        self.stopflag = False
        self.running = False
        self._reset()
    def _reset(self):
        self.confidence = None
        self.json = None
        self.raw = ''
        self.word = ''
        self.detailed = ''
        self.words = []
        self.started = False # whether run() has been started, not thread start()
    def elapsed(self):
        if self.started is False:
            return None
        elif self.running:
            return _getTime() - self.t0
        else:
            return self.duration
    def _unpackRaw(self):
        # unpack data from raw
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
        self.raw = urllib2.urlopen(self.request)
        self.duration = _getTime() - self.t0
        self._unpackRaw()
        self.running = False
    def stop(self):
        self.running = False
        
class GoogleSpeech():
    """Class to manage a thread for google-speech-recognition of a sound file."""
    def __init__(self, file, opt=gsOptions):
        useragent = "PsychoPy: open-source Psychology & Neuroscience tools; www.psychopy.org"
        opt.results = 5 # how many words wanted
        self.timeout = opt.timeout
        host = "www.google.com/speech-api/v1/recognize"
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
                sys.exit("failed to find flac; if it is installed, use option -p path-to-flac")
            filetype = "x-flac"
            tmp = 'tmp_guess%.6f' % time.time()+'.flac'
            flac_cmd = [FLAC_PATH, "-8", "-f", "--totally-silent", "-o", tmp, file]
            _, se = _shellCall(flac_cmd)
            if se or not os.path.isfile(tmp):
                _message("%s failed to encode file; %s" % (opt.flac, se))
            file = tmp
        _message("Loading: %s as %s, audio/%s" % (self.file, opt.lang, filetype))
        try:
            audio = open(file, 'r+b').read()
        except:
            time.sleep(.1)
            try: # very occasional error
                audio = open(file, 'r+b').read()
            except: 
                raise SoundFileError("Can't read file %s from %s.\n" % (file, self.file))
        finally:
            try: os.remove(tmp)
            except: pass
        # set up the request:
        url = 'https://' + host + '?xjerr=1&' +\
              'client=psychopy2&' +\
              'lang=' + opt.lang +'&'\
              'pfilter=%d' % opt.pro_filter + '&'\
              'maxresults=%d' % opt.results
        header = {'Content-Type' : 'audio/%s; rate=%d' % (filetype, opt.samplingrate),
                  'User-Agent': useragent}
        # this can fail but hope to avoid errors by checking before we do this:
        self.request = urllib2.Request(url, audio, header)
    
    def getThread(self):
        """launch query without blocking, no timeout; returns a thread"""
        gsqthread = _GSQueryThread(self.request)
        gsqthread.start()
        if 'core' in dir():
            core.runningThreads.append(gsqthread)
        _message("Sending:,")
        gsqthread.file = self.file
        while not gsqthread.running:
            _wait(0.001) # can return too quickly if thread is slow to start
        return gsqthread # word and time data are in the namespace
    
    def getResponse(self):
        """launch query, execution blocks until response or timeout"""
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
        sys.exit(_shellCall(['python', sys.argv[0], '--help'])[0])
    
    for file in files:
        goosp = GoogleSpeech(file, gsOptions)
        #resp = goosp.getResponse() # blocks, will see no ... while resp.running
        resp = goosp.getThread() # non-blocking
        while resp.running and resp.elapsed() < gsOptions.timeout:
            _message('.,')
            time.sleep(0.1) # don't need precise timing to poll an http connection
        if resp.running:
            resp.status = 408
            _message('\nTimed out: %.3fs' % gsOptions.timeout)
        if resp.status:
            error = 1
        else:
            _message('\nReceived:,')
            print resp.words, resp.confidence
            _message('Required: %.3fs' % resp.duration)

    sys.exit(error)
