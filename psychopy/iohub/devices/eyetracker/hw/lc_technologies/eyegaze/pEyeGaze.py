"""
ioHub
ioHub Common Eye Tracker Interface
.. file: ioHub/devices/eyetracker/hw/lc_technologies/eyegaze/pEyeGaze.py

Copyright (C) 2012-2013 XXXXXXXX, iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson + contributors
"""

# Begin preamble

import ctypes, os, sys
from ctypes import *

_EYEGAZE_DIR='C:\\EyeGaze\\'
os.environ['PATH'] = _EYEGAZE_DIR + ';' + os.environ['PATH']

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

class UserString:
    def __init__(self, seq):
        if isinstance(seq, basestring):
            self.data = seq
        elif isinstance(seq, UserString):
            self.data = seq.data[:]
        else:
            self.data = str(seq)
    def __str__(self): return str(self.data)
    def __repr__(self): return repr(self.data)
    def __int__(self): return int(self.data)
    def __long__(self): return long(self.data)
    def __float__(self): return float(self.data)
    def __complex__(self): return complex(self.data)
    def __hash__(self): return hash(self.data)

    def __cmp__(self, string):
        if isinstance(string, UserString):
            return cmp(self.data, string.data)
        else:
            return cmp(self.data, string)
    def __contains__(self, char):
        return char in self.data

    def __len__(self): return len(self.data)
    def __getitem__(self, index): return self.__class__(self.data[index])
    def __getslice__(self, start, end):
        start = max(start, 0); end = max(end, 0)
        return self.__class__(self.data[start:end])

    def __add__(self, other):
        if isinstance(other, UserString):
            return self.__class__(self.data + other.data)
        elif isinstance(other, basestring):
            return self.__class__(self.data + other)
        else:
            return self.__class__(self.data + str(other))
    def __radd__(self, other):
        if isinstance(other, basestring):
            return self.__class__(other + self.data)
        else:
            return self.__class__(str(other) + self.data)
    def __mul__(self, n):
        return self.__class__(self.data*n)
    __rmul__ = __mul__
    def __mod__(self, args):
        return self.__class__(self.data % args)

    # the following methods are defined in alphabetical order:
    def capitalize(self): return self.__class__(self.data.capitalize())
    def center(self, width, *args):
        return self.__class__(self.data.center(width, *args))
    def count(self, sub, start=0, end=sys.maxint):
        return self.data.count(sub, start, end)
    def decode(self, encoding=None, errors=None): # XXX improve this?
        if encoding:
            if errors:
                return self.__class__(self.data.decode(encoding, errors))
            else:
                return self.__class__(self.data.decode(encoding))
        else:
            return self.__class__(self.data.decode())
    def encode(self, encoding=None, errors=None): # XXX improve this?
        if encoding:
            if errors:
                return self.__class__(self.data.encode(encoding, errors))
            else:
                return self.__class__(self.data.encode(encoding))
        else:
            return self.__class__(self.data.encode())
    def endswith(self, suffix, start=0, end=sys.maxint):
        return self.data.endswith(suffix, start, end)
    def expandtabs(self, tabsize=8):
        return self.__class__(self.data.expandtabs(tabsize))
    def find(self, sub, start=0, end=sys.maxint):
        return self.data.find(sub, start, end)
    def index(self, sub, start=0, end=sys.maxint):
        return self.data.index(sub, start, end)
    def isalpha(self): return self.data.isalpha()
    def isalnum(self): return self.data.isalnum()
    def isdecimal(self): return self.data.isdecimal()
    def isdigit(self): return self.data.isdigit()
    def islower(self): return self.data.islower()
    def isnumeric(self): return self.data.isnumeric()
    def isspace(self): return self.data.isspace()
    def istitle(self): return self.data.istitle()
    def isupper(self): return self.data.isupper()
    def join(self, seq): return self.data.join(seq)
    def ljust(self, width, *args):
        return self.__class__(self.data.ljust(width, *args))
    def lower(self): return self.__class__(self.data.lower())
    def lstrip(self, chars=None): return self.__class__(self.data.lstrip(chars))
    def partition(self, sep):
        return self.data.partition(sep)
    def replace(self, old, new, maxsplit=-1):
        return self.__class__(self.data.replace(old, new, maxsplit))
    def rfind(self, sub, start=0, end=sys.maxint):
        return self.data.rfind(sub, start, end)
    def rindex(self, sub, start=0, end=sys.maxint):
        return self.data.rindex(sub, start, end)
    def rjust(self, width, *args):
        return self.__class__(self.data.rjust(width, *args))
    def rpartition(self, sep):
        return self.data.rpartition(sep)
    def rstrip(self, chars=None): return self.__class__(self.data.rstrip(chars))
    def split(self, sep=None, maxsplit=-1):
        return self.data.split(sep, maxsplit)
    def rsplit(self, sep=None, maxsplit=-1):
        return self.data.rsplit(sep, maxsplit)
    def splitlines(self, keepends=0): return self.data.splitlines(keepends)
    def startswith(self, prefix, start=0, end=sys.maxint):
        return self.data.startswith(prefix, start, end)
    def strip(self, chars=None): return self.__class__(self.data.strip(chars))
    def swapcase(self): return self.__class__(self.data.swapcase())
    def title(self): return self.__class__(self.data.title())
    def translate(self, *args):
        return self.__class__(self.data.translate(*args))
    def upper(self): return self.__class__(self.data.upper())
    def zfill(self, width): return self.__class__(self.data.zfill(width))

