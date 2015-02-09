#!/usr/bin/env python2
'''
A stimulus class for playing movies (mpeg, avi, etc...) in PsychoPy.
Demo using the experimental movie2 stim to play a video file. Path of video
needs to updated to point to a video you have. movie2 does /not/ require
avbin to be installed.

Movie2 does require:
~~~~~~~~~~~~~~~~~~~~~

1. Python OpenCV package (so openCV libs and the cv2 python interface).
    *. For Windows, a binary installer is available at http://www.lfd.uci.edu/~gohlke/pythonlibs/#opencv
    *. For Linux, it is available via whatever package manager you use.
    *. For OSX, ..... ?
2. VLC application. Just install the standard VLC (32bit) for your OS. http://www.videolan.org/vlc/index.html

To play a video, you /must/:
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

a. Create a visual.MovieStim2(..) instance; pretend it is called mov.
b. Call mov.play() when you want to start playing the video.
c. Call win.flip(), which will display the first frame of the video.
d. In the experiment loop, call mov.draw() followed by win.flip() to draw
   the video frame again mov.draw() determines if the current frame,
   or the next frame should be redrawn and does so accordingly. If the next
   frame is drawn, mov.draw() will return the frame index just drawn. If
   the same frame is drawn as before, None is returned.

This method call sequence must be followed. This should be improved (I think)
depending on how movie stim calls are actually made. The current movie stim
code doc's seem a bit mixed in message.

Current known issues:
~~~~~~~~~~~~~~~~~~~~~~

1. Loop functionality are known to be broken at this time.
2. Auto draw not implemented.
3. Video must have 3 color channels.
4. Intentional Frame dropping (to keep video playing at expected rate on slow machines) is not yet implemented.

What does work so far:
~~~~~~~~~~~~~~~~~~~~~~~~~

1. mov.setMovie(filename) / mov.loadMovie(filename)
2. mov.play()
3. mov.pause()
4. mov.seek()
4. mov.stop()
5. mov.set/getVolume()
6. Standard BaseVisualStim, ContainerMixin methods, unless noted above.

Testing has only been done on Windows and Linux so far.
'''

# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).
#
# Contributed by Sol Simpson, April 2014.
# The MovieStim class was taken and rewritten to use cv2 and vlc instead of avbin

# If True, a print will be done on each flip a new movie frame is displayed
# giving the frame index, flip time, and time since last movie frame flip.
reportNDroppedFrames = 10

import os

# Ensure setting pyglet.options['debug_gl'] to False is done prior to any
# other calls to pyglet or pyglet submodules, otherwise it may not get picked
# up by the pyglet GL engine and have no effect.
# Shaders will work but require OpenGL2.0 drivers AND PyOpenGL3.0+
import pyglet
pyglet.options['debug_gl'] = False
GL = pyglet.gl

import psychopy  # so we can get the __path__
from psychopy import core, logging

from psychopy.tools.arraytools import val2array
from psychopy.tools.attributetools import logAttrib, setAttribute
from psychopy.visual.basevisual import BaseVisualStim, ContainerMixin

import ctypes
import numpy
import cv2
import vlc
from psychopy.clock import Clock
from psychopy.constants import FINISHED, NOT_STARTED, PAUSED, PLAYING, STOPPED


