"""
Python bindings for GLFW.
"""

from __future__ import print_function
from __future__ import division
from __future__ import unicode_literals

__author__ = 'Florian Rhiem (florian.rhiem@gmail.com)'
__copyright__ = 'Copyright (c) 2013-2016 Florian Rhiem'
__license__ = 'MIT'
__version__ = '1.5.1'

# By default (ERROR_REPORTING = True), GLFW errors will be reported as Python
# exceptions. Set ERROR_REPORTING to False or set a curstom error callback to
# disable this behavior.
ERROR_REPORTING = True

import ctypes
import os
import functools
import glob
import sys
import subprocess
import textwrap

# Python 3 compatibility:
try:
    _getcwd = os.getcwdu
except AttributeError:
    _getcwd = os.getcwd
if sys.version_info.major > 2:
    _to_char_p = lambda s: s.encode('utf-8')
    def _reraise(exception, traceback):
        raise exception.with_traceback(traceback)
else:
    _to_char_p = lambda s: s
    def _reraise(exception, traceback):
        raise (exception, None, traceback)


class GLFWError(Exception):
    """
    Exception class used for reporting GLFW errors.
    """
    def __init__(self, message):
        super(GLFWError, self).__init__(message)


def _find_library_candidates(library_names,
                             library_file_extensions,
                             library_search_paths):
    """
    Finds and returns filenames which might be the library you are looking for.
    """
    candidates = set()
    for library_name in library_names:
        for search_path in library_search_paths:
            glob_query = os.path.join(search_path, '*'+library_name+'*')
            for filename in glob.iglob(glob_query):
                filename = os.path.realpath(filename)
                if filename in candidates:
                    continue
                basename = os.path.basename(filename)
                if basename.startswith('lib'+library_name):
                    basename_end = basename[len('lib'+library_name):]
                elif basename.startswith(library_name):
                    basename_end = basename[len(library_name):]
                else:
                    continue
                for file_extension in library_file_extensions:
                    if basename_end.startswith(file_extension):
                        if basename_end[len(file_extension):][:1] in ('', '.'):
                            candidates.add(filename)
                    if basename_end.endswith(file_extension):
                        basename_middle = basename_end[:-len(file_extension)]
                        if all(c in '0123456789.' for c in basename_middle):
                            candidates.add(filename)
    return candidates


def _load_library(library_names, library_file_extensions,
                  library_search_paths, version_check_callback):
    """
    Finds, loads and returns the most recent version of the library.
    """
    candidates = _find_library_candidates(library_names,
                                          library_file_extensions,
                                          library_search_paths)
    library_versions = []
    for filename in candidates:
        version = version_check_callback(filename)
        if version is not None and version >= (3, 0, 0):
            library_versions.append((version, filename))

    if not library_versions:
        return None
    library_versions.sort()
    return ctypes.CDLL(library_versions[-1][1])


def _glfw_get_version(filename):
    """
    Queries and returns the library version tuple or None by using a
    subprocess.
    """
    version_checker_source = '''
        import sys
        import ctypes

        def get_version(library_handle):
            """
            Queries and returns the library version tuple or None.
            """
            major_value = ctypes.c_int(0)
            major = ctypes.pointer(major_value)
            minor_value = ctypes.c_int(0)
            minor = ctypes.pointer(minor_value)
            rev_value = ctypes.c_int(0)
            rev = ctypes.pointer(rev_value)
            if hasattr(library_handle, 'glfwGetVersion'):
                library_handle.glfwGetVersion(major, minor, rev)
                version = (major_value.value,
                           minor_value.value,
                           rev_value.value)
                return version
            else:
                return None

        try:
            input_func = raw_input
        except NameError:
            input_func = input
        filename = input_func().strip()

        try:
            library_handle = ctypes.CDLL(filename)
        except OSError:
            pass
        else:
            version = get_version(library_handle)
            print(version)
    '''

    args = [sys.executable, '-c', textwrap.dedent(version_checker_source)]
    process = subprocess.Popen(args, universal_newlines=True,
                               stdin=subprocess.PIPE, stdout=subprocess.PIPE)
    out = process.communicate(filename)[0]
    out = out.strip()
    if out:
        return eval(out)
    else:
        return None


def _get_library_search_paths():
    """
    Returns a list of library search paths, considering of the current working
    directory, default paths and paths from environment variables.
    """
    search_paths = [
        '',
        '/usr/lib64',
        '/usr/local/lib64',
        '/usr/lib', '/usr/local/lib',
        '/run/current-system/sw/lib',
        '/usr/lib/x86_64-linux-gnu/',
        os.path.abspath(os.path.dirname(__file__))
    ]

    if sys.platform == 'darwin':
        path_environment_variable = 'DYLD_LIBRARY_PATH'
    else:
        path_environment_variable = 'LD_LIBRARY_PATH'
    if path_environment_variable in os.environ:
        search_paths.extend(os.environ[path_environment_variable].split(':'))
    return search_paths


if os.environ.get('PYGLFW_LIBRARY', ''):
    try:
        _glfw = ctypes.CDLL(os.environ['PYGLFW_LIBRARY'])
    except OSError:
        _glfw = None
elif sys.platform == 'win32':
    # try glfw3.dll using windows search paths
    try:
        _glfw = ctypes.CDLL('glfw3.dll')
    except OSError:
        # try glfw3.dll in package directory
        try:
            _glfw = ctypes.CDLL(os.path.join(os.path.abspath(os.path.dirname(__file__)), 'glfw3.dll'))
        except OSError:
            _glfw = None
else:
    _glfw = _load_library(['glfw', 'glfw3'], ['.so', '.dylib'],
                          _get_library_search_paths(), _glfw_get_version)

if _glfw is None:
    raise ImportError("Failed to load GLFW3 shared library.")

_callback_repositories = []


class _GLFWwindow(ctypes.Structure):
    """
    Wrapper for:
        typedef struct GLFWwindow GLFWwindow;
    """
    _fields_ = [("dummy", ctypes.c_int)]


class _GLFWmonitor(ctypes.Structure):
    """
    Wrapper for:
        typedef struct GLFWmonitor GLFWmonitor;
    """
    _fields_ = [("dummy", ctypes.c_int)]


class _GLFWvidmode(ctypes.Structure):
    """
    Wrapper for:
        typedef struct GLFWvidmode GLFWvidmode;
    """
    _fields_ = [("width", ctypes.c_int),
                ("height", ctypes.c_int),
                ("red_bits", ctypes.c_int),
                ("green_bits", ctypes.c_int),
                ("blue_bits", ctypes.c_int),
                ("refresh_rate", ctypes.c_uint)]

    def __init__(self):
        ctypes.Structure.__init__(self)
        self.width = 0
        self.height = 0
        self.red_bits = 0
        self.green_bits = 0
        self.blue_bits = 0
        self.refresh_rate = 0

    def wrap(self, video_mode):
        """
        Wraps a nested python sequence.
        """
        size, bits, self.refresh_rate = video_mode
        self.width, self.height = size
        self.red_bits, self.green_bits, self.blue_bits = bits

    def unwrap(self):
        """
        Returns a nested python sequence.
        """
        size = self.width, self.height
        bits = self.red_bits, self.green_bits, self.blue_bits
        return size, bits, self.refresh_rate


class _GLFWgammaramp(ctypes.Structure):
    """
    Wrapper for:
        typedef struct GLFWgammaramp GLFWgammaramp;
    """
    _fields_ = [("red", ctypes.POINTER(ctypes.c_ushort)),
                ("green", ctypes.POINTER(ctypes.c_ushort)),
                ("blue", ctypes.POINTER(ctypes.c_ushort)),
                ("size", ctypes.c_uint)]

    def __init__(self):
        ctypes.Structure.__init__(self)
        self.red = None
        self.red_array = None
        self.green = None
        self.green_array = None
        self.blue = None
        self.blue_array = None
        self.size = 0

    def wrap(self, gammaramp):
        """
        Wraps a nested python sequence.
        """
        red, green, blue = gammaramp
        size = min(len(red), len(green), len(blue))
        array_type = ctypes.c_ushort*size
        self.size = ctypes.c_uint(size)
        self.red_array = array_type()
        self.green_array = array_type()
        self.blue_array = array_type()
        for i in range(self.size):
            self.red_array[i] = int(red[i]*65535)
            self.green_array[i] = int(green[i]*65535)
            self.blue_array[i] = int(blue[i]*65535)
        pointer_type = ctypes.POINTER(ctypes.c_ushort)
        self.red = ctypes.cast(self.red_array, pointer_type)
        self.green = ctypes.cast(self.green_array, pointer_type)
        self.blue = ctypes.cast(self.blue_array, pointer_type)

    def unwrap(self):
        """
        Returns a nested python sequence.
        """
        red = [self.red[i]/65535.0 for i in range(self.size)]
        green = [self.green[i]/65535.0 for i in range(self.size)]
        blue = [self.blue[i]/65535.0 for i in range(self.size)]
        return red, green, blue


class _GLFWcursor(ctypes.Structure):
    """
    Wrapper for:
        typedef struct GLFWcursor GLFWcursor;
    """
    _fields_ = [("dummy", ctypes.c_int)]


class _GLFWimage(ctypes.Structure):
    """
    Wrapper for:
        typedef struct GLFWimage GLFWimage;
    """
    _fields_ = [("width", ctypes.c_int),
                ("height", ctypes.c_int),
                ("pixels", ctypes.POINTER(ctypes.c_ubyte))]

    def __init__(self):
        ctypes.Structure.__init__(self)
        self.width = 0
        self.height = 0
        self.pixels = None
        self.pixels_array = None

    def wrap(self, image):
        """
        Wraps a nested python sequence or PIL/pillow Image.
        """
        if hasattr(image, 'size') and hasattr(image, 'convert'):
            # Treat image as PIL/pillow Image object
            self.width, self.height = image.size
            array_type = ctypes.c_ubyte * 4 * (self.width * self.height)
            self.pixels_array = array_type()
            pixels = image.convert('RGBA').getdata()
            for i, pixel in enumerate(pixels):
                self.pixels_array[i] = pixel
        else:
            self.width, self.height, pixels = image
            array_type = ctypes.c_ubyte * 4 * self.width * self.height
            self.pixels_array = array_type()
            for i in range(self.height):
                for j in range(self.width):
                    for k in range(4):
                        self.pixels_array[i][j][k] = pixels[i][j][k]
        pointer_type = ctypes.POINTER(ctypes.c_ubyte)
        self.pixels = ctypes.cast(self.pixels_array, pointer_type)

    def unwrap(self):
        """
        Returns a nested python sequence.
        """
        pixels = [[[int(c) for c in p] for p in l] for l in self.pixels_array]
        return self.width, self.height, pixels


