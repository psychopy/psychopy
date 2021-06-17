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
    'refreshTranscrKeys'
]

import os
import psychopy.logging as logging
from psychopy.alerts import alert
import numpy as np
from pathlib import Path
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
    _recognizers['sphinx'] = sr.Recognizer().recognize_sphinx
    _recognizers['built-in'] = _recognizers['sphinx']  # aliased
    _recognizers['google'] = sr.Recognizer().recognize_google
    _recognizers['googleCloud'] = sr.Recognizer().recognize_google_cloud
    _recognizers['bing'] = sr.Recognizer().recognize_bing
    _recognizers['azure'] = _recognizers['bing']

    # Get API keys for each engine here. Calling `refreshTranscrKeys()`
    # finalizes these values. If any of these are not defined as environment
    # variables, they will be obtained from preferences.
    _apiKeys['google'] = _apiKeys['googleCloud'] = _apiKeys['bing'] = None
    _apiKeys['azure'] = _apiKeys['bing']


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
        if value == 'sphinx':
            if not haveSphinx:
                raise ModuleNotFoundError("To perform built-in (local) transcription you need"
                                          "to have pocketsphinx installed (pip install pocketsphinx)")
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
        List of strings representing expected words or phrases. This will
        constrain the possible output words to the ones specified. Note not all
        engines support this feature (only Sphinx and Google Cloud do at this
        time). A warning will be logged if the engine selected does not support
        this feature. CMU PocketSphinx has an additional feature where the
        sensitivity can be specified for each expected word. You can indicate
        the sensitivity level to use by putting a ``:`` after each word in the
        list (see the Example below). Sensitivity levels range between 50 and
        100. A higher number results in the engine being more conservative,
        resulting in a higher likelihood of false rejections. The default
        sensitivity is 80% for words/phrases without one specified.
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
      environment variables starting with `PSYCHOPY_TRANSCR_KEY_` first. If
      there is no appropriate API key for the given `engine`, then the
      preference *General -> transcrKeyXXX* is used. Keys can be specified as a
      file path, if so, the key data will be loaded from the file. System
      administrators can specify keys this way to use them across a site
      installation without needing the user manage the keys directly.
    * Use `expectedWords` if provided by the API. This will greatly speed up
      recognition. CMU Pocket Sphinx gives the option for sensitivity levels per
      phrase. Higher levels

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

        # expected words 90% confidence on the first two, default for the rest
        expectedWords = ['right:90', 'left:90', 'up', 'down']

        transcribeResults = transcribe(
            resp.samples,
            resp.sampleRateHz,
            expectedWords=expectedWords)

        if transcribeResults.success:  # successful transcription
            # process results ...

    """
    # Bunch of checks to make sure the parameters specified are correct.
    if not _hasSpeechRecognition:  # don't have speech recognition
        raise ModuleNotFoundError(
            "Cannot use `.transcribe()`, missing required module "
            "`speech_recognition` from package `SpeechRecognition`.")

    # check if the engine parameter is valid
    engine = engine.lower()
    if engine not in _recognizers.keys():
        raise ValueError(
            'Parameter `engine` for `transcribe()` is not a valid value.')

    # check if we have necessary keys
    if engine in _apiKeys:
        if not _apiKeys[engine]:
            alert(4615, strFields={'engine': engine})

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
    if engine in ('sphinx', 'built-in'):
        expectedWordsTemp = None
        # check valid language
        config['language'] = language.lower()  # sphinx users en-us not en-US
        if config['language'] not in sphinxLangs:
            url = "https://sourceforge.net/projects/cmusphinx/files/Acoustic%20and%20Language%20Models/"
            raise ValueError(f"Language `{config['language']}` is not installed for pocketsphinx. "
                             f"You can download languages here: {url}"
                             f"Install them here: {pocketsphinx.get_model_path()}")
        # check expected words
        if expectedWords is not None:
            # sensitivity specified as `word:80`
            expectedWordsTemp = []
            for word in expectedWords:
                wordAndSense = word.split(':')
                if len(wordAndSense) == 2:  # specified as `word:80`
                    word, sensitivity = wordAndSense
                    sensitivity = int(sensitivity) / 100.
                else:
                    word = wordAndSense[0]
                    sensitivity = 0.8  # default is 80% confidence

                expectedWordsTemp.append((word, sensitivity))

        config['keyword_entries'] = expectedWordsTemp

    elif engine == 'googleCloud':
        config['preferred_phrases'] = expectedWords
        requiresKey = True
    elif engine == 'google':
        expectedWordsNotSupported = True
        requiresKey = True
    elif engine in ('bing', 'azure'):
        expectedWordsNotSupported = True
        requiresKey = True

    if expectedWordsNotSupported:
        logging.warning(
            f"Transcription engine '{engine}' does not allow for expected phrases to "
            "be specified.")

    # API requires a key
    if requiresKey:
        try:
            if engine != 'googleCloud':
                config['key'] = _apiKeys[engine] if key is None else key
            else:
                config['credentials_json'] = \
                    _apiKeys[engine] if key is None else key
        except KeyError:
            raise ValueError(
                f"Selected speech-to-text engine '{engine}' requires an API key but one"
                "cannot be found. Add key to PsychoPy prefs or try specifying "
                "`key` directly.")

    # combine channels if needed
    samples = np.atleast_2d(samples)  # enforce 2D
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

    # remove empty words
    result = [word for word in respAPI.split(' ') if word != '']

    # object to return containing transcription data
    toReturn = TranscriptionResult(
        words=result,
        unknownValue=unknownValueError,
        requestFailed=requestError,
        engine=engine,
        language=language)

    # split only if the user does not want the raw API data
    return toReturn


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
        else:
            keyVal = envVal

        # Check if we are dealing with a file path, if so load the data as the
        # key value.
        if os.path.isfile(keyVal):
            if engineName != 'googleCloud':
                with open(keyVal, 'r') as keyFile:
                    keyVal = keyFile.read()

        _apiKeys[engineName] = keyVal

    # hack to get 'bing' and 'azure' recognized as the same
    if 'bing' in _apiKeys.keys():
        _apiKeys['azure'] = _apiKeys['bing']


# initial call to populate the API key values
refreshTranscrKeys()


if __name__ == "__main__":
    pass