class MutableString(UserString):
    """mutable string objects

    Python strings are immutable objects.  This has the advantage, that
    strings may be used as dictionary keys.  If this property isn't needed
    and you insist on changing string values in place instead, you may cheat
    and use MutableString.

    But the purpose of this class is an educational one: to prevent
    people from inventing their own mutable string class derived
    from UserString and than forget thereby to remove (override) the
    __hash__ method inherited from UserString.  This would lead to
    errors that would be very hard to track down.

    A faster and better solution is to rewrite your program using lists."""
    def __init__(self, string=""):
        self.data = string
    def __hash__(self):
        raise TypeError("unhashable type (it is mutable)")
    def __setitem__(self, index, sub):
        if index < 0:
            index += len(self.data)
        if index < 0 or index >= len(self.data): raise IndexError
        self.data = self.data[:index] + sub + self.data[index+1:]
    def __delitem__(self, index):
        if index < 0:
            index += len(self.data)
        if index < 0 or index >= len(self.data): raise IndexError
        self.data = self.data[:index] + self.data[index+1:]
    def __setslice__(self, start, end, sub):
        start = max(start, 0); end = max(end, 0)
        if isinstance(sub, UserString):
            self.data = self.data[:start]+sub.data+self.data[end:]
        elif isinstance(sub, basestring):
            self.data = self.data[:start]+sub+self.data[end:]
        else:
            self.data =  self.data[:start]+str(sub)+self.data[end:]
    def __delslice__(self, start, end):
        start = max(start, 0); end = max(end, 0)
        self.data = self.data[:start] + self.data[end:]
    def immutable(self):
        return UserString(self.data)
    def __iadd__(self, other):
        if isinstance(other, UserString):
            self.data += other.data
        elif isinstance(other, basestring):
            self.data += other
        else:
            self.data += str(other)
        return self
    def __imul__(self, n):
        self.data *= n
        return self

class String(MutableString, Union):

    _fields_ = [('raw', POINTER(c_char)),
                ('data', c_char_p)]

    def __init__(self, obj=""):
        if isinstance(obj, (str, unicode, UserString)):
            self.data = str(obj)
        else:
            self.raw = obj

    def __len__(self):
        return self.data and len(self.data) or 0

    def from_param(cls, obj):
        # Convert None or 0
        if obj is None or obj == 0:
            return cls(POINTER(c_char)())

        # Convert from String
        elif isinstance(obj, String):
            return obj

        # Convert from str
        elif isinstance(obj, str):
            return cls(obj)

        # Convert from c_char_p
        elif isinstance(obj, c_char_p):
            return obj

        # Convert from POINTER(c_char)
        elif isinstance(obj, POINTER(c_char)):
            return obj

        # Convert from raw pointer
        elif isinstance(obj, int):
            return cls(cast(obj, POINTER(c_char)))

        # Convert from object
        else:
            return String.from_param(obj._as_parameter_)
    from_param = classmethod(from_param)

def ReturnString(obj, func=None, arguments=None):
    return String.from_param(obj)

# As of ctypes 1.0, ctypes does not support custom error-checking
# functions on callbacks, nor does it support custom datatypes on
# callbacks, so we must ensure that all callbacks return
# primitive datatypes.
#
# Non-primitive return values wrapped with UNCHECKED won't be
# typechecked, and will be converted to c_void_p.
def UNCHECKED(type):
    if (hasattr(type, "_type_") and isinstance(type._type_, str)
        and type._type_ != "P"):
        return type
    else:
        return c_void_p

# ctypes doesn't have direct support for variadic functions, so we have to write
# our own wrapper class
class _variadic_function(object):
    def __init__(self,func,restype,argtypes):
        self.func=func
        self.func.restype=restype
        self.argtypes=argtypes
    def _as_parameter_(self):
        # So we can pass this variadic function as a function pointer
        return self.func
    def __call__(self,*args):
        fixed_args=[]
        i=0
        for argtype in self.argtypes:
            # Typecheck what we can
            fixed_args.append(argtype.from_param(args[i]))
            i+=1
        return self.func(*fixed_args+list(args[i:]))

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

import os.path, re, sys, glob
import ctypes
import ctypes.util

def _environ_path(name):
    if name in os.environ:
        return os.environ[name].split(":")
    else:
        return []

class LibraryLoader(object):
    def __init__(self):
        self.other_dirs=[]

    def load_library(self,libname):
        """Given the name of a library, load it."""
        paths = self.getpaths(libname)

        for path in paths:
            if os.path.exists(path):
                return self.load(path)

        raise ImportError("%s not found." % libname)

    def load(self,path):
        """Given a path to a library, load it."""
        try:
            # Darwin requires dlopen to be called with mode RTLD_GLOBAL instead
            # of the default RTLD_LOCAL.  Without this, you end up with
            # libraries not being loadable, resulting in "Symbol not found"
            # errors
            if sys.platform == 'darwin':
                return ctypes.CDLL(path, ctypes.RTLD_GLOBAL)
            else:
                return ctypes.cdll.LoadLibrary(path)
        except OSError,e:
            raise ImportError(e)

    def getpaths(self,libname):
        """Return a list of paths where the library might be found."""
        if os.path.isabs(libname):
            yield libname
        else:
            # FIXME / TODO return '.' and os.path.dirname(__file__)
            for path in self.getplatformpaths(libname):
                yield path

            path = ctypes.util.find_library(libname)
            if path: yield path

    def getplatformpaths(self, libname):
        return []