VERSION_MAJOR = 3
VERSION_MINOR = 2
VERSION_REVISION = 1
RELEASE = 0
PRESS = 1
REPEAT = 2
KEY_UNKNOWN = -1
KEY_SPACE = 32
KEY_APOSTROPHE = 39
KEY_COMMA = 44
KEY_MINUS = 45
KEY_PERIOD = 46
KEY_SLASH = 47
KEY_0 = 48
KEY_1 = 49
KEY_2 = 50
KEY_3 = 51
KEY_4 = 52
KEY_5 = 53
KEY_6 = 54
KEY_7 = 55
KEY_8 = 56
KEY_9 = 57
KEY_SEMICOLON = 59
KEY_EQUAL = 61
KEY_A = 65
KEY_B = 66
KEY_C = 67
KEY_D = 68
KEY_E = 69
KEY_F = 70
KEY_G = 71
KEY_H = 72
KEY_I = 73
KEY_J = 74
KEY_K = 75
KEY_L = 76
KEY_M = 77
KEY_N = 78
KEY_O = 79
KEY_P = 80
KEY_Q = 81
KEY_R = 82
KEY_S = 83
KEY_T = 84
KEY_U = 85
KEY_V = 86
KEY_W = 87
KEY_X = 88
KEY_Y = 89
KEY_Z = 90
KEY_LEFT_BRACKET = 91
KEY_BACKSLASH = 92
KEY_RIGHT_BRACKET = 93
KEY_GRAVE_ACCENT = 96
KEY_WORLD_1 = 161
KEY_WORLD_2 = 162
KEY_ESCAPE = 256
KEY_ENTER = 257
KEY_TAB = 258
KEY_BACKSPACE = 259
KEY_INSERT = 260
KEY_DELETE = 261
KEY_RIGHT = 262
KEY_LEFT = 263
KEY_DOWN = 264
KEY_UP = 265
KEY_PAGE_UP = 266
KEY_PAGE_DOWN = 267
KEY_HOME = 268
KEY_END = 269
KEY_CAPS_LOCK = 280
KEY_SCROLL_LOCK = 281
KEY_NUM_LOCK = 282
KEY_PRINT_SCREEN = 283
KEY_PAUSE = 284
KEY_F1 = 290
KEY_F2 = 291
KEY_F3 = 292
KEY_F4 = 293
KEY_F5 = 294
KEY_F6 = 295
KEY_F7 = 296
KEY_F8 = 297
KEY_F9 = 298
KEY_F10 = 299
KEY_F11 = 300
KEY_F12 = 301
KEY_F13 = 302
KEY_F14 = 303
KEY_F15 = 304
KEY_F16 = 305
KEY_F17 = 306
KEY_F18 = 307
KEY_F19 = 308
KEY_F20 = 309
KEY_F21 = 310
KEY_F22 = 311
KEY_F23 = 312
KEY_F24 = 313
KEY_F25 = 314
KEY_KP_0 = 320
KEY_KP_1 = 321
KEY_KP_2 = 322
KEY_KP_3 = 323
KEY_KP_4 = 324
KEY_KP_5 = 325
KEY_KP_6 = 326
KEY_KP_7 = 327
KEY_KP_8 = 328
KEY_KP_9 = 329
KEY_KP_DECIMAL = 330
KEY_KP_DIVIDE = 331
KEY_KP_MULTIPLY = 332
KEY_KP_SUBTRACT = 333
KEY_KP_ADD = 334
KEY_KP_ENTER = 335
KEY_KP_EQUAL = 336
KEY_LEFT_SHIFT = 340
KEY_LEFT_CONTROL = 341
KEY_LEFT_ALT = 342
KEY_LEFT_SUPER = 343
KEY_RIGHT_SHIFT = 344
KEY_RIGHT_CONTROL = 345
KEY_RIGHT_ALT = 346
KEY_RIGHT_SUPER = 347
KEY_MENU = 348
KEY_LAST = KEY_MENU
MOD_SHIFT = 0x0001
MOD_CONTROL = 0x0002
MOD_ALT = 0x0004
MOD_SUPER = 0x0008
MOUSE_BUTTON_1 = 0
MOUSE_BUTTON_2 = 1
MOUSE_BUTTON_3 = 2
MOUSE_BUTTON_4 = 3
MOUSE_BUTTON_5 = 4
MOUSE_BUTTON_6 = 5
MOUSE_BUTTON_7 = 6
MOUSE_BUTTON_8 = 7
MOUSE_BUTTON_LAST = MOUSE_BUTTON_8
MOUSE_BUTTON_LEFT = MOUSE_BUTTON_1
MOUSE_BUTTON_RIGHT = MOUSE_BUTTON_2
MOUSE_BUTTON_MIDDLE = MOUSE_BUTTON_3
JOYSTICK_1 = 0
JOYSTICK_2 = 1
JOYSTICK_3 = 2
JOYSTICK_4 = 3
JOYSTICK_5 = 4
JOYSTICK_6 = 5
JOYSTICK_7 = 6
JOYSTICK_8 = 7
JOYSTICK_9 = 8
JOYSTICK_10 = 9
JOYSTICK_11 = 10
JOYSTICK_12 = 11
JOYSTICK_13 = 12
JOYSTICK_14 = 13
JOYSTICK_15 = 14
JOYSTICK_16 = 15
JOYSTICK_LAST = JOYSTICK_16
NOT_INITIALIZED = 0x00010001
NO_CURRENT_CONTEXT = 0x00010002
INVALID_ENUM = 0x00010003
INVALID_VALUE = 0x00010004
OUT_OF_MEMORY = 0x00010005
API_UNAVAILABLE = 0x00010006
VERSION_UNAVAILABLE = 0x00010007
PLATFORM_ERROR = 0x00010008
FORMAT_UNAVAILABLE = 0x00010009
NO_WINDOW_CONTEXT = 0x0001000A
FOCUSED = 0x00020001
ICONIFIED = 0x00020002
RESIZABLE = 0x00020003
VISIBLE = 0x00020004
DECORATED = 0x00020005
AUTO_ICONIFY = 0x00020006
FLOATING = 0x00020007
MAXIMIZED = 0x00020008
RED_BITS = 0x00021001
GREEN_BITS = 0x00021002
BLUE_BITS = 0x00021003
ALPHA_BITS = 0x00021004
DEPTH_BITS = 0x00021005
STENCIL_BITS = 0x00021006
ACCUM_RED_BITS = 0x00021007
ACCUM_GREEN_BITS = 0x00021008
ACCUM_BLUE_BITS = 0x00021009
ACCUM_ALPHA_BITS = 0x0002100A
AUX_BUFFERS = 0x0002100B
STEREO = 0x0002100C
SAMPLES = 0x0002100D
SRGB_CAPABLE = 0x0002100E
REFRESH_RATE = 0x0002100F
DOUBLEBUFFER = 0x00021010
CLIENT_API = 0x00022001
CONTEXT_VERSION_MAJOR = 0x00022002
CONTEXT_VERSION_MINOR = 0x00022003
CONTEXT_REVISION = 0x00022004
CONTEXT_ROBUSTNESS = 0x00022005
OPENGL_FORWARD_COMPAT = 0x00022006
OPENGL_DEBUG_CONTEXT = 0x00022007
OPENGL_PROFILE = 0x00022008
CONTEXT_RELEASE_BEHAVIOR = 0x00022009
CONTEXT_NO_ERROR = 0x0002200A
CONTEXT_CREATION_API = 0x0002200B
NO_API = 0
OPENGL_API = 0x00030001
OPENGL_ES_API = 0x00030002
NO_ROBUSTNESS = 0
NO_RESET_NOTIFICATION = 0x00031001
LOSE_CONTEXT_ON_RESET = 0x00031002
OPENGL_ANY_PROFILE = 0
OPENGL_CORE_PROFILE = 0x00032001
OPENGL_COMPAT_PROFILE = 0x00032002
CURSOR = 0x00033001
STICKY_KEYS = 0x00033002
STICKY_MOUSE_BUTTONS = 0x00033003
CURSOR_NORMAL = 0x00034001
CURSOR_HIDDEN = 0x00034002
CURSOR_DISABLED = 0x00034003
ANY_RELEASE_BEHAVIOR = 0
RELEASE_BEHAVIOR_FLUSH = 0x00035001
RELEASE_BEHAVIOR_NONE = 0x00035002
NATIVE_CONTEXT_API = 0x00036001
EGL_CONTEXT_API = 0x00036002
ARROW_CURSOR = 0x00036001
IBEAM_CURSOR = 0x00036002
CROSSHAIR_CURSOR = 0x00036003
HAND_CURSOR = 0x00036004
HRESIZE_CURSOR = 0x00036005
VRESIZE_CURSOR = 0x00036006
CONNECTED = 0x00040001
DISCONNECTED = 0x00040002
DONT_CARE = -1

_exc_info_from_callback = None
def _callback_exception_decorator(func):
    @functools.wraps(func)
    def callback_wrapper(*args, **kwargs):
        global _exc_info_from_callback
        if _exc_info_from_callback is not None:
            # We are on the way back to Python after an exception was raised.
            # Do not call further callbacks and wait for the errcheck function
            # to handle the exception first.
            return
        try:
            return func(*args, **kwargs)
        except (KeyboardInterrupt, SystemExit):
            raise
        except:
            _exc_info_from_callback = sys.exc_info()
    return callback_wrapper


def _prepare_errcheck():
    """
    This function sets the errcheck attribute of all ctypes wrapped functions
    to evaluate the _exc_info_from_callback global variable and re-raise any
    exceptions that might have been raised in callbacks.
    It also modifies all callback types to automatically wrap the function
    using the _callback_exception_decorator.
    """
    def errcheck(result, *args):
        global _exc_info_from_callback
        if _exc_info_from_callback is not None:
            exc = _exc_info_from_callback
            _exc_info_from_callback = None
            _reraise(exc[1], exc[2])
        return result

    for symbol in dir(_glfw):
        if symbol.startswith('glfw'):
            getattr(_glfw, symbol).errcheck = errcheck

    _globals = globals()
    for symbol in _globals:
        if symbol.startswith('_GLFW') and symbol.endswith('fun'):
            def wrapper_cfunctype(func, cfunctype=_globals[symbol]):
                return cfunctype(_callback_exception_decorator(func))
            _globals[symbol] = wrapper_cfunctype


_GLFWerrorfun = ctypes.CFUNCTYPE(None,
                                 ctypes.c_int,
                                 ctypes.c_char_p)
_GLFWwindowposfun = ctypes.CFUNCTYPE(None,
                                     ctypes.POINTER(_GLFWwindow),
                                     ctypes.c_int,
                                     ctypes.c_int)
