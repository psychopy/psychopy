# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).

"""Wrapper for iViewXAPI.h.

Generated with:
ctypesgen.py -a --insert-file=prepend_contents.py --cpp=cl -E -l iViewXAPI -o iViewXAPI.py iViewXAPI.h

Do not modify this file.

"""

__docformat__ = 'restructuredtext'

# Begin preamble

import ctypes
import os
import sys
from ctypes import *

_int_types = (c_int16, c_int32)
if hasattr(ctypes, 'c_int64'):
    # Some builds of ctypes apparently do not have c_int64
    # defined; it's a pretty good bet that these builds do not
    # have 64-bit pointers.
    _int_types += (c_int64,)
for t in _int_types:
    if sizeof(t) == sizeof(c_size_t):
        c_ptrdiff_t = t
del t
del _int_types


class c_void(Structure):
    # c_void_p is a buggy return type, converting to int, so
    # POINTER(None) == c_void_p is actually written as
    # POINTER(c_void), so it can be treated as a real pointer.
    _fields_ = [('dummy', c_int)]


def POINTER(obj):
    p = ctypes.POINTER(obj)

    # Convert None to a real NULL pointer to work around bugs
    # in how ctypes handles None on 64-bit platforms
    if not isinstance(p.from_param, classmethod):
        def from_param(cls, x):
            if x is None:
                return cls()
            else:
                return x
        p.from_param = classmethod(from_param)

    return p


def String(python_base_str):
    return c_char_p(str(python_base_str))

# class UserString:
#    def __init__(self, seq):
#        if isinstance(seq, basestring):
#            self.data = seq
#        elif isinstance(seq, UserString):
#            self.data = seq.data[:]
#        else:
#            self.data = str(seq)
#    def __str__(self): return str(self.data)
#    def __repr__(self): return repr(self.data)
#    def __int__(self): return int(self.data)
#    def __long__(self): return long(self.data)
#    def __float__(self): return float(self.data)
#    def __complex__(self): return complex(self.data)
#    def __hash__(self): return hash(self.data)
#
#    def __cmp__(self, string):
#        if isinstance(string, UserString):
#            return cmp(self.data, string.data)
#        else:
#            return cmp(self.data, string)
#    def __contains__(self, char):
#        return char in self.data
#
#    def __len__(self): return len(self.data)
#    def __getitem__(self, index): return self.__class__(self.data[index])
#    def __getslice__(self, start, end):
#        start = max(start, 0); end = max(end, 0)
#        return self.__class__(self.data[start:end])
#
#    def __add__(self, other):
#        if isinstance(other, UserString):
#            return self.__class__(self.data + other.data)
#        elif isinstance(other, basestring):
#            return self.__class__(self.data + other)
#        else:
#            return self.__class__(self.data + str(other))
#    def __radd__(self, other):
#        if isinstance(other, basestring):
#            return self.__class__(other + self.data)
#        else:
#            return self.__class__(str(other) + self.data)
#    def __mul__(self, n):
#        return self.__class__(self.data*n)
#    __rmul__ = __mul__
#    def __mod__(self, args):
#        return self.__class__(self.data % args)
#
#    # the following methods are defined in alphabetical order:
#    def capitalize(self): return self.__class__(self.data.capitalize())
#    def center(self, width, *args):
#        return self.__class__(self.data.center(width, *args))
#    def count(self, sub, start=0, end=sys.maxint):
#        return self.data.count(sub, start, end)
#    def decode(self, encoding=None, errors=None): # XXX improve this?
#        if encoding:
#            if errors:
#                return self.__class__(self.data.decode(encoding, errors))
#            else:
#                return self.__class__(self.data.decode(encoding))
#        else:
#            return self.__class__(self.data.decode())
#    def encode(self, encoding=None, errors=None): # XXX improve this?
#        if encoding:
#            if errors:
#                return self.__class__(self.data.encode(encoding, errors))
#            else:
#                return self.__class__(self.data.encode(encoding))
#        else:
#            return self.__class__(self.data.encode())
#    def endswith(self, suffix, start=0, end=sys.maxint):
#        return self.data.endswith(suffix, start, end)
#    def expandtabs(self, tabsize=8):
#        return self.__class__(self.data.expandtabs(tabsize))
#    def find(self, sub, start=0, end=sys.maxint):
#        return self.data.find(sub, start, end)
#    def index(self, sub, start=0, end=sys.maxint):
#        return self.data.index(sub, start, end)
#    def isalpha(self): return self.data.isalpha()
#    def isalnum(self): return self.data.isalnum()
#    def isdecimal(self): return self.data.isdecimal()
#    def isdigit(self): return self.data.isdigit()
#    def islower(self): return self.data.islower()
#    def isnumeric(self): return self.data.isnumeric()
#    def isspace(self): return self.data.isspace()
#    def istitle(self): return self.data.istitle()
#    def isupper(self): return self.data.isupper()
#    def join(self, seq): return self.data.join(seq)
#    def ljust(self, width, *args):
#        return self.__class__(self.data.ljust(width, *args))
#    def lower(self): return self.__class__(self.data.lower())
#    def lstrip(self, chars=None): return self.__class__(self.data.lstrip(chars))
#    def partition(self, sep):
#        return self.data.partition(sep)
#    def replace(self, old, new, maxsplit=-1):
#        return self.__class__(self.data.replace(old, new, maxsplit))
#    def rfind(self, sub, start=0, end=sys.maxint):
#        return self.data.rfind(sub, start, end)
#    def rindex(self, sub, start=0, end=sys.maxint):
#        return self.data.rindex(sub, start, end)
#    def rjust(self, width, *args):
#        return self.__class__(self.data.rjust(width, *args))
#    def rpartition(self, sep):
#        return self.data.rpartition(sep)
#    def rstrip(self, chars=None): return self.__class__(self.data.rstrip(chars))
#    def split(self, sep=None, maxsplit=-1):
#        return self.data.split(sep, maxsplit)
#    def rsplit(self, sep=None, maxsplit=-1):
#        return self.data.rsplit(sep, maxsplit)
#    def splitlines(self, keepends=0): return self.data.splitlines(keepends)
#    def startswith(self, prefix, start=0, end=sys.maxint):
#        return self.data.startswith(prefix, start, end)
#    def strip(self, chars=None): return self.__class__(self.data.strip(chars))
#    def swapcase(self): return self.__class__(self.data.swapcase())
#    def title(self): return self.__class__(self.data.title())
#    def translate(self, *args):
#        return self.__class__(self.data.translate(*args))
#    def upper(self): return self.__class__(self.data.upper())
#    def zfill(self, width): return self.__class__(self.data.zfill(width))
#
# class MutableString(UserString):
#    """mutable string objects
#
#    Python strings are immutable objects.  This has the advantage, that
#    strings may be used as dictionary keys.  If this property isn't needed
#    and you insist on changing string values in place instead, you may cheat
#    and use MutableString.
#
#    But the purpose of this class is an educational one: to prevent
#    people from inventing their own mutable string class derived
#    from UserString and than forget thereby to remove (override) the
#    __hash__ method inherited from UserString.  This would lead to
#    errors that would be very hard to track down.
#
#    A faster and better solution is to rewrite your program using lists."""
#    def __init__(self, string=""):
#        self.data = string
#    def __hash__(self):
#        raise TypeError("unhashable type (it is mutable)")
#    def __setitem__(self, index, sub):
#        if index < 0:
#            index += len(self.data)
#        if index < 0 or index >= len(self.data): raise IndexError
#        self.data = self.data[:index] + sub + self.data[index+1:]
#    def __delitem__(self, index):
#        if index < 0:
#            index += len(self.data)
#        if index < 0 or index >= len(self.data): raise IndexError
#        self.data = self.data[:index] + self.data[index+1:]
#    def __setslice__(self, start, end, sub):
#        start = max(start, 0); end = max(end, 0)
#        if isinstance(sub, UserString):
#            self.data = self.data[:start]+sub.data+self.data[end:]
#        elif isinstance(sub, basestring):
#            self.data = self.data[:start]+sub+self.data[end:]
#        else:
#            self.data =  self.data[:start]+str(sub)+self.data[end:]
#    def __delslice__(self, start, end):
#        start = max(start, 0); end = max(end, 0)
#        self.data = self.data[:start] + self.data[end:]
#    def immutable(self):
#        return UserString(self.data)
#    def __iadd__(self, other):
#        if isinstance(other, UserString):
#            self.data += other.data
#        elif isinstance(other, basestring):
#            self.data += other
#        else:
#            self.data += str(other)
#        return self
#    def __imul__(self, n):
#        self.data *= n
#        return self
#
# class String(MutableString, Union):
#
#    _fields_ = [('raw', POINTER(c_char)),
#                ('data', c_char_p)]
#
#    def __init__(self, obj=""):
#        if isinstance(obj, (str, unicode, UserString)):
#            self.data = str(obj)
#        else:
#            self.raw = obj
#
#    def __len__(self):
#        return self.data and len(self.data) or 0
#
#    def from_param(cls, obj):
#        # Convert None or 0
#        if obj is None or obj == 0:
#            return cls(POINTER(c_char)())
#
#        # Convert from String
#        elif isinstance(obj, String):
#            return obj
#
#        # Convert from str
#        elif isinstance(obj, str):
#            return cls(obj)
#
#        # Convert from c_char_p
#        elif isinstance(obj, c_char_p):
#            return obj
#
#        # Convert from POINTER(c_char)
#        elif isinstance(obj, POINTER(c_char)):
#            return obj
#
#        # Convert from raw pointer
#        elif isinstance(obj, int):
#            return cls(cast(obj, POINTER(c_char)))
#
#        # Convert from object
#        else:
#            return String.from_param(obj._as_parameter_)
#    from_param = classmethod(from_param)
#
# def ReturnString(obj, func=None, arguments=None):
#    return String.from_param(obj)

