#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
A stimulus class for playing movies (mp4, divx, avi etc...) in PsychoPy.
Demo using the experimental movie3 stim to play a video file. Path of video
needs to updated to point to a video you have. movie2 does /not/ require
avbin to be installed.

Movie3 does require:
~~~~~~~~~~~~~~~~~~~~~

moviepy (which requires imageio, Decorator). These can be installed
(including dependencies) on a standard Python install using
`pip install moviepy`
imageio will download further compiled libs (ffmpeg) as needed

Current known issues:
~~~~~~~~~~~~~~~~~~~~~~

volume control not implemented
movie is long then audio will be huge and currently the whole thing gets
    loaded in one go. We should provide streaming audio from disk.

"""

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, division, print_function

from builtins import str
reportNDroppedFrames = 10

import os

from psychopy import logging, prefs  # adding prefs to be able to check sound lib -JK
from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import logAttrib, setAttribute
from psychopy.tools.filetools import pathToString
from psychopy.visual.basevisual import BaseVisualStim, ContainerMixin, TextureMixin

from moviepy.video.io.VideoFileClip import VideoFileClip

import ctypes
import numpy
from psychopy.clock import Clock
from psychopy.constants import FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED

import pyglet.gl as GL


class MovieStim3(BaseVisualStim, ContainerMixin, TextureMixin):
    """A stimulus class for playing movies.

    This class uses MoviePy and FFMPEG as a backend for loading and decoding
    video data from files.

    Parameters
    ----------
    filename : str
        A string giving the relative or absolute path to the movie.
    flipVert : True or *False*
        If True then the movie will be top-bottom flipped
    flipHoriz : True or *False*
        If True then the movie will be right-left flipped
    volume :
        The nominal level is 100, and 0 is silence.
    loop : bool, optional
        Whether to start the movie over from the beginning if draw is called and
        the movie is done.

    Examples
    --------
    See Movie2Stim.py for demo.

    """
    def __init__(self, win,
                 filename="",
                 units='pix',
                 size=None,
                 pos=(0.0, 0.0),
                 ori=0.0,
                 flipVert=False,
                 flipHoriz=False,
                 color=(1.0, 1.0, 1.0),
                 colorSpace='rgb',
                 opacity=1.0,
                 volume=1.0,
                 name='',
                 loop=False,
                 autoLog=True,
                 depth=0.0,
                 noAudio=False,
                 vframe_callback=None,
                 fps=None,
                 interpolate=True):
        # what local vars are defined (these are the init params) for use
        # by __repr__
        self._initParams = dir()
        self._initParams.remove('self')
        super(MovieStim3, self).__init__(win, units=units, name=name,
                                         autoLog=False)

        retraceRate = win._monitorFrameRate
        if retraceRate is None:
            retraceRate = win.getActualFrameRate()
        if retraceRate is None:
            logging.warning("FrameRate could not be supplied by psychopy; "
                            "defaulting to 60.0")
            retraceRate = 60.0
        self._retraceInterval = 1.0/retraceRate
        self.filename = pathToString(filename)
        self.loop = loop
        self.flipVert = flipVert
        self.flipHoriz = flipHoriz
        self.pos = numpy.asarray(pos, float)
        self.depth = depth
        self.opacity = opacity
        self.noAudio = noAudio
        self._audioStream = None
        self._videoFrameBufferSize = None  # size of the video buffer in bytes
        self._audioTrack = None

        if noAudio:  # to avoid dependency problems in silent movies
            self.sound = None
        else:
            from psychopy import sound
            self.sound = sound

        # interpolation
        self._interpolate = None  # defined here, set in property
        self._texFilterNeedsUpdate = None
        self.interpolate = interpolate

        # set autoLog (now that params have been initialised)
        self.autoLog = autoLog
        if autoLog:
            logging.exp("Created %s = %s" % (self.name, str(self)))

        self._videoClock = Clock()
        self._pixBuffId = GL.GLuint(0)
        self._texID = GL.GLuint(0)
        self.loadMovie(self.filename)
        self.setVolume(volume)
        self.nDroppedFrames = 0

        # size
        if size is None:
            self.size = numpy.array([self._mov.w, self._mov.h],
                                    float)
        else:
            self.size = val2array(size)
        self.ori = ori
        self._setupTextureBuffers()
        self._updateVertices()

    @property
    def interpolate(self):
        """Enable linear interpolation (`bool').

        If `True` linear filtering will be applied to the video making the image
        less pixelated if scaled.

        """
        return self._interpolate

    @interpolate.setter
    def interpolate(self, value):
        self._interpolate = value
        self._texFilterNeedsUpdate = True

    def reset(self):
        self._numpyFrame = None
        self._nextFrameT = None
        self._pixBuffId = GL.GLuint(0)
        self._texID = GL.GLuint(0)
        self.status = NOT_STARTED

    def setMovie(self, filename, log=True):
        """See `~MovieStim.loadMovie` (the functions are identical).

        This form is provided for syntactic consistency with other visual
        stimuli.
        """
        self.loadMovie(filename, log=log)

    def loadMovie(self, filename, log=True):
        """Load a movie from file

        :Parameters:

            filename: string
                The name of the file, including path if necessary

        After the file is loaded MovieStim.duration is updated with the movie
        duration (in seconds).
        """
        filename = pathToString(filename)
        self.reset()  # set status and timestamps etc

        # Create Video Stream stuff
        if os.path.isfile(filename):
            self._mov = VideoFileClip(
                filename,
                audio=(1 - self.noAudio),
                fps_source='fps')  # actual FPS from file metadata

            if (not self.noAudio) and (self._mov.audio is not None):
                sound = self.sound
                try:
                    self._audioStream = sound.Sound(
                        self._mov.audio.to_soundarray(),
                        sampleRate=self._mov.audio.fps)
                except:
                    # JWE added this as a patch for a moviepy oddity where the
                    # duration is inflated in the saved file causes the
                    # audioclip to be the wrong length, so round down and it
                    # should work
                    jwe_tmp = self._mov.subclip(0, round(self._mov.duration))
                    self._audioStream = sound.Sound(
                        jwe_tmp.audio.to_soundarray(),
                        sampleRate=self._mov.audio.fps)
                    del jwe_tmp
                    pass
            else:  # make sure we set to None (in case prev clip had audio)
                self._audioStream = None
        else:
            raise IOError("Movie file '%s' was not found" % filename)
        # mov has attributes:
            # size, duration, fps
        # mov.audio has attributes
            # duration, fps (aka sampleRate), to_soundarray()
        self._frameInterval = 1.0 / self._mov.fps
        self.duration = self._mov.duration
        self.filename = filename

        self._setupTextureBuffers()  # create appropriate buffers
        self._updateFrameTexture()
        logAttrib(self, log, 'movie', filename)

    def play(self, log=True):
        """Continue a paused movie from current position.
        """
        status = self.status
        if status != PLAYING:
            self.status = PLAYING  # moved this to get better audio behavior - JK
            # Added extra check to prevent audio doubling - JK
            if self._audioStream is not None and self._audioStream.status is not PLAYING: 
                self._audioStream.play()
            if status == PAUSED:
                if self.getCurrentFrameTime() < 0:  # Check for valid timestamp, correct if needed -JK
                    self._audioSeek(0)
                else:
                    self._audioSeek(self.getCurrentFrameTime())
            self._videoClock.reset(-self.getCurrentFrameTime())
            if log and self.autoLog:
                self.win.logOnFlip("Set %s playing" % (self.name),
                                   level=logging.EXP, obj=self)
            self._updateFrameTexture()

    def pause(self, log=True):
        """
        Pause the current point in the movie (sound will stop, current frame
        will not advance).  If play() is called again both will restart.
        """
        if self.status == PLAYING:
            self.status = PAUSED
            if self._audioStream:
                if prefs.hardware['audioLib'] == ['sounddevice']:
                    self._audioStream.pause()  # sounddevice has a "pause" function -JK
                else:
                    self._audioStream.stop()
            if log and self.autoLog:
                self.win.logOnFlip("Set %s paused" %
                                   (self.name), level=logging.EXP, obj=self)
            return True
        if log and self.autoLog:
            self.win.logOnFlip("Failed Set %s paused" %
                               (self.name), level=logging.EXP, obj=self)
        return False

    def stop(self, log=True):
        """Stop the current point in the movie (sound will stop, current frame
        will not advance). Once stopped the movie cannot be restarted -
        it must be loaded again. Use pause() if you may need to restart
        the movie.
        """
        if self.status != STOPPED:
            self._unload()
            self.reset()
            self.status = STOPPED # set status to STOPPED after _unload
            if log and self.autoLog:
                self.win.logOnFlip("Set %s stopped" % (self.name),
                                   level=logging.EXP, obj=self)

    def setVolume(self, volume):
        pass  # to do

    def setFlipHoriz(self, newVal=True, log=True):
        """If set to True then the movie will be flipped horizontally
        (left-to-right). Note that this is relative to the original,
        not relative to the current state.
        """
        self.flipHoriz = newVal
        logAttrib(self, log, 'flipHoriz')
        self._needVertexUpdate = True

    def setFlipVert(self, newVal=True, log=True):
        """If set to True then the movie will be flipped vertically
        (top-to-bottom). Note that this is relative to the original,
        not relative to the current state.
        """
        self.flipVert = newVal
        logAttrib(self, log, 'flipVert')
        self._needVertexUpdate = True

    def getFPS(self):
        """Get the movie frames per second.

        Returns
        -------
        float
            Frames per second.

        """
        return float(self._mov.fps)

    def getCurrentFrameTime(self):
        """Get the time that the movie file specified the current
        video frame as having.
        """
        return self._nextFrameT - self._frameInterval

    def _setupTextureBuffers(self):
        """Setup texture buffers which hold frame data. This creates a 2D
        RGB texture and pixel buffer. The pixel buffer serves as the store for
        texture color data. Each frame, the pixel buffer memory is mapped and
        frame data is copied over to the GPU from the decoder.

        This is called everytime a video file is loaded, destroying any pixel
        buffers or textures previously in use.

        """
        # delete buffers and textures if previously created
        if self._pixBuffId.value > 0:
            GL.glDeleteBuffers(1, self._pixBuffId)

        # Calculate the total size of the pixel store in bytes needed to hold a
        # single video frame. This value is reused during the pixel upload
        # process. Assumes RGB color format.
        self._videoFrameBufferSize = \
            self._mov.w * self._mov.h * 3 * ctypes.sizeof(GL.GLubyte)

        # Create the pixel buffer object which will serve as the texture memory
        # store. Pixel data will be copied to this buffer each frame.
        GL.glGenBuffers(1, ctypes.byref(self._pixBuffId))
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._pixBuffId)
        GL.glBufferData(
            GL.GL_PIXEL_UNPACK_BUFFER,
            self._videoFrameBufferSize,
            None,
            GL.GL_STREAM_DRAW)  # one-way app -> GL
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)

        # delete the old texture if present
        if self._texID.value > 0:
            GL.glDeleteTextures(1, self._texID)

        # Create a texture which will hold the data streamed to the pixel
        # buffer. Only one texture needs to be allocated.
        GL.glGenTextures(1, ctypes.byref(self._texID))
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGB8,
            self._mov.w, self._mov.h,  # frame width and height in pixels
            0,
            GL.GL_RGB,
            GL.GL_UNSIGNED_BYTE,
            None)
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)

        if self.interpolate:
            texFilter = GL.GL_LINEAR
        else:
            texFilter = GL.GL_NEAREST

        GL.glTexParameteri(
            GL.GL_TEXTURE_2D,
            GL.GL_TEXTURE_MAG_FILTER,
            texFilter)
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D,
            GL.GL_TEXTURE_MIN_FILTER,
            texFilter)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)

    def _updateFrameTexture(self):
        """Update texture pixel store to contain the present frame. Decoded
        frame image samples are streamed to the texture buffer.

        """
        if self._nextFrameT is None or self._nextFrameT < 0:
            # movie has no current position (or invalid position -JK), 
            # need to reset the clock to zero in order to have the 
            # timing logic work otherwise the video stream would skip 
            # frames until the time since creating the movie object has passed
            self._videoClock.reset()
            self._nextFrameT = 0.0

        # only advance if next frame (half of next retrace rate)
        if self._nextFrameT > self.duration:
            self._onEos()
        elif self._numpyFrame is not None:
            if self._nextFrameT > (self._videoClock.getTime() -
                                   self._retraceInterval/2.0):
                return None
        try:
            self._numpyFrame = self._mov.get_frame(self._nextFrameT)
        except OSError:
            if self.autoLog:
                logging.warning(
                    "Frame {} not found, moving one frame and trying "
                    "again".format(self._nextFrameT), obj=self)
            self._nextFrameT += self._frameInterval
            self._updateFrameTexture()

        if self._texID is None:  # no nothing until we have a texture
            return

        # Copy frame pixel data retrieved from the video decoder this frame.
        # Here we use "texture streaming" which permits the efficient transfer
        # of video data to the GPU by mapping the texture memory store to client
        # (CPU) memory space.

        # bind pixel unpack buffer
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, self._pixBuffId)

        # Free last storage buffer before mapping and writing new frame data.
        # This allows the GPU to process the extant buffer in VRAM uploaded last
        # cycle without being stalled by the CPU accessing it.
        GL.glBufferData(
            GL.GL_PIXEL_UNPACK_BUFFER,
            self._videoFrameBufferSize,
            None,
            GL.GL_STREAM_DRAW)

        # Map the buffer to client memory, `GL_WRITE_ONLY` to tell the driver to
        # optimize for a one-way copy operation. This returns a pointer which
        # we can encapsulate with a numpy array for easy access.
        bufferPtr = GL.glMapBuffer(GL.GL_PIXEL_UNPACK_BUFFER, GL.GL_WRITE_ONLY)

        # upload pixel data by copying
        numpy.copyto(
            numpy.ctypeslib.as_array(
                ctypes.cast(bufferPtr, ctypes.POINTER(GL.GLubyte)),
                shape=self._numpyFrame.shape),
            self._numpyFrame,
            casting='no')

        # Very important that we unmap the buffer data after copying, but keep
        # the buffer bound for setting the texture.
        GL.glUnmapBuffer(GL.GL_PIXEL_UNPACK_BUFFER)

        # bind the texture in openGL
        GL.glEnable(GL.GL_TEXTURE_2D)

        # copy the PBO to the texture
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        GL.glTexSubImage2D(
            GL.GL_TEXTURE_2D, 0, 0, 0,
            self._numpyFrame.shape[1],
            self._numpyFrame.shape[0],
            GL.GL_RGB,
            GL.GL_UNSIGNED_BYTE,
            0)  # point to the presently bound buffer

        # update texture filtering if needed
        if self._texFilterNeedsUpdate:
            if self.interpolate:
                texFilter = GL.GL_LINEAR
            else:
                texFilter = GL.GL_NEAREST

            GL.glTexParameteri(
                GL.GL_TEXTURE_2D,
                GL.GL_TEXTURE_MAG_FILTER,
                texFilter)
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D,
                GL.GL_TEXTURE_MIN_FILTER,
                texFilter)

            self._texFilterNeedsUpdate = False

        # important to unbind the PBO
        GL.glBindBuffer(GL.GL_PIXEL_UNPACK_BUFFER, 0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glDisable(GL.GL_TEXTURE_2D)

        if self.status == PLAYING:
            self._nextFrameT += self._frameInterval

    def draw(self, win=None):
        """Draw the current frame to a particular visual.Window (or to the
        default win for this object if not specified). The current position in
        the movie will be determined automatically.

        This method should be called on every frame that the movie is meant to
        appear.

        Parameters
        ----------
        win : :class:`~psychopy.visual.Window` or None
            Window the video is being drawn to. If `None`, the window specified
            by property `win` will be used. Default is `None`.

        """
        if (self.status == NOT_STARTED or
                (self.status == FINISHED and self.loop)):
            self.play()
        elif self.status == FINISHED and not self.loop:
            return
        if win is None:
            win = self.win
        self._selectWindow(win)
        self._updateFrameTexture()  # will check if it's needed

        # scale the drawing frame and get to centre of field
        GL.glPushMatrix()  # push before drawing, pop after
        # push the data for client attributes
        GL.glPushClientAttrib(GL.GL_CLIENT_ALL_ATTRIB_BITS)

        self.win.setScale('pix')
        # move to centre of stimulus and rotate
        vertsPix = self.verticesPix

        # bind textures
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)

        # sets opacity (1,1,1 = RGB placeholder)
        GL.glColor4f(1, 1, 1, self.opacity)

        # Why do this every frame? Only when `verticesPix` is updated :/
        array = (GL.GLfloat * 32)(
            1, 1,  # texture coords
            vertsPix[0, 0], vertsPix[0, 1], 0.,  # vertex
            0, 1,
            vertsPix[1, 0], vertsPix[1, 1], 0.,
            0, 0,
            vertsPix[2, 0], vertsPix[2, 1], 0.,
            1, 0,
            vertsPix[3, 0], vertsPix[3, 1], 0.,
        )

        # 2D texture array, 3D vertex array
        GL.glInterleavedArrays(GL.GL_T2F_V3F, 0, array)
        GL.glDrawArrays(GL.GL_QUADS, 0, 4)
        GL.glPopClientAttrib()
        GL.glPopMatrix()
        # unbind the textures
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glEnable(GL.GL_TEXTURE_2D)  # implicitly disables 1D

    def seek(self, t):
        """Go to a specific point in time for both the audio and video streams
        """
        # video is easy: set both times to zero and update the frame texture
        self._nextFrameT = t
        self._videoClock.reset(t)
        self._audioSeek(t)

    def _audioSeek(self, t):
        sound = self.sound
        if self._audioStream is None:
            return  # do nothing
        # Check if sounddevice  is being used. If so we can use seek. If not we
        # have to reload the audio stream and begin at the new loc.
        if prefs.hardware['audioLib'] == ['sounddevice']:
            self._audioStream.seek(t)
        else:
            self._audioStream.stop()
            sndArray = self._mov.audio.to_soundarray()
            startIndex = int(t * self._mov.audio.fps)
            self._audioStream = sound.Sound(
                sndArray[startIndex:, :], sampleRate=self._mov.audio.fps)
            if self.status != PAUSED: #Allows for seeking while paused - JK
                self._audioStream.play()

    def _getAudioStreamTime(self):
        return self._audio_stream_clock.getTime()

    def _unload(self):
        # remove textures from graphics card to prevent crash
        self.clearTextures()
        if self._mov is not None:
            self._mov.close()
        self._mov = None
        self._numpyFrame = None
        if self._audioStream is not None:
            self._audioStream.stop()
        self._audioStream = None
        self.status = FINISHED

    def _onEos(self):
        if self.loop:
            self.seek(0.0)
        else:
            self.status = FINISHED
            self.stop()

        if self.autoLog:
            self.win.logOnFlip("Set %s finished" % self.name,
                               level=logging.EXP, obj=self)

    def __del__(self):
        try:
            self._unload()
        except (ImportError, ModuleNotFoundError, TypeError):
            pass  # has probably been garbage-collected already

    def setAutoDraw(self, val, log=None):
        """Add or remove a stimulus from the list of stimuli that will be
        automatically drawn on each flip

        :parameters:
            - val: True/False
                True to add the stimulus to the draw list, False to remove it
        """
        if val:
            self.play(log=False)  # set to play in case stopped
        else:
            self.pause(log=False)
        # add to drawing list and update status
        setAttribute(self, 'autoDraw', val, log)
