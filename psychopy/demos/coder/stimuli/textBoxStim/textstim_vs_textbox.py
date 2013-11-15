# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 18:37:10 2013

@author: Sol
"""
import string,os
import random
from psychopy import visual, core, event
from psychopy.iohub.util import NumPyRingBuffer
import pyglet.gl as gl

# Variables to control text string length etc.
text_length=160
chng_txt_each_flips=5
max_flip_count=60*60*2
display_resolution=1920,1080

# Circular buffers to store timing measures
stim1_txt_change_draw_times=NumPyRingBuffer(6000)
stim1_no_change_draw_times=NumPyRingBuffer(6000)
stim2_txt_change_draw_times=NumPyRingBuffer(6000)
stim2_no_change_draw_times=NumPyRingBuffer(6000)

# Some utility functions >>>
#
char_choices=string.ascii_uppercase+u"ùéèàç^ùèàçé«¼±£¢¤¬¦²³½¾°µ¯­±√∞≤≥±≠"
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
    gl.glFinish()
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


fm=visual.textbox.getFontManager()
available_font_names=fm.getFontFamilyStyles()
prefered_fonts=[fn for fn,fs in available_font_names if fn in [
                                                            'Courier New',
                                                            'Consolas',
                                                            'Lucida Sans Typewriter',
                                                            'Ubuntu Mono',
                                                            'DejaVu Sans Mono',
                                                            'Bitstream Vera Sans Mono',
                                                            'Luxi Mono']]
if prefered_fonts:
    font_name=prefered_fonts[0]
else:
    font_name=available_font_names[0][0]
bold=False
italic=False

stime=core.getTime()*1000.0                                    
textbox=visual.TextBox(window=window,
                         text=text, 
                         font_name=font_name,
                         bold=bold,
                         italic=italic,
                         font_size=32,
                         font_color=[0,0,0], 
                         #background_color=[128,32,192,255],
                         dpi=72,
                         #border_color=[0,255,0,64],
                         #border_stroke_width=2,
                         #grid_color=[255,255,0,255],
                         #grid_stroke_width=1,
                         size=(1.6,.25),
                         pos=(0.0,.25), 
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
                    text=text,autoLog=False,wrapWidth=display_resolution[0]*0.8)
textstim.draw()
etime=core.getTime()*1000.0
textstim_init_dur=etime-stime


# Do the first stim display and start into the testing loop.
#


#stim_draw_orders=[[textstim,textbox],[textbox,textstim]]
stim_draw_orders=[[textstim,textbox],]
for stim1, stim2 in stim_draw_orders:
    stim1_txt_change_draw_times.clear()    
    stim2_txt_change_draw_times.clear()    
    stim1_no_change_draw_times.clear()    
    stim2_no_change_draw_times.clear()    
    demo_start=window.flip()     
    event.clearEvents()
    fcount=0
    while True:
        # For the textBox and TextStim resources, change the text every
        # chng_txt_each_flips, and record the time it takes to update the text
        # and redraw() each resource type.
        #
    
        # Make sure timing of stim is for the time taken for that stim alone. ;)
        gl.glFlush()
        gl.glFinish()
    
        if fcount==0 or fcount%chng_txt_each_flips==0:
            t=getRandomString(text_length)
            stim1_dur=updateStimText(stim1,t)
            stim1_txt_change_draw_times.append(stim1_dur)
            t=getRandomString(text_length)
            stim2_dur=updateStimText(stim2,t)
            stim2_txt_change_draw_times.append(stim2_dur)
        else:
            stim1_dur=updateStimText(stim1)
            stim1_no_change_draw_times.append(stim1_dur)
            stim2_dur=updateStimText(stim2)
            stim2_no_change_draw_times.append(stim2_dur)
            
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
    print '+ Draw Order: %s then %s\t'%(stim1.__class__.__name__,stim2.__class__.__name__)
    print '+ Text Stim Char Length:\t',text_length
    if stim1.__class__.__name__ == 'TextBox':
        print '+ TextBox INIT Dur (secs):\t%.3f'%(textbox_init_dur/1000.0)
    else:    
        print '+ TextStim INIT Dur (secs):\t%.3f'%(textstim_init_dur/1000.0)
    if stim1 != stim2:
        if stim2.__class__.__name__ == 'TextBox':
            print '+ TextBox INIT Dur (secs):\t%.3f'%(textbox_init_dur/1000.0)
        else:    
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
    print '%s\t\t%.3f\t\t%.3f'%(stim1.__class__.__name__,
        stim1_no_change_draw_times.mean(),stim1_txt_change_draw_times.mean())
    print '%s\t%.3f\t\t%.3f'%(stim2.__class__.__name__,
        stim2_no_change_draw_times.mean(),stim2_txt_change_draw_times.mean())
    print
    print '+ %s / %s Draw Time Ratio:'%(stim1.__class__.__name__,stim2.__class__.__name__)
    print
    print '\tNo Txt Change\tTxt Change'
    print
    print 'Ratio\t%.3f\t\t%.3f'%(stim1_no_change_draw_times.mean()/stim2_no_change_draw_times.mean(),
        stim1_txt_change_draw_times.mean()/stim2_txt_change_draw_times.mean())
    print
    print '---------------------------------------'

core.quit()