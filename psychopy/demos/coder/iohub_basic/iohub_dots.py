"""
iohub
.. file: iohub/examples/dots/run.py

------------------------------------------------------------------------------------------------------------------------

dots
++++

Overview:
---------

This script is a copy of the PsychoPy 'dots' demo with
ioHub integration.
"""
from psychopy import visual, core
from psychopy.iohub import Computer, quickStartHubServer, FullScreenWindow

DOT_COUNT=1000

# Example where ioHub does not use yaml config files specified by user.

import random
io=quickStartHubServer(experiment_code="exp_code",session_code="s%d"%(random.randint(1,1000000)))

# By default, keyboard, mouse, and display devices are created if you
# do not pass any config info to the ioHubConnection class above.
display=io.devices.display
keyboard=io.devices.keyboard

# Create a psychopy window, full screen resolution, full screen mode, pix units,
# with no boarder, using the monitor default profile name used by ioHub,
# which is created on the fly right now by the script. (ioHubDefault)
myWin= FullScreenWindow(display)

coord_type=display.getCoordinateType()

#INITIALISE SOME STIMULI
dotPatch =visual.DotStim(myWin,
                        color=(1.0,1.0,1.0),
                        dir=270,
                        nDots=DOT_COUNT,
                        fieldShape='circle',
                        fieldPos=(0.0,0.0),
                        fieldSize=display.getPixelResolution(),
                        dotLife=5, #number of frames for each dot to be drawn
                        signalDots='same', #are the signal dots the 'same' on each frame? (see Scase et al)
                        noiseDots='direction', #do the noise dots follow random- 'walk', 'direction', or 'position'
                        speed=3.0,
                        coherence=90.0,
                        units=coord_type
                        )

message =visual.TextStim(myWin,
                         text='Hit Q to quit',
                         pos=(0,-0.5),
                         units=coord_type
                         )

Computer.enableHighPriority(disable_gc=False)

io.clearEvents('all')

dur=5*60
endTime=Computer.currentTime()+dur
fcounter=0
reportedRefreshInterval=display.getRetraceInterval()
print 'Screen has a reported refresh interval of ',reportedRefreshInterval

dotPatch.draw()
message.draw()
[myWin.flip() for i in range(10)]
lastFlipTime=Computer.getTime()
myWin.fps()
exit=False

myWin.setRecordFrameIntervals(True)

while not exit and endTime>Computer.currentTime():
    dotPatch.draw()
    message.draw()
    myWin.flip()#redraw the buffer
    flipTime=Computer.getTime()
    IFI=flipTime-lastFlipTime
    lastFlipTime=flipTime
    fcounter+=1

    if IFI > reportedRefreshInterval*1.5:
        print "Frame {0} dropped: IFI of {1}".format(fcounter,IFI)

    #handle key presses each frame
    for event in keyboard.getEvents():
        if event.key in ['ESCAPE','Q','q']:
            exit=True
            break

Computer.disableHighPriority()
myWin.close()

io.quit()### End of experiment logic

core.quit()