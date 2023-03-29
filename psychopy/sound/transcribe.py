#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for transcribing speech in audio data to text.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'TranscriptionResult',
    'transcribe',
    'TRANSCR_LANG_DEFAULT',
    'BaseTranscriber',
    'WhisperTranscriber',
    'recognizerEngineValues',
    'recognizeSphinx',
    'recognizeGoogle',
    'recognizeWhisper',
    'getAllTranscribers'
]

import sys
import os
import psychopy.logging as logging
from psychopy.alerts import alert
from pathlib import Path
from psychopy.preferences import prefs
from .audioclip import *
from .exceptions import *
import numpy as np

# ------------------------------------------------------------------------------
# Initialize the speech recognition system
#

# _hasSpeechRecognition = True
# try:
#     import speech_recognition as sr
# except (ImportError, ModuleNotFoundError):
#     logging.warning(
#         "Speech-to-text recognition module for PocketSphinx is not available "
#         "(use command `pip install SpeechRecognition` to get it). "
#         "Transcription will be unavailable using that service this session.")
#     _hasSpeechRecognition = False

# Google Cloud API
# _hasGoogleCloud = True
# _googleCloudClient = None  # client for Google Cloud, instanced on first use
# try:
#     import google.cloud.speech
#     import google.auth.exceptions
# except (ImportError, ModuleNotFoundError):
#     logging.warning(
#         "Speech-to-text recognition using Google online services is not "
#         "available (use command `pip install google-api-core google-auth "
#         "google-cloud google-cloud-speech googleapis-common-protos` to get "
#         "it). Transcription will be unavailable using that service this "
#         "session.")
#     _hasGoogleCloud = False

# try:
#     import pocketsphinx
#     sphinxLangs = [folder.stem for folder
#                    in Path(pocketsphinx.get_model_path()).glob('??-??')]
#     haveSphinx = True
# except (ImportError, ModuleNotFoundError):
#     haveSphinx = False
#     sphinxLangs = None

# Constants related to the transcription system.
TRANSCR_LANG_DEFAULT = 'en-US'

# Values for specifying recognizer engines. This dictionary is used by Builder
# to populate the component property dropdown.
recognizerEngineValues = {
    0: ('sphinx', "CMU Pocket Sphinx", "Offline, Built-in"),
    1: ('google', "Google Cloud Speech API", "Online, Key Required"),
    2: ('whisper', "OpenAI Whisper", "Offline")
}


# ------------------------------------------------------------------------------
# Classes and functions for speech-to-text transcription
#

class TranscriptionResult:
    """Descriptor for returned transcription data.

    Fields within this class can be used to access transcribed words and other
    information related to the transcription request.

    This is returned by functions and methods which perform speech-to-text
    transcription from audio data within PsychoPy. The user usually does not
    create instances of this class themselves.

    Parameters
    ----------
    words : list of str
        Words extracted from the audio clip.
    unknownValue : bool
        `True` if the transcription API failed make sense of the audio and did
        not complete the transcription.
    requestFailed : bool
        `True` if there was an error with the transcriber itself. For instance,
        network error or improper formatting of the audio data.
    engine : str
        Name of engine used to perform this transcription.
    language : str
        Identifier for the language used to perform the transcription.

    """
    __slots__ = [
        '_words',
        '_text',
        '_confidence',  # unused on Python for now
        '_response',
        '_engine',
        '_language',
        '_expectedWords',
        '_requestFailed',
        '_unknownValue']

    def __init__(self, words, unknownValue, requestFailed, engine, language):
        self.words = words
        self.unknownValue = unknownValue
        self.requestFailed = requestFailed
        self.engine = engine
        self.language = language

    def __repr__(self):
        return (f"TranscriptionResult(words={self._words}, "
                f"unknownValue={self._unknownValue}, ",
                f"requestFailed={self._requestFailed}, ",
                f"engine={self._engine}, ",
                f"language={self._language})")

    def __str__(self):
        return " ".join(self._words)

    @property
    def wordCount(self):
        """Number of words found (`int`)."""
        return len(self._words)

    @property
    def words(self):
        """Words extracted from the audio clip (`list` of `str`)."""
        return self._words

    @property
    def text(self):
        """Text transcribed for the audio data (`str`).
        """
        return self._text

    @words.setter
    def words(self, value):
        self._words = list(value)

    @property
    def response(self):
        """Raw API response from the transcription engine (`str`).
        """
        return self._response

    @response.setter
    def response(self, val):
        self._response = val

    def getWordData(self):
        pass
        
    @property
    def success(self):
        """`True` if the transcriber returned a result successfully (`bool`)."""
        return not (self._unknownValue or self._requestFailed)

    @property
    def error(self):
        """`True` if there was an error during transcription (`bool`). Value is
        always the compliment of `.success`."""
        return not self.success

    @property
    def unknownValue(self):
        """`True` if the transcription API failed make sense of the audio and
        did not complete the transcription (`bool`).
        """
        return self._unknownValue

    @unknownValue.setter
    def unknownValue(self, value):
        self._unknownValue = bool(value)

    @property
    def requestFailed(self):
        """`True` if there was an error with the transcriber itself (`bool`).
        For instance, network error or improper formatting of the audio data,
        invalid key, or if there was network connection error.
        """
        return self._requestFailed

    @requestFailed.setter
    def requestFailed(self, value):
        self._requestFailed = bool(value)

    @property
    def engine(self):
        """Name of engine used to perform this transcription (`str`).
        """
        return self._engine

    @engine.setter
    def engine(self, value):
        if value == 'sphinx':
            if not haveSphinx:
                raise ModuleNotFoundError(
                    "To perform built-in (local) transcription you need to "
                    "have pocketsphinx installed (pip install pocketsphinx)")
        self._engine = str(value)

    @property
    def language(self):
        """Identifier for the language used to perform the transcription
        (`str`).
        """
        return self._language

    @language.setter
    def language(self, value):
        self._language = str(value)


