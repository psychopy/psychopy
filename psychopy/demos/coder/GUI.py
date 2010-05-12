#!/usr/bin/env python
from psychopy import gui

# create a DlgFromDict
info = {'Observer':'jwp', 'GratingOri':45, 'ExpVersion': 1.1, 'Debug Mode': True}
infoDlg = gui.DlgFromDict(dictionary=info, title='TestExperiment', 
    fixed=['ExpVersion'])#this attribute can't be changed by the user
if infoDlg.OK: #this will be True (user hit OK) or False (cancelled)
    print info
else: 
    print 'User Cancelled'

#this alternative uses a Dlg and you manually extract the data (maybe more control?!)
myDlg = gui.Dlg(title="JWP's experiment", pos=(200,400))
myDlg.addText('Subject info')
myDlg.addField('Name:')
myDlg.addField('Age:', 21)
myDlg.addText('Experiment Info')
myDlg.addField('Grating Ori:',45)

myDlg.show()#you have to call show() for a Dlg (it gets done implicitly by a DlgFromDict)
if myDlg.OK:
    thisInfo = myDlg.data #this will be a list of data returned from each field added in order
    print thisInfo
else: print 'user cancelled'
