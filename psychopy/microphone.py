# -*- coding: utf-8 -*-
"""Audio capture and analysis using pyo"""

# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# Author: Jeremy R. Gray, March 2012

from __future__ import division
import os, sys, shutil, time
import threading, urllib2, json
import tempfile, glob
from psychopy import core, logging
from psychopy.constants import NOT_STARTED, PSYCHOPY_USERAGENT
# import pyo is done within switchOn/Off to better encapsulate it, because it can be very slow
# idea: don't want to delay up to 3 sec when importing microphone
# downside: to make this work requires some trickiness with globals

global haveMic
haveMic = False # goes True in switchOn, if can import pyo; goes False in switchOff


class AudioCapture(object):
    """Capture a sound sample from the default sound input, and save to a file.
        
        Untested whether you can have two recordings going on simultaneously.
        
        **Examples**::
        
            from psychopy import microphone
            from psychopy import event, visual  # for key events
            
            microphone.switchOn(sampleRate=16000)  # do once
            
            # Record for 1.000 seconds, save to mic.savedFile
            mic = microphone.AudioCapture()
            mic.record(1)
            mic.playback()
            
            # Resample, creates a new file discards orig
            mic.resample(48000, keep=False)
            
            # Record new file for 60 sec or until key 'q'
            w = visual.Window()  # needed for key-events
            mic.reset()
            mic.record(60, block=False)
            while mic.recorder.running:
                if 'q' in event.getKeys():
                    mic.stop()
            
            microphone.switchOff()  # do once 
        
        Also see Builder Demo "voiceCapture".
            
        :Author: Jeremy R. Gray, March 2012
    """
    
    class _Recorder(object):
        """Class for internal object to make an audio recording using pyo.
        
        Never needed by end-users; only used internally in __init__:
            self.recorder = _Recorder(None) # instantiate, global
        Then in record(), do:
            self.recorder.run(file, sec)
        This sets recording parameters, starts recording.
        To stop a recording that is in progress, do
            self.stop()
        This class never handles blocking; AudioCapture has to do that.
        
        Motivation: Doing pyo Record from within a function worked most of the time,
        but failed catastrophically ~1% of time with a bus error. Seemed to be due to
        a namespace scoping issue, which using globals seemed to fix; see pyo mailing
        list, 7 April 2012. This draws heavily on Olivier Belanger's solution.
        """
        def __init__(self, file, sec=0, sampletype=0):
            self.running = False
            if file:
                inputter = Input(chnl=0, mul=1)
                self.recorder = Record(inputter,
                               file,
                               chnls=2,
                               fileformat=0,
                               sampletype=sampletype,
                               buffering=4)
                self.clean = Clean_objects(sec, self.recorder)
        def run(self, file, sec, sampletype):
            self.__init__(file, sec, sampletype)
            self.running = True
            self.clean.start() # controls recording onset (now) and offset (later)
            threading.Timer(sec, self._stop).start() # set running flag False
        def stop(self):
            self.recorder.stop()
            self._stop()
        def _stop(self):
            self.running = False
            
    def __init__(self, name='mic', file='', saveDir='', sampletype=0):
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
            sampletype : bit depth
                pyo recording option: 0=16 bits int, 1=24 bits int; 2=32 bits int
        """
        self.name = name
        self.saveDir = saveDir
        if file:
            self.wavOutFilename = file
        else:
            self.wavOutFilename = os.path.join(self.saveDir, name + '.wav')
        if not self.saveDir:
            self.wavOutFilename = os.path.abspath(self.wavOutFilename)
        else:
            if not os.path.isdir(self.saveDir):
                os.makedirs(self.saveDir, 0770)

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
        
        # the recorder object needs to persist, or else get bus errors:
        self.recorder = self._Recorder(None)
        self.sampletype = sampletype # pass through .run()

    def __del__(self):
        pass
    def stop(self):
        """Interrupt a recording that is in progress; close & keep the file.
        
        Ends the recording before the duration that was initially specified. The
        same file name is retained, with the same onset time but a shorter duration.
        
        The same recording cannot be resumed after a stop (it is not a pause),
        but you can start a new one.
        """
        if not self.recorder.running:
            logging.exp('%s: Stop requested, but no record() in progress' % self.loggingId )
            return
        self.duration = core.getTime() - self.onset  # new shorter duration
        self.recorder.stop()
        logging.data('%s: Record stopped early, new duration %.3fs' % (self.loggingId, self.duration))

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
        while self.recorder.running:
            pass
        self.duration = float(sec)
        self.onset = core.getTime() # note: report onset time in log, and use in filename
        logging.data('%s: Record: onset %.3f, capture %.3fs' %
                     (self.loggingId, self.onset, self.duration) )
        if not file:
            onsettime = '-%.3f' % self.onset
            self.savedFile = onsettime.join(os.path.splitext(self.wavOutFilename))
        else:
            self.savedFile = os.path.abspath(file).strip('.wav') + '.wav'
        
        t0 = core.getTime()
        self.recorder.run(self.savedFile, self.duration, self.sampletype)
        self.rate = pyoServer.getSamplingRate()
        
        if block:
            core.wait(self.duration - .0008) # .0008 fudge factor for better reporting
                # actual timing is done by Clean_objects
            logging.exp('%s: Record: stop. %.3f, capture %.3fs (est)' %
                     (self.loggingId, core.getTime(), core.getTime() - t0) )
        else:
            logging.exp('%s: Record: return immediately, no blocking' %
                     (self.loggingId) )

        return self.savedFile
    
    def playback(self):
        """Plays the saved .wav file, as just recorded or resampled
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
    
    def resample(self, newRate=16000, keep=True):
        """Re-sample the saved file to a new rate, return the full path.
        
        Can take several visual frames to resample a 2s recording.
        
        The default values for resample() are for google-speech, keeping the
        original (presumably recorded at 48kHz) to archive.
        A warning is generated if the new rate not an integer factor / multiple of the old rate.
        
        To control anti-aliasing, use pyo.downsamp() or upsamp() directly.
        """
        if not self.savedFile or not os.path.isfile(self.savedFile):
            msg = '%s: Re-sample requested but no saved file' % self.loggingId
            logging.error(msg)
            raise ValueError(msg)
        if newRate <= 0 or type(newRate) != int:
            msg = '%s: Re-sample bad new rate = %s' % (self.loggingId, repr(newRate))
            logging.error(msg)
            raise ValueError(msg)
        
        # set-up:
        if self.rate >= newRate:
            ratio = float(self.rate) / newRate
            info = '-ds%i' % ratio
        else:
            ratio = float(newRate) / self.rate
            info = '-us%i' % ratio
        if ratio != int(ratio):
            logging.warn('%s: old rate is not an integer factor of new rate'% self.loggingId)
        ratio = int(ratio)
        newFile = info.join(os.path.splitext(self.savedFile))
        
        # use pyo's downsamp or upsamp based on relative rates:
        if not ratio:
            logging.warn('%s: Re-sample by %sx is undefined, skipping' % (self.loggingId, str(ratio)))
        elif self.rate >= newRate:
            t0 = time.time()
            downsamp(self.savedFile, newFile, ratio) # default 128-sample anti-aliasing
            logging.exp('%s: Down-sampled %sx in %.3fs to %s' % (self.loggingId, str(ratio), time.time()-t0, newFile))
        else:
            t0 = time.time()
            upsamp(self.savedFile, newFile, ratio) # default 128-sample anti-aliasing
            logging.exp('%s: Up-sampled %sx in %.3fs to %s' % (self.loggingId, str(ratio), time.time()-t0, newFile))    
            
        # clean-up:
        if not keep:
            os.unlink(self.savedFile)
            self.savedFile = newFile
            self.rate = newRate
        
        return os.path.abspath(newFile)
    
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
            return core.getTime() - self.t0
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
        self.t0 = core.getTime() # before .running goes True
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
                logging.error(str(ex))
                self.running = False # proceeds as if "timedout"
        self.duration = core.getTime() - self.t0
        # if no one called .stop() in the meantime, unpack the data:
        if self.running: 
            self._unpackRaw()
            self.running = False
            self.timedout = False
        else:
            self.timedout = True
    def stop(self):
        self.running = False
        
