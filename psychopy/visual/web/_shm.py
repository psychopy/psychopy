#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""Shared memory frames are passed from the web browser server in.

The server creates a segment for each page (and again each time its frames
change size), writes frames to its slots, and removes it. The stimulus attaches
to it and reads them. Which slots each side may use is passed in messages (see
`_protocol`), so nothing in the segment needs to be synchronized.

This module only uses the standard library, as the server imports it without
importing PsychoPy.
"""

import ctypes
import os
import sys
import weakref
from multiprocessing import shared_memory

try:
    import _protocol  # imported by the server, as a script
except ImportError:
    from . import _protocol

__all__ = ['FrameRing', 'closeOwnedRings']

_ALIGN = 64

# segments this process made, so they can be removed if it has to exit early
_ownedRings = weakref.WeakSet()


def closeOwnedRings():
    """Remove all the segments this process made which are still open."""
    for ring in list(_ownedRings):
        try:
            ring.close()
        except Exception:
            pass


def _attachUntracked(name):
    """Attach to a segment without the resource tracker removing it when this
    process exits, as it belongs to the process that made it."""
    if sys.version_info >= (3, 13):
        return shared_memory.SharedMemory(name=name, track=False)

    shm = shared_memory.SharedMemory(name=name)
    if os.name == 'posix':  # Windows doesn't track segments
        from multiprocessing import resource_tracker
        try:
            resource_tracker.unregister(shm._name, 'shared_memory')
        except Exception:
            pass

    return shm


class FrameRing:
    """Slots for frames of one size in a shared memory segment.

    Use `create` (in the server) or `attach` (in the stimulus) to make one.

    Parameters
    ----------
    shm : SharedMemory
        Segment holding the frames.
    width, height : int
        Size of the frames in pixels.
    stride : int
        Bytes per row of a frame.
    fmt : str
        Pixel format, a key of `_protocol.FORMATS`.
    nSlots : int
        Number of frames the segment holds.
    gen : int
        Generation of the page's frames.
    owner : bool
        Whether this process made the segment, and so removes it.

    """
    def __init__(self, shm, width, height, stride, fmt, nSlots, gen, owner):
        self._shm = shm
        self.width = width
        self.height = height
        self.stride = stride
        self.fmt = fmt
        self.nSlots = nSlots
        self.gen = gen
        self.owner = owner
        self.slotSize = self.slotSizeFor(stride, height)
        self._base = None  # ctypes view of the segment, for addresses

    @staticmethod
    def slotSizeFor(stride, height):
        """Bytes each slot takes, so they all start aligned."""
        size = stride * height
        return (size + _ALIGN - 1) // _ALIGN * _ALIGN

    @classmethod
    def create(cls, name, width, height, stride, fmt, nSlots, gen):
        """Make a segment for frames (in the server).

        Parameters
        ----------
        name : str
            Name of the segment, see `_protocol.shmName`.
        width, height, stride, fmt, nSlots, gen
            As for `FrameRing`.

        Returns
        -------
        FrameRing

        """
        size = _protocol.HEADER_SIZE + nSlots * cls.slotSizeFor(stride, height)
        shm = shared_memory.SharedMemory(name=name, create=True, size=size)
        shm.buf[:_protocol.HEADER.size] = _protocol.HEADER.pack(
            _protocol.HEADER_MAGIC, _protocol.PROTOCOL_VERSION, width, height,
            stride, _protocol.FORMATS[fmt], nSlots, gen)

        ring = cls(shm, width, height, stride, fmt, nSlots, gen, owner=True)
        _ownedRings.add(ring)

        return ring

    @classmethod
    def attach(cls, name, width, height, stride, fmt, nSlots, gen):
        """Attach to a segment the server made (in the stimulus), checking it
        holds what the server said it would.

        Parameters
        ----------
        name : str
            Name of the segment.
        width, height, stride, fmt, nSlots, gen
            As given in the server's `surface` message.

        Returns
        -------
        FrameRing

        Raises
        ------
        ValueError
            If the segment doesn't hold what was expected.

        """
        shm = _attachUntracked(name)
        try:
            header = _protocol.HEADER.unpack_from(shm.buf)
            expected = (
                _protocol.HEADER_MAGIC, _protocol.PROTOCOL_VERSION, width,
                height, stride, _protocol.FORMATS[fmt], nSlots, gen)
            if header != expected:
                raise ValueError(
                    "Shared memory {} holds {}, expected {}".format(
                        name, header, expected))
            needed = (_protocol.HEADER_SIZE
                      + nSlots * cls.slotSizeFor(stride, height))
            if shm.size < needed:
                raise ValueError(
                    "Shared memory {} is {} bytes, expected {}".format(
                        name, shm.size, needed))
        except Exception:
            shm.close()
            raise

        return cls(shm, width, height, stride, fmt, nSlots, gen, owner=False)

    @property
    def name(self):
        """Name of the segment (`str`)."""
        return self._shm.name

    def slotOffset(self, slot):
        """Offset of a slot from the start of the segment, in bytes."""
        if not 0 <= slot < self.nSlots:
            raise IndexError("No slot {} of {}".format(slot, self.nSlots))
        return _protocol.HEADER_SIZE + slot * self.slotSize

    def write(self, slot, data):
        """Write a frame to a slot.

        Parameters
        ----------
        slot : int
            Slot to write to.
        data : buffer
            Frame, `stride * height` bytes.

        """
        data = memoryview(data).cast('B')
        if data.nbytes != self.stride * self.height:
            raise ValueError("Frame is {} bytes, expected {}".format(
                data.nbytes, self.stride * self.height))
        offset = self.slotOffset(slot)
        self._shm.buf[offset:offset + data.nbytes] = data

    def view(self, slot):
        """Get the frame in a slot, without copying it.

        Release the view (e.g. with `del`) before closing the ring.

        Parameters
        ----------
        slot : int
            Slot to get.

        Returns
        -------
        memoryview
            Frame, `stride * height` bytes.

        """
        offset = self.slotOffset(slot)
        return self._shm.buf[offset:offset + self.stride * self.height]

    def address(self, slot):
        """Memory address of the frame in a slot (e.g. for uploading it with
        OpenGL).

        Parameters
        ----------
        slot : int
            Slot to get.

        Returns
        -------
        int
            Address of the first byte of the frame.

        """
        if self._base is None:
            self._base = (ctypes.c_char * self._shm.size).from_buffer(
                self._shm.buf)
        return ctypes.addressof(self._base) + self.slotOffset(slot)

    def close(self):
        """Detach from the segment, and remove it if this process made it."""
        if self._shm is None:
            return
        self._base = None  # can't close with views of it still around
        shm, self._shm = self._shm, None
        try:
            shm.close()
        except BufferError:  # a `view` is still held, it is freed with it
            pass
        if self.owner:
            try:
                shm.unlink()
            except FileNotFoundError:
                pass

    def __del__(self):
        try:
            self.close()
        except Exception:
            pass
