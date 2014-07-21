#!/usr/bin/env python2
from psychopy import visual, core, event

"""One easy way to handle stimuli that are drawn repeatedly is to 
setAutoDraw(True) for that stimulus. It will continue to be drawn until
stim.setAutoDraw(False) is called. By default a logging message of
level EXP will be created when the setAutoDraw is called. 

This can be turned off for each call with stim with stim.setAutoDraw(True, autoLog=False)
"""

win=visual.Window([800,800])
stim1=visual.PatchStim(win,pos=[-0.5,-0.5], name='stim1')#name is used in log entries
stim2=visual.TextStim(win,pos=[0.5,0.5],text='stim2',name='textStim')
fixation=visual.PatchStim(win,mask='gauss',tex=None,size=0.02,
    name='fixation', autoLog=False)#no need to log the fixation piont info

fixation.setAutoDraw(True)#no need to log fixation info
stim1.setAutoDraw(True)
stim2.setAutoDraw(True)
#both on
for frameN in range(20):#run 20 frames like this
    win.flip()

stim2.setAutoDraw(False)
#only stim1 (and fixation)
for frameN in range(20):#run 20 frames like this
    win.flip()
    
stim1.setAutoDraw(False)
stim2.setAutoDraw(True)
#only stim2 (and fixation)
for frameN in range(20):#run 20 frames like this
    win.flip()
    
for stim in [stim1, stim2, fixation]:
    stim.setAutoDraw(False)
win.flip()#will cause the 'off' log messages to be sent
