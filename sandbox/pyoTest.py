import pyo, sys, time
from labjack import u3
d = u3.U3()

soundfile="/Users/jwp/Music/Hourglass.wav"
s = pyo.Server().boot()#sr=44100,nchnls=2, duplex=0)
s.setOutputDevice(2)
s.setBufferSize(128)
s=s.boot()

d.setFIOState(4, 1)
s.start()
sndstim = pyo.SfPlayer(soundfile,speed=1.0,loop=False).out()
time.sleep(2)
print 'got here'
s.stop()

d.setFIOState(4, 0)
time.sleep(.25)
s.shutdown()

