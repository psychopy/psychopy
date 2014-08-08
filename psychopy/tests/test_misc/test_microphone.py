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
        os.chdir(self.tmp)
        microphone.haveMic = False
        with pytest.raises(MicrophoneError):
            AdvAudioCapture()
        microphone.haveMic = True

        switchOn(16000, 1, 2048)
        switchOn(48000)

        mic = AdvAudioCapture(saveDir=self.tmp)
        mic.record(.10, block=False)  # returns immediately
        core.wait(.02)
        mic.stop()

    def test_AdvAudioCapture(self):
        os.chdir(self.tmp)
        mic = AdvAudioCapture()
        tone = sound.Sound(440, secs=.02)
        mic.setMarker(tone=tone)
        mic = AdvAudioCapture(filename='test_mic.wav', saveDir=self.tmp)

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
        assert old_size / 3.1 < os.path.getsize(new_file) < old_size / 2.9
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
class TestMicrophoneNoSound(object):
    @classmethod
    def setup_class(self):
        try:
            assert _getFlacPath()
        except:
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
        #microphone.FLAC_PATH = None
        #with pytest.raises(MicrophoneError):
        #    _getFlacPath('this is not flac')
        microphone.FLAC_PATH = None
        _getFlacPath()
        microphone.FLAC_PATH = None
        _getFlacPath('flac')

        microphone.FLAC_PATH = 'flac'
        assert microphone.FLAC_PATH

    def test_misc(self):
        getRMS([1,2,3,4,5])

    def test_wav_flac(self):
        filename = os.path.join(self.tmp, 'test_bad_readWav')
        with open(filename, 'wb') as fd:
            fd.write('x')
        with pytest.raises(SoundFileError):
            readWavFile(filename)

        testFile = join(self.tmp, 'red_16000.wav')
        newFile = wav2flac(testFile, keep=True)
        flac2wav(newFile, keep=True)
        wav2flac('.', keep=True)
        flac2wav('.', keep=True)
        wav2flac('', keep=True)
        flac2wav('', keep=True)

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


    def test_Speech2Text(self):
        try:
            web.requireInternetAccess()
        except web.NoInternetAccessError:
            pytest.skip()

        # load a known sound file
        testFile = join(self.tmp, 'red_16000.wav')

        gs = Speech2Text(filename=testFile)
        resp = gs.getResponse()
        assert resp.word == 'red'

        bs = BatchSpeech2Text(files=glob.glob(join(self.tmp, 'red_*.wav')))
        os.unlink(join(self.tmp, 'green_48000.wav'))
        bs = BatchSpeech2Text(files=self.tmp, threads=1)
