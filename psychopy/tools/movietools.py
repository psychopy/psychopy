#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""Classes and functions for working with movies in PsychoPy.
"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'MovieFileWriter'
]

import time
import threading
import queue
import numpy as np


class MovieFileWriter:
    """Create movies from a sequence of images.

    This class allows you to create movies from a sequence of images. Writing 
    movies to disk is a slow process, so this class uses a separate thread to
    write the movie in the background. This means that you can continue to
    add images to the movie while it is being written to disk.

    This does not support audio tracks. If you need to add audio to your movie,
    create the movie first, then add the audio track to the file.

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
    
    """
    def __init__(self, filename, size, fps, codec=None):
        # video file options
        self._filename = filename
        self._size = size
        self._fps = fps
        self._codec = codec
        self._pts = 0.0  # most recent presentation timestamp

        # objects needed to build up the asynchronous movie writer interface
        self._writer = None  # handle for the movie writer
        self._writerThread = None  # thread for writing the movie file
        self._frameQueue = queue.Queue()  # queue for frames to be written

        # frame interval in seconds
        self._frameInterval = 1.0 / self._fps

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

        def writeFramesAsync(writer, frameQueue):
            """Local function used to write frames to the movie file.

            This is executed in a thread to allow the main thread to continue
            adding frames to the movie while the movie is being written to
            disk.

            Parameters
            ----------
            writer : MediaWriter
                The movie writer.
            frameQueue : queue.Queue
                A queue containing the frames to write to the movie file.
                Pushing `None` to the queue will cause the thread to exit.

            """
            from ffpyplayer.tools import SWScale

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
                    ofmt='yuv420p'
                )

                # write the frame to the file
                recordingBytes = writer.write_frame(
                    img=sws.scale(colorData),
                    pts=pts,
                    stream=0
                )

            writer.close()

        # options to configure the writer
        frameWidth, frameHeight = self.size
        writerOptions = {
            'pix_fmt_in': 'yuv420p',  # default for now using mp4
            # 'preset': 'medium',
            'width_in': frameWidth,
            'height_in': frameHeight,
            'codec': self._codec,
            'frame_rate': self._frameRate
        }

        # create the movie writer, don't manipulate this object while the 
        # movie is being written to disk
        self._writer = MediaWriter(self._filename, writerOptions)

        # initialize the thread, the thread will wait on frames to be added to 
        # the queue
        self._writerThread = threading.Thread(
            target=writeFramesAsync,
            args=(self._writer, self._frameQueue))
        
        self._writerThread.start()
        
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
    def isOpen(self):
        """Whether the movie file is open (`bool`).
        """
        return self._writer is not None

    def close(self):
        """Close the movie file.

        This shuts down the background thread and finalizes the movie file.

        """
        if self._writerThread is None:
            return

        # if the writer thread is alive still, signal it to exit
        if self._writerThread.is_alive():
            self._frameQueue.put(None)
            self._writerThread.join()   # waits until the thread exits
        
        self._writerThread = self._writer = None

    @property
    def framesWaiting(self):
        """The number of frames waiting to be written to disk (`int`).
        """
        return self._frameQueue.qsize()

    def addFrame(self, image, pts):
        """Add a frame to the movie.

        Parameters
        ----------
        image : numpy.ndarray or ffpyplayer.tools.Image
            The image to add to the movie. The image must be in RGB format
            and have the same size as the movie. If the image is an `Image` 
            instance, it must have the same size as the movie.
        pts : float or None
            The presentation timestamp for the frame. This is the time at
            which the frame should be displayed. The presentation timestamp
            is in seconds and should be monotonically increasing. If `None`,
            the presentation timestamp will be automatically generated based
            on the frame rate.

        """
        if self._writerThread is None:
            raise RuntimeError('Movie file is not open.')
        
        if not self._writerThread.is_alive():
            return
        
        # convert the image to a format that `ffpyplayer` can use if needed
        if isinstance(image, np.ndarray):
            from ffpyplayer.tools import Image
            colorData = Image(
                plane_buffers=[image.tobytes()], 
                pix_fmt='rgb24', 
                size=self._size
            )
        elif isinstance(image, Image):
            colorData = image
        else:
            raise TypeError('Unsupported image type.')
        
        # get computed presentation timestamp if not provided
        pts = self._pts if pts is None else pts
            
        # pass the image data to the writer thread
        self._frameQueue.put((colorData, pts))

        # update the presentation timestamp after adding the frame
        self._pts += self._frameInterval

    def __del__(self):
        pass


if __name__ == "__main__":
    pass
