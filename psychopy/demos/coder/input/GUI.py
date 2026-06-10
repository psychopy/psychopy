#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Shows how to use the psychopy.gui to present the users with a dialog box to get info from them.

The contents of this file are in the public domain.
"""

from psychopy import gui  # Fetch default gui handler (qt if available)
from psychopy import __version__ # Get the PsychoPy version currently in use
from numpy import random
## You can explicitly choose one of the qt/wx backends like this:
## from psychopy.gui import wxgui as gui
## from psychopy.gui import qtgui as gui

# specify fields for dlg as a dict
info = {
    # strings and numbers will show as an editable text field
    'Observer': "jwp", 
    'Grating Orientation': 45, 
    # lists will show as a dropdown of choices
    'Condition': ["A", "B"],
    # using a | symbol in the field name lets you tell PsychoPy that the field is...
    # ...required (|req)
    'Session ID|req': "",
    # ...fixed, so the user can't change the value
    'PsychoPy Version|fix': __version__,
    # ...a configuration parameter, to be hidden behind a "read more" tag (|cgf)
    'Debug Mode|cfg': True,
    # ...or hidden from the user entirely (|hid)
    'uid|hid': random.randint(0, 100000)
}

# create a dialog from the dict
infoDlg = gui.DlgFromDict(
    dictionary=info, 
    # this sets a title in the dialog's sash
    title="Test experiment",
    # this dict sets tooltips which are displayed on hover
    tip={
        'Observer': "Trained visual observer, initials"
    }
)

# this will be True if the user clicked OK and False if they clicked Cancel
if infoDlg.OK:
    print(info)
else: 
    print('User Cancelled')


## you could also use a gui.Dlg and you manually extract the data, this approach gives more 
## control, eg, text color.


# create dlg
dlg = gui.Dlg(
    title="Test experiment",
    pos=(200, 400)
)
# add each field manually
dlg.addText('Subject Info', color="Blue")
dlg.addField('Name:', tip="or subject code")
dlg.addField('Age:', 21)
dlg.addText('Experiment Info', color="Blue")
dlg.addField('', 45)
# call show() to show the dlg and wait for it to close (this was automatic with DlgFromDict)
thisInfo = dlg.show()

# this will be True if the user clicked OK and False if they clicked Cancel
if dlg.OK:
    print(thisInfo)
else:
    print('User cancelled')