# As of ctypes 1.0, ctypes does not support custom error-checking
# functions on callbacks, nor does it support custom datatypes on
# callbacks, so we must ensure that all callbacks return
# primitive datatypes.
#
# Non-primitive return values wrapped with UNCHECKED won't be
# typechecked, and will be converted to c_void_p.


def UNCHECKED(type):
    if (hasattr(type, '_type_') and isinstance(type._type_, str)
            and type._type_ != 'P'):
        return type
    else:
        return c_void_p

# ctypes doesn't have direct support for variadic functions, so we have to write
# our own wrapper class


class _variadic_function(object):

    def __init__(self, func, restype, argtypes):
        self.func = func
        self.func.restype = restype
        self.argtypes = argtypes

    def _as_parameter_(self):
        # So we can pass this variadic function as a function pointer
        return self.func

    def __call__(self, *args):
        fixed_args = []
        i = 0
        for argtype in self.argtypes:
            # Typecheck what we can
            fixed_args.append(argtype.from_param(args[i]))
            i += 1
        return self.func(*fixed_args + list(args[i:]))

# End preamble

_libs = {}
_libdirs = []

# Begin loader

# ----------------------------------------------------------------------------
# Copyright (c) 2008 David James
# Copyright (c) 2006-2008 Alex Holkner
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions
# are met:
#
#  * Redistributions of source code must retain the above copyright
#    notice, this list of conditions and the following disclaimer.
#  * Redistributions in binary form must reproduce the above copyright
#    notice, this list of conditions and the following disclaimer in
#    the documentation and/or other materials provided with the
#    distribution.
#  * Neither the name of pyglet nor the names of its
#    contributors may be used to endorse or promote products
#    derived from this software without specific prior written
#    permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS
# "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT
# LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS
# FOR A PARTICULAR PURPOSE ARE DISCLAIMED. IN NO EVENT SHALL THE
# COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT,
# INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING,
# BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER
# CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT
# LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN
# ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF THE
# POSSIBILITY OF SUCH DAMAGE.
# ----------------------------------------------------------------------------

import os.path
import re
import sys
import glob
import ctypes
import ctypes.util


def _environ_path(name):
    if name in os.environ:
        return os.environ[name].split(':')
    else:
        return []


class LibraryLoader(object):

    def __init__(self):
        self.other_dirs = []

    def load_library(self, libname):
        """Given the name of a library, load it."""
        paths = self.getpaths(libname)

        for path in paths:
            if os.path.exists(path):
                return self.load(path)

        raise ImportError('%s not found.' % libname)

    def load(self, path):
        """Given a path to a library, load it."""
        try:
            # Darwin requires dlopen to be called with mode RTLD_GLOBAL instead
            # of the default RTLD_LOCAL.  Without this, you end up with
            # libraries not being loadable, resulting in "Symbol not found"
            # errors
            if sys.platform == 'darwin':
                return ctypes.CDLL(path, ctypes.RTLD_GLOBAL)
            else:
                return ctypes.windll.LoadLibrary(path)
        except OSError as e:
            raise ImportError(e)

    def getpaths(self, libname):
        """Return a list of paths where the library might be found."""
        if os.path.isabs(libname):
            yield libname
        else:
            # FIXME / TODO return '.' and os.path.dirname(__file__)
            for path in self.getplatformpaths(libname):
                yield path

            path = ctypes.util.find_library(libname)
            if path:
                yield path

    def getplatformpaths(self, libname):
        return []

# Darwin (Mac OS X)


class DarwinLibraryLoader(LibraryLoader):
    name_formats = ['lib%s.dylib', 'lib%s.so', 'lib%s.bundle', '%s.dylib',
                    '%s.so', '%s.bundle', '%s']

    def getplatformpaths(self, libname):
        if os.path.pathsep in libname:
            names = [libname]
        else:
            names = [format % libname for format in self.name_formats]

        for dir in self.getdirs(libname):
            for name in names:
                yield os.path.join(dir, name)

    def getdirs(self, libname):
        '''Implements the dylib search as specified in Apple documentation:

        http://developer.apple.com/documentation/DeveloperTools/Conceptual/
            DynamicLibraries/Articles/DynamicLibraryUsageGuidelines.html

        Before commencing the standard search, the method first checks
        the bundle's ``Frameworks`` directory if the application is running
        within a bundle (OS X .app).
        '''

        dyld_fallback_library_path = _environ_path(
            'DYLD_FALLBACK_LIBRARY_PATH')
        if not dyld_fallback_library_path:
            dyld_fallback_library_path = [os.path.expanduser('~/lib'),
                                          '/usr/local/lib', '/usr/lib']

        dirs = []

        if '/' in libname:
            dirs.extend(_environ_path('DYLD_LIBRARY_PATH'))
        else:
            dirs.extend(_environ_path('LD_LIBRARY_PATH'))
            dirs.extend(_environ_path('DYLD_LIBRARY_PATH'))

        dirs.extend(self.other_dirs)
        dirs.append('.')
        dirs.append(os.path.dirname(__file__))

        if hasattr(sys, 'frozen') and sys.frozen == 'macosx_app':
            dirs.append(os.path.join(
                os.environ['RESOURCEPATH'],
                '..',
                'Frameworks'))

        dirs.extend(dyld_fallback_library_path)

        return dirs

# Posix


class PosixLibraryLoader(LibraryLoader):
    _ld_so_cache = None

    def _create_ld_so_cache(self):
        # Recreate search path followed by ld.so.  This is going to be
        # slow to build, and incorrect (ld.so uses ld.so.cache, which may
        # not be up-to-date).  Used only as fallback for distros without
        # /sbin/ldconfig.
        #
        # We assume the DT_RPATH and DT_RUNPATH binary sections are omitted.

        directories = []
        for name in ('LD_LIBRARY_PATH',
                     'SHLIB_PATH',  # HPUX
                     'LIBPATH',  # OS/2, AIX
                     'LIBRARY_PATH',  # BE/OS
                     ):
            if name in os.environ:
                directories.extend(os.environ[name].split(os.pathsep))
        directories.extend(self.other_dirs)
        directories.append('.')
        directories.append(os.path.dirname(__file__))

        try:
            directories.extend([dir.strip()
                                for dir in open('/etc/ld.so.conf')])
        except IOError:
            pass

        directories.extend(['/lib', '/usr/lib', '/lib64', '/usr/lib64'])

        cache = {}
        lib_re = re.compile(r'lib(.*)\.s[ol]')
        ext_re = re.compile(r'\.s[ol]$')
        for dir in directories:
            try:
                for path in glob.glob('%s/*.s[ol]*' % dir):
                    file = os.path.basename(path)

                    # Index by filename
                    if file not in cache:
                        cache[file] = path

                    # Index by library name
                    match = lib_re.match(file)
                    if match:
                        library = match.group(1)
                        if library not in cache:
                            cache[library] = path
            except OSError:
                pass

        self._ld_so_cache = cache

    def getplatformpaths(self, libname):
        if self._ld_so_cache is None:
            self._create_ld_so_cache()

        result = self._ld_so_cache.get(libname)
        if result:
            yield result

        path = ctypes.util.find_library(libname)
        if path:
            yield os.path.join('/lib', path)

# Windows


class _WindowsLibrary(object):

    def __init__(self, path):
        self.windll = ctypes.windll.LoadLibrary(path)

    def __getattr__(self, name):
        try:
            return getattr(self.windll, name)
        except AttributeError:
            raise


