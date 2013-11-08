# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 18:37:10 2013

@author: Sol
"""
import string
import random
from psychopy import visual, core, event
from psychopy.iohub.util import NumPyRingBuffer

# Variables to control text string length etc.
text_length=30
chng_txt_each_flips=5
max_flip_count=60*60*2
display_resolution=1920,1080
textbox_width=display_resolution[0]*.8
textbox_height=200

# Circular buffers to store timing measures
textstim_txt_change_draw_times=NumPyRingBuffer(6000)
textstim_no_change_draw_times=NumPyRingBuffer(6000)
textbox_txt_change_draw_times=NumPyRingBuffer(6000)
textbox_no_change_draw_times=NumPyRingBuffer(6000)

# Some utility functions >>>
#
char_choices=u"ùéèàç^ùèàçé«¼±£¢¤¬¦²³½¾°µ¯­±√∞≤≥±≠"+string.ascii_uppercase[:15]
def getRandomString(slength):
    s=u''.join(random.choice(char_choices) for i in range(slength))
    ns=u''
    lns=len(ns)
    while lns<slength:
        ns+=s[lns:lns+random.choice([1,3,5,7,9])]+' '
        lns=len(ns)
    return ns[:slength]
    
text=getRandomString(text_length)

def updateStimText(stim,text=None):
    stime=core.getTime()*1000.0
    if text:    
        stim.setText(text)
    stim.draw()
    etime=core.getTime()*1000.0 
    return etime-stime
#
# <<<<<

# Create PsychoPy Window and various visual stim, 
# including a TextStim and two Textbox stim.    

# Create Window
window=visual.Window(display_resolution,
                        units='pix',
                        fullscr=True, allowGUI=False,
                        screen=0
                        )

# Create a TextBox stim, defining the text style to use for the stim
# by passing arguements to the TextBox init.
# We also time how long it takes to create the stim and 
# perform the first stim draw() call.
#
stime=core.getTime()*1000.0                                    
textbox=visual.TextBox(window=window,
                         text_style_label='white_40pt', 
                         text=text, 
                         font_file_name='VeraMono.ttf', 
                         font_size=36,
                         dpi=72, 
                         font_color=[0,255,0,255], 
                         background_color=None,#[128,32,192,255],
                         border_color=None,#[0,255,0,64],
                         border_stroke_width=2,
                         grid_color=None,#[255,255,0,255],
                         grid_stroke_width=1,
                         size=(0.8,.1),
                         pos=(0.0,0.0), 
                         units='norm',
                         grid_horz_justification='center',
                         grid_vert_justification='center',
                         color_space='rgb255'
                         )
textbox.draw()
etime=core.getTime()*1000.0
textbox_init_dur=etime-stime

# Create a TextStim stim, using the default font.
# We also time how long it takes to create the stim and 
# perform the first stim draw() call.
#
stime=core.getTime()*1000.0
textstim = visual.TextStim(window,pos=(0.0,-(display_resolution[1]/4)),
                    alignHoriz='center',alignVert='center',height=40,
                    text=text,autoLog=False,wrapWidth=textbox_width)
textstim.draw()
etime=core.getTime()*1000.0
textstim_init_dur=etime-stime

# Create some other non text psychopy stim.
#
fixSpot = visual.PatchStim(window,tex="none", mask="gauss",
                    pos=(0,0), size=(30,30),color='black', autoLog=False)
fixSpot.draw()

lgrating = visual.PatchStim(window,pos=(-300,0),
                    tex="sin",mask="gauss",
                    color=[-1.0,0.5,1.0],
                    size=(150.0,150.0), sf=(0.01,0.0),
                    autoLog=False)
lgrating.draw()

rgrating = visual.PatchStim(window,pos=(300,0),
                    tex="sin",mask="gauss",
                    color=[1.0,0.5,-1.0],
                    size=(150.0,150.0), sf=(0.01,0.0),
                    autoLog=False)
rgrating.draw()

# Do the first stim display and start into the testing loop.
#
demo_start=window.flip()     
event.clearEvents()
fcount=0
while True:
    lgrating.setOri(5, '+')
    lgrating.setPhase(0.05, '+')
    lgrating.draw()
    fixSpot.draw()

    # For the textBox and TextStim resources, change the text every
    # chng_txt_each_flips, and record the time it takes to update the text
    # and redraw() each resource type.
    #
    if fcount==0 or fcount%chng_txt_each_flips==0:
        t=getRandomString(text_length)
        textbox_dur=updateStimText(textbox,t)
        textbox_txt_change_draw_times.append(textbox_dur)
        pyglet_dur=updateStimText(textstim,t)
        textstim_txt_change_draw_times.append(pyglet_dur)
    else:
        textbox_dur=updateStimText(textbox)
        textbox_no_change_draw_times.append(textbox_dur)
        pyglet_dur=updateStimText(textstim)
        textstim_no_change_draw_times.append(pyglet_dur)
    
    rgrating.setOri(5, '+')
    rgrating.setPhase(0.05, '+')
    rgrating.draw()
        
    # Update the display to show stim changes
    flip_time=window.flip()
    fcount+=1

    # End the test when a keyboard event is detected or when max_flip_count
    # win.flip() calls have been made.
    #
    kb_events=event.getKeys()
    if kb_events:
        break
    if fcount>=max_flip_count:
        break

# Print a comparision of the TextBox and TextStim performance.
#
print
print '-------Text Draw Duration Test---------'
print
print '+ Text Stim Char Length:\t',text_length
print '+ TextBox INIT Dur (secs):\t%.3f'%(textbox_init_dur/1000.0)
print '+ TextStim INIT Dur (secs):\t%.3f'%(textstim_init_dur/1000.0)
print '+ Text Change Flip Perc:\t%.2f'%((1.0/chng_txt_each_flips)*100.0),r'%'
print
print '+ Total Flip Count:\t\t',fcount
print '+ Test Duration (secs):\t\t%.3f'%(flip_time-demo_start)
print '+ FPS:\t\t\t\t%.3f'%(float(fcount)/(flip_time-demo_start))
print
print '+ Average Draw Call Durations (msec):'
print
print 'Text Object\tNo Txt Change\tTxt Change'
print
print '%s\t\t%.3f\t\t%.3f'%(textbox.__class__.__name__,
    textbox_no_change_draw_times.mean(),textbox_txt_change_draw_times.mean())
print '%s\t%.3f\t\t%.3f'%(textstim.__class__.__name__,
    textstim_no_change_draw_times.mean(),textstim_txt_change_draw_times.mean())
print
print '+ TextStim / TextBox Draw Time Ratio:'
print
print '\tNo Txt Change\tTxt Change'
print
print 'Ratio\t%.3f\t\t%.3f'%(textstim_no_change_draw_times.mean()/textbox_no_change_draw_times.mean(),
    textstim_txt_change_draw_times.mean()/textbox_txt_change_draw_times.mean())
print
print '---------------------------------------'

window.getMovieFrame()
window.saveMovieFrames('text_test_%d.png'%(text_length))
kb_events=event.waitKeys()

core.quit()