from psychopy import *
import pygame

win = visual.Window([400,400], monitor='testMonitor')

gab = visual.PatchStim(win, rgb=0.5, size =2, ori=45, sf=6, mask='gauss')
gab.draw()

txt1 = visual.TextStim(win, units='deg', pos=[0,-1.5],
                       font='brushscript', text=u'unicode fonts in',
                       rgb=[-1,-1,-1], italic=True,alignVert='bottom',alignHoriz='center',
                       ori=0,height=70, antialias=True)
txt2 = visual.TextStim(win, units='pix', pos=[0,-75],
                       font='',text=u'\u00A9 PsychoPy', #00A9 is the unicode character for copyright
                       rgb=[1,-1,-1], italic=True,alignVert='bottom',alignHoriz='center',
                       ori=0,height=90, antialias=True)

txt1.draw()
txt2.draw()

win.update()
core.wait(2)