#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Tools for interacting with the operating system and getting information about
# the system.
#

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = [
    'CAMERA_API_AVFOUNDATION',
    'CAMERA_API_DIRECTSHOW',
    'CAMERA_API_UNKNOWN',
    'CAMERA_API_NULL',
    'CAMERA_LIB_FFPYPLAYER',
    'CAMERA_LIB_UNKNOWN',
    'CAMERA_LIB_NULL',
    'CAMERA_UNKNOWN_VALUE',
    'CAMERA_NULL_VALUE',
    'AUDIO_LIBRARY_PTB',
    'getCameras',
    'getAudioDevices',
    'getAudioCaptureDevices',
    'getAudioPlaybackDevices',
    'systemProfilerMacOS'
]

# Keep imports to a minimum here! We don't want to import the whole stack to
# simply populate a drop-down list. Try to keep platform-specific imports inside
# the functions, not on the top-level scope for this module.
import sys
import platform
import subprocess as sp
from psychopy.preferences import prefs

# ------------------------------------------------------------------------------
# Constants
#

CAMERA_API_AVFOUNDATION = u'AVFoundation'  # mac
CAMERA_API_DIRECTSHOW = u'DirectShow'      # windows
# CAMERA_API_VIDEO4LINUX = u'Video4Linux'  # linux
# CAMERA_API_OPENCV = u'OpenCV'            # opencv, cross-platform API
CAMERA_API_UNKNOWN = u'Unknown'            # unknown API
CAMERA_API_NULL = u'Null'                  # empty field
CAMERA_LIB_FFPYPLAYER = u'FFPyPlayer'
CAMERA_LIB_UNKNOWN = u'Unknown'
CAMERA_LIB_NULL = u'Null'
CAMERA_UNKNOWN_VALUE = u'Unknown'  # fields where we couldn't get a value
CAMERA_NULL_VALUE = u'Null'  # fields where we couldn't get a value

# audio library identifiers
AUDIO_LIBRARY_PTB = 'ptb'  # PsychPortAudio from Psychtoolbox


# ------------------------------------------------------------------------------
# Audio playback and capture devices
#

def getAudioDevices():
    """Get all audio devices.

    This function gets all audio devices attached to the system, either playback
    or capture.

    This command is supported on Windows, MacOSX and Linux. On Windows, WASAPI
    devices are preferred and will only be returned by default.

    Returns
    -------
    dict
        Dictionary where the keys are devices names and values are mappings
        whose fields contain information about the device.

    Examples
    --------
    Get audio devices installed on this system::

        allDevs = getAudioDevices()

    The following dictionary is returned by the above command when called on an
    Apple MacBook Pro (2022)::

        {
            'MacBook Pro Microphone': {   # audio capture device
                'index': 0,
                'name': 'MacBook Pro Microphone',
                'hostAPI': 'Core Audio',
                'outputChannels': 0,
                'outputLatency': (0.01, 0.1),
                'inputChannels': 1,
                'inputLatency': (0.0326984126984127, 0.04285714285714286),
                'defaultSampleRate': 44100.0,
                'audioLib': 'ptb'
            },
            'MacBook Pro Speakers': {    # audio playback device
                'index': 1,
                'name': 'MacBook Pro Speakers',
                'hostAPI': 'Core Audio',
                'outputChannels': 2,
                'outputLatency': (0.008480725623582767, 0.018639455782312925),
                'inputChannels': 0,
                'inputLatency': (0.01, 0.1),
                'defaultSampleRate': 44100.0,
                'audioLib': 'ptb'
            }
        }

    """
    # use the PTB backend for audio
    import psychtoolbox.audio as audio

    try:
        enforceWASAPI = bool(prefs.hardware["audioForceWASAPI"])
    except KeyError:
        enforceWASAPI = True  # use default if option not present in settings

    # query PTB for devices
    if enforceWASAPI and sys.platform == 'win32':
        allDevs = audio.get_devices(device_type=13)
    else:
        allDevs = audio.get_devices()

    # make sure we have an array of descriptors
    allDevs = [allDevs] if isinstance(allDevs, dict) else allDevs

    # format the PTB dictionary to PsychoPy standards
    toReturn = {}
    for dev in allDevs:
        thisAudioDev = {
            'index': int(dev['DeviceIndex']),
            'name': dev['DeviceName'],
            'hostAPI': dev['HostAudioAPIName'],
            'outputChannels': int(dev['NrOutputChannels']),
            'outputLatency': (
                dev['LowOutputLatency'], dev['HighOutputLatency']),
            'inputChannels': int(dev['NrInputChannels']),
            'inputLatency': (
                dev['LowInputLatency'], dev['HighInputLatency']),
            'defaultSampleRate': dev['DefaultSampleRate'],
            'audioLib': AUDIO_LIBRARY_PTB
        }

        toReturn[thisAudioDev['name']] = thisAudioDev

    return toReturn


