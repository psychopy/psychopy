import platform
import profile

from psychopy.hardware.manager import DeviceManager
from psychopy.tools import systemtools as st
from psychopy.hardware.camera._base import (
    CAMERA_LIB_FFPYPLAYER, CAMERA_NULL_VALUE, CameraDevice, CameraInfo,
    pixelFormatTbl)
import time
from psychopy.hardware.camera._base import (
    CAMERA_API_DIRECTSHOW, CAMERA_API_AVFOUNDATION, CAMERA_API_VIDEO4LINUX2,
    CAMERA_FRAMERATE_NTSC, CAMERA_FRAMERATE_NOMINAL_NTSC, CAMERA_LIB_NULL, 
    CAMERA_STATUS_EOF, CAMERA_STATUS_PAUSED,
    CameraNotFoundError, CameraNotReadyError, CameraFrameSizeNotSupportedError, 
    PlayerNotAvailableError,
    FormatNotFoundError)
import logging  
import math
import threading


class FFPyPlayerCameraDevice(CameraDevice):
    """Class providing an interface with a camera attached to the system using FFmpeg (ffpyplayer).
    
    This interface handles the opening, closing, and reading of camera streams.

    Parameters
    ----------
    device : Any
        Camera device to open a stream with. The type of this value is dependent
        on the platform and the camera library being used. This can be an integer
        index, a string representing the camera device name.
    pollingInterval : float or None
        Interval in seconds to poll the camera stream for new frames. If `None`,
        the default polling interval is used which is equal to the frame rate. 
        The default value is `None`.

    """
    _streams = {}
    def __init__(self, device, captureAPI=None, decoderOpts=None, bufferSecs=5.0, pollingInterval=None):        
        # if device is an integer, get name from index
        foundProfile = None
        if isinstance(device, int):
            for profile in self.getAvailableDevices():
                if profile['device'] == device:
                    foundProfile = profile
                    break
        # if device is a string, get profile from name
        elif isinstance(device, str):
            for profile in self.getAvailableDevices():
                if profile['deviceName'] == device:
                    foundProfile = profile
                    break
        # if device is a dict, use it directly
        elif isinstance(device, dict):
            foundProfile = device

        if foundProfile is None:
            raise CameraNotFoundError(
                "Cannot find camera with index or name '{}'.".format(device))

        self.info = foundProfile
        self._device = self.info['deviceName']
        self._decoderOpts = decoderOpts if decoderOpts is not None else {}
        self._pollingInterval = pollingInterval if pollingInterval is not None else self.frameInterval
        self._pollingTimerThread = None
        self._pollingLock = threading.Lock()
        self._bufferSecs = bufferSecs
        self._frameCount = 0
        self._capture = None  # will hold the ffpyplayer MediaPlayer object

        if captureAPI is None:  # select based on platform
            if platform.system() == 'Darwin':
                self._captureAPI = CAMERA_API_AVFOUNDATION
            elif platform.system() == 'Windows':
                self._captureAPI = CAMERA_API_DIRECTSHOW
            elif platform.system() == 'Linux':
                self._captureAPI = CAMERA_API_VIDEO4LINUX2
            else:
                raise OSError(
                    "Unsupported platform '{}', cannot select capture API.".format(
                        platform.system()))
        else:
            self._captureAPI = captureAPI

        # keep track of clients attached to this camera stream
        self._cameraClients = []

        self.open()  # open the camera stream

    @property
    def frameSize(self):
        """Get the frame size of the camera stream.

        Returns
        -------
        tuple
            Frame size as (width, height). Returns `None` if the camera stream
            is not open or if metadata needs to be obtained from the stream.

        """
        if self._capture is None:
            return None

        return self.info['frameSize']
    
    @property
    def frameRate(self):
        """Get the frame rate of the camera stream.

        Returns
        -------
        float
            Frame rate in frames per second. Returns `None` if the camera stream
            is not open or if metadata needs to be obtained from the stream.

        """
        if self._capture is None:
            return None

        return self.info['frameRate']

    @property
    def frameInterval(self):
        """Get the frame interval of the camera stream.

        Returns
        -------
        float
            Frame interval in seconds. Returns `-1.0` if the camera stream is not
            open or if metadata needs to be obtained from the stream.

        """
        if self.info is None:
            return -1.0

        return 1.0 / self.info['frameRate']

    def bind(self, client):
        """Register a client to receive new frames from the camera stream.

        Parameters
        ----------
        client : object
            Client object that has an `onNewFrames(frames)` method to receive new frames.

        """
        if client not in self._cameraClients:
            self._cameraClients.append(client)
        
    def unbind(self, client):
        """Unregister a client from receiving new frames from the camera stream.

        Parameters
        ----------
        client : object
            Client object that was previously registered to receive new frames.

        """
        if client in self._cameraClients:
            self._cameraClients.remove(client)

    def _onNewFrames(self, frames):
        """Callback function called when new frames are available from the camera stream.
        
        Parameters
        ----------
        frames : list of tuples
            List of tuples containing the frames and their timestamps. Each tuple
            contains (frame, timestamp).

        """
        for client in self._cameraClients:
            client._onNewFrames(frames)

    def _getFrames(self):
        """Get the most recent frames from the camera stream opened with FFmpeg
        (ffpyplayer).
        
        Returns
        -------
        numpy.ndarray
            Most recent frames from the camera stream. Returns `None` if no
            frames are available.

        """
        if self._capture is None:
            raise PlayerNotAvailableError(
                "Camera stream is not open. Call `open()` first.")
        
        # read all buffered frames from the camera stream until we get nothing
        with self._pollingLock:
            recentFrames = []
            while 1:
                frame, status = self._capture.get_frame()

                if status == CAMERA_STATUS_EOF or status == CAMERA_STATUS_PAUSED: 
                    break

                if frame is None:  # ditto 
                    break

                img, curPts = frame
                # if curPts < 0.0:
                #     del img  # free the memory used by the frame
                #     # if the frame is before the recording start time, skip it
                #     continue

                self._frameCount += 1  # increment the frame count

                recentFrames.append((
                    img, 
                    curPts,
                    curPts))

            self._onNewFrames(recentFrames)  
            
        return recentFrames
    
    def _setupAutoPolling(self):
        """Set up automatic polling of the camera stream to read frames at regular intervals.
        
        This method sets up a thread that calls the `_poll` method at regular intervals
        defined by `self._pollingInterval`. The `_poll` method reads frames from the camera
        stream and processes them.

        """
        if self._pollingTimerThread is not None:
            self._pollingTimerThread.cancel()

        logging.debug(
            "Setting up automatic polling of the camera stream every {} seconds.".format(
                self._pollingInterval))

        # set up a thread to call the poll method at regular intervals
        class PollingTimerThread(threading.Thread):
            """Thread class used to call the poll method at regular 
            intervals.
            """
            def __init__(self, interval, function):
                super().__init__()
                self.interval = interval
                self.function = function
                self._stop_event = threading.Event()

            def run(self):
                while not self._stop_event.is_set():
                    time.sleep(self.interval)
                    self.function()

            def cancel(self):
                self._stop_event.set()

        # set up a thread to call the poll method at regular intervals
        self._pollingTimerThread = PollingTimerThread(
            self._pollingInterval, 
            self._poll)
        self._pollingTimerThread.daemon = True
        self._pollingTimerThread.start()

    @property
    def paused(self):
        """Check if the camera stream is paused.

        Returns
        -------
        bool
            `True` if the camera stream is paused, `False` otherwise.

        """
        if self._capture is None:
            raise PlayerNotAvailableError(
                "Camera stream is not open. Call `open()` first.")

        return self._capture.get_pause()
    
    @paused.setter
    def paused(self, value):
        """Pause or resume the camera stream.

        Parameters
        ----------
        value : bool
            If `True`, pause the camera stream. If `False`, resume the camera stream.

        """
        self.setPause(value)

    def setPause(self, pause):
        """Pause or resume the camera stream.

        This method allows pausing or resuming the camera stream. When paused, the 
        camera stream will not provide new frames until resumed. This can lower
        latency and reduce CPU usage when the camera is not needed.

        Parameters
        ----------
        pause : bool
            If `True`, pause the camera stream. If `False`, resume the camera stream.

        """
        if self._capture is None:
            raise PlayerNotAvailableError(
                "Camera stream is not open. Call `open()` first.")

        self._capture.set_pause(pause)

    @property
    def isOpen(self):
        """Check if the camera stream is open.

        Returns
        -------
        bool
            `True` if the camera stream is open, `False` otherwise.

        """
        return self._capture is not None

    def open(self):
        """Open the camera stream using FFmpeg (ffpyplayer).
        
        This method should be called to open the camera stream using FFmpeg.
        It should initialize the camera and prepare it for reading frames.

        """
        if self.isOpen:
            logging.debug(
                "Camera stream for device '{}' is already open.".format(
                    self._device))
            return
        
        # get settings from the profile
        self._frameSize = self.info['frameSize']
        self._frameRate = self.info['frameRate']
        self._codecFormat = self.info['codecFormat']
        self._pixelFormat = self.info['pixelFormat']

        self._bufferSecs = self._bufferSecs  # default buffer size in seconds
        self._decoderOpts = {}  # default decoder options

        # if we already have a stream for this device, reuse it
        if self._device in FFPyPlayerCameraDevice._streams.keys():
            if self.isSameDevice(FFPyPlayerCameraDevice._streams[self._device]):
                self._capture = FFPyPlayerCameraDevice._streams[self._device]._capture
                logging.debug(
                    "Reusing existing camera stream for device '{}'.".format(
                        self._device))
                return

        # compute the polling interval based on the frame rate, if not specified
        self._pollingInterval = 0.066

        # configure the camera stream reader
        ff_opts = {}  # ffmpeg options
        lib_opts = {}  # ffpyplayer options
        _camera = CAMERA_NULL_VALUE
        _frameRate = CAMERA_NULL_VALUE

        # setup commands for FFMPEG
        if self._captureAPI == CAMERA_API_DIRECTSHOW:  # windows
            ff_opts['f'] = 'dshow'
            _camera = 'video={}'.format(self.info['name'])
            _frameRate = self._frameRate
            if self._pixelFormat:
                ff_opts['pixel_format'] = self._pixelFormat
            if self._codecFormat:
                ff_opts['vcodec'] = self._codecFormat
        elif self._captureAPI == CAMERA_API_AVFOUNDATION:  # darwin
            ff_opts['f'] = 'avfoundation'
            ff_opts['i'] = _camera = self._device

            # handle pixel formats using FourCC
            global pixelFormatTbl
            ffmpegPixFmt = pixelFormatTbl.get(self._pixelFormat, None)

            if ffmpegPixFmt is None:
                raise FormatNotFoundError(
                    "Cannot find suitable FFMPEG pixel format for '{}'. Try a "
                    "different format or camera.".format(
                        self._pixelFormat))

            self._pixelFormat = ffmpegPixFmt

            # this needs to be exactly specified if using NTSC
            # if math.isclose(CAMERA_FRAMERATE_NTSC, self._frameRate):
            #     _frameRate = CAMERA_FRAMERATE_NOMINAL_NTSC
            # else:
            _frameRate = self._frameRate

            # need these since hardware acceleration is not possible on Mac yet
            lib_opts['fflags'] = 'nobuffer'
            lib_opts['flags'] = 'low_delay'
            lib_opts['pixel_format'] = self._pixelFormat
            lib_opts['use_wallclock_as_timestamps'] = '1'
            # ff_opts['framedrop'] = True
            # ff_opts['fast'] = True
        elif self._captureAPI == CAMERA_API_VIDEO4LINUX2:
            ff_opts['f'] = 'v4l2'
            # ff_opts['thread_queue_size'] = 1024
            # ff_opts['preset'] = 'ultrafast'
            _camera = self._device
            _frameRate = self._frameRate
        else:
            raise RuntimeError("Unsupported camera API specified.")

        # set library options
        camWidth, camHeight = self._frameSize
        logging.warning(
            "Using camera mode {}x{} at {} fps".format(
                camWidth, camHeight, _frameRate))
        
        # configure the real-time buffer size, we compute using RGB8 since this 
        # is uncompressed and represents the largest size we can expect
        self._frameSizeBytes = int(camWidth * camHeight * 3)
        framesToBufferCount = int(self._bufferSecs * float(_frameRate))
        _bufferSize = int(self._frameSizeBytes * framesToBufferCount)
        logging.debug(
            "Setting real-time buffer size to {} bytes "
            "for {} seconds of video ({} frames @ {} fps)".format(
                _bufferSize, 
                self._bufferSecs,
                framesToBufferCount,
                _frameRate)
        )

        # common settings across libraries
        ff_opts['low_delay'] = True  # low delay for real-time playback
        # ff_opts['framedrop'] = True
        # ff_opts['use_wallclock_as_timestamps'] = True
        ff_opts['fast'] = True
        # ff_opts['sync'] = 'ext'
        ff_opts['rtbufsize'] = str(_bufferSize)  # set the buffer size
        ff_opts['an'] = True
        # ff_opts['infbuf'] = True  # enable infinite buffering

        # for ffpyplayer, we need to set the video size and framerate
        lib_opts['video_size'] = '{width}x{height}'.format(
            width=camWidth, height=camHeight)
        lib_opts['framerate'] = str(_frameRate)
        ff_opts['loglevel'] = 'error'
        ff_opts['nostdin'] = True

        # open the media player
        from ffpyplayer.player import MediaPlayer
        self._capture = MediaPlayer(
            _camera, 
            ff_opts=ff_opts, 
            lib_opts=lib_opts)

        # compute the frame interval, needed for generating timestamps
        self._frameInterval = 1.0 / self._frameRate 
        
        # get metadata from the capture stream
        tStart = time.time()  # start time for the stream
        metadataTimeout = 5.0  # timeout for metadata retrieval
        while time.time() - tStart < metadataTimeout:  # wait for metadata
            streamMetadata = self._capture.get_metadata()
            if streamMetadata['src_vid_size'] != (0, 0):
                break
            time.sleep(0.001)  # wait for metadata to be available
        else:
            msg = (
                "Failed to obtain stream metadata (possibly caused by a device " 
                "already in use by other application)."
            )
            logging.error(msg)
            raise CameraNotReadyError(msg)

        self._metadata = streamMetadata  # store the metadata for later use

        # check if the camera metadata matches the requested settings
        if streamMetadata['src_vid_size'] != tuple(self._frameSize):
            raise CameraFrameSizeNotSupportedError(
                "Camera does not support the requested frame size "
                "{size}. Supported sizes are: {supportedSizes}".format(
                    size=self._frameSize,
                    supportedSizes=streamMetadata['src_vid_size']))

        # register stream in the class-level dictionary
        FFPyPlayerCameraDevice._streams[self._device] = self._capture

        if self._pollingTimerThread is None:
            self._setupAutoPolling()  # set up automatic polling of the camera stream
        
        # otherwise, create a new stream for this device
        FFPyPlayerCameraDevice._streams[self._device] = self

    @property
    def clientCount(self):
        """Get the number of clients registered to receive frames from this camera stream.

        Returns
        -------
        int
            Number of registered clients.

        """
        return len(self._cameraClients)

    def close(self):
        """Close the camera stream.
        
        This method should be called to close the camera stream and release any
        resources associated with it.

        Camera clients should unregister themselves before calling this method from 
        their own `close()` method.

        """
        if self._cameraClients:
            logging.debug(
                "Closed called for camera stream for device '{}' that has {} registered "
                "clients remaining. Keeping stream active.".format(
                    self._device, self.clientCount))
            return
            
        if self._capture is not None:
            # self._capture.set_pause(True)  # pause the stream
            self._capture.close_player()
            self._capture = None
        else:
            logging.debug(
                "Camera stream for device '{}' is already closed.".format(
                    self._device))

        if self._pollingTimerThread is not None:
            self._pollingTimerThread.cancel()
            self._pollingTimerThread = None
            logging.debug(
                "Stopped automatic polling of the camera stream for device '{}'.".format(
                    self._device))

    def _poll(self):
        """Poll the camera stream for new frames."""
        # Implementation for polling the camera stream
        self._getFrames()  # get the most recent frames

    def isSameDevice(self, other):
        """
        Check if this camera device is the same as another camera device.

        Parameters
        ----------
        other : FFPyPlayerCameraDevice
            Another camera device to compare with.

        Returns
        -------
        bool
            True if both devices are the same, False otherwise.
        """
        if isinstance(other, FFPyPlayerCameraDevice):
            return self.info['device'] == other.info['device']
        elif isinstance(other, dict) and 'device' in other:
            return self.info['device'] == other['device']

    @staticmethod
    def getAvailableDevices(best=False):
        """
        Get all available devices of this type.

        Parameters
        ----------
        best : bool
            If True, return only the best available frame rate/resolution for each device, rather 
            than returning all. Best available spec is chosen as the highest resolution with a 
            frame rate above 30fps (or just highest resolution, if none are over 30fps).

        Returns
        -------
        list[dict]
            List of dictionaries containing the parameters needed to initialise each device.
        """
        profiles = []
        # iterate through cameras
        for cams in FFPyPlayerCameraDevice.getCameras().values():
            # Skip devices with no available formats
            if not cams:
                continue
            # if requested, filter for best spec for each device
            if best:
                allCams = cams.copy()
                lastBest = {
                    'pixels': 0,
                    'frameRate': 0
                }
                bestResolution = None
                minFrameRate = max(28, min([cam.frameRate for cam in allCams]))
                for cam in allCams:
                    # summarise spec of this cam
                    current = {
                        'pixels': cam.frameSize[0] * cam.frameSize[1],
                        'frameRate': cam.frameRate
                    }
                    # store best frame rate as a fallback
                    if bestResolution is None or current['pixels'] > lastBest['pixels']:
                        bestResolution = cam
                    # if it's better than the last, set it as the only cam
                    if current['pixels'] > lastBest['pixels'] and current['frameRate'] >= minFrameRate:
                        cams = [cam]
                # if no cameras meet frame rate requirement, use one with best resolution
                cams = [bestResolution]
            # iterate through all (possibly filtered) cameras
            for cam in cams:
                # construct a dict profile from the CameraInfo object
                profiles.append({
                    'deviceName': cam.name,
                    'deviceClass': "psychopy.hardware.camera.CameraDevice",
                    'device': cam.index,
                    'captureLib': cam.cameraLib, 
                    'frameSize': cam.frameSize, 
                    'frameRate': cam.frameRate, 
                    'pixelFormat': cam.pixelFormat, 
                    'codecFormat': cam.codecFormat, 
                    'captureAPI': cam.cameraAPI
                })

        return profiles

    @staticmethod
    def getCameras(cameraLib=None):
        """Get a list of devices this interface can open.

        Parameters  
        ----------
        cameraLib : str or None
            Camera library to use for opening the camera stream. This can be 
            either 'ffpyplayer' or 'opencv'. If `None`, the default recommend 
            library is used.

        Returns
        -------
        dict 
            List of objects which represent cameras that can be opened by this
            interface. Pass any of these values to `device` to open a stream.

        """
        if cameraLib is None:
            cameraLib = CAMERA_LIB_FFPYPLAYER

        if cameraLib == CAMERA_LIB_FFPYPLAYER:
            global _cameraGetterFuncTbl
            systemName = platform.system()

            # lookup the function for the given platform
            getCamerasFunc = _cameraGetterFuncTbl.get(systemName, None)
            if getCamerasFunc is None:  # if unsupported
                raise OSError(
                    "Cannot get cameras, unsupported platform '{}'.".format(
                        systemName))

            return getCamerasFunc()


