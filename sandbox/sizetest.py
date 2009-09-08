from psychopy import visual, core

StimVSize = 8
mywin = visual.Window([600,600], monitor="testMonitor", rgb=1, units="deg", allowGUI=False)
stimDeg = visual.TextStim(win=mywin, font='Courier Bold', rgb=[1,-1,-1], units="deg", pos=(0,4), opacity=0.5, height=StimVSize)
print stimDeg.heightPix, stimDeg._posRendered
stimCm =  visual.TextStim(win=mywin, font='Courier Bold', rgb=[-1,1,1], units="cm", pos=(0,4), opacity=0.5, height=StimVSize)
print stimCm.heightPix, stimCm._posRendered


stim = "jrk"
stimDeg.setText(stim)
stimCm.setText(stim)

stimDeg.draw()
stimCm.draw() 
mywin.getMovieFrame(buffer='back')

mywin.flip()
#mywin.saveMovieFrames('DegVsCm.png')
core.wait(5)

