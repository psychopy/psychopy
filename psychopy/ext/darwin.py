import sys, ctypes, ctypes.util

#constants
KERN_SUCCESS=0;
kCGLCPSwapInterval= ctypes.c_int(222)
#these defined in thread_policy.h from apple (googleable)
THREAD_STANDARD_POLICY=1 
THREAD_STANDARD_POLICY_COUNT=0 
THREAD_EXTENDED_POLICY=1
THREAD_EXTENDED_POLICY_COUNT=1 
THREAD_TIME_CONSTRAINT_POLICY=2
THREAD_TIME_CONSTRAINT_POLICY_COUNT=4 
#these were found in pyglet/window/carbon/constants thanks to Alex Holkner
kCFStringEncodingASCII = 0x0600
kCFStringEncodingUnicode = 0x0100
kCFStringEncodingUTF8 = 0x08000100
kCFNumberLongType = 10
#some data types these can be found in various *.defs
CGDirectDisplayID = ctypes.c_void_p
CGDisplayCount = ctypes.c_uint32
CGTableCount = ctypes.c_uint32
CGDisplayCoord = ctypes.c_int32
CGByteValue = ctypes.c_ubyte
CGOpenGLDisplayMask = ctypes.c_uint32
CGRefreshRate = ctypes.c_double
CGCaptureOptions = ctypes.c_uint32
integer_t = ctypes.c_int32
natural_t = ctypes.c_uint32
thread_flavor_t		= ctypes.c_int32 #in mach_types.defs
thread_info_t		= integer_t * 12 #in mach_types.defs
thread_policy_flavor_t	= natural_t #in mach_types.defs
thread_policy_t		= integer_t * 16 #in mach_types.defs
#for use with sysctl()
CTL_HW=6		#/* generic cpu/io */
HW_BUS_FREQ=14

cocoa = ctypes.cdll.LoadLibrary(ctypes.util.find_library("Cocoa"))#could use carbon instead?
#mach = ctypes.cdll.LoadLibrary(ctypes.util.find_library("libm"))#not needed - all the functions seem to be in cocoa
#ogl = ctypes.cdll.LoadLibrary(ctypes.util.find_library("OpenGL"))#not needed - all the functions seem to be in cocoa

def _create_cfstring(text):#some string parameters need to be converted to SFStrings
    return cocoa.CFStringCreateWithCString(ctypes.c_void_p(), 
                                            text.encode('utf8'),
                                            kCFStringEncodingUTF8)
class _timeConstraintThreadPolicy(ctypes.Structure):
    _fields_ = [('period', ctypes.c_uint),#HZ/160
            ('computation', ctypes.c_uint),#HZ/3300
            ('constrain', ctypes.c_uint),#HZ/2200
            ('preemptible', ctypes.c_int)]

def syncSwapBuffers(n):
    """syncSwapBuffers(n)
    if n==1 then buffers will sync, otherwise sync will bee turned off"""
    try:        
        # set v to 1 to enable vsync, 0 to disable vsync
        v = ctypes.c_int(n)
        #this is the parameter index?!
        cocoa.CGLSetParameter(cocoa.CGLGetCurrentContext(), kCGLCPSwapInterval, ctypes.pointer(v))
    except:
        print "Unable to set vsync mode. Using driver defaults" 
        
def getBusFreq():
    """Get the frequency of the system bus (HZ)"""
    mib = (ctypes.c_int*2)(CTL_HW, HW_BUS_FREQ)
    val = ctypes.c_int()
    intSize = ctypes.c_int(ctypes.sizeof(val))
    cocoa.sysctl(ctypes.byref(mib), 2, ctypes.byref(val), ctypes.byref(intSize), 0, 0)
    return val.value
    
def rush(value=True):
    if value:
        HZ = getBusFreq()
        extendedPolicy=_timeConstraintThreadPolicy()
        extendedPolicy.period=ctypes.c_uint(HZ/160)
        extendedPolicy.computation=ctypes.c_uint(HZ/3300)
        extendedPolicy.constrain=ctypes.c_uint(HZ/2200)
        extendedPolicy.preemptible=ctypes.c_uint(1)
        err=cocoa.thread_policy_set(cocoa.mach_thread_self(), THREAD_TIME_CONSTRAINT_POLICY, 
            ctypes.byref(extendedPolicy), #send the address of the struct
            THREAD_TIME_CONSTRAINT_POLICY_COUNT)
#    if (error != KERN_SUCCESS)
    else:
        cocoa.thread_policy_set(cocoa.mach_thread_self(), THREAD_STANDARD_POLICY)
def getRush():
    """Determine whether rush is currently set """
    pass
def getScreens():
    """Get a list of display IDs from cocoa"""
    count = CGDisplayCount()
    cocoa.CGGetActiveDisplayList(0, None, ctypes.byref(count))
    displays = (CGDirectDisplayID * count.value)()
    cocoa.CGGetActiveDisplayList(count.value, displays, ctypes.byref(count))
    return [id for id in displays]
    
def getRefreshRate(screen=None):
    """Return the refresh rate of the given screen. If 
    """
    screens=getScreens()
    if screen==None:
        scrID = cocoa.CGMainDisplayID()
    elif screen>(len(screens)-1):
        raise IndexError, "Requested refresh rate of screen %i, but only %i screens were found" %(screen, len(screens))
    else:
        scrID=getScreens()[screen]
    mode = cocoa.CGDisplayCurrentMode(scrID)
    refreshCF = cocoa.CFDictionaryGetValue(mode, _create_cfstring('RefreshRate'))
    refresh = ctypes.c_long()
    cocoa.CFNumberGetValue(refreshCF, kCFNumberLongType, ctypes.byref(refresh))
    return refresh.value
    
    
    