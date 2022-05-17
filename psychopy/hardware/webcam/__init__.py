#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for reading and writing webcam streams.

A webcam may be used to document participant responses on video or used by the
experimenter to create movie stimuli or instructions.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['CameraNotFoundError', 'Webcam', 'CameraInfo', 'getWebcams']

import os
import platform
import glob
from psychopy.constants import PLAYING, PAUSED, STOPPED, STOPPING, NOT_STARTED
from psychopy.core import getTime
from ffpyplayer.player import MediaPlayer
from ffpyplayer.writer import MediaWriter
from ffpyplayer.pic import SWScale


# ------------------------------------------------------------------------------
# Constants
#

VIDEO_DEVICE_ROOT_LINUX = '/dev'


# ------------------------------------------------------------------------------
# Exceptions
#

class CameraNotFoundError(Exception):
    """Raised when a camera cannot be found on the system."""


class PlayerNotAvailableError(Exception):
    """Raised when a player object is not available but is required."""


# ------------------------------------------------------------------------------
# Descriptors
#

class CameraInfo:
    """Descriptor for cameras connected to the system (such as webcams).

    Parameters
    ----------
    name : str
        Camera name retrieved by the OS.

    """
    __slots__ = [
        '_name',
        '_frameWidth',
        '_frameHeight',
        '_frameRateMin',
        '_frameRateMax',
        '_pixelFormat',
        '_codecFormat',
        '_cameraLib',
        '_cameraAPI'  # API in use, e.g. DirectShow on Windows
    ]

    def __init__(self,
                 name=u'Null',
                 frameSize=(-1, -1),
                 frameRateMin=-1,
                 frameRateMax=-1,
                 pixelFormat=u'rgb',
                 codecFormat=u'Null',
                 cameraLib=u'Null',
                 cameraAPI=u'Null'):

        self.name = name
        self._frameWidth = frameSize[0]
        self._frameHeight = frameSize[1]
        self._frameRateMin = frameRateMin
        self._frameRateMax = frameRateMax
        self._pixelFormat = pixelFormat
        self._codecFormat = codecFormat
        self._cameraLib = cameraLib
        self._cameraAPI = cameraAPI

    @property
    def name(self):
        """Camera name (`str`). This is the camera name retrieved by the OS.
        """
        return self._name

    @name.setter
    def name(self, value):
        self._name = str(value)


# ------------------------------------------------------------------------------
# Classes
#


