# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 18:37:10 2013

@author: Sol
"""

from psychopy import visual, core
from psychopy.iohub import launchHubServer
import string
import random


char_choices=u"ùéèàç^ùèàçé«¼±£¢¤¬¦²³½¾°µ¯­±"+string.ascii_uppercase
def getRandomString(slength):
    s=u''.join(random.choice(char_choices) for i in range(slength))
    ns=u''
    lns=len(ns)
    while lns<slength:
        ns+=s[lns:lns+random.choice([1,3,5,7,9])]+' '
        lns=len(ns)
    return ns[:slength]
    
# create the process that will run in the background polling devices
io=launchHubServer()

# some default devices have been created that can now be used
display = io.devices.display
keyboard = io.devices.keyboard
mouse=io.devices.mouse

# Hide the 'system mouse cursor'.
mouse.setSystemCursorVisibility(False)

# We can use display to find info for the Window creation, like the resolution
# (which means PsychoPy won't warn you that the fullscreen does not match your requested size)
display_resolution=display.getPixelResolution()

# ioHub currently supports the use of a single full-screen PsychoPy Window
window=visual.Window(display_resolution,
                        units='pix',
                        fullscr=True, allowGUI=False,
                        screen=0
                        )

# **** TextBox Setup *****

# Add font search dir. 
#Default is currently the psychopy.visual.textbox.fonts dir
#TextBox.addFontSearchDirectories('font_dir_TBD')

# Create font of a given size and dpi using a ttf file. Label is used
# When creating textBox instance. 

text_length=120
text=getRandomString(text_length)

stime=core.getTime()*1000.0
text_stim=visual.TextBox(window=window,
                         label='textbox1', 
                         font_stim_label='white_40pt', 
                         text=text, 
                         font_file_name='VeraMono.ttf', 
                         font_size=40,
                         dpi=72, 
                         font_color=[1,1,1,1], 
                         font_background_color=None,#[0,0,1,1],
                         line_spacing=None,
                         line_spacing_units=None,
                         border_color=None,#[1,0,0,1],
                         border_stroke_width=2,
                         background_color=None,#[0,1,0,1],
                         grid_color=None,#[0,0,1,.5],
                         grid_stroke_width=None,#1,
                         size=(display_resolution[0]*.9,100),
                         pos=(0.0,0.0), 
                         units='pix',  
                         align_horz='center',
                         align_vert='center',
                         draw_time_buffer_size=30
                         )
etime=core.getTime()*1000.0
print 'TextBox INIT Dur (msec):', etime-stime               

#text_stim.addFontStim(font_stim_label='VeraMono',file_name='VeraMono.ttf',size=42,font_color=[1,0,0,1])

print 'DefaultFontStim:',text_stim.getDefaultFontStim()

stime=core.getTime()*1000.0
message = visual.TextStim(window,pos=(0.0,-(display_resolution[1]/4)),
                    alignHoriz='center',alignVert='center',height=40,
                    text=text,autoLog=False,wrapWidth=display_resolution[0]*.9)
etime=core.getTime()*1000.0
print 'TextStim INIT Dur (msec):', etime-stime               

fixSpot = visual.PatchStim(window,tex="none", mask="gauss",
                    pos=(0,0), size=(30,30),color='black', autoLog=False)
grating = visual.PatchStim(window,pos=(300,0),
                    tex="sin",mask="gauss",
                    color=[1.0,0.5,-1.0],
                    size=(150.0,150.0), sf=(0.01,0.0),
                    autoLog=False)

def updateStimText(stim,text=None):
    stime=core.getTime()*1000.0
    if text:    
        stim.setText(text)
    stim.draw()
    etime=core.getTime()*1000.0 
    return etime-stime

t=getRandomString(text_length)
pyglet_dur=0
textbox_dur=0
fcount=0

io.clearEvents('all')
demo_timeout_start=window.flip()
     
while True:
    grating.setOri(5, '+')
    grating.setPhase(0.05, '+')
    grating.draw()

    fixSpot.draw()

    fcount+=1
    if fcount==1 or fcount%20==0:
        t=getRandomString(text_length)
        pyglet_dur=updateStimText(message,t)
        textbox_dur=updateStimText(text_stim,t)
    else:
        pyglet_dur=updateStimText(message)
        textbox_dur=updateStimText(text_stim)
        
    flip_time=window.flip()#redraw the buffer
    if fcount==1 or fcount%10==0:
        print '---'
        if fcount==1 or fcount%20==0:
            print 'New text:',len(t)
        print 'textbox draw (msec): ',textbox_dur
        print 'pyglet textstim draw (msec): ',pyglet_dur
        
    kb_events=keyboard.getEvents()
    if kb_events:
        break

    if flip_time-demo_timeout_start>300.0:
        print "Ending Demo Due to 30 Seconds of Inactivity."
        break
    
io.quit()
core.quit()