# ------------------------------------------------------------------------------
# Functions
#

def _getCameraInfoMacOS():
    """Get a list of capabilities associated with a camera attached to the 
    system.

    This is used by `getCameraInfo()` for querying camera details on MacOS.
    Don't call this function directly unless testing.

    Returns
    -------
    list of CameraInfo
        List of camera descriptors.

    """
    if platform.system() != 'Darwin':
        raise OSError(
            "Cannot query cameras with this function, platform not 'Darwin'.")

    # import objc  # may be needed in the future for more advanced stuff
    import AVFoundation as avf  # only works on MacOS
    import CoreMedia as cm

    # get a list of capture devices
    allDevices = avf.AVCaptureDevice.devices()

    # get video devices
    videoDevices = {}
    devIdx = 0
    for device in allDevices:
        devFormats = device.formats()
        if devFormats[0].mediaType() != 'vide':  # not a video device
            continue

        # camera details
        cameraName = device.localizedName()

        # found video formats
        supportedFormats = []
        for _format in devFormats:
            # get the format description object
            formatDesc = _format.formatDescription()

            # get dimensions in pixels of the video format
            dimensions = cm.CMVideoFormatDescriptionGetDimensions(formatDesc)
            frameHeight = dimensions.height
            frameWidth = dimensions.width

            # Extract the codec in use, pretty useless since FFMPEG uses its
            # own conventions, we'll need to map these ourselves to those
            # values
            codecType = cm.CMFormatDescriptionGetMediaSubType(formatDesc)

            # Convert codec code to a FourCC code using the following byte
            # operations.
            #
            # fourCC = ((codecCode >> 24) & 0xff,
            #           (codecCode >> 16) & 0xff,
            #           (codecCode >> 8) & 0xff,
            #           codecCode & 0xff)
            #
            pixelFormat4CC = ''.join(
                [chr((codecType >> bits) & 0xff) for bits in (24, 16, 8, 0)])

            # Get the range of supported framerate, use the largest since the
            # ranges are rarely variable within a format.
            frameRateRange = _format.videoSupportedFrameRateRanges()[0]
            frameRateMax = frameRateRange.maxFrameRate()
            # frameRateMin = frameRateRange.minFrameRate()  # don't use for now

            # Create a new camera descriptor
            thisCamInfo = CameraInfo(
                index=devIdx,
                name=cameraName,
                pixelFormat=pixelFormat4CC,  # macs only use pixel format
                codecFormat=CAMERA_NULL_VALUE,
                frameSize=(int(frameWidth), int(frameHeight)),
                frameRate=frameRateMax,
                cameraAPI=CAMERA_API_AVFOUNDATION,
                cameraLib="ffpyplayer",
            )

            supportedFormats.append(thisCamInfo)

            devIdx += 1

        # add to output dictionary
        videoDevices[cameraName] = supportedFormats

    return videoDevices


