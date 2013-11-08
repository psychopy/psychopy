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

display_resolution=800,600
textbox_width=1.66
textbox_height=.33
textbox_units='norm'

# Create PsychoPy Window and various visual stim, 
# including a TextStim and two Textbox stim.    

# Create Window
window=visual.Window(display_resolution,
                        units='pix',
                        fullscr=False, allowGUI=False,
                        screen=0
                        )

# Here we are adding a text style that will be used by the second TextBox stim.
# By creating the text style this way, multiple textbox instances can share
# the same text style if desired.
#
#  ** IMPORTANT: TextBox.createTextStyle can only be called PRIOR to
#                any actual TextBox class instances being created.

visual.TextBox.createTextStyle(text_style_label='style1',
                                    file_name='VeraMoBd.ttf',
                                    font_size=24,
                                    dpi=72,
                                    font_color=[0,0,0],
                                    font_background_color=None,
                                    color_space='rgb255',
                                    opacity=1)
                                                               
#textbox=visual.TextBox(window=window,
#                         name='textbox1', 
#                         text_style_label='style1',
#                         text='This is the default TextBox UX.', 
#                         size=(textbox_width,textbox_height),
#                         pos=(0.0,0.5), 
#                         units=textbox_units,  
#                         align_horz='center',
#                         align_vert='center',
#                         grid_horz_justification='center',
#                         grid_vert_justification='center'
#                         )

textbox2=visual.TextBox(window=window,
                         name='textbox1', 
                         text='This TextBox is using the different UX features.', 
                         font_file_name='VeraMono.ttf', 
                         font_size=36,
                         dpi=72, 
                         font_color=[255,255,255,255], 
                         background_color=[0,0,0,255],
                         border_color=[0,0,255,255],
                         border_stroke_width=4,
                         grid_color=[255,0,0,128],
                         grid_stroke_width=1,
                         size=(textbox_width,textbox_height),
                         pos=(0.0,0.0), 
                         units=textbox_units,  
                         align_horz='center',
                         align_vert='center',
                         grid_horz_justification='center',
                         grid_vert_justification='center',
                         color_space='rgb255'
                         )

#textbox.draw()
textbox2.draw()

demo_start=window.flip()     
event.clearEvents()
fcount=0
while True:

#    textbox.draw()
    textbox2.draw()
    # Update the display to show stim changes
    flip_time=window.flip()
    fcount+=1

    # End the test when a keyboard event is detected or when max_flip_count
    # win.flip() calls have been made.
    #
    kb_events=event.getKeys()
    if kb_events:
        break

core.quit()