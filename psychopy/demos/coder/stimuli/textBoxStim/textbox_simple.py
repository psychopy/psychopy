# -*- coding: utf-8 -*-
"""
Shows how to create two textBox stim and present them. The first textbox
simply displays the text provided, centered. The second textbox shows more
of the configuration options available for the stim type.

Created on Thu Mar 21 18:37:10 2013

@author: Sol
"""
from psychopy import visual, core, event

# Create Window
window=visual.Window((800,600),
                        units='norm',
                        fullscr=False, allowGUI=True,
                        screen=0
                        )

sometext=u'PRESS ANY KEY TO QUIT DEMO.'                                                        
textbox=visual.TextBox(window=window, 
                         text=sometext,
                         font_size=21,
                         font_color=[-1,-1,1], 
                         size=(1.9,.3),
                         pos=(0.0,0.25), 
                         grid_horz_justification='center',
                         units='norm',
                         )

textbox2=visual.TextBox(window=window,
                         text='This TextBox illustrates many of the different UX elements.', 
                         font_size=32,
                         font_color=[1,-1,-1], 
                         background_color=[-1,-1,-1,1],
                         border_color=[-1,-1,1,1],
                         border_stroke_width=4,
                         textgrid_shape=[20,4], # 20 cols (20 chars wide)
                                                # by 4 rows (4 lines of text)
                         pos=(0.0,-0.25),
                         )

textbox.draw()
textbox2.draw()
demo_start=window.flip()     

event.clearEvents()
last_attrib_change_time=demo_start
while True:
    if core.getTime()-last_attrib_change_time> 2.5:
        last_attrib_change_time=core.getTime()

    textbox.draw()
    textbox2.draw()

    # Update the display to show any stim changes
    flip_time=window.flip()

    # End the test when a keyboard event is detected
    #
    kb_events=event.getKeys()
    if kb_events:
        break

core.quit()