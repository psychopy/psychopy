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
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).
#
# Contributed by Sol Simpson, April 2014.
# The MovieStim class was taken and rewritten to use cv2 and vlc instead of avbin

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
from psychopy.tools.attributetools import logAttrib
from psychopy.visual.basevisual import BaseVisualStim, ContainerMixin

import numpy
import cv2
from arrayimage2 import ArrayInterfaceImage
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
                 depth=0.0,):
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
        self.filename = filename
        self.loop = loop
        if loop: #and pyglet.version>='1.2':
            logging.error("looping of movies is not currently supported")
        self.flipVert = flipVert
        self.flipHoriz = flipHoriz
        self.pos = numpy.asarray(pos, float)
        self.depth = depth
        self.opacity = float(opacity)
        self.volume = volume
        self._av_stream_time_offset = 0.145

        self._reset()
        self.loadMovie(self.filename)
        self.setVolume(volume)

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
        self._frame_texture = None
        self._frame_data_interface = None
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
        self._last_video_flip_time = None
        self._next_frame_displayed = False
        self._video_track_clock = Clock()
        self._vlc_instance = None
        self._vlc_event_manager = None
        self._audio_stream = None
        self._audio_stream_player = None
        self._audio_stream_started = False
        self._last_audio_callback_time = core.getTime()
        self._last_audio_stream_time = None
        self._first_audio_callback_time = None
        self._audio_computer_time_drift = None

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
        self._reset()
        self._unload()
        self._createAudioStream()
        self._video_stream = cv2.VideoCapture()
        self._video_stream.open(filename)
        if not self._video_stream.isOpened():
          raise RuntimeError( "Error when reading image file")

        self._total_frame_count = self._video_stream.get(cv2.cv.CV_CAP_PROP_FRAME_COUNT)
        self._video_width = self._video_stream.get(cv2.cv.CV_CAP_PROP_FRAME_WIDTH)
        self._video_height = self._video_stream.get(cv2.cv.CV_CAP_PROP_FRAME_HEIGHT)
        self._format = self._video_stream.get(cv2.cv.CV_CAP_PROP_FORMAT)
        # TODO: Read depth from video source
        self._video_frame_depth = 3
        self._video_frame_rate = self._video_stream.get(cv2.cv.CV_CAP_PROP_FPS)
        self._inter_frame_interval = 1.0/self._video_frame_rate

        # Create a numpy array that can hold one video frame, as returned by cv2.
        self._numpy_frame = numpy.zeros((self._video_height,
                                          self._video_width,
                                          self._video_frame_depth),
                                         dtype=numpy.uint8)

        # Uses a preallocated numpy array as the pyglet ImageData data
        self._frame_data_interface = ArrayInterfaceImage(self._numpy_frame,
                                                         allow_copy=False,
                                                         rectangle=True,
                                                         force_rectangle=True)
        #frame texture; transformed so it looks right in psychopy
        self._frame_texture = self._frame_data_interface.texture.get_transform(flip_x=not self.flipHoriz,
                                                    flip_y=not self.flipVert)

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
        self._vlc_event_manager = self._audio_stream_player.event_manager()
        self._vlc_event_manager.event_attach(vlc.EventType.MediaPlayerTimeChanged, self._audio_time_callback, self._audio_stream_player)
        self._vlc_event_manager.event_attach(vlc.EventType.MediaPlayerEndReached, self._audio_end_callback)

    def _flipCallback(self):
        import inspect
        flip_time = inspect.currentframe().f_back.f_locals.get('now')
        if flip_time is None:
            raise RuntimeError("Movie2._flipCallback: Can not access the currect flip time.")
        self._last_video_flip_time = flip_time
        self._next_frame_displayed = True

    def play(self, log=True):
        """Continue a paused movie from current position.
        """
        if self.status != PLAYING:

            if self.status == PAUSED:
                # toggle audio pause
                self._audio_stream_player.pause()
            self.status = PLAYING
            if log and self.autoLog:
                    self.win.logOnFlip("Set %s playing" %(self.name),
                                       level=logging.EXP, obj=self)
            #print '### PLAY ###'
            self._video_track_clock.reset(-self._getNextFrame())
            self._updateFrameTexture()
            self.win.callOnFlip(self._flipCallback)
            #self._player._on_eos=self._onEos

    def pause(self, log=True):
        """Pause the current point in the movie (sound will stop, current frame
        will not advance).  If play() is called again both will restart.

        Completely untested in all regards.
        """
        if self.status == PLAYING and self._audio_stream_player:
            if self._audio_stream_player.can_pause():
                self.status = PAUSED
                self._audio_stream_player.pause()
                #print '### PAUSE ###'
                if log and self.autoLog:
                    self.win.logOnFlip("Set %s paused" %(self.name), level=logging.EXP, obj=self)
                return True
        if log and self.autoLog:
            self.win.logOnFlip("Failed Set %s paused" %(self.name), level=logging.EXP, obj=self)
        return False

    def stop(self, log=True):
        """Stop the current point in the movie (sound will stop, current frame
        will not advance). Once stopped the movie cannot be restarted - it must
        be loaded again. Use pause() if you may need to restart the movie.
        """
        #print '### STOP ###'
        self.status = STOPPED
        self._unload()
        self._reset()
        if log and self.autoLog:
            self.win.logOnFlip("Set %s stopped" %(self.name),
                level=logging.EXP,obj=self)


    def seek(self, timestamp, log=True):
        """ Seek to a particular timestamp in the movie.
        Completely untested in all regards.
        Does not currently work.
        """
        if self._audio_stream_player:
            if self.status in [PLAYING, PAUSED] and self._audio_stream_player.is_seekable():
                if self.status == PLAYING:
                    self.pause()
                aresult = self._audio_stream_player.set_time(int(timestamp*1000.0))
                vresult = self._video_stream.set(cv2.cv.CV_CAP_PROP_POS_MSEC,
                                        timestamp*1000.0)
                self.play()
                if log:
                    logAttrib(self, log, 'seek', timestamp)

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
        if 0.0 <= v <= 1.0 and isinstance(v, (float,)):
            v = int(v*100)
        else:
            v = int(v)
        #print 'setting volume:',v
        self.volume = v
        if self._audio_stream_player:
            self._audio_stream_player.audio_set_volume(v)

    def getVolume(self):
        if self._audio_stream_player:
            self.volume = self._audio_stream_player.audio_get_volume()
        return self.volume

    def getTimeToNextFrameDraw(self):
        try:
            #assert self._video_track_clock != None
            #assert self._next_frame_sec != None
            #assert self._retracerate != None
            rt = (self._next_frame_sec - 1.0/self._retracerate) - self._video_track_clock.getTime()
            #if rt > self._inter_frame_interval or rt <= -1.0/self._retracerate:
            #    print 'getTimeToNextFrameDraw:', rt
            return rt
        except:
            import traceback
            traceback.print_exc()
            return 0.0

    def shouldDrawVideoFrame(self):
        return self.getTimeToNextFrameDraw() <= 0.0

    def getCurrentFrameIndex(self):
        return self._next_frame_index

    def getCurrentFrameTime(self):
        return self._next_frame_sec

    def getPercentageComplete(self):
        return self._video_perc_done

    def getCurrentFrameDisplayed(self):
        return self._next_frame_displayed

    def _getNextFrame(self):
        # get next frame info ( do not decode frame yet)
        # TODO: Implement frame skipping (multiple grabs) if _next_frame_sec < video_track_clock - framerate
        if self._video_stream.grab():
            self._prev_frame_index = self._next_frame_index
            self._prev_frame_sec = self._next_frame_sec
            self._next_frame_sec = self._video_stream.get(cv2.cv.CV_CAP_PROP_POS_MSEC)/1000.0
            self._next_frame_index = self._video_stream.get(cv2.cv.CV_CAP_PROP_POS_FRAMES)
            self._video_perc_done = self._video_stream.get(cv2.cv.CV_CAP_PROP_POS_AVI_RATIO)
            self._next_frame_displayed = False
            return self._next_frame_sec
        else:
            self.status = FINISHED
            if self._audio_stream_player:
                self._audio_stream_player.stop()
            self._onEos()

    def _updateFrameTexture(self):
        # decode frame into np array and move to opengl tex
        ret, f = self._video_stream.retrieve()
        if ret:
            #self._numpy_frame[:] = f[...,::-1]
            numpy.copyto(self._numpy_frame, cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
            self._frame_data_interface.dirty()
        else:
            raise RuntimeError("Could not load video frame data.")

    def draw(self, win=None):
        """Draw the current frame to a particular visual.Window (or to the
        default win for this object if not specified). The current position in
        the movie will be determined automatically.

        This method should be called on every frame that the movie is meant to
        appear"""
        if self.status != PLAYING:
            return

        return_next_frame_index = False
        if win is None:
            win = self.win
        self._selectWindow(win)

        if not self._audio_stream_started and self._video_track_clock.getTime() >= self._av_stream_time_offset:
            self._startAudio()
        if self._next_frame_displayed:
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
        t=self._frame_texture.tex_coords
        array = (GL.GLfloat * 32)(
             t[0],  t[1],
             vertsPix[0,0], vertsPix[0,1],    0.,  #vertex
             t[3],  t[4],
             vertsPix[1,0], vertsPix[1,1],    0.,
             t[6],  t[7],
             vertsPix[2,0], vertsPix[2,1],    0.,
             t[9],  t[10],
             vertsPix[3,0], vertsPix[3,1],    0.,
             )
        GL.glPushAttrib(GL.GL_ENABLE_BIT)
        GL.glEnable(self._frame_texture.target)
        GL.glBindTexture(self._frame_texture.target, self._frame_texture.id)
        GL.glPushClientAttrib(GL.GL_CLIENT_VERTEX_ARRAY_BIT)
        #2D texture array, 3D vertex array
        GL.glInterleavedArrays(GL.GL_T2F_V3F, 0, array)
        GL.glDrawArrays(GL.GL_QUADS, 0, 4)
        GL.glPopClientAttrib()
        GL.glPopAttrib()
        GL.glPopMatrix()
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
        self._audio_stream_started = True
        self._last_audio_callback_time = core.getTime()
        self._audio_stream_player.play()

    def getAudioStreamTime(self):
        """
        Get the current sec.msec audio track time, by taking the last
        reported audio stream time and adding the time since the
        _audio_time_callback was last called.
        """
        #TODO: This will not be correct is video is paused. Fix.
        return self._last_audio_stream_time + (core.getTime() -
                                               self._last_audio_callback_time)

    def _audio_time_callback(self, event, player):
        """
        Called by VLC every few hundred msec providing the current audio track
        time. This info is used to pace the display of video frames read using
        cv2.
        """
        self._last_audio_callback_time = core.getTime()
        self._last_audio_stream_time = player.get_time()/1000.0
        if self._first_audio_callback_time is None:
           self._first_audio_callback_time = self._last_audio_callback_time-self._last_audio_stream_time
        self._audio_computer_time_drift = self._last_audio_stream_time-(
            self._last_audio_callback_time-self._first_audio_callback_time)


    def _audio_end_callback(self, event):
        """
        Called by VLC when the audio track ends. Right now, when this is called
        the video is stopped.
        """
#        print('End of media stream (event %s)' % event.type)
        self.status = FINISHED
        self._onEos()

    def _unload(self):
        if self._video_stream:
            self._video_stream.release()
        if self._audio_stream_player:
            self._audio_stream_player.stop()
        self._video_stream = None
        self._audio_stream_player = None
        self._frame_data_interface = None
        self._numpy_frame = None
        self.status = FINISHED

    def __del__(self):
        self._unload()

    def _onEos(self):
        if self.loop:
            self.loadMovie(self.filename)
            self.play()
            self.status = PLAYING
        else:
            self.status = FINISHED

        if self.autoLog:
            self.win.logOnFlip("Set %s finished" %(self.name),
                level=logging.EXP,obj=self)

#    def setAutoDraw(self, val, log=True):
#        """Add or remove a stimulus from the list of stimuli that will be
#        automatically drawn on each flip
#
#        :parameters:
#            - val: True/False
#                True to add the stimulus to the draw list, False to remove it
#        """
#        if val:
#            self.play(log=False)  # set to play in case stopped
#        else:
#            self.pause(log=False)
#        #add to drawing list and update status
#        self.autoDraw = val
#    def __del__(self):
#        self._player.next()