_GLFWwindowsizefun = ctypes.CFUNCTYPE(None,
                                      ctypes.POINTER(_GLFWwindow),
                                      ctypes.c_int,
                                      ctypes.c_int)
_GLFWwindowclosefun = ctypes.CFUNCTYPE(None,
                                       ctypes.POINTER(_GLFWwindow))
_GLFWwindowrefreshfun = ctypes.CFUNCTYPE(None,
                                         ctypes.POINTER(_GLFWwindow))
_GLFWwindowfocusfun = ctypes.CFUNCTYPE(None,
                                       ctypes.POINTER(_GLFWwindow),
                                       ctypes.c_int)
_GLFWwindowiconifyfun = ctypes.CFUNCTYPE(None,
                                         ctypes.POINTER(_GLFWwindow),
                                         ctypes.c_int)
_GLFWframebuffersizefun = ctypes.CFUNCTYPE(None,
                                           ctypes.POINTER(_GLFWwindow),
                                           ctypes.c_int,
                                           ctypes.c_int)
_GLFWmousebuttonfun = ctypes.CFUNCTYPE(None,
                                       ctypes.POINTER(_GLFWwindow),
                                       ctypes.c_int,
                                       ctypes.c_int,
                                       ctypes.c_int)
_GLFWcursorposfun = ctypes.CFUNCTYPE(None,
                                     ctypes.POINTER(_GLFWwindow),
                                     ctypes.c_double,
                                     ctypes.c_double)
_GLFWcursorenterfun = ctypes.CFUNCTYPE(None,
                                       ctypes.POINTER(_GLFWwindow),
                                       ctypes.c_int)
_GLFWscrollfun = ctypes.CFUNCTYPE(None,
                                  ctypes.POINTER(_GLFWwindow),
                                  ctypes.c_double,
                                  ctypes.c_double)
_GLFWkeyfun = ctypes.CFUNCTYPE(None,
                               ctypes.POINTER(_GLFWwindow),
                               ctypes.c_int,
                               ctypes.c_int,
                               ctypes.c_int,
                               ctypes.c_int)
_GLFWcharfun = ctypes.CFUNCTYPE(None,
                                ctypes.POINTER(_GLFWwindow),
                                ctypes.c_int)
_GLFWmonitorfun = ctypes.CFUNCTYPE(None,
                                   ctypes.POINTER(_GLFWmonitor),
                                   ctypes.c_int)
_GLFWdropfun = ctypes.CFUNCTYPE(None,
                                ctypes.POINTER(_GLFWwindow),
                                ctypes.c_int,
                                ctypes.POINTER(ctypes.c_char_p))
_GLFWcharmodsfun = ctypes.CFUNCTYPE(None,
                                    ctypes.POINTER(_GLFWwindow),
                                    ctypes.c_uint,
                                    ctypes.c_int)
_GLFWjoystickfun = ctypes.CFUNCTYPE(None,
                                    ctypes.c_int,
                                    ctypes.c_int)


_glfw.glfwInit.restype = ctypes.c_int
_glfw.glfwInit.argtypes = []
def init():
    """
    Initializes the GLFW library.

    Wrapper for:
        int glfwInit(void);
    """
    cwd = _getcwd()
    res = _glfw.glfwInit()
    os.chdir(cwd)
    return res

_glfw.glfwTerminate.restype = None
_glfw.glfwTerminate.argtypes = []
def terminate():
    """
    Terminates the GLFW library.

    Wrapper for:
        void glfwTerminate(void);
    """

    for callback_repository in _callback_repositories:
        for window_addr in list(callback_repository.keys()):
            del callback_repository[window_addr]
    for window_addr in list(_window_user_data_repository.keys()):
        del _window_user_data_repository[window_addr]
    _glfw.glfwTerminate()

_glfw.glfwGetVersion.restype = None
_glfw.glfwGetVersion.argtypes = [ctypes.POINTER(ctypes.c_int),
                                 ctypes.POINTER(ctypes.c_int),
                                 ctypes.POINTER(ctypes.c_int)]
def get_version():
    """
    Retrieves the version of the GLFW library.

    Wrapper for:
        void glfwGetVersion(int* major, int* minor, int* rev);
    """
    major_value = ctypes.c_int(0)
    major = ctypes.pointer(major_value)
    minor_value = ctypes.c_int(0)
    minor = ctypes.pointer(minor_value)
    rev_value = ctypes.c_int(0)
    rev = ctypes.pointer(rev_value)
    _glfw.glfwGetVersion(major, minor, rev)
    return major_value.value, minor_value.value, rev_value.value

_glfw.glfwGetVersionString.restype = ctypes.c_char_p
_glfw.glfwGetVersionString.argtypes = []
def get_version_string():
    """
    Returns a string describing the compile-time configuration.

    Wrapper for:
        const char* glfwGetVersionString(void);
    """
    return _glfw.glfwGetVersionString()

@_callback_exception_decorator
def _raise_glfw_errors_as_exceptions(error_code, description):
    """
    Default error callback that raises GLFWError exceptions for glfw errors.
    Set an alternative error callback or set glfw.ERROR_REPORTING to False to
    disable this behavior.
    """
    global ERROR_REPORTING
    if ERROR_REPORTING:
        message = "(%d) %s" % (error_code, description)
        raise GLFWError(message)

_default_error_callback = _GLFWerrorfun(_raise_glfw_errors_as_exceptions)
_error_callback = (_raise_glfw_errors_as_exceptions, _default_error_callback)
_glfw.glfwSetErrorCallback.restype = _GLFWerrorfun
_glfw.glfwSetErrorCallback.argtypes = [_GLFWerrorfun]
_glfw.glfwSetErrorCallback(_default_error_callback)
def set_error_callback(cbfun):
    """
    Sets the error callback.

    Wrapper for:
        GLFWerrorfun glfwSetErrorCallback(GLFWerrorfun cbfun);
    """
    global _error_callback
    previous_callback = _error_callback
    if cbfun is None:
        cbfun = _raise_glfw_errors_as_exceptions
        c_cbfun = _default_error_callback
    else:
        c_cbfun = _GLFWerrorfun(cbfun)
    _error_callback = (cbfun, c_cbfun)
    cbfun = c_cbfun
    _glfw.glfwSetErrorCallback(cbfun)
    if previous_callback is not None and previous_callback[0] != _raise_glfw_errors_as_exceptions:
        return previous_callback[0]

_glfw.glfwGetMonitors.restype = ctypes.POINTER(ctypes.POINTER(_GLFWmonitor))
_glfw.glfwGetMonitors.argtypes = [ctypes.POINTER(ctypes.c_int)]
def get_monitors():
    """
    Returns the currently connected monitors.

    Wrapper for:
        GLFWmonitor** glfwGetMonitors(int* count);
    """
    count_value = ctypes.c_int(0)
    count = ctypes.pointer(count_value)
    result = _glfw.glfwGetMonitors(count)
    monitors = [result[i] for i in range(count_value.value)]
    return monitors

_glfw.glfwGetPrimaryMonitor.restype = ctypes.POINTER(_GLFWmonitor)
_glfw.glfwGetPrimaryMonitor.argtypes = []
def get_primary_monitor():
    """
    Returns the primary monitor.

    Wrapper for:
        GLFWmonitor* glfwGetPrimaryMonitor(void);
    """
    return _glfw.glfwGetPrimaryMonitor()

_glfw.glfwGetMonitorPos.restype = None
_glfw.glfwGetMonitorPos.argtypes = [ctypes.POINTER(_GLFWmonitor),
                                    ctypes.POINTER(ctypes.c_int),
                                    ctypes.POINTER(ctypes.c_int)]
def get_monitor_pos(monitor):
    """
    Returns the position of the monitor's viewport on the virtual screen.

    Wrapper for:
        void glfwGetMonitorPos(GLFWmonitor* monitor, int* xpos, int* ypos);
    """
    xpos_value = ctypes.c_int(0)
    xpos = ctypes.pointer(xpos_value)
    ypos_value = ctypes.c_int(0)
    ypos = ctypes.pointer(ypos_value)
    _glfw.glfwGetMonitorPos(monitor, xpos, ypos)
    return xpos_value.value, ypos_value.value

_glfw.glfwGetMonitorPhysicalSize.restype = None
_glfw.glfwGetMonitorPhysicalSize.argtypes = [ctypes.POINTER(_GLFWmonitor),
                                             ctypes.POINTER(ctypes.c_int),
                                             ctypes.POINTER(ctypes.c_int)]
def get_monitor_physical_size(monitor):
    """
    Returns the physical size of the monitor.

    Wrapper for:
        void glfwGetMonitorPhysicalSize(GLFWmonitor* monitor, int* width, int* height);
    """
    width_value = ctypes.c_int(0)
    width = ctypes.pointer(width_value)
    height_value = ctypes.c_int(0)
    height = ctypes.pointer(height_value)
    _glfw.glfwGetMonitorPhysicalSize(monitor, width, height)
    return width_value.value, height_value.value

_glfw.glfwGetMonitorName.restype = ctypes.c_char_p
_glfw.glfwGetMonitorName.argtypes = [ctypes.POINTER(_GLFWmonitor)]
def get_monitor_name(monitor):
    """
    Returns the name of the specified monitor.

    Wrapper for:
        const char* glfwGetMonitorName(GLFWmonitor* monitor);
    """
    return _glfw.glfwGetMonitorName(monitor)

_monitor_callback = None
_glfw.glfwSetMonitorCallback.restype = _GLFWmonitorfun
_glfw.glfwSetMonitorCallback.argtypes = [_GLFWmonitorfun]
def set_monitor_callback(cbfun):
    """
    Sets the monitor configuration callback.

    Wrapper for:
        GLFWmonitorfun glfwSetMonitorCallback(GLFWmonitorfun cbfun);
    """
    global _monitor_callback
    previous_callback = _monitor_callback
    if cbfun is None:
        cbfun = 0
    c_cbfun = _GLFWmonitorfun(cbfun)
    _monitor_callback = (cbfun, c_cbfun)
    cbfun = c_cbfun
    _glfw.glfwSetMonitorCallback(cbfun)
    if previous_callback is not None and previous_callback[0] != 0:
        return previous_callback[0]

_glfw.glfwGetVideoModes.restype = ctypes.POINTER(_GLFWvidmode)
_glfw.glfwGetVideoModes.argtypes = [ctypes.POINTER(_GLFWmonitor),
                                    ctypes.POINTER(ctypes.c_int)]
def get_video_modes(monitor):
    """
    Returns the available video modes for the specified monitor.

    Wrapper for:
        const GLFWvidmode* glfwGetVideoModes(GLFWmonitor* monitor, int* count);
    """
    count_value = ctypes.c_int(0)
    count = ctypes.pointer(count_value)
    result = _glfw.glfwGetVideoModes(monitor, count)
    videomodes = [result[i].unwrap() for i in range(count_value.value)]
    return videomodes

