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
    'getKeyboards',
    'getSerialPorts',
    # 'getParallelPorts',
    'systemProfilerMacOS'
]

# Keep imports to a minimum here! We don't want to import the whole stack to
# simply populate a drop-down list. Try to keep platform-specific imports inside
# the functions, not on the top-level scope for this module.
import platform
# if platform.system() == 'Windows':
#     # this has to be imported here before anything else
#     import winrt.windows.devices.enumeration as windows_devices
import sys
import glob
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

SERIAL_MAX_ENUM_PORTS = 32  # can be as high as 256 on Win32, not used on Unix


# ------------------------------------------------------------------------------
# Detect VMs (for GitHub Actions, Travis...)
#

def isVM_CI():
    """Attempts to detect TravisCI or GitHub actions virtual machines os.env

    Returns the type of VM ('travis', 'github', 'conda') being run or None
    """
    import os
    if (str(os.environ.get('GITHUB_WORKFLOW')) != 'None'):
        return 'github'
    elif ("{}".format(os.environ.get('TRAVIS')).lower() == 'true'):
        return 'travis'
    elif ("{}".format(os.environ.get('CONDA')).lower() == 'true'):
        return 'conda'

# ------------------------------------------------------------------------------
# Audio playback and capture devices
#

def getAudioDevices():
    """Get all audio devices.

    This function gets all audio devices attached to the system, either playback
    or capture. Uses the `psychtoolbox` library to obtain the relevant
    information.

    This command is supported on Windows, MacOSX and Linux. On Windows, WASAPI
    devices are preferred to achieve precise timing and will be returned by
    default. To get all audio devices (including non-WASAPI ones), set the
    preference `audioForceWASAPI` to `False`.

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

    To determine whether something is a playback or capture device, check the
    number of output and input channels, respectively::

        # determine if a device is for audio capture
        isCapture = allDevs['MacBook Pro Microphone']['inputChannels'] > 0

        # determine if a device is for audio playback
        isPlayback = allDevs['MacBook Pro Microphone']['outputChannels'] > 0

    You may also call :func:`getAudioCaptureDevices` and
    :func:`getAudioPlaybackDevices` to get just audio capture and playback
    devices.

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

    This command is supported on Windows, MacOSX and Linux. On Windows, WASAPI
    devices are preferred to achieve precise timing and will be returned by
    default. To get all audio capture devices (including non-WASAPI ones), set
    the preference `audioForceWASAPI` to `False`.

    Uses the `psychtoolbox` library to obtain the relevant information.

    Returns
    -------
    dict
        Dictionary where the keys are devices names and values are mappings
        whose fields contain information about the capture device. See
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

    This command is supported on Windows, MacOSX and Linux. On Windows, WASAPI
    devices are preferred to achieve precise timing and will be returned by
    default. To get all audio playback devices (including non-WASAPI ones), set
    the preference `audioForceWASAPI` to `False`.

    Uses the `psychtoolbox` library to obtain the relevant information.

    Returns
    -------
    dict
        Dictionary where the keys are devices names and values are mappings
        whose fields contain information about the playback device. See
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
    Don't call this function directly unless testing. Requires `AVFoundation`
    and `CoreMedia` libraries.

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


# def _getCameraInfoWindowsWinRT():
#     """Get a list of capabilities for the specified associated with a camera
#     attached to the system.
#
#     This is used by `getCameraInfo()` for querying camera details on Windows.
#     Don't call this function directly unless testing. Requires `ffpyplayer`
#     to use this function.
#
#     Returns
#     -------
#     list of CameraInfo
#         List of camera descriptors.
#
#     """
#     if platform.system() != 'Windows':
#         raise OSError(
#             "Cannot query cameras with this function, platform not 'Windows'.")
#
#     import asyncio
#
#     async def findCameras():
#         """Get all video camera devices."""
#         videoDeviceClass = 4  # for video capture devices
#         return await windows_devices.DeviceInformation.find_all_async(
#             videoDeviceClass)
#
#     # interrogate the OS using WinRT to acquire camera data
#     foundCameras = asyncio.run(findCameras())
#
#     # get all the supported modes for the camera
#     videoDevices = {}
#
#     # iterate over cameras
#     for idx in range(foundCameras.size):
#         try:
#             cameraData = foundCameras.get_at(idx)
#         except RuntimeError:
#             continue
#
#         # get required fields
#         cameraName = cameraData.name
#
#         videoDevices[cameraName] = {
#             'index': idx,
#             'name': cameraName
#         }
#
#     return videoDevices


