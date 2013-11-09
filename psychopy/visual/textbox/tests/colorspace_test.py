# -*- coding: utf-8 -*-
"""
Created on Thu Mar 21 18:37:10 2013

@author: Sol
"""
import string
import random
from psychopy import visual, core, event
from psychopy.iohub.util import NumPyRingBuffer
from decimal import *

# Variables to control text string length etc.
text_length=200
chng_txt_each_flips=5
max_flip_count=60*60*2
display_resolution=1920,1080
textbox_width=display_resolution[0]*.8
textbox_height=200


# Some utility functions >>>
#
char_choices=u"ùéèàç^ùèàçé«¼±£¢¤¬¦²³½¾°µ¯­±√∞≤≥±≠"+string.ascii_uppercase[:15]
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
                                    font_color=[-1,1,-1,1],
                                    font_background_color=None,
                                    color_space='rgb',
                                    opacity=1.0)
                                    
                                
textbox=visual.TextBox(window=window,
                         name='textbox1', 
                         active_text_style_label='style1', 
                         text=text, 
                         border_stroke_width=2,
                         grid_color=[-1,-1,1,.5],
                         grid_stroke_width=1,
                         size=(textbox_width,textbox_height),
                         pos=(0.0,0.0), 
                         units='pix',  
                         align_horz='center',
                         align_vert='center',
                         grid_horz_justification='center',
                         grid_vert_justification='center'
                         )

# text colorspace conversion func. Note that this test access private attributes
# of textbox so a single textbox can be used to test many color space conversions.
# This is not code that would be used in a end user script.

color_conditions=[]

# Condition tests that have rgba = None *should* raise an exception for the
# test case to pass

# rgb (3 or 4 elementsm, -1 to 1.0):
color_conditions.append(dict(color_space='rgb',color=[0.0,0.0,0.0],opacity=.75,rbga=[0.5,0.5,0.5,0.75]))
color_conditions.append(dict(color_space='rgb',color=0.0,opacity=.75,rbga=[0.5,0.5,0.5,0.75]))
color_conditions.append(dict(color_space='rgb',color=1,opacity=.75,rbga=[1.0,1.0,1.0,0.75]))
color_conditions.append(dict(color_space='rgb',color=[-1,0.0,1],opacity=0,rbga=[0.0,0.5,1.0,0.0]))
color_conditions.append(dict(color_space='rgb',color=[1,-1,-1,1],opacity=0.5,rbga=[1.0,0.0,0.0,1.0]))
color_conditions.append(dict(color_space='rgb',color=[2,-1,-1,1],opacity=1,rbga=None))
color_conditions.append(dict(color_space='rgb',color=[0,-1,-1,1,1],opacity=1,rbga=None))
color_conditions.append(dict(color_space='rgb',color=['A',-1,-1],opacity=1,rbga=None))
color_conditions.append(dict(color_space='rgb',color=2,opacity=1,rbga=None))

# rgba255 (3 or 4 elementsm, -1 to 1.0):
color_conditions.append(dict(color_space='rgb255',color=[128,128,128],opacity=.75,rbga=[0.5,0.5,0.5,0.75]))
color_conditions.append(dict(color_space='rgb255',color=0,opacity=.75,rbga=[0.0,0.0,0.0,0.75]))
color_conditions.append(dict(color_space='rgb255',color=255,opacity=.75,rbga=[1.0,1.0,1.0,0.75]))
color_conditions.append(dict(color_space='rgb255',color=[0,128,255.0],opacity=0,rbga=[0.0,0.5,1.0,0.0]))
color_conditions.append(dict(color_space='rgb255',color=[255,0.0,0.0,255],opacity=0.5,rbga=[1.0,0.0,0.0,1.0]))
color_conditions.append(dict(color_space='rgb255',color=[300,0,0,255],opacity=1,rbga=None))
color_conditions.append(dict(color_space='rgb255',color=[255,0,0],opacity=2,rbga=None))
color_conditions.append(dict(color_space='rgb255',color=257,opacity=1,rbga=None))

# hex colors

color_conditions.append(dict(color_space='rgb255',color='0xFFFAF0',opacity=.75,rbga=[1.0,0.98,.94,0.75]))
color_conditions.append(dict(color_space='rgb',color='#FFFAF0',opacity=0,rbga=[1.0,0.98,.94,0.0]))
color_conditions.append(dict(color_space=None,color='0xFFFA00',opacity=0.5,rbga=[1.0,0.98,0.0,0.5]))
color_conditions.append(dict(color_space='rgb255',color='##FFFA0',opacity=1,rbga=None))
color_conditions.append(dict(color_space='rgb255',color='##FFFAF0Z',opacity=1,rbga=None))
color_conditions.append(dict(color_space='rgb255',color='0xFFFA0',opacity=2,rbga=None))
color_conditions.append(dict(color_space='rgb255',color='0xFFFAF0Z',opacity=2,rbga=None))

# html colors

color_conditions.append(dict(color_space='rgb255',color='AliceBlue',opacity=.75,rbga=[.94,0.97,1.0,0.75]))
color_conditions.append(dict(color_space='rgb',color='LightGray',opacity=0,rbga=[.83,0.83,.83,0.0]))
color_conditions.append(dict(color_space=None,color='Gold',opacity=0.5,rbga=[1.0,0.84,0.0,0.5]))
color_conditions.append(dict(color_space='rgb255',color='NotAColor',opacity=1,rbga=None))
color_conditions.append(dict(color_space=None,color='ThisIsWrong',opacity=1,rbga=None))
color_conditions.append(dict(color_space=None,color='AliceBlue',opacity=2,rbga=None))

# dkl colors
print
print '** TODO: Test dkl color conversion'
print

# lms colors
print
print '** TODO: Test lms color conversion'
print

# hsv colors
print
print '** TODO: Test hsv color conversion'
print

# Run tests >>>
getcontext().prec = 2

failed_tests=[]
ok_tests=[]
decone=Decimal(1.0)
for ccond in color_conditions:
    try:
        expected_rgba=ccond['rbga']

        textbox._color_space=ccond['color_space']
        textbox._background_color=ccond['color']
        textbox._opacity=ccond['opacity']
        
        cspace=textbox.getColorSpace()
        color=textbox.getBackgroundColor()
        opacity=textbox.getOpacity()
        
        rgba_result=textbox._toRGBA(color)
        
        if expected_rgba is None:
            r=dict(ccond)
            r['result']=rgba_result
            failed_tests.append(r)
        elif len([re for i,re in enumerate(rgba_result) if Decimal(re)*decone == Decimal(expected_rgba[i])*decone]) == len(expected_rgba):
            r=dict(ccond)
            r['result']=rgba_result
            ok_tests.append(r)
        else:
            r=dict(ccond)
            r['result']=rgba_result
            failed_tests.append(r)
            
    except Exception, e:
        if expected_rgba:
            r=dict(ccond)
            r['result']=e
            failed_tests.append(r)
        else:
            r=dict(ccond)
            r['result']=e
            ok_tests.append(r)

import pprint
print 'Color Space Conversion Test Results:'

print 'Total Test Cases:',len(color_conditions)
print 'Passed Test Cases:',len(ok_tests)
print 'Failed Test Cases:',len(failed_tests)
print 'Passed Percentage:',len(ok_tests)*100.0/len(color_conditions)
print 
print 'Failed Cases:'
print
for c,fc in enumerate(failed_tests):
    print '(%d)'%(c)
    pprint.pprint(fc)
    print
print '#############################'
core.quit()