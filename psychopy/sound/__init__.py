#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Load and play sounds

By default PsychoPy will try to use the following Libs, in this order, for
sound reproduction but you can alter the order in
preferences > hardware > audioLib:
    ['sounddevice', 'pygame', 'pyo']
For portaudio-based backends (all except for pygame) there is also a
choice of the underlying sound driver (e.g. ASIO, CoreAudio etc).

After importing sound, the sound lib and driver being used will be stored as::
    `psychopy.sound.audioLib`
    `psychopy.sound.audioDriver`

For control of bitrate and buffer size you can call psychopy.sound.init before
creating your first Sound object::

    from psychopy import sound
    sound.init(rate=44100, stereo=True, buffer=128)
    s1 = sound.Sound('ding.wav')

The history of sound libs in PsychoPy:

    - we started with pygame but latencies were always poor
    - we switched to pyo and latencies were better but very system-dependent.
      The problem with pyo is that it has to be compiled which was always
      more painful and prevents us from modifying it easily when needed. It
      also doesn't support python3 as of 2016 and it doesn't support pip for
      installation (e.g. in Anaconda)
    - pysoundcard and sounddevice are new pure python portaudio libraries
      They both install trivially with pip and support python3
      Sounddevice appears to be under most recent development (and shares a
      lot of the original pysoundcard code). In testing we've found the
      latencies to be low

As of PsychoPy 1.85 **sounddevice looks like it will be the best option** but
while it is new there may be some teething problems! To be fair, when writing
the sounddevice code we also changed the method of starting sounds (and pyo
also supports the new method). It is likely that pyo can achieve the same
low latencies as sounddevice, but the other advantages of sounddevice make it
preferable.
"""

# Part of the PsychoPy library
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, division, print_function

from builtins import str
import sys
import os
from psychopy import logging, prefs, exceptions

pyoSndServer = None
Sound = None
audioLib = None
audioDriver = None

_audioLibs = ['sounddevice', 'pyo', 'pysoundcard', 'pygame']

# check if this is being imported on Travis (has no audio card)
travisCI = bool(str(os.environ.get('TRAVIS')).lower() == 'true')
if travisCI:
    # for sounddevice we built in some TravisCI protection but not in pyo
    prefs.hardware['audioLib'] = ['sounddevice']

for thisLibName in prefs.hardware['audioLib']:

    try:
        if thisLibName == 'pyo':
            from . import backend_pyo as backend
            Sound = backend.SoundPyo
            pyoSndServer = backend.pyoSndServer
            audioDriver = backend.audioDriver
        elif thisLibName == 'sounddevice':
            from . import backend_sounddevice as backend
            Sound = backend.SoundDeviceSound
        elif thisLibName == 'pygame':
            from . import backend_pygame as backend
            Sound = backend.SoundPygame
        elif thisLibName == 'pysoundcard':
            from . import backend_pysound as backend
            Sound = backend.SoundPySoundCard
        else:
            msg = ("audioLib pref should be one of {!r}, not {!r}"
                   .format(_audioLibs, thisLibName))
            raise ValueError(msg)
        # if we got this far we were successful in loading the lib
        audioLib = thisLibName
        init = backend.init
        if hasattr(backend, 'getDevices'):
            getDevices = backend.getDevices
        logging.info('sound is using audioLib: %s' % audioLib)
        break
    except exceptions.DependencyError:
        msg = '%s audio lib was requested but not loaded: %s'
        logging.warning(msg % (thisLibName, sys.exc_info()[1]))
        continue  # to try next audio lib

if audioLib is None:
    raise exceptions.DependencyError(
            "No sound libs could be loaded. Tried: {}\n"
            "Check whether the necessary sound libs are installed"
            .format(prefs.hardware['audioLib']))

# function to set the device (if current lib allows it)
def setDevice(dev, kind=None):
    """Sets the device to be used for new streams being created.

    :param dev: the device to be used (name, index or sounddevice.device)
    :param kind: one of [None, 'output', 'input']
    """
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
        if travisCI:  # travisCI doesn't have any audio devices at all. Ignore
            return
        else:
            raise TypeError("`kind` should be one of [None, 'output', 'input']"
                            "not {!r}".format(kind))

# Set the device according to user prefs (if current lib allows it)
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
    if dev=='default' or travisCI:
        pass  # do nothing
    elif dev not in backend.getDevices(kind='output'):
        devNames = sorted(backend.getDevices(kind='output').keys())
        logging.error(u"Requested audio device '{}' that is not available on "
                        "this hardware. The 'audioDevice' preference should be one of "
                        "{}".format(dev, devNames))
    else:
        setDevice(dev, kind='output')
