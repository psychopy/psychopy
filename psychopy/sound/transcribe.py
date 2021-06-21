#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Classes and functions for transcribing speech in audio data to text.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'TranscriptionResult',
    'transcribe',
    'TRANSCR_LANG_DEFAULT',
    'transcriberEngineValues',
    'apiKeyNames',
    'refreshTranscrKeys',
    'RecognizerLanguageNotSupportedError',
    'RecognizerEngineNotFoundError'
]

import os
import psychopy.logging as logging
from psychopy.alerts import alert
import numpy as np
from pathlib import Path
from psychopy.preferences import prefs
from psychopy.sound import AudioClip

# ------------------------------------------------------------------------------
# Initialize the speech recognition system
#

_hasSpeechRecognition = True
try:
    import speech_recognition as sr
except (ImportError, ModuleNotFoundError):
    logging.warning(
        "Speech-to-text recognition module not available (use command `pip "
        "install SpeechRecognition` to get it. Transcription will be "
        "unavailable.")
    _hasSpeechRecognition = False

# Google Cloud API
_hasGoogleCloud = True
_googleCloudClient = None  # client for Google Cloud, instanced on first use
try:
    import google.cloud.speech
except (ImportError, ModuleNotFoundError):
    _hasGoogleCloud = False

try:
    import pocketsphinx
    sphinxLangs = [folder.stem for folder
                   in Path(pocketsphinx.get_model_path()).glob('??-??')]
    haveSphinx = True
except ModuleNotFoundError:
    haveSphinx = False
    sphinxLangs = None

# Constants related to the transcription system.
TRANSCR_LANG_DEFAULT = 'en-US'

# Values for specifying transcriber engine. This dictionary is used by Builder
# to populate the component property dropdown.
transcriberEngineValues = {
    0: ('sphinx', "CMU Pocket Sphinx", "Offline, Built-in"),
    1: ('google', "Google Speech Recognition", "Online"),
    2: ('googleCloud', "Google Cloud Speech API", "Online, Key Required"),
    3: ('azure', "Microsoft Azure/Bing Voice Recognition",
        "Online, Key Required")
}

# Names of environment variables which API keys may be stored. These cover
# online services only.
apiKeyNames = {
    'google': ('PSYCHOPY_TRANSCR_KEY_GOOGLE', 'transcrKeyGoogle'),
    'googleCloud':
        ('PSYCHOPY_TRANSCR_KEY_GOOGLE_CLOUD', 'transcrKeyGoogleCloud'),
    'bing': ('PSYCHOPY_TRANSCR_KEY_AZURE', 'transcrKeyAzure')  # alias Azure
}

# Get references to recognizers for various supported speech-to-text engines
# available through the `SpeechRecognition` package.
_recognizers = {}
_apiKeys = {}  # API key loaded
if _hasSpeechRecognition:
    _recogBase = sr.Recognizer()
    _recognizers['sphinx'] = _recogBase.recognize_sphinx
    _recognizers['built-in'] = _recognizers['sphinx']  # aliased
    _recognizers['google'] = _recogBase.recognize_google
    _recognizers['googleCloud'] = _recogBase.recognize_google_cloud
    _recognizers['bing'] = _recogBase.recognize_bing
    _recognizers['azure'] = _recognizers['bing']

    # Get API keys for each engine here. Calling `refreshTranscrKeys()`
    # finalizes these values. If any of these are not defined as environment
    # variables, they will be obtained from preferences.
    _apiKeys['google'] = _apiKeys['googleCloud'] = _apiKeys['bing'] = None
    _apiKeys['azure'] = _apiKeys['bing']


# ------------------------------------------------------------------------------
# Exceptions
#

class RecognizerLanguageNotSupportedError(ValueError):
    """Raised when the specified language is not supported by the engine. If you
    get this, you need to install the appropriate language support or select
    another language.
    """


class RecognizerEngineNotFoundError(ModuleNotFoundError):
    """Raised when the specified recognizer cannot be found. Usually get this
    error if the required packages are not installed for a recognizer that is
    invoked.
    """


# ------------------------------------------------------------------------------
# Classes and functions for speech-to-text transcription
#

class TranscriptionResult(object):
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
        '_confidence',  # unused on Python for now
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

    @words.setter
    def words(self, value):
        self._words = list(value)

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