# Darwin (Mac OS X)

class DarwinLibraryLoader(LibraryLoader):
    name_formats = ["lib%s.dylib", "lib%s.so", "lib%s.bundle", "%s.dylib",
                "%s.so", "%s.bundle", "%s"]

    def getplatformpaths(self,libname):
        if os.path.pathsep in libname:
            names = [libname]
        else:
            names = [format % libname for format in self.name_formats]

        for dir in self.getdirs(libname):
            for name in names:
                yield os.path.join(dir,name)

    def getdirs(self,libname):
        '''Implements the dylib search as specified in Apple documentation:

        http://developer.apple.com/documentation/DeveloperTools/Conceptual/
            DynamicLibraries/Articles/DynamicLibraryUsageGuidelines.html

        Before commencing the standard search, the method first checks
        the bundle's ``Frameworks`` directory if the application is running
        within a bundle (OS X .app).
        '''

        dyld_fallback_library_path = _environ_path("DYLD_FALLBACK_LIBRARY_PATH")
        if not dyld_fallback_library_path:
            dyld_fallback_library_path = [os.path.expanduser('~/lib'),
                                          '/usr/local/lib', '/usr/lib']

        dirs = []

        if '/' in libname:
            dirs.extend(_environ_path("DYLD_LIBRARY_PATH"))
        else:
            dirs.extend(_environ_path("LD_LIBRARY_PATH"))
            dirs.extend(_environ_path("DYLD_LIBRARY_PATH"))

        dirs.extend(self.other_dirs)
        dirs.append(".")
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
        for name in ("LD_LIBRARY_PATH",
                     "SHLIB_PATH", # HPUX
                     "LIBPATH", # OS/2, AIX
                     "LIBRARY_PATH", # BE/OS
                    ):
            if name in os.environ:
                directories.extend(os.environ[name].split(os.pathsep))
        directories.extend(self.other_dirs)
        directories.append(".")
        directories.append(os.path.dirname(__file__))

        try: directories.extend([dir.strip() for dir in open('/etc/ld.so.conf')])
        except IOError: pass

        directories.extend(['/lib', '/usr/lib', '/lib64', '/usr/lib64'])

        cache = {}
        lib_re = re.compile(r'lib(.*)\.s[ol]')
        ext_re = re.compile(r'\.s[ol]$')
        for dir in directories:
            try:
                for path in glob.glob("%s/*.s[ol]*" % dir):
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
        if result: yield result

        path = ctypes.util.find_library(libname)
        if path: yield os.path.join("/lib",path)

# Windows

class _WindowsLibrary(object):
    def __init__(self, path):
        self.cdll = ctypes.cdll.LoadLibrary(path)
        self.windll = ctypes.windll.LoadLibrary(path)

    def __getattr__(self, name):
        try: return getattr(self.cdll,name)
        except AttributeError:
            try: return getattr(self.windll,name)
            except AttributeError:
                raise

class WindowsLibraryLoader(LibraryLoader):
    name_formats = ["%s.dll", "lib%s.dll", "%slib.dll"]

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
                raise ImportError("%s not found." % libname)
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
    "darwin":   DarwinLibraryLoader,
    "cygwin":   WindowsLibraryLoader,
    "win32":    WindowsLibraryLoader
}

loader = loaderclass.get(sys.platform, PosixLibraryLoader)()

def add_library_search_dirs(other_dirs):
    loader.other_dirs = other_dirs

load_library = loader.load_library

del loaderclass

# End loader

# Begin libraries

_libs["lctigaze"] = load_library("lctigaze")

# 1 libraries
# End libraries

# No modules

NULL = None # <built-in>

PVOID = POINTER(None) # <input>: 54

# <input>: 72
class struct__BITMAPINFOHEADER(Structure):
    pass

struct__BITMAPINFOHEADER.__slots__ = [
    'biSize',
    'biWidth',
    'biHeight',
    'biPlanes',
    'biBitCount',
    'biCompression',
    'biSizeImage',
    'biXPelsPerMeter',
    'biYPelsPerMeter',
    'biClrUsed',
    'biClrImportant',
]
struct__BITMAPINFOHEADER._fields_ = [
    ('biSize', c_ulong),
    ('biWidth', c_long),
    ('biHeight', c_long),
    ('biPlanes', c_ushort),
    ('biBitCount', c_ushort),
    ('biCompression', c_ulong),
    ('biSizeImage', c_ulong),
    ('biXPelsPerMeter', c_long),
    ('biYPelsPerMeter', c_long),
    ('biClrUsed', c_ulong),
    ('biClrImportant', c_ulong),
]

BITMAPINFOHEADER = struct__BITMAPINFOHEADER # <input>: 72

# <input>: 79
class struct__RGBQUAD(Structure):
    pass

