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
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2024 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
from pathlib import Path

from psychopy.tools.versiontools import deprecated

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


@deprecated("2023.1.0", replacement="psychopy.visual.MovieStim")
class MovieStim3(BaseVisualStim, ContainerMixin, TextureMixin):
    """A stimulus class for playing movies. This is a lazy-imported class,
    therefore import using full path 
    `from psychopy.visual.movie3 import MovieStim3` when inheriting from it.

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
                 anchor="center",
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
        BaseVisualStim.__init__(
            self, win, units=units, name=name,
            autoLog=False
        )

        retraceRate = win._monitorFrameRate
        # if retraceRate is None:
        #     retraceRate = win.getActualFrameRate()
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
        self.anchor = anchor
        self.depth = depth
        self.opacity = opacity
        self.interpolate = interpolate
        self.noAudio = noAudio
        self._audioStream = None
        self.useTexSubImage2D = True

        if noAudio:  # to avoid dependency problems in silent movies
            self.sound = None
        else:
            from psychopy import sound
            self.sound = sound

        # set autoLog (now that params have been initialised)
        self.autoLog = autoLog
        if autoLog:
            logging.exp("Created %s = %s" % (self.name, str(self)))

        self._videoClock = Clock()
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

    @property
    def duration(self):
        """Duration of the video clip in seconds (`float`). Only valid after
        loading a clip, always returning `0.0` if not.
        """
        if self._mov is None:
            return 0.0

        return self._mov.duration

    @property
    def frameInterval(self):
        """Time in seconds each frame is to be presented on screen (`float`).
        Value is `0.0` if no movie is loaded.
        """
        if self._mov is None:
            return 0.0

        return 1. / self._mov.fps

    def reset(self):
        self._numpyFrame = None
        self._nextFrameT = 0.0
        self._texID = None
        self.status = NOT_STARTED
        self.nDroppedFrames = 0
        
    def setMovie(self, filename, log=True):
        """See `~MovieStim.loadMovie` (the functions are identical).

        This form is provided for syntactic consistency with other visual
        stimuli.

        Parameters
        ----------
        filename : str
            The name of the file, including path if necessary.
        log : bool
            Log this event.

        """
        self.loadMovie(filename, log=log)

    def loadMovie(self, filename, log=True):
        """Load a movie from file.

        After the file is loaded `MovieStim.duration` is updated with the movie
        duration (in seconds).

        Parameters
        ----------
        filename : str
            The name of the file, including path if necessary.
        log : bool
            Log this event.

        """
        filename = pathToString(filename)
        self.reset()  # set status and timestamps etc

        self._mov = None
        # Create Video Stream stuff
        if os.path.isfile(filename):
            self._mov = VideoFileClip(filename, audio=(1 - self.noAudio))
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
                    del(jwe_tmp)
            else:  # make sure we set to None (in case prev clip had audio)
                self._audioStream = None
        elif not filename.startswith(prefs.paths['resources']):
            # If not found, and we aren't already looking in the Resources folder, try again in the Resources folder
            self.loadMovie(Path(prefs.paths['resources']) / filename, log=False)
        else:
            # Raise error if *still* not found
            raise IOError("Movie file '%s' was not found" % filename)
        # mov has attributes:
            # size, duration, fps
        # mov.audio has attributes
            # duration, fps (aka sampleRate), to_soundarray()
        self._frameInterval = 1.0 / self._mov.fps
        # self.duration = self._mov.duration
        self.filename = filename
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
                if prefs.hardware['audioLib'] in ['sounddevice', 'PTB']:
                    self._audioStream.pause()  # sounddevice and PTB have a "pause" function -JK
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
            self.status = STOPPED  # set status to STOPPED after _unload
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
        return self._nextFrameT - self.frameInterval

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

        while self._nextFrameT <= (self._videoClock.getTime() - self._frameInterval*2):
            self.nDroppedFrames += 1
            if self.nDroppedFrames <= reportNDroppedFrames:
                logging.warning("{}: Video catchup needed, advancing self._nextFrameT from"
                                " {} to {}".format(self._videoClock.getTime(), self._nextFrameT,
                                                   self._nextFrameT+self._frameInterval))
            if self.nDroppedFrames == reportNDroppedFrames:
                logging.warning("Max reportNDroppedFrames reached, will not log any more dropped frames")

            self._nextFrameT += self._frameInterval

        try:
            self._numpyFrame = self._mov.get_frame(self._nextFrameT)
        except OSError:
            if self.autoLog:
                logging.warning("Frame {} not found, moving one frame and trying again"
                    .format(self._nextFrameT), obj=self)
            self._nextFrameT += self._frameInterval
            self._updateFrameTexture()
        useSubTex = self.useTexSubImage2D
        if self._texID is None:
            self._texID = GL.GLuint()
            GL.glGenTextures(1, ctypes.byref(self._texID))
            useSubTex = False

        GL.glActiveTexture(GL.GL_TEXTURE0)
        # bind that name to the target
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        # bind the texture in openGL
        GL.glEnable(GL.GL_TEXTURE_2D)
        # makes the texture map wrap (this is actually default anyway)
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP)
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP)
        # data from PIL/numpy is packed, but default for GL is 4 bytes
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)
        # important if using bits++ because GL_LINEAR
        # sometimes extrapolates to pixel vals outside range
        if self.interpolate:
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
            if useSubTex is False:
                GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB8,
                                self._numpyFrame.shape[1],
                                self._numpyFrame.shape[0], 0,
                                GL.GL_RGB, GL.GL_UNSIGNED_BYTE,
                                self._numpyFrame.ctypes)
            else:
                GL.glTexSubImage2D(GL.GL_TEXTURE_2D, 0, 0, 0,
                                   self._numpyFrame.shape[1],
                                   self._numpyFrame.shape[0],
                                   GL.GL_RGB, GL.GL_UNSIGNED_BYTE,
                                   self._numpyFrame.ctypes)
        else:
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
            GL.glTexParameteri(
                GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
            if useSubTex is False:
                GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB8,
                                self._numpyFrame.shape[1],
                                self._numpyFrame.shape[0], 0,
                                GL.GL_BGR, GL.GL_UNSIGNED_BYTE,
                                self._numpyFrame.ctypes)
            else:
                GL.glTexSubImage2D(GL.GL_TEXTURE_2D, 0, 0, 0,
                                   self._numpyFrame.shape[1],
                                   self._numpyFrame.shape[0],
                                   GL.GL_BGR, GL.GL_UNSIGNED_BYTE,
                                   self._numpyFrame.ctypes)
        GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE,
                     GL.GL_MODULATE)  # ?? do we need this - think not!

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
        GL.glActiveTexture(GL.GL_TEXTURE1)
        GL.glBindTexture(GL.GL_TEXTURE_2D, 0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        GL.glEnable(GL.GL_TEXTURE_2D)

        # sets opacity (1,1,1 = RGB placeholder)
        GL.glColor4f(1, 1, 1, self.opacity)

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
        # check if sounddevice or PTB is being used. If so we can use seek. If not we
        # have to reload the audio stream and begin at the new loc
        if prefs.hardware['audioLib'] in ['sounddevice', 'PTB']:
            self._audioStream.seek(t)
        else:
            self._audioStream.stop()
            sndArray = self._mov.audio.to_soundarray()
            startIndex = int(t * self._mov.audio.fps)
            self._audioStream = sound.Sound(
                sndArray[startIndex:, :], sampleRate=self._mov.audio.fps)
            if self.status != PAUSED:  # Allows for seeking while paused - JK
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
        automatically drawn on each flip.

        Parameters
        ----------
        val : bool
            True to add the stimulus to the draw list, False to remove it.

        """
        if val:
            self.play(log=False)  # set to play in case stopped
        else:
            self.pause(log=False)
        # add to drawing list and update status
        setAttribute(self, 'autoDraw', val, log)


if __name__ == "__main__":
    pass
