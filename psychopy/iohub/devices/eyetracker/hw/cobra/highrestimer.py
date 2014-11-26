import sys

if sys.platform == 'win32':
    global _fcounter, _qpfreq, _winQPC
    from ctypes import byref, c_int64, windll
    _fcounter = c_int64()
    _qpfreq = c_int64()
    windll.Kernel32.QueryPerformanceFrequency(byref(_qpfreq))
    _qpfreq=float(_qpfreq.value)
    _winQPC=windll.Kernel32.QueryPerformanceCounter

    def getTime():
        _winQPC(byref(_fcounter))
        return  _fcounter.value/_qpfreq
else:
    raise RuntimeError("Only Windows OS is supported")
    #cur_pyver = sys.version_info
    #if cur_pyver[0]==2 and cur_pyver[1]<=6:
    #    getTime = time.time
    #else:
    #    import timeit
    #    getTime = timeit.default_timer