class Speech2Text(object):
    """Class for speech-recognition (voice to text), using Google's public API.
    
        Google's speech API is currently free to use, and seems to work well.
        Intended for within-experiment processing (near real-time, 1-2s delayed), in which
        its often important to skip a slow or failed response, and not wait a long time;
        `BatchSpeech2Text()` reverses these priorities.
        
        It is possible (and
        perhaps even likely) that Google will start charging for usage. In addition, they
        can change the interface at any time, including in the middle of an experiment.
        (If so, please post to the user list and we'll try to develop a fix, but
        there could still be some downtime.) Presumably, confidential
        or otherwise sensitive voice data should not be sent to google. 
        
        :Usage:
        
        a) Always import and make an object; no data are available yet::
        
            from microphone import Speech2Text
            gs = Speech2Text('speech_clip.wav') # set-up only
        
        b) Then, either: Initiate a query and wait for response from google (or until the time-out limit is reached). This is "blocking" mode, and is the easiest to do::
        
            resp = gs.getResponse() # execution blocks here
            print resp.word, resp.confidence
        
        c) Or instead (advanced usage): Initiate a query, but do not wait for a response ("thread" mode: no blocking, no timeout, more control). `running` will change to False when a response is received (or hang indefinitely if something goes wrong--so you might want to implement a time-out as well)::
        
            resp = gs.getThread() # returns immediately
            while resp.running:
                print '.', # displays dots while waiting
                sys.stdout.flush()
                time.sleep(0.1)
            print resp.words
        
        d) Options: Set-up with a different language for the same speech clip; you'll get a different response (possibly having UTF-8 characters)::
        
            gs = Speech2Text('speech_clip.wav', lang='ja-JP')
            resp = gs.getResponse()
        
        :Example:
        
            See Coder demos / input / say_rgb.py -- be sure to read the text at the top of the file.
            The demo works better when run from the command-line than from the Coder.
        
        :Error handling:
            
            If there is an error during http connection, it is handled as a lack of
            response. The connection was probably lost if you get: `WARNING <urlopen error [Errno 8] nodename nor servname provided, or not known>`
            
        :Known limitations:
        
            a) Availability is subject to the whims of google. Any changes google
            makes along the way could either cause complete failure (disruptive),
            or could cause slightly different results to be obtained (without it being
            readily obvious that something had changed). For this reason,
            its probably a good idea to re-run speech samples through `Speech2Text` at the end of
            a study; see `BatchSpeech2Text()`.
            
            b) Only tested with: Win XP-sp2,
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
            
                `file` : <required>
                    name of the speech file (.flac, .wav, or .spx) to process. wav files will be
                    converted to flac, and for this to work you need to have flac (as an
                    executable). spx format is speex-with-headerbyte (for google).
                `lang` :
                    the presumed language of the speaker, as a locale code; default 'en-US'
                `timeout` :
                    seconds to wait before giving up, default 10
                `samplingrate` :
                    the sampling rate of the speech clip in Hz, either 16000 or 8000. You can
                    record at a higher rate, and then down-sample to 16000 for speech
                    recognition. `file` is the down-sampled file, not the original.
                `flac_exe` :
                    **Windows only**: path to binary for converting wav to flac;
                    must be a string with **two back-slashes where you want one** to appear
                    (this does not display correctly above, in the web documentation auto-build);
                    default is 'C:\\\\\\\\Program Files\\\\\\\\FLAC\\\\\\\\flac.exe'
                `pro_filter` :
                    profanity filter level; default 2 (e.g., f***)
                `quiet` :
                    no reporting intermediate details; default `True` (non-verbose)
                 
        """
        # set up some key parameters:
        results = 5 # how many words wanted
        self.timeout = timeout
        useragent = PSYCHOPY_USERAGENT
        host = "www.google.com/speech-api/v1/recognize"
        if sys.platform == 'win32':
            FLAC_PATH = flac_exe
        else:
            # best not to do every time
            FLAC_PATH, _ = core.shellCall(['/usr/bin/which', 'flac'], stderr=True)
        
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
            _, se = core.shellCall(flac_cmd, stderr=True)
            if se: logging.warn(se)
            while not os.path.isfile(tmp): # just try again
                # ~2% incidence when recording for 1s, 650+ trials
                # never got two in a row; time.sleep() does not help
                logging.warn('Failed to convert to tmp.flac; trying again')
                _, se = core.shellCall(flac_cmd, stderr=True)
                if se: logging.warn(se)
            file = tmp # note to self: ugly & confusing to switch up like this
        logging.info("Loading: %s as %s, audio/%s" % (self.file, lang, filetype))
        try:
            c = 0 # occasional error; time.sleep(.1) is not always enough; better slow than fail
            while not os.path.isfile(file) and c < 10:
                time.sleep(.1)
                c += 1
            audio = open(file, 'r+b').read()
        except:
            msg = "Can't read file %s from %s.\n" % (file, self.file)
            logging.error(msg)
            raise SoundFileError(msg)
        finally:
            try: os.remove(tmp)
            except: pass
        
        # urllib2 makes no attempt to validate the server certificate. here's an idea:
        # http://thejosephturner.com/blog/2011/03/19/https-certificate-verification-in-python-with-urllib2/
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
            logging.info("https request failed. %s, %s. trying again..." % (file, self.file))
            time.sleep(0.2)
            self.request = urllib2.Request(url, audio, header)
    def _removeThread(self, gsqthread):
        del core.runningThreads[core.runningThreads.index(gsqthread)]
    def getThread(self):
        """Send a query to google using a new thread, no blocking or timeout.
        
        Returns a thread which will **eventually** (not immediately) have the speech
        data in its namespace; see getResponse. In theory, you could have several
        threads going simultaneously (almost all the time is spent waiting for a
        response), rather than doing them sequentially (not tested).
        """
        gsqthread = _GSQueryThread(self.request)
        gsqthread.start()
        core.runningThreads.append(gsqthread)
        # this is the right idea, but need to .cancel() it when a response has come:
        #threading.Timer(self.timeout, self._removeThread, (gsqthread,)).start()
        logging.info("Sending speech-recognition https request to google")
        gsqthread.file = self.file
        while not gsqthread.running:
            core.wait(0.001) # can return too quickly if thread is slow to start
        return gsqthread # word and time data will eventually be in the namespace
    def getResponse(self):
        """Calls `getThread()`, and then polls the thread until there's a response.
        
        Will time-out if no response comes within `timeout` seconds. Returns an 
        object having the speech data in its namespace. If there's no match, 
        generally the values will be equivalent to `None` (e.g., an empty string).
        
        If you do `resp = getResponse()`, you'll be able to access the data
        in several ways:
        
            `resp.word` :
                the best match, i.e., the most probably word, or `None`
            `resp.confidence` :
                google's confidence about `.word`, ranging 0 to 1
            `resp.words` :
                tuple of up to 5 guesses; so `.word` == `.words[0]`
            `resp.raw` :
                the raw response from google (just a string)
            `resp.json` :
                a parsed version of raw, from `json.load(raw)`
        """
        gsqthread = self.getThread()
        while gsqthread.elapsed() < self.timeout:
            time.sleep(0.1) # don't need precise timing to poll an http connection
            if not gsqthread.running:
                break
        if gsqthread.running: # timed out
            gsqthread.status = 408 # same as http code
        return gsqthread # word and time data are already in the namespace

