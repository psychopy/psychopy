#! /usr/local/bin/python2.5
from psychopy import *
import sys

#create a window to draw in
myWin = visual.Window((600.0,600.0),allowGUI=False,
				monitor='testMonitor', units ='cm', winType='pygame')
    
if sys.platform=='win32':
    fancy = 'c:\\windows\\fonts\\brush' #this will find brush script
    sans = 'arial' #on windows you can use short names for any system fonts
    serif = 'c:\\windows\\fonts\\timesi.ttf' #times in (genuine) italic
    comic = 'c:\\windows\\fonts\\comic.ttf' #comic
else:
    #Note that you must have a *.ttf font matching these names/paths
    #You can download ttf fonts free at http://www.webpagepublicity.com/free-fonts.html
    fancy = '/Library/Fonts/Tolkien Regular.ttf'
    sans = 'blah'#invalid name will use default font
    serif = '/Library/Fonts/Palatino*'
    comic = '/Library/Fonts/Comic Sans MS.ttf'
    
#INITIALISE SOME STIMULI
fpsText = visual.TextStim(myWin, 
                        units='norm',height = 0.2,
                        pos=(-0.98, -0.98), text='starting...',
                        font=sans, 
                        alignHoriz = 'left',alignVert='bottom',
                        rgb=[+1,-1,-1])
rotating = visual.TextStim(myWin,text="Fonts rotate!",pos=(0, 0),
                        rgb=[-1.0,-1,1],
                        ori=0, height = 1,
                        font=comic,
                        alignHoriz='left',alignVert='bottom')
rotating = visual.TextStim(myWin,text="Fonts rotate!",pos=(0, 0),
                        rgb=[-1.0,-1,1],
                        ori=0, height = 1,
                        font=comic,
                        alignHoriz='left',alignVert='bottom')
unicodeStuff = visual.TextStim(myWin,
                        text = u"unicode (eg \u03A8 \u040A \u03A3)",#you can find the unicode character value from MS Word 'insert symbol'
                        italic=True, #use (fake) italics for whole string
                        rgb=-1,  font=serif,
                        height = 1.5)
psychopyTxt = visual.TextStim(myWin, 
                        text = u"PsychoPy \u00A9Jon Peirce",
                        units='norm', height=0.1,
                        pos=[0.95, 0.95], alignHoriz='right',alignVert='top',
                        font=fancy) #this won't exist but will be replaced with a default
trialClock = core.Clock()
t=lastFPSupdate=0;
while t<20:#quits after 20 secs
    t=trialClock.getTime()
    
    rotating.setOri(0.1,"+")
    rotating.draw()
    
    unicodeStuff.draw()
    
    if t-lastFPSupdate>1:#update the fps every second
        fpsText.setText("%i fps" %myWin.fps())
        lastFPSupdate+=1
    fpsText.draw()
    psychopyTxt.draw()
    
    myWin.flip()

