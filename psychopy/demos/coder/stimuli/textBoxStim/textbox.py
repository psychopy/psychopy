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

                                                               
textbox=visual.TextBox(window=window, 
                         text='This is the plain TextBox UX.', 
                         font_name='Lucida Console',
                         bold=False,
                         italic=False,
                         font_size=32,
                         font_color=[1,1,1], 
                         background_color=[0,.25,.9,1],
                         size=(1.33,.30),
                         pos=(0.0,0.25), 
                         units='norm',
                         grid_horz_justification='center',
                         grid_vert_justification='center',
                         )
#
#textbox2=visual.TextBox(window=window,
#                         text='This TextBox is using the different UX features.', 
#                         font_name='Lucida Console',
#                         bold=False,
#                         italic=False,
#                         font_size=32,
#                         font_color=[-1,-1,-1], 
#                         background_color=[-1,-1,-1,1],
#                         border_color=[-1,-1,1,1],
#                         border_stroke_width=4,
#                         grid_color=[-1,1,-1,1],
#                         grid_stroke_width=1,
#                         size=(1.5,.25),
#                         pos=(0.0,-0.25),
#                         grid_horz_justification='center',
#                         grid_vert_justification='center',
#                         )

textbox.draw()
#textbox2.draw()
demo_start=window.flip()     
event.clearEvents()

while True:
    textbox.draw()
    #textbox2.draw()
    # Update the display to show stim changes
    flip_time=window.flip()

    # End the test when a keyboard event is detected
    #
    kb_events=event.getKeys()
    if kb_events:
        break

core.quit()