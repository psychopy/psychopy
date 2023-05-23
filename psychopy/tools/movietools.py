#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for working with movies in PsychoPy.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'MovieFileWriter',
    'closeAllMovieWriters',
    'addAudioToMovie'
]

import time
import threading
import queue
import atexit
import numpy as np
import psychopy.logging as logging


# keep track of open movie writers
_openMovieWriters = set()


class MovieFileWriter:
    """Create movies from a sequence of images.

    This class allows for the creation of movies from a sequence of images using
    FFMPEG (via the `ffpyplayer` library). Writing movies to disk is a slow 
    process, so this class uses a separate thread to write the movie in the 
    background. This means that you can continue to add images to the movie 
    while frames are still being written to disk. Movie writers are closed 
    automatically when the main thread exits. Any remaining frames are flushed 
    to the file before the file is finalized.

    This does not support writing audio tracks. If you need to add audio to your 
    movie, create the movie first, then add the audio track to the file.

    Parameters
    ----------
    filename : str
        The name (or path) of the file to write the movie to. The file extension
        determines the movie format.
    size : tuple
        The size of the movie in pixels (width, height).
    fps : float
        The number of frames per second.
    codec : str or None
        The codec to use for encoding the movie. The default codec is
        'mpeg4' for .mp4 files and 'libx264' for .avi files. If `None`, the 
        codec will be automatically selected based on the file extension.
    pixelFormat : str
        Pixel format for frames being added to the movie. This should be 
        either 'rgb24' or 'rgba32'. The default is 'rgb24'. When passing frames
        to `addFrame()` as a numpy array, the array should be in the format
        specified here.
    syncBarrier : threading.Barrier or None
        A `threading.Barrier` object used to synchronize the movie writer with
        other threads.
    
    """
    # supported pixel formats as constants
    PIXEL_FORMAT_RGB24 = 'rgb24'
    PIXEL_FORMAT_RGBA32 = 'rgb32'

    def __init__(self, filename, size, fps, codec=None, pixelFormat='rgb24',
                 syncBarrier=None):
        # video file options
        self._filename = filename
        self._size = size
        self._fps = fps
        self._codec = codec
        self._pts = 0.0  # most recent presentation timestamp
        self._pixelFormat = pixelFormat
        self._syncBarrier = syncBarrier
        self._dataLock = threading.Lock()  # lock for accessing shared data

        # objects needed to build up the asynchronous movie writer interface
        self._writerThread = None  # thread for writing the movie file
        self._frameQueue = queue.Queue()  # queue for frames to be written

        # frame interval in seconds
        self._frameInterval = 1.0 / self._fps

        # keep track of the number of bytes we saved to the movie file
        self._bytesOut = 0

    def __hash__(self):
        """Use the filename as the hash value since we only allow one instance
        per file.
        """
        return hash(self._filename)
    
    @property
    def bytesOut(self):
        """Total number of bytes saved to the movie file (`int`).
        """
        with self._dataLock:
            return self._bytesOut
        
    def open(self):
        """Open the movie file for writing.

        This creates a new thread that will write the movie file to disk in
        the background.

        After calling this method, you can add frames to the movie using
        `addFrame()`. When you are done adding frames, call `close()` to
        finalize the movie file.

        """
        # import in the class too avoid hard dependency on ffpyplayer
        from ffpyplayer.writer import MediaWriter

        # register ourselves as an open movie writer
        global _openMovieWriters
        # check if we already have a movie writer for this file
        if self in _openMovieWriters:
            raise ValueError(
                'A movie writer is already open for file {}'.format(
                    self._filename))

        def writeFramesAsync(filename, writerOptions, frameQueue, readyBarrier,
                             dataLock):
            """Local function used to write frames to the movie file.

            This is executed in a thread to allow the main thread to continue
            adding frames to the movie while the movie is being written to
            disk.

            Parameters
            ----------
            filename : str
                Path of the movie file to write.
            writerOptions : dict
                Options to configure the movie writer.
            frameQueue : queue.Queue
                A queue containing the frames to write to the movie file.
                Pushing `None` to the queue will cause the thread to exit.
            readyBarrier : threading.Barrier or None
                A `threading.Barrier` object used to synchronize the movie
                writer with other threads. This guarantees that the movie writer
                is ready before frames are passed te the queue. If `None`, 
                no synchronization is performed.
            dataLock : threading.Lock
                A lock used to synchronize access to the movie writer object for
                accessing variables.

            """
            from ffpyplayer.pic import SWScale

            # create the movie writer, don't manipulate this object while the 
            # movie is being written to disk
            writer = MediaWriter(filename, [writerOptions])

            # wait on a barrier
            if readyBarrier is not None:
                readyBarrier.wait()

            while True:
                frame = frameQueue.get()  # waited on until a frame is added
                if frame is None:
                    break

                # get the frame data
                colorData, pts = frame
                
                # do color conversion
                frameWidth, frameHeight = colorData.get_size()
                sws = SWScale(
                    frameWidth, frameHeight,
                    colorData.get_pixel_format(),
                    ofmt='yuv420p')

                # write the frame to the file
                bytesOut = writer.write_frame(
                    img=sws.scale(colorData),
                    pts=pts,
                    stream=0)
                
                # update the number of bytes saved
                with dataLock:
                    self._bytesOut += bytesOut

            writer.close()

        # options to configure the writer
        frameWidth, frameHeight = self.size
        writerOptions = {
            'pix_fmt_in': 'yuv420p',  # default for now using mp4
            # 'preset': 'medium',
            'width_in': frameWidth,
            'height_in': frameHeight,
            'codec': self._codec,
            'frame_rate': (self._fps, 1)
        }

        # reset the number of bytes saved
        self._bytesOut = 0

        # initialize the thread, the thread will wait on frames to be added to 
        # the queue
        self._writerThread = threading.Thread(
            target=writeFramesAsync,
            args=(self._filename, 
                  writerOptions, 
                  self._frameQueue,
                  self._syncBarrier,
                  self._dataLock))
        
        self._writerThread.start()
        
        # add to the list of open movie writers
        _openMovieWriters.add(self)
        
    @property
    def filename(self):
        """The name (path) of the movie file (`str`).
        """
        return self._filename
    
    @property
    def size(self):
        """The size of the movie in pixels (`tuple`). This is a tuple of the
        form (width, height).
        """
        return self._size
    
    @property
    def fps(self):
        """Output frames per second (`float`).
        """
        return self._fps
    
    @property
    def codec(self):
        """Codec used to encode the movie (`str`). This is `None`, if the codec
        was automatically selected based on the file extension.
        """
        return self._codec
    
    @property
    def pixelFormat(self):
        """Pixel format for frames being added to the movie (`str`).
        """
        return self._pixelFormat
    
    @property
    def isOpen(self):
        """Whether the movie file is open (`bool`).
        """
        if self._writerThread is None:
            return False
        
        return self._writerThread.is_alive()
    
    def flush(self):
        """Flush the movie file.

        This will cause all frames waiting in the queue to be written to disk
        before continuing the program. This is useful for ensuring that all
        frames are written to disk before the program exits. However, it will
        block the program until all frames are written.

        """
        # check if the writer thread present and is alive
        if self._writerThread is None:
            return
        elif not self._writerThread.is_alive():
            return

        # block until the queue is empty
        nWaiting = self.framesWaiting
        while not self._frameQueue.empty():
            # simple check to see if the queue size is decreasing monotonically
            nWaitingNew = self.framesWaiting
            if nWaitingNew > nWaiting:
                logging.warn(
                    "Queue length not decreasing monotonically during "
                    "`flush()`. This may indicate that frames are still being "
                    "added ({} -> {}).".format(
                        nWaiting, nWaitingNew)
                )
            nWaiting = nWaitingNew
            time.sleep(0.001)  # sleep for 1 ms

    def close(self):
        """Close the movie file.

        This shuts down the background thread and finalizes the movie file. Any
        frames still waiting in the queue will be written to disk before the
        movie file is closed. This will block the program until all frames are
        written, therefore, it is recommended for `close()` to be called outside
        any time-critical code.

        """
        if self._writerThread is None:
            return

        # if the writer thread is alive still, then we need to shut it down
        if self._writerThread.is_alive():
            self._frameQueue.put(None)  # signal the thread to exit
            # flush remaining frames, if any
            msg = ("File '{}' still has {} frame(s) queued to be written to "
                   "disk, waiting to complete.")
            nWaiting = self.framesWaiting
            if nWaiting > 0:
                logging.warning(msg.format(self.filename, nWaiting))
                self.flush()

            self._writerThread.join()  # waits until the thread exits

        # unregister ourselves as an open movie writer
        try:
            global _openMovieWriters
            _openMovieWriters.remove(self)
        except AttributeError:
            pass
        
        self._writerThread = None

    @property
    def framesWaiting(self):
        """The number of frames waiting to be written to disk (`int`).
        """
        return self._frameQueue.qsize()

    def addFrame(self, image, pts=None):
        """Add a frame to the movie.

        Parameters
        ----------
        image : numpy.ndarray or ffpyplayer.pic.Image
            The image to add to the movie. The image must be in RGB format and 
            have the same size as the movie. If the image is an `Image` 
            instance, it must have the same size as the movie.
        pts : float or None
            The presentation timestamp for the frame. This is the time at which 
            the frame should be displayed. The presentation timestamp is in 
            seconds and should be monotonically increasing. If `None`, the 
            presentation timestamp will be automatically generated based on the 
            chosen frame rate for the output video. 

        Returns
        -------
        float
            Presentation timestamp assigned to the frame. Should match the value 
            passed in as `pts` if provided.

        """
        if self._writerThread is None:
            raise RuntimeError('Movie file is not open.')
        
        if not self._writerThread.is_alive():  # no thread running yet
            return
        
        # convert the image to a format that `ffpyplayer` can use if needed
        import ffpyplayer.pic as pic
        if isinstance(image, np.ndarray):
            # make sure we are the correct format
            image = np.ascontiguousarray(image, dtype=np.uint8).tobytes()
            colorData = pic.Image(
                plane_buffers=[image], 
                pix_fmt=self._pixelFormat, 
                size=self._size)
        elif isinstance(image, pic.Image):
            # check if the format is valid
            if image.get_pixel_format() != self._pixelFormat:
                raise ValueError('Invalid pixel format for image.')
            colorData = image
        else:
            raise TypeError('Unsupported image type.')
        
        # get computed presentation timestamp if not provided
        pts = self._pts if pts is None else pts
            
        # pass the image data to the writer thread
        self._frameQueue.put((colorData, pts))

        # update the presentation timestamp after adding the frame
        self._pts += self._frameInterval

        return pts

    def __del__(self):
        """Close the movie file when the object is deleted.
        """
        try:
            self.close()
        except AttributeError:
            pass


