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

import sys
import time

from psychopy import logging
from ..exceptions import MovieFileFormatError
from ..frame import (
    FRAME_PIXEL_FORMAT, _RGBFrameAdapter, _YUVFrameAdapter,
    _SWSCALE_TO_AVCOL_SPC, _frameColorMatrix, _isYUVFormat, _isGPUYUVFormat)
from ._base import MovieFileReader, defaultTimeout

# Hardware decoders `hardwareDecoding=True` tries on each platform, best first
# (CUDA takes the least CPU to hand frames over), of those FFmpeg was built
# with. Those which can't be used here, or can't decode the movie, are passed
# over.
_AUTO_HARDWARE_DECODERS = {
    'win32': ('cuda', 'd3d11va', 'dxva2'),
    'linux': ('cuda', 'vaapi'),
    'darwin': ('videotoolbox',)}


def _hardwareDecodersToTry(request):
    """Hardware decoders (FFmpeg device types) to try for a
    `hardwareDecoding` setting, best first.

    Parameters
    ----------
    request : bool, str or None
        `True` or `'auto'` for the best available, a device type (e.g.
        `'cuda'`) for that one, or `False` or `None` for none.

    Returns
    -------
    tuple
        `(devices, problem)`: the decoders to try, and if there are none to
        try for a request for some, why not (else `None`).

    """
    if not request:
        return [], None

    problem = PyAVMovieFileReader._hardwareDecodingProblem()
    if problem is not None:
        return [], problem

    from av.codec.hwaccel import hwdevices_available
    available = set(hwdevices_available())
    availableText = ', '.join(sorted(available)) or 'none'

    if request is True or request == 'auto':
        platform = 'linux' if sys.platform.startswith('linux') \
            else sys.platform
        candidates = _AUTO_HARDWARE_DECODERS.get(platform, ())
        devices = [device for device in candidates if device in available]
        if not devices:
            return [], (
                "PyAV has none of the hardware decoders tried on this "
                "platform ({}; it has: {})".format(
                    ', '.join(candidates) or 'none', availableText))
        return devices, None

    if request not in available:
        return [], "PyAV has no hardware decoder {!r} (it has: {})".format(
            request, availableText)

    return [request], None