struct__RGBQUAD.__slots__ = [
    'rgbBlue',
    'rgbGreen',
    'rgbRed',
    'rgbReserved',
]
struct__RGBQUAD._fields_ = [
    ('rgbBlue', c_ubyte),
    ('rgbGreen', c_ubyte),
    ('rgbRed', c_ubyte),
    ('rgbReserved', c_ubyte),
]

RGBQUAD = struct__RGBQUAD # <input>: 79

# <input>: 84
class struct__BITMAPINFO(Structure):
    pass

struct__BITMAPINFO.__slots__ = [
    'bmiHeader',
    'bmiColors',
]
struct__BITMAPINFO._fields_ = [
    ('bmiHeader', BITMAPINFOHEADER),
    ('bmiColors', RGBQUAD * 1),
]

BITMAPINFO = struct__BITMAPINFO # <input>: 84

# <input>: 176
class struct__stEgData(Structure):
    pass

# <input>: 91
class struct__stEgControl(Structure):
    pass

struct__stEgControl.__slots__ = [
    'pstEgData',
    'iNDataSetsInRingBuffer',
    'bTrackingActive',
    'iScreenWidthPix',
    'iScreenHeightPix',
    'bEgCameraDisplayActive',
    'iEyeImagesScreenPos',
    'iCommType',
    'pszCommName',
    'iVisionSelect',
    'iNPointsAvailable',
    'iNBufferOverflow',
    'iSamplePerSec',
    'fHorzPixPerMm',
    'fVertPixPerMm',
    'pvEgVideoBufferAddress',
    'hEyegaze',
]
struct__stEgControl._fields_ = [
    ('pstEgData', POINTER(struct__stEgData)),
    ('iNDataSetsInRingBuffer', c_int),
    ('bTrackingActive', c_int),
    ('iScreenWidthPix', c_int),
    ('iScreenHeightPix', c_int),
    ('bEgCameraDisplayActive', c_int),
    ('iEyeImagesScreenPos', c_int),
    ('iCommType', c_int),
    ('pszCommName', POINTER(c_wchar)),
    ('iVisionSelect', c_int),
    ('iNPointsAvailable', c_int),
    ('iNBufferOverflow', c_int),
    ('iSamplePerSec', c_int),
    ('fHorzPixPerMm', c_float),
    ('fVertPixPerMm', c_float),
    ('pvEgVideoBufferAddress', POINTER(None)),
    ('hEyegaze', POINTER(None)),
]

struct__stEgData.__slots__ = [
    'bGazeVectorFound',
    'iIGaze',
    'iJGaze',
    'fPupilRadiusMm',
    'fXEyeballOffsetMm',
    'fYEyeballOffsetMm',
    'fFocusRangeImageTime',
    'fFocusRangeOffsetMm',
    'fLensExtOffsetMm',
    'ulCameraFieldCount',
    'dGazeTimeSec',
    'dAppMarkTimeSec',
    'iAppMarkCount',
    'dReportTimeSec',
]
struct__stEgData._fields_ = [
    ('bGazeVectorFound', c_int),
    ('iIGaze', c_int),
    ('iJGaze', c_int),
    ('fPupilRadiusMm', c_float),
    ('fXEyeballOffsetMm', c_float),
    ('fYEyeballOffsetMm', c_float),
    ('fFocusRangeImageTime', c_float),
    ('fFocusRangeOffsetMm', c_float),
    ('fLensExtOffsetMm', c_float),
    ('ulCameraFieldCount', c_ulong),
    ('dGazeTimeSec', c_double),
    ('dAppMarkTimeSec', c_double),
    ('iAppMarkCount', c_int),
    ('dReportTimeSec', c_double),
]

# <input>: 231
class struct__stEyeImageInfo(Structure):
    pass

struct__stEyeImageInfo.__slots__ = [
    'prgbEyeImage',
    'bmiEyeImage',
    'iWidth',
    'iHeight',
]
struct__stEyeImageInfo._fields_ = [
    ('prgbEyeImage', POINTER(c_ubyte)),
    ('bmiEyeImage', BITMAPINFO),
    ('iWidth', c_int),
    ('iHeight', c_int),
]

# <input>: 242
if hasattr(_libs['lctigaze'], 'EgInit'):
    EgInit = _libs['lctigaze'].EgInit
    EgInit.argtypes = [POINTER(struct__stEgControl)]
    EgInit.restype = c_int

# <input>: 246
if hasattr(_libs['lctigaze'], 'EgCalibrate'):
    EgCalibrate = _libs['lctigaze'].EgCalibrate
    EgCalibrate.argtypes = [POINTER(struct__stEgControl), PVOID, c_int]
    EgCalibrate.restype = None

# <input>: 251
if hasattr(_libs['lctigaze'], 'EgCalibrate1'):
    EgCalibrate1 = _libs['lctigaze'].EgCalibrate1
    EgCalibrate1.argtypes = [POINTER(struct__stEgControl), PVOID, c_int]
    EgCalibrate1.restype = None

# <input>: 256
if hasattr(_libs['lctigaze'], 'EgCalibrate2'):
    EgCalibrate2 = _libs['lctigaze'].EgCalibrate2
    EgCalibrate2.argtypes = [POINTER(struct__stEgControl), c_int]
    EgCalibrate2.restype = None