_glfw.glfwGetVideoMode.restype = ctypes.POINTER(_GLFWvidmode)
_glfw.glfwGetVideoMode.argtypes = [ctypes.POINTER(_GLFWmonitor)]
def get_video_mode(monitor):
    """
    Returns the current mode of the specified monitor.

    Wrapper for:
        const GLFWvidmode* glfwGetVideoMode(GLFWmonitor* monitor);
    """
    videomode = _glfw.glfwGetVideoMode(monitor).contents
    return videomode.unwrap()

_glfw.glfwSetGamma.restype = None
_glfw.glfwSetGamma.argtypes = [ctypes.POINTER(_GLFWmonitor),
                               ctypes.c_float]
def set_gamma(monitor, gamma):
    """
    Generates a gamma ramp and sets it for the specified monitor.

    Wrapper for:
        void glfwSetGamma(GLFWmonitor* monitor, float gamma);
    """
    _glfw.glfwSetGamma(monitor, gamma)

_glfw.glfwGetGammaRamp.restype = ctypes.POINTER(_GLFWgammaramp)
_glfw.glfwGetGammaRamp.argtypes = [ctypes.POINTER(_GLFWmonitor)]
def get_gamma_ramp(monitor):
    """
    Retrieves the current gamma ramp for the specified monitor.

    Wrapper for:
        const GLFWgammaramp* glfwGetGammaRamp(GLFWmonitor* monitor);
    """
    gammaramp = _glfw.glfwGetGammaRamp(monitor).contents
    return gammaramp.unwrap()

_glfw.glfwSetGammaRamp.restype = None
_glfw.glfwSetGammaRamp.argtypes = [ctypes.POINTER(_GLFWmonitor),
                                   ctypes.POINTER(_GLFWgammaramp)]
def set_gamma_ramp(monitor, ramp):
    """
    Sets the current gamma ramp for the specified monitor.

    Wrapper for:
        void glfwSetGammaRamp(GLFWmonitor* monitor, const GLFWgammaramp* ramp);
    """
    gammaramp = _GLFWgammaramp()
    gammaramp.wrap(ramp)
    _glfw.glfwSetGammaRamp(monitor, ctypes.pointer(gammaramp))

_glfw.glfwDefaultWindowHints.restype = None
_glfw.glfwDefaultWindowHints.argtypes = []
def default_window_hints():
    """
    Resets all window hints to their default values.

    Wrapper for:
        void glfwDefaultWindowHints(void);
    """
    _glfw.glfwDefaultWindowHints()

_glfw.glfwWindowHint.restype = None
_glfw.glfwWindowHint.argtypes = [ctypes.c_int,
                                 ctypes.c_int]
def window_hint(target, hint):
    """
    Sets the specified window hint to the desired value.

    Wrapper for:
        void glfwWindowHint(int target, int hint);
    """
    _glfw.glfwWindowHint(target, hint)

_glfw.glfwCreateWindow.restype = ctypes.POINTER(_GLFWwindow)
_glfw.glfwCreateWindow.argtypes = [ctypes.c_int,
                                   ctypes.c_int,
                                   ctypes.c_char_p,
                                   ctypes.POINTER(_GLFWmonitor),
                                   ctypes.POINTER(_GLFWwindow)]
def create_window(width, height, title, monitor, share):
    """
    Creates a window and its associated context.

    Wrapper for:
        GLFWwindow* glfwCreateWindow(int width, int height, const char* title, GLFWmonitor* monitor, GLFWwindow* share);
    """
    return _glfw.glfwCreateWindow(width, height, _to_char_p(title),
                                  monitor, share)

_glfw.glfwDestroyWindow.restype = None
_glfw.glfwDestroyWindow.argtypes = [ctypes.POINTER(_GLFWwindow)]
def destroy_window(window):
    """
    Destroys the specified window and its context.

    Wrapper for:
        void glfwDestroyWindow(GLFWwindow* window);
    """
    _glfw.glfwDestroyWindow(window)
    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_ulong)).contents.value
    for callback_repository in _callback_repositories:
        if window_addr in callback_repository:
            del callback_repository[window_addr]
    if window_addr in _window_user_data_repository:
        del _window_user_data_repository[window_addr]

_glfw.glfwWindowShouldClose.restype = ctypes.c_int
_glfw.glfwWindowShouldClose.argtypes = [ctypes.POINTER(_GLFWwindow)]
def window_should_close(window):
    """
    Checks the close flag of the specified window.

    Wrapper for:
        int glfwWindowShouldClose(GLFWwindow* window);
    """
    return _glfw.glfwWindowShouldClose(window)

_glfw.glfwSetWindowShouldClose.restype = None
_glfw.glfwSetWindowShouldClose.argtypes = [ctypes.POINTER(_GLFWwindow),
                                           ctypes.c_int]
def set_window_should_close(window, value):
    """
    Sets the close flag of the specified window.

    Wrapper for:
        void glfwSetWindowShouldClose(GLFWwindow* window, int value);
    """
    _glfw.glfwSetWindowShouldClose(window, value)

_glfw.glfwSetWindowTitle.restype = None
_glfw.glfwSetWindowTitle.argtypes = [ctypes.POINTER(_GLFWwindow),
                                     ctypes.c_char_p]
def set_window_title(window, title):
    """
    Sets the title of the specified window.

    Wrapper for:
        void glfwSetWindowTitle(GLFWwindow* window, const char* title);
    """
    _glfw.glfwSetWindowTitle(window, _to_char_p(title))

_glfw.glfwGetWindowPos.restype = None
_glfw.glfwGetWindowPos.argtypes = [ctypes.POINTER(_GLFWwindow),
                                   ctypes.POINTER(ctypes.c_int),
                                   ctypes.POINTER(ctypes.c_int)]
def get_window_pos(window):
    """
    Retrieves the position of the client area of the specified window.

    Wrapper for:
        void glfwGetWindowPos(GLFWwindow* window, int* xpos, int* ypos);
    """
    xpos_value = ctypes.c_int(0)
    xpos = ctypes.pointer(xpos_value)
    ypos_value = ctypes.c_int(0)
    ypos = ctypes.pointer(ypos_value)
    _glfw.glfwGetWindowPos(window, xpos, ypos)
    return xpos_value.value, ypos_value.value

_glfw.glfwSetWindowPos.restype = None
_glfw.glfwSetWindowPos.argtypes = [ctypes.POINTER(_GLFWwindow),
                                   ctypes.c_int,
                                   ctypes.c_int]
def set_window_pos(window, xpos, ypos):
    """
    Sets the position of the client area of the specified window.

    Wrapper for:
        void glfwSetWindowPos(GLFWwindow* window, int xpos, int ypos);
    """
    _glfw.glfwSetWindowPos(window, xpos, ypos)

_glfw.glfwGetWindowSize.restype = None
_glfw.glfwGetWindowSize.argtypes = [ctypes.POINTER(_GLFWwindow),
                                    ctypes.POINTER(ctypes.c_int),
                                    ctypes.POINTER(ctypes.c_int)]
def get_window_size(window):
    """
    Retrieves the size of the client area of the specified window.

    Wrapper for:
        void glfwGetWindowSize(GLFWwindow* window, int* width, int* height);
    """
    width_value = ctypes.c_int(0)
    width = ctypes.pointer(width_value)
    height_value = ctypes.c_int(0)
    height = ctypes.pointer(height_value)
    _glfw.glfwGetWindowSize(window, width, height)
    return width_value.value, height_value.value

_glfw.glfwSetWindowSize.restype = None
_glfw.glfwSetWindowSize.argtypes = [ctypes.POINTER(_GLFWwindow),
                                    ctypes.c_int,
                                    ctypes.c_int]
def set_window_size(window, width, height):
    """
    Sets the size of the client area of the specified window.

    Wrapper for:
        void glfwSetWindowSize(GLFWwindow* window, int width, int height);
    """
    _glfw.glfwSetWindowSize(window, width, height)

_glfw.glfwGetFramebufferSize.restype = None
_glfw.glfwGetFramebufferSize.argtypes = [ctypes.POINTER(_GLFWwindow),
                                         ctypes.POINTER(ctypes.c_int),
                                         ctypes.POINTER(ctypes.c_int)]
def get_framebuffer_size(window):
    """
    Retrieves the size of the framebuffer of the specified window.

    Wrapper for:
        void glfwGetFramebufferSize(GLFWwindow* window, int* width, int* height);
    """
    width_value = ctypes.c_int(0)
    width = ctypes.pointer(width_value)
    height_value = ctypes.c_int(0)
    height = ctypes.pointer(height_value)
    _glfw.glfwGetFramebufferSize(window, width, height)
    return width_value.value, height_value.value

_glfw.glfwIconifyWindow.restype = None
_glfw.glfwIconifyWindow.argtypes = [ctypes.POINTER(_GLFWwindow)]
def iconify_window(window):
    """
    Iconifies the specified window.

    Wrapper for:
        void glfwIconifyWindow(GLFWwindow* window);
    """
    _glfw.glfwIconifyWindow(window)

_glfw.glfwRestoreWindow.restype = None
_glfw.glfwRestoreWindow.argtypes = [ctypes.POINTER(_GLFWwindow)]
def restore_window(window):
    """
    Restores the specified window.

    Wrapper for:
        void glfwRestoreWindow(GLFWwindow* window);
    """
    _glfw.glfwRestoreWindow(window)

_glfw.glfwShowWindow.restype = None
_glfw.glfwShowWindow.argtypes = [ctypes.POINTER(_GLFWwindow)]
def show_window(window):
    """
    Makes the specified window visible.

    Wrapper for:
        void glfwShowWindow(GLFWwindow* window);
    """
    _glfw.glfwShowWindow(window)

_glfw.glfwHideWindow.restype = None
_glfw.glfwHideWindow.argtypes = [ctypes.POINTER(_GLFWwindow)]
def hide_window(window):
    """
    Hides the specified window.

    Wrapper for:
        void glfwHideWindow(GLFWwindow* window);
    """
    _glfw.glfwHideWindow(window)

_glfw.glfwGetWindowMonitor.restype = ctypes.POINTER(_GLFWmonitor)
_glfw.glfwGetWindowMonitor.argtypes = [ctypes.POINTER(_GLFWwindow)]
def get_window_monitor(window):
    """
    Returns the monitor that the window uses for full screen mode.

    Wrapper for:
        GLFWmonitor* glfwGetWindowMonitor(GLFWwindow* window);
    """
    return _glfw.glfwGetWindowMonitor(window)

_glfw.glfwGetWindowAttrib.restype = ctypes.c_int
_glfw.glfwGetWindowAttrib.argtypes = [ctypes.POINTER(_GLFWwindow),
                                      ctypes.c_int]
