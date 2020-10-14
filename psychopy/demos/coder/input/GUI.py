#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo to illustrate Dialog (Dlg) classes and usage.
"""

from __future__ import absolute_import, division, print_function

from psychopy import gui  #fetch default gui handler (qt if available)
## you can explicitly choose one of the qt/wx backends like this:
## from psychopy.gui import wxgui as gui
## from psychopy.gui import qtgui as gui

# create a DlgFromDict
info = {'Observer':'jwp', 'gender':['male', 'female'],
    'GratingOri':45, 'ExpVersion': 1.1, 'Debug Mode': True}
infoDlg = gui.DlgFromDict(dictionary=info, title='TestExperiment',
    order=['ExpVersion', 'Observer'],
    tip={'Observer': 'trained visual observer, initials'},
    fixed=['ExpVersion'])  # this attribute can't be changed by the user
if infoDlg.OK:  # this will be True (user hit OK) or False (cancelled)
    print(info)
else:
    print('User Cancelled')

# This alternative uses a gui.Dlg and you manually extract the data.
# This approach gives more control, eg, text color.
dlg = gui.Dlg(title="My experiment", pos=(200, 400))
dlg.addText('Subject Info', color='Blue')
dlg.addField('Name:', tip='or subject code')
dlg.addField('Age:', 21)
dlg.addText('Experiment Info', color='Blue')
dlg.addField('', 45)

thisInfo = dlg.show()  # you have to call show() for a Dlg (automatic with a DlgFromDict)    
if dlg.OK:
    print(thisInfo)
else:
    print('User cancelled')

# The contents of this file are in the public domain.