class WindowsLibraryLoader(LibraryLoader):
    name_formats = ['%s.dll', 'lib%s.dll', '%slib.dll']

    def load_library(self, libname):
        try:
            result = LibraryLoader.load_library(self, libname)
        except ImportError:
            result = None
            if os.path.sep not in libname:
                for name in self.name_formats:
                    try:
                        result = getattr(ctypes.cdll, name % libname)
                        if result:
                            break
                    except WindowsError:
                        result = None
            if result is None:
                try:
                    result = getattr(ctypes.cdll, libname)
                except WindowsError:
                    result = None
            if result is None:
                raise ImportError('%s not found.' % libname)
        return result

    def load(self, path):
        return _WindowsLibrary(path)

    def getplatformpaths(self, libname):
        if os.path.sep not in libname:
            for name in self.name_formats:
                dll_in_current_dir = os.path.abspath(name % libname)
                if os.path.exists(dll_in_current_dir):
                    yield dll_in_current_dir
                path = ctypes.util.find_library(name % libname)
                if path:
                    yield path

# Platform switching

# If your value of sys.platform does not appear in this dict, please contact
# the Ctypesgen maintainers.

loaderclass = {
    'darwin': DarwinLibraryLoader,
    'cygwin': WindowsLibraryLoader,
    'win32': WindowsLibraryLoader
}

loader = loaderclass.get(sys.platform, PosixLibraryLoader)()


def add_library_search_dirs(other_dirs):
    loader.other_dirs = other_dirs

load_library = loader.load_library

del loaderclass

# End loader

add_library_search_dirs([])

# Begin libraries

_libs['iViewXAPI'] = load_library('iViewXAPI')

# 1 libraries
# End libraries

# No modules

enum_ETDevice = c_int  # <input>: 153

NONE = 0  # <input>: 153

RED = 1  # <input>: 153

REDm = 2  # <input>: 153

HiSpeed = 3  # <input>: 153

MRI = 4  # <input>: 153

HED = 5  # <input>: 153

ETG = 6  # <input>: 153

Custom = 7  # <input>: 153

enum_ETApplication = c_int  # <input>: 173

iViewX = 0  # <input>: 173

iViewXOEM = 1  # <input>: 173

enum_FilterType = c_int  # <input>: 189

Average = 0  # <input>: 189

enum_FilterAction = c_int  # <input>: 204

Query = 0  # <input>: 204

Set = 1  # <input>: 204

enum_CalibrationStatusEnum = c_int  # <input>: 222

calibrationUnknown = 0  # <input>: 222

calibrationInvalid = 1  # <input>: 222

calibrationValid = 2  # <input>: 222

calibrationInProgress = 3  # <input>: 222

enum_REDGeometryEnum = c_int  # <input>: 242

monitorIntegrated = 0  # <input>: 242

standalone = 1  # <input>: 242

# <input>: 258


class struct_SystemInfoStruct(Structure):
    pass

struct_SystemInfoStruct.__slots__ = [
    'samplerate',
    'iV_MajorVersion',
    'iV_MinorVersion',
    'iV_Buildnumber',
    'API_MajorVersion',
    'API_MinorVersion',
    'API_Buildnumber',
    'iV_ETDevice',
]
struct_SystemInfoStruct._fields_ = [
    ('samplerate', c_int),
    ('iV_MajorVersion', c_int),
    ('iV_MinorVersion', c_int),
    ('iV_Buildnumber', c_int),
    ('API_MajorVersion', c_int),
    ('API_MinorVersion', c_int),
    ('API_Buildnumber', c_int),
    ('iV_ETDevice', enum_ETDevice),
]

# <input>: 294


class struct_CalibrationPointStruct(Structure):
    pass

struct_CalibrationPointStruct.__slots__ = [
    'number',
    'positionX',
    'positionY',
]
struct_CalibrationPointStruct._fields_ = [
    ('number', c_int),
    ('positionX', c_int),
    ('positionY', c_int),
]

# <input>: 315


class struct_EyeDataStruct(Structure):
    pass

struct_EyeDataStruct.__slots__ = [
    'gazeX',
    'gazeY',
    'diam',
    'eyePositionX',
    'eyePositionY',
    'eyePositionZ',
]
struct_EyeDataStruct._fields_ = [
    ('gazeX', c_double),
    ('gazeY', c_double),
    ('diam', c_double),
    ('eyePositionX', c_double),
    ('eyePositionY', c_double),
    ('eyePositionZ', c_double),
]

# <input>: 344


class struct_SampleStruct(Structure):
    pass

struct_SampleStruct.__slots__ = [
    'timestamp',
    'leftEye',
    'rightEye',
    'planeNumber',
]
struct_SampleStruct._fields_ = [
    ('timestamp', c_longlong),
    ('leftEye', struct_EyeDataStruct),
    ('rightEye', struct_EyeDataStruct),
    ('planeNumber', c_int),
]

# <input>: 368


class struct_SampleStruct32(Structure):
    pass

struct_SampleStruct32.__slots__ = [
    'timestamp',
    'leftEye',
    'rightEye',
    'planeNumber',
]
struct_SampleStruct32._fields_ = [
    ('timestamp', c_double),
    ('leftEye', struct_EyeDataStruct),
    ('rightEye', struct_EyeDataStruct),
    ('planeNumber', c_int),
]

# <input>: 392


class struct_EventStruct(Structure):
    pass

struct_EventStruct.__slots__ = [
    'eventType',
    'eye',
    'startTime',
    'endTime',
    'duration',
    'positionX',
    'positionY',
]
struct_EventStruct._fields_ = [
    ('eventType', c_char),
    ('eye', c_char),
    ('startTime', c_longlong),
    ('endTime', c_longlong),
    ('duration', c_longlong),
    ('positionX', c_double),
    ('positionY', c_double),
]

# <input>: 426


class struct_EventStruct32(Structure):
    pass

struct_EventStruct32.__slots__ = [
    'startTime',
    'endTime',
    'duration',
    'positionX',
    'positionY',
    'eventType',
    'eye',
]
struct_EventStruct32._fields_ = [
    ('startTime', c_double),
    ('endTime', c_double),
    ('duration', c_double),
    ('positionX', c_double),
    ('positionY', c_double),
    ('eventType', c_char),
    ('eye', c_char),
]

# <input>: 466


class struct_EyePositionStruct(Structure):
    pass

struct_EyePositionStruct.__slots__ = [
    'validity',
    'relativePositionX',
    'relativePositionY',
    'relativePositionZ',
    'positionRatingX',
    'positionRatingY',
    'positionRatingZ',
]
struct_EyePositionStruct._fields_ = [
    ('validity', c_int),
    ('relativePositionX', c_double),
    ('relativePositionY', c_double),
    ('relativePositionZ', c_double),
    ('positionRatingX', c_double),
    ('positionRatingY', c_double),
    ('positionRatingZ', c_double),
]

# <input>: 499


class struct_TrackingStatusStruct(Structure):
    pass

struct_TrackingStatusStruct.__slots__ = [
    'timestamp',
    'leftEye',
    'rightEye',
    'total',
]
struct_TrackingStatusStruct._fields_ = [
    ('timestamp', c_longlong),
    ('leftEye', struct_EyePositionStruct),
    ('rightEye', struct_EyePositionStruct),
    ('total', struct_EyePositionStruct),
]

# <input>: 522


class struct_AccuracyStruct(Structure):
    pass

struct_AccuracyStruct.__slots__ = [
    'deviationLX',
    'deviationLY',
    'deviationRX',
    'deviationRY',
]
struct_AccuracyStruct._fields_ = [
    ('deviationLX', c_double),
    ('deviationLY', c_double),
    ('deviationRX', c_double),
    ('deviationRY', c_double),
]

# <input>: 545


class struct_CalibrationStruct(Structure):
    pass

struct_CalibrationStruct.__slots__ = [
    'method',
    'visualization',
    'displayDevice',
    'speed',
    'autoAccept',
    'foregroundBrightness',
    'backgroundBrightness',
    'targetShape',
    'targetSize',
    'targetFilename',
]
struct_CalibrationStruct._fields_ = [
    ('method', c_int),
    ('visualization', c_int),
    ('displayDevice', c_int),
    ('speed', c_int),
    ('autoAccept', c_int),
    ('foregroundBrightness', c_int),
    ('backgroundBrightness', c_int),
    ('targetShape', c_int),
    ('targetSize', c_int),
    ('targetFilename', c_char * 256),
]

# <input>: 587


class struct_REDGeometryStruct(Structure):
    pass