def _getCameraInfoWindows():
    """Get a list of capabilities for the specified associated with a camera
    attached to the system.

    This is used by `getCameraInfo()` for querying camera details on Windows.
    Don't call this function directly unless testing.

    Returns
    -------
    list of CameraInfo
        List of camera descriptors.

    """
    if platform.system() != 'Windows':
        raise OSError(
            "Cannot query cameras with this function, platform not 'Windows'.")

    # FFPyPlayer can query the OS via DirectShow for Windows cameras
    from ffpyplayer.tools import list_dshow_devices
    videoDevs, _, names = list_dshow_devices()

    # get all the supported modes for the camera
    videoDevices = {}

    # iterate over names
    devIndex = 0
    for devURI in videoDevs.keys():
        supportedFormats = []
        cameraName = names[devURI]
        for _format in videoDevs[devURI]:
            pixelFormat, codecFormat, frameSize, frameRateRng = _format
            _, frameRateMax = frameRateRng
            temp = CameraInfo(
                index=devIndex,
                name=cameraName,
                pixelFormat=pixelFormat,
                codecFormat=codecFormat,
                frameSize=frameSize,
                frameRate=frameRateMax,
                cameraAPI=CAMERA_API_DIRECTSHOW,
                cameraLib="ffpyplayer",
            )
            supportedFormats.append(temp)
            devIndex += 1

        videoDevices[names[devURI]] = supportedFormats

    return videoDevices