def transcribe(audioClip, engine='sphinx', language='en-US', expectedWords=None,
               key=None, config=None):
    """Convert speech in audio to text.

    This feature passes the audio clip samples to a text-to-speech engine which
    will attempt to transcribe any speech within. The efficacy of the
    transcription depends on the engine selected, recording hardware and audio
    quality, and quality of the language support. By default, Pocket Sphinx is
    used which provides decent transcription capabilities offline for English
    and a few other languages. For more robust transcription capabilities with a
    greater range of language support, online providers such as Google may be
    used.

    If the audio clip has multiple channels, they will be combined prior to
    being passed to the transcription service.

    Speech-to-text conversion blocks the main application thread when used on
    Python. Don't transcribe audio during time-sensitive parts of your
    experiment! This issue is known to the developers and will be fixed in a
    later release.

    Parameters
    ----------
    audioClip : :class:`~psychopy.sound.AudioClip` or tuple
        Audio clip containing speech to transcribe (e.g., recorded from a
        microphone). Can be either an :class:`~psychopy.sound.AudioClip` object
        or tuple where the first values is as a Nx1 or Nx2 array of audio
        samples and the second the sample rate in Hertz (e.g.,
        ``(samples, 480000)``).
    engine : str
        Speech-to-text engine to use. Can be one of 'sphinx' or 'google'.
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
    key : str or None
        API key or credentials, format depends on the API in use. If `None`,
        the values will be obtained elsewhere (See Notes). An alert will be
        raised if the `engine` requested requires a key but is not specified.
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
    * Online transcription services (eg., Google, Bing, etc.) provide robust
      and accurate speech recognition capabilities with broader language
      support than offline solutions. However, these services may require a
      paid subscription to use, reliable broadband internet connections, and
      may not respect the privacy of your participants as their responses
      are being sent to a third-party. Also consider that a track of audio
      data being sent over the network can be large, users on metered
      connections may incur additional costs to run your experiment.
    * Some errors may be emitted by the `SpeechRecognition` API, check that
      project's documentation if you encounter such an error for more
      information.
    * If `key` is not specified (i.e. is `None`) then PsychoPy will look for the
      API key at other locations. By default, PsychoPy will look for an
      environment variables starting with `PSYCHOPY_TRANSCR_KEY_` first. If
      there is no appropriate API key for the given `engine`, then the
      preference *General -> transcrKeyXXX* is used. Keys can be specified as a
      file path, if so, the key data will be loaded from the file. System
      administrators can specify keys this way to use them across a site
      installation without needing the user manage the keys directly.
    * Use `expectedWords` if provided by the API. This will greatly speed up
      recognition. CMU Pocket Sphinx gives the option for sensitivity levels per
      phrase.

    Examples
    --------
    Use a voice command as a response to a task::

        # after doing  microphone recording
        resp = mic.getRecording()

        transcribeResults = transcribe(resp.samples, resp.sampleRateHz)
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

    """
    # check if the engine parameter is valid
    engine = engine.lower()  # make lower case
    if engine not in _recognizers.keys():
        raise ValueError(
            f'Parameter `engine` for `transcribe()` should be one of '
            f'{list(_recognizers.keys())} not {engine}')

    # check if we have necessary keys
    if engine in _apiKeys:
        if not _apiKeys[engine]:
            alert(4615, strFields={'engine': engine})

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


def refreshTranscrKeys():
    """Refresh transcription engine API keys. Call this if any of the keys have
    been updated since starting the PsychoPy session.
    """
    global _apiKeys
    global apiKeyNames

    # go over each supported engine and load the key
    for engineName, keyVal in _apiKeys.items():
        if engineName == 'azure':  # skip MS Azure for now, alias of Bing
            continue

        envVarName, prefName = apiKeyNames[engineName]

        # check if the engine key is provided as an environment variable
        envVal = os.environ.get(envVarName, None)

        # if an environment variable is not defined, look into prefs
        if envVal is None:
            keyVal = prefs.general[prefName]
            if keyVal == '':  # empty string means None
                keyVal = None
        else:
            keyVal = envVal

        # Check if we are dealing with a file path, if so load the data as the
        # key value.
        if keyVal is not None:
            if os.path.isfile(keyVal):
                with open(keyVal, 'r') as keyFile:
                    keyVal = keyFile.read()

        _apiKeys[engineName] = keyVal

    # hack to get 'bing' and 'azure' recognized as the same
    if 'bing' in _apiKeys.keys():
        _apiKeys['azure'] = _apiKeys['bing']


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