# <input>: 260
if hasattr(_libs['lctigaze'], 'EgGetData'):
    EgGetData = _libs['lctigaze'].EgGetData
    EgGetData.argtypes = [POINTER(struct__stEgControl)]
    EgGetData.restype = c_int

# <input>: 267
if hasattr(_libs['lctigaze'], 'EgGetEvent'):
    EgGetEvent = _libs['lctigaze'].EgGetEvent
    EgGetEvent.argtypes = [POINTER(struct__stEgControl), POINTER(None)]
    EgGetEvent.restype = c_int

# <input>: 270
if hasattr(_libs['lctigaze'], 'EgGetVersion'):
    EgGetVersion = _libs['lctigaze'].EgGetVersion
    EgGetVersion.argtypes = []
    EgGetVersion.restype = c_int

# <input>: 271
if hasattr(_libs['lctigaze'], 'EgExit'):
    EgExit = _libs['lctigaze'].EgExit
    EgExit.argtypes = [POINTER(struct__stEgControl)]
    EgExit.restype = c_int

# <input>: 275
if hasattr(_libs['lctigaze'], 'EgGetApplicationStartTimeSec'):
    EgGetApplicationStartTimeSec = _libs['lctigaze'].EgGetApplicationStartTimeSec
    EgGetApplicationStartTimeSec.argtypes = []
    EgGetApplicationStartTimeSec.restype = c_double

# <input>: 279
if hasattr(_libs['lctigaze'], 'EgLogFileOpen'):
    EgLogFileOpen = _libs['lctigaze'].EgLogFileOpen
    EgLogFileOpen.argtypes = [POINTER(struct__stEgControl), String, String]
    EgLogFileOpen.restype = c_int

# <input>: 283
if hasattr(_libs['lctigaze'], 'EgLogWriteColumnHeader'):
    EgLogWriteColumnHeader = _libs['lctigaze'].EgLogWriteColumnHeader
    EgLogWriteColumnHeader.argtypes = [POINTER(struct__stEgControl)]
    EgLogWriteColumnHeader.restype = None

# <input>: 285
if hasattr(_libs['lctigaze'], 'EgLogAppendText'):
    EgLogAppendText = _libs['lctigaze'].EgLogAppendText
    EgLogAppendText.argtypes = [POINTER(struct__stEgControl), String]
    EgLogAppendText.restype = None

# <input>: 288
if hasattr(_libs['lctigaze'], 'EgLogStart'):
    EgLogStart = _libs['lctigaze'].EgLogStart
    EgLogStart.argtypes = [POINTER(struct__stEgControl)]
    EgLogStart.restype = None

# <input>: 290
if hasattr(_libs['lctigaze'], 'EgLogStop'):
    EgLogStop = _libs['lctigaze'].EgLogStop
    EgLogStop.argtypes = [POINTER(struct__stEgControl)]
    EgLogStop.restype = None

# <input>: 292
if hasattr(_libs['lctigaze'], 'EgLogMark'):
    EgLogMark = _libs['lctigaze'].EgLogMark
    EgLogMark.argtypes = [POINTER(struct__stEgControl)]
    EgLogMark.restype = c_uint

# <input>: 294
if hasattr(_libs['lctigaze'], 'EgLogFileClose'):
    EgLogFileClose = _libs['lctigaze'].EgLogFileClose
    EgLogFileClose.argtypes = [POINTER(struct__stEgControl)]
    EgLogFileClose.restype = None

# <input>: 297
if hasattr(_libs['lctigaze'], 'EgSetScreenDimensions'):
    EgSetScreenDimensions = _libs['lctigaze'].EgSetScreenDimensions
    EgSetScreenDimensions.argtypes = [POINTER(struct__stEgControl), c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int]
    EgSetScreenDimensions.restype = None

# <input>: 307
if hasattr(_libs['lctigaze'], 'EgInitScreenDimensions'):
    EgInitScreenDimensions = _libs['lctigaze'].EgInitScreenDimensions
    EgInitScreenDimensions.argtypes = [POINTER(struct__stEgControl), c_int, c_int, c_int, c_int, c_int, c_int, c_int, c_int]
    EgInitScreenDimensions.restype = None

# <input>: 317
if hasattr(_libs['lctigaze'], 'EgUpdateScreenResolutions'):
    EgUpdateScreenResolutions = _libs['lctigaze'].EgUpdateScreenResolutions
    EgUpdateScreenResolutions.argtypes = [c_int, c_int]
    EgUpdateScreenResolutions.restype = None

# <input>: 320
if hasattr(_libs['lctigaze'], 'EgUpdateMonPixelOffsets'):
    EgUpdateMonPixelOffsets = _libs['lctigaze'].EgUpdateMonPixelOffsets
    EgUpdateMonPixelOffsets.argtypes = [c_int, c_int]
    EgUpdateMonPixelOffsets.restype = None

# <input>: 323
if hasattr(_libs['lctigaze'], 'EgUpdateWindowParameters'):
    EgUpdateWindowParameters = _libs['lctigaze'].EgUpdateWindowParameters
    EgUpdateWindowParameters.argtypes = [c_int, c_int, c_int, c_int]
    EgUpdateWindowParameters.restype = None

