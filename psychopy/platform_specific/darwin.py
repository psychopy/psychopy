# Part of the PsychoPy library
# Copyright (C) 2015 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, time
from psychopy import logging
try:
    import ctypes, ctypes.util
    importCtypesFailed = False
except:
    importCtypesFailed = True
    logging.debug("rush() not available because import ctypes failed in contrib/darwin.py")

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
thread_flavor_t = ctypes.c_int32 #in mach_types.defs
thread_info_t = integer_t * 12 #in mach_types.defs
thread_policy_flavor_t = natural_t #in mach_types.defs
thread_policy_t = integer_t * 16 #in mach_types.defs
#for use with sysctl()
CTL_HW=ctypes.c_int(6) #/* generic cpu/io */
HW_BUS_FREQ=ctypes.c_int(14)

cocoa = ctypes.cdll.LoadLibrary(ctypes.util.find_library("Cocoa"))#could use carbon instead?
#mach = ctypes.cdll.LoadLibrary(ctypes.util.find_library("libm"))#not needed - all the functions seem to be in cocoa
#ogl = ctypes.cdll.LoadLibrary(ctypes.util.find_library("OpenGL"))#not needed - all the functions seem to be in cocoa

def _create_cfstring(text):#some string parameters need to be converted to SFStrings
    if importCtypesFailed: return False

    return cocoa.CFStringCreateWithCString(ctypes.c_void_p(),
                                            text.encode('utf8'),
                                            kCFStringEncodingUTF8)
if importCtypesFailed == False:
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
    if importCtypesFailed: return False

    mib = (ctypes.c_int*2)(CTL_HW, HW_BUS_FREQ)
    val = ctypes.c_int()
    intSize = ctypes.c_int(ctypes.sizeof(val))
    cocoa.sysctl(ctypes.byref(mib), 2, ctypes.byref(val), ctypes.byref(intSize), 0, 0)
    return val.value

def rush(value=True, realtime = False):
    """Raise the priority of the current thread/process
    Win32 and OS X only so far - on linux use os.nice(niceIncrement)

    Set with rush(True) or rush(False).

    realtime arg is not used by osx implementation.

    Beware and don't take priority until after debugging your code
    and ensuring you have a way out (e.g. an escape sequence of
    keys within the display loop). Otherwise you could end up locked
    out and having to reboot!
    """
    if importCtypesFailed: return False

    if value:
        bus = getBusFreq()
        extendedPolicy=_timeConstraintThreadPolicy()
        extendedPolicy.period=bus/160 #number of cycles in hz (make higher than frame rate)
        extendedPolicy.computation=bus/320#half of that period
        extendedPolicy.constrain= bus/640#max period that they should be carried out in
        extendedPolicy.preemptible=1
        extendedPolicy=getThreadPolicy(getDefault=True, flavour=THREAD_TIME_CONSTRAINT_POLICY)
        err=cocoa.thread_policy_set(cocoa.mach_thread_self(), THREAD_TIME_CONSTRAINT_POLICY,
            ctypes.byref(extendedPolicy), #send the address of the struct
            THREAD_TIME_CONSTRAINT_POLICY_COUNT)
        if err!=KERN_SUCCESS:
            logging.error('Failed to set darwin thread policy, with thread_policy_set')
        else:
            logging.info('Successfully set darwin thread to realtime')
    else:
        #revert to default policy
        extendedPolicy=getThreadPolicy(getDefault=True, flavour=THREAD_STANDARD_POLICY)
        err=cocoa.thread_policy_set(cocoa.mach_thread_self(), THREAD_STANDARD_POLICY,
            ctypes.byref(extendedPolicy), #send the address of the struct
            THREAD_STANDARD_POLICY_COUNT)
    return True

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
    if importCtypesFailed: return False

    extendedPolicy=_timeConstraintThreadPolicy()#to store the infos
    getDefault=ctypes.c_int(getDefault)#we want to retrive actual policy or the default
    err=cocoa.thread_policy_get(cocoa.mach_thread_self(), THREAD_TIME_CONSTRAINT_POLICY,
        ctypes.byref(extendedPolicy), #send the address of the policy struct
        ctypes.byref(THREAD_TIME_CONSTRAINT_POLICY_COUNT),
        ctypes.byref(getDefault))
    return extendedPolicy
def getRush():
    """Determine whether or not we are in rush mode. Returns True/False"""
    if importCtypesFailed: return None
    policy = getThreadPolicy(getDefault=False,flavour=THREAD_TIME_CONSTRAINT_POLICY)
    default = getThreadPolicy(getDefault=True,flavour=THREAD_TIME_CONSTRAINT_POLICY)
    return policy.period != default.period #by default this is zero, so not zero means we've changed it
