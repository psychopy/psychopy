#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Digital signal processing functions; pyo table, file, & sample conversions
"""

from __future__ import absolute_import, division, print_function

import os
import sys
import time
import numpy as np
from scipy.signal import butter, lfilter
try:
    import pyo64 as pyo
except Exception:
    import pyo


class PyoFormatException(Exception):
    pass


# --- time-related helper functions --------------------------

# Ensure we have a high-resolution clock; code from PsychoPy (Sol Simpson)
if sys.platform == 'win32':
    from ctypes import byref, c_int64, windll
    _fcounter = c_int64()
    _qpfreq = c_int64()
    windll.Kernel32.QueryPerformanceFrequency(byref(_qpfreq))
    _qpfreq = float(_qpfreq.value)
    _winQPC = windll.Kernel32.QueryPerformanceCounter

    def get_time():
        """High-precision replacement for time.time() on Windows.
        """
        _winQPC(byref(_fcounter))
        return _fcounter.value / _qpfreq
else:
    import timeit
    get_time = timeit.default_timer

MIN_SLEEP = 0.001  # used in sleep() function


def sleep(sec=0):
    """Use time.sleep with a minimum duration sleep threshold.
    """
    time.sleep(max(MIN_SLEEP, sec))


# --- digital signal processing helper functions --------------------------

_butter_cache = {}


def _butter(order, band, rate=44100):
    """Cache-ing version of scipy.signal's butter().

    Allows faster band-pass filtering during real-time processing.
    """
    global _butter_cache
    _h = hash((order, band, rate))
    if not _h in _butter_cache:
        low, high = band
        nyqfreq = float(rate) / 2
        lowf = low / nyqfreq
        highf = high / nyqfreq
        _butter_cache[_h] = butter(order, (lowf, highf), btype='band')
    return _butter_cache[_h]


def bandpass_pre_cache(lows=(80, 100, 120),
                       highs=(1200, 3000, 8000),
                       bands=((2000, 8000),),  # content-filtered speech
                       rate=44100):
    """Call _butter now to cache some useful (b, a) values.
    """
    for low in lows:
        for high in highs:
            _butter(6, (low, high), rate=rate)
    for band in bands:
        _butter(6, band, rate=rate)


def bandpass(data, low=80, high=1200, rate=44100, order=6):
    """Return bandpass filtered `data`.
    """
    b, a = _butter(order, (low, high), rate)
    return lfilter(b, a, data)


def rms(data):
    """Basic audio-power measure: root-mean-square of data.

    Identical to `std` when the mean is zero; faster to compute just rms.
    """
    if data.dtype == np.int16:
        md2 = data.astype(np.float) ** 2  # int16 wrap around --> negative
    else:
        md2 = data ** 2
    return np.sqrt(np.mean(md2))


def std(data):
    """Like rms, but also subtracts the mean (= slower).
    """
    return np.std(data)


def smooth(data, win=16, tile=True):
    """Running smoothed average, via convolution over `win` window-size.

    `tile` with the mean at start and end by default; otherwise replace with 0.
    """
    weights = np.ones(win) / win
    data_c = np.convolve(data, weights)[win - 1:-(win - 1)]
    if tile:
        pre = np.tile(data_c[0], win // 2)
        post = np.tile(data_c[-1], win // 2)
    else:
        pre = post = np.zeros(win // 2)
    data_pre_c = np.concatenate((pre, data_c))
    data_pre_c_post = np.concatenate((data_pre_c, post))
    return data_pre_c_post[:len(data)]


def zero_crossings(data):
    """Return a vector of length n-1 of zero-crossings within vector `data`.

    1 if the adjacent values switched sign, or
    0 if they stayed the same sign.
    """
    zx = np.zeros(len(data))
    zx[np.where(data[:-1] * data[1:] < 0)] = 1
    return zx


def tone(freq=440, sec=2, rate=44100, vol=.99):
    """Return a np.array suitable for use as a tone (pure sine wave).
    """
    samples = sec * rate
    time_steps = np.arange(0., 1., 1. / samples)
    scaling = 2 * np.pi * freq * sec
    return np.sin(time_steps * scaling) * vol


def apodize(data, ms=5, rate=44100):
    """Apply a Hanning window (5ms) to reduce a sound's 'click' onset / offset.
    """
    hw_size = int(min(rate // (1000 / ms), len(data) // 15))
    hanning_window = np.hanning(2 * hw_size + 1)
    data[:hw_size] *= hanning_window[:hw_size]
    data[-hw_size:] *= hanning_window[-hw_size:]
    return data


# --- pyo helper functions ------------------------------------------------

# format codes for _get_pyo_codes():
pyo_formats = {'wav': 0, 'aif': 1, 'aiff': 1, 'au': 2, 'raw': 3,
               'sd2': 4, 'flac': 5, 'caf': 6, 'ogg': 7}
pyo_dtype = {'int16': 0, 'int24': 1, 'int32': 2, 'float32': 3,
             'float64': 4, 'U-Law': 5, 'A-Law': 6}


def _get_pyo_codes(fmt='', dtype='int16', file_out=''):
    """Convert file and data formats to int codes, e.g., wav int16 -> (0, 0).
    """

    if not fmt:
        dot_ext = os.path.splitext(file_out)[1]
        fmt = dot_ext.lower().strip('.')
    if fmt in pyo_formats:
        file_fmt = pyo_formats[fmt]
    else:
        msg = 'format `{0}` not supported'.format(file_out)
        raise PyoFormatException(msg)

    if fmt in ['sd2', 'flac']:
        ok_dfmt = {'int16': 0, 'int24': 1}
    else:
        ok_dfmt = pyo_dtype

    if dtype in ok_dfmt:
        data_fmt = pyo_dtype[dtype]
    else:
        msg = 'data format `{0}` not supported for `{1}`'.format(
            dtype, file_out)
        raise PyoFormatException(msg)
    return file_fmt, data_fmt


def samples_from_table(table, start=0, stop=-1, rate=44100):
    """Return samples as a np.array read from a pyo table.

    A (start, stop) selection in seconds may require a non-default rate.
    """
    samples = np.array(table.getTable())
    if (start, stop) != (0, -1):
        if stop > start:
            samples = samples[start * rate:stop * rate]
        elif start:
            samples = samples[start * rate:]
    return samples


def table_from_samples(samples, start=0, stop=-1, rate=44100):
    """Return a pyo DataTable constructed from samples.

    A (start, stop) selection in seconds may require a non-default rate.
    """
    if type(samples) == np.ndarray:
        samples = samples.tolist()
    if type(samples) != list:
        raise TypeError('samples should be a list or np.array')
    if (start, stop) != (0, -1):
        if stop > start:
            samples = samples[start * rate:stop * rate]
        elif start:
            samples = samples[start * rate:]
    table = pyo.DataTable(size=len(samples), init=samples)
    return table


def table_from_file(file_in, start=0, stop=-1):
    """Read data from files, any pyo format, returns (rate, pyo SndTable)
    """
    table = pyo.SndTable()
    try:
        table.setSound(file_in, start=start, stop=stop)
    except TypeError:
        msg = 'bad file `{0}`, or format not supported'.format(file_in)
        raise PyoFormatException(msg)
    rate = pyo.sndinfo(file_in)[2]
    return rate, table


def samples_from_file(file_in, start=0, stop=-1):
    """Read data from files, returns tuple (rate, np.array(.float64))
    """
    if not os.path.isfile(file_in):
        raise IOError('no such file `{0}`'.format(file_in))
    rate, table = table_from_file(file_in, start=start, stop=stop)
    return rate, np.array(table.getTable())


def samples_to_file(samples, rate, file_out, fmt='', dtype='int16'):
    """Write data to file, using requested format or infer from file .ext.

    Only integer `rate` values are supported.

    See http://ajaxsoundstudio.com/pyodoc/api/functions/sndfile.html

    """
    file_fmt, data_fmt = _get_pyo_codes(fmt, dtype, file_out)
    if type(samples) == np.ndarray:
        samples = samples.tolist()
    if type(samples) != list:
        raise TypeError('samples should be a list or np.array')
    try:
        pyo.savefile(samples, path=file_out, sr=int(rate), channels=1,
                     fileformat=file_fmt, sampletype=data_fmt)
    except Exception:
        msg = 'could not save `{0}`; permissions or other issue?'
        raise IOError(msg.format(file_out))


def table_to_file(table, file_out, fmt='', dtype='int16'):
    """Write data to file, using requested format or infer from file .ext.
    """
    file_fmt, data_fmt = _get_pyo_codes(fmt, dtype, file_out)
    try:
        pyo.savefileFromTable(table=table, path=file_out,
                              fileformat=file_fmt, sampletype=data_fmt)
    except Exception:
        msg = 'could not save `{0}`; permissions or other issue?'
        raise IOError(msg.format(file_out))
