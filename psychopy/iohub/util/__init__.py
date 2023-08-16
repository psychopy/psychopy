# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import sys
import os
import copy
import inspect
import warnings
import numpy
import numbers  # numbers.Integral is like (int, long) but supports Py3
import datetime
from ..errors import print2err, printExceptionDetailsToStdErr
import re
import collections.abc
import psychopy.plugins as plugins

########################
#
# .yaml read / write

try:
    from yaml import load as yload
    from yaml import dump as ydump
    from yaml import CLoader as yLoader, CDumper as yDumper
except ImportError:
    from yaml import Loader as yLoader, Dumper as yDumper

try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable


def saveConfig(config, dst_path):
    '''
    Saves a config dict to dst_path in YAML format.
    '''
    ydump(config, open(dst_path, 'w'), Dumper=yDumper)
    return os.path.exists(dst_path)


def readConfig(scr_path):
    '''
    Returns the config dict loaded from scr_path, which must be the path to
    a YAML file.
    '''
    return yload(open(scr_path, 'r'), Loader=yLoader)


def mergeConfigurationFiles(base_config_file_path, update_from_config_file_path, merged_save_to_path):
    """Merges two iohub configuration files into one and saves it to a file
    using the path/file name in merged_save_to_path."""
    base_config = yload(open(base_config_file_path, 'r'), Loader=yLoader)
    update_from_config = yload(
        open(
            update_from_config_file_path,
            'r'),
        Loader=yLoader)

    def merge(update, base):
        if isinstance(update, dict) and isinstance(base, dict):
            for k, v in base.items():
                if k not in update:
                    update[k] = v
                else:
                    if isinstance(update[k], list):
                        if isinstance(v, list):
                            v.extend(update[k])
                            update[k] = v
                        else:
                            update[k].insert(0, v)
                    else:
                        update[k] = merge(update[k], v)
        return update

    merged = merge(copy.deepcopy(update_from_config), base_config)
    ydump(merged, open(merged_save_to_path, 'w'), Dumper=yDumper)

    return merged

########################


def normjoin(*path_parts):
    """
    normjoin combines the following Python os.path functions in the following
    call order:
        * join
        * normcase
        * normpath

    Args:
        *path_parts (tuple): The tuple of path parts to pass to os.path.join.

    Returns:

    """
    return os.path.normpath(os.path.normcase(os.path.join(*path_parts)))


def addDirectoryToPythonPath(path_from_iohub_root, leaf_folder=''):
    from .. import IOHUB_DIRECTORY
    dir_path = os.path.join(
        IOHUB_DIRECTORY,
        path_from_iohub_root,
        sys.platform,
        'python{0}{1}'.format(
            *
            sys.version_info[
                0:2]),
        leaf_folder)
    if os.path.isdir(dir_path) and dir_path not in sys.path:
        sys.path.append(dir_path)
    else:
        print2err('Could not add path: ', dir_path)
        dir_path = None
    return dir_path


def module_path(local_function):
    """returns the module path without the use of __file__.

    Requires a function defined
    locally in the module. from http://stackoverflow.com/questions/729583/getting-file-path-of-imported-module

    """
    return os.path.abspath(inspect.getsourcefile(local_function))


def module_directory(local_function):
    mp = module_path(local_function)
    moduleDirectory, mname = os.path.split(mp)
    return moduleDirectory


def isIterable(o):
    return isinstance(o, Iterable)