def getAudioCaptureDevices():
    """Get audio capture devices (i.e. microphones) installed on the system.

    Returns
    -------
    dict
        Dictionary where the keys are devices names and values are mappings
        whose fields contain information about the device. See
        :func:`getAudioDevices()` examples to see the format of the output.

    """
    allDevices = getAudioDevices()  # gat all devices

    inputDevices = {}  # dict for input devices

    if not allDevices:
        return inputDevices  # empty

    # filter for capture devices
    for name, devInfo in allDevices.items():
        if devInfo['inputChannels'] < 1:
            continue

        inputDevices[name] = devInfo  # is capture device

    return inputDevices


def getAudioPlaybackDevices():
    """Get audio playback devices (i.e. speakers) installed on the system.

    Returns
    -------
    dict
        Dictionary where the keys are devices names and values are mappings
        whose fields contain information about the device. See
        :func:`getAudioDevices()` examples to see the format of the output.

    """
    allDevices = getAudioDevices()  # gat all devices

    outputDevices = {}  # dict for output devices

    if not allDevices:
        return outputDevices  # empty

    # filter for playback devices
    for name, devInfo in allDevices.items():
        if devInfo['outputChannels'] < 1:
            continue

        outputDevices[name] = devInfo  # is playback device

    return outputDevices


# ------------------------------------------------------------------------------
# Cameras
#