# empty result returned when a transcriber is given no data
NULL_TRANSCRIPTION_RESULT = TranscriptionResult(
    words=[''],
    unknownValue=False,
    requestFailed=False,
    engine='null',
    language=TRANSCR_LANG_DEFAULT
)


# ------------------------------------------------------------------------------
# Transcription interfaces
#

class BaseTranscriber:
    """Base class for text-to-speech transcribers.

    This class defines the API for transcription, which is an interface to a 
    speech-to-text engine. All transcribers must be sub-classes of this class
    and implement all members of this class.

    Parameters
    ----------
    initConfig : dict or None
        Options to configure the speech-to-text engine during initialization. 

    """
    _isLocal = True
    _engine = u'Null'
    _longName = u"Null"
    _lastResult = None
    def __init__(self, initConfig=None):
        self._initConf = initConfig

    @property
    def longName(self):
        """Human-readable name of the transcriber (`str`).
        """
        return self._longName

    @property
    def engine(self):
        """Identifier for the transcription engine which this object interfaces 
        with (`str`).
        """
        return self._engine

    @property
    def isLocal(self):
        """`True` if the transcription engine works locally without sending data
        to a remote server.
        """
        return self._isLocal

    @property
    def isComplete(self):
        """`True` if the transcriber has completed its transcription. The result 
        can be accessed through `.lastResult`.
        """
        return True
    
    @property
    def lastResult(self):
        """Result of the last transcription.
        """
        return self._lastResult

    @lastResult.setter
    def lastResult(self, val):
        self._lastResult = val

    def transcribe(self, audioClip, modelConfig=None, decoderConfig=None):
        """Perform speech-to-text conversion on the provided audio samples.

        Parameters
        ----------
        audioClip : :class:`~psychopy.sound.AudioClip`
            Audio clip containing speech to transcribe (e.g., recorded from a
            microphone).
        modelConfig : dict or None
            Additional configuration options for the model used by the engine.
        decoderConfig : dict or None
            Additional configuration options for the decoder used by the engine.

        Returns
        -------
        TranscriptionResult
            Transcription result object.

        """
        return NULL_TRANSCRIPTION_RESULT


