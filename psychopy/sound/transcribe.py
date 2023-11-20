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
    'recognizerEngineValues',
    'recognizeSphinx',
    'recognizeGoogle',
    'getAllTranscriberInterfaces',
    'getTranscriberInterface',
    'setupTranscriber',
    'getActiveTranscriber',
    'getActiveTranscriberEngine',
    'submit'
]

import json
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
    0: ('sphinx', "CMU Pocket Sphinx", "Offline"),
    1: ('google', "Google Cloud Speech API", "Online, Key Required"),
    2: ('whisper', "OpenAI Whisper", "Offline, Built-in")
}

# the active transcriber interface
_activeTranscriber = None


# ------------------------------------------------------------------------------
# Exceptions for the speech recognition interface
#

class TranscriberError(Exception):
    """Base class for transcriber exceptions.
    """
    pass


class TranscriberNotSetupError(TranscriberError):
    """Exception raised when a transcriber interface has not been setup.
    """
    pass


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
        '_wordData',  # additional word data
        '_text',  # unused for now, will be used in future
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

        # initialize other fields
        self._wordData = None
        self._text = ""  
        self._confidence = 0.0  
        self._response = None
        self._expectedWords = None
        self._requestFailed = True
        self._unknownValue = True

    def __repr__(self):
        return (f"TranscriptionResult(words={self._words}, "
                f"unknownValue={self._unknownValue}, ",
                f"requestFailed={self._requestFailed}, ",
                f"engine={self._engine}, ",
                f"language={self._language})")

    def __str__(self):
        return " ".join(self._words)

    def __json__(self):
        return str(self)

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

    @property
    def responseData(self):
        """
        Values from self.response, parsed into a `dict`.
        """
        return json.loads(self.response)

    @responseData.setter
    def responseData(self, val):
        self._response = str(val)

    @property
    def wordData(self):
        """Additional data about each word (`list`).

        Not all engines provide this data in the same format or at all.
        """
        return self._wordData

    @wordData.setter
    def wordData(self, val):
        self._wordData = val

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
        self._lastResult = NULL_TRANSCRIPTION_RESULT  # dummy value

        return self._lastResult

    def unload(self):
        """Unload the transcriber interface.

        This method is called when the transcriber interface is no longer
        needed. This is useful for freeing up resources used by the transcriber
        interface.

        This might not be available on all transcriber interfaces.

        """
        pass


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
    

# ------------------------------------------------------------------------------
# Functions
#

