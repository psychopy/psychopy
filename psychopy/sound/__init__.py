"""Load and play sounds

By default PsychoPy will try to use the following Libs, in this order, for
sound reproduction but you can alter the order in
preferences > general > audioLib:
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
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import division
import sys
from psychopy import logging, prefs, exceptions

pyoSndServer = None
Sound = None
audioLib = None
audioDriver = None

for thisLibName in prefs.general['audioLib']:

    try:
        if thisLibName == 'pyo':
            from . import backend_pyo as backend
            Sound = backend.SoundPyo
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
            msg = ("Audio lib options are currently only 'pyo' or "
                   "'pygame', not '%s'")
            raise ValueError(msg % thisLibName)
        # if we got this far we were sucessful in loading the lib
        audioLib = thisLibName
        init = backend.init
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
            .format(prefs.general['audioLib']))

def _bestDriver(devNames, devIDs):
    """Find ASIO or Windows sound drivers
    """
    preferredDrivers = prefs.general['audioDriver']
    outputID = None
    audioDriver = None
    osEncoding = sys.getfilesystemencoding()
    for prefDriver in preferredDrivers:
        logging.info('Looking for {}'.format(prefDriver))
        if prefDriver.lower() == 'directsound':
            prefDriver = u'Primary Sound'
        # look for that driver in available devices
        for devN, devString in enumerate(devNames):
            logging.info('Examining for {}'.format(devString))
            try:
                ds = devString.decode(osEncoding).encode('utf-8').lower()
                if prefDriver.encode('utf-8').lower() in ds:
                    audioDriver = devString.decode(osEncoding).encode('utf-8')
                    outputID = devIDs[devN]
                    logging.info('Success: {}'.format(devString))
                    # we found a driver don't look for others
                    return audioDriver, outputID
            except (UnicodeDecodeError, UnicodeEncodeError):
                logging.info('Failed: {}'.format(devString))
                logging.warn('find best sound driver - could not '
                             'interpret unicode in driver name')
    else:
        return None, None