# <input>: 328
for _lib in _libs.itervalues():
    if not hasattr(_lib, 'EgWindowPixFromMonMm'):
        continue
    EgWindowPixFromMonMm = _lib.EgWindowPixFromMonMm
    EgWindowPixFromMonMm.argtypes = [POINTER(c_int), POINTER(c_int), c_float, c_float]
    EgWindowPixFromMonMm.restype = None
    break

# <input>: 333
for _lib in _libs.itervalues():
    if not hasattr(_lib, 'MonMmFromEgWindowPix'):
        continue
    MonMmFromEgWindowPix = _lib.MonMmFromEgWindowPix
    MonMmFromEgWindowPix.argtypes = [POINTER(c_float), POINTER(c_float), POINTER(c_float), c_int, c_int]
    MonMmFromEgWindowPix.restype = None
    break

# <input>: 339
for _lib in _libs.itervalues():
    if not hasattr(_lib, 'EgMonitorPixFromMonMm'):
        continue
    EgMonitorPixFromMonMm = _lib.EgMonitorPixFromMonMm
    EgMonitorPixFromMonMm.argtypes = [POINTER(c_int), POINTER(c_int), c_float, c_float]
    EgMonitorPixFromMonMm.restype = None
    break

# <input>: 344
for _lib in _libs.itervalues():
    if not hasattr(_lib, 'MonMmFromEgMonitorPix'):
        continue
    MonMmFromEgMonitorPix = _lib.MonMmFromEgMonitorPix
    MonMmFromEgMonitorPix.argtypes = [POINTER(c_float), POINTER(c_float), POINTER(c_float), c_int, c_int]
    MonMmFromEgMonitorPix.restype = None
    break

# <input>: 350
for _lib in _libs.itervalues():
    if not hasattr(_lib, 'EgMonitorPixFromEgWindowPix'):
        continue
    EgMonitorPixFromEgWindowPix = _lib.EgMonitorPixFromEgWindowPix
    EgMonitorPixFromEgWindowPix.argtypes = [POINTER(c_int), POINTER(c_int), c_int, c_int]
    EgMonitorPixFromEgWindowPix.restype = None
    break

# <input>: 355
for _lib in _libs.itervalues():
    if not hasattr(_lib, 'EgWindowPixFromEgMonitorPix'):
        continue
    EgWindowPixFromEgMonitorPix = _lib.EgWindowPixFromEgMonitorPix
    EgWindowPixFromEgMonitorPix.argtypes = [POINTER(c_int), POINTER(c_int), c_int, c_int]
    EgWindowPixFromEgMonitorPix.restype = None
    break

# <input>: 360
for _lib in _libs.itervalues():
    if not hasattr(_lib, 'GdsPixFromMonMm'):
        continue
    GdsPixFromMonMm = _lib.GdsPixFromMonMm
    GdsPixFromMonMm.argtypes = [POINTER(c_int), POINTER(c_int), c_float, c_float]
    GdsPixFromMonMm.restype = None
    break

# <input>: 365
for _lib in _libs.itervalues():
    if not hasattr(_lib, 'MonMmFromGdsPix'):
        continue
    MonMmFromGdsPix = _lib.MonMmFromGdsPix
    MonMmFromGdsPix.argtypes = [POINTER(c_float), POINTER(c_float), POINTER(c_float), c_int, c_int]
    MonMmFromGdsPix.restype = None
    break

# <input>: 371
for _lib in _libs.itervalues():
    if not hasattr(_lib, 'ScaleEgMonPixFromMm'):
        continue
    ScaleEgMonPixFromMm = _lib.ScaleEgMonPixFromMm
    ScaleEgMonPixFromMm.argtypes = [POINTER(c_int), POINTER(c_int), c_float, c_float]
    ScaleEgMonPixFromMm.restype = None
    break

# <input>: 376
for _lib in _libs.itervalues():
    if not hasattr(_lib, 'ScaleEgMonMmFromPix'):
        continue
    ScaleEgMonMmFromPix = _lib.ScaleEgMonMmFromPix
    ScaleEgMonMmFromPix.argtypes = [POINTER(c_float), POINTER(c_float), c_int, c_int]
    ScaleEgMonMmFromPix.restype = None
    break

# <input>: 383
if hasattr(_libs['lctigaze'], 'EgEyeImageInit'):
    EgEyeImageInit = _libs['lctigaze'].EgEyeImageInit
    EgEyeImageInit.argtypes = [POINTER(struct__stEyeImageInfo), c_int]
    EgEyeImageInit.restype = POINTER(struct__stEyeImageInfo)

# <input>: 387
if hasattr(_libs['lctigaze'], 'EgEyeImageDisplay'):
    EgEyeImageDisplay = _libs['lctigaze'].EgEyeImageDisplay
    EgEyeImageDisplay.argtypes = [c_int, c_int, c_int, c_int, c_int, PVOID]
    EgEyeImageDisplay.restype = None

enum_anon_1 = c_int # <input>: 450

EG_CALIBRATE_DISABILITY_APP = 0 # <input>: 450

EG_CALIBRATE_NONDISABILITY_APP = (EG_CALIBRATE_DISABILITY_APP + 1) # <input>: 450

enum_anon_2 = c_int # <input>: 453

