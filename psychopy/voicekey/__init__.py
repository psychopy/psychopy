#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""voicekey: A toolkit for programming virtual voice-keys.

Copyright (c) Jeremy R. Gray, 2015
License: Distributed under the terms of the GPLv3
Dev status: beta. Can work well in some circumstances, not widely tested.

_BaseVoiceKey is the main abstract class. Subclass and override the detect()
method. See SimpleThresholdVoiceKey or OnsetVoiceKey for examples.
"""

from __future__ import absolute_import, division, print_function

from builtins import range
from builtins import object
__version__ = 0.5

import sys
import os
import numpy as np

# pyo: see http://ajaxsoundstudio.com/pyodoc
try:
    import pyo64 as pyo
    have_pyo64 = True
except Exception:
    import pyo
    have_pyo64 = False

# pyo_server will point to a booted pyo server once pyo_init() is called:
pyo_server = None

# helper functions for time, signal processing, and file I/O:
from . vk_tools import *

# Constants:
T_BASELINE_PERIOD = 0.200  # sec; time assumed not to contain any speech
T_BASELINE_ON = 0.035  # sec; self.baseline is between T_BASELINE_ON ..OFF
T_BASELINE_OFF = 0.180  # sec
TOO_LOUD = 0.01
TOO_QUIET = 10 ** -7
RATE = 44100  # default sampling rate

# max recording time 30 minutes; longer is ok but not tested, lots of lag:
MAX_RECORDING_SEC = 1800


class VoiceKeyException(Exception):
    pass


class _BaseVoiceKey(object):
    """Abstract base class for virtual voice-keys.

    Accepts data as real-time input (from a microphone by default) or off-line
    (if `file_in` is a valid file).
    Over-ride detect() and other methods as needed. See examples.
    """

    def __init__(self, sec=0, file_out='', file_in='', **config):
        """
        :Parameters:

            sec:
                duration to record in seconds

            file_out:
                name for output filename (for microphone input)

            file_in:
                name of input file for sound source (not microphone)

            config:  kwargs dict of parameters for configuration. defaults are:

                'msPerChunk': 2; duration of each real-time analysis chunk, in ms

                'signaler': default None

                'autosave': True; False means manual saving to a file is still
                    possible (by calling .save() but not called automatically upon
                    stopping

                'chnl_in' : microphone channel;
                    see psychopy.sound.backend.get_input_devices()

                'chnl_out': not implemented; output device to use

                'start': 0, select section from a file based on (start, stop) time

                'stop': -1, end of file (default)

                'vol': 0.99, volume 0..1

                'low': 100, Hz, low end of bandpass; can vary for M/F speakers

                'high': 3000, Hz, high end of bandpass

                'threshold': 10

                'baseline': 0; 0 = auto-detect; give a non-zero value to use that

                'more_processing': True; compute more stats per chunk including
                    bandpass; try False if 32-bit python can't keep up

                'zero_crossings': True
        """
        if not (pyo_server and pyo_server.getIsBooted() and
                pyo_server.getIsStarted()):
            msg = 'Need a running pyo server: call voicekey.pyo_init()'
            raise VoiceKeyException(msg)
        self.rate = pyo_server.getSamplingRate()  # pyo_init enforces 16000+ Hz
        self.sec = float(sec)
        if self.sec > MAX_RECORDING_SEC:
            msg = 'for recording, time in seconds cannot be longer than {0}'
            raise VoiceKeyException(msg.format(MAX_RECORDING_SEC))

        # detect whether given a numpy array directly
        # TO-DO: self.array_in handling needs code review
        source = file_in
        self.array_in = []
        if type(source) in [np.ndarray]:
            self.array_in = source
            file_in = '<array len={0}>'.format(len(source))
        self.file_in, self.file_out = file_in, file_out

        # Configuration defaults:
        self.config = {'msPerChunk': 2,
                       'signaler': None,
                       'autosave': True,
                       'chnl_in': 0,  # pyo.pa_get_default_input()
                       # 'chnl_out': 2,  # pyo.pa_get_default_output() no go
                       'start': 0,
                       'stop': -1,
                       'vol': 0.99,
                       'low': 100,
                       'high': 3000,
                       'threshold': 10,
                       'baseline': 0,
                       'more_processing': True,
                       'zero_crossings': True}
        self.config.update(config)
        self.baseline = self.config['baseline']
        self.bad_baseline = False
        self.stopped = False
        self.msPerChunk = float(self.config['msPerChunk'])
        if not 0.65 <= self.msPerChunk <= 32:
            msg = 'msPerChunk should be 0.65 to 32; suggested = 2'
            raise ValueError(msg)

        self._set_source()
        self._set_defaults()
        self._set_signaler()
        self._set_tables()

    def _set_source(self):
        """Data source: file_in, array, or microphone
        """
        if os.path.isfile(self.file_in):
            _rate, self._sndTable = table_from_file(self.file_in,
                                                    start=self.config['start'],
                                                    stop=self.config['stop'])
            if _rate != self.rate:
                print('file sample rate differs from the voice-key rate.')
            self._source = pyo.TableRead(self._sndTable,
                                         freq=self._sndTable.getRate(),
                                         mul=self.config['vol'])
            self.sec = self._sndTable.getDur()
        elif len(self.array_in):
            self._sndTable = table_from_samples(self.array_in,
                                                start=self.config['start'],
                                                stop=self.config['stop'],
                                                rate=self.rate)
            self._source = pyo.TableRead(self._sndTable,
                                         freq=self._sndTable.getRate(),
                                         mul=self.config['vol'])
            self.sec = self._sndTable.size / self.rate
        else:
            # fall through to source = microphone
            ch = self.config['chnl_in']
            self._source = pyo.Input(chnl=ch, mul=self.config['vol'])

    def _set_defaults(self):
        """Set remaining defaults, initialize lists to hold summary stats
        """
        # adjust self.sec based on start, stop times:
        if (self.config['start'], self.config['stop']) != (0, -1):
            if self.config['stop'] > self.config['start']:
                self.sec = self.config['stop'] - self.config['start']
            elif self.config['start'] <= self.sec:
                self.sec = self.sec - self.config['start']
        self.chunks = int(self.sec * 1000. / self.msPerChunk)  # ideal no slip
        # total chunk count and current-chunk index:
        self.count = 0

        self.filename = self.file_out or 'rec.wav'
        self.filesize = None

        # timing data for diagnostics
        self.elapsed = 0
        self.t_enter = []  # time at chunk entry
        self.t_exit = []  # time at chunk exit
        self.t_proc = []  # proportion of chunk-time spent doing _do_chunk

        # data cache:
        self.data = []  # raw unprocessed data, in chunks
        self.power = []
        self.power_bp = []
        self.power_above = []
        self.zcross = []
        self.max_bp = 0
        self.max_bp_chunk = None
        bandpass_pre_cache(rate=self.rate)  # for faster bandpass filtering

        # default event parameters:
        self.event_detected = False
        self.event_lag = 0  # lag required to detect the event prior to trip()
        self.event_time = 0  # becomes time of detected event = time at trip()
        self.event_onset = 0  # best estimate of the onset of the event

    def _set_signaler(self):
        """Set the signaler to be called by trip()
        """
        if not self.config['signaler']:
            self.config['signaler'] = None  # _BaseVoiceKeySignal()
        self.event_signaler = self.config['signaler']

    def _set_tables(self):
        """Set up the pyo tables (allocate memory, etc).

        One source -> three pyo tables: chunk=short, whole=all, baseline.
        triggers fill tables from self._source; make triggers in .start()
        """
        sec_per_chunk = self.msPerChunk / 1000.
        self._chunktable = pyo.NewTable(length=sec_per_chunk)
        self._wholetable = pyo.NewTable(length=self.sec)
        if self.baseline < TOO_QUIET:
            self._baselinetable = pyo.NewTable(length=T_BASELINE_OFF)

    def _set_baseline(self):
        """Set self.baseline = rms(silent period) using _baselinetable data.

        Called automatically (via pyo trigger) when the baseline table
        is full. This is better than using chunks (which have gaps between
        them) or the whole table (which can be very large = slow to work
        with).
        """
        data = np.array(self._baselinetable.getTable())
        tstart = int(T_BASELINE_ON * self.rate)
        segment_power = rms(data[tstart:])

        # Look for bad baseline period:
        if self.baseline > TOO_LOUD:
            self.bad_baseline = True

        # Dubiously quiet is bad too:
        if segment_power < TOO_QUIET:
            self.stop()
            msg = ('Baseline period is TOO quiet\nwrong input '
                   'channel selected? device-related initial delay?')
            raise ValueError(msg)

        self.baseline = max(segment_power, 1)

    def _process(self, chunk):
        """Calculate and store basic stats about the current chunk.

        This gets called every chunk -- keep it efficient, esp 32-bit python
        """
        # band-pass filtering:
        if self.config['more_processing']:
            bp_chunk = bandpass(chunk, self.config['low'],
                                self.config['high'], self.rate)
        else:
            bp_chunk = chunk

        # loudness after bandpass filtering:
        self.power_bp.append(rms(bp_chunk))

        _mx = max(bp_chunk)
        if _mx > self.max_bp:
            self.max_bp = _mx
            self.max_bp_chunk = self.count  # chunk containing the max

        if self.config['more_processing']:
            # more bandpass
            bp3k_chunk = bandpass(chunk, self.config['low'], 3000, self.rate)
            bp8k_chunk = bandpass(chunk, self.config['low'], 8000, self.rate)
            # "content filtered speech" (~ affect only):
            bp2k8k_chunk = bandpass(chunk, 2000, 8000, self.rate)

            # basic loudness:
            self.power.append(rms(chunk))

            # above a threshold or not:
            above_01 = int(self.power[self.count] > self.config['threshold'])
            self.power_above.append(above_01)

        if self.config['zero_crossings']:
            # zero-crossings per ms:
            zx = zero_crossings(bp_chunk)
            self.zcross.append(np.sum(zx) / self.msPerChunk)

    def detect(self):
        """Override to define a detection algorithm.
            if condition:
                self.trip()

        See SimpleThresholdVoiceKey for a minimal usage example, or
        VoicelessPlosiveVoiceKey for a more involved one.
        """
        raise NotImplementedError('override; see SimpleThresholdVoiceKey')

    def trip(self):
        """Trip the voice-key; does not stop recording.
        """
        # calls .start() on the event-signaler thread. Only `detect()` should
        # call `trip()`. Customize `.detect()` rather than the logic here.

        self.event_detected = True
        self.event_time = self.elapsed
        if hasattr(self, 'event_signaler') and self.event_signaler:
            self.event_signaler.start()

    def _do_chunk(self):
        """Core function to handle a chunk (= a few ms) of input.

        There can be small temporal gaps between or within chunks, i.e.,
        `slippage`. Adjust several parameters until this is small: msPerChunk,
        and what processing is done within ._process().

        A trigger (`_chunktrig`) signals that `_chunktable` has been filled
        and has set `_do_chunk` as the function to call upon triggering.
        `.play()` the trigger again to start recording the next chunk.
        """
        if self.stopped:
            return

        self.t_enter.append(get_time())
        self.elapsed = self.t_enter[-1] - self.t_enter[0]
        self.t_baseline_has_elapsed = bool(self.elapsed > T_BASELINE_PERIOD)

        # Get the table content as np.array
        chunk = np.asarray(self._chunktable.getTable())
        chunk = np.int16(chunk * 2 ** 15)
        self.data.append(chunk)

        # Calc basic stats, then use to detect features
        self._process(chunk)
        self.detect()  # conditionally call trip()

        # Trigger a new chunk recording, or stop if stopped or time is up:
        t_end = get_time()
        if t_end - self.t_enter[0] < self.sec:
            if not self.stopped:
                self._chunktrig.play()  # *** triggers the next chunk ***
                self.count += 1
        else:
            self.stop()
        self.t_exit.append(t_end)

    def start(self, silent=False):
        """Start reading and processing audio data from a file or microphone.
        """
        if self.stopped:
            raise VoiceKeyException('cannot start a stopped recording')
        self.t_start = get_time()

        # triggers: fill tables, call _do_chunk & _set_baseline:
        self._chunktrig = pyo.Trig()
        self._chunkrec = pyo.TrigTableRec(self._source, self._chunktrig,
                                          self._chunktable)
        self._chunklooper = pyo.TrigFunc(self._chunkrec["trig"],
                                         self._do_chunk)
        self._wholetrig = pyo.Trig()
        self._wholerec = pyo.TrigTableRec(self._source, self._wholetrig,
                                          self._wholetable)
        self._wholestopper = pyo.TrigFunc(self._wholerec["trig"], self.stop)

        # skip if a baseline value was given in config:
        if not self.baseline:
            self._baselinetrig = pyo.Trig()
            self._baselinerec = pyo.TrigTableRec(self._source,
                                                 self._baselinetrig,
                                                 self._baselinetable)
            self._calc_baseline = pyo.TrigFunc(self._baselinerec["trig"],
                                               self._set_baseline)

        # send _source to sound-output (speakers etc) as well:
        if self.file_in and not silent:
            self._source.out()

        # start calling self._do_chunk by flipping its trigger;
        # _do_chunk then triggers itself via _chunktrigger until done:
        self._chunktrig.play()
        self._wholetrig.play()
        self._baselinetrig.play()

        return self

    @property
    def slippage(self):
        """Diagnostic: Ratio of the actual (elapsed) time to the ideal time.

        Ideal ratio = 1 = sample-perfect acquisition of msPerChunk, without
        any gaps between or within chunks. 1. / slippage is the proportion of
        samples contributing to chunk stats.
        """
        if len(self.t_enter) > 1:
            diffs = np.array(self.t_enter[1:]) - np.array(self.t_enter[:-1])
            ratio = np.mean(diffs) * 1000. / self.msPerChunk
        else:
            ratio = 0
        return ratio

    @property
    def started(self):
        """Boolean property, whether `.start()` has been called.
        """
        return bool(hasattr(self, '_chunklooper'))  # .start() has been called

    def stop(self):
        """Stop a voice-key in progress.

        Ends and saves the recording if using microphone input.
        """
        # Will be stopped at self.count (= the chunk index), but that is less
        # reliable than self.elapsed due to any slippage.

        if self.stopped:
            return
        self.stopped = True
        self.t_stop = get_time()
        self._source.stop()
        self._chunktrig.stop()
        self._wholetrig.stop()

        if self.config['autosave']:
            self.save()

        # Calc the proportion of the available time spent doing _do_chunk:
        for ch in range(len(self.t_exit)):
            t_diff = self.t_exit[ch] - self.t_enter[ch]
            self.t_proc.append(t_diff * 1000 / self.msPerChunk)

    def join(self, sec=None):
        """Sleep for `sec` or until end-of-input, and then call stop().
        """
        sleep(sec or self.sec - self.elapsed)
        self.stop()

    def wait_for_event(self, plus=0):
        """Start, join, and wait until the voice-key trips, or it times out.

        Optionally wait for some extra time, `plus`, before calling `stop()`.
        """
        if not self.started:
            self.start()
        while not self.event_time and not self.stopped:
            sleep(self.msPerChunk / 1000.)
        if not self.stopped:
            naptime = min(plus, self.sec - self.elapsed)  # approx...
            if naptime > 0:
                sleep(naptime)
            self.stop()
        # next sleep() helps avoid pyo error:
        #    "ReferenceError: weakly-referenced object no longer exists"
        sleep(1.5 * self.msPerChunk / 1000.)

        return self.elapsed

    def save(self, ftype='', dtype='int16'):
        """Save new data to file, return the size of the saved file (or None).

        The file format is inferred from the filename extension, e.g., `flac`.
        This will be overridden by the `ftype` if one is provided; defaults to
        `wav` if nothing else seems reasonable. The optional `dtype` (e.g.,
        `int16`) can be any of the sample types supported by `pyo`.
        """
        if self.file_in or not self.count:
            return

        self.save_fmt = os.path.splitext(self.filename)[1].lstrip('.')
        fmt = ftype or self.save_fmt or 'wav'
        if not self.filename.endswith('.' + fmt):
            self.filename += '.' + fmt

        # Save the recording (continuous, non-chunked):
        end_index = int(self.elapsed * self.rate)  # ~samples
        if end_index < self._wholetable.size:
            dataf = np.asarray(self._wholetable.getTable()[:end_index])
            samples_to_file(dataf, self.rate, self.filename,
                            fmt=fmt, dtype=dtype)
            self.sec = pyo.sndinfo(self.filename)[1]
        else:
            table_to_file(self._wholetable, self.filename,
                          fmt=fmt, dtype=dtype)
        self.filesize = os.path.getsize(self.filename)
        return self.filesize


class SimpleThresholdVoiceKey(_BaseVoiceKey):
    """Class for simple threshold voice key (loudness-based onset detection).

    The "hello world" of voice-keys.
    """

    def detect(self):
        """Trip if the current chunk's audio power > 10 * baseline loudness.
        """
        if self.event_detected or not self.baseline:
            return
        current = self.power[-1]
        threshold = 10 * self.baseline
        if current > threshold:
            self.trip()


class OnsetVoiceKey(_BaseVoiceKey):
    """Class for speech onset detection.

    Uses bandpass-filtered signal (100-3000Hz). When the voice key trips,
    the best voice-onset RT estimate is saved as `self.event_onset`, in sec.

    """

    def detect(self):
        """Trip if recent audio power is greater than the baseline.
        """
        if self.event_detected or not self.baseline:
            return
        window = 5  # recent hold duration window, in chunks
        threshold = 10 * self.baseline
        conditions = all([x > threshold for x in self.power_bp[-window:]])
        if conditions:
            self.event_lag = window * self.msPerChunk / 1000.
            self.event_onset = self.elapsed - self.event_lag
            self.trip()
            self.event_time = self.event_onset


class OffsetVoiceKey(_BaseVoiceKey):
    """Class to detect the offset of a single-word utterance.
    """

    def __init__(self, sec=10, file_out='', file_in='', delay=0.3, **kwargs):
        """Record and ends the recording after speech offset.  When the voice
        key trips, the best voice-offset RT estimate is saved as
        `self.event_offset`, in seconds.

        :Parameters:

            `sec`: duration of recording in the absence of speech or
                other sounds.

            `delay`: extra time to record after speech offset, default 0.3s.

        The same methods are available as for class OnsetVoiceKey.
        """
        config = {'sec': sec,
                  'file_out': file_out,
                  'file_in': file_in,
                  'delay': delay}
        kwargs.update(config)
        super(OffsetVoiceKey, self).__init__(**kwargs)

    def detect(self):
        """Listen for onset, offset, delay, then end the recording.
        """
        if self.event_detected or not self.baseline:
            return
        if not self.event_onset:
            window = 5  # chunks
            threshold = 10 * self.baseline
            conditions = all([x > threshold for x in self.power_bp[-window:]])
            if conditions:
                self.event_lag = window * self.msPerChunk / 1000.
                self.event_onset = self.elapsed - self.event_lag
                self.event_offset = 0
        elif not self.event_offset:
            window = 25
            threshold = 10 * self.baseline
            # segment = np.array(self.power_bp[-window:])
            conditions = all([x < threshold for x in self.power_bp[-window:]])
            # conditions = np.all(segment < threshold)
            if conditions:
                self.event_lag = window * self.msPerChunk / 1000.
                self.event_offset = self.elapsed - self.event_lag
                self.event_time = self.event_offset  # for plotting
        elif self.elapsed > self.event_offset + self.config['delay']:
            self.trip()
            self.stop()


# ----- Convenience classes -------------------------------------------------

class Recorder(_BaseVoiceKey):
    """Convenience class: microphone input only (no real-time analysis).

    Using `record()` is like `.join()`: it will block execution. But it will
    also try to save the recording automatically even if interrupted (whereas
    `.start().join()` will not do so). This might be especially useful when
    making long recordings.
    """

    def __init__(self, sec=2, filename='rec.wav'):
        super(Recorder, self).__init__(sec, file_out=filename)
    # def _set_defaults(self):
    #    pass

    def __del__(self):
        if hasattr(self, 'filename') and not os.path.isfile(self.filename):
            self.save()

    def _set_baseline(self):
        pass

    def detect(self):
        pass

    def _process(self, *args, **kwargs):
        pass

    def record(self, sec=None):
        try:
            self.start().join(sec)
        except Exception:
            self.save()
            raise


class Player(_BaseVoiceKey):
    """Convenience class: sound output only (no real-time analysis).
    """

    def __init__(self, sec=None, source='rec.wav',
                 start=0, stop=-1, rate=44100):
        if type(source) in [np.ndarray]:
            sec = len(source) / rate
        elif os.path.isfile(source):
            sec = pyo.sndinfo(source)[1]
        config = {'start': start,
                  'stop': stop}
        super(Player, self).__init__(sec, file_in=source, **config)
    # def _set_defaults(self):  # ideally override but need more refactoring
    #    pass

    def _set_baseline(self):
        pass

    def detect(self):
        pass

    def _process(self, *args, **kwargs):
        pass

    def play(self, sec=None):
        self.start().join(sec)


# ----- pyo initialization (essential) -------------------------------------

def pyo_init(rate=44100, nchnls=1, buffersize=32, duplex=1):
    """Start and boot a global pyo server, restarting if needed.
    """
    global pyo_server
    if rate < 16000:
        raise ValueError('sample rate must be 16000 or higher')

    # re-init
    if hasattr(pyo_server, 'shutdown'):
        pyo_server.stop()
        sleep(0.25)  # make sure enough time passes for the server to shutdown
        pyo_server.shutdown()
        sleep(0.25)
        pyo_server.reinit(sr=rate, nchnls=nchnls,
                          buffersize=buffersize, duplex=duplex)
    else:
        pyo_server = pyo.Server(sr=rate,
                                nchnls=nchnls,  # 1 = mono
                                buffersize=buffersize,  # ideal = 64 or higher
                                duplex=duplex)  # 1 = input + output
    pyo_server.boot().start()

    # avoid mac issue of losing first 0.5s if no sound played for ~1 minute:
    if sys.platform == 'darwin':
        z2 = np.zeros(2)
        _sndTable = pyo.DataTable(size=2, init=z2.T.tolist(), chnls=nchnls)
        _snd = pyo.TableRead(_sndTable, freq=rate, mul=0)
        _snd.play()
        time.sleep(0.510)
