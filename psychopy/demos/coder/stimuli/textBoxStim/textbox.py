# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 18:37:10 2013

@author: Sol
"""
from psychopy import visual, core, event

display_resolution=800,600
# Create Window
window=visual.Window(display_resolution,
                        units='pix',
                        fullscr=False, allowGUI=False,
                        screen=0
                        )

# Here we are adding text styles that will be used by the TextBox 
# created later in the script.
# By creating the text style this way, multiple textbox instances can share
# the same text style if desired.
#
#  ** IMPORTANT: TextBox.createTextStyle can only be called PRIOR to
#                any actual TextBox class instances being created.

visual.TextBox.createTextStyle(text_style_label='VeraBold24',
                                    file_name='VeraMoBd.ttf',
                                    font_size=24,
                                    font_color=[1,-1,-1],
                                    font_background_color=[1,1,1]
                                    )

visual.TextBox.createTextStyle(text_style_label='Vera36',
                                    file_name='VeraMono.ttf',
                                    font_size=36,
                                    font_color=[1,1,1,1]
                                    )
                                                               
textbox=visual.TextBox(window=window, 
                         text_style_label='Vera36',
                         text='This is the plain TextBox UX.', 
                         size=(1.33,.30),
                         pos=(0.0,0.25), 
                         grid_horz_justification='center',
                         grid_vert_justification='center'                       
                         )

textbox2=visual.TextBox(window=window,
                         text_style_label='VeraBold24',
                         text='This TextBox is using the different UX features.', 
                         background_color=[-1,-1,-1,1],
                         border_color=[-1,-1,1,1],
                         border_stroke_width=4,
                         grid_color=[-1,1,-1,1],
                         grid_stroke_width=1,
                         size=(1.5,.25),
                         pos=(0.0,-0.25),
                         grid_horz_justification='center',
                         grid_vert_justification='center',
                         )

textbox.draw()
textbox2.draw()
demo_start=window.flip()     
event.clearEvents()

while True:
    textbox.draw()
    textbox2.draw()
    # Update the display to show stim changes
    flip_time=window.flip()

    # End the test when a keyboard event is detected
    #
    kb_events=event.getKeys()
    if kb_events:
        break

core.quit()