class MovieStim2(BaseVisualStim, ContainerMixin):
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
                 pos=(0.0,0.0),
                 ori=0.0,
                 flipVert=False,
                 flipHoriz=False,
                 color=(1.0,1.0,1.0),
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
                 interpolate = True,
        ):
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
        super(MovieStim2, self).__init__(win, units=units, name=name,
                                         autoLog=False)
        #check for pyglet
        if win.winType != 'pyglet':
            logging.error('Movie stimuli can only be used with a pyglet window')
            core.quit()
        self._retracerate = win._monitorFrameRate
        if self._retracerate is None:
            self._retracerate = win.getActualFrameRate()
        if self._retracerate is None:
            logging.warning("FrameRate could not be supplied by psychopy; defaulting to 60.0")
            self._retracerate = 60.0
        self.filename = filename
        self.loop = loop
        self.flipVert = flipVert
        self.flipHoriz = flipHoriz
        self.pos = numpy.asarray(pos, float)
        self.depth = depth
        self.opacity = float(opacity)
        self.volume = volume
        self._av_stream_time_offset = 0.145
        self._no_audio = noAudio
        self._requested_fps = fps
        self._vframe_callback = vframe_callback
        self.interpolate = interpolate

        self.useTexSubImage2D = True

        self._texID = None
        self._reset()
        self.loadMovie(self.filename)
        self.setVolume(volume)
        self.nDroppedFrames = 0

        self.aspectRatio = self._video_width/float(self._video_height)
        #size
        if size is None:
            self.size = numpy.array([self._video_width, self._video_height],
                                   float)
        elif isinstance(size, (int, float, long)):
            # treat size as desired width, and calc a height
            # that maintains the aspect ratio of the video.
            self.size = numpy.array([size, size/self.aspectRatio], float)
        else:
            self.size = val2array(size)
        self.ori = ori
        self._updateVertices()
        #set autoLog (now that params have been initialised)
        self.autoLog = autoLog
        if autoLog:
            logging.exp("Created %s = %s" %(self.name, str(self)))

    def _reset(self):
        self.duration = None
        self.status = NOT_STARTED
        self._numpy_frame = None
        if self._texID is not None:
            GL.glDeleteTextures(1, self._texID)
            self._texID = None
        self._video_stream = None
        self._total_frame_count = None
        self._video_width = None
        self._video_height = None
        # TODO: Read depth from video source
        self._video_frame_depth = 3
        self._video_frame_rate = None
        self._inter_frame_interval = None
        self._prev_frame_sec = None
        self._next_frame_sec = None
        self._next_frame_index = None
        self._prev_frame_index = None
        self._video_perc_done = None
