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
# Copyright (C) 2018 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from __future__ import absolute_import, division, print_function

from builtins import str
reportNDroppedFrames = 10

import os

from psychopy import logging, prefs #adding prefs to be able to check sound lib -JK
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
    """A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy
    that does not require avbin. Instead it requires the cv2 python package
    for OpenCV. The VLC media player also needs to be installed on the
    psychopy computer.

    **Example**::

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
        """
        :Parameters:

            filename :
                a string giving the relative or absolute path to the movie.
            flipVert : True or *False*
                If True then the movie will be top-bottom flipped
            flipHoriz : True or *False*
                If True then the movie will be right-left flipped
            volume :
                The nominal level is 100, and 0 is silence.
            loop : bool, optional
                Whether to start the movie over from the beginning if draw is
                called and the movie is done.

        """
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
        self.opacity = float(opacity)
        self.interpolate = interpolate
        self.noAudio = noAudio
        self._audioStream = None
        self.useTexSubImage2D = True

        if noAudio:  # to avoid dependency problems in silent movies
            self.sound = None
        else:
            from psychopy import sound
            self.sound = sound

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
        # set autoLog (now that params have been initialised)
        self.autoLog = autoLog
        if autoLog:
            logging.exp("Created %s = %s" % (self.name, str(self)))

    def reset(self):
        self._numpyFrame = None
        self._nextFrameT = None
        self._texID = None
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
        else:
            raise IOError("Movie file '%s' was not found" % filename)
        # mov has attributes:
            # size, duration, fps
        # mov.audio has attributes
            # duration, fps (aka sampleRate), to_soundarray()
        self._frameInterval = 1.0/self._mov.fps
        self.duration = self._mov.duration
        self.filename = filename
        self._updateFrameTexture()
        logAttrib(self, log, 'movie', filename)

    def play(self, log=True):
        """Continue a paused movie from current position.
        """
        status = self.status
        if status != PLAYING:
            self.status = PLAYING #moved this to get better audio behavior - JK
            #Added extra check to prevent audio doubling - JK
            if self._audioStream is not None and self._audioStream.status is not PLAYING: 
                self._audioStream.play()
            if status == PAUSED:
                if self.getCurrentFrameTime() < 0: #Check for valid timestamp, correct if needed -JK
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
                    self._audioStream.pause() #sounddevice has a "pause" function -JK
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
        """
        Returns the movie frames per second playback speed.
        """
        return self._mov.fps

    def getCurrentFrameTime(self):
        """Get the time that the movie file specified the current
        video frame as having.
        """
        return self._nextFrameT - self._frameInterval

    def _updateFrameTexture(self):
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
                logging.warning("Frame {} not found, moving one frame and trying again" 
                    .format(self._nextFrameT), obj=self)
            self._nextFrameT += self._frameInterval
            self._updateFrameTexture()
        useSubTex = self.useTexSubImage2D
        if self._texID is None:
            self._texID = GL.GLuint()
            GL.glGenTextures(1, ctypes.byref(self._texID))
            useSubTex = False

        # bind the texture in openGL
        GL.glEnable(GL.GL_TEXTURE_2D)
        # bind that name to the target
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        # makes the texture map wrap (this is actually default anyway)
        GL.glTexParameteri(
            GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_REPEAT)
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
        default win for this object if not specified). The current
        position in the movie will be determined automatically.

        This method should be called on every frame that the movie is
        meant to appear.
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
        #check if sounddevice  is being used. If so we can use seek. If not we have to 
        #reload the audio stream and begin at the new loc
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
        self._unload()

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