def get_window_attrib(window, attrib):
    """
    Returns an attribute of the specified window.

    Wrapper for:
        int glfwGetWindowAttrib(GLFWwindow* window, int attrib);
    """
    return _glfw.glfwGetWindowAttrib(window, attrib)

_window_user_data_repository = {}
_glfw.glfwSetWindowUserPointer.restype = None
_glfw.glfwSetWindowUserPointer.argtypes = [ctypes.POINTER(_GLFWwindow),
                                           ctypes.c_void_p]
def set_window_user_pointer(window, pointer):
    """
    Sets the user pointer of the specified window. You may pass a normal python object into this function and it will
    be wrapped automatically. The object will be kept in existence until the pointer is set to something else or
    until the window is destroyed.

    Wrapper for:
        void glfwSetWindowUserPointer(GLFWwindow* window, void* pointer);
    """

    data = (False, pointer)
    if not isinstance(pointer, ctypes.c_void_p):
        data = (True, pointer)
        # Create a void pointer for the python object
        pointer = ctypes.cast(ctypes.pointer(ctypes.py_object(pointer)), ctypes.c_void_p)

    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_long)).contents.value
    _window_user_data_repository[window_addr] = data
    _glfw.glfwSetWindowUserPointer(window, pointer)

_glfw.glfwGetWindowUserPointer.restype = ctypes.c_void_p
_glfw.glfwGetWindowUserPointer.argtypes = [ctypes.POINTER(_GLFWwindow)]
def get_window_user_pointer(window):
    """
    Returns the user pointer of the specified window.

    Wrapper for:
        void* glfwGetWindowUserPointer(GLFWwindow* window);
    """

    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_long)).contents.value

    if window_addr in _window_user_data_repository:
        data = _window_user_data_repository[window_addr]
        is_wrapped_py_object = data[0]
        if is_wrapped_py_object:
            return data[1]
    return _glfw.glfwGetWindowUserPointer(window)

_window_pos_callback_repository = {}
_callback_repositories.append(_window_pos_callback_repository)
_glfw.glfwSetWindowPosCallback.restype = _GLFWwindowposfun
_glfw.glfwSetWindowPosCallback.argtypes = [ctypes.POINTER(_GLFWwindow),
                                           _GLFWwindowposfun]
def set_window_pos_callback(window, cbfun):
    """
    Sets the position callback for the specified window.

    Wrapper for:
        GLFWwindowposfun glfwSetWindowPosCallback(GLFWwindow* window, GLFWwindowposfun cbfun);
    """
    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_long)).contents.value
    if window_addr in _window_pos_callback_repository:
        previous_callback = _window_pos_callback_repository[window_addr]
    else:
        previous_callback = None
    if cbfun is None:
        cbfun = 0
    c_cbfun = _GLFWwindowposfun(cbfun)
    _window_pos_callback_repository[window_addr] = (cbfun, c_cbfun)
    cbfun = c_cbfun
    _glfw.glfwSetWindowPosCallback(window, cbfun)
    if previous_callback is not None and previous_callback[0] != 0:
        return previous_callback[0]

_window_size_callback_repository = {}
_callback_repositories.append(_window_size_callback_repository)
_glfw.glfwSetWindowSizeCallback.restype = _GLFWwindowsizefun
_glfw.glfwSetWindowSizeCallback.argtypes = [ctypes.POINTER(_GLFWwindow),
                                            _GLFWwindowsizefun]
def set_window_size_callback(window, cbfun):
    """
    Sets the size callback for the specified window.

    Wrapper for:
        GLFWwindowsizefun glfwSetWindowSizeCallback(GLFWwindow* window, GLFWwindowsizefun cbfun);
    """
    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_long)).contents.value
    if window_addr in _window_size_callback_repository:
        previous_callback = _window_size_callback_repository[window_addr]
    else:
        previous_callback = None
    if cbfun is None:
        cbfun = 0
    c_cbfun = _GLFWwindowsizefun(cbfun)
    _window_size_callback_repository[window_addr] = (cbfun, c_cbfun)
    cbfun = c_cbfun
    _glfw.glfwSetWindowSizeCallback(window, cbfun)
    if previous_callback is not None and previous_callback[0] != 0:
        return previous_callback[0]

_window_close_callback_repository = {}
_callback_repositories.append(_window_close_callback_repository)
_glfw.glfwSetWindowCloseCallback.restype = _GLFWwindowclosefun
_glfw.glfwSetWindowCloseCallback.argtypes = [ctypes.POINTER(_GLFWwindow),
                                             _GLFWwindowclosefun]
def set_window_close_callback(window, cbfun):
    """
    Sets the close callback for the specified window.

    Wrapper for:
        GLFWwindowclosefun glfwSetWindowCloseCallback(GLFWwindow* window, GLFWwindowclosefun cbfun);
    """
    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_long)).contents.value
    if window_addr in _window_close_callback_repository:
        previous_callback = _window_close_callback_repository[window_addr]
    else:
        previous_callback = None
    if cbfun is None:
        cbfun = 0
    c_cbfun = _GLFWwindowclosefun(cbfun)
    _window_close_callback_repository[window_addr] = (cbfun, c_cbfun)
    cbfun = c_cbfun
    _glfw.glfwSetWindowCloseCallback(window, cbfun)
    if previous_callback is not None and previous_callback[0] != 0:
        return previous_callback[0]

_window_refresh_callback_repository = {}
_callback_repositories.append(_window_refresh_callback_repository)
_glfw.glfwSetWindowRefreshCallback.restype = _GLFWwindowrefreshfun
_glfw.glfwSetWindowRefreshCallback.argtypes = [ctypes.POINTER(_GLFWwindow),
                                               _GLFWwindowrefreshfun]
def set_window_refresh_callback(window, cbfun):
    """
    Sets the refresh callback for the specified window.

    Wrapper for:
        GLFWwindowrefreshfun glfwSetWindowRefreshCallback(GLFWwindow* window, GLFWwindowrefreshfun cbfun);
    """
    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_long)).contents.value
    if window_addr in _window_refresh_callback_repository:
        previous_callback = _window_refresh_callback_repository[window_addr]
    else:
        previous_callback = None
    if cbfun is None:
        cbfun = 0
    c_cbfun = _GLFWwindowrefreshfun(cbfun)
    _window_refresh_callback_repository[window_addr] = (cbfun, c_cbfun)
    cbfun = c_cbfun
    _glfw.glfwSetWindowRefreshCallback(window, cbfun)
    if previous_callback is not None and previous_callback[0] != 0:
        return previous_callback[0]

_window_focus_callback_repository = {}
_callback_repositories.append(_window_focus_callback_repository)
_glfw.glfwSetWindowFocusCallback.restype = _GLFWwindowfocusfun
_glfw.glfwSetWindowFocusCallback.argtypes = [ctypes.POINTER(_GLFWwindow),
                                             _GLFWwindowfocusfun]
def set_window_focus_callback(window, cbfun):
    """
    Sets the focus callback for the specified window.

    Wrapper for:
        GLFWwindowfocusfun glfwSetWindowFocusCallback(GLFWwindow* window, GLFWwindowfocusfun cbfun);
    """
    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_long)).contents.value
    if window_addr in _window_focus_callback_repository:
        previous_callback = _window_focus_callback_repository[window_addr]
    else:
        previous_callback = None
    if cbfun is None:
        cbfun = 0
    c_cbfun = _GLFWwindowfocusfun(cbfun)
    _window_focus_callback_repository[window_addr] = (cbfun, c_cbfun)
    cbfun = c_cbfun
    _glfw.glfwSetWindowFocusCallback(window, cbfun)
    if previous_callback is not None and previous_callback[0] != 0:
        return previous_callback[0]

_window_iconify_callback_repository = {}
_callback_repositories.append(_window_iconify_callback_repository)
_glfw.glfwSetWindowIconifyCallback.restype = _GLFWwindowiconifyfun
_glfw.glfwSetWindowIconifyCallback.argtypes = [ctypes.POINTER(_GLFWwindow),
                                               _GLFWwindowiconifyfun]
def set_window_iconify_callback(window, cbfun):
    """
    Sets the iconify callback for the specified window.

    Wrapper for:
        GLFWwindowiconifyfun glfwSetWindowIconifyCallback(GLFWwindow* window, GLFWwindowiconifyfun cbfun);
    """
    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_long)).contents.value
    if window_addr in _window_iconify_callback_repository:
        previous_callback = _window_iconify_callback_repository[window_addr]
    else:
        previous_callback = None
    if cbfun is None:
        cbfun = 0
    c_cbfun = _GLFWwindowiconifyfun(cbfun)
    _window_iconify_callback_repository[window_addr] = (cbfun, c_cbfun)
    cbfun = c_cbfun
    _glfw.glfwSetWindowIconifyCallback(window, cbfun)
    if previous_callback is not None and previous_callback[0] != 0:
        return previous_callback[0]

_framebuffer_size_callback_repository = {}
_callback_repositories.append(_framebuffer_size_callback_repository)
_glfw.glfwSetFramebufferSizeCallback.restype = _GLFWframebuffersizefun
_glfw.glfwSetFramebufferSizeCallback.argtypes = [ctypes.POINTER(_GLFWwindow),
                                                 _GLFWframebuffersizefun]
def set_framebuffer_size_callback(window, cbfun):
    """
    Sets the framebuffer resize callback for the specified window.

    Wrapper for:
        GLFWframebuffersizefun glfwSetFramebufferSizeCallback(GLFWwindow* window, GLFWframebuffersizefun cbfun);
    """
    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_long)).contents.value
    if window_addr in _framebuffer_size_callback_repository:
        previous_callback = _framebuffer_size_callback_repository[window_addr]
    else:
        previous_callback = None
    if cbfun is None:
        cbfun = 0
    c_cbfun = _GLFWframebuffersizefun(cbfun)
    _framebuffer_size_callback_repository[window_addr] = (cbfun, c_cbfun)
    cbfun = c_cbfun
    _glfw.glfwSetFramebufferSizeCallback(window, cbfun)
    if previous_callback is not None and previous_callback[0] != 0:
        return previous_callback[0]

_glfw.glfwPollEvents.restype = None
_glfw.glfwPollEvents.argtypes = []
def poll_events():
    """
    Processes all pending events.

    Wrapper for:
        void glfwPollEvents(void);
    """
    _glfw.glfwPollEvents()

_glfw.glfwWaitEvents.restype = None
_glfw.glfwWaitEvents.argtypes = []
def wait_events():
    """
    Waits until events are pending and processes them.

    Wrapper for:
        void glfwWaitEvents(void);
    """
    _glfw.glfwWaitEvents()

_glfw.glfwGetInputMode.restype = ctypes.c_int
_glfw.glfwGetInputMode.argtypes = [ctypes.POINTER(_GLFWwindow),
                                   ctypes.c_int]