def recognizeSphinx(audioClip, language='en-US', expectedWords=None,
                    config=None):
    """Perform speech-to-text conversion on the provided audio samples using
    CMU Pocket Sphinx.

    Parameters
    ----------
    audioClip : :class:`~psychopy.sound.AudioClip`
        Audio clip containing speech to transcribe (e.g., recorded from a
        microphone).
    language : str
        BCP-47 language code (eg., 'en-US'). Should match the language which the
        speaker is using. Pocket Sphinx requires language packs to be installed
        locally.
    expectedWords : list or None
        List of strings representing expected words or phrases. This will
        attempt bias the possible output words to the ones specified if the
        engine is uncertain. Note not all engines support this feature (only Sphinx and Google Cloud do at
        this time). A warning will be logged if the engine selected does not
        support this feature. CMU PocketSphinx has an additional feature where
        the sensitivity can be specified for each expected word. You can
        indicate the sensitivity level to use by putting a ``:`` after each word
        in the list (see the Example below). Sensitivity levels range between 0
        and 100. A higher number results in the engine being more conservative,
        resulting in a higher likelihood of false rejections. The default
        sensitivity is 80% for words/phrases without one specified.
    config : dict or None
        Additional configuration options for the specified engine.

    Returns
    -------
    TranscriptionResult
        Transcription result object.

    """
    if not haveSphinx:  # does not have Sphinx
        raise RecognizerEngineNotFoundError()

    if language not in sphinxLangs:  # missing a language pack error
        url = "https://sourceforge.net/projects/cmusphinx/files/" \
              "Acoustic%20and%20Language%20Models/"
        msg = (f"Language `{config['language']}` is not installed for "
               f"`pocketsphinx`. You can download languages here: {url}. "
               f"Install them here: {pocketsphinx.get_model_path()}")
        raise RecognizerLanguageNotSupportedError(msg)

    # check if we have a valid audio clip
    if not isinstance(audioClip, AudioClip):
        raise TypeError(
            "Expected parameter `audioClip` to have type "
            "`psychopy.sound.AudioClip`.")

    # engine configuration
    config = {} if config is None else config
    if not isinstance(config, dict):
        raise TypeError(
            "Invalid type for parameter `config` specified, must be `dict` "
            "or `None`.")

    if not isinstance(language, str):
        raise TypeError(
            "Invalid type for parameter `language`, must be type `str`.")

    # configure the recognizer
    config['language'] = language.lower()  # sphinx users en-us not en-US
    config['show_all'] = False
    if expectedWords is not None:
        config['keyword_entries'] = zip(_parseExpectedWords(expectedWords))

    # convert audio to format for transcription
    sampleWidth = 2  # two bytes per sample
    audioData = sr.AudioData(
        audioClip.asMono().convertToWAV(),
        sample_rate=audioClip.sampleRateHz,
        sample_width=sampleWidth)

    # submit audio samples to the API
    respAPI = ''
    unknownValueError = requestError = False
    try:
        respAPI = _recogBase.recognize_sphinx(audioData, **config)
    except sr.UnknownValueError:
        unknownValueError = True
    except sr.RequestError:
        requestError = True

    # remove empty words
    result = [word for word in respAPI.split(' ') if word != '']

    # object to return containing transcription data
    toReturn = TranscriptionResult(
        words=result,
        unknownValue=unknownValueError,
        requestFailed=requestError,
        engine='sphinx',
        language=language)

    # split only if the user does not want the raw API data
    return toReturn


def recognizeGoogle(audioClip, language='en-US', expectedWords=None,
                    config=None):
    """Perform speech-to-text conversion on the provided audio samples using
    the Google Cloud API.

    The first invocation of this function will take considerably longer to run
    that successive calls as the client has not been started yet. Call
    `initClient` prior to

    Parameters
    ----------
    audioClip : :class:`~psychopy.sound.AudioClip`
        Audio clip containing speech to transcribe (e.g., recorded from a
        microphone).
    language : str
        BCP-47 language code (eg., 'en-US'). Should match the language which the
        speaker is using.

    """
    global _googleCloudClient
    if _googleCloudClient is None:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = _apiKeys['googleCloud']
        _googleCloudClient = \
            google.cloud.speech.SpeechClient.from_service_account_file(
                _apiKeys['googleCloud'])

    # check if we have a valid audio clip
    if not isinstance(audioClip, AudioClip):
        raise TypeError(
            "Expected parameter `audioClip` to have type "
            "`psychopy.sound.AudioClip`.")

    # convert to the correct format for upload
    params = {
        'encoding': google.cloud.speech.RecognitionConfig.AudioEncoding.LINEAR16,
        'sample_rate_hertz': audioClip.sampleRateHz,
        'language_code': language}
    audio = google.cloud.speech.RecognitionAudio(
        content=audioClip.asMono().convertToWAV())
    config = google.cloud.speech.RecognitionConfig(**params)

    # Detects speech in the audio file
    response = _googleCloudClient.recognize(config=config, audio=audio)

    return [result.alternatives[0].transcript for result in response.results]


# initial call to populate the API key values
refreshTranscrKeys()


if __name__ == "__main__":
    pass