def _getCameraInfoMacOS():
    """Get a list of capabilities for the specified associated with a camera
    attached to the system.

    This is used by `getCameraInfo()` for querying camera details on *MacOS*.
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
            thisCamInfo = {
                'index': devIdx,
                'name': cameraName,
                'pixelFormat': pixelFormat4CC,
                'codecFormat': CAMERA_NULL_VALUE,
                'frameSize': (int(frameWidth), int(frameHeight)),
                'frameRate': frameRateMax,
                'cameraAPI': CAMERA_API_AVFOUNDATION

            }

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

    # import this to get camera details
    from ffpyplayer.tools import list_dshow_devices

    # FFPyPlayer can query the OS via DirectShow for Windows cameras
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

            thisCamInfo = {
                'index': devIndex,
                'name': cameraName,
                'pixelFormat': pixelFormat,
                'codecFormat': codecFormat,
                'frameSize': frameSize,
                'frameRate': frameRateMax,
                'cameraAPI': CAMERA_API_DIRECTSHOW

            }
            supportedFormats.append(thisCamInfo)
            devIndex += 1

        videoDevices[names[devURI]] = supportedFormats

    return videoDevices


# Mapping for platform specific camera getter functions used by `getCameras`.
_cameraGetterFuncTbl = {
    'Darwin': _getCameraInfoMacOS,
    'Windows': _getCameraInfoWindows
}


def getCameras():
    """Get information about installed cameras and their formats on this system.

    Returns
    -------
    dict
        Mapping where camera names (`str`) are keys and values are and array of
        `CameraInfo` objects.

    """
    systemName = platform.system()  # get the system name

    # lookup the function for the given platform
    getCamerasFunc = _cameraGetterFuncTbl.get(systemName, None)
    if getCamerasFunc is None:  # if unsupported
        raise OSError(
            "Cannot get cameras, unsupported platform '{}'.".format(
                systemName))

    return getCamerasFunc()


# ------------------------------------------------------------------------------
# Miscellaneous utilities
#

def systemProfilerMacOS(dataTypes=None, detailLevel='basic', timeout=180):
    """Call the MacOS system profiler and return data in a JSON format.

    Parameters
    ----------
    dataTypes : str, list or None
        Identifier(s) for the data to retrieve. All data types available will
        be returned if `None`. See output of shell command `system_profiler
        -listDataTypes` for all possible values. Specifying data types also
        speeds up the time it takes for this function to return as superfluous
        information is not queried.
    detailLevel : int or str
        Level of detail for the report. Possible values are `'mini'`, `'basic'`,
        or `'full'`. Note that increasing the level of detail will expose
        personally identifying information in the resulting report. Best
        practice is to use the lowest level of detail needed to obtain the
        desired information, or use `dataTypes` to limit what information is
        returned.
    timeout : float or int
        Amount of time to spend gathering data in seconds. Default is 180
        seconds, while specifying 0 means no timeout.

    Returns
    -------
    str
        Result of the `system_profiler` call as a JSON formatted string. You can
        pass the string to a JSON library to parse out what information is
        desired.

    Examples
    --------
    Get details about cameras attached to this system::

        dataTypes = "SPCameraDataType"  # data to query
        systemReportJSON = systemProfilerMacOS(dataTypes, detailLevel='basic')
        # >>> print(systemReportJSON)
        # {
        #   "SPCameraDataType" : [
        #     ...
        #   ]
        # }

    Parse the result using a JSON library::

        import json
        systemReportJSON = systemProfilerMacOS(
            "SPCameraDataType", detailLevel='mini')
        cameraInfo = json.loads(systemReportJSON)
        # >>> print(cameraInfo)
        # {'SPCameraDataType': [{'_name': 'Live! Cam Sync 1080p',
        # 'spcamera_model-id': 'UVC Camera VendorID_1054 ProductID_16541',
        # 'spcamera_unique-id': '0x2200000041e409d'}]

    """
    if platform.system() != 'Darwin':
        raise OSError(
            "Cannot call `systemProfilerMacOS`, detected OS is not 'darwin'."
        )

    if isinstance(dataTypes, (tuple, list)):
        dataTypesStr = " ".join(dataTypes)
    elif isinstance(dataTypes, str):
        dataTypesStr = dataTypes
    elif dataTypes is None:
        dataTypesStr = ""
    else:
        raise TypeError(
            "Expected type `list`, `tuple`, `str` or `NoneType` for parameter "
            "`dataTypes`")

    if detailLevel not in ('mini', 'basic', 'full'):
        raise ValueError(
            "Value for parameter `detailLevel` should be one of 'mini', 'basic'"
            " or 'full'."
        )

    # build the command
    shellCmd = ['system_profiler']
    if dataTypesStr:
        shellCmd.append(dataTypesStr)

    shellCmd.append('-json')  # ask for report in JSON formatted string
    shellCmd.append('-detailLevel')  # set detail level
    shellCmd.append(detailLevel)
    shellCmd.append('-timeout')  # set timeout
    shellCmd.append(str(timeout))

    # call the system profiler
    systemProfilerCall = sp.Popen(
        shellCmd,
        stdout=sp.PIPE)
    systemProfilerRet = systemProfilerCall.communicate()[0]  # bytes

    # We're going to need to handle errors from this command at some point, for
    # now we're leaving that up to the user.

    return systemProfilerRet.decode("utf-8")  # convert to string


if __name__ == "__main__":
    pass
