#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for handling and recording camera stream data.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['StreamStatus', 'StreamData', 'StreamWriterThread', 'renderVideo']

import os
import threading
import queue
from psychopy.visual.movies.metadata import MovieMetadata
import psychopy.logging as logging
from psychopy.constants import NOT_STARTED
from ffpyplayer.writer import MediaWriter
from ffpyplayer.pic import SWScale

# Something in moviepy.editor's initialisation breaks Mouse, so import these
# from the source instead
# from moviepy.editor import VideoFileClip, AudioFileClip, CompositeAudioClip
from moviepy.video.io.VideoFileClip import VideoFileClip
from moviepy.audio.io.AudioFileClip import AudioFileClip
from moviepy.audio.AudioClip import CompositeAudioClip


class StreamStatus:
    """Descriptor class for stream status.

    This class is used to report the current status of the stream read/writer.

    Parameters
    ----------
    status : int
        Status flag for the stream.
    streamTime : float
        Current stream time in seconds. This value increases monotonically and
        is common to all webcams attached to the system.
    recTime : float
        If recording, this field will report the current timestamp within the
        output file. Otherwise, this value is zero.
    recBytes : float
        If recording, this value indicates the number of bytes that have been
        written out to file.

    """
    __slots__ = ['_status',
                 '_streamTime',
                 '_recTime',
                 '_recBytes']

    def __init__(self,
                 status=NOT_STARTED,
                 streamTime=0.0,
                 recTime=0.0,
                 recBytes=0):

        self._status = int(status)
        self._streamTime = float(streamTime)
        self._recTime = float(recTime)
        self._recBytes = int(recBytes)

    @property
    def status(self):
        """Status flag for the stream (`int`).
        """
        return self._status

    @property
    def streamTime(self):
        """Current stream time in seconds (`float`).

        This value increases monotonically and is common timebase for all
        cameras attached to the system.
        """
        return self._streamTime

    @property
    def recBytes(self):
        """Current recording size on disk (`int`).

        If recording, this value indicates the number of bytes that have been
        written out to file.
        """
        return self._recBytes

    @property
    def recTime(self):
        """Current recording time (`float`).

        If recording, this field will report the current timestamp within the
        output file. Otherwise, this value is zero.
        """
        return self._recTime


class StreamData:
    """Descriptor for camera stream data.

    Instances of this class are produced by the stream reader/writer thread
    which contain: metadata about the stream, frame image data (i.e. pixel
    values), and the stream status.

    Parameters
    ----------
    metadata : MovieMetadata
        Stream metadata.
    frameImage : object
        Video frame image data.
    streamStatus : StreamStatus
        Video stream status.
    cameraLib : str
        Camera library in use to process the stream.

    """
    __slots__ = ['_metadata',
                 '_frameImage',
                 '_streamStatus',
                 '_cameraLib']

    def __init__(self, metadata, frameImage, streamStatus, cameraLib):
        self._metadata = metadata
        self._frameImage = frameImage
        self._streamStatus = streamStatus
        self._cameraLib = cameraLib

    @property
    def metadata(self):
        """Stream metadata at the time the video frame was acquired
        (`MovieMetadata`).
        """
        return self._metadata

    @metadata.setter
    def metadata(self, value):
        if not isinstance(value, MovieMetadata) or value is not None:
            raise TypeError("Incorrect type for property `metadata`, expected "
                            "`MovieMetadata` or `None`.")

        self._metadata = value

    @property
    def frameImage(self):
        """Frame image data from the codec (`ffpyplayer.pic.Image`).
        """
        return self._frameImage

    @frameImage.setter
    def frameImage(self, value):
        self._frameImage = value

    @property
    def streamStatus(self):
        """Stream status (`StreamStatus`).
        """
        return self._streamStatus

    @streamStatus.setter
    def streamStatus(self, value):
        if not isinstance(value, StreamStatus) or value is not None:
            raise TypeError("Incorrect type for property `streamStatus`, "
                            "expected `StreamStatus` or `None`.")

        self._streamStatus = value

    @property
    def cameraLib(self):
        """Camera library in use to obtain the stream (`str`). Value is
        blank if `metadata` is `None`.
        """
        if self._metadata is not None:
            return self._metadata.movieLib

        return u''


