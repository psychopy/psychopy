#!/usr/bin/env python

"""
compImageStimDemo.py

illustrates: 
- taking a snapshot of a static, multi-item screen image (eg, graphics + text),
- saving as a ComplexImageStim for later fast draw (0.12ms regardless of size)
- assessing timing stats for set-up and display
"""
__author__ = 'Jeremy Gray'

from psychopy import visual, event, core

        
def demo(myWin, rect='fullscreen'):
    """
    """
    print "CompImageStim(win, rect=%s)" % repr(rect)
    
    # first compose your still-life screen-shot: as many slow, static stim as you want
    myWin.flip()
    imageStim = visual.SimpleImageStim(myWin, "beach.jpg")
    imageStim.draw()
    imageStim2 = visual.SimpleImageStim(myWin, "face.jpg", pos=(300,20))
    imageStim2.draw()
    wordStim = visual.TextStim(myWin, text='This is a text stim that is kinda verbose and long, so it will take a while to render completely.', pos=(0,-.24))
    wordStim.draw()
    
    myClock = core.Clock()
    t0 = myClock.getTime()
    
    # then grab a screen shot from the back buffer:
    img = visual.CompImageStim(myWin, buffer='back', rect=rect)

    print " one-time costs:\n   set-up time = %.1fms" % (1000.*(myClock.getTime() - t0)), 'to take a screenshot of size =', img.size, 'pix'        
    
    # set up to display the screen-shot, img, plus moving text
    wordsAnim = visual.TextStim(myWin, text='''screenshot() %s\neverything static is a single .draw()\npress any key to continue.''' % (str(img.size)))
    
    frameTimes = []
    drawTimeSingle = [] # accumulate draw times of the ScreenshotStim
    drawTimeMulti = [] # accumulate draw times of the pieces of ScreenshotStim, drawn separately
    frameCounter = 0
    step = .002
    last = myClock.getTime()
    event.clearEvents()
    while True:
        if len(event.getKeys()): break
        # img.draw()
        # myWin.flip()
        # --- the above 3 lines are all you need ---
        
        # just for timing:
        if frameCounter % 2 == 0: 
            t3 = myClock.getTime()        
            
            ## this is the key line--draws the CompImageStim
            img.draw()
            
            drawTimeSingle.append(myClock.getTime() - t3)
        else: # just for timing
            t3 = myClock.getTime()
            imageStim.draw()
            imageStim2.draw()
            wordStim.draw()
            drawTimeMulti.append(myClock.getTime() - t3) # just for timing
        frameCounter += 1
        
        # just more interesting to show something dynamic on the top:
        wordsAnim.draw()
        wordsAnim.pos[1] += step
        if wordsAnim.pos[1] > 0.15 or wordsAnim.pos[1] < -0.15:
            step *= -1
        myWin.flip()
        
        frameTimes.append(myClock.getTime() - last)
        last = myClock.getTime()
    
    # Report timing info:
    ms = map(lambda x:int(0.5+x*1000), frameTimes)
    threshold = 19.5
    droppedFrames = len([m for m in ms[3:] if m > threshold])
    
    first = drawTimeSingle.pop(0)
    multi = 1000.*sum(drawTimeMulti)/len(drawTimeMulti)
    single = 1000.*sum(drawTimeSingle)/len(drawTimeSingle)
    print "   first frame = %.2fms transfer to graphics card" % (1000.*first)
    print " every frame:\n   draw 3 non-PatchStim = %.2fms" % (multi)
    print "   draw 1 compImageStim   = %.2fms, ratio = %.2f x faster, all other frames" % (single, multi/single) 
    print "   frames dropped?    = %d of %d (%.2f%%) > %.1fms, ignoring the first three)" % \
        (droppedFrames, len(ms[3:]), 100.*droppedFrames/len(ms[3:]), threshold) 
    
if __name__== '__main__':
    myWin = visual.Window(fullscr=True, winType='pyglet', units='norm', monitor='testMonitor')
    print
    demo(myWin, rect=[-1,1,1,-1]) # rect controls the edges: Left Top Right Bottom, norm units; here = whole-screen
    print
    demo(myWin, rect=[-.7,.4,.7,-.4]) # no need to be symmetrical; it just works well for the demo
    print
    