class BatchSpeech2Text(list):
    def __init__(self, files, threads=3, verbose=False):
        """Like `Speech2Text()`, but takes a list of sound files or a directory name to search
        for matching sound files, and returns a list of `(filename, response)` tuples.
        `response`'s are described in `Speech2Text.getResponse()`.
        
        Can use up to 5 concurrent threads. Intended for
        post-experiment processing of multiple files, in which waiting for a slow response
        is not a problem (better to get the data).
        
        If `files` is a string, it will be used as a directory name for glob
        (matching all `*.wav`, `*.flac`, and `*.spx` files).
        There's currently no re-try on http error."""
        list.__init__(self) # [ (file1, resp1), (file2, resp2), ...]
        maxThreads = min(threads, 5) # I get http errors with 6
        self.timeout = 30
        if type(files) == str and os.path.isdir(files):
            f = glob.glob(os.path.join(files, '*.wav'))
            f += glob.glob(os.path.join(files, '*.flac'))
            f += glob.glob(os.path.join(files, '*.spx'))
            fileList = f
        else:
            fileList = list(files)
        for i, file in enumerate(fileList):
            gs = Speech2Text(file)
            self.append( (file, gs.getThread()) ) # tuple
            if verbose:
                print i, file
            while self._activeCount() >= maxThreads:
                core.wait(.1, hogCPUPeriod=0) # idle at max count
    def _activeCount(self):
        # self is a list of (name, thread) tuples; count active threads
        count = len([f for f,t in self if t.running and t.elapsed() <= self.timeout] )
        return count
    
