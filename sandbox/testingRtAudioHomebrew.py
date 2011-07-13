import ctypes, ctypes.util
#rtLib = ctypes.cdll.LoadLibrary("/Users/jwp/Downloads/rtaudio-4.0.7/librtaudio.dylib")
rtLib = ctypes.cdll.LoadLibrary("/usr/local/lib/librtaudio.dylib")

rta = rtLib.RtAudio()

print rta.getDeviceCount