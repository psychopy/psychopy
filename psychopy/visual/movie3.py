import pysoundfile as sndfile
import pysoundcard as sndcard
import time
import sys

#print 'sndcard:', dir(sndcard)
#print 'sndfile:', dir(sndfile)
for dev in sndcard.devices():
    print dev['name']
print 'default device:', sndcard.default_output_device
print 'apis', list(sndcard.apis())

snd = sndfile.SoundFile('audiocheck.net_sweep20-20klin.wav')
#print 'snd:', dir(snd)
sndArr = snd[:100000] #this is a numpy array
print sndArr.shape
block_length = 512
print snd.channels
print snd.format
global timeList
timeList = []

soundPos = 0
def callback(out_data, block_length, time_info, status):
    global soundPos
    out_data[:] = sndArr[soundPos:soundPos+block_length]
    soundPos += block_length
    return (out_data, 0)

try:#changed at some point in pysoundcard (older version on ubuntu?)
    rate = snd.sample_rate
except:
    rate = snd.samplerate

if False: #callback method
    s = sndcard.Stream(sample_rate=44100, block_length=block_length, callback=callback)
    s.start()
    time.sleep(2)
    t0=time.time()
    while time.time()-t0 < 0.1:
        pass
    time.sleep(1)
    s.stop()
else: #read/write method
    s = sndcard.Stream(sample_rate=44100, block_length=block_length)
    s.start()
    s.write(sndArr)
    print 'here'
    sys.stdout.flush()
    time.sleep(2)
    t0=time.time()
    while time.time()-t0 < 0.1:
        pass
    s.stop()

