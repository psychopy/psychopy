# -*- coding: utf-8 -*-
"""Audio capture and analysis using pyo"""

# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import division
import os, sys, shutil, time
import threading, urllib2, json
import tempfile
from psychopy import core, logging
from psychopy.constants import NOT_STARTED, PSYCHOPY_USERAGENT
# import pyo is done within switchOn/Off to better encapsulate it, because it can be very slow
# idea: don't want to delay up to 3 sec when importing microphone
# downside: to make this work requires some trickiness with globals

__author__ = 'Jeremy R. Gray'

ONSET_TIME_HERE = '!ONSET_TIME_HERE!'

global haveMic
haveMic = False # goes True in switchOn, if can import pyo; goes False in switchOff


class AudioCapture(object):
    """Capture a sound sample from the default sound input, and save to a file.
        
        Untested whether you can have two recordings going on simultaneously.
        
        **Example**::
        
            from psychopy import microphone
            
            microphone.switchOn(sampleRate=16000) # do once when starting, can take 2-3s
            
            mic = microphone.AudioCapture()  # prepare to record; only one can be active
            mic.record(1)  # record for 1.000 seconds, save to a file
            mic.playback()
            savedFileName = mic.savedFile
            
            microphone.switchOff() # do once, at exit 
        
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
        This class never handles blocking; SimpleAudioCapture has to do that.
        
        Motivation: Doing pyo Record from within a function worked most of the time,
        but failed catastrophically ~1% of time with a bus error. Seemed to be due to
        a namespace scoping issue, which using globals seemed to fix; see pyo mailing
        list, 7 April 2012. This draws heavily on Olivier Belanger's solution.
        """
        def __init__(self, file, sec=0):
            self.running = False
            if file:
                inputter = Input(chnl=0, mul=1)
                recorder = Record(inputter,
                               file,
                               chnls=2,
                               fileformat=0,
                               sampletype=0,
                               buffering=4)
                self.clean = Clean_objects(sec, recorder)
        def run(self, file, sec):
            self.__init__(file, sec)
            self.running = True
            self.clean.start() # controls recording onset (now) and offset (later)
            threading.Timer(sec, self.stop).start() # set running flag False
        def stop(self):
            self.running = False
            
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
        while self.recorder.running:
            pass
        self.duration = float(sec)
        self.onset = core.getTime() # note: report onset time in log, and use in filename
        logging.data('%s: Record: onset %.3f, capture %.3fs' %
                     (self.loggingId, self.onset, self.duration) )
        if not file:
            self.savedFile = self.wavOutFilename.replace(ONSET_TIME_HERE, '-%.3f' % self.onset)
        else:
            self.savedFile = os.path.abspath(file).strip('.wav')+'.wav'
        
        t0 = core.getTime()
        self.recorder.run(self.savedFile, self.duration)
        
        if block:
            core.wait(self.duration - .0008) # .0008 fudge factor for better reporting
                # actual timing is done by Clean_object in _theGlobalRecordingThread()
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
    """Class for speech-recognition (voice to text), using google's public API.
    
        Google's speech API is currently free to use, and seems to work well. It is possible (and
        perhaps even likely) that Google will start charging for usage. In addition, they
        can change the interface at any time, including in the middle of an experiment.
        (If so, please post to the user list and we'll try to develop a fix, but
        there could still be some downtime.) Presumably, confidential
        or otherwise sensitive voice data should not be sent to google. 
        
        :Usage:
        
        a) Always import and make an object; no data are available yet::
        
            from speech import GoogleSpeech2Text
            gs = Speech2Text('speech_clip.wav') # set-up only
        
        b) Then, either: Initiate a query and wait for response from google (or until the time-out limit is reached). This is "blocking" mode, and is the easiest to do::
        
            resp = gs.getResponse() # execution blocks here
            print resp.word, resp.confidence
        
        c) Or instead (more advanced usage): Initiate a query, but do not wait for a response ("thread" mode: no blocking, no timeout, more control). `running` will change to False when a response is received (or hang indefinitely if something goes wrong--so you might want to implement a time-out as well)::
        
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
        
            a) Availabiity is subject to the whims of google, and any changes google
            makes along the way could either cause complete failure (which is disruptive),
            or could cause slightly different results to be obtained. For this reason,
            its probably a good idea to re-run speech samples through google at the end of
            a study.
            
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
            
                file : <required>
                    name of the speech file (.flac, .wav, or .spx) to process. wav files will be
                    converted to flac, and for this to work you need to have flac (as an
                    executable). spx format is speex-with-headerbyte (for google).
                lang :
                    the presumed language of the speaker, as a locale code; default 'en-US'
                timeout :
                    seconds to wait before giving up, default 10
                samplingrate :
                    the sampling rate of the speech clip in Hz, either 16000 or 8000
                flac_exe :
                    **Windows only**: path to binary for converting wav to flac;
                    must be a string with **two back-slashes where you want one** to appear
                    (this does not display correctly above, in the web documentation auto-build);
                    default is 'C:\\\\\\\\Program Files\\\\\\\\FLAC\\\\\\\\flac.exe'
                pro_filter :
                    profanity filter level; default 2 (e.g., f***)
                quiet :
                    no reporting intermediate details; default True (non-verbose)
                 
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
        data in its namespace; see getResponse.
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
        """Calls getThread, and then polls the thread to until there's a response.
        
        Will time-out if no response comes within `timeout` seconds. Returns an 
        object having the speech data in its namespace. If there's no match, 
        generally the values will be equivalent to `None` (e.g., an empty string).
        
        :Namespace:
        
            `.word` :
                the best match, i.e., the most probably word, or `None`
            `.confidence` :
                google's confidence about `.word`, ranging 0 to 1
            `.words` :
                tuple of up to 5 guesses; so `.word` == `.words[0]`
            `.raw` :
                the raw response from google (just a string)
            `.json` :
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

def switchOn(sampleRate=44100):
    """You need to switch on the microphone before use. Can take several seconds.
    """
    # imports from pyo, creates globals pyoServer
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
    logging.exp('%s: switch on (%dhz) took %.3fs' % (__file__.strip('.py'), sampleRate, core.getTime() - t0))
    
def switchOff():
    """Must explicitly switch off the microphone when done (to avoid a seg fault).
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
