# -*- coding: utf-8 -*-
"""
** Be sure to change the 'display_resolution' variable on line 29 so that
   it matches your screen resolution.
  
Tests the performance of the TextBox and TextStim components for three 
different conditions:
   * Time to create and perform the first build() of each stim type.
   * Time to change the stim text to be displayed and call draw().
   * Time to do a draw() call when the stim text content has not changed.

At the end of the test, a txt report is printed to the console giving the
various timing measures collected.

Created on Thu Mar 21 18:37:10 2013

@author: Sol
"""
from __future__ import print_function
from __future__ import division
from builtins import range
import string
import random
from psychopy import visual, core, event
from psychopy.visual import textbox
from psychopy.iohub.util import NumPyRingBuffer
import pyglet.gl as gl
fm = textbox.getFontManager()
print(dir(fm))
print(fm.getFontFamilyNames())

# Variables to control text string length etc.
text_length=160
chng_txt_each_flips=5
max_flip_count=60*10
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
    """
    Create a random text string of length 'slength' from the unichar values 
    in char_choices; then split the random text into 'words' of random length
    from [1,3,5,7,9].
    """
    s=u''.join(random.choice(char_choices) for i in range(slength))
    ns=u''
    lns=len(ns)
    while lns<slength:
        ns+=s[lns:lns+random.choice([1,3,5,7,9])]+' '
        lns=len(ns)
    return ns[:slength]
    
text=getRandomString(text_length)

def updateStimText(stim,text=None):
    """
    Function used by all text stim types for redrawing the stim.
    
    Update the text for the stim type assigned to 'stim', call stim.draw(),
    and ensure that all graphics card operations are complete before returning
    the time (in msec) taken to run the update logic. If 'text' is None, just 
    time the call to stim.draw(). 
    """
    stime=core.getTime()*1000.0
    if text:    
        stim.setText(text)
    stim.draw()
    gl.glFinish()
    etime=core.getTime()*1000.0 
    return etime-stime

### Main text Script logic ###

# Create Window
window=visual.Window(display_resolution,
                        units='pix',
                        fullscr=True, allowGUI=False,
                        screen=0
                        )

# Find a font that is available on the system.
fm = textbox.getFontManager()
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

# Create a TextBox stim and perform draw on it. Time how long it takes 
# to create the initial stim and do the initial draw. 
stime=core.getTime()*1000.0                                    
textbox=visual.TextBox(window=window,
                         text=text, 
                         font_name=font_name,
                         font_size=32,
                         font_color=[0,0,0],
                         dpi=72,
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

# Create a TextStim stim and perform draw on it. Time how long it takes 
# to create the initial stim and do the initial draw. 
stime=core.getTime()*1000.0
textstim = visual.TextStim(window,pos=(0.0,-(display_resolution[1]//4)),
                    alignHoriz='center',alignVert='center',height=32,
                    text=text,autoLog=False,wrapWidth=display_resolution[0]*0.8)
textstim.draw()
etime=core.getTime()*1000.0
textstim_init_dur=etime-stime

# Start the draw duration tests, for text change and no text change conditions.

stim_draw_orders=[[textstim,textbox],[textbox,textstim]]
#stim_draw_orders=[[textstim,textbox],]
for stim1, stim2 in stim_draw_orders:
    stim1_txt_change_draw_times.clear()    
    stim2_txt_change_draw_times.clear()    
    stim1_no_change_draw_times.clear()    
    stim2_no_change_draw_times.clear()    
    demo_start=window.flip()     
    event.clearEvents()
    fcount=0

    stim1_type=stim1.__class__.__name__+u' '
    stim2_type=stim2.__class__.__name__+u' '
    while True:
        # For the textBox and TextStim resource, change the text every
        # chng_txt_each_flips, and record the time it takes to update the text
        # and redraw() each resource type.
        #
    
        # Make sure timing of stim is for the time taken for that stim alone. ;)
        gl.glFlush()
        gl.glFinish()
    
        if fcount==0 or fcount%chng_txt_each_flips==0:
            t=getRandomString(text_length)
            
            stim1_dur=updateStimText(stim1,stim1_type+t)
            stim1_txt_change_draw_times.append(stim1_dur)
            t=getRandomString(text_length)
            stim2_dur=updateStimText(stim2,stim2_type+t)
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
    
    # Print a comparison of the TextBox and TextStim performance.
    #
    print()
    print('-------Text Draw Duration Test---------')
    print()
    print('+ Draw Order: %s then %s\t'%(stim1_type,stim2_type))
    print('+ Text Stim Char Length:\t',text_length)
    if stim1_type == 'TextBox':
        print('+ TextBox INIT Dur (secs):\t%.3f'%(textbox_init_dur/1000.0))
    else:    
        print('+ TextStim INIT Dur (secs):\t%.3f'%(textstim_init_dur/1000.0))
    if stim1 != stim2:
        if stim2_type == 'TextBox':
            print('+ TextBox INIT Dur (secs):\t%.3f'%(textbox_init_dur/1000.0))
        else:    
            print('+ TextStim INIT Dur (secs):\t%.3f'%(textstim_init_dur/1000.0))
    print('+ Text Change Flip Perc:\t%.2f'%((1.0/chng_txt_each_flips)*100.0),r'%')
    print()
    print('+ Total Flip Count:\t\t',fcount)
    print('+ Test Duration (secs):\t\t%.3f'%(flip_time-demo_start))
    print('+ FPS:\t\t\t\t%.3f'%(fcount/flip_time-demo_start))
    print()
    print('+ Average Draw Call Durations (msec):')
    print()
    print('Text Object\tNo Txt Change\tTxt Change')
    print()
    print('%s\t\t%.3f\t\t%.3f'%(stim1_type,
        stim1_no_change_draw_times.mean(),stim1_txt_change_draw_times.mean()))
    print('%s\t%.3f\t\t%.3f'%(stim2_type,
        stim2_no_change_draw_times.mean(),stim2_txt_change_draw_times.mean()))
    print()
    print('+ %s / %s Draw Time Ratio:'%(stim1_type,stim2_type))
    print()
    print('\tNo Txt Change\tTxt Change')
    print()
    print('Ratio\t%.3f\t\t%.3f'%(
        stim1_no_change_draw_times.mean()/stim2_no_change_draw_times.mean(),
        stim1_txt_change_draw_times.mean()/stim2_txt_change_draw_times.mean()))
    print()
    print('---------------------------------------')

core.quit()
