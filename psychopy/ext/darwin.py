try: 
    import _darwin #simply import eveything from the c extension
except: 
    print "Didn't find module _darwin. That's normal during install."

def syncSwapBuffers(n):
    """syncSwapBuffers(n)
    if n==1 then buffers will sync, otherwise sync will bee turned off"""
    _darwin.syncSwapBuffers(n)
    return 1