class PocketSphinxTranscriber(BaseTranscriber):
    """Class to perform speech-to-text conversion on the provided audio samples 
    using CMU Pocket Sphinx.

    Parameters
    ----------
    initConfig : dict or None
        Options to configure the speech-to-text engine during initialization. 

    """
    _isLocal = True
    _engine = u'sphinx'
    _longName = u"CMU PocketSphinx"
    def __init__(self, initConfig=None):
        super(PocketSphinxTranscriber, self).__init__(initConfig)

        # import the library and get language models
        import speech_recognition as sr

        # create a recognizer interface
        self._recognizer = sr.Recognizer()

    @staticmethod
    def getAllModels():
        """Get available language models for the PocketSphinx transcriber 
        (`list`).

        Returns
        -------
        list 
            List of available models.

        """
        import pocketsphinx
        modelPath = pocketsphinx.get_model_path()
        toReturn = [folder.stem for folder in Path(modelPath).glob('??-??')]

        return toReturn
    
    def transcribe(self, audioClip, modelConfig=None, decoderConfig=None):
        """Perform speech-to-text conversion on the provided audio samples using
        CMU Pocket Sphinx.

        Parameters
        ----------
        audioClip : :class:`~psychopy.sound.AudioClip`
            Audio clip containing speech to transcribe (e.g., recorded from a
            microphone).
        modelConfig : dict or None
            Additional configuration options for the model used by the engine.
        decoderConfig : dict or None
            Additional configuration options for the decoder used by the engine.
            Presently unused by this transcriber.

        Returns
        -------
        TranscriptionResult
            Transcription result object.

        """
        import speech_recognition as sr
        try:
            import pocketsphinx
        except (ImportError, ModuleNotFoundError):
            raise RecognizerEngineNotFoundError()
        
        # warmup the engine, not used here but needed for compatibility
        if audioClip is None:
            return NULL_TRANSCRIPTION_RESULT

        if isinstance(audioClip, AudioClip):
            pass
        elif isinstance(audioClip, (tuple, list,)):
            waveform, sampleRate = audioClip
            audioClip = AudioClip(waveform, sampleRateHz=sampleRate)
        else:
            raise TypeError(
                "Expected type for parameter `audioClip` to be either " 
                "`AudioClip`, `list` or `tuple`")

        # engine configuration
        modelConfig = {} if modelConfig is None else modelConfig
        if not isinstance(modelConfig, dict):
            raise TypeError(
                "Invalid type for parameter `config` specified, must be `dict` "
                "or `None`.")

        language = modelConfig.get('language', TRANSCR_LANG_DEFAULT)
        if not isinstance(language, str):
            raise TypeError(
                "Invalid type for parameter `language`, must be type `str`.")

        language = language.lower()
        if language not in sphinxLangs:  # missing a language pack error
            url = "https://sourceforge.net/projects/cmusphinx/files/" \
                "Acoustic%20and%20Language%20Models/"
            msg = (f"Language `{language}` is not installed for "
                f"`pocketsphinx`. You can download languages here: {url}. "
                f"Install them here: {pocketsphinx.get_model_path()}")
            raise RecognizerLanguageNotSupportedError(msg)
        
        # configure the recognizer
        modelConfig['language'] = language  # sphinx users en-us not en-US
        modelConfig['show_all'] = False

        expectedWords = modelConfig.get('keyword_entries', None)
        if expectedWords is not None:
            words, sens = _parseExpectedWords(expectedWords)
            modelConfig['keyword_entries'] = tuple(zip(words, sens))

        # convert audio to format for transcription
        sampleWidth = 2  # two bytes per sample for  WAV
        audioData = sr.AudioData(
            audioClip.asMono().convertToWAV(),
            sample_rate=audioClip.sampleRateHz,
            sample_width=sampleWidth)

        # submit audio samples to the API
        respAPI = ''
        unknownValueError = requestError = False
        try:
            respAPI = self._recognizer.recognize_sphinx(
                audioData, **modelConfig)
        except sr.UnknownValueError:
            unknownValueError = True
        except sr.RequestError:
            requestError = True

        # remove empty words
        result = [word for word in respAPI.split(' ') if word != '']

        # object to return containing transcription data
        self.lastResult = toReturn = TranscriptionResult(
            words=result,
            unknownValue=unknownValueError,
            requestFailed=requestError,
            engine='sphinx',
            language=language)

        # split only if the user does not want the raw API data
        return toReturn
        