struct_REDGeometryStruct.__slots__ = [
    'redGeometry',
    'monitorSize',
    'setupName',
    'stimX',
    'stimY',
    'stimHeightOverFloor',
    'redHeightOverFloor',
    'redStimDist',
    'redInclAngle',
    'redStimDistHeight',
    'redStimDistDepth',
]
struct_REDGeometryStruct._fields_ = [
    ('redGeometry', c_int),
    ('monitorSize', c_int),
    ('setupName', c_char * 256),
    ('stimX', c_int),
    ('stimY', c_int),
    ('stimHeightOverFloor', c_int),
    ('redHeightOverFloor', c_int),
    ('redStimDist', c_int),
    ('redInclAngle', c_int),
    ('redStimDistHeight', c_int),
    ('redStimDistDepth', c_int),
]

# <input>: 656


class struct_ImageStruct(Structure):
    pass

struct_ImageStruct.__slots__ = [
    'imageHeight',
    'imageWidth',
    'imageSize',
    'imageBuffer',
]
struct_ImageStruct._fields_ = [
    ('imageHeight', c_int),
    ('imageWidth', c_int),
    ('imageSize', c_int),
    ('imageBuffer', c_char_p),
]

# <input>: 678


class struct_DateStruct(Structure):
    pass

struct_DateStruct.__slots__ = [
    'day',
    'month',
    'year',
]
struct_DateStruct._fields_ = [
    ('day', c_int),
    ('month', c_int),
    ('year', c_int),
]

# <input>: 697


class struct_AOIRectangleStruct(Structure):
    pass

struct_AOIRectangleStruct.__slots__ = [
    'x1',
    'x2',
    'y1',
    'y2',
]
struct_AOIRectangleStruct._fields_ = [
    ('x1', c_int),
    ('x2', c_int),
    ('y1', c_int),
    ('y2', c_int),
]

# <input>: 719


class struct_AOIStruct(Structure):
    pass

struct_AOIStruct.__slots__ = [
    'enabled',
    'aoiName',
    'aoiGroup',
    'position',
    'fixationHit',
    'outputValue',
    'outputMessage',
    'eye',
]
struct_AOIStruct._fields_ = [
    ('enabled', c_int),
    ('aoiName', c_char * 256),
    ('aoiGroup', c_char * 256),
    ('position', struct_AOIRectangleStruct),
    ('fixationHit', c_int),
    ('outputValue', c_int),
    ('outputMessage', c_char * 256),
    ('eye', c_char),
]

pDLLSetCalibrationPoint = WINFUNCTYPE(
    UNCHECKED(c_int),
    struct_CalibrationPointStruct)  # <input>: 750

pDLLSetAOIHit = WINFUNCTYPE(UNCHECKED(c_int), c_int)  # <input>: 756

pDLLSetSample = WINFUNCTYPE(
    UNCHECKED(c_int),
    struct_SampleStruct)  # <input>: 762

pDLLSetEvent = WINFUNCTYPE(
    UNCHECKED(c_int),
    struct_EventStruct)  # <input>: 768

pDLLSetEyeImage = WINFUNCTYPE(
    UNCHECKED(c_int),
    struct_ImageStruct)  # <input>: 773

pDLLSetSceneVideo = WINFUNCTYPE(
    UNCHECKED(c_int),
    struct_ImageStruct)  # <input>: 778

pDLLSetTrackingMonitor = WINFUNCTYPE(
    UNCHECKED(c_int),
    struct_ImageStruct)  # <input>: 783

# <input>: 798
if hasattr(_libs['iViewXAPI'], 'iV_AbortCalibration'):
    AbortCalibration = _libs['iViewXAPI'].iV_AbortCalibration
    AbortCalibration.argtypes = []
    AbortCalibration.restype = c_int

# <input>: 812
if hasattr(_libs['iViewXAPI'], 'iV_AcceptCalibrationPoint'):
    AcceptCalibrationPoint = _libs['iViewXAPI'].iV_AcceptCalibrationPoint
    AcceptCalibrationPoint.argtypes = []
    AcceptCalibrationPoint.restype = c_int

# <input>: 837
if hasattr(_libs['iViewXAPI'], 'iV_Calibrate'):
    Calibrate = _libs['iViewXAPI'].iV_Calibrate
    Calibrate.argtypes = []
    Calibrate.restype = c_int

# <input>: 854
if hasattr(_libs['iViewXAPI'], 'iV_ChangeCalibrationPoint'):
    ChangeCalibrationPoint = _libs['iViewXAPI'].iV_ChangeCalibrationPoint
    ChangeCalibrationPoint.argtypes = [c_int, c_int, c_int]
    ChangeCalibrationPoint.restype = c_int

# <input>: 864
if hasattr(_libs['iViewXAPI'], 'iV_ClearAOI'):
    ClearAOI = _libs['iViewXAPI'].iV_ClearAOI
    ClearAOI.argtypes = []
    ClearAOI.restype = c_int

# <input>: 880
if hasattr(_libs['iViewXAPI'], 'iV_ClearRecordingBuffer'):
    ClearRecordingBuffer = _libs['iViewXAPI'].iV_ClearRecordingBuffer
    ClearRecordingBuffer.argtypes = []
    ClearRecordingBuffer.restype = c_int

# <input>: 899
if hasattr(_libs['iViewXAPI'], 'iV_ConfigureFilter'):
    ConfigureFilter = _libs['iViewXAPI'].iV_ConfigureFilter
    ConfigureFilter.argtypes = [c_int, c_int, POINTER(None)]
    ConfigureFilter.restype = c_int

# <input>: 920
if hasattr(_libs['iViewXAPI'], 'iV_Connect'):
    Connect = _libs['iViewXAPI'].iV_Connect
    Connect.argtypes = [c_char_p, c_int, c_char_p, c_int]
    Connect.restype = c_int

# <input>: 937
if hasattr(_libs['iViewXAPI'], 'iV_ConnectLocal'):
    ConnectLocal = _libs['iViewXAPI'].iV_ConnectLocal
    ConnectLocal.argtypes = []
    ConnectLocal.restype = c_int

# <input>: 948
if hasattr(_libs['iViewXAPI'], 'iV_ContinueEyetracking'):
    ContinueEyetracking = _libs['iViewXAPI'].iV_ContinueEyetracking
    ContinueEyetracking.argtypes = []
    ContinueEyetracking.restype = c_int

# <input>: 968
if hasattr(_libs['iViewXAPI'], 'iV_ContinueRecording'):
    ContinueRecording = _libs['iViewXAPI'].iV_ContinueRecording
    ContinueRecording.argtypes = [c_char_p]
    ContinueRecording.restype = c_int

# <input>: 980
if hasattr(_libs['iViewXAPI'], 'iV_DefineAOI'):
    DefineAOI = _libs['iViewXAPI'].iV_DefineAOI
    DefineAOI.argtypes = [POINTER(struct_AOIStruct)]
    DefineAOI.restype = c_int

# <input>: 993
if hasattr(_libs['iViewXAPI'], 'iV_DefineAOIPort'):
    DefineAOIPort = _libs['iViewXAPI'].iV_DefineAOIPort
    DefineAOIPort.argtypes = [c_int]
    DefineAOIPort.restype = c_int

# <input>: 1009
if hasattr(_libs['iViewXAPI'], 'iV_DeleteREDGeometry'):
    DeleteREDGeometry = _libs['iViewXAPI'].iV_DeleteREDGeometry
    DeleteREDGeometry.argtypes = [c_char_p]
    DeleteREDGeometry.restype = c_int

# <input>: 1022
if hasattr(_libs['iViewXAPI'], 'iV_DisableAOI'):
    DisableAOI = _libs['iViewXAPI'].iV_DisableAOI
    DisableAOI.argtypes = [c_char_p]
    DisableAOI.restype = c_int

# <input>: 1035
if hasattr(_libs['iViewXAPI'], 'iV_DisableAOIGroup'):
    DisableAOIGroup = _libs['iViewXAPI'].iV_DisableAOIGroup
    DisableAOIGroup.argtypes = [c_char_p]
    DisableAOIGroup.restype = c_int

# <input>: 1044
if hasattr(_libs['iViewXAPI'], 'iV_DisableGazeDataFilter'):
    DisableGazeDataFilter = _libs['iViewXAPI'].iV_DisableGazeDataFilter
    DisableGazeDataFilter.argtypes = []
    DisableGazeDataFilter.restype = c_int

# <input>: 1054
if hasattr(_libs['iViewXAPI'], 'iV_DisableProcessorHighPerformanceMode'):
    DisableProcessorHighPerformanceMode = _libs[
        'iViewXAPI'].iV_DisableProcessorHighPerformanceMode
    DisableProcessorHighPerformanceMode.argtypes = []
    DisableProcessorHighPerformanceMode.restype = c_int

