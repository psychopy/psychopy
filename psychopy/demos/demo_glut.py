#! /usr/local/bin/python2.5
from psychopy import visual, core

def main():
    #create a window to draw in
    myWin = visual.Window((600.0,600.0),fullscr=0,rgb=(0.5,0.5,0.6),winType="glut")

    #INITIALISE SOME STIMULI

    grating = visual.PatchStim(myWin,pos=(0,0.0),
                        tex="sin", texRes=256,
                        mask='circle',
                        rgb=[1.0,1.0,1.0],
                        size=(0.5,0.5), sf=(2.0,0), phase=(315.0/360.0,0),
                        ori=45)

    trialClock = core.Clock()#make a timer for the trial
    frameClock = core.Clock()#and another to check the time each frame
    def updateStims():
        if trialClock.getTime()>60:# run for a minute
            core.quit()
        delta = frameClock.getTime(); frameClock.reset()
        grating.setOri(delta*60,'+')
        grating.draw()
        myWin.update()

    def mousePress(button,state,x,y):
        if state:
            print x,',',y
            print myWin.fps()
            
    def keyPress(key,mousex,mousey):
        if key is "f":
            myWin.fullScr()
        if key is "q":
            myWin.close()
            return()

    visual.GLUT.glutMouseFunc(mousePress)
    visual.GLUT.glutKeyboardFunc(keyPress)
    myWin.whenIdle(updateStims)
    myWin.go()

main()