def getAllTranscriberInterfaces(engineKeys=False):
    """Get all available transcriber interfaces.

    Transcriber interface can be implemented in plugins. When loaded, this 
    function will return them. 

    It is not recommended to work with transcriber interfaces directly. Instead,
    setup a transcriber interface using `setupTranscriber()` and use
    `submit()` to perform transcriptions.

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


def getTranscriberInterface(engine):
    """Get a transcriber interface by name.

    It is not recommended to work with transcriber interfaces directly. Instead,
    setup a transcriber interface using `setupTranscriber()` and use
    `submit()` to perform transcriptions.

    Parameters
    ----------
    engine : str
        Name of the transcriber interface to get.

    Returns
    -------
    Subclass of `BaseTranscriber`
        Transcriber interface.

    Examples
    --------
    Get a transcriber interface and initalize it::

        whisperInterface = getTranscriberInterface('whisper')
        # initialize it
        transcriber = whisperInterface({'device': 'cuda'})
    
    """
    transcribers = getAllTranscriberInterfaces(engineKeys=True)

    try:
        transcriber = transcribers[engine]
    except KeyError:
        raise ValueError(
            f"Transcriber with engine name `{engine}` not found.")

    return transcriber


def setupTranscriber(engine, config=None):
    """Setup a transcriber interface.

    Calling this function will instantiate a transcriber interface and perform
    any necessary setup steps. This function is useful for performing the
    initialization step without blocking the main thread during a time-sensitive
    part of the experiment.

    You can only instantiate a single transcriber interface at a time. Calling
    this function will replace the existing transcriber interface if one is
    already setup.

    Parameters
    ----------
    engine : str
        Name of the transcriber interface to setup.
    config : dict or None
        Options to configure the speech-to-text engine during initialization.
    
    """
    engine = engine.lower()  # make lower case

    global _activeTranscriber
    if _activeTranscriber is not None:
        oldInterface = _activeTranscriber.engine
        logging.warning(
            "Transcriber interface already setup, replacing existing "
            "interface `{}` with `{}`".format(oldInterface, engine))

        # unload the model if the interface supports it
        if hasattr(_activeTranscriber, 'unload'):
            _activeTranscriber.unload()

        _activeTranscriber = None

    logging.debug(f"Setting up transcriber `{engine}` with options `{config}`.")
    transcriber = getTranscriberInterface(engine)
    _activeTranscriber = transcriber(config)  # init the transcriber


def getActiveTranscriber():
    """Get the currently active transcriber interface instance.

    Should return a subclass of `BaseTranscriber` upon a successful call to
    `setupTranscriber()`, otherwise `None` is returned.

    Returns
    -------
    Subclass of `BaseTranscriber` or None
        Active transcriber interface instance, or `None` if none is active.

    """
    global _activeTranscriber
    return _activeTranscriber


def getActiveTranscriberEngine():
    """Get the name currently active transcriber interface.

    Should return a string upon a successful call to `setupTranscriber()`, 
    otherwise `None` is returned.

    Returns
    -------
    str or None
        Name of the active transcriber interface, or `None` if none is active.

    """
    activeTranscriber = getActiveTranscriber()
    if activeTranscriber is None:
        return None

    return activeTranscriber.engine


def submit(audioClip, config=None):
    """Submit an audio clip for transcription.

    This will begin the transcription process using the currently loaded 
    transcriber and return when completed. Unlike `transcribe`, not calling 
    `setupTranscriber` before calling this function will raise an exception.

    Parameters
    ----------
    audioClip : :class:`~psychopy.sound.AudioClip` or tuple
        Audio clip containing speech to transcribe (e.g., recorded from a
        microphone). Can be either an :class:`~psychopy.sound.AudioClip` object
        or tuple where the first value is as a Nx1 or Nx2 array of audio
        samples (`ndarray`) and the second the sample rate (`int`) in Hertz
        (e.g., `(samples, 48000)`).
    config : dict or None
        Additional configuration options for the specified engine. These
        are specified using a dictionary (ex. `config={'pfilter': 1}` will
        enable the profanity filter when using the `'google'` engine).

    Returns
    -------
    TranscriptionResult
        Result of the transcription.

    """
    global _activeTranscriber
    if getActiveTranscriberEngine() is None:
        raise TranscriberNotSetupError(
            "No transcriber interface has been setup, call `setupTranscriber` "
            "before calling `submit`.")

    return _activeTranscriber.transcribe(audioClip, config=config)


def transcribe(audioClip, engine='whisper', language='en-US', expectedWords=None,
               config=None):
    """Convert speech in audio to text.

    This function accepts an audio clip and returns a transcription of the
    speech in the clip. The efficacy of the transcription depends on the engine 
    selected, audio quality, and language support.

    Speech-to-text conversion blocks the main application thread when used on
    Python. Don't transcribe audio during time-sensitive parts of your
    experiment! Instead, initialize the transcriber before the experiment
    begins by calling this function with `audioClip=None`.

    Parameters
    ----------
    audioClip : :class:`~psychopy.sound.AudioClip` or tuple
        Audio clip containing speech to transcribe (e.g., recorded from a
        microphone). Can be either an :class:`~psychopy.sound.AudioClip` object
        or tuple where the first value is as a Nx1 or Nx2 array of audio
        samples (`ndarray`) and the second the sample rate (`int`) in Hertz
        (e.g., `(samples, 48000)`). Passing `None` will initialize the
        the transcriber without performing a transcription. This is useful for
        performing the initialization step without blocking the main thread 
        during a time-sensitive part of the experiment.
    engine : str
        Speech-to-text engine to use.
    language : str
        BCP-47 language code (eg., 'en-US'). Note that supported languages
        vary between transcription engines.
    expectedWords : list or tuple
        List of strings representing expected words or phrases. This will
        constrain the possible output words to the ones specified which 
        constrains the model for better accuracy. Note not all engines support 
        this feature (only Sphinx and Google Cloud do at this time). A warning 
        will be logged if the engine selected does not support this feature. CMU 
        PocketSphinx has an additional feature where the sensitivity can be 
        specified for each expected word. You can indicate the sensitivity level 
        to use by putting a ``:`` after each word in the list (see the Example 
        below). Sensitivity levels range between 0 and 100. A higher number 
        results in the engine being more conservative, resulting in a higher 
        likelihood of false rejections. The default sensitivity is 80% for 
        words/phrases without one specified.
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
    * The recommended transcriber is OpenAI Whisper which can be used locally
      without an internet connection once a model is downloaded to cache. It can 
      be selected by passing `engine='whisper'` to this function.
    * Online transcription services (eg., Google) provide robust and accurate
      speech recognition capabilities with broader language support than offline
      solutions. However, these services may require a paid subscription to use,
      reliable broadband internet connections, and may not respect the privacy
      of your participants as their responses are being sent to a third-party.
      Also consider that a track of audio data being sent over the network can
      be large, users on metered connections may incur additional costs to run
      your experiment. Offline transcription services (eg., CMU PocketSphinx and 
      OpenAI Whisper) do not require an internet connection after the model has
      been downloaded and installed.
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

    Initialize the transcriber without performing a transcription::

        # initialize the transcriber
        transcribe(None, config={
            'model_name': 'tiny.en',
            'device': 'auto'}
        )

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

    if config is None:
        config = {}

    global _activeTranscriber
    if _activeTranscriber is None:
        logging.warning(
            "Called `transcribe` before calling `setupTranscriber`. The "
            "transcriber interface will be initialized now. If this is a "
            "time sensitive part of your experiment, consider calling "
            "`setupTranscriber` before any experiment routine begins.")
        setupTranscriber(engine, config=config)

        return NULL_TRANSCRIPTION_RESULT

    # check if we have necessary keys
    if engine in ('google',):
        alert(4615, strFields={'engine': engine})

    # if we got a tuple, convert to audio clip object
    if isinstance(audioClip, (tuple, list,)):
        samples, sampleRateHz = audioClip
        audioClip = AudioClip(samples, sampleRateHz)

    # bit of a hack for the wisper transcriber
    if engine == 'whisper':
        # trim the language specifier, this should be close enough for now
        langSplit = language.split('-')
        if len(langSplit) > 1:
            language = langSplit[0]
        else:
            language = language
    else:
        config['expectedWords'] = expectedWords
        config['language'] = language

    # do the actual transcription
    return _activeTranscriber.transcribe(
        audioClip,
        language=language,
        expectedWords=expectedWords,
        config=config)


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


if __name__ == "__main__":
    pass
