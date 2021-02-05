# -*- coding: utf-8 -*-
"""
Tests the timing of the TextBox, TextBox2, and TextStim:
   * Time to create and perform the first build() of each stim type.
   * Time to change the stim text to be displayed and call draw().
   * Time to do a draw() call when the stim text content has not changed.

At the end of the test, a txt report is printed to the console giving the
various timing measures collected.
"""
import string
import random
from psychopy import visual, core, event
from psychopy.visual import textbox
from psychopy.iohub.util import NumPyRingBuffer
import pyglet.gl as gl

# Variables to control text string length etc.
text_length=160
chng_txt_each_flips=5
max_flip_count=60*10
text_stim_types = [visual.TextBox, visual.TextBox2, visual.TextStim]
text_stim = []
stim_init_durations={}
txt_change_draw_times={}
no_change_draw_times={}

for stype in text_stim_types:
    # Circular buffers to store timing measures
    cname = stype.__name__
    txt_change_draw_times[cname]=NumPyRingBuffer(max_flip_count)
    no_change_draw_times[cname]=NumPyRingBuffer(max_flip_count)

# Some utility functions >>>
#
char_choices=string.ascii_uppercase+"ùéèàç^ùèàçé«¼±£¢¤¬¦²³½¾°µ¯­±√∞≤≥±≠"

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

### Main text Script logic ###

# Create Window
window=visual.Window((1920,1080),
                        units='pix',
                        fullscr=True, allowGUI=False,
                        screen=0
                        )

# Find a font that is available on the system.
fm = textbox.getFontManager()
font_names=fm.getFontFamilyNames()
font_name=font_names[0]
prefered_fonts=[fn for fn in font_names if fn in ['Courier New',
                                                  'Consolas',
                                                  'Lucida Sans Typewriter',
                                                  'Ubuntu Mono',
                                                  'DejaVu Sans Mono',
                                                  'Bitstream Vera Sans Mono']]
if prefered_fonts:
    font_name=prefered_fonts[0]
print("Using font: ", font_name)

text_class_params=dict()
text_class_params['TextBox']=dict(window=window,
                                text=text, 
                                font_name=font_name,
                                font_size=28,
                                font_color=[255,255,255],
                                size=(1.5,.5),
                                pos=(0.0,.5), 
                                units='norm',
                                grid_horz_justification='left',
                                grid_vert_justification='center',
                                color_space='rgb255')
text_class_params['TextBox2']=dict(win=window, 
                                text=text,
                                font=font_name,
                                borderColor=None, 
                                fillColor=[0,0,0],
                                pos=(0.0,-0.1),
                                units='height',
                                anchor='center',
                                letterHeight=0.03,
                                editable=False,
                                size=[1.5,.33])
text_class_params['TextStim']=dict(win=window,
                                pos=(0.0,-0.5),
                                font=font_name,
                                units='norm',
                                height=0.06,
                                text=text,
                                autoLog=False,
                                wrapWidth=1.5)

# Create each stim type and perform draw on it. Time how long it takes 
# to create the initial stim and do the initial draw. 
for ttype in text_stim_types:
    cname = ttype.__name__
    stime=core.getTime()                                   
    text_stim.append(ttype(**text_class_params[cname]))
    text_stim[-1].draw()
    etime=core.getTime()
    stim_init_durations[cname]=etime-stime


# Start the draw duration tests, for text change and no text change conditions.
demo_start=window.flip()     
event.clearEvents()
fcount=0

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
        
        for tstim in text_stim:
            cname = tstim.__class__.__name__
            stime=core.getTime()*1000.0
            tstim.setText(tstim.__class__.__name__+t)
            tstim.draw()
            gl.glFinish()
            etime=core.getTime()*1000.0 
            txt_change_draw_times[cname].append(etime-stime)

    else:
        for tstim in text_stim:    
            cname = tstim.__class__.__name__
            stime=core.getTime()*1000.0
            tstim.draw()
            gl.glFinish()
            etime=core.getTime()*1000.0 
            no_change_draw_times[cname].append(etime-stime)
        
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

print()
print('-------Text Draw Duration Test---------')
print()
print('+ Draw Order: {}\t'.format([c.__name__ for c in text_stim_types]))
print('+ Text Stim Char Length:\t',text_length)
print()
for stim_type,init_dur in stim_init_durations.items():
    print('+ {} INIT Dur (sec):\t{}'.format(stim_type, init_dur))
print()
print('+ Text Change Flip Perc:\t%.2f'%((1.0/chng_txt_each_flips)*100.0))
print('+ Total Flip Count:\t\t',fcount)
print('+ Test Duration (secs):\t\t%.3f'%(flip_time-demo_start))
print('+ FPS:\t\t\t\t%.3f'%(fcount/(flip_time-demo_start)))
print()
print('+ Average Draw Call Durations (msec):')
print()
print('  Text Object\t\tNo Txt Change\tTxt Change')
for stim_type in text_stim_types:
    cname = stim_type.__name__
    print('  %s\t\t%.3f\t\t%.3f'%(cname, 
                                  no_change_draw_times[cname].mean(),
                                  txt_change_draw_times[cname].mean()))
print()
    
core.quit()
