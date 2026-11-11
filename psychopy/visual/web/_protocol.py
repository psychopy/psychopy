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
* `gpuStatus` - whether shared slots on the GPU checked out (`gen`, `ok`,
  `reason`), see `_gpushare`.
* `close` - close a page, `shutdown` - close everything and exit.

`create` has a `gpu` field (`deviceUUID`, `driverUUID` of the stimulus'
OpenGL context) when the stimulus can take frames on the GPU.

Messages from the server:

* `hello` - sent once connected (`protocol`, `pid`, `versions`), or `fatal`
  (`error`) if the server can't start.
* `surface` - where frames will be written (`shm`, `w`, `h`, `stride`, `fmt`,
  `slots`, `gen`, `dpr`), then `frame` for each frame written there (`slot`,
  `seq`, `gen`, `t`). For frames on the GPU it has `transport` `'gpu'`, no
  `shm` or `stride`, and `memSize`, and is followed by the file descriptors
  of each slot's memory, *ready* and *done* semaphores (see `_gpushare`).
* `gpuFallback` (`reason`) - frames go in shared memory from now on.
* `loadStarted`, `loadProgress` (`pct`), `loadFinished` (`ok`, `url`),
  `urlChanged` (`url`), `titleChanged` (`title`).
* `console` (`level`, `msg`, `line`, `src`), `pageMessage` (`data`, `origin`),
  `dialog` (`kind`, `msg`).
* `navBlocked` (`url`), `permissionDenied` (`feature`, `origin`), `cursor`
  (`shape`), `renderGone` (`status`, `code`), `jsResult` (`id`, `ok`, `value`
  or `error`), `error` (`msg`), `closed`.

A message followed by file descriptors (`sendFds`) says how many in `nfds`.
`hello` has a `gpu` field, `'auto'` if the server can share frames on the GPU
and `'off'` if not.

This module only uses the standard library and msgpack, as the server imports
it without importing PsychoPy.
"""

import array
import os
import socket
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
    'shmName',
    'sendFds',
    'recvFds',
    'makeBlocking'
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


def makeBlocking(conn):
    """Make a connection's socket blocking again.

    A socket object made while a default timeout is set (`psychopy.web` sets
    one) puts the socket into non-blocking mode, which reads on the connection
    then fail with `BlockingIOError`.

    On Windows connections are named pipes, not sockets, which a default
    timeout doesn't affect (and their handles aren't file descriptors), so they
    are left alone.

    Parameters
    ----------
    conn : multiprocessing.connection.Connection
        Connection to fix.

    """
    if os.name != 'posix':
        return
    os.set_blocking(conn.fileno(), True)


def _socketFor(conn):
    """A socket object for a connection's socket, to pass file descriptors
    on, which leaves it blocking."""
    sock = socket.socket(fileno=os.dup(conn.fileno()))
    sock.settimeout(None)  # whatever the default timeout is
    return sock


def sendFds(conn, fds):
    """Send file descriptors on a Unix socket connection, after the message
    they go with. The caller still owns (and closes) its own.

    Parameters
    ----------
    conn : multiprocessing.connection.Connection
        Connection to send on.
    fds : list of int
        File descriptors to send.

    """
    with _socketFor(conn) as sock:
        sock.sendmsg(
            [bytes([len(fds) % 256])],
            [(socket.SOL_SOCKET, socket.SCM_RIGHTS, array.array('i', fds))])


def recvFds(conn, count):
    """Receive file descriptors sent with `sendFds`, right after reading the
    message they go with.

    Parameters
    ----------
    conn : multiprocessing.connection.Connection
        Connection to receive on.
    count : int
        Number of file descriptors sent.

    Returns
    -------
    list of int
        The file descriptors, which the caller owns.

    """
    fds = array.array('i')
    with _socketFor(conn) as sock:
        msg, ancdata, flags, addr = sock.recvmsg(
            1, socket.CMSG_SPACE(count * fds.itemsize))
    for level, kind, data in ancdata:
        if level == socket.SOL_SOCKET and kind == socket.SCM_RIGHTS:
            fds.frombytes(data[:len(data) - (len(data) % fds.itemsize)])
    if len(fds) != count:
        for fd in fds:
            os.close(fd)
        raise RuntimeError("Expected {} file descriptors, got {}".format(
            count, len(fds)))
    return list(fds)