def switchOn(sampleRate=48000, outputDevice=None, bufferSize=None):
    """You need to switch on the microphone before use, which can take several seconds.
    The only time you can specify the sample rate (in Hz) is during switchOn().
    You can switchOff() and switchOn() with a different rate, and can `resample()`
    a given an `AudioCapture()` object (if one has been recorded).
    
    Considerations on the default sample rate 48kHz::
    
        DVD or video = 48,000
        CD-quality   = 44,100 / 24 bit
        human hearing: ~15,000 (adult); children & young adult higher
        human speech: 100-8,000 (useful for telephone: 100-3,300)
        google speech API: 16,000 or 8,000 only
        Nyquist frequency: twice the highest rate, good to oversample a bit
        
    pyo's downsamp() function can reduce 48,000 to 16,000 in about 0.02s (uses integer steps sizes)
    So recording at 48kHz will generate high-quality archival data, and permit easy downsampling.
    
    outputDevice, bufferSize: set these parameters on the pyoServer before booting;
        None means use pyo's default values
    """
    # imports from pyo, creates globals pyoServer
    t0 = core.getTime()
    try:
        global Server, Record, Input, Clean_objects, SfPlayer, serverCreated, serverBooted
        from pyo import Server, Record, Input, Clean_objects, SfPlayer, serverCreated, serverBooted
        global getVersion, pa_get_input_devices, pa_get_output_devices, downsamp, upsamp
        from pyo import getVersion, pa_get_input_devices, pa_get_output_devices, downsamp, upsamp
        global haveMic
        haveMic = True
    except ImportError:
        msg = 'Microphone class not available, needs pyo; see http://code.google.com/p/pyo/'
        logging.error(msg)
        raise ImportError(msg)
    global pyoServer
    if serverCreated():
        pyoServer.setSamplingRate(sampleRate)
        
    else:
        pyoServer = Server(sr=sampleRate, nchnls=2, duplex=1)
    if outputDevice:
        pyoServer.setOutputDevice(outputDevice)
    if bufferSize:
        pyoServer.setBufferSize(bufferSize)
    pyoServer.boot()
    core.pyoServers.append(pyoServer)
    pyoServer.start()
    logging.exp('%s: switch on (%dhz) took %.3fs' % (__file__.strip('.py'), sampleRate, core.getTime() - t0))
    