# Get available device module paths
def getDevicePaths(device_name=""):
    """Get the paths to the iohub device modules that are available.

    Parameters
    ----------
    device_name : str, optional
        The name of the device to get the paths for. If not provided, all
        available device paths are returned.

    Returns
    -------
    list
        A list of tuples containing the path to the device module and the
        name of the device module.

    """
    from psychopy.iohub.devices import import_device

    # mdc - Changes here were made to support loading device modules from
    #       extensions. This allows support for devices that are not included in 
    #       the iohub package.

    def _getDevicePaths(iohub_device_path):
        """Look for device configuration files in the specified path.
        
        Parameters
        ----------
        iohub_device_path : str
            The path to the iohub device module.

        Returns
        -------
        list
            A list of tuples containing the path to the device module and the
            name of the device module. If empty, no device configuration files
            were found.
        
        """
        yaml_paths = []
        for root, _, files in os.walk(iohub_device_path):
            device_folder = None
            for file in files:
                if file == 'supported_config_settings.yaml':
                    device_folder = root
                    break
            if device_folder:
                for dfile in files:
                    if dfile.startswith("default_") and dfile.endswith('.yaml'):
                        yaml_paths.append((device_folder, dfile))
        
        return yaml_paths

    scs_yaml_paths = []  # stores the paths to the device config files
    plugins.refreshBundlePaths()  # make sure eyetracker external plugins are reachable 

    # get device paths for extant extensions
    try:  # tobii eyetrackers
        logging.debug("Looking for Tobii device configuration files...")
        import psychopy_eyetracker_tobii.tobii as tobii
        deviceConfig = _getDevicePaths(os.path.dirname(tobii.__file__))
        if deviceConfig:
            logging.debug("Found Tobii device configuration files.")
            scs_yaml_paths.extend(deviceConfig)
    except ImportError:
        pass  # do nothing

    try:  # for SR Research EyeLink
        logging.debug("Looking for SR Research EyeLink device configuration files...")
        import psychopy_eyetracker_sr_research.sr_research.eyelink as eyelink
        deviceConfig = _getDevicePaths(os.path.dirname(eyelink.__file__))
        if deviceConfig:
            logging.debug("Found SR Research EyeLink device configuration files.")
            scs_yaml_paths.extend(deviceConfig)
    except ImportError:
        pass 

    try:  # for Gazepoint eye trackers
        logging.debug("Looking for Gazepoint device configuration files...")
        import psychopy_eyetracker_gazepoint.gazepoint.gp3 as gp3
        deviceConfig = _getDevicePaths(os.path.dirname(gp3.__file__))
        if deviceConfig:
            logging.debug("Found Gazepoint device configuration files.")
            scs_yaml_paths.extend(deviceConfig)
    except ImportError:
        pass  

    try:  # for PupilLabs eye trackers
        logging.debug("Looking for PupilLabs device configuration files...")
        import psychopy_eyetracker_pupil_labs.pupil_labs.pupil_core as pupil_core
        deviceConfig = _getDevicePaths(os.path.dirname(pupil_core.__file__))
        if deviceConfig:
            logging.debug("Found PupilLabs device configuration files.")
            scs_yaml_paths.extend(deviceConfig)
    except ImportError:
        pass    
    
    # use this method for built-in devices
    iohub_device_path = module_directory(import_device)
    if device_name:
        iohub_device_path = os.path.join(
            iohub_device_path, device_name.replace('.', os.path.sep))

    deviceConfigs = _getDevicePaths(iohub_device_path)
    if deviceConfigs:
        scs_yaml_paths.extend(deviceConfigs)

    return scs_yaml_paths