def get_input_mode(window, mode):
    """
    Returns the value of an input option for the specified window.

    Wrapper for:
        int glfwGetInputMode(GLFWwindow* window, int mode);
    """
    return _glfw.glfwGetInputMode(window, mode)

_glfw.glfwSetInputMode.restype = None
_glfw.glfwSetInputMode.argtypes = [ctypes.POINTER(_GLFWwindow),
                                   ctypes.c_int,
                                   ctypes.c_int]
def set_input_mode(window, mode, value):
    """
    Sets an input option for the specified window.
    @param[in] window The window whose input mode to set.
    @param[in] mode One of `GLFW_CURSOR`, `GLFW_STICKY_KEYS` or
    `GLFW_STICKY_MOUSE_BUTTONS`.
    @param[in] value The new value of the specified input mode.

    Wrapper for:
        void glfwSetInputMode(GLFWwindow* window, int mode, int value);
    """
    _glfw.glfwSetInputMode(window, mode, value)

_glfw.glfwGetKey.restype = ctypes.c_int
_glfw.glfwGetKey.argtypes = [ctypes.POINTER(_GLFWwindow),
                             ctypes.c_int]
def get_key(window, key):
    """
    Returns the last reported state of a keyboard key for the specified
    window.

    Wrapper for:
        int glfwGetKey(GLFWwindow* window, int key);
    """
    return _glfw.glfwGetKey(window, key)

_glfw.glfwGetMouseButton.restype = ctypes.c_int
_glfw.glfwGetMouseButton.argtypes = [ctypes.POINTER(_GLFWwindow),
                                     ctypes.c_int]
def get_mouse_button(window, button):
    """
    Returns the last reported state of a mouse button for the specified
    window.

    Wrapper for:
        int glfwGetMouseButton(GLFWwindow* window, int button);
    """
    return _glfw.glfwGetMouseButton(window, button)

_glfw.glfwGetCursorPos.restype = None
_glfw.glfwGetCursorPos.argtypes = [ctypes.POINTER(_GLFWwindow),
                                   ctypes.POINTER(ctypes.c_double),
                                   ctypes.POINTER(ctypes.c_double)]
def get_cursor_pos(window):
    """
    Retrieves the last reported cursor position, relative to the client
    area of the window.

    Wrapper for:
        void glfwGetCursorPos(GLFWwindow* window, double* xpos, double* ypos);
    """
    xpos_value = ctypes.c_double(0.0)
    xpos = ctypes.pointer(xpos_value)
    ypos_value = ctypes.c_double(0.0)
    ypos = ctypes.pointer(ypos_value)
    _glfw.glfwGetCursorPos(window, xpos, ypos)
    return xpos_value.value, ypos_value.value

_glfw.glfwSetCursorPos.restype = None
_glfw.glfwSetCursorPos.argtypes = [ctypes.POINTER(_GLFWwindow),
                                   ctypes.c_double,
                                   ctypes.c_double]
def set_cursor_pos(window, xpos, ypos):
    """
    Sets the position of the cursor, relative to the client area of the window.

    Wrapper for:
        void glfwSetCursorPos(GLFWwindow* window, double xpos, double ypos);
    """
    _glfw.glfwSetCursorPos(window, xpos, ypos)

_key_callback_repository = {}
_callback_repositories.append(_key_callback_repository)
_glfw.glfwSetKeyCallback.restype = _GLFWkeyfun
_glfw.glfwSetKeyCallback.argtypes = [ctypes.POINTER(_GLFWwindow),
                                     _GLFWkeyfun]
def set_key_callback(window, cbfun):
    """
    Sets the key callback.

    Wrapper for:
        GLFWkeyfun glfwSetKeyCallback(GLFWwindow* window, GLFWkeyfun cbfun);
    """
    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_long)).contents.value
    if window_addr in _key_callback_repository:
        previous_callback = _key_callback_repository[window_addr]
    else:
        previous_callback = None
    if cbfun is None:
        cbfun = 0
    c_cbfun = _GLFWkeyfun(cbfun)
    _key_callback_repository[window_addr] = (cbfun, c_cbfun)
    cbfun = c_cbfun
    _glfw.glfwSetKeyCallback(window, cbfun)
    if previous_callback is not None and previous_callback[0] != 0:
        return previous_callback[0]

_char_callback_repository = {}
_callback_repositories.append(_char_callback_repository)
_glfw.glfwSetCharCallback.restype = _GLFWcharfun
_glfw.glfwSetCharCallback.argtypes = [ctypes.POINTER(_GLFWwindow),
                                      _GLFWcharfun]
def set_char_callback(window, cbfun):
    """
    Sets the Unicode character callback.

    Wrapper for:
        GLFWcharfun glfwSetCharCallback(GLFWwindow* window, GLFWcharfun cbfun);
    """
    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_long)).contents.value
    if window_addr in _char_callback_repository:
        previous_callback = _char_callback_repository[window_addr]
    else:
        previous_callback = None
    if cbfun is None:
        cbfun = 0
    c_cbfun = _GLFWcharfun(cbfun)
    _char_callback_repository[window_addr] = (cbfun, c_cbfun)
    cbfun = c_cbfun
    _glfw.glfwSetCharCallback(window, cbfun)
    if previous_callback is not None and previous_callback[0] != 0:
        return previous_callback[0]

_mouse_button_callback_repository = {}
_callback_repositories.append(_mouse_button_callback_repository)
_glfw.glfwSetMouseButtonCallback.restype = _GLFWmousebuttonfun
_glfw.glfwSetMouseButtonCallback.argtypes = [ctypes.POINTER(_GLFWwindow),
                                             _GLFWmousebuttonfun]
def set_mouse_button_callback(window, cbfun):
    """
    Sets the mouse button callback.

    Wrapper for:
        GLFWmousebuttonfun glfwSetMouseButtonCallback(GLFWwindow* window, GLFWmousebuttonfun cbfun);
    """
    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_long)).contents.value
    if window_addr in _mouse_button_callback_repository:
        previous_callback = _mouse_button_callback_repository[window_addr]
    else:
        previous_callback = None
    if cbfun is None:
        cbfun = 0
    c_cbfun = _GLFWmousebuttonfun(cbfun)
    _mouse_button_callback_repository[window_addr] = (cbfun, c_cbfun)
    cbfun = c_cbfun
    _glfw.glfwSetMouseButtonCallback(window, cbfun)
    if previous_callback is not None and previous_callback[0] != 0:
        return previous_callback[0]

_cursor_pos_callback_repository = {}
_callback_repositories.append(_cursor_pos_callback_repository)
_glfw.glfwSetCursorPosCallback.restype = _GLFWcursorposfun
_glfw.glfwSetCursorPosCallback.argtypes = [ctypes.POINTER(_GLFWwindow),
                                           _GLFWcursorposfun]
def set_cursor_pos_callback(window, cbfun):
    """
    Sets the cursor position callback.

    Wrapper for:
        GLFWcursorposfun glfwSetCursorPosCallback(GLFWwindow* window, GLFWcursorposfun cbfun);
    """
    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_long)).contents.value
    if window_addr in _cursor_pos_callback_repository:
        previous_callback = _cursor_pos_callback_repository[window_addr]
    else:
        previous_callback = None
    if cbfun is None:
        cbfun = 0
    c_cbfun = _GLFWcursorposfun(cbfun)
    _cursor_pos_callback_repository[window_addr] = (cbfun, c_cbfun)
    cbfun = c_cbfun
    _glfw.glfwSetCursorPosCallback(window, cbfun)
    if previous_callback is not None and previous_callback[0] != 0:
        return previous_callback[0]

_cursor_enter_callback_repository = {}
_callback_repositories.append(_cursor_enter_callback_repository)
_glfw.glfwSetCursorEnterCallback.restype = _GLFWcursorenterfun
_glfw.glfwSetCursorEnterCallback.argtypes = [ctypes.POINTER(_GLFWwindow),
                                             _GLFWcursorenterfun]
def set_cursor_enter_callback(window, cbfun):
    """
    Sets the cursor enter/exit callback.

    Wrapper for:
        GLFWcursorenterfun glfwSetCursorEnterCallback(GLFWwindow* window, GLFWcursorenterfun cbfun);
    """
    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_long)).contents.value
    if window_addr in _cursor_enter_callback_repository:
        previous_callback = _cursor_enter_callback_repository[window_addr]
    else:
        previous_callback = None
    if cbfun is None:
        cbfun = 0
    c_cbfun = _GLFWcursorenterfun(cbfun)
    _cursor_enter_callback_repository[window_addr] = (cbfun, c_cbfun)
    cbfun = c_cbfun
    _glfw.glfwSetCursorEnterCallback(window, cbfun)
    if previous_callback is not None and previous_callback[0] != 0:
        return previous_callback[0]

_scroll_callback_repository = {}
_callback_repositories.append(_scroll_callback_repository)
_glfw.glfwSetScrollCallback.restype = _GLFWscrollfun
_glfw.glfwSetScrollCallback.argtypes = [ctypes.POINTER(_GLFWwindow),
                                        _GLFWscrollfun]
def set_scroll_callback(window, cbfun):
    """
    Sets the scroll callback.

    Wrapper for:
        GLFWscrollfun glfwSetScrollCallback(GLFWwindow* window, GLFWscrollfun cbfun);
    """
    window_addr = ctypes.cast(ctypes.pointer(window),
                              ctypes.POINTER(ctypes.c_long)).contents.value
    if window_addr in _scroll_callback_repository:
        previous_callback = _scroll_callback_repository[window_addr]
    else:
        previous_callback = None
    if cbfun is None:
        cbfun = 0
    c_cbfun = _GLFWscrollfun(cbfun)
    _scroll_callback_repository[window_addr] = (cbfun, c_cbfun)
    cbfun = c_cbfun
    _glfw.glfwSetScrollCallback(window, cbfun)
    if previous_callback is not None and previous_callback[0] != 0:
        return previous_callback[0]

_glfw.glfwJoystickPresent.restype = ctypes.c_int
_glfw.glfwJoystickPresent.argtypes = [ctypes.c_int]
def joystick_present(joy):
    """
    Returns whether the specified joystick is present.

    Wrapper for:
        int glfwJoystickPresent(int joy);
    """
    return _glfw.glfwJoystickPresent(joy)

_glfw.glfwGetJoystickAxes.restype = ctypes.POINTER(ctypes.c_float)
_glfw.glfwGetJoystickAxes.argtypes = [ctypes.c_int,
                                      ctypes.POINTER(ctypes.c_int)]