class GoogleCloudTranscriber(BaseTranscriber):
    """Class for speech-to-text transcription using Google Cloud API services.

    Parameters
    ----------
    initConfig : dict or None
        Options to configure the speech-to-text engine during initialization. 

    """
    _isLocal = False
    _engine = u'googleCloud'
    _longName = u'Google Cloud'
    def __init__(self, initConfig=None):
        super(GoogleCloudTranscriber, self).__init__(initConfig)

        try:
            import google.cloud.speech
            import google.auth.exceptions
        except (ImportError, ModuleNotFoundError):
            pass

        if "GOOGLE_APPLICATION_CREDENTIALS" not in os.environ:
            os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = \
                prefs.general['appKeyGoogleCloud']
            
        # empty string indicates no key has been specified, raise error
        if not os.environ["GOOGLE_APPLICATION_CREDENTIALS"]:
            raise RecognizerAPICredentialsError(
                'No application key specified for Google Cloud Services, '
                'specify the path to the key file with either the system '
                'environment variable `GOOGLE_APPLICATION_CREDENTIALS` or in '
                'preferences (General -> appKeyGoogleCloud).')

        # open new client, takes a while the first go
        try:
            client = google.cloud.speech.SpeechClient()
        except google.auth.exceptions.DefaultCredentialsError:
            raise RecognizerAPICredentialsError(
                'Invalid key specified for Google Cloud Services, check if the '
                'key file is valid and readable.')

        self._googleCloudClient = client

    def transcribe(self, audioClip, modelConfig=None, decoderConfig=None):
        """Transcribe text using Google Cloud.

        Parameters
        ----------
        audioClip : AudioClip, list or tuple
            Audio clip containing speech to transcribe (e.g., recorded from a
            microphone). Can be either an :class:`~psychopy.sound.AudioClip` 
            object or tuple where the first value is as a Nx1 or Nx2 array of 
            audio samples (`ndarray`) and the second the sample rate (`int`) in 
            Hertz (e.g., ``(samples, 48000)``).

        Returns
        -------
        TranscriptionResult
            Result of the transcription.
        
        """
        # if None, return a null transcription result and just open a client
        if audioClip is None:
            return NULL_TRANSCRIPTION_RESULT
        
        if isinstance(audioClip, (list, tuple,)):
            waveform, sr = audioClip
            audioClip = AudioClip(waveform, sampleRateHz=sr)


        # check if we have a valid audio clip
        if not isinstance(audioClip, AudioClip):
            raise TypeError(
                "Expected parameter `audioClip` to have type "
                "`psychopy.sound.AudioClip`.")
        
        # import here the first time
        import google.cloud.speech as speech
        import google.auth.exceptions

        # defaults
        languageCode = modelConfig.get('language', 'language_code')
        model = modelConfig.get('model', 'command_and_search')
        expectedWords = modelConfig.get('expectedWords', None)

        # configure the recognizer
        params = {
            'encoding': speech.RecognitionConfig.AudioEncoding.LINEAR16,
            'sample_rate_hertz': audioClip.sampleRateHz,
            'language_code': languageCode,
            'model': model,
            'audio_channel_count': audioClip.channels,
            'max_alternatives': 1}

        if isinstance(modelConfig, dict):  # overwrites defaults!
            params.update(modelConfig)

        # speech context (i.e. expected phrases)
        if expectedWords is not None:
            expectedWords, _ = _parseExpectedWords(expectedWords)
            params['speech_contexts'] = \
                [google.cloud.speech.SpeechContext(phrases=expectedWords)]

        # Detects speech in the audio file
        response = self._googleCloudClient.recognize(
            config=google.cloud.speech.RecognitionConfig(**params),
            audio=google.cloud.speech.RecognitionAudio(
                content=audioClip.convertToWAV()))

        # package up response
        result = [
            result.alternatives[0].transcript for result in response.results]
        toReturn = TranscriptionResult(
            words=result,
            unknownValue=False,  # not handled yet
            requestFailed=False,  # not handled yet
            engine='google',
            language=languageCode)
        toReturn.response = response

        self._lastResult = toReturn

        return toReturn


def _download(url, root, in_memory):
    """Download a model for the OpenAI Whisper speech-to-text transcriber.

    This function is monkey-patched to override the `_download()` function to 
    use the `requests` library to get models from remote sources. This gets 
    around the SSL certificate errors we see with `urllib`.

    """
    # derived from source code found here:
    # https://github.com/openai/whisper/blob/main/whisper/__init__.py
    import hashlib
    import os
    import requests
    import warnings

    os.makedirs(root, exist_ok=True)

    expected_sha256 = url.split("/")[-2]
    download_target = os.path.join(root, os.path.basename(url))

    if os.path.exists(download_target) and not os.path.isfile(download_target):
        raise RuntimeError(
            f"{download_target} exists and is not a regular file")

    if os.path.isfile(download_target):
        with open(download_target, "rb") as f:
            model_bytes = f.read()
        if hashlib.sha256(model_bytes).hexdigest() == expected_sha256:
            return model_bytes if in_memory else download_target
        else:
            warnings.warn(
                f"{download_target} exists, but the SHA256 checksum does not "
                f"match; re-downloading the file"
            )
    
    # here is the change we make that uses `requests` instead of `urllib`
    req = requests.get(url, allow_redirects=True)
    with open(download_target, 'wb') as dt:
        dt.write(req.content)

    model_bytes = open(download_target, "rb").read()
    if hashlib.sha256(model_bytes).hexdigest() != expected_sha256:
        raise RuntimeError(
            "Model has been downloaded but the SHA256 checksum does not not "
            "match. Please retry loading the model."
        )

    return model_bytes if in_memory else download_target



