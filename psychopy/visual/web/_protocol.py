#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Messages passed between `WebBrowserStim` and the web browser server process.

Each message is a dict packed with msgpack, with an `'op'` key naming what it
is and, for messages about one page, a `'view'` key with the page's ID.

Messages to the server:

* `create` - open a page (`w`, `h`, `url` or `html` with `baseUrl`, `zoom`,
  `javascript`, `transparent`, `bgColor`, `muted`, `maxFps`, `allowedUrls`,
  `newWindowPolicy`).
* `navigate` (`url`), `setHtml` (`html`, `baseUrl`), `history` (`action`, one
  of `'back'`, `'forward'`, `'reload'` or `'stop'`), `resize` (`w`, `h`),
  `zoom` (`factor`), `setMuted` (`muted`), `setMaxFps` (`fps`).
* `js` - run JavaScript (`id`, `code`), answered by `jsResult`.
* `message` - send data to the page's `psychopy` message handlers (`data`).
* `input` - mouse, wheel, key, text (`ime`) or focus input (`kind` and the
  fields for that kind, see `WebBrowserStim`).
* `release` - the stimulus has finished with a frame (`slot`, `gen`).
* `close` - close a page, `shutdown` - close everything and exit.

Messages from the server:

* `hello` - sent once connected (`protocol`, `pid`, `versions`), or `fatal`
  (`error`) if the server can't start.
* `surface` - where frames will be written (`shm`, `w`, `h`, `stride`, `fmt`,
  `slots`, `gen`, `dpr`), then `frame` for each frame written there (`slot`,
  `seq`, `gen`, `t`).
* `loadStarted`, `loadProgress` (`pct`), `loadFinished` (`ok`, `url`),
  `urlChanged` (`url`), `titleChanged` (`title`).
* `console` (`level`, `msg`, `line`, `src`), `pageMessage` (`data`, `origin`),
  `dialog` (`kind`, `msg`).
* `navBlocked` (`url`), `permissionDenied` (`feature`, `origin`), `cursor`
  (`shape`), `renderGone` (`status`, `code`), `jsResult` (`id`, `ok`, `value`
  or `error`), `error` (`msg`), `closed`.

This module only uses the standard library and msgpack, as the server imports
it without importing PsychoPy.
"""

import struct

import msgpack

__all__ = [
    'PROTOCOL_VERSION',
    'ENV_AUTHKEY',
    'ENV_SERVER_CMD',
    'MESSAGE_TAG',
    'FORMATS',
    'HEADER',
    'HEADER_SIZE',
    'HEADER_MAGIC',
    'pack',
    'unpack',
    'shmName'
]

# bumped whenever messages change, the server refuses other versions
PROTOCOL_VERSION = 1

# environment variable the connection's authentication key is passed in, so it
# isn't visible in the server's command line
ENV_AUTHKEY = 'PSYCHOPY_WEB_AUTHKEY'

# environment variable giving a command to run in place of the server (for
# testing), the connection arguments are appended to it
ENV_SERVER_CMD = 'PSYCHOPY_WEB_SERVER_CMD'

# prefix of console messages which are messages from the page to PsychoPy
MESSAGE_TAG = '__psychopy_message__:'

# pixel formats of frames, by name in `surface` messages: whether the bytes of
# each pixel are in RGBA or BGRA order, and whether colors are premultiplied by
# alpha (they always are, as Qt gives them)
FORMATS = {
    'rgba_pm': 1,
    'bgra_pm': 2
}

# header at the start of each shared memory segment, so the stimulus can check
# it is reading what it was told it would be: magic, protocol version, width,
# height, stride (bytes per row), format, number of slots and generation
HEADER = struct.Struct('<4sIIIIIII')
HEADER_SIZE = 64  # the header, padded so frames start aligned
HEADER_MAGIC = b'PWB1'


def pack(msg):
    """Pack a message to send.

    Parameters
    ----------
    msg : dict
        Message, with at least an `'op'` key.

    Returns
    -------
    bytes
        Packed message.

    """
    return msgpack.packb(msg, use_bin_type=True)


def unpack(data):
    """Unpack a received message.

    Parameters
    ----------
    data : bytes
        Packed message.

    Returns
    -------
    dict
        Message.

    """
    return msgpack.unpackb(data, raw=False)


def shmName(pid, view, gen):
    """Name of the shared memory segment frames of a page are written to.

    POSIX shared memory names are limited to 31 characters on macOS, including
    the leading slash Python adds, so names are kept short.

    Parameters
    ----------
    pid : int
        Process ID of the server.
    view : int
        ID of the page.
    gen : int
        Generation of the page's frames, which changes when they change size.

    Returns
    -------
    str
        Name of the segment.

    """
    return 'pw{:x}_{:x}_{:x}'.format(pid, view, gen)
