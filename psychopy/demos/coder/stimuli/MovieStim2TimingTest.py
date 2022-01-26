#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
 ** IMPORTANT: Review the software and hardware details saved by this program
   before sending the file to anyone. You must be comfortable with a 3rd party
   viewing the computer details being reported.

This script plays a video file using visual.MovieStim2, records timing
information about each video frame displayed, as well as information about
the computer software and hardware used to run the script.

The hope is that this script can be used to further understand what is,
and is not, working with MovieStim2, and provide information that may help
determine the root cause of any issues found.

The following variables control what video is played during the test as well as
other configuration settings:
"""

#   Test Config.

# Relative path (from this scripts folder) for the video clip to be played .
video_name = r'./jwpIntro.mp4'

# If False, no audio tracks will be played.
INCLUDE_AUDIO_TRACK = True

# Size of the PsychoPy Window to create (in pixels).
WINDOW_SIZE = [1280, 720]

# If True, WINDOW_SIZE is ignored and a full screen PsychoPy Window is created.
USE_FULLSCREEN_WINDOW = False

# On systems with > 1 screen, the index of the screen to open the win in.
SCREEN_NUMBER = 0

# If the video frame rate is less than the monitor's refresh rate, then there
# will be some monitor retraces where the video frame does not change. In
# this case, SLEEP_IF_NO_FLIP = True will cause the script to sleep for 1 msec.
# If False, the video playback loop does not insert any sleep times.
SLEEP_IF_NO_FLIP = True

# If True, data about each process running on the computer when this script
# is executed is saved to the results file. Set to False if you do not want
# this information saved. If a string, processes with that name are saved
SAVE_PER_PROCESS_DATA = 'python.exe'

# If you do not want any results file saved at all, set this to None, otherwise
# keep it as an empty list.
video_results = []
#
"""
[ .. script docs continued ..]

A results file is saved in the same folder as the video file that was played.
The results file name is:

[video_name]_frame_timing.txt

video_name is the file name of the video played, with '.' replaced with '_'.

The results file contains several sections of information, the
last of which is the actual tab delimited video frame timing data.

The frame timing section can be opened by a program like LibreOffice Calc.
Select 'tabs' as the column delimiter.

Example Results File Output
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

 ** Video Info **
Video File:
    Name: 	./jwpIntro.mp4
    Frame Count: 	145.0
    Width: 	320.0
    Height: 	240.0
    FPS (Format, Requested): 	(25.0, None)
    Play Audio Track: 	True
Video Display:
    Window Resolution: 	[1920 1080]
    Window Fullscreen: 	True
    Drawn Size: 	[ 320.  240.]
    Refresh Rate (reported / calculated): 	60 / 59.9989858627

 ** System Info **
    OS:
        Name: Windows-7-6.1.7601-SP1
    Computer Hardware:
        CPUs (cores / logical): (4, 8)
        System Memory:
            Available: 7.3G
            Used: 8.6G
            Total: 16.0G
            Percent: 54.2
            Free: 7.3G
    Python:
        exe: C:\\Anaconda\\python.exe
        version: 2.7.7 |Anaconda 2.1.0 (64-bit)| (default, Jun 11 2014, 10: 40: 02) [MSC v.1500 64 bit (AMD64)]
    Packages:
        numpy: 1.9.0
        pyglet: 1.2alpha1
        cv2: 2.4.9
        PsychoPy: 1.81.03
    Graphics:
        shaders: True
        opengl:
            version: 4.4.0 NVIDIA 344.11
            vendor: NVIDIA Corporation
            engine: GeForce GTX 580/PCIe/SSE2
            Max vert in VA: 1048576
            extensions:
                GL_ARB_multitexture: True
                GL_EXT_framebuffer_object: True
                GL_ARB_fragment_program: True
                GL_ARB_shader_objects: True
                GL_ARB_vertex_shader: True
                GL_ARB_texture_non_power_of_two: True
                GL_ARB_texture_float: True
                GL_STEREO: False
    Processes: [Only Saved if SAVE_PER_PROCESS_DATA = True]

        [Each user accessible process running on the computer will be output]
        [Example output for 3 processes: ]

        15187:
            num_threads: 3
            exe: C:\\Program Files (x86)\\Notepad++\\notepad++.exe
            name: notepad++.exe
            cpu_percent: 0.0
            cpu_affinity: [0, 1, 2, 3, 4, 5, 6, 7]
            memory_percent: 0.176239720445
            num_ctx_switches: pctxsw(voluntary=5220262, involuntary=0)
            ppid: 4648
            nice: 32
        16656:
            num_threads: 11
            exe: C:\\Program Files (x86)\\Google\\Chrome\\Application\\chrome.exe
            name: chrome.exe
            cpu_percent: 0.0
            cpu_affinity: [0, 1, 2, 3, 4, 5, 6, 7]
            memory_percent: 0.200959182049
            num_ctx_switches: pctxsw(voluntary=136232, involuntary=0)
            ppid: 8588
            nice: 32
        16688:
            num_threads: 17
            exe: C:\\Anaconda\\python.exe
            name: python.exe
            cpu_percent: 75.1
            cpu_affinity: [0, 1, 2, 3, 4, 5, 6, 7]
            memory_percent: 0.786193630842
            num_ctx_switches: pctxsw(voluntary=76772, involuntary=0)
            ppid: 12912
            nice: 32

 ** Column Definitions **