class WhisperTranscriber(BaseTranscriber):
    """Class for speech-to-text transcription using OpenAI Whisper.

    This class provides an interface for OpenAI Whisper for off-line (local) 
    speech-to-text transcription in various languages. You must first download
    the model used for transcription on the local machine.

    Parameters
    ----------
    initConfig : dict or None
        Options to configure the speech-to-text engine during initialization. 
    
    """
    _isLocal = True
    _engine = u'whisper'
    _longName = u"OpenAI Whisper"
    def __init__(self, initConfig=None):
        super(WhisperTranscriber, self).__init__(initConfig)

        # pull in imports
        import whisper
        whisper._download = _download  # patch download func using `requests`

        initConfig = {} if initConfig is None else initConfig

        self._device = initConfig.get('device', 'cpu')  # set the device
        self._modelName = initConfig.get('model_name', 'base')  # set the model

        # setup the model
        self._model = whisper.load_model(self._modelName).to(self._device)

    @property
    def device(self):
        """Device in use (`str`).
        """
        return self._device
    
    @property
    def model(self):
        """Model in use (`str`).
        """
        return self._modelName

    @staticmethod
    def downloadModel(modelName):
        """Download a model from the internet onto the local machine.
        
        Parameters
        ----------
        modelName : str
            Name of the model to download. You can get available models by 
            calling `getAllModels()`.

        Notes
        -----
        * In order to download models, you need to have the correct certificates
          installed on your system.
        
        """
        import whisper
        # todo - specify file name for the model
        whisper.load_model(modelName)  # calling this downloads the model

    @staticmethod
    def getAllModels():
        """Get available language models for the Whisper transcriber (`list`).

        Parameters
        ----------
        language : str
            Filter available models by specified language code.

        Returns
        -------
        list 
            List of available models.

        """
        import whisper

        return whisper.available_models()
    
    def transcribe(self, audioClip, modelConfig=None, decoderConfig=None):
        """Perform a speech-to-text transcription of a voice recording.

        Parameters
        ----------
        audioClip : AudioClip, ArrayLike
            Audio clip containing speech to transcribe (e.g., recorded from a
            microphone). Can be either an :class:`~psychopy.sound.AudioClip` 
            object or tuple where the first value is as a Nx1 or Nx2 array of 
            audio samples (`ndarray`) and the second the sample rate (`int`) in 
            Hertz (e.g., ``(samples, 48000)``).
        modelConfig : dict or None
            Configuration options for the model.
        decoderConfig : dict or None
            Configuration options for the decoder.

        Returns
        -------
        TranscriptionResult
            Transcription result instance.

        Notes
        -----
        * Audio is down-sampled to 16Khz prior to conversion which may add some
          overhead.

        """
        if isinstance(audioClip, AudioClip):  # use raw samples from mic
            samples = audioClip.samples
            sr = audioClip.sampleRateHz
        elif isinstance(audioClip, (list, tuple,)):
            samples, sr = audioClip

        # whisper requires data to be a flat `float32` array
        waveform = np.frombuffer(
            samples, samples.dtype).flatten().astype(np.float32)
        
        # resample if needed
        if sr != 16000:
            import librosa
            waveform = librosa.resample(
                waveform, 
                orig_sr=sr, 
                target_sr=16000)
        
        # pad and trim the data as required
        import whisper.audio as _audio
        waveform = _audio.pad_or_trim(waveform)

        modelConfig = {} if modelConfig is None else modelConfig
        decoderConfig = {} if decoderConfig is None else decoderConfig

        # our defaults
        language = "en" if self._modelName.endswith(".en") else None
        temperature = modelConfig.get('temperature', 0.0)
        word_timestamps = modelConfig.get('word_timestamps', True)

        # initiate the transcription
        result = self._model.transcribe(
            waveform, 
            language=language, 
            temperature=temperature, 
            word_timestamps=word_timestamps,
            **decoderConfig)
        
        transcribed = result.get('text', '')
        transcribed = transcribed.split(' ')  # split words 
        language = result.get('langauge', '')

        # create the response value
        toReturn = TranscriptionResult(
            words=transcribed,
            unknownValue=False,
            requestFailed=False,
            engine=self._engine,
            language=language)
        toReturn.response = str(result)  # provide raw JSON response

        self.lastResult = toReturn
        
        return toReturn


# ------------------------------------------------------------------------------
# Functions
#

def getAllTranscribers(engineKeys=False):
    """Get all available transcriber interfaces.

    Transcriber interface can be implemented in plugins. When loaded, this 
    function will return them. 

    Parameters
    ----------
    engineKeys : bool
        Have the returned mapping use engine names for keys instead of class 
        names.

    Returns
    -------
    dict
        Mapping of transcriber class or engine names (`str`) and references to 
        classes (subclasses of `BaseTranscriber`.)

    Examples
    --------
    Getting a transcriber interface, initializing it, and doing a 
    transcription::

        whisperInterface = sound.getAllTranscribers()['WhisperTranscriber']
        # create the instance which initialize the transcriber service
        transcriber = whisperInterface({'device': 'cuda'})
        # you can now begin transcribing audio
        micRecording = mic.getRecording()
        result = transcriber.transcribe(micRecording)

    """
    from psychopy.plugins import discoverModuleClasses

    # build a dictionary with names
    here = sys.modules[__name__]
    foundTranscribers = discoverModuleClasses(here, BaseTranscriber)
    del foundTranscribers['BaseTranscriber']  # remove base, not needed
 
    if not engineKeys:
        return foundTranscribers
    
    # remap using engine names, more useful for builder
    toReturn = {}
    for className, interface in foundTranscribers.items():
        if hasattr(interface, '_engine'):  # has interface
            toReturn[interface._engine] = interface

    return toReturn