def getDeviceDefaultConfig(device_name, builder_hides=True):
    """
    Return the default iohub config dictionary for the given device(s). The dictionary contains the
    (possibly nested) settings that should be displayed for the device (the dct item key) and the default value
    (the dict item value).

    Example:
        import pprint
        gp3_et_conf_defaults = getDeviceDefaultConfig('eyetracker.hw.gazepoint.gp3')
        pprint.pprint(gp3_et_conf_defaults)

    Output:
        {'calibration': {'target_delay': 0.5, 'target_duration': 1.25},
         'event_buffer_length': 1024,
         'manufacturer_name': 'GazePoint',
         'model_name': 'GP3',
         'monitor_event_types': ['BinocularEyeSampleEvent',
                                 'FixationStartEvent',
                                 'FixationEndEvent'],
         'network_settings': {'ip_address': '127.0.0.1', 'port': 4242},
         'runtime_settings': {'sampling_rate': 60},
         'save_events': True,
         'stream_events': True}
    """
    if device_name.endswith(".EyeTracker"):
        device_name = device_name[:-11]
    device_paths = getDevicePaths(device_name)

    device_configs = []
    for dpath, dconf in device_paths:
        dname, dconf_dict = list(readConfig(os.path.join(dpath, dconf)).items())[0]
        if builder_hides:
            to_hide = dconf_dict.get('builder_hides', [])
            for param in to_hide:
                if param.find('.') >= 0:
                    # it is a nested param
                    param_tokens = param.split('.')
                    cdict = dconf_dict
                    for pt in param_tokens[:-1]:
                        cdict = cdict.get(pt)
                    try:
                        del cdict[param_tokens[-1]]
                    except KeyError:
                        # key does not exist
                        pass
                    except TypeError:
                        pass
                else:
                    del dconf_dict[param]
        device_configs.append({dname: dconf_dict})
    # if len(device_configs) == 1:
    #     # simplify return value when only one device was requested
    #     return list(device_configs[0].values())[0]
    
    return device_configs


def getDeviceNames(device_name="eyetracker.hw", get_paths=True):
    """
    Return a list of iohub eye tracker device names, as would be used as keys to launchHubServer. If get_paths is true,
    return both device manufacturer name (for display in builder) as well as iohub device name.

    Example:
        eyetrackers = getDeviceNames()
        print(eyetrackers)

    Output:
        [('GazePoint', 'eyetracker.hw.gazepoint.gp3.EyeTracker'),
         ('MouseGaze', 'eyetracker.hw.mouse.EyeTracker'),
         ('SR Research Ltd', 'eyetracker.hw.sr_research.eyelink.EyeTracker'),
         ('Tobii Technology', 'eyetracker.hw.tobii.EyeTracker')]
    """
    names = []
    dconfigs = getDeviceDefaultConfig(device_name)
    for dcfg in dconfigs:
        d_path = tuple(dcfg.keys())[0]
        d_config = tuple(dcfg.values())[0]
        if get_paths is False:
            names.append(d_path)
        else:
            names.append((d_config.get('manufacturer_name'), d_path))
    return names

def getDeviceFile(device_name, file_name):
    """
    Returns the contents of file_name for the specified device. If file_name does not exist, None is returned.

    :param device_name: iohub device name
    :param: file_name: name of device yaml file to load
    :return: dict
    """
    if device_name.endswith(".EyeTracker"):
        device_name = device_name[:-11]
    device_paths = getDevicePaths(device_name)
    device_sconfigs = []
    for dpath, _ in device_paths:
        device_sconfigs.append(readConfig(os.path.join(dpath, file_name)))
    if len(device_sconfigs) == 1:
        # simplify return value when only one device was requested
        return list(device_sconfigs[0].values())[0]
    return device_sconfigs

def getDeviceSupportedConfig(device_name):
    """
    Returns the contents of the supported_config_settings.yaml for the specified device.

    :param device_name: iohub device name
    :return: dict
    """
    return getDeviceFile(device_name, 'supported_config_settings.yaml')

if sys.platform == 'win32':
    import pythoncom

    def win32MessagePump():
        """Pumps the Windows Message Queue so that PsychoPy
        Window(s) lock up if psychopy has not called
        the windows 'dispatch_events()' method recently.

        If you are not flipping regularly (say because you do not need
        to and do not want to block frequently, you can call this, which
        will not block waiting for messages, but only pump out what is
        in the queue already. On an i7 desktop, this call method takes
        between 10 and 90 usec.

        """
        if pythoncom.PumpWaitingMessages() == 1:
            raise KeyboardInterrupt()
else:
    def win32MessagePump():
        pass