class Webcam:
    """Class of displaying and recording video from a USB/PCI connected camera
    (usually a webcam).

    This class is capable of opening and recording webcam video streams.

    Parameters
    ----------
    camera : str or int
        Camera to open a stream with. If the ID is not valid, an error will be
        raised when `start()` is called. Value can be a string or number. String
        values are platform-dependent: a DirectShow URI on Windows, a path
        on GNU/Linux (e.g., '/dev/video0`), and a camera name on MacOS.
        Specifying a number (>=0) is a platform-independent means of selecting a
        webcam. PsychoPy enumerates possible camera devices and makes them
        selectable without explicitly having the name of the cameras attached to
        the system. Use caution when specifying a number, as the same index may
        not reference the same camera everytime.
    mic : :class:`~psychopy.sound.microphone.Microphone` or None
        Microphone to record audio samples from during recording. The microphone
        input device must not be in use when `record()` is called.
    outFile : str or None
        File name to write video frames to. If `None`, the video will only be
        decoded and no video will be written to disk.
    cameraLib : str
        Interface library (backend) to use for accessing the webcam. Only
        `ffpyplayer` is available at this time.
    libOpts : dict or None
        Additional options to configure the camera interface library.

    Examples
    --------
    Opening a webcam stream and closing it::

        webcam = Webcam(camera='/dev/video0')
        webcam.open()  # exception here on invalid camera
        # webcam.status == NOT_STARTED
        webcam.start()
        # webcam.status == PLAYING
        webcam.stop()
        # webcam.status == STOPPED
        webcam.close()

    """
    def __init__(self, camera=0, mic=None, outFile=None,
                 cameraLib=u'ffpyplayer', libOpts=None):

        # add attributes for setters
        self.__dict__.update(
            {'_camera': None,
             '_mic': None,
             '_outFile': None,
             '_cameraLib': u'',
             '_libOpts': None})

        # resolve getting the camera identifier
        if isinstance(camera, int):  # get camera if integer
            try:
                self.camera = getWebcams()[camera]
            except IndexError:  # catch as
                raise CameraNotFoundError(
                    'Could not enumerate camera with index `{}`.'.format(
                        camera))
        elif isinstance(camera, str):  # get camera if integer
            self.camera = camera
        else:
            raise TypeError(
                "Incorrect type for `camera`, expected `int` or `str`.")

        # camera library in use
        self._cameraLib = cameraLib

        self.mic = mic
        self.outFile = outFile

        # current camera frame since the start of recording
        self._player = None  # media player instance
        self._status = NOT_STARTED
        self._frameIndex = -1

        # timestamp data
        self._absPts = 0.0  # timestamp of the video stream in absolute time
        self._pts = 0.0  # timestamp used for writing the video stream

        # parameters for the writer
        self._writer = None

    @staticmethod
    def getWebcams():
        """Get information about installed cameras on this system.

        Returns
        -------
        list
            List of camera identifiers.

        """
        return getWebcams()

    def _initVideoWriter(self):
        """Initialize and configure the media writer.
        """
        pass

    # @property
    # def win(self):
    #     return self._win
    #
    # @win.setter
    # def win(self, value):
    #     self._win = value

    @property
    def status(self):
        """Status flag for the webcam (`int`).

        Can be either `PLAYING`, `PAUSED`, `STOPPED`, `STOPPING`, or
        `NOT_STARTED`.

        """
        return self._status

    @property
    def outFile(self):
        """Output file for the video stream (`str`).
        """
        return self._outFile

    @outFile.setter
    def outFile(self, value):
        self._outFile = value

    @property
    def camera(self):
        """Camera to use (`str` or `None`).

        String specifying the name of the camera to open a stream with. This
        must be set prior to calling `start()`. If the name is not valid, an
        error will be raised when `start()` is called.

        """
        return self._camera

    @camera.setter
    def camera(self, value):
        self._camera = value

    @property
    def mic(self):
        """Microphone to record audio samples from during recording
        (:class:`~psychopy.sound.microphone.Microphone` or `None`). If `None`,
        no audio will be recorded.
        """
        return self._mic

    @mic.setter
    def mic(self, value):
        self._mic = value

    @property
    def _hasPlayer(self):
        """`True` if we have an active media player instance.
        """
        return self._player is not None

    def _assertMediaPlayer(self):
        """Assert that we have a media player instance open.

        This will raise a `RuntimeError` if there is no player open. Use this
        function to ensure that a player is present before running subsequent
        code.
        """
        if self._player is not None:
            return

        raise PlayerNotAvailableError('Media player not initialized.')

    def _enqueueFrame(self, timeout=-1.0):
        """Grab the latest frame from the stream.

        Parameters
        ----------
        timeout : float
            Amount of time to wait for a frame in seconds. If -1.0, this method
            will return immediately. If a frame could not be pulled from the
            stream in the allotted time a warning will be logged.

        Returns
        -------
        bool
            `True` if a frame has been enqueued. Returns `False` if the camera
            is not ready or if the stream was closed.

        """
        self._assertMediaPlayer()

        # todo - if paused, return the last queued frame instead of pulling a new one

        # grab a frame from the camera
        tStart = getTime()
        while 1:  # not frame available
            timedOut = (getTime() - tStart) < timeout
            frame, val = self._player.get_frame()

            if frame is None and timedOut:
                return False

            if val == 'eof':  # end of stream but there is a valid frame
                break

        # img, t = frame
        # scl = SWScale(frame_size[0], frame_size[1], img.get_pixel_format(), ofmt='yuv420p')
        # img2 = scl.scale(img)
        # print(t)
        # tvid += 1 / 30.
        # print(writer.write_frame(img=img2, pts=tvid, stream=0))

    def open(self):
        """Open the webcam stream and begin decoding frames (if available).

        The value of `currentFrame` will be updated as new frames from the
        camera arrive.

        """
        if self._hasPlayer:
            raise RuntimeError('Cannot open `MediaPlayer`, already opened.')

        # open a stream and pause it until ready
        self._player = MediaPlayer(self._camera)
        self._player.set_pause(True)

    def start(self):
        """Start recording frames.
        """
        pass

    def stop(self):
        """Stop recording frames.
        """
        pass

    def close(self):
        """Close the camera.
        """
        pass

    def getVideoFrame(self):
        """Get the current video frame.
        """
        pass


# ------------------------------------------------------------------------------
# Functions
#

def getWebcams():
    """Get information about installed cameras on this system.

    Returns
    -------
    list
        List of camera identifiers.

    """
    systemName = platform.system()  # get the system name
    foundCameras = []
    if systemName == 'Darwin':  # MacOS
        pass
    elif systemName == 'Linux':
        # use glob to get possible cameras connected to the system
        globResult = glob.glob(
            'video*',
            root_dir=VIDEO_DEVICE_ROOT_LINUX,
            recursive=False)
        foundCameras.extend(globResult)
        # ensure the glob gives values in the same order
        foundCameras.sort()
    elif systemName == 'Windows':
        pass
    else:
        raise OSError(
            "Cannot get cameras, unsupported platform '{}'.".format(
                systemName))

    return foundCameras


if __name__ == "__main__":
    pass