[INSERT: Description of each column of the video playback data saved.]

 ** Per Frame Video Playback Data **
frame_num	frame_flip_time	playback_duration	frame_num_dx	dropped_count

[INSERT: One row for each frame displayed during video playback]

[...]
15	3.284598	0.628544	1	1	0.000254	0.005486	0.033325	0.033325	23.865
16	3.334647	0.678593	1	1	0.000258	0.015530	0.050049	0.050049	23.578
17	3.367943	0.711889	1	1	0.000286	0.008799	0.033296	0.033296	23.880
18	3.401261	0.745207	1	1	0.000260	0.002137	0.033318	0.033318	24.154
19	3.451266	0.795213	1	1	0.000264	0.012135	0.050006	0.050006	23.893
20	3.484598	0.828544	1	1	0.000268	0.005463	0.033331	0.033331	24.139
[...]
"""


from psychopy import visual, core, event, constants

getTime = core.getTime
import time, os, numpy as np

# Globals

drop_count = 0
last_frame_ix = -1
last_frame_time = 0
first_flip_time = 0
flip_dur = 0
draw_dur = 0
video_results_data = []

def getVideoFilePath():
    videopath = os.path.normpath(os.path.join(os.getcwd(), video_name))
    if not os.path.exists(videopath):
        raise RuntimeError("Video File could not be found:" + videopath)
    return videopath

def getResultsFilePath():
    _vdir, _vfile = os.path.split(getVideoFilePath())
    _results_file = u'%s_frame_timing.txt' % (_vfile.replace('.', '_'))
    return os.path.join(_vdir, _results_file)

def removeExistingResultsFile():
    # delete existing results file of same name (if exists)
    rfpath = getResultsFilePath()
    if os.path.exists(rfpath):
        try:
            os.remove(rfpath)
        except Exception:
            pass

def initProcessStats():
    try:
        import psutil

        for proc in psutil.process_iter():
            proc.cpu_percent()
    except Exception:
        pass

def getSysInfo(win):
    from collections import OrderedDict
    # based on sysInfo.py
    from pyglet.gl import gl_info, GLint, glGetIntegerv, GL_MAX_ELEMENTS_VERTICES
    import sys, platform

    sys_info = OrderedDict()
    sys_info['OS'] = OrderedDict()
    sys_info['OS']['Name'] = platform.platform()
    if sys.platform == 'darwin':
        OSXver, _, architecture = platform.mac_ver()
        sys_info['OS']['OSX Version'] = OSXver
        sys_info['OS']['OSX Architecture'] = architecture

    sys_info['Computer Hardware'] = OrderedDict()
    try:
        import psutil

        def getMemoryInfo():
            rdict = dict()
            nt = psutil.virtual_memory()
            for name in nt._fields:
                value = getattr(nt, name)
                if name != 'percent':
                    value = bytes2human(value)
                rdict[name.capitalize()] = value  # '%s%s%-10s : %7s\n'%(rstr, '\t' * indent, name.capitalize(), value)
            return rdict

        core_count = psutil.cpu_count(logical=False)
        logical_psu_count = psutil.cpu_count()
        memory_info = getMemoryInfo()
        sys_info['Computer Hardware']['CPUs (cores / logical)'] = (core_count, logical_psu_count)
        sys_info['Computer Hardware']['System Memory'] = memory_info

    except Exception:
        sys_info['Computer Hardware']['Failed'] = 'psutil 2.x + is required.'

    sys_info['Python'] = OrderedDict()
    sys_info['Python']['exe'] = sys.executable
    sys_info['Python']['version'] = sys.version

    sys_info['Packages'] = OrderedDict()
    try:
        import numpy
        sys_info['Packages']['numpy'] = numpy.__version__
    except ImportError:
        sys_info['Packages']['numpy'] = "Not Installed"
    try:
        import pyglet
        sys_info['Packages']['pyglet'] = pyglet.version
    except ImportError:
        sys_info['Packages']['pyglet'] = "Not Installed"
    try:
        import cv2
        sys_info['Packages']['cv2'] = cv2.__version__
    except ImportError:
        sys_info['Packages']['cv2'] = "Not Installed"
    try:
        import psychopy
        sys_info['Packages']['PsychoPy'] = psychopy.__version__
    except ImportError:
        sys_info['Packages']['PsychoPy'] = "Not Installed"

    sys_info['Graphics'] = OrderedDict()
    sys_info['Graphics']['shaders'] = win._haveShaders
    sys_info['Graphics']['opengl'] = OrderedDict()
    sys_info['Graphics']['opengl']['version'] = gl_info.get_version()
    sys_info['Graphics']['opengl']['vendor'] = gl_info.get_vendor()
    sys_info['Graphics']['opengl']['engine'] = gl_info.get_renderer()
    maxVerts = GLint()
    glGetIntegerv(GL_MAX_ELEMENTS_VERTICES, maxVerts)
    sys_info['Graphics']['opengl']['Max vert in VA'] = maxVerts.value
    sys_info['Graphics']['opengl']['extensions'] = OrderedDict()
    extensionsOfInterest = ['GL_ARB_multitexture',
                            'GL_EXT_framebuffer_object', 'GL_ARB_fragment_program',
                            'GL_ARB_shader_objects', 'GL_ARB_vertex_shader',
                            'GL_ARB_texture_non_power_of_two', 'GL_ARB_texture_float', 'GL_STEREO']
    for ext in extensionsOfInterest:
        sys_info['Graphics']['opengl']['extensions'][ext] = bool(gl_info.have_extension(ext))

    sys_info['Processes'] = OrderedDict()
    if sys.platform == 'darwin':
        sys_info['Processes']['Failed'] = 'Not Supported on OSX.'
    elif SAVE_PER_PROCESS_DATA:
        try:
            import psutil

            for proc in psutil.process_iter():
                pkey = proc.pid
                vattrs = ['name', 'exe', 'ppid', 'num_threads', 'memory_percent', 'cpu_percent', 'cpu_affinity', 'nice',
                          'num_ctx_switches']
                procinfo = proc.as_dict(attrs=vattrs, ad_value=u"Access Denied")
                if procinfo['exe'] != "Access Denied" and (SAVE_PER_PROCESS_DATA is True or SAVE_PER_PROCESS_DATA == procinfo['name']):
                    sys_info['Processes'][pkey] = procinfo
        except ImportError:
            sys_info['Processes']['Failed'] = 'psutil 2.x + is required.'
    else:
        sys_info['Processes']['Disabled'] = 'Per Process details disabled by user.'

    return sys_info

def formattedDictStr(d, indent=1, rstr=''):
    try:
        from collections import OrderedDict
    except ImportError:
        from psychopy.iohub import OrderedDict
    for key, value in list(d.items()):
        if isinstance(value, (dict, OrderedDict)):
            rstr = "{rstr}{numtabs}{key}:\n".format(numtabs='\t' * indent, key=key, rstr=rstr)
            rstr = formattedDictStr(value, indent + 1, rstr)
        else:
            rstr = "{rstr}{numtabs}{key}: {value}\n".format(numtabs='\t' * indent, value=value, key=key, rstr=rstr)
    return rstr

def bytes2human(n):
    # https://code.activestate.com/recipes/578019/
    # >>  > bytes2human(10000)
    # '9.8K'
    # >>  > bytes2human(100001221)
    # '95.4M'
    symbols = ('K', 'M', 'G', 'T', 'P', 'E', 'Z', 'Y')
    prefix = {}
    for i, s in enumerate(symbols):
        prefix[s] = 1 <<  (i + 1) * 10
    for s in reversed(symbols):
        if n >=  prefix[s]:
            value = float(n) / prefix[s]
            return '%.1f%s' % (value, s)
    return "%sB" % n

def storeVideoFrameInfo(flip_time, frame_num):
    global first_flip_time, last_frame_time, last_frame_ix, drop_count, flip_dur, draw_dur
    if video_results is not None:
        ifi = 0
        ixdx = 0
        movie_playback_dur = 0
        fps = 0
        per_frame_interval = 0

        if first_flip_time == 0:
            video_results.append(
                "frame_num\tframe_flip_time\tplayback_duration\tframe_num_dx\tdropped_count\tdraw_duration\tflip_duration\tflip_interval\tper_frame_interval\tfps\n")
            first_flip_time = flip_time

        # manually check for dropped movie frames
        if last_frame_ix >=  0:
            ixdx = frame_num - last_frame_ix
            if ixdx >=  2:
                drop_count = drop_count + (ixdx - 1)
            elif ixdx < 0:
                print("ERROR: frame index change <=  0. This should not happen in this demo. frame=%d, last_frame=%d, ixdx=%d" % (
                frame_num, last_frame_ix, ixdx))
        last_frame_ix = frame_num

        # calculate inter movie frame interval etc.
        if last_frame_time > 0:
            ifi = flip_time - last_frame_time
            per_frame_interval = ifi / ixdx
            movie_playback_dur = flip_time - first_flip_time
            fps = last_frame_ix / movie_playback_dur

        last_frame_time = flip_time
        # video_results.append("%d\t%.6f\t%.6f\t%d\t%d\t%.6f\t%.6f\t%.6f\t%.6f\t%.3f\n" % (
        video_results_data.append((frame_num, flip_time, movie_playback_dur, ixdx, drop_count, draw_dur, flip_dur, ifi, per_frame_interval, fps))
        # <<  <<  < Playback stats calculations

def createResultsFile():
    if video_results is not None:
        with open(getResultsFilePath(), 'a') as f:
            print("Saving Frame Timing Results to: %s" % (getResultsFilePath()))

            import cv2

            f.write(" ** Video Info ** \n")
            f.write("Video File:\n")
            f.write("\tName:\t{0}\n".format(video_name))
            f.write("\tFrame Count:\t{0}\n".format(mov._total_frame_count))
            mov_duration = mov._total_frame_count/mov._video_stream.get(cv2.CAP_PROP_FPS)
            f.write("\tVideo Duration:\t{0}\n".format(mov_duration))
            f.write("\tWidth:\t{0}\n".format(mov._video_width))
            f.write("\tHeight:\t{0}\n".format(mov._video_height))
            f.write("\tFPS:\t{0}\n".format(mov.getFPS()))
            f.write("\tPlay Audio Track:\t{0}\n".format(not mov._no_audio))

            f.write("Video Display:\n")
            f.write("\tWindow Resolution:\t{0}\n".format(win.size))
            f.write("\tWindow Fullscreen:\t{0}\n".format(win._isFullScr))
            f.write("\tDrawn Size:\t{0}\n".format(mov.size))
            f.write("\tRefresh Rate (reported / calculated):\t{0} / {1}\n".format(win.winHandle._screen.get_mode().rate,
                                                                                  win.getActualFrameRate()))

            f.write("\n ** System Info ** \n")
            f.write(formattedDictStr(getSysInfo(win)))

def saveVideoFrameResults():
    if video_results is not None:
        with open(getResultsFilePath(), 'a') as f:
            video_results_array = np.asarray(video_results_data, dtype=np.float32)
            playack_duration = video_results_array[-1][2]
            dropped_count = video_results_array[-1][4]
            draw_tarray = video_results_array[: , 5]
            flip_tarray = video_results_array[: , 6]
            vframedur_tarray = draw_tarray + flip_tarray
            iflipi_tarray = video_results_array[: , 7]
            iframei_tarray = video_results_array[: , 8]

            f.write("\n ** Video Playback Stats ** \n")
            f.write("Playback Time: %.3f\n"%(playack_duration))
            f.write("Total Frames Dropped: %d\n"%(int(dropped_count)))
            f.write("Draw duration (min, max, mean): (%.6f, %.6f, %.6f)\n"%(draw_tarray.min(), draw_tarray.max(), draw_tarray.mean()))
            f.write("Flip duration (min, max, mean): (%.6f, %.6f, %.6f)\n"%(flip_tarray.min(), flip_tarray.max(), flip_tarray.mean()))
            f.write("Draw + Flip duration (min, max, mean): (%.6f, %.6f, %.6f)\n"%(vframedur_tarray.min(), vframedur_tarray.max(), vframedur_tarray.mean()))
            f.write("Frame Display Interval (min, max, mean): (%.6f, %.6f, %.6f)\n"%(iflipi_tarray.min(), iflipi_tarray.max(), iflipi_tarray.mean()))
            f.write("Effective Frame Interval (min, max, mean): (%.6f, %.6f, %.6f)\n"%(iframei_tarray.min(), iframei_tarray.max(), iframei_tarray.mean()))

            f.write("\n ** Column Definitions ** \n")
            f.write("frame_num:\tThe frame index being displayed. Range is 1 to video frame count.\n")
            f.write("frame_flip_time:\tThe time returned by win.flip() for the current frame_num.\n")
            f.write("playback_duration:\tcurrent frame_flip_time minus the first video frame_flip_time.\n")
            f.write("frame_num_dx:\tEquals current frame_num - the last flipped frame_num.\n")
            f.write("dropped_count:\tTotal number of video frames dropped so far.\n")
            f.write("draw_duration:\tThe time taken for the current video frames .draw() call to return.\n")
            f.write("flip_duration:\tThe time taken for the win.flip() call to return.\n")
            f.write("flip_interval:\tcurrent frame_num frame_flip_time - last frame_flip_time.\n")
            f.write("per_frame_interval:\tEquals flip_interval / frame_num_dx.\n")
            f.write("fps:\tEquals playback_duration / current frame_num.\n")
            f.write("\n ** Per Frame Video Playback Data ** \n")
            f.writelines(video_results)
            for vfd in video_results_data:
                f.write("%.0f\t%.6f\t%.6f\t%.0f\t%.0f\t%.6f\t%.6f\t%.6f\t%.6f\t%.3f\n"%vfd)
        del video_results[: ]

if __name__ == '__main__':
    removeExistingResultsFile()

    win = visual.Window(WINDOW_SIZE, fullscr=USE_FULLSCREEN_WINDOW, allowGUI=not USE_FULLSCREEN_WINDOW,
                        screen=SCREEN_NUMBER)

    # Create your movie stim.
    mov = visual.MovieStim2(win, getVideoFilePath(),
                            size=None,  # (1280, 720),
                            # pos specifies the /center/ of the movie stim location
                            pos=[0, 0],
                            flipVert=False,
                            flipHoriz=False,
                            noAudio=not INCLUDE_AUDIO_TRACK,
                            # fps=90,
                            loop=False)

    mov.useTexSubImage2D = True

    initProcessStats()

    # Start the movie stim by preparing it to play
    dt1 = getTime()
    display_frame_num = mov.play()
    draw_dur = getTime() - dt1

    while mov.status != constants.FINISHED:
        # Only flip when a new frame should be displayed. Can significantly reduce
        # CPU usage. This only makes sense if the movie is the only /dynamic/ stim
        # displayed.
        if display_frame_num:
            # Movie has already been drawn , so just draw text stim and flip
            # text.draw()
            ft1 = getTime()
            ftime = win.flip()
            flip_dur = getTime() - ft1
            storeVideoFrameInfo(ftime, display_frame_num)
        elif SLEEP_IF_NO_FLIP:
            # Give the OS a break if a flip is not needed
            time.sleep(0.001)

        # Drawn movie stim again. Updating of movie stim frames as necessary
        # is handled internally.
        dt1 = getTime()
        display_frame_num = mov.draw()
        draw_dur = getTime() - dt1

        # Check for action keys.....
        for key in event.getKeys():
            if key in ['escape', 'q']:
                mov.status = constants.FINISHED
                break

    createResultsFile()
    mov.stop()
    saveVideoFrameResults()

    core.quit()

# Movie2 logic not currently used / tested by this script

#        elif key in ['s', ]:
#            if mov.status in [constants.PLAYING, constants.PAUSED]:
#                # To stop the movie being played.....,
#                mov.stop()
#                # Clear screen of last displayed frame.
#                win.flip()
#                # When movie stops, clear screen of last displayed frame,
#                # and display text stim only....
#                # text.draw()
#                # win.flip()
#            else:
#                # To replay a movie that was stopped.....
#                mov.loadMovie(videopath)
#                display_frame_num = mov.play()
#        elif key in ['p', ]:
#            # To pause the movie while it is playing....
#            if mov.status == constants.PLAYING:
#                mov.pause()
#            elif mov.status == constants.PAUSED:
#                # To /unpause/ the movie if pause has been called....
#                display_frame_num = mov.play()
#        elif key == 'period':
#            # To skip ahead 1 second in movie.
#            ntime = min(mov.getCurrentFrameTime() + 1.0, mov.duration)
#            mov.seek(ntime)
#        elif key == 'comma':
#            # To skip back 1 second in movie ....
#            ntime = max(mov.getCurrentFrameTime()-1.0, 0.0)
#            mov.seek(ntime)
#        elif key == 'minus':
#            # To decrease movie sound a bit ....
#            cv = max(mov.getVolume()-5, 0)
#            mov.setVolume(cv)
#        elif key == 'equal':
#            # To increase movie sound a bit ....
#            cv = mov.getVolume()
#            cv = min(mov.getVolume() + 5, 100)
#            mov.setVolume(cv)

win.close()
core.quit()

# The contents of this file are in the public domain.