class StreamWriterThread(threading.Thread):
    """Class for high-performance writing of video frames to disk asynchronously
    using threading.

    This thread is spawned along with a :class:`~psychopy.hardware.Camera`
    instance, providing the capability to save real-time (live) video to disk
    for later viewing or use. Communication and control of the thread are
    done either by calling methods associated with this class, or directly
     putting commands into the command queue, from another thread.

    """
    def __init__(self, mic=None):
        threading.Thread.__init__(self)
        self.daemon = True

        self._mic = mic
        self._commandQueue = queue.Queue()
        self._writerClosedEvent = threading.Event()
        self._writerClosedEvent.clear()

        self._warmUpLock = threading.Lock()

    def run(self):
        """Main loop for the writer thread.

        This waits on commands from the command queue and processes them
        continuously until the `'end'` command is received. This thread may be
        created along with the camera instance and killed when done.

        If the stream format changes at any point, you should close the writer
        and open a new one with updated parameters before writing more frames.

        """
        self._warmUpLock.acquire(blocking=False)
        writer = None   # instance for the writer
        filepath = ''  # path to the file
        alive = True
        while alive:
            # block main thread until we are in the command loop
            if self._warmUpLock.locked():
                self._warmUpLock.release()

            # process input commands
            cmdOptCode, cmdVals = self._commandQueue.get(block=True)
            if cmdOptCode == 'open':
                # Open a file to write values to.
                if writer is not None:
                    raise IOError(
                        "Attempted to start a new `MediaWriter` instance "
                        "without closing the existing one first."
                    )
                filepath, writerOpts = cmdVals
                # create a new writer instance
                writer = MediaWriter(filepath, writerOpts)
                self._commandQueue.task_done()
            elif cmdOptCode == 'write_frame':  # write a frame
                # Write a frame out to the file. Passing a boolean as arg[3]
                # will tell the code whether to block until the frame has
                # been written (or buffered and waiting) by the writer. Use
                # `True` for synchronous operation and `False` for
                # asynchronous.
                if writer is None:
                    raise IOError(
                        'Got `write_frame` command but the writer has not '
                        'been opened yet.')

                colorData, pts, blockUntilDone = cmdVals
                if not blockUntilDone:
                    self._commandQueue.task_done()

                frameWidth, frameHeight = colorData.get_size()
                sws = SWScale(frameWidth, frameHeight,
                    colorData.get_pixel_format(),
                    ofmt='yuv420p')

                # write the frame to the file
                recordingBytes = writer.write_frame(
                    img=sws.scale(colorData),
                    pts=pts,
                    stream=0)

                logging.debug(
                    'Writing {} bytes to file `{}`'.format(
                        recordingBytes, filepath)
                )

                if blockUntilDone:
                    self._commandQueue.task_done()
            elif cmdOptCode == 'close':
                # Close the file we are writing to but keep the writer
                # thread hot. This allows for successive recordings to be
                # made as quickly as possible without needing to spawn
                # another thread each time.
                if writer is None:
                    raise IOError(
                        "Attempted to close the `MediaWriter` instance "
                        "without opening on first.")
                writer.close()
                writer = None
                self._commandQueue.task_done()
            elif cmdOptCode == 'end':  # end the thread
                alive = False
                continue

        # if we have an open file, close it just in case
        if writer is not None:
            writer.close()

        # set when the writer exits
        self._commandQueue.task_done()  # when end is called

        logging.debug('Media writer thread has been killed.')

    @property
    def commandQueue(self):
        """The command queue for this thread (`queue.Queue`).
        """
        return self._commandQueue

    def begin(self):
        """Begin the file writer thread. Blocks until we can start accepting
        commands.
        """
        self.start()
        self._warmUpLock.acquire(blocking=True)

    def end(self):
        """Shutdown the thread.
        """
        self.sendCommand('end', (None,))  # blocks until done

    def open(self, filePath, writerOpts):
        """Open a file to writer frames to.

        Parameters
        ----------
        filePath : str
            Path to file to write frames to. This is usually a temporary
            directory.
        writerOpts : dict
            Optional settings for the writer.

        """
        self.sendCommand('open', (filePath, writerOpts))  # blocks until done

    def writeFrame(self, colorData, pts, blockUntilDone=False):
        """Write a frame to the presently opened file.

        Parameters
        ----------
        colorData : object
            Image data to pass to the encoder.
        pts : float
            Presentation time stamp for the frame.
        blockUntilDone : bool
            Block this function until the frame has been written to disk.
            Otherwise, this function will return immediately and the frame will
            be written out asynchronously.

        """
        self.sendCommand('write_frame', (colorData, pts, blockUntilDone))

    def close(self):
        """Close the file. This will write out the result.
        """
        self.sendCommand('close', (None,))

    def sendCommand(self, opcode, args):
        """Send a command to this thread.

        Parameters
        ----------
        opcode : str
            Command key or operation code.
        args : tuple
            Arguments for the command.

        """
        self._commandQueue.put((opcode, args))
        self._commandQueue.join()  # block until tasks are done


def renderVideo(outputFile, videoFile, audioFile=None):
    """Render a video.

    Combine visual and audio streams into a single movie file. This is used
    mainly for compositing video and audio data for the camera. Video and audio
    should have roughly the same duration.

    Parameters
    ----------
    outputFile : str
        Filename to write the movie to. Should have the extension of the file
        too.
    videoFile : str
        Video file path.
    audioFile : str or None
        Audio file path. If not provided the movie file will simply be copied
        to `outFile`.

    Returns
    -------
    int
        Size of the resulting file in bytes.

    """
    # merge audio and video tracks, we use MoviePy for this
    videoClip = VideoFileClip(videoFile)

    # if we have a microphone, merge the audio track in
    if audioFile is not None:
        audioClip = AudioFileClip(audioFile)
        # add audio track to the video
        videoClip.audio = CompositeAudioClip([audioClip])

    # transcode with the format the user wants
    videoClip.write_videofile(outputFile, verbose=False, logger=None)

    return os.path.getsize(outputFile)


if __name__ == "__main__":
    pass
