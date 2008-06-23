import sys, ctypes, ctypes.util

def syncSwapBuffers(n):
    """syncSwapBuffers(n)
    if n==1 then buffers will sync, otherwise sync will bee turned off"""
    try:
        ogl = ctypes.cdll.LoadLibrary(ctypes.util.find_library("OpenGL"))
        # set v to 1 to enable vsync, 0 to disable vsync
        v = ctypes.c_int(n)
        kCGLCPSwapInterval= 222#this is the parameter index?!
        ogl.CGLSetParameter(ogl.CGLGetCurrentContext(), ctypes.c_int(kCGLCPSwapInterval), ctypes.pointer(v))
    except:
        print "Unable to set vsync mode. Using driver defaults"