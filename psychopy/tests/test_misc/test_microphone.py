from __future__ import division

from builtins import object
from past.utils import old_div
from psychopy import microphone, core, web
from psychopy.microphone import *
from psychopy.microphone import _getFlacPath
import pytest
import shutil, os, glob
from tempfile import mkdtemp
from os.path import abspath, dirname, join


# py.test -k microphone --cov-report term-missing --cov microphone.py tests/

# flac2wav will delete the .flac file unless given keep=True
# Speech2Text can overwrite and then delete .flac if given a .wav of the same name

from psychopy.tests.utils import TESTS_PATH, TESTS_DATA_PATH

@pytest.mark.needs_sound
@pytest.mark.microphone
@pytest.mark.slow
class TestMicrophone(object):
    @classmethod
    def setup_class(self):
        global sound
        from psychopy import sound
        switchOn(48000)
        self.tmp = mkdtemp(prefix='psychopy-tests-microphone')
    @classmethod
    def teardown_class(self):
        if hasattr(self, 'tmp'):
            shutil.rmtree(self.tmp, ignore_errors=True)
        switchOff()  # not needed, just get code coverage

    def test_AudioCapture_basics(self):
        microphone.haveMic = False
        with pytest.raises(MicrophoneError):
            AdvAudioCapture(autoLog=False)
        microphone.haveMic = True

        switchOn(16000, 1, 2048)
        switchOn(48000)

        mic = AdvAudioCapture(saveDir=self.tmp, autoLog=False)
        mic = AdvAudioCapture(saveDir=self.tmp+'_test', autoLog=False)
        mic.record(.10, block=False)  # returns immediately
        core.wait(.02)
        mic.stop()
        mic.reset()

        mic.record(0.2, block=True)
        assert os.path.isfile(mic.savedFile)

    def test_AdvAudioCapture(self):
        filename = os.path.join(self.tmp, 'test_mic.wav')
        mic = AdvAudioCapture(autoLog=False)
        tone = sound.Sound(440, secs=.02, autoLog=False)
        mic.setMarker(tone=tone)
        mic = AdvAudioCapture(filename=filename, saveDir=self.tmp, autoLog=False)

        mic.record(1, block=True)
        mic.setFile(mic.savedFile)  # same file name
        mic.getMarkerOnset()

        mic.compress()
        assert os.path.exists(mic.savedFile)
        assert mic.savedFile.endswith('.flac')

        mic.uncompress()
        assert mic.savedFile.endswith('.wav')
        assert os.path.exists(mic.savedFile)

        old_size = os.path.getsize(mic.savedFile)
        new_file = mic.resample(keep=False)
        assert old_div(old_size, 3.1) < os.path.getsize(new_file) < old_div(old_size, 2.9)
        mic.getLoudness()

        mic.playback()
        mic.playback(loops=2, block=False)
        mic.playback(stop=True)

        tmp = mic.savedFile
        mic.savedFile = None
        with pytest.raises(ValueError):
            mic.playback()
        with pytest.raises(ValueError):
            mic.getLoudness()
        mic.savedFile = tmp

        mic.resample(keep=False)
        mic.resample(newRate=48000, keep=False)
        tmp = mic.savedFile
        mic.savedFile = None
        with pytest.raises(ValueError):
            mic.resample(keep=False)
        mic.savedFile = tmp
        with pytest.raises(ValueError):
            mic.resample(newRate=-1)

#@pytest.mark.needs_sound
@pytest.mark.microphone
@pytest.mark.speech
@pytest.mark.mic_utils
class TestMicrophoneNoSound(object):
    @classmethod
    def setup_class(self):
        try:
            assert _getFlacPath()
        except Exception:
            # some of the utils could be designed not to need flac but they
            # currently work on a file that is distributed in flac format
            pytest.skip()
        self.tmp = mkdtemp(prefix='psychopy-tests-microphone')
        for testFile in ['red_16000.flac.dist', 'green_48000.flac.dist']:
            t = join(TESTS_DATA_PATH, testFile)
            new_wav = join(self.tmp, testFile.replace('.dist', ''))
            shutil.copyfile(t, new_wav)
            flac2wav(new_wav)
    @classmethod
    def teardown_class(self):
        if hasattr(self, 'tmp'):
            shutil.rmtree(self.tmp, ignore_errors=True)

    def test_getFlacPath(self):
        microphone.FLAC_PATH = None
        with pytest.raises(MicrophoneError):
            _getFlacPath('this is not the flac you are looking for')

        microphone.FLAC_PATH = None
        _getFlacPath('flac')

        microphone.FLAC_PATH = 'flac'
        assert microphone.FLAC_PATH

        microphone.FLAC_PATH = None
        _getFlacPath()

    def test_wav_flac(self):
        filename = os.path.join(self.tmp, 'test_bad_readWav')
        with open(filename, 'wb') as fd:
            fd.write(b'x')
        with pytest.raises(SoundFileError):
            readWavFile(filename)

        testFile = join(self.tmp, 'green_48000.wav')
        newFile = wav2flac(testFile, keep=True)
        flac2wav(newFile, keep=True)

        newFile0 = wav2flac(testFile, keep=True, level=0)
        newFile8 = wav2flac(testFile, keep=True, level=8)
        assert os.path.getsize(newFile0) >= os.path.getsize(newFile8)

        wav2flac('.', keep=True)
        flac2wav('.', keep=True)
        wav2flac('', keep=True)
        flac2wav('', keep=True)

        wav2flac(self.tmp, keep=True)

    def test_Speech2Text(self):
        pytest.skip()  # google speech API gives Error 400: Bad request

        try:
            web.requireInternetAccess()
        except web.NoInternetAccessError:
            pytest.skip()

        # load a known sound file
        testFile = join(self.tmp, 'red_16000.wav')

        gs = Speech2Text(filename=testFile)
        resp = gs.getResponse()
        assert resp.word == 'red'

        # test batch-discover files in a directory
        tmp = join(self.tmp, 'tmp')
        os.mkdir(tmp)
        shutil.copy(testFile, tmp)
        bs = BatchSpeech2Text(files=tmp)

        bs = BatchSpeech2Text(files=glob.glob(join(self.tmp, 'red_*.wav')))
        while bs._activeCount():
            core.wait(.1, 0)
        resp = bs[0][1]
        assert 0.6 < resp.confidence < 0.75  # 0.68801856
        assert resp.word == 'red'

    def test_DFT(self):
        testFile = join(self.tmp, 'red_16000.wav')
        data, sampleRate = readWavFile(testFile)

        with pytest.raises(OverflowError):
            getDft([])
        getDft(data)
        getDftBins(data)
        getDftBins(data, sampleRate=16000)
        getDft(data, sampleRate=sampleRate)
        getDft(data, wantPhase=True)

    def test_RMS(self):
        testFile = join(self.tmp, 'red_16000.wav')
        data, sampleRate = readWavFile(testFile)

        rms = getRMS(data)
        assert 588.60 < rms < 588.61

        rmsb = getRMSBins(data, chunk=64)
        assert 10.2 < rmsb[0] < 10.3
        assert len(rmsb) == 480

    def test_marker(self):
        testFile = join(self.tmp, 'green_48000.wav')

        marker = getMarkerOnset(testFile)  # 19kHz marker sound
        assert 0.0666 < marker[0] < 0.06677  # start
        assert 0.0773 < marker[1] < 0.07734  # end