CAL_KEY_COMMAND_ESCAPE = 0 # <input>: 453

CAL_KEY_COMMAND_RESTART = (CAL_KEY_COMMAND_ESCAPE + 1) # <input>: 453

CAL_KEY_COMMAND_SKIP = (CAL_KEY_COMMAND_RESTART + 1) # <input>: 453

CAL_KEY_COMMAND_ACCEPT = (CAL_KEY_COMMAND_SKIP + 1) # <input>: 453

CAL_KEY_COMMAND_RETRIEVE = (CAL_KEY_COMMAND_ACCEPT + 1) # <input>: 453

CAL_KEY_COMMAND_SPACE = (CAL_KEY_COMMAND_RETRIEVE + 1) # <input>: 453

_BITMAPINFOHEADER = struct__BITMAPINFOHEADER # <input>: 72

_RGBQUAD = struct__RGBQUAD # <input>: 79

_BITMAPINFO = struct__BITMAPINFO # <input>: 84

_stEgData = struct__stEgData # <input>: 176

_stEgControl = struct__stEgControl # <input>: 91

_stEyeImageInfo = struct__stEyeImageInfo # <input>: 231

# No inserted files

######## From EgConfig.h >>>>>>>
#
## <input>: 14
class struct__stEgConfig(Structure):
    pass

struct__stEgConfig.__slots__ = [
    'iNVis',
    'bEyefollower',
]
struct__stEgConfig._fields_ = [
    ('iNVis', c_int),
    ('bEyefollower', c_int),
]
#
## <input>: 24
if hasattr(_libs['lctigaze'], 'EgGetConfig'):
    EgGetConfig = _libs['lctigaze'].EgGetConfig
    EgGetConfig.argtypes = [POINTER(struct__stEgControl), POINTER(struct__stEgConfig), c_int]
    EgGetConfig.restype = c_int

_stEgConfig = struct__stEgConfig # <input>: 14

######## From EgConfig.h <<<<<<<<<

######## From lcttimer.h >>>>>>>

# double lct_TimerRead(unsigned int *puiProcessorSpeedMHz);

if hasattr(_libs['lctigaze'], 'lct_TimerRead'):
    lct_TimerRead = _libs['lctigaze'].lct_TimerRead
    lct_TimerRead.argtypes = [POINTER(c_int)]
    lct_TimerRead.restype = c_double

# int ReadProcSpeed(void);
if hasattr(_libs['lctigaze'], 'ReadProcSpeed'):
    ReadProcSpeed = _libs['lctigaze'].ReadProcSpeed
    ReadProcSpeed.argtypes = []
    ReadProcSpeed.restype = c_double

######## From lcttimer.h <<<<<<<<<
#
## defines
#
EG_COMM_TYPE_LOCAL  =0    # Single computer configuration. 
EG_COMM_TYPE_SOCKET =1    # 2 computers, comm over TCP/IP. 
EG_COMM_TYPE_SERIAL =2    # 2 computers, comm over TCP/IP. 

EG_MESSAGE_TYPE_GAZEINFO      = 0
EG_MESSAGE_TYPE_MOUSEPOSITION = 1
EG_MESSAGE_TYPE_MOUSEBUTTON   = 2
EG_MESSAGE_TYPE_KEYBD_COMMAND = 3
EG_MESSAGE_TYPE_MOUSERELATIVE = 4
EG_MESSAGE_TYPE_VERGENCE      = 5
EG_MESSAGE_TYPE_IMAGEDATA     = 81

EG_MESSAGE_TYPE_CALIBRATE            =  10
EG_MESSAGE_TYPE_WORKSTATION_QUERY    =  11
EG_MESSAGE_TYPE_WORKSTATION_RESPONSE =  12
EG_MESSAGE_TYPE_CLEAR_SCREEN         =  13
EG_MESSAGE_TYPE_SET_COLOR            =  14
EG_MESSAGE_TYPE_SET_DIAMETER        =   15
EG_MESSAGE_TYPE_DRAW_CIRCLE         =   16
EG_MESSAGE_TYPE_DRAW_CROSS          =   17
EG_MESSAGE_TYPE_DISPLAYTEXT          = 18
EG_MESSAGE_TYPE_CALIBRATION_COMPLETE =  19
EG_MESSAGE_TYPE_CALIBRATION_ABORTED  =  20
EG_MESSAGE_TYPE_TRACKING_ACTIVE      =  22
EG_MESSAGE_TYPE_TRACKING_INACTIVE =     23
EG_MESSAGE_TYPE_VOICE_ACTIVE    =       24
EG_MESSAGE_TYPE_VOICE_INACTIVE =        25

EG_MESSAGE_TYPE_BEGIN_SENDING_DATA  =   30
EG_MESSAGE_TYPE_STOP_SENDING_DATA   =   31
EG_MESSAGE_TYPE_CLOSE_AND_RECYCLE =     32
EG_MESSAGE_TYPE_FILE_OPEN        =      33
EG_MESSAGE_TYPE_FILE_WRITE_HEADER  =    34
EG_MESSAGE_TYPE_FILE_APPENDTEXT   =    35
EG_MESSAGE_TYPE_FILE_START_RECORDING =  36
EG_MESSAGE_TYPE_FILE_STOP_RECORDING  =  37
EG_MESSAGE_TYPE_FILE_MARK_EVENT  =      38
EG_MESSAGE_TYPE_FILE_CLOSE   =          39
EG_MESSAGE_TYPE_CALIBRATE_ABORT   =     21
EG_MESSAGE_TYPE_BEGIN_SENDING_VERGENCE =40
EG_MESSAGE_TYPE_STOP_SENDING_VERGENCE = 41