def getScreens():
    """Get a list of display IDs from cocoa"""
    if importCtypesFailed: return False

    count = CGDisplayCount()
    cocoa.CGGetActiveDisplayList(0, None, ctypes.byref(count))
    displays = (CGDirectDisplayID * count.value)()
    cocoa.CGGetActiveDisplayList(count.value, displays, ctypes.byref(count))
    return [id for id in displays]
def getRefreshRate(screen=0):
    """Return the refresh rate of the given screen (typically screen is 0 or 1)

    NB. If two screens are connected with different refresh rates then the rate at which we
    draw may not reflect the refresh rate of the monitor, because
    """
    if importCtypesFailed: return False

    screens=getScreens()
    if screen>(len(screens)-1):
        raise IndexError, "Requested refresh rate of screen %i, but only %i screens were found" %(screen, len(screens))
    else:
        scrID=getScreens()[screen]
    mode = cocoa.CGDisplayCurrentMode(scrID)
    refreshCF = cocoa.CFDictionaryGetValue(mode, _create_cfstring('RefreshRate'))
    refresh = ctypes.c_long()
    cocoa.CFNumberGetValue(refreshCF, kCFNumberLongType, ctypes.byref(refresh))
    if refresh.value==0:
        return 60#probably an LCD
    else:
        return refresh.value


def getScreenSizePix(screen=0):
    """Return the height and width (in pixels) of the given screen (typically screen is 0 or 1)
    If no screen is given then screen 0 is used.

    h,w = getScreenSizePix()
    """

    if importCtypesFailed: return False
    screens=getScreens()
    if screen>(len(screens)-1):
        raise IndexError, "Requested refresh rate of screen %i, but only %i screens were found" %(screen, len(screens))
    else:
        scrID=getScreens()[screen]
    h = cocoa.CGDisplayPixelsHigh(scrID)
    w = cocoa.CGDisplayPixelsWide(scrID)
    return [h,w]

def waitForVBL(screen=0,nFrames=1):
    """DEPRECATED: the code for doing this is now smaller and cross-platform so
    is included in visual.Window.flip()

    This version is based on detecting the display beam position. It may give
    unpredictable results for an LCD.
    """
    if importCtypesFailed: return False

    screens=getScreens()
    if screen>(len(screens)-1):
        raise IndexError, "Requested refresh rate of screen %i, but only %i screens were found" %(screen, len(screens))
    else:
        scrID=getScreens()[screen]
    framePeriod=1.0/getRefreshRate(screen)
    if screen>0: #got multiple screens, check if they have same rate
        mainFramePeriod = 1.0/getRefreshRate(0)
        if mainFramePeriod!=framePeriod:
            #CGDisplayBeamPosition is unpredictable in this case - usually synced to the first monitor, but maybe better if 2 gfx cards?
            logging.warning("You are trying to wait for blanking on a secondary monitor that has a different \
refresh rate to your primary monitor. This is not recommended (likely to reduce your frame rate to the primary monitor).")
    #when we're in a VBL the current beam position is greater than the screen height (for up to ~30 lines)
    top=getScreenSizePix(screen)[0]
    if cocoa.CGDisplayBeamPosition(scrID)>top:
        nFrames+=1#we're in a VBL already, wait for one more
    while nFrames>0:
        beamPos =  cocoa.CGDisplayBeamPosition(scrID)#get current pos
        #choose how long to wait
        while framePeriod*(top-beamPos)/top > 0.005:#we have at least 5ms to go so can wait for 1ms
#            print 'plenty', beamPos, framePeriod*(top-beamPos)/top, time.time()
#            time.sleep(0.0001)#actually it seems that time.sleep() waits too long on os x
            beamPos =  cocoa.CGDisplayBeamPosition(scrID)#get current pos
        #now near top so poll continuously
        while beamPos<top:
            beamPos =  cocoa.CGDisplayBeamPosition(scrID)#get current pos
        #if this was not the last frame, then wait until start of next frame before continuing
        #so that we don't detect the VBL again. If this was the last frame then get back to script asap
        if nFrames>1:
            while beamPos>=top:
                beamPos =  cocoa.CGDisplayBeamPosition(scrID)
        nFrames-=1

def sendStayAwake():
    """Sends a signal to your system to indicate that the computer is in use and
    should not sleep. This should be sent periodically, but PsychoPy will send
    the signal by default on each screen refresh.
    Added: v1.79.00

    Currently supported on: windows, OS X
    """
    cocoa.UpdateSystemActivity(0)

#beamPos =  cocoa.CGDisplayBeamPosition(1)
#while beamPos<=1000:
#        beamPos =  cocoa.CGDisplayBeamPosition(1)
#        print beamPos
#first=last=time.time()
#print getRefreshRate(1)
#for nFrames in range(20):
#    waitForVBL(1, nFrames=1)
#    time.sleep(0.005)
#    this=time.time()
#    print this-first, this-last, 1/(this-last)
#    last=this
#rush()