#        self._last_video_flip_time = None
        self._next_frame_displayed = False
        self._video_track_clock = Clock()

        self._audio_stream_clock=Clock()
        self._vlc_instance = None
        self._audio_stream = None
        self._audio_stream_player = None
        self._audio_stream_started = False
        self._audio_stream_event_manager=None

    def setMovie(self, filename, log=True):
        """See `~MovieStim.loadMovie` (the functions are identical).
        This form is provided for syntactic consistency with other visual stimuli.
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
        self._unload()
        self._reset()
        if self._no_audio is False:
            self._createAudioStream()

        # Create Video Stream stuff
        self._video_stream = cv2.VideoCapture()
        self._video_stream.open(filename)
        vfstime = core.getTime()
        while not self._video_stream.isOpened() and core.getTime()-vfstime < 1.0:
          raise RuntimeError( "Error when reading image file")

        if not self._video_stream.isOpened():
          raise RuntimeError( "Error when reading image file")

        self._total_frame_count = self._video_stream.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
        self._video_width = self._video_stream.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
        self._video_height = self._video_stream.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
        self._format = self._video_stream.get(cv2.cv.CV_CAP_PROP_FORMAT)
        # TODO: Read depth from video source
        self._video_frame_depth = 3

        cv_fps = self._video_stream.get(cv2.cv.CV_CAP_PROP_FPS)
        if self._requested_fps:
            if self._no_audio is False and cv_fps != self._requested_fps:
                self._no_audio = True
                logging.error("MovieStim2 video fps != requested fps. Disabling Audio Stream.")
                logging.flush()

        if self._no_audio and self._requested_fps:
            self._video_frame_rate = self._requested_fps
        else:
            self._video_frame_rate = cv_fps

        self._inter_frame_interval = 1.0/self._video_frame_rate

        # Create a numpy array that can hold one video frame, as returned by cv2.
        self._numpy_frame = numpy.zeros((self._video_height,
                                          self._video_width,
                                          self._video_frame_depth),
                                         dtype=numpy.uint8)
        self.duration = self._total_frame_count * self._inter_frame_interval
        self.status = NOT_STARTED

        self.filename = filename
        logAttrib(self, log, 'movie', filename)

    def _createAudioStream(self):
        """
        Create the audio stream player for the video using pyvlc.
        """
        if not os.access(self.filename, os.R_OK):
            raise RuntimeError('Error: %s file not readable' % self.filename)
        self._vlc_instance = vlc.Instance('--novideo')
        try:
            self._audio_stream = self._vlc_instance.media_new(self.filename)
        except NameError:
            raise ImportError('NameError: %s vs LibVLC %s' % (vlc.__version__,
                                                       vlc.libvlc_get_version()))
        self._audio_stream_player = self._vlc_instance.media_player_new()
        self._audio_stream_player.set_media(self._audio_stream)
        self._audio_stream_event_manager = self._audio_stream_player.event_manager()
        self._audio_stream_event_manager.event_attach(vlc.EventType.MediaPlayerTimeChanged, self._audio_time_callback, self._audio_stream_player)
        self._audio_stream_event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._audio_end_callback)

    def _releaseeAudioStream(self):
        if self._audio_stream_player:
            self._audio_stream_player.stop()

        if self._audio_stream_event_manager:
            self._audio_stream_event_manager.event_detach(vlc.EventType.MediaPlayerTimeChanged)
            self._audio_stream_event_manager.event_detach(vlc.EventType.MediaPlayerEndReached)

        if self._audio_stream:
            self._audio_stream.release()

        if self._vlc_instance:
            self._vlc_instance.vlm_release()
            self._vlc_instance.release()

        self._audio_stream = None
        self._audio_stream_event_manager = None
        self._audio_stream_player = None
        self._vlc_instance = None

    def _flipCallback(self):
        self._next_frame_displayed = True

    def play(self, log=True):
        """Continue a paused movie from current position.
        """
        cstat = self.status
        if cstat != PLAYING:
            self.status = PLAYING

            if self._next_frame_sec is None:
                # movie has no current position, need to reset the clock
                # to zero in order to have the timing logic work
                # otherwise the video stream would skip frames until the
                # time since creating the movie object has passed
                self._video_track_clock.reset()

            if cstat == PAUSED:
                # toggle audio pause
                if self._audio_stream_player:
                    self._audio_stream_player.pause()
                    self._audio_stream_clock.reset(-self._audio_stream_player.get_time()/1000.0)
                if self._next_frame_sec:
                    self._video_track_clock.reset(-self._next_frame_sec)
            else:
                nt = self._getNextFrame()
                self._video_track_clock.reset(-nt)

            if log and self.autoLog:
                    self.win.logOnFlip("Set %s playing" %(self.name),
                                       level=logging.EXP, obj=self)

            self._updateFrameTexture()
            self.win.callOnFlip(self._flipCallback)
            return self._next_frame_index

    def pause(self, log=True):
        """
        Pause the current point in the movie (sound will stop, current frame
        will not advance).  If play() is called again both will restart.
        """
        if self.status == PLAYING:
            self.status = PAUSED
            if self._audio_stream_player and self._audio_stream_player.can_pause():
                self._audio_stream_player.pause()
            if log and self.autoLog:
                self.win.logOnFlip("Set %s paused" %(self.name), level=logging.EXP, obj=self)
            return True
        if log and self.autoLog:
            self.win.logOnFlip("Failed Set %s paused" %(self.name), level=logging.EXP, obj=self)
        return False

    def stop(self, log=True):
        """
        Stop the current point in the movie (sound will stop, current frame
        will not advance). Once stopped the movie cannot be restarted - it must
        be loaded again. Use pause() if you may need to restart the movie.
        """
        if self.status != STOPPED:
            self.status = STOPPED
            self._unload()
            self._reset()
            if log and self.autoLog:
                self.win.logOnFlip("Set %s stopped" %(self.name),
                    level=logging.EXP,obj=self)


    def seek(self, timestamp, log=True):
        """ Seek to a particular timestamp in the movie.
        """
        if self.status in [PLAYING, PAUSED]:
            if timestamp > 0.0:
                if self.status == PLAYING:
                    self.pause()

                if self._audio_stream_player and self._audio_stream_player.is_seekable():
                    self._audio_stream_player.set_time(int(timestamp*1000.0))
                    self._audio_stream_clock.reset(-timestamp)

                self._video_stream.set(cv2.cv.CV_CAP_PROP_POS_MSEC,
                                        timestamp*1000.0)
                self._video_track_clock.reset(-timestamp)
                self._next_frame_index = self._video_stream.get(cv2.cv.CV_CAP_PROP_POS_FRAMES)
                self._next_frame_sec = self._video_stream.get(cv2.cv.CV_CAP_PROP_POS_MSEC)/1000.0
            else:
                self.stop()
                self.loadMovie(self.filename)
            if log:
                logAttrib(self, log, 'seek', timestamp)

            self.play()

    def setFlipHoriz(self, newVal=True, log=True):
        """If set to True then the movie will be flipped horizontally (left-to-right).
        Note that this is relative to the original, not relative to the current state.
        """
        self.flipHoriz = newVal
        logAttrib(self, log, 'flipHoriz')

    def setFlipVert(self, newVal=True, log=True):
        """If set to True then the movie will be flipped vertically (top-to-bottom).
        Note that this is relative to the original, not relative to the current state.
        """
        self.flipVert = not newVal
        logAttrib(self, log, 'flipVert')

    def setVolume(self, v):
        """
        Set the audio track volume. 0 = mute, 100 = 0 dB. float values
        between 0.0 and 1.0 are also accepted, and scaled to an int between 0
        and 100.
        """
        if self._audio_stream_player:
            if 0.0 <= v <= 1.0 and isinstance(v, (float,)):
                v = int(v*100)
            else:
                v = int(v)
            self.volume = v
            self._audio_stream_player.audio_set_volume(v)

    def getVolume(self):
        """
        Returns the current movie audio volume. 0 is no audio, 100 is max audio
        volume.
        """
        if self._audio_stream_player:
            self.volume = self._audio_stream_player.audio_get_volume()
        return self.volume

    def getFPS(self):
        """
        Returns the movie frames per second playback speed.
        """
        return self._video_frame_rate

    def setFPS(self, fps):
        """
        If the movie was created with noAudio = True kwarg, then the movie
        playback speed can be changed from the original frame rate. For example,
        if the movie being played has 30 fps and you would like to play it at 2x
        normal speed, setFPS(60) will do that.
        """
        if self._no_audio:
            self._requested_fps = fps
            self._video_frame_rate = fps
            self._inter_frame_interval = 1.0/self._video_frame_rate
            return
        raise ValueError("Error calling movie.setFPS(): MovieStim must be created with kwarg noAudio=True.")

    def getTimeToNextFrameDraw(self):
        """
        Get the number of sec.msec remaining until the next movie video frame
        should be drawn.
        """
#        rt = (self._next_frame_sec - 1.0/self._retracerate) - self._video_track_clock.getTime()
        try:
            rt = (self._next_frame_sec - 1.0/self._retracerate) - self._video_track_clock.getTime()
            #print "getTimeToNextFrameDraw: ",self.getCurrentFrameNumber(), rt
            return rt
        except:
            #import traceback
            #traceback.print_exc()
            logging.warning("MovieStim2.getTimeToNextFrameDraw failed.")
            return 0.0

    def shouldDrawVideoFrame(self):
        """
        True if the next movie frame should be drawn, False if it is not yet
        time. See getTimeToNextFrameDraw().
        """
        return self.getTimeToNextFrameDraw() <= 0.0

    def getCurrentFrameNumber(self):
        """
        Get the current movie frame number. The first frame number in a file is
        1.
        """
        return self._next_frame_index

    def getCurrentFrameTime(self):
        """
        Get the time that the movie file specified the current video frame as
        having.
        """
        return self._next_frame_sec

    def getPercentageComplete(self):
        """
        Provides a value between 0.0 and 100.0, indicating the amount of the
        movie that has been already played.
        """
        return self._video_perc_done

    def isCurrentFrameVisible(self):
        """
        The current video frame goes through two stages; the first being when
        the movie frame is being loaded, but is not visible on the display.
        The second is when the frame has actually been presented on the display.
        Returns False if the frame is in the first stage, True when in stage 2.
        """
        return self._next_frame_displayed

    def _getNextFrame(self):
        # get next frame info ( do not decode frame yet)
        while self.status == PLAYING:
            if self._video_stream.grab():
                self._prev_frame_index = self._next_frame_index
                self._prev_frame_sec = self._next_frame_sec
                self._next_frame_index = self._video_stream.get(cv2.cv.CV_CAP_PROP_POS_FRAMES)
                if self._requested_fps and self._no_audio:
                    self._next_frame_sec = self._next_frame_index/self._requested_fps#*self._video_stream.get(cv2.cv.CV_CAP_PROP_POS_MSEC)/1000.0
                else:
                    self._next_frame_sec = self._video_stream.get(cv2.cv.CV_CAP_PROP_POS_MSEC)/1000.0
                self._video_perc_done = self._video_stream.get(cv2.cv.CV_CAP_PROP_POS_AVI_RATIO)
                self._next_frame_displayed = False
                if self.getTimeToNextFrameDraw() > -self._inter_frame_interval/2.0:
                    return self._next_frame_sec
                else:
                    self.nDroppedFrames += 1
                    if self.nDroppedFrames < reportNDroppedFrames:
                        logging.warning("MovieStim2 dropping video frame index: %d"%(self._next_frame_index))
                    elif self.nDroppedFrames == reportNDroppedFrames:
                        logging.warning("Multiple Movie frames have "
                                        "occurred - I'll stop bothering you "
                                        "about them!")
            else:
                self._onEos()
                break

    def _updateFrameTexture(self):
        # decode frame into np array and move to opengl tex
        ret, self._numpy_frame[:] = self._video_stream.retrieve()
        if ret:
            #if callable(self._vframe_callback):
            #    try:
            #        self._vframe_callback(self._next_frame_index, self._numpy_frame)
            #    except:
            #        print "MovieStim2 Error: vframe_callback raised an exception. Using original frame data."
            #        import traceback
            #        traceback.print_exc()

            useSubTex=self.useTexSubImage2D
            if self._texID is None:
                self._texID = GL.GLuint()
                GL.glGenTextures(1, ctypes.byref(self._texID))
                useSubTex=False

            #bind the texture in openGL
            GL.glEnable(GL.GL_TEXTURE_2D)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)#bind that name to the target
            GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_WRAP_S,GL.GL_REPEAT) #makes the texture map wrap (this is actually default anyway)
            GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)  # data from PIL/numpy is packed, but default for GL is 4 bytes
            #important if using bits++ because GL_LINEAR
            #sometimes extrapolates to pixel vals outside range
            if self.interpolate:
                GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_LINEAR)
                if self.useShaders:#GL_GENERATE_MIPMAP was only available from OpenGL 1.4
                    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
                    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_GENERATE_MIPMAP, GL.GL_TRUE)
                    if useSubTex is False:
                        GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, pyglet.gl.GL_RGB8,
                            self._numpy_frame.shape[1],self._numpy_frame.shape[0], 0,
                            GL.GL_BGR, GL.GL_UNSIGNED_BYTE, self._numpy_frame.ctypes)
                    else:
                        GL.glTexSubImage2D(GL.GL_TEXTURE_2D, 0, 0, 0,
                            self._numpy_frame.shape[1], self._numpy_frame.shape[0],
                            GL.GL_BGR, GL.GL_UNSIGNED_BYTE, self._numpy_frame.ctypes)

                else:#use glu
                    GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR_MIPMAP_NEAREST)
                    GL.gluBuild2DMipmaps(GL.GL_TEXTURE_2D, GL.GL_RGB8,
                        self._numpy_frame.shape[1],self._numpy_frame.shape[0], GL.GL_BGR, GL.GL_UNSIGNED_BYTE, self._numpy_frame.ctypes)
            else:
                GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MAG_FILTER,GL.GL_NEAREST)
                GL.glTexParameteri(GL.GL_TEXTURE_2D,GL.GL_TEXTURE_MIN_FILTER,GL.GL_NEAREST)
                if useSubTex is False:
                    GL.glTexImage2D(GL.GL_TEXTURE_2D, 0, GL.GL_RGB8,
                                    self._numpy_frame.shape[1],self._numpy_frame.shape[0], 0,
                                    GL.GL_BGR, GL.GL_UNSIGNED_BYTE, self._numpy_frame.ctypes)
                else:
                    GL.glTexSubImage2D(GL.GL_TEXTURE_2D, 0, 0, 0,
                        self._numpy_frame.shape[1], self._numpy_frame.shape[0],
                        GL.GL_BGR, GL.GL_UNSIGNED_BYTE, self._numpy_frame.ctypes)
            GL.glTexEnvi(GL.GL_TEXTURE_ENV, GL.GL_TEXTURE_ENV_MODE, GL.GL_MODULATE)#?? do we need this - think not!
        else:
            raise RuntimeError("Could not load video frame data.")

    def _getVideoAudioTimeDiff(self):
        if self._audio_stream_started is False:
            return 0
        return self.getCurrentFrameTime()-self._getAudioStreamTime()

    def draw(self, win=None):
        """
        Draw the current frame to a particular visual.Window (or to the
        default win for this object if not specified). The current position in
        the movie will be determined automatically.

        This method should be called on every frame that the movie is meant to
        appear"""
        if self.status==NOT_STARTED or (self.status==FINISHED and self.loop):
            self.play()
        elif self.status == FINISHED and not self.loop:
            return
        return_next_frame_index = False
        if win is None:
            win = self.win
        self._selectWindow(win)

        if self._no_audio is False and not self._audio_stream_started and self._video_track_clock.getTime() >= self._av_stream_time_offset:
            self._startAudio()

        if self._next_frame_displayed:
            if self._getVideoAudioTimeDiff() > self._inter_frame_interval:
                self._video_track_clock.reset(-self._next_frame_sec)
            else:
                self._getNextFrame()

        if self.shouldDrawVideoFrame() and not self._next_frame_displayed:
            self._updateFrameTexture()
            return_next_frame_index = True

        #make sure that textures are on and GL_TEXTURE0 is active
        GL.glActiveTexture(GL.GL_TEXTURE0)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glColor4f(1, 1, 1, self.opacity)  # sets opacity (1,1,1 = RGB placeholder)
        GL.glPushMatrix()
        self.win.setScale('pix')
        #move to centre of stimulus and rotate
        vertsPix = self.verticesPix

        array = (GL.GLfloat * 32)(
             1,  1, #texture coords
             vertsPix[0,0], vertsPix[0,1],    0.,  #vertex
             0,  1,
             vertsPix[1,0], vertsPix[1,1],    0.,
             0, 0,
             vertsPix[2,0], vertsPix[2,1],    0.,
             1, 0,
             vertsPix[3,0], vertsPix[3,1],    0.,
             )
        GL.glPushAttrib(GL.GL_ENABLE_BIT)
        GL.glEnable(GL.GL_TEXTURE_2D)
        GL.glBindTexture(GL.GL_TEXTURE_2D, self._texID)
        GL.glPushClientAttrib(GL.GL_CLIENT_VERTEX_ARRAY_BIT)
        #2D texture array, 3D vertex array
        GL.glInterleavedArrays(GL.GL_T2F_V3F, 0, array)
        GL.glDrawArrays(GL.GL_QUADS, 0, 4)
        GL.glPopClientAttrib()
        GL.glPopAttrib()
        GL.glPopMatrix()
        #GL.glActiveTexture(0)
        #GL.glDisable(GL.GL_TEXTURE_2D)
        if return_next_frame_index:
            self.win.callOnFlip(self._flipCallback)
            return self._next_frame_index

    def setContrast(self):
        """Not yet implemented for MovieStim"""
        pass

    def _startAudio(self):
        """
        Start the audio playback stream.
        """
        if self._audio_stream_player:
            self._audio_stream_started = True

            self._audio_stream_player.play()
            self._audio_stream_clock.reset(-self._audio_stream_player.get_time()/1000.0)

    def _getAudioStreamTime(self):
        return self._audio_stream_clock.getTime()

    def _audio_time_callback(self, event, player):
        """
        Called by VLC every few hundred msec providing the current audio track
        time. This info is used to pace the display of video frames read using
        cv2.
        """
        self._audio_stream_clock.reset(-event.u.new_time/1000.0)

    def _audio_end_callback(self, event):
        """
        Called by VLC when the audio track ends. Right now, when this is called
        the video is stopped.
        """
        self._onEos()

    def _unload(self):
        if self._video_stream:
            self._video_stream.release()
        self._video_stream = None
        self._numpy_frame = None

        self._releaseeAudioStream()

        self.status = FINISHED

    def _onEos(self):
        if self.loop:
            self.seek(0.0)
        else:
            self.status = FINISHED
            self.stop()

        if self.autoLog:
            self.win.logOnFlip("Set %s finished" %(self.name),
                level=logging.EXP,obj=self)

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
        #add to drawing list and update status
        setAttribute(self, 'autoDraw', val, log)