# PsychoPy Window Hide / Show functions.
# Windows 10 and macOS have different code that needs to be called
# to show a second full screen window on top of an existing one, like
# is done by most eye tracker calibration routines.
def hideWindow(win, force=False):
    """
    If needed, hide / minimize the in.
    :param win: PsychoPy window instance
    :return: None
    """
    if force or sys.platform == 'win32':
        if win._isFullScr:
            win.winHandle.minimize()  # minimize the PsychoPy window
            win.winHandle.set_fullscreen(False)
    elif sys.platform == 'darwin':
        pass
    elif sys.platform == 'linux':
        # TODO: test on Linux, assuming same as macOS right now
        pass
    else:
        print("Warning: Unhandled sys.platform: ", sys.platform)

def showWindow(win, force=False):
    """
    If needed, hide / minimize the in.
    :param win: PsychoPy window instance
    :return: None
    """
    if force or sys.platform == 'win32':
        if win._isFullScr:
            win.winHandle.set_fullscreen(True)
            win.winHandle.maximize()  # maximize the PsychoPy window
    elif sys.platform == 'darwin':
        pass
    elif sys.platform == 'linux':
        # TODO: test on Linux, assuming same as macOS right now
        pass
    else:
        print("Warning: Unhandled sys.platform: ", sys.platform)

def createCustomCalibrationStim(win, cal_settings):
    """
    Create a custom calibration target using the CUSTOM eyetracker calibration settings. Returns an instance of
    target_attributes:custom:class_name class. If no custom target is defined, returns None.

    :param win: psychopy.visual.Window instance
    :param cal_settings: eye tracker calibration settings dictionary
    :return: visual stim instance
    """
    try:
        import importlib

        custom_target_settings = cal_settings.get('target_attributes').get('custom')
        TargetClass = getattr(importlib.import_module(custom_target_settings.get('module_name')),
                              custom_target_settings.get('class_name'))
        targ_kwargs = custom_target_settings.get('class_kwargs', {})
        targ_kwargs['win'] = win

        path_kwargs = ['filename', 'image']
        for pkwarg in path_kwargs:
            if pkwarg in targ_kwargs.keys():
                if not os.path.isfile(targ_kwargs.get(pkwarg)):
                    import psychopy
                    abspath = os.path.join(psychopy.iohub.EXP_SCRIPT_DIRECTORY, targ_kwargs.get(pkwarg))
                    if os.path.isfile(abspath):
                        targ_kwargs[pkwarg] = abspath

        # Instantiate the class (pass arguments to the constructor, if needed)
        return TargetClass(**targ_kwargs)
    except Exception:
        printExceptionDetailsToStdErr()
        print2err("Error creating custom iohub calibration graphics. Using default FixationTarget.")


def getObjectModuleAndClassName(obj, split=True):
    """
    Get the fully-qualified class name of a python object.
    """
    cls = type(obj)
    module = cls.__module__
    name = cls.__qualname__
    if module in ("__builtin__", "__main__"):
        module = None
    if split:
        return module, name
    if module is not None:
        name = module + "." + name
    return name


# Recursive updating of values from one dict into another if the key does not key exist.
# Supported nested dicts and uses deep copy when setting values in the
# target dict.
def updateDict(add_to, add_from):
    for key, value in add_from.items():
        if key not in add_to:
            add_to[key] = copy.deepcopy(value)
        elif isinstance(value, dict) and isinstance(add_to[key], dict):
            updateDict(add_to[key], value)


def updateSettings(d, u):
    for k, v in u.items():
        if type(k) == bytes:
            k = k.decode('UTF-8')
        if isinstance(v, collections.abc.Mapping):
            d[k] = updateSettings(d.get(k, {}), v)
        else:
            if type(v) == bytes:
                v = v.decode('UTF-8')
            d[k] = v
    return d


# Convert Camel to Snake variable name format
first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def convertCamelToSnake(name, lower_snake=True):
    s1 = first_cap_re.sub(r'\1_\2', name)
    if lower_snake:
        return all_cap_re.sub(r'\1_\2', s1).lower()
    return all_cap_re.sub(r'\1_\2', s1).upper()


# A couple date / time related utility functions

getCurrentDateTime = datetime.datetime.now
getCurrentDateTimeString = lambda: getCurrentDateTime().strftime("%Y-%m-%d %H:%M")


