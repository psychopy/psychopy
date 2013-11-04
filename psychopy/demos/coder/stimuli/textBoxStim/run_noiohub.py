# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 18:37:10 2013

@author: Sol
"""

from psychopy import visual, core,event
import string
import random
from psychopy.iohub.util import NumPyRingBuffer

textstim_txt_change_draw_times=NumPyRingBuffer(6000)
textstim_no_change_draw_times=NumPyRingBuffer(6000)
textbox_txt_change_draw_times=NumPyRingBuffer(6000)
textbox_no_change_draw_times=NumPyRingBuffer(6000)

char_choices=u"ùéèàç^ùèàçé«¼±£¢¤¬¦²³½¾°µ¯­±√∞≤≥±≠"+string.ascii_uppercase[:15]
def getRandomString(slength):
    s=u''.join(random.choice(char_choices) for i in range(slength))
    ns=u''
    lns=len(ns)
    while lns<slength:
        ns+=s[lns:lns+random.choice([1,3,5,7,9])]+' '
        lns=len(ns)
    return ns[:slength]
    
display_resolution=1920,1080
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

text_length=10
chng_txt_each_flips=5
max_flip_count=60*60*2
text=getRandomString(text_length)

stime=core.getTime()*1000.0
textbox=visual.TextBox(window=window,
                         label='textbox1', 
                         font_stim_label='white_40pt', 
                         text=text, 
                         font_file_name='VeraMono.ttf', 
                         font_size=40,
                         dpi=72, 
                         font_color=[1,0,1,0.5], 
                         font_background_color=None,#[0,0,1,1],
                         line_spacing=None,
                         line_spacing_units=None,
                         border_color=None,#[1,0,0,1],
                         border_stroke_width=2,
                         background_color=None,#[0.25,0.25,0.25,1],
                         grid_color=None,#[0,0,1,.5],
                         grid_stroke_width=None,#1,
                         size=(display_resolution[0]*.2,50),
                         pos=(0.0,0.0), 
                         units='pix',  
                         align_horz='center',
                         align_vert='center',
                         draw_time_buffer_size=30
                         )
textbox.draw()
etime=core.getTime()*1000.0
textbox_init_dur=etime-stime

#textbox.addFontStim(font_stim_label='VeraMono',file_name='VeraMono.ttf',size=42,font_color=[1,0,0,1])
#print 'DefaultFontStim:',textbox.getDefaultFontStim()

stime=core.getTime()*1000.0
textstim = visual.TextStim(window,pos=(0.0,-(display_resolution[1]/4)),
                    alignHoriz='center',alignVert='center',height=40,
                    text=text,autoLog=False,wrapWidth=display_resolution[0]*.2)
textstim.draw()
etime=core.getTime()*1000.0
textstim_init_dur=etime-stime

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

event.clearEvents()
demo_timeout_start=window.flip()
     
while True:
    grating.setOri(5, '+')
    grating.setPhase(0.05, '+')
    grating.draw()

    fixSpot.draw()

    if fcount==0 or fcount%chng_txt_each_flips==0:
        t=getRandomString(text_length)
        pyglet_dur=updateStimText(textstim,t)
        textbox_dur=updateStimText(textbox,t)
        textstim_txt_change_draw_times.append(pyglet_dur)
        textbox_txt_change_draw_times.append(textbox_dur)
    else:
        pyglet_dur=updateStimText(textstim)
        textbox_dur=updateStimText(textbox)
        textstim_no_change_draw_times.append(pyglet_dur)
        textbox_no_change_draw_times.append(textbox_dur)
        
    flip_time=window.flip()#redraw the buffer
    fcount+=1

    kb_events=event.getKeys()
    if kb_events:
        break

    if fcount>=max_flip_count or flip_time-demo_timeout_start>300.0:
        print "Ending Demo Due to 30 Seconds of Inactivity."
        break
print
print '-------Text Draw Duration Test---------'
print
print '+ Text Stim Char Length:\t',text_length
print '+ TextBox INIT Dur (secs):\t%.3f'%(textbox_init_dur/1000.0)
print '+ TextStim INIT Dur (secs):\t%.3f'%(textstim_init_dur/1000.0)
print '+ Text Change Flip Perc:\t%.2f'%((1.0/chng_txt_each_flips)*100.0),r'%'
print
print '+ Total Flip Count:\t\t',fcount
print '+ Test Duration (secs):\t\t%.3f'%(flip_time-demo_timeout_start)
print '+ FPS:\t\t\t\t%.3f'%(float(fcount)/(flip_time-demo_timeout_start))
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