# <input>: 1067
if hasattr(_libs['iViewXAPI'], 'iV_Disconnect'):
    Disconnect = _libs['iViewXAPI'].iV_Disconnect
    Disconnect.argtypes = []
    Disconnect.restype = c_int

# <input>: 1080
if hasattr(_libs['iViewXAPI'], 'iV_EnableAOI'):
    EnableAOI = _libs['iViewXAPI'].iV_EnableAOI
    EnableAOI.argtypes = [c_char_p]
    EnableAOI.restype = c_int

# <input>: 1093
if hasattr(_libs['iViewXAPI'], 'iV_EnableAOIGroup'):
    EnableAOIGroup = _libs['iViewXAPI'].iV_EnableAOIGroup
    EnableAOIGroup.argtypes = [c_char_p]
    EnableAOIGroup.restype = c_int

# <input>: 1103
if hasattr(_libs['iViewXAPI'], 'iV_EnableGazeDataFilter'):
    EnableGazeDataFilter = _libs['iViewXAPI'].iV_EnableGazeDataFilter
    EnableGazeDataFilter.argtypes = []
    EnableGazeDataFilter.restype = c_int

# <input>: 1113
if hasattr(_libs['iViewXAPI'], 'iV_EnableProcessorHighPerformanceMode'):
    EnableProcessorHighPerformanceMode = _libs[
        'iViewXAPI'].iV_EnableProcessorHighPerformanceMode
    EnableProcessorHighPerformanceMode.argtypes = []
    EnableProcessorHighPerformanceMode.restype = c_int

# <input>: 1134
if hasattr(_libs['iViewXAPI'], 'iV_GetAccuracy'):
    GetAccuracy = _libs['iViewXAPI'].iV_GetAccuracy
    GetAccuracy.argtypes = [POINTER(struct_AccuracyStruct), c_int]
    GetAccuracy.restype = c_int

# <input>: 1150
if hasattr(_libs['iViewXAPI'], 'iV_GetAccuracyImage'):
    GetAccuracyImage = _libs['iViewXAPI'].iV_GetAccuracyImage
    GetAccuracyImage.argtypes = [POINTER(struct_ImageStruct)]
    GetAccuracyImage.restype = c_int

# <input>: 1163
if hasattr(_libs['iViewXAPI'], 'iV_GetAOIOutputValue'):
    GetAOIOutputValue = _libs['iViewXAPI'].iV_GetAOIOutputValue
    GetAOIOutputValue.argtypes = [POINTER(c_int)]
    GetAOIOutputValue.restype = c_int

# <input>: 1175
if hasattr(_libs['iViewXAPI'], 'iV_GetCalibrationParameter'):
    GetCalibrationParameter = _libs['iViewXAPI'].iV_GetCalibrationParameter
    GetCalibrationParameter.argtypes = [POINTER(struct_CalibrationStruct)]
    GetCalibrationParameter.restype = c_int

# <input>: 1188
if hasattr(_libs['iViewXAPI'], 'iV_GetCalibrationPoint'):
    GetCalibrationPoint = _libs['iViewXAPI'].iV_GetCalibrationPoint
    GetCalibrationPoint.argtypes = [
        c_int, POINTER(struct_CalibrationPointStruct)]
    GetCalibrationPoint.restype = c_int

# <input>: 1202
if hasattr(_libs['iViewXAPI'], 'iV_GetCalibrationStatus'):
    GetCalibrationStatus = _libs['iViewXAPI'].iV_GetCalibrationStatus
    GetCalibrationStatus.argtypes = [POINTER(enum_CalibrationStatusEnum)]
    GetCalibrationStatus.restype = c_int

# <input>: 1216
if hasattr(_libs['iViewXAPI'], 'iV_GetCurrentCalibrationPoint'):
    GetCurrentCalibrationPoint = _libs[
        'iViewXAPI'].iV_GetCurrentCalibrationPoint
    GetCurrentCalibrationPoint.argtypes = [
        POINTER(struct_CalibrationPointStruct)]
    GetCurrentCalibrationPoint.restype = c_int

# <input>: 1228
if hasattr(_libs['iViewXAPI'], 'iV_GetCurrentREDGeometry'):
    GetCurrentREDGeometry = _libs['iViewXAPI'].iV_GetCurrentREDGeometry
    GetCurrentREDGeometry.argtypes = [POINTER(struct_REDGeometryStruct)]
    GetCurrentREDGeometry.restype = c_int

# <input>: 1241
if hasattr(_libs['iViewXAPI'], 'iV_GetCurrentTimestamp'):
    GetCurrentTimestamp = _libs['iViewXAPI'].iV_GetCurrentTimestamp
    GetCurrentTimestamp.argtypes = [POINTER(c_longlong)]
    GetCurrentTimestamp.restype = c_int

# <input>: 1255
if hasattr(_libs['iViewXAPI'], 'iV_GetDeviceName'):
    GetDeviceName = _libs['iViewXAPI'].iV_GetDeviceName
    GetDeviceName.argtypes = [c_char * 64]
    GetDeviceName.restype = c_int

# <input>: 1268
if hasattr(_libs['iViewXAPI'], 'iV_GetEvent'):
    GetEvent = _libs['iViewXAPI'].iV_GetEvent
    GetEvent.argtypes = [POINTER(struct_EventStruct)]
    GetEvent.restype = c_int

# <input>: 1281
if hasattr(_libs['iViewXAPI'], 'iV_GetEvent32'):
    GetEvent32 = _libs['iViewXAPI'].iV_GetEvent32
    GetEvent32.argtypes = [POINTER(struct_EventStruct32)]
    GetEvent32.restype = c_int

# <input>: 1295
if hasattr(_libs['iViewXAPI'], 'iV_GetEyeImage'):
    GetEyeImage = _libs['iViewXAPI'].iV_GetEyeImage
    GetEyeImage.argtypes = [POINTER(struct_ImageStruct)]
    GetEyeImage.restype = c_int

# <input>: 1306
if hasattr(_libs['iViewXAPI'], 'iV_GetFeatureKey'):
    GetFeatureKey = _libs['iViewXAPI'].iV_GetFeatureKey
    GetFeatureKey.argtypes = [POINTER(c_longlong)]
    GetFeatureKey.restype = c_int

# <input>: 1324
if hasattr(_libs['iViewXAPI'], 'iV_GetGeometryProfiles'):
    GetGeometryProfiles = _libs['iViewXAPI'].iV_GetGeometryProfiles
    GetGeometryProfiles.argtypes = [c_int, c_char_p]
    GetGeometryProfiles.restype = c_int

# <input>: 1335
if hasattr(_libs['iViewXAPI'], 'iV_GetLicenseDueDate'):
    GetLicenseDueDate = _libs['iViewXAPI'].iV_GetLicenseDueDate
    GetLicenseDueDate.argtypes = [POINTER(struct_DateStruct)]
    GetLicenseDueDate.restype = c_int

# <input>: 1350
if hasattr(_libs['iViewXAPI'], 'iV_GetREDGeometry'):
    GetREDGeometry = _libs['iViewXAPI'].iV_GetREDGeometry
    GetREDGeometry.argtypes = [c_char_p, POINTER(struct_REDGeometryStruct)]
    GetREDGeometry.restype = c_int

# <input>: 1362
if hasattr(_libs['iViewXAPI'], 'iV_GetSample'):
    GetSample = _libs['iViewXAPI'].iV_GetSample
    GetSample.argtypes = [POINTER(struct_SampleStruct)]
    GetSample.restype = c_int

# <input>: 1375
if hasattr(_libs['iViewXAPI'], 'iV_GetSample32'):
    GetSample32 = _libs['iViewXAPI'].iV_GetSample32
    GetSample32.argtypes = [POINTER(struct_SampleStruct32)]
    GetSample32.restype = c_int

# <input>: 1390
if hasattr(_libs['iViewXAPI'], 'iV_GetSceneVideo'):
    GetSceneVideo = _libs['iViewXAPI'].iV_GetSceneVideo
    GetSceneVideo.argtypes = [POINTER(struct_ImageStruct)]
    GetSceneVideo.restype = c_int

# <input>: 1406
if hasattr(_libs['iViewXAPI'], 'iV_GetSerialNumber'):
    GetSerialNumber = _libs['iViewXAPI'].iV_GetSerialNumber
    GetSerialNumber.argtypes = [c_char * 64]
    GetSerialNumber.restype = c_int

# <input>: 1418
if hasattr(_libs['iViewXAPI'], 'iV_GetSystemInfo'):
    GetSystemInfo = _libs['iViewXAPI'].iV_GetSystemInfo
    GetSystemInfo.argtypes = [POINTER(struct_SystemInfoStruct)]
    GetSystemInfo.restype = c_int

