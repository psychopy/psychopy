#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Movie reader using OpenCV.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2025 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'OpenCVMovieFileReader',
]

from psychopy import logging
from ..exceptions import MovieFileFormatError
from ..frame import _RGBFrameAdapter
from ._base import MovieFileReader

# OpenCV's nearest equivalents of the `swscale` filters frames are scaled down
# with, see `_resizeFrameOpenCV`
_OPENCV_INTERPOLATION = {
    'POINT': 'INTER_NEAREST',
    'FAST_BILINEAR': 'INTER_LINEAR',
    'BILINEAR': 'INTER_LINEAR',
    'BICUBIC': 'INTER_CUBIC',
    'LANCZOS': 'INTER_LANCZOS4'}


def _resizeFrameOpenCV(frame, size, interpolation='AREA'):
    """Scale a frame decoded by OpenCV down to `size`.

    A box filter (`'AREA'`) is quick where the frame's size is a whole multiple
    of `size`, but the general case is slow for large reductions (~20 ms
    taking a 4K frame down to 333x250). So unless the sizes divide exactly,
    the frame is first halved for as long as it divides exactly without going
    below `size`, which stays on the quick path, and only what's left is done
    the slow way. That softens the result a little compared with doing it in
    one go, and makes the cost a few milliseconds at most for a 4K frame.

    Parameters
    ----------
    frame : ndarray
        Frame decoded by OpenCV, shaped `(h, w, channels)`.
    size : tuple
        Size `(w, h)` in pixels to scale to, no larger than the frame's own.
    interpolation : str
        `swscale` name of the filter to use, see `setOutputFrameSize`.

    Returns
    -------
    ndarray
        The frame at `size`.

    """
    import cv2

    if interpolation != 'AREA':
        return cv2.resize(frame, size, interpolation=getattr(
            cv2, _OPENCV_INTERPOLATION.get(interpolation, 'INTER_AREA')))

    height, width = frame.shape[:2]
    if width % size[0] or height % size[1]:
        def halvings(src, dst):
            factor = 1
            while src % (2 * factor) == 0 and src // (2 * factor) >= dst:
                factor *= 2
            return factor

        xFactor, yFactor = halvings(width, size[0]), halvings(height, size[1])
        if xFactor > 1 or yFactor > 1:
            frame = cv2.resize(
                frame, (width // xFactor, height // yFactor),
                interpolation=cv2.INTER_AREA)

    if (frame.shape[1], frame.shape[0]) == tuple(size):
        return frame

    return cv2.resize(frame, size, interpolation=cv2.INTER_AREA)


class OpenCVMovieFileReader(MovieFileReader):
    """Read movie frames from a file with OpenCV.

    As with `pyav`, frames are decoded ahead of playback on a background
    thread (see `_runDecoder`), and OpenCV provides no audio playback of its
    own. Presentation timestamps are derived from frame indices and the
    reported frame rate, so movies with a variable frame rate will not be timed
    correctly. See `MovieFileReader` for parameters.

    """
    _decoderLib = 'opencv'

    def __init__(self, filename, decoderLib=None, decoderOpts=None):
        super().__init__(filename, decoderLib, decoderOpts)

        self._capture = None  # cv2.VideoCapture object

    def _open(self):
        """Open a movie reader using OpenCV.

        This function opens the movie file using the `cv2` package and extracts
        metadata about the movie file. Metadata will be accessible via the
        `getMetadata()` method.

        As with `PyAV`, once the first frame has been read, frames are decoded
        ahead of playback on a background thread (see `_runDecoder`), and
        OpenCV provides no audio playback of its own. OpenCV reports frame
        positions as indices rather than timestamps, so presentation timestamps
        are derived from the frame index and the frame rate. This assumes a
        constant frame rate; use `pyav` or `ffpyplayer` for variable frame
        rate movies.

        """
        logging.info("Using OpenCV for reading movie frames.")
        try:
            import cv2
        except ImportError:
            raise ImportError(
                'The `opencv-python` (cv2) library is required to read movie '
                'files with `decoderLib=opencv`. Install it with '
                '`pip install opencv-python`.')

        logging.info("Opening movie file: {}".format(self._filename))

        capture = cv2.VideoCapture(self._filename)
        if not capture.isOpened():
            capture.release()
            raise MovieFileFormatError(self._filename)

        self._capture = capture

        # determine the frame rate, OpenCV reports `0` if it cannot work it out
        frameRate = float(capture.get(cv2.CAP_PROP_FPS))
        if not frameRate > 0.0:
            self._freePlayer()
            raise RuntimeError(
                'OpenCV could not determine the frame rate of the movie file. '
                'Try `movieLib="pyav"` instead for this file.')

        width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        if width <= 0 or height <= 0:
            self._freePlayer()
            raise RuntimeError(
                'OpenCV could not determine the frame size of the movie file.')

        # OpenCV has no direct notion of duration, so it is computed from the
        # frame count and the frame rate
        frameCount = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
        if frameCount <= 0:
            self._freePlayer()
            raise RuntimeError(
                'OpenCV could not determine the duration of the movie file. '
                'Try `movieLib="pyav"` instead for this file.')
        duration = frameCount / frameRate

        self._setMovieProperties((width, height), frameRate, duration)

        # warm up the decoder by grabbing the first frame
        success, firstFrame = capture.read()
        if not success:
            self._freePlayer()
            raise RuntimeError(
                'OpenCV failed to decode the first frame of the movie. Check '
                'the movie file.')

        # carry on decoding from here in the background, as with `pyav`
        self._startDecoder(firstFrame)

    def _freePlayer(self):
        # the decode thread must be done with the capture before it can be
        # released
        if not self._stopDecoder():
            return
        if self._capture is not None:
            self._capture.release()
            self._capture = None

    def _decodeNextFrame(self):
        import cv2

        # The frame index before reading is that of the frame about to be
        # decoded, which gives its PTS, OpenCV going by frame indices
        frameIndex = int(self._capture.get(cv2.CAP_PROP_POS_FRAMES))
        success, bgrFrame = self._capture.read()
        if not success:
            return None

        return bgrFrame, self._frameIndexToTimestamp(frameIndex)

    def _seekDecoder(self, pts):
        """Seek the capture to the frame at or before `pts` (seconds). Only the
        decode thread may call this once it has been started.

        OpenCV decodes forward from the keyframe before that frame itself, so
        the next frame read is the one at `pts`.

        """
        import cv2

        # prefer frame-index seeking since presentation timestamps for this
        # backend are derived from frame indices
        targetFrame = self._timestampToFrameIndex(pts)
        if not self._capture.set(cv2.CAP_PROP_POS_FRAMES, targetFrame):
            # fall back to millisecond seeking if the backend in use doesn't
            # support seeking by frame index
            self._capture.set(cv2.CAP_PROP_POS_MSEC, pts * 1000.0)

    def _convertFrameToRGB(self, frame):
        """Convert an OpenCV frame to RGB format.

        OpenCV decodes frames as BGR arrays, which must be converted to RGB
        before being uploaded as a texture.

        Parameters
        ----------
        frame : numpy.ndarray or `_RGBFrameAdapter`
            The frame to convert. If already an `_RGBFrameAdapter` (i.e.
            previously converted), it is returned unchanged.

        Returns
        -------
        _RGBFrameAdapter
            The converted frame, wrapped to present an `ffpyplayer`-like
            interface to downstream code.

        """
        if isinstance(frame, _RGBFrameAdapter):
            return frame  # already converted

        import cv2

        # Scaled down before converting, which then has fewer pixels to do,
        # see `setOutputFrameSize`
        outputSize, interpolation, _ = self._outputFrameFormat
        if outputSize is not None:
            height, width = frame.shape[:2]
            size = (min(outputSize[0], width), min(outputSize[1], height))
            if size != (width, height):
                frame = _resizeFrameOpenCV(frame, size, interpolation)

        # OpenCV decodes to BGR; this also fills in an opaque alpha channel
        return _RGBFrameAdapter(cv2.cvtColor(frame, cv2.COLOR_BGR2RGBA))
