 # -*- coding: utf-8 -*-
"""
Shows use of getGlyphPositionForTextIndex() to get exact bounding box for a
given glyph based on an index in the text string being shown.

Displayed the mouse position in display coord's so the reported glyph position
can be validated.

Created on Thu Mar 21 18:37:10 2013

@author: Sol
"""
from __future__ import print_function

from psychopy import visual, core, event

display_resolution=800,600
# Create Window
window=visual.Window(display_resolution,
                        units='norm',
                        fullscr=False, allowGUI=True,
                        screen=0
                        )

myMouse = event.Mouse()

# Create two textBox stim, each using different parameters supported by
# Textbox. Note that since no font_name is provided when creating the
# textbox stim, a default font is selected by TextBox stim automatically.  
#
sometext=u'PRESS ANY KEY TO QUIT DEMO.'                                                        
textbox=visual.TextBox(window=window, 
                         text=sometext,
                         bold=False,
                         italic=False,
                         font_size=21,
                         font_color=[-1,-1,1], 
                         size=(1.9,.3),
                         grid_color=[-1,1,-1,1],
                         grid_stroke_width=1,
                         pos=(0.0,0.5), 
                         units='norm',
                         grid_horz_justification='center',
                         grid_vert_justification='center',
                         )

if textbox.getDisplayedText()!=textbox.getText():
    print('**Note: Text provided to TextBox does not fit within the TextBox bounds.')

#print textbox.getTextGridCellPlacement()
print('Char Index 0 glyph box:',textbox.getGlyphPositionForTextIndex(0))
print('Char Index 7 glyph box:',textbox.getGlyphPositionForTextIndex(7))
disp_txt_len=len(textbox.getDisplayedText())-1
print('Char Index %d glyph box:'%(disp_txt_len),textbox.getGlyphPositionForTextIndex(disp_txt_len))


mouse_position=visual.TextBox(window=window, 
                         text='(123456,123456)',
                         bold=False,
                         italic=False,
                         font_size=14,
                         font_color=[1,1,1], 
                         textgrid_shape=(20,1),
                         pos=(0.0,0.5), 
                         units='norm',
                         align_horz='left',
                         align_vert='bottom',
                         grid_horz_justification='left',
                         grid_vert_justification='left',
                         )

textbox.draw()
demo_start=window.flip()     
event.clearEvents()
last_attrib_change_time=demo_start
while True:
    if core.getTime()-last_attrib_change_time> 2.5:
        last_attrib_change_time=core.getTime()
                
    textbox.draw()
    mp=myMouse.getPos()
    mouse_position.setText("%.3f,%.3f"%(mp[0], mp[1]))
    mouse_position.setPosition(mp)
    mouse_position.draw()
    # Update the display to show any stim changes
    flip_time=window.flip()

    # End the test when a keyboard event is detected
    #
    kb_events=event.getKeys()
    if kb_events:
        break

core.quit()