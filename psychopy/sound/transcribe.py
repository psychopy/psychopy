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
    'TRANSCRIPTION_LANG_DEFAULT',
    'transcriberEngineValues'
]

import os
import psychopy.logging as logging
import numpy as np
from psychopy.preferences import prefs

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


# Get references to recognizers for various supported speech-to-text engines
# available through the `SpeechRecognition` package.
_recognizers = {}
_apiKey = ''  # API key loaded by _getAPIKey()
if _hasSpeechRecognition:
    _recognizers['sphinx'] = sr.Recognizer().recognize_sphinx
    _recognizers['google'] = sr.Recognizer().recognize_google
    _recognizers['googleCloud'] = sr.Recognizer().recognize_google_cloud
    _recognizers['bing'] = sr.Recognizer().recognize_bing
    _recognizers['azure'] = _recognizers['bing']

# Constants related to the transcription system.
TRANSCRIPTION_LANG_DEFAULT = 'en-US'

# Values for specifying transcriber engine. This dictionary is used by Builder
# to populate the component property dropdown.
transcriberEngineValues = {
    0: ('sphinx', "CMU Pocket Sphinx", "Offline, Built-in"),
    1: ('google', "Google Speech Recognition", "Online"),
    2: ('googleCloud', "Google Cloud Speech API", "Online, Key Required"),
    3: ('bing', "Microsoft Bing Voice Recognition", "Online, Key Required")
}


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
        For instance, network error or improper formatting of the audio data.
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


def transcribe(samples, sampleRate, engine='sphinx', language='en-US',
               expectedWords=(), key=None, config=None):
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
    samples : ArrayLike
        Audio clip containing speech to transcribe (e.g., recorded from a
        microphone) as a Nx1 or Nx2 array.
    sampleRate : int or float
        Sample rate which `samples` was recorded in Hertz (Hz).
    engine : str
        Speech-to-text engine to use. Can be one of 'sphinx', 'google',
        'googleCloud', or 'bing'.
    language : str
        BCP-47 language code (eg., 'en-US'). Note that supported languages
        vary between transcription engines.
    expectedWords : list or tuple
        List of strings representing expected words. This will constrain the
        possible output words to the ones specified. Note not all engines
        support this feature (only Sphinx and Google Cloud do at this time).
        A warning will be logged if the engine selected does not support
        this feature.
    key : str or None
        API key or credentials, format depends on the API in use. If `None`,
        the values will be obtained elsewhere (See Notes).
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
      environment variable called `PSYCHOPY_TRANSCRIBE_KEY` first. If that is
      not defined, then the preference *General -> transcribeKey* is used. Keys
      can be specified as a file path, if so, the key data will be loaded from
      the file. System administrators can specify keys this way to use them
      across a site installation without needing the user manage the keys
      directly.

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

    """
    # Bunch of checks to make sure the parameters specified are correct.
    if not _hasSpeechRecognition:  # don't have speech recognition
        raise ModuleNotFoundError(
            "Cannot use `.transcribe()`, missing required module "
            "`speech_recognition` from package `SpeechRecognition`.")

    # check if the engine parameter is valid
    if engine not in _recognizers.keys():
        raise ValueError(
            'Parameter `engine` for `transcribe()` is not a valid value.')

    # engine configuration
    config = {} if config is None else config
    if not isinstance(config, dict):
        raise TypeError(
            "Invalid type for parameter `config` specified, must be `dict` "
            "or `None`.")

    if not isinstance(language, str):
        raise TypeError(
            "Invalid type for parameter `language`, must be type `str`.")

    # common engine configuration options
    config['language'] = language  # set language code
    config['show_all'] = False

    # API specific config
    expectedWordsNotSupported = requiresKey = False
    if engine == 'sphinx':
        config['keyword_entries'] = expectedWords
    elif engine == 'googleCloud':
        config['preferred_phrases'] = expectedWords
        requiresKey = True
    elif engine == 'google':
        expectedWordsNotSupported = True
    elif engine in ('bing', 'azure'):
        expectedWordsNotSupported = True
        requiresKey = True

    if expectedWordsNotSupported:
        logging.warning(
            "Engine '{engine}' does not allow for expected phrases to "
            "be specified.".format(engine=engine))

    # API requires a key
    if requiresKey:
        config['key'] = _getAPIKey() if key is None else key
        if config['key'] is None:  # could not load a key
            logging.warning(
                "Selected speech-to-text engine '{}' requires a key but "
                "`None` is specified.")

    # combine channels if needed
    if samples.shape[1] > 1:
        samplesMixed = \
            np.sum(samples, axis=1, dtype=np.float32) / np.float32(2.)
    else:
        samplesMixed = samples

    # convert samples to WAV PCM format
    clipDataInt16 = np.asarray(
        samplesMixed * ((1 << 15) - 1), dtype=np.int16).tobytes()

    sampleWidth = 2  # two bytes per sample
    audio = sr.AudioData(clipDataInt16,
                         sample_rate=sampleRate,
                         sample_width=sampleWidth)

    config = {} if config is None else config
    assert isinstance(config, dict)

    # submit audio samples to the API
    respAPI = ''
    unknownValueError = requestError = False
    engine = engine.lower()
    try:
        respAPI = _recognizers[engine.lower()](audio, **config)
    except KeyError:
        raise ValueError("Invalid transcriber `engine` specified.")
    except sr.UnknownValueError:
        unknownValueError = True
    except sr.RequestError:
        requestError = True

    # object to return containing transcription data
    toReturn = TranscriptionResult(
        words=respAPI.split(' '),
        unknownValue=unknownValueError,
        requestFailed=requestError,
        engine=engine,
        language=language)

    # split only if the user does not want the raw API data
    return toReturn


def _getAPIKey(refresh=False):
    """Get the API key for the transcriber.

    The API key is used to access web-based transcription services. Usually the
    key is a string which is passed along to the API along with the audio data.
    The key can be specified in multiple ways, either as a string or within a
    plain-text file, given as an environment variable or preference. If an
    environment variable is present, it will be used over the value specified in
    preferences.

    PsychPy looks for an environment variable called ``PSYCHOPY_TRANSCRIBE_KEY``
    first. If not found, the preference `General -> transcribeKey` is used.

    Parameters
    ----------
    refresh : bool
        Refresh the API key. If `False`, the key will only be updated when this
        module is first loaded. This function will always return that value. If
        `True`, the value will be refreshed.

    Returns
    -------
    str
        API key data.

    """
    global _apiKey
    if _apiKey is not None and not refresh:  # hasn't been loaded yet
        return _apiKey

    # check if we have an environment variable set
    keyEnv = os.environ.get('PSYCHOPY_TRANSCRIBE_KEY', None)

    # no environment variable? get the key from preferences
    if keyEnv is None:
        keyValue = prefs.general['transcribeKey']
    else:
        keyValue = keyEnv

    # check if the user specified a file name
    if not os.path.isfile(keyValue):
        _apiKey = keyValue
        return _apiKey

    with open(keyValue, 'r') as keyFile:
        keyData = keyFile.read()

    _apiKey = keyData

    return _apiKey


# initial loading of the key when this module is imported
_getAPIKey()

if __name__ == "__main__":
    pass