# <input>: 1432
if hasattr(_libs['iViewXAPI'], 'iV_GetTrackingMonitor'):
    GetTrackingMonitor = _libs['iViewXAPI'].iV_GetTrackingMonitor
    GetTrackingMonitor.argtypes = [POINTER(struct_ImageStruct)]
    GetTrackingMonitor.restype = c_int

# <input>: 1446
if hasattr(_libs['iViewXAPI'], 'iV_GetTrackingStatus'):
    GetTrackingStatus = _libs['iViewXAPI'].iV_GetTrackingStatus
    GetTrackingStatus.argtypes = [POINTER(struct_TrackingStatusStruct)]
    GetTrackingStatus.restype = c_int

# <input>: 1456
if hasattr(_libs['iViewXAPI'], 'iV_HideAccuracyMonitor'):
    HideAccuracyMonitor = _libs['iViewXAPI'].iV_HideAccuracyMonitor
    HideAccuracyMonitor.argtypes = []
    HideAccuracyMonitor.restype = c_int

# <input>: 1466
if hasattr(_libs['iViewXAPI'], 'iV_HideEyeImageMonitor'):
    HideEyeImageMonitor = _libs['iViewXAPI'].iV_HideEyeImageMonitor
    HideEyeImageMonitor.argtypes = []
    HideEyeImageMonitor.restype = c_int

# <input>: 1476
if hasattr(_libs['iViewXAPI'], 'iV_HideSceneVideoMonitor'):
    HideSceneVideoMonitor = _libs['iViewXAPI'].iV_HideSceneVideoMonitor
    HideSceneVideoMonitor.argtypes = []
    HideSceneVideoMonitor.restype = c_int

# <input>: 1486
if hasattr(_libs['iViewXAPI'], 'iV_HideTrackingMonitor'):
    HideTrackingMonitor = _libs['iViewXAPI'].iV_HideTrackingMonitor
    HideTrackingMonitor.argtypes = []
    HideTrackingMonitor.restype = c_int

# <input>: 1496
if hasattr(_libs['iViewXAPI'], 'iV_IsConnected'):
    IsConnected = _libs['iViewXAPI'].iV_IsConnected
    IsConnected.argtypes = []
    IsConnected.restype = c_int

# <input>: 1514
if hasattr(_libs['iViewXAPI'], 'iV_LoadCalibration'):
    LoadCalibration = _libs['iViewXAPI'].iV_LoadCalibration
    LoadCalibration.argtypes = [c_char_p]
    LoadCalibration.restype = c_int

# <input>: 1525
if hasattr(_libs['iViewXAPI'], 'iV_Log'):
    Log = _libs['iViewXAPI'].iV_Log
    Log.argtypes = [c_char_p]
    Log.restype = c_int

# <input>: 1536
if hasattr(_libs['iViewXAPI'], 'iV_PauseEyetracking'):
    PauseEyetracking = _libs['iViewXAPI'].iV_PauseEyetracking
    PauseEyetracking.argtypes = []
    PauseEyetracking.restype = c_int

# <input>: 1552
if hasattr(_libs['iViewXAPI'], 'iV_PauseRecording'):
    PauseRecording = _libs['iViewXAPI'].iV_PauseRecording
    PauseRecording.argtypes = []
    PauseRecording.restype = c_int

# <input>: 1565
if hasattr(_libs['iViewXAPI'], 'iV_Quit'):
    Quit = _libs['iViewXAPI'].iV_Quit
    Quit.argtypes = []
    Quit.restype = c_int

# <input>: 1575
if hasattr(_libs['iViewXAPI'], 'iV_ReleaseAOIPort'):
    ReleaseAOIPort = _libs['iViewXAPI'].iV_ReleaseAOIPort
    ReleaseAOIPort.argtypes = []
    ReleaseAOIPort.restype = c_int

# <input>: 1588
if hasattr(_libs['iViewXAPI'], 'iV_RemoveAOI'):
    RemoveAOI = _libs['iViewXAPI'].iV_RemoveAOI
    RemoveAOI.argtypes = [c_char_p]
    RemoveAOI.restype = c_int

# <input>: 1598
if hasattr(_libs['iViewXAPI'], 'iV_ResetCalibrationPoints'):
    ResetCalibrationPoints = _libs['iViewXAPI'].iV_ResetCalibrationPoints
    ResetCalibrationPoints.argtypes = []
    ResetCalibrationPoints.restype = c_int

# <input>: 1615
if hasattr(_libs['iViewXAPI'], 'iV_SaveCalibration'):
    SaveCalibration = _libs['iViewXAPI'].iV_SaveCalibration
    SaveCalibration.argtypes = [c_char_p]
    SaveCalibration.restype = c_int

# <input>: 1638
if hasattr(_libs['iViewXAPI'], 'iV_SaveData'):
    SaveData = _libs['iViewXAPI'].iV_SaveData
    SaveData.argtypes = [c_char_p, c_char_p, c_char_p, c_int]
    SaveData.restype = c_int

# <input>: 1654
if hasattr(_libs['iViewXAPI'], 'iV_SendCommand'):
    SendCommand = _libs['iViewXAPI'].iV_SendCommand
    SendCommand.argtypes = [c_char_p]
    SendCommand.restype = c_int

# <input>: 1669
if hasattr(_libs['iViewXAPI'], 'iV_SendImageMessage'):
    SendImageMessage = _libs['iViewXAPI'].iV_SendImageMessage
    SendImageMessage.argtypes = [c_char_p]
    SendImageMessage.restype = c_int

# <input>: 1686
if hasattr(_libs['iViewXAPI'], 'iV_SetAOIHitCallback'):
    SetAOIHitCallback = _libs['iViewXAPI'].iV_SetAOIHitCallback
    SetAOIHitCallback.argtypes = [pDLLSetAOIHit]
    SetAOIHitCallback.restype = c_int

# <input>: 1701
if hasattr(_libs['iViewXAPI'], 'iV_SetCalibrationCallback'):
    SetCalibrationCallback = _libs['iViewXAPI'].iV_SetCalibrationCallback
    SetCalibrationCallback.argtypes = [pDLLSetCalibrationPoint]
    SetCalibrationCallback.restype = c_int

# <input>: 1714
if hasattr(_libs['iViewXAPI'], 'iV_SetConnectionTimeout'):
    SetConnectionTimeout = _libs['iViewXAPI'].iV_SetConnectionTimeout
    SetConnectionTimeout.argtypes = [c_int]
    SetConnectionTimeout.restype = c_int

# <input>: 1728
if hasattr(_libs['iViewXAPI'], 'iV_SelectREDGeometry'):
    SelectREDGeometry = _libs['iViewXAPI'].iV_SelectREDGeometry
    SelectREDGeometry.argtypes = [c_char_p]
    SelectREDGeometry.restype = c_int

# <input>: 1743
if hasattr(_libs['iViewXAPI'], 'iV_SetEventCallback'):
    SetEventCallback = _libs['iViewXAPI'].iV_SetEventCallback
    SetEventCallback.argtypes = [pDLLSetEvent]
    SetEventCallback.restype = c_int

# <input>: 1757
if hasattr(_libs['iViewXAPI'], 'iV_SetEventDetectionParameter'):
    SetEventDetectionParameter = _libs[
        'iViewXAPI'].iV_SetEventDetectionParameter
    SetEventDetectionParameter.argtypes = [c_int, c_int]
    SetEventDetectionParameter.restype = c_int

# <input>: 1771
if hasattr(_libs['iViewXAPI'], 'iV_SetEyeImageCallback'):
    SetEyeImageCallback = _libs['iViewXAPI'].iV_SetEyeImageCallback
    SetEyeImageCallback.argtypes = [pDLLSetEyeImage]
    SetEyeImageCallback.restype = c_int

# <input>: 1783
if hasattr(_libs['iViewXAPI'], 'iV_SetLicense'):
    SetLicense = _libs['iViewXAPI'].iV_SetLicense
    SetLicense.argtypes = [c_char_p]
    SetLicense.restype = c_int

# <input>: 1797
if hasattr(_libs['iViewXAPI'], 'iV_SetLogger'):
    SetLogger = _libs['iViewXAPI'].iV_SetLogger
    SetLogger.argtypes = [c_int, c_char_p]
    SetLogger.restype = c_int

# <input>: 1810
if hasattr(_libs['iViewXAPI'], 'iV_SetResolution'):
    SetResolution = _libs['iViewXAPI'].iV_SetResolution
    SetResolution.argtypes = [c_int, c_int]
    SetResolution.restype = c_int

# <input>: 1825
if hasattr(_libs['iViewXAPI'], 'iV_SetSampleCallback'):
    SetSampleCallback = _libs['iViewXAPI'].iV_SetSampleCallback
    SetSampleCallback.argtypes = [pDLLSetSample]
    SetSampleCallback.restype = c_int