# rgb255 color utils
def hilo(a, b, c):
    if c < b:
        b, c = c, b
    if b < a:
        a, b = b, a
    if c < b:
        b, c = c, b
    return a + c


def complement(r, g, b):
    if r == g == b:
        # handle mono color
        if r >= 128:
            return 0, 0, 0
        return 255, 255, 255
    k = hilo(r, g, b)
    return tuple(k - u for u in (r, g, b))


class NumPyRingBuffer():
    """NumPyRingBuffer is a circular buffer implemented using a one dimensional
    numpy array on the backend. The algorithm used to implement the ring buffer
    behavior does not require any array copies to occur while the ring buffer
    is maintained, while at the same time allowing sequential element access
    into the numpy array using a subset of standard slice notation.

    When the circular buffer is created, a maximum size , or maximum
    number of elements,  that the buffer can hold *must* be specified. When
    the buffer becomes full, each element added to the buffer removes the oldest
    element from the buffer so that max_size is never exceeded.

    Items are added to the ring buffer using the classes append method.

    The current number of elements in the buffer can be retrieved using the
    getLength() method of the class.

    The isFull() method can be used to determine if
    the ring buffer has reached its maximum size, at which point each new element
    added will disregard the oldest element in the array.

    The getElements() method is used to retrieve the actual numpy array containing
    the elements in the ring buffer. The element in index 0 is the oldest remaining
    element added to the buffer, and index n (which can be up to max_size-1)
    is the the most recent element added to the buffer.

    Methods that can be called from a standard numpy array can also be called using the
    NumPyRingBuffer instance created. However Numpy module level functions will not accept
    a NumPyRingBuffer as a valid argument.

    To clear the ring buffer and start with no data in the buffer, without
    needing to create a new NumPyRingBuffer object, call the clear() method
    of the class.

    Example::

        ring_buffer=NumPyRingBuffer(10)

        for i in range(25):
            ring_buffer.append(i)
            print('-------')
            print('Ring Buffer Stats:')
            print('\tWindow size: ',len(ring_buffer))
            print('\tMin Value: ',ring_buffer.min())
            print('\tMax Value: ',ring_buffer.max())
            print('\tMean Value: ',ring_buffer.mean())
            print('\tStandard Deviation: ',ring_buffer.std())
            print('\tFirst 3 Elements: ',ring_buffer[:3])
            print('\tLast 3 Elements: ',ring_buffer[-3:])

    """

    def __init__(self, max_size, dtype=numpy.float32):
        self._dtype = dtype
        self._npa = numpy.empty(max_size * 2, dtype=dtype)
        self.max_size = max_size
        self._index = 0

    def append(self, element):
        """Add element e to the end of the RingBuffer. The element must match
        the numpy data type specified when the NumPyRingBuffer was created. By
        default, the RingBuffer uses float32 values.

        If the Ring Buffer is full, adding the element to the end of the array
        removes the currently oldest element from the start of the array.

        :param numpy.dtype element: An element to add to the RingBuffer.
        :returns None:

        """
        i = self._index
        self._npa[i % self.max_size] = element
        self._npa[(i % self.max_size) + self.max_size] = element
        self._index += 1

    def getElements(self):
        """Return the numpy array being used by the RingBuffer, the length of
        which will be equal to the number of elements added to the list, or the
        last max_size elements added to the list. Elements are in order of
        addition to the ring buffer.

        :param None:
        :returns numpy.array: The array of data elements that make up the Ring Buffer.

        """
        return self._npa[
            self._index %
            self.max_size:(
                self._index %
                self.max_size) + self.max_size]

    def isFull(self):
        """Indicates if the RingBuffer is at it's max_size yet.

        :param None:
        :returns bool: True if max_size or more elements have been added to the RingBuffer; False otherwise.

        """
        return self._index >= self.max_size

    def clear(self):
        """Clears the RingBuffer. The next time an element is added to the
        buffer, it will have a size of one.

        :param None:
        :returns None:

        """
        self._index = 0

    def __setitem__(self, indexs, v):
        if isinstance(indexs, (list, tuple)):
            for i in indexs:
                if isinstance(i, numbers.Integral):
                    i = i + self._index
                    self._npa[i % self.max_size] = v
                    self._npa[(i % self.max_size) + self.max_size] = v
                elif isinstance(i, slice):
                    istart = indexs.start
                    if istart is None:
                        istart = 0
                    istop = indexs.stop
                    if indexs.stop is None:
                        istop = 0
                    start = istart + self._index
                    stop = istop + self._index
                    self._npa[
                        slice(
                            start %
                            self.max_size,
                            stop %
                            self.max_size,
                            i.step)] = v
                    self._npa[
                        slice(
                            (start %
                             self.max_size) + self.max_size, (stop %
                                                              self.max_size) + self.max_size, i.step)] = v
        elif isinstance(indexs, numbers.Integral):
            i = indexs + self._index
            self._npa[i % self.max_size] = v
            self._npa[(i % self.max_size) + self.max_size] = v
        elif isinstance(indexs, slice):
            istart = indexs.start
            if istart is None:
                istart = 0
            istop = indexs.stop
            if indexs.stop is None:
                istop = 0
            start = istart + self._index
            stop = istop + self._index
            self._npa[
                slice(
                    start %
                    self.max_size,
                    stop %
                    self.max_size,
                    indexs.step)] = v
            self._npa[
                slice(
                    (start %
                     self.max_size) +
                    self.max_size,
                    (stop %
                     self.max_size) +
                    self.max_size,
                    indexs.step)] = v
        else:
            raise TypeError()

    def __getitem__(self, indexs):
        current_array = self.getElements()
        if isinstance(indexs, (list, tuple)):
            rarray = []
            for i in indexs:
                if isinstance(i, int):
                    rarray.append(current_array[i])
                elif isinstance(i, slice):
                    rarray.extend(current_array[i])
            return numpy.asarray(rarray, dtype=self._dtype)
        elif isinstance(indexs, (int, slice)):
            return current_array[indexs]
        else:
            raise TypeError()

    def __getattr__(self, a):
        if self._index < self.max_size:
            return getattr(self._npa[:self._index], a)
        return getattr(
            self._npa[
                self._index %
                self.max_size:(
                    self._index %
                    self.max_size) + self.max_size], a)

    def __len__(self):
        if self.isFull():
            return self.max_size
        return self._index

