#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Demo to illustrate Dialog (Dlg) classes and usage.
"""

from psychopy import gui  # Fetch default gui handler (qt if available)
from psychopy import __version__ # Get the PsychoPy version currently in use
## You can explicitly choose one of the qt/wx backends like this:
## from psychopy.gui import wxgui as gui
## from psychopy.gui import qtgui as gui

# Specify fields for dlg as a dict
info = {'Observer':'jwp', 
    'Condition':['A', 'B'],
    'Grating Orientation': 45, 
    'PsychoPy Version': __version__,
    'Debug Mode': True}
# Use this dict to create the dlg
infoDlg = gui.DlgFromDict(dictionary=info, 
    title='TestExperiment',
    order=['PsychoPy Version', 'Observer'],
    tip={'Observer': 'trained visual observer, initials'},
    fixed=['PsychoPy Version'])  # This attribute can't be changed by the user
# Script will now wait for the dlg to close...

if infoDlg.OK:  # This will be True if user hit OK...
    print(info)
else: # ...or False, if they hit Cancel
    print('User Cancelled')

## You could also use a gui.Dlg and you manually extract the data, this approach gives more 
## control, eg, text color.

# Create dlg
dlg = gui.Dlg(title="My experiment", pos=(200, 400))
# Add each field manually
dlg.addText('Subject Info', color='Blue')
dlg.addField('Name:', tip='or subject code')
dlg.addField('Age:', 21)
dlg.addText('Experiment Info', color='Blue')
dlg.addField('', 45)
# Call show() to show the dlg and wait for it to close (this was automatic with DlgFromDict
thisInfo = dlg.show()

if dlg.OK: # This will be True if user hit OK...
    print(thisInfo)
else:
    print('User cancelled') # ...or False, if they hit Cancel

## The contents of this file are in the public domain.
