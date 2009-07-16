import sys, ctypes, ctypes.util
from psychopy import log

#constants
KERN_SUCCESS=0;
kCGLCPSwapInterval= ctypes.c_int(222)
#these defined in thread_policy.h from apple (googleable)
THREAD_STANDARD_POLICY=ctypes.c_int(1)
THREAD_STANDARD_POLICY_COUNT=ctypes.c_int(0 )
THREAD_EXTENDED_POLICY=ctypes.c_int(1)
THREAD_EXTENDED_POLICY_COUNT=ctypes.c_int(1) 
THREAD_TIME_CONSTRAINT_POLICY=ctypes.c_int(2)
THREAD_TIME_CONSTRAINT_POLICY_COUNT=ctypes.c_int(4)
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
CTL_HW=ctypes.c_int(6)		#/* generic cpu/io */
HW_BUS_FREQ=ctypes.c_int(14)

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
    """Raise the priority of the current thread/process 
    Win32 and OS X only so far - on linux use os.nice(niceIncrement)
    
    Set with rush(True) or rush(False)
    
    Beware and don't take priority until after debugging your code
    and ensuring you have a way out (e.g. an escape sequence of
    keys within the display loop). Otherwise you could end up locked
    out and having to reboot!
    """
    if value:
        HZ = getBusFreq()
        extendedPolicy=_timeConstraintThreadPolicy()
        extendedPolicy.period=HZ/160
        extendedPolicy.computation=HZ/3300
        extendedPolicy.constrain= HZ/2200
        extendedPolicy.preemptible=1
#        extendedPolicy=getThreadPolicy(getDefault=True, flavour=THREAD_TIME_CONSTRAINT_POLICY)
        err=cocoa.thread_policy_set(cocoa.mach_thread_self(), THREAD_TIME_CONSTRAINT_POLICY, 
            ctypes.byref(extendedPolicy), #send the address of the struct
            THREAD_TIME_CONSTRAINT_POLICY_COUNT)
        if err!=KERN_SUCCESS:
            log.error('Failed to set darwin thread policy, with thread_policy_set')
        else:
            print 'ok'
            log.info('Successfully set darwin thread to realtime')
    else:
        #revert to default policy
        extendedPolicy=getThreadPolicy(getDefault=True, flavour=THREAD_STANDARD_POLICY)
        err=cocoa.thread_policy_set(cocoa.mach_thread_self(), THREAD_STANDARD_POLICY, 
            ctypes.byref(extendedPolicy), #send the address of the struct
            THREAD_STANDARD_POLICY_COUNT)
        
def getThreadPolicy(getDefault, flavour):
    """Retrieve the current (or default) thread policy.
    
    getDefault should be True or False
    flavour should be 1 (standard) or 2 (realtime)
    
    Returns a ctypes struct with fields:
           .period
           .computation
           .constrain
           .preemptible
           
    See http://docs.huihoo.com/darwin/kernel-programming-guide/scheduler/chapter_8_section_4.html"""
    extendedPolicy=_timeConstraintThreadPolicy()#to store the infos
    getDefault=ctypes.c_int(getDefault)#we want to retrive actual policy or the default
    err=cocoa.thread_policy_get(cocoa.mach_thread_self(), THREAD_TIME_CONSTRAINT_POLICY, 
        ctypes.byref(extendedPolicy), #send the address of the policy struct
        ctypes.byref(THREAD_TIME_CONSTRAINT_POLICY_COUNT),
        ctypes.byref(getDefault))
    return extendedPolicy
def getRush():
    """Determine whether or not we are in rush mode. Returns True/False"""
    policy = getThreadPolicy(getDefault=False,flavour=THREAD_TIME_CONSTRAINT_POLICY)
    default = getThreadPolicy(getDefault=True,flavour=THREAD_TIME_CONSTRAINT_POLICY)
    return policy.period != default.period #by default this is zero, so not zero means we've changed it
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
    