def get_joystick_axes(joy):
    """
    Returns the values of all axes of the specified joystick.

    Wrapper for:
        const float* glfwGetJoystickAxes(int joy, int* count);
    """
    count_value = ctypes.c_int(0)
    count = ctypes.pointer(count_value)
    result = _glfw.glfwGetJoystickAxes(joy, count)
    return result, count_value.value

_glfw.glfwGetJoystickButtons.restype = ctypes.POINTER(ctypes.c_ubyte)
_glfw.glfwGetJoystickButtons.argtypes = [ctypes.c_int,
                                         ctypes.POINTER(ctypes.c_int)]
def get_joystick_buttons(joy):
    """
    Returns the state of all buttons of the specified joystick.

    Wrapper for:
        const unsigned char* glfwGetJoystickButtons(int joy, int* count);
    """
    count_value = ctypes.c_int(0)
    count = ctypes.pointer(count_value)
    result = _glfw.glfwGetJoystickButtons(joy, count)
    return result, count_value.value

_glfw.glfwGetJoystickName.restype = ctypes.c_char_p
_glfw.glfwGetJoystickName.argtypes = [ctypes.c_int]
def get_joystick_name(joy):
    """
    Returns the name of the specified joystick.

    Wrapper for:
        const char* glfwGetJoystickName(int joy);
    """
    return _glfw.glfwGetJoystickName(joy)

_glfw.glfwSetClipboardString.restype = None
_glfw.glfwSetClipboardString.argtypes = [ctypes.POINTER(_GLFWwindow),
                                         ctypes.c_char_p]
def set_clipboard_string(window, string):
    """
    Sets the clipboard to the specified string.

    Wrapper for:
        void glfwSetClipboardString(GLFWwindow* window, const char* string);
    """
    _glfw.glfwSetClipboardString(window, _to_char_p(string))

_glfw.glfwGetClipboardString.restype = ctypes.c_char_p
_glfw.glfwGetClipboardString.argtypes = [ctypes.POINTER(_GLFWwindow)]
def get_clipboard_string(window):
    """
    Retrieves the contents of the clipboard as a string.

    Wrapper for:
        const char* glfwGetClipboardString(GLFWwindow* window);
    """
    return _glfw.glfwGetClipboardString(window)

_glfw.glfwGetTime.restype = ctypes.c_double
_glfw.glfwGetTime.argtypes = []
def get_time():
    """
    Returns the value of the GLFW timer.

    Wrapper for:
        double glfwGetTime(void);
    """
    return _glfw.glfwGetTime()

_glfw.glfwSetTime.restype = None
_glfw.glfwSetTime.argtypes = [ctypes.c_double]
def set_time(time):
    """
    Sets the GLFW timer.

    Wrapper for:
        void glfwSetTime(double time);
    """
    _glfw.glfwSetTime(time)

_glfw.glfwMakeContextCurrent.restype = None
_glfw.glfwMakeContextCurrent.argtypes = [ctypes.POINTER(_GLFWwindow)]
def make_context_current(window):
    """
    Makes the context of the specified window current for the calling
    thread.

    Wrapper for:
        void glfwMakeContextCurrent(GLFWwindow* window);
    """
    _glfw.glfwMakeContextCurrent(window)

_glfw.glfwGetCurrentContext.restype = ctypes.POINTER(_GLFWwindow)
_glfw.glfwGetCurrentContext.argtypes = []
def get_current_context():
    """
    Returns the window whose context is current on the calling thread.

    Wrapper for:
        GLFWwindow* glfwGetCurrentContext(void);
    """
    return _glfw.glfwGetCurrentContext()

_glfw.glfwSwapBuffers.restype = None
_glfw.glfwSwapBuffers.argtypes = [ctypes.POINTER(_GLFWwindow)]
def swap_buffers(window):
    """
    Swaps the front and back buffers of the specified window.

    Wrapper for:
        void glfwSwapBuffers(GLFWwindow* window);
    """
    _glfw.glfwSwapBuffers(window)

_glfw.glfwSwapInterval.restype = None
_glfw.glfwSwapInterval.argtypes = [ctypes.c_int]
def swap_interval(interval):
    """
    Sets the swap interval for the current context.

    Wrapper for:
        void glfwSwapInterval(int interval);
    """
    _glfw.glfwSwapInterval(interval)

_glfw.glfwExtensionSupported.restype = ctypes.c_int
_glfw.glfwExtensionSupported.argtypes = [ctypes.c_char_p]
def extension_supported(extension):
    """
    Returns whether the specified extension is available.

    Wrapper for:
        int glfwExtensionSupported(const char* extension);
    """
    return _glfw.glfwExtensionSupported(_to_char_p(extension))

_glfw.glfwGetProcAddress.restype = ctypes.c_void_p
_glfw.glfwGetProcAddress.argtypes = [ctypes.c_char_p]
def get_proc_address(procname):
    """
    Returns the address of the specified function for the current
    context.

    Wrapper for:
        GLFWglproc glfwGetProcAddress(const char* procname);
    """
    return _glfw.glfwGetProcAddress(_to_char_p(procname))

if hasattr(_glfw, 'glfwSetDropCallback'):
    _window_drop_callback_repository = {}
    _callback_repositories.append(_window_drop_callback_repository)
    _glfw.glfwSetDropCallback.restype = _GLFWdropfun
    _glfw.glfwSetDropCallback.argtypes = [ctypes.POINTER(_GLFWwindow),
                                          _GLFWdropfun]
    def set_drop_callback(window, cbfun):
        """
        Sets the file drop callback.

        Wrapper for:
            GLFWdropfun glfwSetDropCallback(GLFWwindow* window, GLFWdropfun cbfun);
        """
        window_addr = ctypes.cast(ctypes.pointer(window),
                                  ctypes.POINTER(ctypes.c_long)).contents.value
        if window_addr in _window_drop_callback_repository:
            previous_callback = _window_drop_callback_repository[window_addr]
        else:
            previous_callback = None
        if cbfun is None:
            cbfun = 0
        else:
            def cb_wrapper(window, count, c_paths, cbfun=cbfun):
                paths = [c_paths[i].decode('utf-8') for i in range(count)]
                cbfun(window, paths)
            cbfun = cb_wrapper
        c_cbfun = _GLFWdropfun(cbfun)
        _window_drop_callback_repository[window_addr] = (cbfun, c_cbfun)
        cbfun = c_cbfun
        _glfw.glfwSetDropCallback(window, cbfun)
        if previous_callback is not None and previous_callback[0] != 0:
            return previous_callback[0]

if hasattr(_glfw, 'glfwSetCharModsCallback'):
    _window_char_mods_callback_repository = {}
    _callback_repositories.append(_window_char_mods_callback_repository)
    _glfw.glfwSetCharModsCallback.restype = _GLFWcharmodsfun
    _glfw.glfwSetCharModsCallback.argtypes = [ctypes.POINTER(_GLFWwindow),
                                              _GLFWcharmodsfun]
    def set_char_mods_callback(window, cbfun):
        """
        Sets the Unicode character with modifiers callback.

        Wrapper for:
            GLFWcharmodsfun glfwSetCharModsCallback(GLFWwindow* window, GLFWcharmodsfun cbfun);
        """
        window_addr = ctypes.cast(ctypes.pointer(window),
                                  ctypes.POINTER(ctypes.c_long)).contents.value
        if window_addr in _window_char_mods_callback_repository:
            previous_callback = _window_char_mods_callback_repository[window_addr]
        else:
            previous_callback = None
        if cbfun is None:
            cbfun = 0
        c_cbfun = _GLFWcharmodsfun(cbfun)
        _window_char_mods_callback_repository[window_addr] = (cbfun, c_cbfun)
        cbfun = c_cbfun
        _glfw.glfwSetCharModsCallback(window, cbfun)
        if previous_callback is not None and previous_callback[0] != 0:
            return previous_callback[0]

if hasattr(_glfw, 'glfwVulkanSupported'):
    _glfw.glfwVulkanSupported.restype = ctypes.c_int
    _glfw.glfwVulkanSupported.argtypes = []
    def vulkan_supported():
        """
        Returns whether the Vulkan loader has been found.

        Wrapper for:
            int glfwVulkanSupported(void);
        """
        return _glfw.glfwVulkanSupported() != 0

if hasattr(_glfw, 'glfwGetRequiredInstanceExtensions'):
    _glfw.glfwGetRequiredInstanceExtensions.restype = ctypes.POINTER(ctypes.c_char_p)
    _glfw.glfwGetRequiredInstanceExtensions.argtypes = [ctypes.POINTER(ctypes.c_uint32)]
    def get_required_instance_extensions():
        """
        Returns the Vulkan instance extensions required by GLFW.

        Wrapper for:
            const char** glfwGetRequiredInstanceExtensions(uint32_t* count);
        """
        count_value = ctypes.c_uint32(0)
        count = ctypes.pointer(count_value)
        c_extensions = _glfw.glfwGetRequiredInstanceExtensions(count)
        count = count_value.value
        extensions = [c_extensions[i].decode('utf-8') for i in range(count)]
        return extensions

if hasattr(_glfw, 'glfwGetTimerValue'):
    _glfw.glfwGetTimerValue.restype = ctypes.c_uint64
    _glfw.glfwGetTimerValue.argtypes = []
    def get_timer_value():
        """
        Returns the current value of the raw timer.

        Wrapper for:
            uint64_t glfwGetTimerValue(void);
        """
        return int(_glfw.glfwGetTimerValue())

if hasattr(_glfw, 'glfwGetTimerFrequency'):
    _glfw.glfwGetTimerFrequency.restype = ctypes.c_uint64
    _glfw.glfwGetTimerFrequency.argtypes = []
    def get_timer_frequency():
        """
        Returns the frequency, in Hz, of the raw timer.

        Wrapper for:
            uint64_t glfwGetTimerFrequency(void);
        """
        return int(_glfw.glfwGetTimerFrequency())


if hasattr(_glfw, 'glfwSetJoystickCallback'):
    _joystick_callback = None
    _glfw.glfwSetJoystickCallback.restype = _GLFWjoystickfun
    _glfw.glfwSetJoystickCallback.argtypes = [_GLFWjoystickfun]
    def set_joystick_callback(cbfun):
        """
        Sets the error callback.

        Wrapper for:
            GLFWjoystickfun glfwSetJoystickCallback(GLFWjoystickfun cbfun);
        """
        global _joystick_callback
        previous_callback = _error_callback
        if cbfun is None:
            cbfun = 0
        c_cbfun = _GLFWjoystickfun(cbfun)
        _joystick_callback = (cbfun, c_cbfun)
        cbfun = c_cbfun
        _glfw.glfwSetJoystickCallback(cbfun)
        if previous_callback is not None and previous_callback[0] != 0:
            return previous_callback[0]