def transcribe(audioClip, engine='sphinx', language='en-US', expectedWords=None,
               config=None):
    """Convert speech in audio to text.

    This feature passes the audio clip samples to a specified text-to-speech
    engine which will attempt to transcribe any speech within. The efficacy of
    the transcription depends on the engine selected, audio quality, and
    language support. By default, Pocket Sphinx is used which provides decent
    transcription capabilities offline for English and a few other languages.
    For more robust transcription capabilities with a greater range of language
    support, online providers such as Google may be used.

    Speech-to-text conversion blocks the main application thread when used on
    Python. Don't transcribe audio during time-sensitive parts of your
    experiment! This issue is known to the developers and will be fixed in a
    later release.

    Parameters
    ----------
    audioClip : :class:`~psychopy.sound.AudioClip` or tuple
        Audio clip containing speech to transcribe (e.g., recorded from a
        microphone). Can be either an :class:`~psychopy.sound.AudioClip` object
        or tuple where the first value is as a Nx1 or Nx2 array of audio
        samples (`ndarray`) and the second the sample rate (`int`) in Hertz
        (e.g., ``(samples, 480000)``).
    engine : str
        Speech-to-text engine to use. Can be one of 'sphinx' for CMU Pocket
        Sphinx or 'google' for Google Cloud.
    language : str
        BCP-47 language code (eg., 'en-US'). Note that supported languages
        vary between transcription engines.
    expectedWords : list or tuple
        List of strings representing expected words or phrases. This will
        constrain the possible output words to the ones specified. Note not all
        engines support this feature (only Sphinx and Google Cloud do at this
        time). A warning will be logged if the engine selected does not support
        this feature. CMU PocketSphinx has an additional feature where the
        sensitivity can be specified for each expected word. You can indicate
        the sensitivity level to use by putting a ``:`` after each word in the
        list (see the Example below). Sensitivity levels range between 0 and
        100. A higher number results in the engine being more conservative,
        resulting in a higher likelihood of false rejections. The default
        sensitivity is 80% for words/phrases without one specified.
    config : dict or None
        Additional configuration options for the specified engine. These
        are specified using a dictionary (ex. `config={'pfilter': 1}` will
        enable the profanity filter when using the `'google'` engine).

    Returns
    -------
    :class:`~psychopy.sound.transcribe.TranscriptionResult`
        Transcription result.

    Notes
    -----
    * Online transcription services (eg., Google) provide robust and accurate
      speech recognition capabilities with broader language support than offline
      solutions. However, these services may require a paid subscription to use,
      reliable broadband internet connections, and may not respect the privacy
      of your participants as their responses are being sent to a third-party.
      Also consider that a track of audio data being sent over the network can
      be large, users on metered connections may incur additional costs to run
      your experiment.
    * If the audio clip has multiple channels, they will be combined prior to
      being passed to the transcription service if needed.

    Examples
    --------
    Use a voice command as a response to a task::

        # after doing  microphone recording
        resp = mic.getRecording()

        transcribeResults = transcribe(resp)
        if transcribeResults.success:  # successful transcription
            words = transcribeResults.words
            if 'hello' in words:
                print('You said hello.')

    Specifying expected words with sensitivity levels when using CMU Pocket
    Sphinx:

        # expected words 90% sensitivity on the first two, default for the rest
        expectedWords = ['right:90', 'left:90', 'up', 'down']

        transcribeResults = transcribe(
            resp.samples,
            resp.sampleRateHz,
            expectedWords=expectedWords)

        if transcribeResults.success:  # successful transcription
            # process results ...

    Specifying the API key to use Google's Cloud service for speech-to-text::

        # set the environment variable
        import os
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = \
            "C:\\path\\to\\my\\key.json"

        # you can now call the transcriber ...
        results = transcribe(
            myRecording,
            engine='google',
            expectedWords=['left', 'right'])

        if results.success:
            print("You said: {}".format(results.words[0]))

    """
    # check if the engine parameter is valid
    engine = engine.lower()  # make lower case

    # check if we have necessary keys
    if engine in ('google',):
        alert(4615, strFields={'engine': engine})

    # if we got a tuple, convert to audio clip object
    if isinstance(audioClip, (tuple, list,)):
        samples, sampleRateHz = audioClip
        audioClip = AudioClip(samples, sampleRateHz)

    # pass data over to the appropriate engine for transcription
    if engine in ('sphinx', 'built-in'):
        return recognizeSphinx(
            audioClip,
            language=language,
            expectedWords=expectedWords,
            config=config)
    elif engine == 'google':
        return recognizeGoogle(
            audioClip,
            language=language,
            expectedWords=expectedWords,
            config=config)
    elif engine == 'whisper':
        return recognizeWhisper(
            audioClip,
            language=language,
            expectedWords=expectedWords,
            config=config)
    else:
        raise ValueError(
            f'Parameter `engine` for `transcribe()` should be one of '
            f'"sphinx", "built-in", "whisper" or "google" not "{engine}"')


