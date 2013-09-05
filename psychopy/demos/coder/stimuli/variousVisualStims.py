from psychopy import visual, event, core
import numpy

win = visual.Window([600,600], rgb=-1)
gabor = visual.GratingStim(win, mask='gauss', pos=[-0.5,-0.5], color=[0,0,1],sf=5, ori=30)
movie = visual.MovieStim(win, 'jwpIntro.mov', units='pix',pos=[100,100],size=[160,120])
text = visual.TextStim(win, pos=[0.5,-0.5],text=u"unicode (eg \u03A8 \u040A \u03A3)", font=['Times New Roman'])
faceRGB = visual.ImageStim(win,image='face.jpg',pos=[-0.5,0.5])
fixSpot = visual.GratingStim(win,tex=None, mask="gauss", size=(0.05,0.05),color='white')
myMouse=event.Mouse(win=win)

t=0.0
while True:
    #get mouse events
    mouse_dX,mouse_dY = myMouse.getRel()
    mouse1, mouse2, mouse3 = myMouse.getPressed()
    if (mouse1):
        gabor.setOri(mouse_dY/10.0, '-')
        text.setOri(mouse_dY/10.0, '+')
        faceRGB.setOri(mouse_dY/10.0, '+')
        movie.setOri(mouse_dY/10.0, '-')
        
    t+=1/60.0
    gabor.setPhase(t*2.0)
    gabor.draw()
    text.setColor([numpy.sin(t), 0, 1])
    text.draw()
    fixSpot.draw()
    faceRGB.draw()
    movie.draw()
    
    win.flip()
    