if hasattr(_glfw, 'glfwGetKeyName'):
    _glfw.glfwGetKeyName.restype = ctypes.c_char_p
    _glfw.glfwGetKeyName.argtypes = [ctypes.c_int, ctypes.c_int]
    def get_key_name(key, scancode):
        """
        Returns the localized name of the specified printable key.

        Wrapper for:
            const char* glfwGetKeyName(int key, int scancode);
        """
        key_name = _glfw.glfwGetKeyName(key, scancode)
        if key_name:
            return key_name.decode('utf-8')
        return None

if hasattr(_glfw, 'glfwCreateCursor'):
    _glfw.glfwCreateCursor.restype = ctypes.POINTER(_GLFWcursor)
    _glfw.glfwCreateCursor.argtypes = [ctypes.POINTER(_GLFWimage),
                                       ctypes.c_int,
                                       ctypes.c_int]
    def create_cursor(image, xhot, yhot):
        """
        Creates a custom cursor.

        Wrapper for:
            GLFWcursor* glfwCreateCursor(const GLFWimage* image, int xhot, int yhot);
        """
        c_image = _GLFWimage()
        c_image.wrap(image)
        return _glfw.glfwCreateCursor(ctypes.pointer(c_image), xhot, yhot)

if hasattr(_glfw, 'glfwCreateStandardCursor'):
    _glfw.glfwCreateStandardCursor.restype = ctypes.POINTER(_GLFWcursor)
    _glfw.glfwCreateStandardCursor.argtypes = [ctypes.c_int]
    def create_standard_cursor(shape):
        """
        Creates a cursor with a standard shape.

        Wrapper for:
            GLFWcursor* glfwCreateStandardCursor(int shape);
        """
        return _glfw.glfwCreateStandardCursor(shape)

if hasattr(_glfw, 'glfwDestroyCursor'):
    _glfw.glfwDestroyCursor.restype = None
    _glfw.glfwDestroyCursor.argtypes = [ctypes.POINTER(_GLFWcursor)]
    def destroy_cursor(cursor):
        """
        Destroys a cursor.

        Wrapper for:
            void glfwDestroyCursor(GLFWcursor* cursor);
        """
        _glfw.glfwDestroyCursor(cursor)

if hasattr(_glfw, 'glfwSetCursor'):
    _glfw.glfwSetCursor.restype = None
    _glfw.glfwSetCursor.argtypes = [ctypes.POINTER(_GLFWwindow),
                                    ctypes.POINTER(_GLFWcursor)]
    def set_cursor(window, cursor):
        """
        Sets the cursor for the window.

        Wrapper for:
            void glfwSetCursor(GLFWwindow* window, GLFWcursor* cursor);
        """
        _glfw.glfwSetCursor(window, cursor)

if hasattr(_glfw, 'glfwCreateWindowSurface'):
    _glfw.glfwCreateWindowSurface.restype = ctypes.c_int
    _glfw.glfwCreateWindowSurface.argtypes = [ctypes.c_void_p,
                                              ctypes.POINTER(_GLFWwindow),
                                              ctypes.c_void_p,
                                              ctypes.c_void_p]
    def create_window_surface(instance, window, allocator, surface):
        """
        Creates a Vulkan surface for the specified window.

        Wrapper for:
            VkResult glfwCreateWindowSurface(VkInstance instance, GLFWwindow* window, const VkAllocationCallbacks* allocator, VkSurfaceKHR* surface);
        """
        return _glfw.glfwCreateWindowSurface(instance, window, allocator, surface)

if hasattr(_glfw, 'glfwGetPhysicalDevicePresentationSupport'):
    _glfw.glfwGetPhysicalDevicePresentationSupport.restype = ctypes.c_int
    _glfw.glfwGetPhysicalDevicePresentationSupport.argtypes = [ctypes.c_void_p,
                                                               ctypes.c_void_p,
                                                               ctypes.c_uint32]
    def get_physical_device_presentation_support(instance, device, queuefamily):
        """
        Creates a Vulkan surface for the specified window.

        Wrapper for:
            int glfwGetPhysicalDevicePresentationSupport(VkInstance instance, VkPhysicalDevice device, uint32_t queuefamily);
        """
        return _glfw.glfwGetPhysicalDevicePresentationSupport(instance, device, queuefamily)

if hasattr(_glfw, 'glfwGetInstanceProcAddress'):
    _glfw.glfwGetInstanceProcAddress.restype = ctypes.c_void_p
    _glfw.glfwGetInstanceProcAddress.argtypes = [ctypes.c_void_p,
                                                 ctypes.c_char_p]
    def get_instance_proc_address(instance, procname):
        """
        Returns the address of the specified Vulkan instance function.

        Wrapper for:
            GLFWvkproc glfwGetInstanceProcAddress(VkInstance instance, const char* procname);
        """
        return _glfw.glfwGetInstanceProcAddress(instance, procname)

if hasattr(_glfw, 'glfwSetWindowIcon'):
    _glfw.glfwSetWindowIcon.restype = None
    _glfw.glfwSetWindowIcon.argtypes = [ctypes.POINTER(_GLFWwindow),
                                        ctypes.c_int,
                                        ctypes.POINTER(_GLFWimage)]


    def set_window_icon(window, count, images):
        """
        Sets the icon for the specified window.

        Wrapper for:
            void glfwSetWindowIcon(GLFWwindow* window, int count, const GLFWimage* images);
        """
        if count == 1 and (not hasattr(images, '__len__') or len(images) == 3):
            # Stay compatible to calls passing a single icon
            images = [images]
        array_type = _GLFWimage * count
        _images = array_type()
        for i, image in enumerate(images):
            _images[i].wrap(image)
        _glfw.glfwSetWindowIcon(window, count, _images)

if hasattr(_glfw, 'glfwSetWindowSizeLimits'):
    _glfw.glfwSetWindowSizeLimits.restype = None
    _glfw.glfwSetWindowSizeLimits.argtypes = [ctypes.POINTER(_GLFWwindow),
                                              ctypes.c_int, ctypes.c_int,
                                              ctypes.c_int, ctypes.c_int]


    def set_window_size_limits(window,
                               minwidth, minheight,
                               maxwidth, maxheight):
        """
        Sets the size limits of the specified window.

        Wrapper for:
            void glfwSetWindowSizeLimits(GLFWwindow* window, int minwidth, int minheight, int maxwidth, int maxheight);
        """
        _glfw.glfwSetWindowSizeLimits(window,
                                      minwidth, minheight,
                                      maxwidth, maxheight)

if hasattr(_glfw, 'glfwSetWindowAspectRatio'):
    _glfw.glfwSetWindowAspectRatio.restype = None
    _glfw.glfwSetWindowAspectRatio.argtypes = [ctypes.POINTER(_GLFWwindow),
                                               ctypes.c_int, ctypes.c_int]
    def set_window_aspect_ratio(window, numer, denom):
        """
        Sets the aspect ratio of the specified window.

        Wrapper for:
            void glfwSetWindowAspectRatio(GLFWwindow* window, int numer, int denom);
        """
        _glfw.glfwSetWindowAspectRatio(window, numer, denom)

if hasattr(_glfw, 'glfwGetWindowFrameSize'):
    _glfw.glfwGetWindowFrameSize.restype = None
    _glfw.glfwGetWindowFrameSize.argtypes = [ctypes.POINTER(_GLFWwindow),
                                             ctypes.POINTER(ctypes.c_int),
                                             ctypes.POINTER(ctypes.c_int),
                                             ctypes.POINTER(ctypes.c_int),
                                             ctypes.POINTER(ctypes.c_int)]
    def set_get_window_frame_size(window):
        """
        Retrieves the size of the frame of the window.

        Wrapper for:
            void glfwGetWindowFrameSize(GLFWwindow* window, int* left, int* top, int* right, int* bottom);
        """
        left = ctypes.c_int(0)
        top = ctypes.c_int(0)
        right = ctypes.c_int(0)
        bottom = ctypes.c_int(0)
        _glfw.glfwGetWindowFrameSize(window,
                                     ctypes.pointer(left),
                                     ctypes.pointer(top),
                                     ctypes.pointer(right),
                                     ctypes.pointer(bottom))
        return left.value, top.value, right.value, bottom.value

if hasattr(_glfw, 'glfwMaximizeWindow'):
    _glfw.glfwMaximizeWindow.restype = None
    _glfw.glfwMaximizeWindow.argtypes = [ctypes.POINTER(_GLFWwindow)]
    def maximize_window(window):
        """
        Maximizes the specified window.

        Wrapper for:
            void glfwMaximizeWindow(GLFWwindow* window);
        """
        _glfw.glfwMaximizeWindow(window)

if hasattr(_glfw, 'glfwFocusWindow'):
    _glfw.glfwFocusWindow.restype = None
    _glfw.glfwFocusWindow.argtypes = [ctypes.POINTER(_GLFWwindow)]
    def focus_window(window):
        """
        Brings the specified window to front and sets input focus.

        Wrapper for:
            void glfwFocusWindow(GLFWwindow* window);
        """
        _glfw.glfwFocusWindow(window)

if hasattr(_glfw, 'glfwSetWindowMonitor'):
    _glfw.glfwSetWindowMonitor.restype = None
    _glfw.glfwSetWindowMonitor.argtypes = [ctypes.POINTER(_GLFWwindow),
                                           ctypes.POINTER(_GLFWmonitor),
                                           ctypes.c_int,
                                           ctypes.c_int,
                                           ctypes.c_int,
                                           ctypes.c_int,
                                           ctypes.c_int]
    def set_window_monitor(window, monitor, xpos, ypos, width, height,
                           refresh_rate):
        """
        Sets the mode, monitor, video mode and placement of a window.

        Wrapper for:
            void glfwSetWindowMonitor(GLFWwindow* window, GLFWmonitor* monitor, int xpos, int ypos, int width, int height, int refreshRate);
        """
        _glfw.glfwSetWindowMonitor(window, monitor,
                                   xpos, ypos, width, height, refresh_rate)

if hasattr(_glfw, 'glfwWaitEventsTimeout'):
    _glfw.glfwWaitEventsTimeout.restype = None
    _glfw.glfwWaitEventsTimeout.argtypes = [ctypes.c_double]
    def wait_events_timeout(timeout):
        """
        Waits with timeout until events are queued and processes them.

        Wrapper for:
            void glfwWaitEventsTimeout(double timeout);
        """
        _glfw.glfwWaitEventsTimeout(timeout)

if hasattr(_glfw, 'glfwPostEmptyEvent'):
    _glfw.glfwPostEmptyEvent.restype = None
    _glfw.glfwPostEmptyEvent.argtypes = []
    def post_empty_event():
        """
        Posts an empty event to the event queue.

        Wrapper for:
            void glfwPostEmptyEvent();
        """
        _glfw.glfwPostEmptyEvent()

_prepare_errcheck()