def _getCameraInfoLinux():
    """Get camera information on Linux systems.

    This is used by `getCameraInfo()` for querying camera details on Linux. Don't
    call this function directly unless testing. Requires `v4l2-ctl` to be installed
    on the host system. If the command is not found, an empty list is returned.

    Returns
    -------
    list of CameraInfo
        List of camera descriptors.
    
    """
    if platform.system() != 'Linux':
        raise OSError(
            "Cannot query cameras with this function, platform not 'Linux'.")

    # get video devices
    videoDevices = {}

    # find devices in /dev
    import glob
    devFiles = glob.glob('/dev/video*')

    if not devFiles:
        return videoDevices
    
    # sort the device files
    devFiles.sort()

    # call ffmpeg to get camera details
    import subprocess as sp
    for vf in devFiles:
        try:
            proc = sp.Popen(
                ['v4l2-ctl', '--list-formats-ext', '-d', vf],
                stderr=sp.PIPE,
                stdout=sp.PIPE
            )
            stdout, stderr = proc.communicate()
            output = stdout.decode('utf-8')
        except Exception as err:
            logging.error(f"Could not query cameras via v4l2-ctl: {err}")
            return videoDevices

        if not output:
            continue

        # parse the output
        lines = output.split('\n')
        lines = [line.strip() for line in lines]

        cameraModes = {}
        pixelFormat = None
        devIndex = 0
        for line in lines:
            if line.startswith('[') and line[1:2].isdigit():
                modeIdx = int(line[1:line.index(']')])
                # get the pixel format
                pixelFormat = line.split(' ')[1].strip("'").strip()
                cameraModes[modeIdx] = []
                continue

            if pixelFormat is None:  # no pixel format, skip
                continue
            
            # inside a valid mode description
            if line.startswith('Size:'):
                sizeStr = line.split(' ')[-1].strip()
                if 'x' in sizeStr:
                    width, height = sizeStr.split('x')
                    width = int(width.strip())
                    height = int(height.strip())
                else:
                    width = height = 0
                continue

            if line.startswith('Interval:'):
                fpsStr = line.split('(')[-1].rstrip(')').strip()
                fpsVal = float(fpsStr.split(' ')[0].strip())
                cameraModes[modeIdx].append(
                    (devIndex, pixelFormat, (width, height), fpsVal))
                devIndex += 1

        if not cameraModes:  # reject anything without modes
            continue

        # reformat into the output structure
        supportedFormats = []
        for modeIdx, modes in cameraModes.items():
            for mode in modes:
                devIndex, pixelFormat, frameSize, frameRate = mode

                pixelFormat = pixelFormat.lower()
                if pixelFormat == 'mjpg':
                    codecFormat = 'mjpg'
                    pixelFormat = None
                else:
                    codecFormat = None

                thisCamInfo = CameraInfo(
                    index=devIndex,
                    name=vf,
                    pixelFormat=pixelFormat,
                    codecFormat=codecFormat,    
                    frameSize=frameSize,
                    frameRate=frameRate,
                    cameraAPI=CAMERA_API_VIDEO4LINUX2,
                    cameraLib="ffpyplayer",
                )
                supportedFormats.append(thisCamInfo)

        videoDevices[vf] = supportedFormats

    return videoDevices


# Mapping for platform specific camera getter functions used by `getCameras`.
_cameraGetterFuncTbl = {
    'Darwin': _getCameraInfoMacOS,
    'Windows': _getCameraInfoWindows,
    'Linux': _getCameraInfoLinux, 
}


if __name__ == "__main__":
    pass