def _getCameraInfoWindows():
    """Get a list of capabilities for the specified associated with a camera
    attached to the system.

    This is used by `getCameraInfo()` for querying camera details on Windows.
    Don't call this function directly unless testing. Requires `ffpyplayer`
    to use this function.

    Returns
    -------
    list of CameraInfo
        List of camera descriptors.

    """
    if platform.system() != 'Windows':
        raise OSError(
            "Cannot query cameras with this function, platform not 'Windows'.")

    # import this to get camera details
    # NB - In the future, we should consider using WinRT to query this info
    # to avoid the ffpyplayer dependency.
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
# We're doing this to allow for plugins to add support for cameras on other
# platforms.
_cameraGetterFuncTbl = {
    'Darwin': _getCameraInfoMacOS,
    'Windows': _getCameraInfoWindows
}


def getCameras():
    """Get information about installed cameras and their formats on this system.

    The command presently only works on Window and MacOSX. Linux support for
    cameras is not available yet.

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
# Keyboards
#

def getKeyboards():
    """Get information about attached keyboards.

    This command works on Windows, MacOSX and Linux.

    Returns
    -------
    dict
        Dictionary where the keys are device names and values are mappings
        whose fields contain information about that device. See the *Examples*
        section for field names.

    Notes
    -----
    * Keyboard names are generated (taking the form of "Generic Keyboard n") if
      the OS does not report the name.

    Examples
    --------
    Get keyboards attached to this system::

        installedKeyboards = getKeyboards()

    Running the previous command on an Apple MacBook Pro (2022) returns the
    following dictionary::

        {
            'TouchBarUserDevice': {
                'usagePageValue': 1,
                'usageValue': 6,
                'usageName': 'Keyboard',
                'index': 4,
                'transport': '',
                'vendorID': 1452,
                'productID': 34304,
                'version': 0.0,
                'manufacturer': '',
                'product': 'TouchBarUserDevice',
                'serialNumber': '',
                'locationID': 0,
                'interfaceID': -1,
                'totalElements': 1046,
                'features': 0,
                'inputs': 1046,
                'outputs': 0,
                'collections': 1,
                'axes': 0,
                'buttons': 0,
                'hats': 0,
                'sliders': 0,
                'dials': 0,
                'wheels': 0,
                'touchDeviceType': -1,
                'maxTouchpoints': -1},
            'Generic Keyboard 0': {
                'usagePageValue': 1,
                'usageValue': 6,
                'usageName': 'Keyboard',
                'index': 13,
                # snip ...
                'dials': 0,
                'wheels': 0,
                'touchDeviceType': -1,
                'maxTouchpoints': -1
            }
        }

    """
    # use PTB to query keyboards, might want to also use IOHub at some point
    from psychtoolbox import hid

    # use PTB to query for keyboards
    indices, names, keyboards = hid.get_keyboard_indices()

    toReturn = {}
    if not indices:
        return toReturn  # just return if no keyboards found

    # ensure these are all the same length
    assert len(indices) == len(names) == len(keyboards), \
        "Got inconsistent array length from `get_keyboard_indices()`"

    missingNameIdx = 0  # for keyboard with empty names
    for i, kbIdx in enumerate(indices):
        name = names[i]
        if not name:
            name = ' '.join(('Generic Keyboard', str(missingNameIdx)))
            missingNameIdx += 1

        keyboard = keyboards[i]

        # reformat values since PTB returns everything as a float
        for key, val in keyboard.items():
            if isinstance(val, float) and key not in ('version',):
                keyboard[key] = int(val)

        toReturn[name] = keyboard

    return toReturn


# ------------------------------------------------------------------------------
# Connectivity
#

def getSerialPorts():
    """Get serial ports attached to this system.

    Serial ports are used for inter-device communication using the RS-232/432
    protocol. This function gets a list of available ports and their default
    configurations as specified by the OS. Ports that are in use by another
    process are not returned.

    This command is supported on Windows, MacOSX and Linux. On Windows, all
    available ports are returned regardless if anything is connected to them,
    so long as they aren't in use. On Unix(-likes) such as MacOSX and Linux,
    port are only returned if there is a device attached and is not being
    accessed by some other process. MacOSX and Linux also have no guarantee port
    names are persistent, where a physical port may not always be assigned the
    same name or enum index when a device is connected or after a system
    reboot.

    Returns
    -------
    dict
        Mapping (`dict`) where keys are serial port names (`str`) and values
        are mappings of the default settings of the port (`dict`). See
        *Examples* below for the format of the returned data.

    Examples
    --------
    Getting available serial ports::

        allPorts = getSerialPorts()

    On a MacBook Pro (2022) with an Arduino Mega (2560) connected to the USB-C
    port, the following dictionary is returned::

        {
            '/dev/cu.Bluetooth-Incoming-Port': {
                'index': 0,
                'port': '/dev/cu.Bluetooth-Incoming-Port',
                'baudrate': 9600,
                'bytesize': 8,
                'parity': 'N',
                'stopbits': 1,
                'xonxoff': False,
                'rtscts': False,
                'dsrdtr': False
            },
            '/dev/cu.usbmodem11101': {
                'index': 1,
                # ... snip ...
                'dsrdtr': False
            },
            '/dev/tty.Bluetooth-Incoming-Port': {
                'index': 2,
                # ... snip ...
            },
            '/dev/tty.usbmodem11101': {
                'index': 3,
                # ... snip ...
            }
        }

    """
    try:
        import serial  # pyserial
    except ImportError:
        raise ImportError("Cannot import `pyserial`, check your installation.")

    # get port names
    thisSystem = platform.system()
    if thisSystem == 'Windows':
        portNames = [
            'COM{}'.format(i + 1) for i in range(SERIAL_MAX_ENUM_PORTS)]
    elif thisSystem == 'Darwin':
        portNames = glob.glob('/dev/tty.*') + glob.glob('/dev/cu.*')
        portNames.sort()  # ensure we get things back in the same order
    elif thisSystem == 'Linux' or thisSystem == 'Linux2':
        portNames = glob.glob('/dev/tty[A-Za-z]*')
        portNames.sort()  # ditto
    else:
        raise EnvironmentError(
            "System '{}' is not supported by `getSerialPorts()`".format(
                thisSystem))

    # enumerate over ports now that we have the names
    portEnumIdx = 0
    toReturn = {}
    for name in portNames:
        try:
            with serial.Serial(name) as ser:
                portConf = {   # port information dict
                    'index': portEnumIdx,
                    'port': ser.port,
                    'baudrate': ser.baudrate,
                    'bytesize': ser.bytesize,
                    'parity': ser.parity,
                    'stopbits': ser.stopbits,
                    # 'timeout': ser.timeout,
                    # 'writeTimeout': ser.write_timeout,
                    # 'interByteTimeout': ser.inter_byte_timeout,
                    'xonxoff': ser.xonxoff,
                    'rtscts': ser.rtscts,
                    'dsrdtr': ser.dsrdtr,
                    # 'rs485_mode': ser.rs485_mode
                }
                toReturn[name] = portConf
                portEnumIdx += 1
        except (OSError, serial.SerialException):
            # no port found with `name` or cannot be opened
            pass

    return toReturn


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