###############################################################################
#
# Generate a set of points in a NxM grid. Useful for creating calibration target positions,
# or grid spaced fixation point positions that can be used for validation / fixation accuracy.
#


def generatedPointGrid(pixel_width, pixel_height, width_scalar=1.0,
                       height_scalar=1.0, horiz_points=5, vert_points=5):

    swidth = pixel_width * width_scalar
    sheight = pixel_height * height_scalar

    # center 0 on screen center
    x, y = numpy.meshgrid(numpy.linspace(-swidth / 2.0, swidth / 2.0, horiz_points),
                          numpy.linspace(-sheight / 2.0, sheight / 2.0, vert_points))
    points = numpy.column_stack((x.flatten(), y.flatten()))

    return points


# Rotate a set of points in 2D
#
# Rotate a set of n 2D points in the form [[x1,x1],[x2,x2],...[xn,xn]]
# around the 2D point origin (x0,y0), by ang radians.
# Returns the rotated point list.
#
# FROM:
# http://gis.stackexchange.com/questions/23587/how-do-i-rotate-the-polygon-about-an-anchor-point-using-python-script


def rotate2D(pts, origin, ang=None):
    '''pts = {} Rotates points(nx2) about center cnt(2) by angle ang(1) in radian'''
    if ang is None:
        ang = numpy.pi / 4
    return numpy.dot(pts - origin,
                     numpy.array([[numpy.cos(ang),
                                   numpy.sin(ang)],
                                  [-numpy.sin(ang),
                                   numpy.cos(ang)]])) + origin