def _parseExpectedWords(wordList, defaultSensitivity=80):
    """Parse expected words list.

    This function is used internally by other functions and classes within the
    `transcribe` module.

    Expected words or phrases are usually specified as a list of strings. CMU
    Pocket Sphinx allows for additional 'sensitivity' values for each phrase
    ranging from *0* to *100*. This function will generate to lists, first with
    just words and another with specified sensitivity values. This allows the
    user to specify sensitivity levels which can be ignored if the recognizer
    engine does not support it.

    Parameters
    ----------
    wordList : list of str
        List of words of phrases. Sensitivity levels for each can be specified
        by putting a value at the end of each string separated with a colon `:`.
        For example, ``'hello:80'`` for 80% sensitivity on 'hello'. Values are
        normalized between *0.0* and *1.0* when returned.
    defaultSensitivity : int or float
        Default sensitivity to use if a word does not have one specified between
        0 and 100%.

    Returns
    -------
    tuple
        Returns list of expected words and list of normalized sensitivities for
        each.

    Examples
    --------
    Specifying expected words to CMU Pocket Sphinx::

        words = [('hello:95', 'bye:50')]
        expectedWords = zip(_parseExpectedWords(words))

    """
    defaultSensitivity = defaultSensitivity / 100.  # normalized

    sensitivities = []
    if wordList is not None:
        # sensitivity specified as `word:80`
        wordListTemp = []
        for word in wordList:
            wordAndSense = word.split(':')
            if len(wordAndSense) == 2:  # specified as `word:80`
                word, sensitivity = wordAndSense
                sensitivity = int(sensitivity) / 100.
            else:
                word = wordAndSense[0]
                sensitivity = defaultSensitivity  # default is 80% confidence

            wordListTemp.append(word)
            sensitivities.append(sensitivity)

        wordList = wordListTemp

    return wordList, sensitivities


# ------------------------------------------------------------------------------
# Recognizers
#
# These functions are used to send off audio and configuration data to the
# indicated speech-to-text engine. Most of these functions are synchronous,
# meaning they block the application until they return. Don't run these in any
# time critical parts of your program.
#

_pocketSphinxTranscriber = None

def recognizeSphinx(audioClip=None, language='en-US', expectedWords=None,
                    config=None):
    """Perform speech-to-text conversion on the provided audio samples using
    CMU Pocket Sphinx.

    Parameters
    ----------
    audioClip : :class:`~psychopy.sound.AudioClip` or None
        Audio clip containing speech to transcribe (e.g., recorded from a
        microphone). Specify `None` to open a client without performing a
        transcription, this will reduce latency when the transcriber is invoked
        in successive calls.
    language : str
        BCP-47 language code (eg., 'en-US'). Should match the language which the
        speaker is using. Pocket Sphinx requires language packs to be installed
        locally.
    expectedWords : list or None
        List of strings representing expected words or phrases. This will
        attempt bias the possible output words to the ones specified if the
        engine is uncertain. Sensitivity can be specified for each expected
        word. You can indicate the sensitivity level to use by putting a ``:``
        after each word in the list (see the Example below). Sensitivity levels
        range between 0 and 100. A higher number results in the engine being
        more conservative, resulting in a higher likelihood of false rejections.
        The default sensitivity is 80% for words/phrases without one specified.
    config : dict or None
        Additional configuration options for the specified engine.

    Returns
    -------
    TranscriptionResult
        Transcription result object.

    """
    if config is None:
        config = {}  # empty dict if `None`

    onlyInitialize = audioClip is None
    global _pocketSphinxTranscriber
    if _pocketSphinxTranscriber is None:
        allTranscribers = getAllTranscribers(engineKeys=True)
        try:
            interface = allTranscribers['sphinx']
        except KeyError:
            raise RecognizerEngineNotFoundError(
                "Cannot load transcriber interface for 'sphinx'.")
    
        _pocketSphinxTranscriber = interface()  # create instance

    if onlyInitialize:
        return NULL_TRANSCRIPTION_RESULT
    
    # extract parameters which we used to support
    config['expectedWords'] = expectedWords
    config['language'] = language
    
    # do transcription and return result
    return _pocketSphinxTranscriber.transcribe(audioClip, modelConfig=config)


_googleCloudTranscriber = None  # keep instance for legacy functions

