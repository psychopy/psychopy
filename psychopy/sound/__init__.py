#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load and play sounds

We have used a number of different Python libraries ("backends") for generating
sounds in PsychoPy. We started with `Pygame`, then tried `pyo` and `sounddevice`
but we now strongly recommend you use the PTB setting. That uses the
`PsychPortAudio`_ engine, written by Mario Kleiner for `Psychophysics Toolbox`_.

With the PTB backend you get some options about how aggressively you want to try
for low latency, and there is also an option to pre-schedule a sound to play at
a given time in the future.

By default PsychoPy will try to use the following Libs, in this order, for
sound reproduction but you can alter the order in
preferences > hardware > audioLib:
    ['sounddevice', 'pygame', 'pyo']
For portaudio-based backends (all except for pygame) there is also a
choice of the underlying sound driver (e.g. ASIO, CoreAudio etc).

After importing sound, the sound lib and driver being used will be stored as::
    `psychopy.sound.audioLib`
    `psychopy.sound.audioDriver`

.. PTB

.. _PsychPortAudio: http://psychtoolbox.org/docs/PsychPortAudio-Open
.. _Psychophysics Toolbox: http://psychtoolbox.org
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = []

import sys
import os
import traceback
from psychopy import logging, prefs, constants
from psychopy.tools import systemtools
from .exceptions import DependencyError, SoundFormatError
from .audiodevice import *
from .audioclip import *  # import objects related to AudioClip

# import microphone if possible
try:
    from .microphone import *  # import objects related to the microphone class
except ImportError as err:
    formatted_tb = ''.join(
        traceback.format_exception(type(err), err, err.__traceback__))
    logging.error(
        "Failed to import psychopy.sound.microphone. Mic recordings will not be"
        "possible on this machine. For details see stack trace below:\n"
        f"{formatted_tb}")

# # import transcription if possible
# try:
#     from .transcribe import *  # import transcription engine stuff
# except ImportError as err:
#     formatted_tb = ''.join(
#         traceback.format_exception(type(err), err, err.__traceback__))
#     logging.error(
#         "Failed to import psychopy.sound.transcribe. Transcription will not be"
#         "possible on this machine. For details see stack trace below:\n"
#         f"{formatted_tb}")

# used to check if we are on 64-bit Python
bits32 = sys.maxsize == 2 ** 32

# Globals for the sound library. We can only load one audio library at a time,
# so once these values are populated they cannot be changed without restarting
# Python.
pyoSndServer = None
Sound = None
audioLib = None
audioDriver = None

# These are the names that can be used in the prefs to specifiy audio libraries. 
# The available libraries are hard-coded at this point until we can overhaul 
# the sound library to be more modular. 
_audioLibs = ['PTB', 'sounddevice', 'pyo', 'pysoundcard', 'pygame']
failed = []  # keep track of audio libs that failed to load

# check if this is being imported on Travis/Github (has no audio card)
if systemtools.isVM_CI():
    # for sounddevice we built in some VM protection but not in pyo
    prefs.hardware['audioLib'] = ['ptb', 'sounddevice']

# ensure that the value for `audioLib` is a list
if isinstance(prefs.hardware['audioLib'], str):
    prefs.hardware['audioLib'] = [prefs.hardware['audioLib']]

# selection and fallback mechanism for audio libraries
for thisLibName in prefs.hardware['audioLib']:
    # Tell the user we are trying to load the specifeid audio library
    logging.info(f"Trying to load audio library: {thisLibName}")

    # Iterate over the list of audioLibs and try to load the first one that
    # is supported. If none are supported, load PTB as a fallback. If PTB isn't 
    # installed, raise an error.
    thisLibName = thisLibName.lower()

    # lowercased list of valid audio libraries for safe comparisons
    validLibs = [libName.lower() for libName in _audioLibs]  

    # check if `thisLibName` is a valid audio library
    if thisLibName not in validLibs:
        failed.append(thisLibName)
        logging.warning(f"Invalid audioLib pref: {thisLibName}. "
                        f"Valid options are: {_audioLibs}")
        continue

    # select the backend and set the Sound class
    if thisLibName == 'ptb':
        # The Psychtoolbox backend is perfered, provides the best performance
        # and is the only one that supports low-latency scheduling. If no other
        # audio backend can be loaded, we will use PTB.
        if not bits32:
            try:
                from . import backend_ptb as backend
                Sound = backend.SoundPTB
                audioDriver = backend.audioDriver
            except Exception:
                failed.append(thisLibName)
                continue
            else:
                break 
        else:
            logging.warning("PTB backend is not supported on 32-bit Python. "
                            "Trying another backend...")
            continue
    elif thisLibName == 'pyo':
        # pyo is a wrapper around PortAudio, which is a cross-platform audio
        # library. It is the recommended backend for Windows and Linux.
        try:
            from . import backend_pyo as backend
            Sound = backend.SoundPyo
            pyoSndServer = backend.pyoSndServer
            audioDriver = backend.audioDriver
        except Exception:
            failed.append(thisLibName)
            continue
        else:
            break
    elif thisLibName == 'sounddevice':
        # sounddevice is a wrapper around PortAudio, which is a cross-platform
        # audio library. It is the recommended backend for Windows and Linux.
        try:
            from . import backend_sounddevice as backend
            Sound = backend.SoundDeviceSound
        except Exception:
            failed.append(thisLibName)
            continue
        else:
            break
    elif thisLibName == 'pygame':
        # pygame is a cross-platform audio library. It is no longer supported by
        # PsychoPy, but we keep it here for backwards compatibility until 
        # something breaks.
        try:
            from . import backend_pygame as backend
            Sound = backend.SoundPygame
        except Exception:
            failed.append(thisLibName)
            continue
        else:
            break
    elif thisLibName == 'pysoundcard':
        # pysoundcard is a wrapper around PortAudio, which is a cross-platform
        # audio library.
        try:
            from . import backend_pysoundcard as backend
            Sound = backend.SoundPySoundCard
        except Exception:
            failed.append(thisLibName)
            continue
        else:
            break
    else:
        # Catch-all for invalid audioLib prefs.
        msg = ("audioLib pref should be one of {!r}, not {!r}"
                .format(_audioLibs, thisLibName))
        raise ValueError(msg)