EG_EVENT_NONE     =         0
EG_EVENT_MOUSEPOSITION =    1
EG_EVENT_MOUSERELATIVE =    2
EG_EVENT_MOUSEBUTTON  =     3
EG_EVENT_KEYBOARD_COMMAND = 4
EG_EVENT_UPDATE_EYE_IMAGE=  5
EG_EVENT_TRACKING_ACTIVE =  6
EG_EVENT_TRACKING_INACTIVE =7
EG_EVENT_VOICE_ACTIVE =     8
EG_EVENT_VOICE_INACTIVE =   9

EG_ERROR_EYEGAZE_ALREADY_INITIALIZED =     9101
EG_ERROR_TRACKING_TERMINATED =             9102
EG_ERROR_MEMORY_ALLOC_FAILED  =            9103
EG_ERROR_LCT_COMM_OPEN_FAILED  =           9104
                                              

## User added functionality

from ctypes import create_string_buffer as StringBuffer
from ctypes import create_unicode_buffer  as UnicodeBuffer

_CAMERA_IMAGE_POSITIONS=('NOT_USED','UPPER_RIGHT','UPPER_LEFT')
_COMM_CHANNEL_TYPES=dict(LOCAL=EG_COMM_TYPE_LOCAL,SOCKET=EG_COMM_TYPE_SOCKET,
                         SERIAL=EG_COMM_TYPE_SERIAL)
    
def initializeEyeGazeDevice(iohub_display, iohub_device_config):
    """
    Initiale and connect to the EyeGaze eye tracker.
    """    
    stEgControl= _stEgControl()
                            
    # Tell Eyegaze the length of the Eyegaze
    # data ring buffer
    stEgControl.iNDataSetsInRingBuffer = iohub_device_config.get('event_buffer_length',32)

    # Tell Eyegaze not to begin image
    # processing yet (so no past gazepoint
    # data samples will have accumulated
    # in the ring buffer when the tracking
    # loop begins).
    stEgControl.bTrackingActive = False;

    # Tell the image processing software what
    # the physical screen dimensions are
    # in pixels.
    pixel_width, pixel_height = iohub_display.getPixelResolution()
    stEgControl.iScreenWidthPix = int(pixel_width)
    stEgControl.iScreenHeightPix = int(pixel_height)

    # Tell Eyegaze not to display the full
    # 640x480 camera image in a separate
    # window.
    v= iohub_device_config.get('display_camera_image',False)
    stEgControl.bEgCameraDisplayActive = v
    
    # Tell Eyegaze that the location for the
    # eye image display is the upper right
    # corner
    # 1 -- upper right corner
    # 2 -- upper left corner
    v= iohub_device_config.get('camera_image_screen_position','UPPER_RIGHT')
    try:
        v=_CAMERA_IMAGE_POSITIONS.index(v)
        stEgControl.iEyeImagesScreenPos = v 
    except Exception:
        print2err('EyeGaze ERROR: Camera Image Position value invalid. Given {0}, must be one of {1}'.format(v,_CAMERA_IMAGE_POSITIONS))
        stEgControl.iEyeImagesScreenPos=0
        
    stEgControl.iVisionSelect=0; # Set this reserved variable to 0

    # The communications type may be set to one of three values. Please see
    # the documentation regarding the different values for communication type.
    # stEgControl.iCommType = EG_COMM_TYPE_LOCAL; // Eyegaze Single Computer Configuration
    # stEgControl.iCommType = EG_COMM_TYPE_SERIAL; // Eyegaze Double Computer Configuration
    # If the comm type is socket or serial, set one of the following:
    # stEgControl.pszCommName = "COM1"; // Eyegaze comm port
    # for EG_COMM_TYPE_SERIAL
    # stEgControl.pszCommName = "127.0.0.1"; // Eyegaze server IP address
    # for EG_COMM_TYPE_SOCKET

    host_conn=iohub_device_config.get('host_connection',None)
    if host_conn:    
        conn_type=host_conn.get('type',None)
        conn_param=host_conn.get('parameter',None)
            
    if conn_type not in _COMM_CHANNEL_TYPES:
        print2err("ERROR: EyeGaze connection_settings comm_type (first list element) must be one of {0}. Received: {1}.".format(_COMM_CHANNEL_TYPES,conn_type))
        print2err("..... USING DEFAULT SETTING OF LOCAL")
        conn_type='LOCAL'
        
    stEgControl.iCommType = _COMM_CHANNEL_TYPES[conn_type]; 
    
    if conn_type not in ['SOCKET','SERIAL']:
        if conn_param is None or len(conn_param)==0:
            stEgControl.pszCommName=None 
        else:
            stEgControl.pszCommName=UnicodeBuffer(conn_param)
            
    # Create the Eyegaze image processing thread
    result=EgInit(byref(stEgControl))
    return stEgControl