def recognizeGoogle(audioClip=None, language='en-US', expectedWords=None,
                    config=None):
    """Perform speech-to-text conversion on the provided audio clip using
    the Google Cloud API.

    This is an online based speech-to-text engine provided by Google as a
    subscription service, providing exceptional accuracy compared to `built-in`.
    Requires an API key to use which you must generate and specify prior to
    calling this function.

    Parameters
    ----------
    audioClip : :class:`~psychopy.sound.AudioClip` or None
        Audio clip containing speech to transcribe (e.g., recorded from a
        microphone). Specify `None` to open a client without performing a
        transcription, this will reduce latency when the transcriber is invoked
        in successive calls.
    language : str
        BCP-47 language code (eg., 'en-US'). Should match the language which the
        speaker is using.
    expectedWords : list or None
        List of strings representing expected words or phrases. These are passed
        as speech context metadata which will make the recognizer prefer a
        particular word in cases where there is ambiguity or uncertainty.
    config : dict or None
        Additional configuration options for the recognizer as a dictionary.

    Notes
    -----
    * The first invocation of this function will take considerably longer to run
      that successive calls as the client has not been started yet. Only one
      instance of a recognizer client can be created per-session.

    Examples
    --------
    Specifying the API key to use Google's Cloud service for speech-to-text::

        import os
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = \
            "C:\\path\\to\\my\\key.json"

        # you can now call the transcriber
        results = recognizeGoogle(myRecording, expectedWords=['left', 'right'])
        if results.success:
            print("You said: {}".format(results.words[0]))  # first word

    """
    if config is None:
        config = {}  # empty dict if `None`

    onlyInitialize = audioClip is None
    global _googleCloudTranscriber
    if _googleCloudTranscriber is None:
        allTranscribers = getAllTranscribers(engineKeys=True)
        try:
            interface = allTranscribers['googleCloud']
        except KeyError:
            raise RecognizerEngineNotFoundError(
                "Cannot load transcriber interface for 'googleCloud'.")
    
        _googleCloudTranscriber = interface()  # create instance

    if onlyInitialize:
        return NULL_TRANSCRIPTION_RESULT
    
    # set parameters which we used to support
    config['expectedWords'] = expectedWords
    config['language'] = language
    
    # do transcription and return result
    return _googleCloudTranscriber.transcribe(audioClip, modelConfig=config)


_whisperTranscriber = None

def recognizeWhisper(audioClip=None, language=None, expectedWords=None,
                     config=None):
    """Perform speech-to-text conversion on the provided audio samples locally 
    using OpenAI Whisper.

    This is a self-hosted (local) transcription engine. This means that the 
    actual transcription is done on the host machine, without passing data over 
    the network. 

    Parameters
    ----------
    audioClip : :class:`~psychopy.sound.AudioClip` or None
        Audio clip containing speech to transcribe (e.g., recorded from a
        microphone). Specify `None` to initialize a client without performing a
        transcription, this will reduce latency when the transcriber is invoked
        in successive calls. Any arguments passed to `config` will be sent to
        the initialization function of the model if `None`.
    language : str or None
        Language code (eg., 'en'). Unused for Whisper since models are 
        multi-lingual, but may be used in the future. 
    expectedWords : list or None
        List of strings representing expected words or phrases. This will
        attempt bias the possible output words to the ones specified if the
        engine is uncertain. Sensitivity can be specified for each expected
        word. You can indicate the sensitivity level to use by putting a ``:``
        after each word in the list (see the Example below). Sensitivity levels
        range between 0 and 100. A higher number results in the engine being
        more conservative, resulting in a higher likelihood of false rejections.
        The default sensitivity is 80% for words/phrases without one specified.
    config : dict or None
        Additional configuration options for the specified engine. For Whisper,
        the following configuration dictionary can be used 
        `{'device': "cpu", 'model_name': "base"}`. Values for `'device'` can be 
        either `'cpu'` or `'cuda'`, and `'model_name'` can be any value returned 
        by `.getAllModels()`. 

    Returns
    -------
    TranscriptionResult
        Transcription result object.

    """
    if config is None:
        config = {}  # empty dict if `None`

    # initialization options
    device = config.get('device', 'cpu')
    modelName = config.get('model_name', 'base')
    initConfig = {'device': device, 'model_name': modelName}

    onlyInitialize = audioClip is None
    global _whisperTranscriber
    if _whisperTranscriber is None:
        allTranscribers = getAllTranscribers(engineKeys=True)
        try:
            interface = allTranscribers['whisper']
        except KeyError:
            raise RecognizerEngineNotFoundError(
                "Cannot load transcriber interface for 'whisper'.")
    
        _whisperTranscriber = interface(initConfig)  # create instance
    
    if onlyInitialize:
        return NULL_TRANSCRIPTION_RESULT
    
    # set parameters which we used to support
    config['expectedWords'] = expectedWords
    config['language'] = language
    
    # do transcription and return result
    return _whisperTranscriber.transcribe(audioClip, modelConfig=config)


if __name__ == "__main__":
    pass