def closeAllMovieWriters():
    """Signal all movie writers to close.

    This function should only be called once at the end of the program. This can 
    be registered `atexit` to ensure that all movie writers are closed when the 
    program exits. If there are open file writers with frames still queued, this 
    function will block until all frames remaining are written to disk. 

    Use caution when calling this function when file writers are being used in a
    multi-threaded environment. Threads that are writing movie frames must be
    stopped prior to calling this function. If not, the thread may continue to
    write frames to the queue during the flush operation and never exit.

    """
    global _openMovieWriters

    if not _openMovieWriters:  # do nothing if no movie writers are open
        return

    logging.info('Closing all open ({}) movie writers now'.format(
        len(_openMovieWriters)))

    for movieWriter in _openMovieWriters.copy():
        # flush the movie writer, this will block until all frames are written
        movieWriter.close()
        
    _openMovieWriters.clear()  # clear the set to free references


# register the cleanup function to run when the program exits
atexit.register(closeAllMovieWriters)


def addAudioToMovie(outputFile, videoFile, audioFile, useThreads=True):
    """Add an audio track to a video file.

    This function will add an audio track to a video file. If the video file
    already has an audio track, it will be replaced with the audio file
    provided. If no audio file is provided, the audio track will be removed
    from the video file.

    The audio track should be exactly the same length as the video track.

    Parameters
    ----------
    outputFile : str
        Path to the output video file where audio and video will be merged.
    videoFile : str
        Path to the input video file.
    audioFile : str
        Path to the audio file to add to the video file.
    useThreads : bool
        If `True`, the audio will be added in a separate thread. This allows the
        audio to be added in the background while the program continues to run.
        If `False`, the audio will be added in the main thread and the program
        will block until the audio is added. Defaults to `True`.

    Examples
    --------
    Combine a video file and an audio file into a single video file::

        from psychopy.tools.movietools import addAudioToMovie
        addAudioToMovie('output.mp4', 'video.mp4', 'audio.mp3')

    """
    from moviepy.video.io.VideoFileClip import VideoFileClip
    from moviepy.audio.io.AudioFileClip import AudioFileClip
    from moviepy.audio.AudioClip import CompositeAudioClip

    def _renderVideo(outputFile, videoFile, audioFile):
        """Render the video file with the audio track.
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

    logging.info('Adding audio to video file: {}'.format(outputFile))
    
    # run the audio/video merge in the main thread
    if not useThreads:
        _renderVideo(outputFile, videoFile, audioFile)
        return

    # run the audio/video merge in a separate thread
    thread = threading.Thread(
        target=_renderVideo, 
        args=(outputFile, videoFile, audioFile))
    thread.start()


if __name__ == "__main__":
    pass