else:
    # if we get here, there is no audioLib that is supported, try for PTB
    msg = ("Failed to load any of the audioLibs: {!r}. Falling back to " 
           "PsychToolbox ('ptb') backend for sound. Be sure to add 'ptb' to "
           "preferences to avoid seeing this message again.".format(failed))
    logging.error(msg)
    try:
        from . import backend_ptb as backend
        Sound = backend.SoundPTB
        audioDriver = backend.audioDriver
    except Exception:
        failed.append(thisLibName)


# we successfully loaded a backend if `Sound` is not None
if Sound is not None:
    audioLib = thisLibName
    init = backend.init
    if hasattr(backend, 'getDevices'):
        getDevices = backend.getDevices
    logging.info('sound is using audioLib: %s' % audioLib)
else:
    # if we get here, there is no audioLib that is supported
    logging.error(
        "No audioLib could be loaded. Tried: {}\n Check whether the necessary "
        "audioLibs are installed".format(prefs.hardware['audioLib']))

# warn the user 
if audioLib.lower() != 'ptb':
    # Could be running PTB, just aren't?
    logging.warning("We strongly recommend you activate the PTB sound "
                    "engine in PsychoPy prefs as the preferred audio "
                    "engine. Its timing is vastly superior. Your prefs "
                    "are currently set to use {} (in that order)."
                    .format(prefs.hardware['audioLib']))


# function to set the device (if current lib allows it)
def setDevice(dev, kind=None):
    """Sets the device to be used for new streams being created.

    :param dev: the device to be used (name, index or sounddevice.device)
    :param kind: one of [None, 'output', 'input']
    """
    if dev is None:
        # if given None, do nothing
        return
    if not hasattr(backend, 'defaultOutput'):
        raise IOError("Attempting to SetDevice (audio) but not supported by "
                      "the current audio library ({!r})".format(audioLib))
    if hasattr(dev,'name'):
        dev = dev['name']
    if kind is None:
        backend.defaultInput = backend.defaultOutput = dev
    elif kind == 'input':
        backend.defaultInput = dev
    elif kind == 'output':
        backend.defaultOutput = dev
    else:
        if systemtools.isVM_CI():  # no audio device on CI, ignore
            return
        else:
            raise TypeError("`kind` should be one of [None, 'output', 'input']"
                            "not {!r}".format(kind))

# Set the device according to user prefs (if current lib allows it)
deviceNames = []
if hasattr(backend, 'defaultOutput'):
    pref = prefs.hardware['audioDevice']
    # is it a list or a simple string?
    if type(prefs.hardware['audioDevice'])==list:
        # multiple options so use zeroth
        dev = prefs.hardware['audioDevice'][0]
    else:
        # a single option
        dev = prefs.hardware['audioDevice']
    # is it simply "default" (do nothing)
    if dev=='default' or systemtools.isVM_CI():
        pass  # do nothing
    elif dev not in backend.getDevices(kind='output'):
        deviceNames = sorted(backend.getDevices(kind='output').keys())
        logging.warn(
            u"Requested audio device '{}' that is not available on "
            "this hardware. The 'audioDevice' preference should be one of "
            "{}".format(dev, deviceNames))
    else:
        setDevice(dev, kind='output')


if __name__ == "__main__":
    pass
