#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Movie reader using PyAV.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'PyAVMovieFileReader',
]

import time

from psychopy import logging
from ..exceptions import MovieFileFormatError
from ..frame import (
    FRAME_PIXEL_FORMAT, _RGBFrameAdapter, _YUVFrameAdapter,
    _YUV_PLANAR_FORMATS, _SWSCALE_TO_AVCOL_SPC, _frameColorMatrix,
    _isYUVFormat)
from ._base import MovieFileReader, defaultTimeout


class PyAVMovieFileReader(MovieFileReader):
    """Read movie frames from a file with PyAV.

    Frames are decoded ahead of playback on a background thread (see
    `_runDecoder`). PyAV provides no audio playback of its own, so the audio
    track is played back separately (this is handled automatically by
    `MovieStim`). See `MovieFileReader` for parameters.

    """
    _decoderLib = 'pyav'

    def __init__(self, filename, decoderLib=None, decoderOpts=None):
        super().__init__(filename, decoderLib, decoderOpts)

        self._container = None  # av.container.InputContainer
        self._videoStream = None  # av video stream being decoded
        self._packetIterator = None  # generator yielding decoded video frames
        # `swscale` colour matrices PyAV has a name for, set on open
        self._namedColorMatrices = frozenset()

    def _open(self):
        """Open a movie reader using PyAV.

        This function opens the movie file using the `av` package and extracts
        metadata about the movie file. Metadata will be accessible via the
        `getMetadata()` method.

        Once the first frame has been read, frames are decoded ahead of
        playback on a background thread (see `_runDecoder`), so that a
        frame which is slow to decode does not hold up drawing.

        """
        logging.info("Using PyAV for reading movie frames.")
        try:
            import av
        except ImportError:
            raise ImportError(
                'The `av` (PyAV) library is required to read movie files with '
                '`decoderLib=pyav`. Install it with `pip install av`.')

        from av.video.reformatter import Colorspace
        self._namedColorMatrices = frozenset(Colorspace.__members__)

        logging.info("Opening movie file: {}".format(self._filename))

        openOpts = self._decoderOpts.get('options', {})
        self._container = av.open(self._filename, options=openOpts)

        videoStream = next(
            (s for s in self._container.streams if s.type == 'video'), None)
        
        if videoStream is None:
            self._container.close()
            self._container = None
            raise MovieFileFormatError(self._filename)

        # use multi-threaded decoding where available for faster frame access
        try:
            videoStream.thread_type = 'AUTO'
        except Exception:
            pass  # not fatal if the codec doesn't support threaded decoding

        self._videoStream = videoStream

        # determine the frame rate; prefer the averaged rate reported by the
        # stream, falling back to the guessed rate if unavailable
        rateFraction = videoStream.average_rate or videoStream.guessed_rate
        if not rateFraction:
            raise RuntimeError(
                'PyAV could not determine the frame rate of the movie file.')
        frameRate = float(rateFraction)

        width = videoStream.codec_context.width
        height = videoStream.codec_context.height

        # determine duration in seconds, preferring the stream's own duration
        if videoStream.duration is not None and videoStream.time_base is not None:
            duration = float(videoStream.duration * videoStream.time_base)
        elif self._container.duration is not None:
            duration = float(self._container.duration / av.time_base)
        else:
            raise RuntimeError(
                'PyAV could not determine the duration of the movie file.')

        self._setMovieProperties((width, height), frameRate, duration)

        # start the decode generator and warm up by grabbing the first frame
        self._packetIterator = self._container.decode(video=0)

        startTime = time.time()
        firstFrame = None
        while time.time() - startTime < defaultTimeout:
            try:
                firstFrame = next(self._packetIterator)
                break
            except StopIteration:
                break
        if firstFrame is None:
            raise RuntimeError(
                'PyAV failed to decode the first frame of the movie. Check '
                'the movie file.')

        # carry on decoding from here in the background
        self._startDecoder(firstFrame)

    def _freePlayer(self):
        # the decode thread must be done with the container before it can be
        # closed
        if not self._stopDecoder():
            return
        if self._container is not None:
            self._container.close()
            self._container = None
        self._videoStream = None
        self._packetIterator = None

    def _decodeNextFrame(self):
        avFrame = next(self._packetIterator, None)
        if avFrame is None:
            return None
        pts = float(avFrame.pts * self._videoStream.time_base) \
            if avFrame.pts is not None else 0.0

        return avFrame, pts

    def _seekDecoder(self, pts):
        """Seek the container to the keyframe at or before `pts` (seconds).
        Only the decode thread may call this once it has been started."""
        self._container.seek(
            int(pts / self._videoStream.time_base), stream=self._videoStream,
            any_frame=False, backward=True)
        # decoding must restart after a container-level seek
        self._packetIterator = self._container.decode(video=0)

    def _convertFrameToRGB(self, frame):
        """Convert a PyAV frame to RGBA format.

        Parameters
        ----------
        frame : av.VideoFrame or `_RGBFrameAdapter`
            The frame to convert. If already an `_RGBFrameAdapter` (i.e.
            previously converted), it is returned unchanged.

        Returns
        -------
        _RGBFrameAdapter
            The converted frame, wrapped to present an `ffpyplayer`-like
            interface to downstream code.

        """
        if isinstance(frame, (_RGBFrameAdapter, _YUVFrameAdapter)):
            return frame  # already converted

        outputSize, interpolation, keepYUV = self._outputFrameFormat
        width, height = frame.width, frame.height
        if outputSize is not None:
            width = min(outputSize[0], width)
            height = min(outputSize[1], height)
        scaled = (width, height) != (frame.width, frame.height)

        formatName = frame.format.name
        if keepYUV and formatName in _YUV_PLANAR_FORMATS:
            # Left as YUV for the shader it's drawn with to convert, see
            # `setOutputPixelFormat`. Scaling it down if need be is the only
            # work there is to do here.
            if scaled:
                frame = frame.reformat(
                    width=width, height=height, interpolation=interpolation)
            return _YUVFrameAdapter(frame)

        # Converted with the colour matrix the frame is encoded with. PyAV goes
        # by what the frame is tagged with, but takes an untagged frame to be
        # BT.601 whatever its size, where players take HD to be BT.709.
        convertOpts = {}
        if _isYUVFormat(formatName):
            colorMatrix = _frameColorMatrix(frame)
            if colorMatrix in self._namedColorMatrices:
                convertOpts['src_colorspace'] = colorMatrix
            else:
                # PyAV before 18 has no name for BT.2020, so the frame is
                # (re)tagged with it instead, which PyAV then goes by
                frame.colorspace = _SWSCALE_TO_AVCOL_SPC[colorMatrix]

        # Scaled down in the same `swscale` pass as the conversion, which costs
        # little more than the conversion alone, see `setOutputFrameSize`
        if scaled:
            convertOpts.update(
                width=width, height=height, interpolation=interpolation)

        return _RGBFrameAdapter(
            frame.to_ndarray(format=FRAME_PIXEL_FORMAT, **convertOpts))
