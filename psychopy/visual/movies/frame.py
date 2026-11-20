#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Decoded movie frames, as movie readers hand them to `MovieStim`.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'FRAME_PIXEL_FORMAT',
    'FRAME_BYTES_PER_PIXEL',
]

import numpy as np

# Pixel format every decoder backend delivers frames in, and the number of bytes
# per pixel it uses. Frames are packed RGBA rather than RGB even though the
# movie has no use for the alpha channel, since many drivers have no native
# three-byte texture format and convert RGB uploads on the way to the GPU.
FRAME_PIXEL_FORMAT = 'rgba'
FRAME_BYTES_PER_PIXEL = 4

# Pixel formats of decoded frames which are uploaded as their planes and
# converted to RGB by a shader as they are (see `gpuColorConversion`):
# 8-bit planar YUV, with any chroma subsampling. Others are converted to RGBA
# by `swscale` as they're decoded.
_YUV_PLANAR_FORMATS = frozenset((
    'yuv420p', 'yuvj420p', 'yuv422p', 'yuvj422p', 'yuv444p', 'yuvj444p',
    'yuv440p', 'yuvj440p', 'yuv411p', 'yuv410p'))

# The same for semi-planar YUV 4:2:0, a luma plane and a plane of interleaved
# chroma pairs, which hardware decoders give frames in (see
# `hardwareDecoding`): 8-bit `nv12`, and `p010le` and `p016le`, whose samples
# are 16-bit with the 10 or 16 bits used at the top
_YUV_SEMIPLANAR_FORMATS = frozenset(('nv12', 'p010le', 'p016le'))

# Bits each sample is stored in, and how many of them are used (at the top),
# for formats where that isn't 8 of 8
_YUV_SAMPLE_BITS = {
    'p010le': (16, 10),
    'p016le': (16, 16)}


def _isGPUYUVFormat(formatName):
    """Whether frames in a pixel format can be uploaded as they are and
    converted to RGB by a shader (`bool`)."""
    return formatName in _YUV_PLANAR_FORMATS or \
        formatName in _YUV_SEMIPLANAR_FORMATS


# `swscale` names of the colour matrices YUV is encoded with, by the value of
# FFmpeg's `AVColorSpace` a frame is tagged with
_AVCOL_SPC_TO_SWSCALE = {
    1: 'ITU709',  # BT709
    4: 'FCC',
    5: 'ITU601',  # BT470BG
    6: 'ITU601',  # SMPTE170M
    7: 'SMPTE240M',
    9: 'BT2020',  # BT2020_NCL
    10: 'BT2020'}  # BT2020_CL, which a matrix can only approximate

# `AVColorSpace` to tag a frame with for `swscale` to convert it with each
# colour matrix, for PyAV versions with no name for one (BT.2020 before 18)
_SWSCALE_TO_AVCOL_SPC = {
    'ITU709': 1,
    'FCC': 4,
    'ITU601': 5,
    'SMPTE240M': 7,
    'BT2020': 9}  # BT2020_NCL, `swscale` refuses BT2020_CL

# Luma coefficients (Kr, Kb) of each colour matrix, see `_yuvToRGBUniforms`
_COLOR_MATRIX_KR_KB = {
    'ITU601': (0.299, 0.114),
    'ITU709': (0.2126, 0.0722),
    'SMPTE240M': (0.212, 0.087),
    'BT2020': (0.2627, 0.0593),
    'FCC': (0.30, 0.11)}


def _frameColorMatrix(frame):
    """Colour matrix a decoded video frame's YUV is encoded with, by its
    `swscale` name (`str`).

    This goes by what the frame is tagged with. An untagged frame is taken to
    be BT.709 if it is HD or larger and BT.601 otherwise, as video players
    take it to be.

    """
    colorMatrix = _AVCOL_SPC_TO_SWSCALE.get(int(frame.colorspace))
    if colorMatrix is None:
        large = frame.width >= 1280 or frame.height >= 720
        colorMatrix = 'ITU709' if large else 'ITU601'

    return colorMatrix


