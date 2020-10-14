# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import division

from builtins import object
import sys
import os
import inspect
import warnings
import numpy
import collections
import numbers  # numbers.Integral is like (int, long) but supports Py3
import datetime

from ..errors import print2err

########################
#
# .yaml read / write

try:
    from yaml import load as yload
    from yaml import dump as ydump
    from yaml import CLoader as yLoader, CDumper as yDumper
except ImportError:
    from yaml import Loader as yLoader, Dumper as yDumper

# Only turn on converting all strings to unicode by the YAML loader
# if running Python 2.7 or higher. 2.6 does not seem to like unicode dict keys.
# ???
#
if sys.version_info[0] != 2 or sys.version_info[1] >= 7:
    def construct_yaml_unistr(self, node):
        return self.construct_scalar(node)
    yLoader.add_constructor(u'tag:yaml.org,2002:str', construct_yaml_unistr)


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
    return isinstance(o, collections.Iterable)

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

########################
#
# Recursive updating of values from one dict into another if the key does not key exist.
# Supported nested dicts and uses deep copy when setting values in the
# target dict.
import copy


def updateDict(add_to, add_from):
    for key, value in add_from.items():
        if key not in add_to:
            add_to[key] = copy.deepcopy(value)
        elif isinstance(value, dict) and isinstance(add_to[key], dict):
            updateDict(add_to[key], value)


########################
#
# Convert Camel to Snake variable name format

import re
first_cap_re = re.compile('(.)([A-Z][a-z]+)')
all_cap_re = re.compile('([a-z0-9])([A-Z])')


def convertCamelToSnake(name, lower_snake=True):
    s1 = first_cap_re.sub(r'\1_\2', name)
    if lower_snake:
        return all_cap_re.sub(r'\1_\2', s1).lower()
    return all_cap_re.sub(r'\1_\2', s1).upper()

###############################################################################
#
## A couple date / time related utility functions
#

getCurrentDateTime = datetime.datetime.now
getCurrentDateTimeString = lambda : getCurrentDateTime().strftime("%Y-%m-%d %H:%M")

########################

class NumPyRingBuffer(object):
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
    a NumPyRingBuffer as a valid arguement.

    To clear the ring buffer and start with no data in the buffer, without
    needing to create a new NumPyRingBuffer object, call the clear() method
    of the class.

    Example::

        ring_buffer=NumPyRingBuffer(10)

        for i in xrange(25):
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

###############################################################################
#
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

###############################################################################
#
# Verify the validity of a given Python package release number
#

try:
    from verlib import suggest_normalized_version, NormalizedVersion

    def validate_version(version):
        rversion = suggest_normalized_version(version)
        if rversion is None:
            raise ValueError('Cannot work with "%s"' % version)
        if rversion != version:
            warnings.warn('"%s" is not a normalized version.\n'
                          'It has been transformed into "%s" '
                          'for interoperability.' % (version, rversion))
        return NormalizedVersion(rversion)

except Exception:
    # just use the version provided if verlib is not installed.
    validate_version = lambda version: version