class PyAVMovieFileReader(MovieFileReader):
    """Read movie frames from a file with PyAV.

    Frames are decoded ahead of playback on a background thread (see
    `_runDecoder`). PyAV provides no audio playback of its own, so the audio
    track is played back separately (this is handled automatically by
    `MovieStim`). See `MovieFileReader` for parameters.

    """
    _decoderLib = 'pyav'
    supportsHardwareDecoding = True

    @classmethod
    def _hardwareDecodingProblem(cls):
        try:
            import av
        except ImportError:
            return "PyAV isn't installed"
        try:
            from av.codec.hwaccel import hwdevices_available  # noqa: F401
        except ImportError:
            return "PyAV {} can't (it needs PyAV 14 or later)".format(
                av.__version__)

        return None

    def __init__(self, filename, decoderLib=None, decoderOpts=None):
        super().__init__(filename, decoderLib, decoderOpts)

        self._container = None  # av.container.InputContainer
        self._videoStream = None  # av video stream being decoded
        self._packetIterator = None  # generator yielding decoded video frames
        # `swscale` colour matrices PyAV has a name for, set on open
        self._namedColorMatrices = frozenset()
        # hardware decoder the movie is decoded with, see `hardwareDecoder`
        self._hardwareDecoder = None

    @property
    def hardwareDecoder(self):
        """FFmpeg device type of the hardware decoder the movie is decoded
        with (e.g. `'cuda'`), or `None` if it's decoded in software (`str` or
        `None`). Set by `open()`, from the decoder option `'hwaccel'` (see
        `MovieStim`'s `hardwareDecoding`)."""
        return self._hardwareDecoder

    def _openContainer(self, av, openOpts, device):
        """Open the movie and decode its first frame, with a hardware decoder
        or in software.

        Returns
        -------
        tuple or None
            `(container, videoStream, firstFrame, hardware)`, `hardware` being
            whether the frame was decoded with the hardware decoder asked for
            (PyAV falls back to software if it can't be used), or `None` if
            the movie has no video stream.

        """
        kwargs = {}
        if device is not None:  # PyAV before 14 has no `hwaccel`
            from av.codec.hwaccel import HWAccel
            kwargs['hwaccel'] = HWAccel(device, allow_software_fallback=True)
        container = av.open(self._filename, options=openOpts, **kwargs)

        videoStream = next(
            (s for s in container.streams if s.type == 'video'), None)
        if videoStream is None:
            container.close()
            return None

        # Use multi-threaded decoding where available for faster frame access.
        # Not frame threads with a hardware decoder, which gain it little
        # (it decodes 4K at over 200 fps without), and at the end of the movie
        # take ~5-7 ms to drain (at 4K) holding the GIL, which stalls drawing.
        try:
            videoStream.thread_type = 'AUTO' if device is None else 'SLICE'
        except Exception:
            pass  # not fatal if the codec doesn't support threaded decoding

        packetIterator = container.decode(video=0)
        startTime = time.time()
        firstFrame = None
        while time.time() - startTime < defaultTimeout:
            try:
                firstFrame = next(packetIterator)
                break
            except StopIteration:
                break

        # Whether the hardware decoder decoded the frame. PyAV's `is_hwaccel`
        # can't say, being true whenever one was asked for, even once FFmpeg
        # has fallen back to software because it couldn't be set up (as
        # VideoToolbox can't for MPEG-2, MPEG-4 Part 2 or ProRes on some
        # Macs). The codec context is left in the hardware decoder's own pixel
        # format (e.g. `videotoolbox_vld`, which has no components) only if
        # it did.
        codecFormat = videoStream.codec_context.format
        hardware = device is not None and firstFrame is not None and \
            codecFormat is not None and not codecFormat.components
        self._packetIterator = packetIterator

        return container, videoStream, firstFrame, hardware

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

        # With a hardware decoder if asked for one, trying each that might do
        # until one does, and in software if none can. Each tried decodes the
        # first frame, which is when it's known whether it could be used.
        opened = None
        self._hardwareDecoder = None
        requested = self._decoderOpts.get('hwaccel')
        devices, problem = _hardwareDecodersToTry(requested)
        for device in devices + [None]:
            if opened is not None:
                opened[0].close()  # the last one tried, which couldn't
                opened = None
            try:
                opened = self._openContainer(av, openOpts, device)
            except av.FFmpegError as err:
                if device is None:
                    raise
                # FFmpeg was built with it, but couldn't set it up here (e.g.
                # there's no GPU, or no access to one)
                logging.info(
                    "Hardware decoder {!r} couldn't be set up for {}: "
                    "{}".format(device, self._filename, err))
                continue
            if opened is None:
                raise MovieFileFormatError(self._filename)
            if device is None or opened[3]:
                self._hardwareDecoder = device
                break
            logging.info(
                "Hardware decoder {!r} can't decode {}.".format(
                    device, self._filename))
        self._container, videoStream, firstFrame, _ = opened
        if self._hardwareDecoder is not None:
            logging.info("Decoding {} with hardware decoder {!r}.".format(
                self._filename, self._hardwareDecoder))
        elif requested:
            # asked for, so say why it's not being used
            if problem is None:
                problem = "{} can't decode it".format(
                    "hardware decoder {!r}".format(devices[0])
                    if len(devices) == 1 else
                    "none of the hardware decoders tried ({})".format(
                        ', '.join(devices)))
            logging.warning(
                "Hardware decoding was asked for, but {}, so {} is decoded "
                "in software.".format(problem, self._filename))

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

        # the first frame was decoded as the movie was opened, as a warm up
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
        if keepYUV and _isGPUYUVFormat(formatName):
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
