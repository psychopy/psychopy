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
    'recognizerEngineValues',
    'recognizeSphinx',
    'recognizeGoogle'
]

import os
import psychopy.logging as logging
from psychopy.alerts import alert
from pathlib import Path
from psychopy.preferences import prefs
from .audioclip import *
from .exceptions import *

# ------------------------------------------------------------------------------
# Initialize the speech recognition system
#

_hasSpeechRecognition = True
try:
    import speech_recognition as sr
except (ImportError, ModuleNotFoundError):
    logging.warning(
        "Speech-to-text recognition module for PocketSphinx is not available "
        "(use command `pip install SpeechRecognition` to get it). "
        "Transcription will be unavailable using that service this session.")
    _hasSpeechRecognition = False

# Google Cloud API
_hasGoogleCloud = True
_googleCloudClient = None  # client for Google Cloud, instanced on first use
try:
    import google.cloud.speech
    import google.auth.exceptions
except (ImportError, ModuleNotFoundError):
    logging.warning(
        "Speech-to-text recognition using Google online services is not "
        "available (use command `pip install google-api-core google-auth "
        "google-cloud google-cloud-speech googleapis-common-protos` to get "
        "it). Transcription will be unavailable using that service this "
        "session.")
    _hasGoogleCloud = False

try:
    import pocketsphinx
    sphinxLangs = [folder.stem for folder
                   in Path(pocketsphinx.get_model_path()).glob('??-??')]
    haveSphinx = True
except (ImportError, ModuleNotFoundError):
    haveSphinx = False
    sphinxLangs = None

# Constants related to the transcription system.
TRANSCR_LANG_DEFAULT = 'en-US'

# Values for specifying recognizer engines. This dictionary is used by Builder
# to populate the component property dropdown.
recognizerEngineValues = {
    0: ('sphinx', "CMU Pocket Sphinx", "Offline, Built-in"),
    1: ('google', "Google Cloud Speech API", "Online, Key Required"),
}

# Get references to recognizers for various supported speech-to-text engines
# available through the `SpeechRecognition` package.
if _hasSpeechRecognition:
    _recogBase = sr.Recognizer()


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


# empty result returned when a transcriber is given no data
NULL_TRANSCRIPTION_RESULT = TranscriptionResult(
    words=[''],
    unknownValue=False,
    requestFailed=False,
    engine='null',
    language=TRANSCR_LANG_DEFAULT
)


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
    else:
        raise ValueError(
            f'Parameter `engine` for `transcribe()` should be one of '
            f'"sphinx", "built-in" or "google" not "{engine}"')


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
    if not haveSphinx:  # does not have Sphinx
        raise RecognizerEngineNotFoundError()

    # warmup the engine, not used here but needed for compatibility
    if audioClip is None:
        return NULL_TRANSCRIPTION_RESULT

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

    language = language.lower()
    if language not in sphinxLangs:  # missing a language pack error
        url = "https://sourceforge.net/projects/cmusphinx/files/" \
              "Acoustic%20and%20Language%20Models/"
        msg = (f"Language `{language}` is not installed for "
               f"`pocketsphinx`. You can download languages here: {url}. "
               f"Install them here: {pocketsphinx.get_model_path()}")
        raise RecognizerLanguageNotSupportedError(msg)

    # configure the recognizer
    config['language'] = language  # sphinx users en-us not en-US
    config['show_all'] = False
    if expectedWords is not None:
        words, sens = _parseExpectedWords(expectedWords)
        config['keyword_entries'] = tuple(zip(words, sens))

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
            print("You said: {}".format(results.words[0]))

    """
    global _googleCloudClient
    if _googleCloudClient is None:
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
            _googleCloudClient = google.cloud.speech.SpeechClient()
        except google.auth.exceptions.DefaultCredentialsError:
            raise RecognizerAPICredentialsError(
                'Invalid key specified for Google Cloud Services, check if the '
                'key file is valid and readable.')

    # if None, return a null transcription result and just open a client
    if audioClip is None:
        return NULL_TRANSCRIPTION_RESULT

    # check if we have a valid audio clip
    if not isinstance(audioClip, AudioClip):
        raise TypeError(
            "Expected parameter `audioClip` to have type "
            "`psychopy.sound.AudioClip`.")

    # configure the recognizer
    params = {
        'encoding': google.cloud.speech.RecognitionConfig.AudioEncoding.LINEAR16,
        'sample_rate_hertz': audioClip.sampleRateHz,
        'language_code': language,
        'model': 'command_and_search',
        'audio_channel_count': audioClip.channels,
        'max_alternatives': 1}

    if isinstance(config, dict):
        params.update(config)

    # speech context (i.e. expected phrases)
    if expectedWords is not None:
        expectedWords, _ = _parseExpectedWords(expectedWords)
        params['speech_contexts'] = \
            [google.cloud.speech.SpeechContext(phrases=expectedWords)]

    # Detects speech in the audio file
    response = _googleCloudClient.recognize(
        config=google.cloud.speech.RecognitionConfig(**params),
        audio=google.cloud.speech.RecognitionAudio(
            content=audioClip.convertToWAV()))

    # package up response
    result = [result.alternatives[0].transcript for result in response.results]
    toReturn = TranscriptionResult(
        words=result,
        unknownValue=False,  # not handled yet
        requestFailed=False,  # not handled yet
        engine='google',
        language=language)

    return toReturn


if __name__ == "__main__":
    pass