def _isYUVFormat(formatName):
    """Whether a pixel format holds YUV (rather than RGB or grey) samples."""
    return 'yuv' in formatName or formatName.startswith(('nv', 'p01', 'p21'))


class _RGBFrameAdapter:
    """Lightweight adapter exposing an `ffpyplayer`-like interface around raw
    RGBA frame bytes obtained from other decoder backends (currently
    `PyAV`, `OpenCV` and `VLC`).

    Higher level code (`MovieFileReader`, `MovieStim`) was originally written
    around `ffpyplayer`'s `Image` objects, which expose `.to_memoryview()`
    (returning a list whose first element has a `.memview` attribute) and
    `.get_pixel_format()`. Wrapping decoded frames from other backends in
    this adapter lets that code stay backend-agnostic instead of branching
    on `decoderLib` throughout.

    Parameters
    ----------
    rgbData : bytes or numpy.ndarray
        Raw RGBA pixel data, row-major, 4 bytes per pixel (see
        `FRAME_PIXEL_FORMAT`). An array is kept
        as-is (made contiguous first if needed) rather than converted to
        `bytes`, which would cost a whole-frame copy per decoded frame for no
        benefit; everything downstream reads this through the buffer protocol.

    """
    __slots__ = ['_data']

    def __init__(self, rgbData):
        if isinstance(rgbData, np.ndarray):
            rgbData = np.ascontiguousarray(rgbData)

        self._data = rgbData

    def to_memoryview(self):
        return [self]

    @property
    def memview(self):
        return self._data

    def get_pixel_format(self):
        return FRAME_PIXEL_FORMAT

    @property
    def size(self):
        """Size `(w, h)` of the frame in pixels (`tuple`), or `None` if the
        frame is raw bytes, which are always the movie's own size."""
        if isinstance(self._data, np.ndarray) and self._data.ndim == 3:
            return self._data.shape[1], self._data.shape[0]

        return None


class _YUVFrameAdapter:
    """A decoded frame kept as its YUV samples, to be uploaded as they are and
    converted to RGB by a shader on the GPU.

    Parameters
    ----------
    frame : av.VideoFrame
        The frame, in one of `_YUV_PLANAR_FORMATS` or
        `_YUV_SEMIPLANAR_FORMATS`. This holds on to it, so that its planes can
        be uploaded straight from where they were decoded.

    """
    __slots__ = ['_frame', 'planes', 'size', 'colorMatrix', 'fullRange',
                 'pixelFormat', 'semiPlanar', 'sampleBits']

    def __init__(self, frame):
        self._frame = frame
        #: Name of the frame's pixel format
        self.pixelFormat = frame.format.name
        #: Whether the chroma is one plane of interleaved U and V samples
        #: (e.g. `nv12`) rather than a plane of each
        self.semiPlanar = self.pixelFormat in _YUV_SEMIPLANAR_FORMATS
        #: Bits each sample is stored in, and how many of them (at the top)
        #: are used, see `_yuvToRGBUniforms`
        self.sampleBits = _YUV_SAMPLE_BITS.get(self.pixelFormat, (8, 8))
        #: Each plane (Y, U then V, or Y then UV) as `(samples, width, height,
        #: rowLength)`, `samples` being a flat array of `rowLength` bytes per
        #: row, and `width` the samples (or pairs of chroma samples) per row
        self.planes = tuple(
            (np.frombuffer(plane, np.uint8), plane.width, plane.height,
             plane.line_size)
            for plane in frame.planes[:2 if self.semiPlanar else 3])
        #: Size `(w, h)` of the frame in pixels
        self.size = (frame.width, frame.height)
        #: `swscale` name of the colour matrix, see `_frameColorMatrix`
        self.colorMatrix = _frameColorMatrix(frame)
        #: Whether the samples are full range, see `_yuvToRGBUniforms`
        self.fullRange = int(frame.color_range) == 2 or \
            self.pixelFormat.startswith('yuvj')

    @property
    def nbytes(self):
        """Bytes of samples the frame's planes hold (`int`)."""
        return sum(samples.nbytes for samples, _, _, _ in self.planes)
