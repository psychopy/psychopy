#!/usr/bin/env python

"""This demo allows for automated testing of the sound latency on your system.
To use it you need a labjack (or adapt for a similar device) and a cable to 
connect the earphones jack to the FIO6 (and GND) pins of the labjack.

(The PsychoPy team would be interested to hear how your measurements go)

"""

import psychopy
from psychopy import visual, core, event, sound
from labjack import u3
import numpy, sys, platform

#setup window (can use for visual pulses)
win = visual.Window([800,800], monitor='testMonitor')
win.setRecordFrameIntervals(False)
stim = visual.PatchStim(win, color=-1, sf=0)

sound.init(rate=44100, buffer=128)
timeWithLabjack=True
maxReps=500

#setup labjack U3
ports = u3.U3()
ports.__del__=ports.close#try to autoclose the ports if script crashes (not working?)

FIO4 = 6004 #use as trigger (to view on scope if desired)
FIO6 = 6006 #use to read in microphone
#get zero value of FIO6
startVal = ports.readRegister(FIO6)
print 'FIO6 is at', startVal

if timeWithLabjack:
    print 'OS\tOSver\taudioAPI\tPsychoPy\trate\tbuffer\tmean\tsd\tmin\tmax'

snd = sound.Sound(1000,secs=0.1)
core.wait(2)#give the system time to settle?
delays=[]
nReps=0
while True:#run the repeats for this sound server
    if event.getKeys('q'):
        core.quit()
    nReps+=1
    #do this repeatedly for timing tests
    ports.writeRegister(FIO4,0)#start low

    #draw black square
    stim.draw()
    win.flip()
    
    if not timeWithLabjack:
        #wait for a key press
        if 'q' in event.waitKeys(): break

    #set to white, flip window and raise level port FIO4
    stim.setColor(1)
    stim.draw()
    win.flip()
    ports.writeRegister(FIO4,1)
    
    timer=core.Clock()
    snd.play()
    
    if timeWithLabjack:
        while ports.readRegister(FIO6)==startVal and timer.getTime()<0.5:
            pass
        if timer.getTime()>0.5:
            print 'failed to detect sound on FIO6 (either inconsistent sound or needs to be louder)'
        t1 = timer.getTime()*1000
        sys.stdout.flush()
        delays.append(t1)
        core.wait(0.5)#ensure sound has finished
    #set color back to black and set FIO4 to low again
    stim.setColor(-1)
    stim.draw()
    win.flip()
    ports.writeRegister(FIO4,0)
    if nReps>=maxReps:
        break

if sys.platform=='darwin':
    sysName = 'OSX'
    sysVer = platform.mac_ver()[0]
elif sys.platform=='win32':
    sysName = 'win'
    sysVer = platform.win32_ver()[0]
elif sys.platform.startswith('linux'):
    sysName = 'linux_'+platform.dist()
    sysVer = platform.release()
else:
    sysName = sysVer = 'n/a'

audioLib = sound.audioLib
if audioLib=='pyo':
    #for pyo we also want the undrelying driver (ASIO, windows etc)
    audioAPI = "%s_%s" %(audioAPI, sound.driver)
    rate = sound.pyoSndServer.getSamplingRate()
    buffer = sound.pyoSndServer.getBufferSize()
else:
    rate=sound.pygame.mixer.get_init()[0]
    buffer=0
    
#print 'OS\tOSver\tPsychoPy\trate\tbuffer\tmean\tsd\tmin\tmax'
if timeWithLabjack:
    print "%s\t%s\t%s\t%s"%(sysName, sysVer, audioLib, psychopy.__version__),
    print "\t%i\t%i" %(rate,buffer),
    print "\t%.3f\t%.3f" %(numpy.mean(delays), numpy.std(delays)),
    print "\t%.3f\t%.3f" %(numpy.min(delays), numpy.max(delays)),
     
import pylab
pylab.plot(delays,'o')
pylab.show()