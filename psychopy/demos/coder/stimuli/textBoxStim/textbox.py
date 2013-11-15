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
if len(prefered_fonts)==1:
    font_name1=prefered_fonts[0]
    font_name2=available_font_names[1][0] 
elif len(prefered_fonts)>1:
    font_name1=prefered_fonts[0]
    font_name2=prefered_fonts[1] 
else:
    font_name1=available_font_names[0][0]   
    font_name2=available_font_names[1][0]   
                                                           
textbox=visual.TextBox(window=window, 
                         text='This is the plain TextBox UX.', 
                         font_name=font_name1,
                         bold=False,
                         italic=False,
                         font_size=32,
                         font_color=[-1,-1,1], 
                         #grid_color=[-1,-1,-1,1],
                         #grid_stroke_width=1,
                         #background_color=[0,.25,.9,1],
                         size=(1.9,.5),
                         pos=(0.0,0.5), 
                         units='norm',
                         grid_horz_justification='center',
                         grid_vert_justification='center',
                         )

textbox2=visual.TextBox(window=window,
                         text='This TextBox is using the different UX features.', 
                         font_name=font_name2,
                         bold=False,
                         italic=False,
                         font_size=36,
                         font_color=[1,-1,-1], 
                         background_color=[-1,-1,-1,1],
                         border_color=[-1,-1,1,1],
                         border_stroke_width=4,
                         grid_color=[-1,1,-1,1],
                         grid_stroke_width=1,
                         size=(1.5,.5),
                         pos=(0.0,-0.5),
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