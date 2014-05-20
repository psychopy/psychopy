#!/usr/bin/env python2
from psychopy import visual, core, event
import sys

#create a window to draw in
myWin = visual.Window((800.0,800.0),allowGUI=False,
            monitor='testMonitor', units ='cm', winType='pygame')
myWin.recordFrameIntervals = True

if sys.platform=='win32':
    fancy = 'c:\\windows\\fonts\\brush' #this will find brush script
    sans = 'arial' #on windows you can use short names for any system fonts
    serif = 'c:\\windows\\fonts\\timesi.ttf' #times in (genuine) italic
    comic = 'c:\\windows\\fonts\\comic.ttf' #comic
elif sys.platform.startswith('linux'):
    # Note: paths are for Debian-based systems and using the fonts from
    #       ttf-sil-gentium-basic and ttf-dejavu-core from Debian main and
    #       use ttf-mscorefonts-installer from contrib for Comic font
    fancy = '/usr/share/fonts/truetype/ttf-sil-gentium-basic/GenBkBasI.ttf'
    sans = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSans.ttf'
    serif = '/usr/share/fonts/truetype/ttf-dejavu/DejaVuSerif.ttf'
    comic = '/usr/share/fonts/truetype/msttcorefonts/Comic_Sans_MS.ttf'
else:
    #Note that you must have a *.ttf font matching these names/paths
    #You can download ttf fonts free at http://www.webpagepublicity.com/free-fonts.html
    fancy = '/Library/Fonts/Zapfino'
    sans = '/Library/Fonts/Microsoft/Gill Sans MT.ttf'
    serif = '/Library/Fonts/Times New Roman.ttf'
    comic = '/Library/Fonts/Comic Sans MS.ttf'
    
#INITIALISE SOME STIMULI
fpsText = visual.TextStim(myWin, 
                        units='norm',height = 0.1,
                        pos=(-0.98, -0.98), text='starting...',
                        font=sans, 
                        alignHoriz = 'left',alignVert='bottom',
                        color=[+1,-1,-1])
rotating = visual.TextStim(myWin,text="Fonts rotate!",pos=(0, 0),#and can have line breaks
                        color=[-1.0,-1,1],units='deg',
                        ori=0, height = 1.0,
                        font=comic)
unicodeStuff = visual.TextStim(myWin,
                        text = u"unicode (eg \u03A8 \u040A \u03A3)",#you can find the unicode character value from MS Word 'insert symbol'
                        color=-1,  font=serif,pos=(0,3),
                        height = 1)
psychopyTxt = visual.TextStim(myWin, rgb=+1,
                        text = u"PsychoPy \u00A9Jon Peirce",
                        units='norm', height=0.1,
                        pos=[0.95, 0.95], alignHoriz='right',alignVert='top',
                        font=fancy, italic=True) 
                        
trialClock = core.Clock()
t=lastFPSupdate=0;
while not event.getKeys(keyList=['q', 'escape']):
    t=trialClock.getTime()
    
    rotating.ori += 1
    rotating.draw()
    
    unicodeStuff.draw()
    
    if t-lastFPSupdate>1:#update the fps every second
        fpsText.text = "%i fps" %myWin.fps()
        lastFPSupdate+=1
    fpsText.draw()
    psychopyTxt.draw()
    
    #in pygame mouse and key events share one buffer. Need to clear them 
    #in case the large number of mouse events fill the buffer preventing keys to be seen
    event.clearEvents('mouse')#only really needed for pygame windows
    
    myWin.flip()