# <input>: 1839
if hasattr(_libs['iViewXAPI'], 'iV_SetSceneVideoCallback'):
    SetSceneVideoCallback = _libs['iViewXAPI'].iV_SetSceneVideoCallback
    SetSceneVideoCallback.argtypes = [pDLLSetSceneVideo]
    SetSceneVideoCallback.restype = c_int

# <input>: 1853
if hasattr(_libs['iViewXAPI'], 'iV_SetTrackingMonitorCallback'):
    SetTrackingMonitorCallback = _libs[
        'iViewXAPI'].iV_SetTrackingMonitorCallback
    SetTrackingMonitorCallback.argtypes = [pDLLSetTrackingMonitor]
    SetTrackingMonitorCallback.restype = c_int

# <input>: 1867
if hasattr(_libs['iViewXAPI'], 'iV_SetTrackingParameter'):
    SetTrackingParameter = _libs['iViewXAPI'].iV_SetTrackingParameter
    SetTrackingParameter.argtypes = [c_int, c_int, c_int]
    SetTrackingParameter.restype = c_int

# <input>: 1883
if hasattr(_libs['iViewXAPI'], 'iV_SetupCalibration'):
    SetupCalibration = _libs['iViewXAPI'].iV_SetupCalibration
    SetupCalibration.argtypes = [POINTER(struct_CalibrationStruct)]
    SetupCalibration.restype = c_int

# <input>: 1899
if hasattr(_libs['iViewXAPI'], 'iV_SetREDGeometry'):
    SetREDGeometry = _libs['iViewXAPI'].iV_SetREDGeometry
    SetREDGeometry.argtypes = [POINTER(struct_REDGeometryStruct)]
    SetREDGeometry.restype = c_int

# <input>: 1915
if hasattr(_libs['iViewXAPI'], 'iV_ShowAccuracyMonitor'):
    ShowAccuracyMonitor = _libs['iViewXAPI'].iV_ShowAccuracyMonitor
    ShowAccuracyMonitor.argtypes = []
    ShowAccuracyMonitor.restype = c_int

# <input>: 1926
if hasattr(_libs['iViewXAPI'], 'iV_ShowEyeImageMonitor'):
    ShowEyeImageMonitor = _libs['iViewXAPI'].iV_ShowEyeImageMonitor
    ShowEyeImageMonitor.argtypes = []
    ShowEyeImageMonitor.restype = c_int

# <input>: 1939
if hasattr(_libs['iViewXAPI'], 'iV_ShowSceneVideoMonitor'):
    ShowSceneVideoMonitor = _libs['iViewXAPI'].iV_ShowSceneVideoMonitor
    ShowSceneVideoMonitor.argtypes = []
    ShowSceneVideoMonitor.restype = c_int

# <input>: 1953
if hasattr(_libs['iViewXAPI'], 'iV_ShowTrackingMonitor'):
    ShowTrackingMonitor = _libs['iViewXAPI'].iV_ShowTrackingMonitor
    ShowTrackingMonitor.argtypes = []
    ShowTrackingMonitor.restype = c_int

# <input>: 1969
if hasattr(_libs['iViewXAPI'], 'iV_Start'):
    Start = _libs['iViewXAPI'].iV_Start
    Start.argtypes = [enum_ETApplication]
    Start.restype = c_int

# <input>: 1985
if hasattr(_libs['iViewXAPI'], 'iV_StartRecording'):
    StartRecording = _libs['iViewXAPI'].iV_StartRecording
    StartRecording.argtypes = []
    StartRecording.restype = c_int

# <input>: 2001
if hasattr(_libs['iViewXAPI'], 'iV_StopRecording'):
    StopRecording = _libs['iViewXAPI'].iV_StopRecording
    StopRecording.argtypes = []
    StopRecording.restype = c_int

# <input>: 2013
if hasattr(_libs['iViewXAPI'], 'iV_TestTTL'):
    TestTTL = _libs['iViewXAPI'].iV_TestTTL
    TestTTL.argtypes = [c_int]
    TestTTL.restype = c_int

# <input>: 2036
if hasattr(_libs['iViewXAPI'], 'iV_Validate'):
    Validate = _libs['iViewXAPI'].iV_Validate
    Validate.argtypes = []
    Validate.restype = c_int

SystemInfoStruct = struct_SystemInfoStruct  # <input>: 258

CalibrationPointStruct = struct_CalibrationPointStruct  # <input>: 294

EyeDataStruct = struct_EyeDataStruct  # <input>: 315

SampleStruct = struct_SampleStruct  # <input>: 344

SampleStruct32 = struct_SampleStruct32  # <input>: 368

EventStruct = struct_EventStruct  # <input>: 392

EventStruct32 = struct_EventStruct32  # <input>: 426

EyePositionStruct = struct_EyePositionStruct  # <input>: 466

TrackingStatusStruct = struct_TrackingStatusStruct  # <input>: 499

AccuracyStruct = struct_AccuracyStruct  # <input>: 522

CalibrationStruct = struct_CalibrationStruct  # <input>: 545

REDGeometryStruct = struct_REDGeometryStruct  # <input>: 587

ImageStruct = struct_ImageStruct  # <input>: 656

DateStruct = struct_DateStruct  # <input>: 678

AOIRectangleStruct = struct_AOIRectangleStruct  # <input>: 697

AOIStruct = struct_AOIStruct  # <input>: 719

# Begin inserted files

# Begin "prepend_contents.py"

# File: prepend_contents.py
# Contents of this file is added to the end of the ctypesgen created file for the iViewAPI
#  python ctypes wrapper.


from ctypes import create_string_buffer as StringBuffer
# Now user can call StringBuffer('some text',SIZE) to create a C char array ptr.
# SIZE defines the max size of the text string and is required if the function was defined
# with a fixed size char array.
#
# i.e.  char param[255]  => param = tringBuffer('some text',255)
#
# If the string param was defined as a char* requiring a null terminated string,
# then the SIZE arg can be left out.
#
# char *param  =>  param = StringBuffer('some text')
#


#
# Useful ctype definitions with user meaning:
#
from ctypes import c_longlong
EyeTrackerTimestamp = c_longlong


#
# Not sure why, but defines are not being generated, so mannnually adding them
#  here based on these .h file defines
#


# define RET_SUCCESS													1
# define RET_NO_VALID_DATA											2
# define RET_CALIBRATION_ABORTED										3
# define RET_SERVER_IS_RUNNING										4
# define RET_CALIBRATION_NOT_IN_PROGRESS								5
# define RET_WINDOW_IS_OPEN											11
# define RET_WINDOW_IS_CLOSED										12
RET_SUCCESS = 1
RET_NO_VALID_DATA = 2
RET_CALIBRATION_ABORTED = 3
RET_SERVER_IS_RUNNING = 4
RET_CALIBRATION_NOT_IN_PROGRESS = 5
RET_WINDOW_IS_OPEN = 11
RET_WINDOW_IS_CLOSED = 12

