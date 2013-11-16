# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 18:37:10 2013

@author: Sol
"""
from psychopy import visual, core, event
import numpy as np

display_resolution=800,600
# Create Window
window=visual.Window(display_resolution,
                        units='pix',
                        fullscr=False, allowGUI=False,
                        screen=0
                        )

# Create two textBox stim, each using different parameters supported by
# Textbox. Note that since no font_name is provided when creating the
# textbox stim, a default font is selected by TextBox stim automatically.  
#                                                         
textbox=visual.TextBox(window=window, 
                         text='PRESS ANY KEY TO QUIT DEMO.\n(Displayed using a plain TextBox.)', 
                         bold=False,
                         italic=False,
                         font_size=18,
                         font_color=[-1,-1,1], 
                         size=(1.9,.5),
                         pos=(0.0,0.5), 
                         units='norm',
                         grid_horz_justification='center',
                         grid_vert_justification='center',
                         )

textbox2=visual.TextBox(window=window,
                         text='This TextBox is using all the different UX elements.', 
                         bold=False,
                         italic=False,
                         font_size=32,
                         font_color=[1,-1,-1], 
                         background_color=[-1,-1,-1,1],
                         border_color=[-1,-1,1,1],
                         border_stroke_width=4,
                         grid_color=[-1,1,-1,1],
                         grid_stroke_width=1,
                         textgrid_shape=[20,4], # 20 cols (20 chars wide)
                                                # by 3 rows (3 lines of text)
                         #size=(1.75,.6),
                         pos=(0.0,-0.5),
                         grid_horz_justification='center', 
                         grid_vert_justification='center',
                         )


textbox.draw()
textbox2.draw()
demo_start=window.flip()     
event.clearEvents()
last_attrib_change_time=demo_start
while True:
    if core.getTime()-last_attrib_change_time> 2.5:
        last_attrib_change_time=core.getTime()
        color=list(((np.random.rand(3,1)*2.0)-1.0)[:,0])
        textbox.setFontColor(list(((np.random.rand(3,1)*2.0)-1.0)[:,0]))
        
        textbox2.setFontColor(list(((np.random.rand(3,1)*2.0)-1.0)[:,0]))
        textbox2.setBackgroundColor(list(((np.random.rand(3,1)*2.0)-1.0)[:,0]))
        textbox2.setBorderColor(list(((np.random.rand(3,1)*2.0)-1.0)[:,0]))
        textbox2.setBorderWidth(np.random.choice([2,4,6,8]))
        textbox2.setTextGridLineColor(list(((np.random.rand(3,1)*2.0)-1.0)[:,0]))
        #textbox2.setTextGridLineWidth(np.random.choice([2,4,6,8]))
        textbox2.setHorzJust(np.random.choice(['left','center','right']))
        textbox2.setVertJust(np.random.choice(['top','center','bottom']))
        #textbox2.setPosition((np.random.choice([-0.1,0,.1]),np.random.choice([-0.3,-0.4,-0.5])))
        #textbox2.setHorzAlignment(np.random.choice(['left','center','right']))
        #textbox2.setVertAlignment(np.random.choice(['top','center','bottom']))
        
        
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