def switchOff():
    """Its good to explicitly switch off the microphone when done (in order to avoid
    a segmentation fault). core.quit() also tries to switchOff if needed, but best to
    do so explicitly.
    """
    t0 = core.getTime()
    global haveMic
    haveMic = False
    global pyoServer
    if serverBooted():
        pyoServer.stop()
        core.wait(.25) # give it a chance to stop before shutdown(), avoid seg fault
    if serverCreated():
        pyoServer.shutdown()
        del core.pyoServers[core.pyoServers.index(pyoServer)]
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
        mic = AudioCapture()
        if len(sys.argv) > 1: # stability test using argv[1] iterations
            for i in xrange(int(sys.argv[1])): 
                print i, mic.record(2)
                mic.resample(8000, keep=False) # removes orig file
                os.remove(mic.savedFile) # removes downsampled file
        else: # two interactive record + playback tests
            testDuration = 2  # sec
            raw_input('testing record and playback, press <return> to start: ')
            print "say something:",
            sys.stdout.flush()
            # tell it to record for 10s:
            mic.record(testDuration * 5, block=False) # block False returns immediately
                # which you want if you might need to stop a recording early
            core.wait(testDuration)  # we'll stop the record after 2s, not 10
            mic.stop()
            print
            print 'record stopped; sleeping 1s'
            sys.stdout.flush()
            core.wait(1)
            print 'start playback ',
            sys.stdout.flush()
            mic.playback()
            print 'end.', mic.savedFile
            sys.stdout.flush()
            os.remove(mic.savedFile)
            mic.reset()
            
            # do another record, fixed duration, use block=True
            raw_input('<ret> for another: ')
            print "say something else:",
            sys.stdout.flush()
            mic.record(testDuration, file='m') # block=True by default; here use explicit file name
            mic.playback()
            print mic.savedFile
            os.remove(mic.savedFile)
    finally:
        switchOff()