# define ERR_COULD_NOT_CONNECT										100
# define ERR_NOT_CONNECTED											101
# define ERR_NOT_CALIBRATED											102
# define ERR_NOT_VALIDATED											103
# define ERR_EYETRACKING_APPLICATION_NOT_RUNNING						104
# define ERR_WRONG_COMMUNICATION_PARAMETER							105
# define ERR_WRONG_DEVICE											111
# define ERR_WRONG_PARAMETER											112
# define ERR_WRONG_CALIBRATION_METHOD								113
# define ERR_CALIBRATION_TIMEOUT										114
# define ERR_TRACKING_NOT_STABLE										115
# define ERR_CREATE_SOCKET											121
# define ERR_CONNECT_SOCKET											122
# define ERR_BIND_SOCKET												123
# define ERR_DELETE_SOCKET											124
# define ERR_NO_RESPONSE_FROM_IVIEWX									131
# define ERR_INVALID_IVIEWX_VERSION									132
# define ERR_WRONG_IVIEWX_VERSION									133
# define ERR_ACCESS_TO_FILE											171
# define ERR_SOCKET_CONNECTION										181
# define ERR_EMPTY_DATA_BUFFER										191
# define ERR_RECORDING_DATA_BUFFER									192
# define ERR_FULL_DATA_BUFFER										193
# define ERR_IVIEWX_IS_NOT_READY										194
# define ERR_IVIEWX_NOT_FOUND										201
# define ERR_IVIEWX_PATH_NOT_FOUND									202
# define ERR_IVIEWX_ACCESS_DENIED									203
# define ERR_IVIEWX_ACCESS_INCOMPLETE								204
# define ERR_IVIEWX_OUT_OF_MEMORY									205
# define ERR_CAMERA_NOT_FOUND										211
# define ERR_WRONG_CAMERA											212
# define ERR_WRONG_CAMERA_PORT										213
# define ERR_COULD_NOT_OPEN_PORT										220
# define ERR_COULD_NOT_CLOSE_PORT									221
# define ERR_AOI_ACCESS												222
# define ERR_AOI_NOT_DEFINED											223
# define ERR_FEATURE_NOT_LICENSED									250
# define ERR_DEPRECATED_FUNCTION										300
# define ERR_INITIALIZATION											400
ERR_COULD_NOT_CONNECT = 100
ERR_NOT_CONNECTED = 101
ERR_NOT_CALIBRATED = 102
ERR_NOT_VALIDATED = 103
ERR_EYETRACKING_APPLICATION_NOT_RUNNING = 104
ERR_WRONG_COMMUNICATION_PARAMETER = 105
ERR_WRONG_DEVICE = 111
ERR_WRONG_PARAMETER = 112
ERR_WRONG_CALIBRATION_METHOD = 113
ERR_CALIBRATION_TIMEOUT = 114
ERR_TRACKING_NOT_STABLE = 115
ERR_CREATE_SOCKET = 121
ERR_CONNECT_SOCKET = 122
ERR_BIND_SOCKET = 123
ERR_DELETE_SOCKET = 124
ERR_NO_RESPONSE_FROM_IVIEWX = 131
ERR_INVALID_IVIEWX_VERSION = 132
ERR_WRONG_IVIEWX_VERSION = 133
ERR_ACCESS_TO_FILE = 171
ERR_SOCKET_CONNECTION = 181
ERR_EMPTY_DATA_BUFFER = 191
ERR_RECORDING_DATA_BUFFER = 192
ERR_FULL_DATA_BUFFER = 193
ERR_IVIEWX_IS_NOT_READY = 194
ERR_IVIEWX_NOT_FOUND = 201
ERR_IVIEWX_PATH_NOT_FOUND = 202
ERR_IVIEWX_ACCESS_DENIED = 203
ERR_IVIEWX_ACCESS_INCOMPLETE = 204
ERR_IVIEWX_OUT_OF_MEMORY = 205
ERR_CAMERA_NOT_FOUND = 211
ERR_WRONG_CAMERA = 212
ERR_WRONG_CAMERA_PORT = 213
ERR_COULD_NOT_OPEN_PORT = 220
ERR_COULD_NOT_CLOSE_PORT = 221
ERR_AOI_ACCESS = 222
ERR_AOI_NOT_DEFINED = 223
ERR_FEATURE_NOT_LICENSED = 250
ERR_DEPRECATED_FUNCTION = 300
ERR_INITIALIZATION = 400

#
# With these defines it is possible to setup the logging status
# for the function "iV_Log". With "iV_Log" it is possible to observe the
# communication between a users application and iView X and/or function
# calls. Log levels can be combined (e.g. LOG_BUG | LOG_IV_COMMAND | LOG_ETCOM).
#
#
# define LOG_LEVEL_BUG					1
# define LOG_LEVEL_iV_FCT				2
# define LOG_LEVEL_ALL_FCT				4
# define LOG_LEVEL_IV_COMMAND			8
# define LOG_LEVEL_RECV_IV_COMMAND		16
LOG_LEVEL_BUG = 1
LOG_LEVEL_iV_FCT = 2
LOG_LEVEL_ALL_FCT = 4
LOG_LEVEL_IV_COMMAND = 8
LOG_LEVEL_RECV_IV_COMMAND = 16


#
# With ET_PARAM_ and function "iV_SetTrackingParameter" it is possible
# to change iView X tracking parameters, for example pupil threshold and
# corneal reflex thresholds, eye image contours, and other parameters.
#
# Important note: This function can strongly affect tracking stability of
# your iView X system. Only experienced users should use this function.
#
# define ET_PARAM_EYE_LEFT				0
# define ET_PARAM_EYE_RIGHT				1
# define ET_PARAM_EYE_BOTH				2
# define ET_PARAM_PUPIL_THRESHOLD		0
# define ET_PARAM_REFLEX_THRESHOLD		1
# define ET_PARAM_SHOW_AOI				2
# define ET_PARAM_SHOW_CONTOUR			3
# define ET_PARAM_SHOW_PUPIL				4
# define ET_PARAM_SHOW_REFLEX			5
# define ET_PARAM_DYNAMIC_THRESHOLD		6
# define ET_PARAM_PUPIL_AREA				11
# define ET_PARAM_PUPIL_PERIMETER		12
# define ET_PARAM_PUPIL_DENSITY			13
# define ET_PARAM_REFLEX_PERIMETER		14
# define ET_PARAM_REFLEX_PUPIL_DISTANCE	15
# define ET_PARAM_MONOCULAR				16
# define ET_PARAM_SMARTBINOCULAR			17
# define ET_PARAM_BINOCULAR				18

ET_PARAM_EYE_LEFT = 0
ET_PARAM_EYE_RIGHT = 1
ET_PARAM_EYE_BOTH = 2
ET_PARAM_PUPIL_THRESHOLD = 0
ET_PARAM_REFLEX_THRESHOLD = 1
ET_PARAM_SHOW_AOI = 2
ET_PARAM_SHOW_CONTOUR = 3
ET_PARAM_SHOW_PUPIL = 4
ET_PARAM_SHOW_REFLEX = 5
ET_PARAM_DYNAMIC_THRESHOLD = 6
ET_PARAM_PUPIL_AREA = 11
ET_PARAM_PUPIL_PERIMETER = 12
ET_PARAM_PUPIL_DENSITY = 13
ET_PARAM_REFLEX_PERIMETER = 14
ET_PARAM_REFLEX_PUPIL_DISTANCE = 15
ET_PARAM_MONOCULAR = 16
ET_PARAM_SMARTBINOCULAR = 17
ET_PARAM_BINOCULAR = 18

#
# The enumeration ETDevice can be used in connection with
# "iV_GetSystemInfo" to get information about which type of device is
# connected to iView X. It is part of the "SystemInfoStruct".
# (NONE = 0, RED = 1, REDm=2 HiSpeed = 3, MRI/MEG = 4, HED = 5, ETG = 6, Custom = 7)
#
# Creating the enum as a dict for utility..
etDeviceTypes = dict(
    NONE=0,
    RED=1,
    REDm=2,
    HiSpeed=3,
    MRI=4,
    HED=5,
    ETG=6,
    Custom=7)

for k, v in etDeviceTypes.items():
    etDeviceTypes[v] = k


############

#/**
#* @enum ETApplication
#*
#* @brief ETApplication can be used to start iView X or iView X OEM
#* (eyetracking-server) application dependent to the used eye tracking
#* device. Set this as a parameter in @ref iV_Start function.
#*/
etApplication = dict(iViewX=0, iViewXOEM=1)


#/**
#* @enum FilterType
#*
#* @brief FilterType can be used to select the filter that is used
#* with @ref iV_ConfigureFilter
#*/
etFilterType = dict(
    #//! left and right gaze data channels are averaged
    #//! the type of the parameter data from @ref iV_ConfigureFilter has to be converted to int*
    #//! The value of data can be [0;1] where 0 means averaging is disabled and 1 means averaging is enabled
    Average_Disabled=c_int(0),
    Average_Enabled=c_int(1))


#/**
#* @enum FilterAction
#*
#* @brief FilterType can be used to select the action that is performed
#* when calling @ref iV_ConfigureFilter
#*/
etFilterAction = dict(
    #//! query the current filter status
    Query=c_int(0),
    #//! configure filter parameters
    Set=c_int(1))


#/**
#* @enum CalibrationStatusEnum
#*
#* @brief This enum provides information about the eyetracking-server calibration status. If the
#* device is not calibrated the eyetracking-server won't deliver valid gaze data. Use the functions
#* @ref iV_GetCalibrationStatus to retrieve the calibration status and
#* @ref iV_Calibrate to perform a calibration.
#*/
etCalibrationStatusEnum = dict(
    #//! calibration status is unknown (i.e. if the connection is not established)
    calibrationUnknown=0,

    #//! the device is not calibrated and will not deliver valid gaze data
    calibrationInvalid=1,

    #//! the device is calibrated and will deliver valid gaze data
    calibrationValid=2,

    #//! the device is currently performing a calibration
    calibrationInProgress=3)

#/**
#* @enum REDGeometryEnum
#*
#* @brief uses to the define the content of @ref REDGeometryStruct
#*/
etREDGeometryEnum = dict(
    #//! use monitor integrated mode
    monitorIntegrated=0,
    #//! use standalone mode
    standalone=1)


# End "prepend_contents.py"

# 1 inserted files
# End inserted files
