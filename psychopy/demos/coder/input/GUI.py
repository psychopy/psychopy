#!/usr/bin/env python2
from psychopy import gui

# create a DlgFromDict
info = {'Observer':'jwp','gender':['male','female'], 'GratingOri':45, 'ExpVersion': 1.1, 'Debug Mode': True}
infoDlg = gui.DlgFromDict(dictionary=info, title='TestExperiment', 
    order=['ExpVersion', 'Observer'], 
    tip={'Observer': 'trained visual observer, initials'},
    fixed=['ExpVersion'])#this attribute can't be changed by the user
if infoDlg.OK: #this will be True (user hit OK) or False (cancelled)
    print info
else: 
    print 'User Cancelled'

#this alternative uses a Dlg and you manually extract the data (more control: eg, text, color)
myDlg = gui.Dlg(title="JWP's experiment", pos=(200,400))
myDlg.addText('Subject Info', color='Blue')
myDlg.addField('Name:', tip='or subject code')
myDlg.addField('Age:', 21)
myDlg.addText('Experiment Info', color='Blue')
myDlg.addField('',45)

myDlg.show()#you have to call show() for a Dlg (it gets done implicitly by a DlgFromDict)
if myDlg.OK:
    thisInfo = myDlg.data #this will be a list of data returned from each field added in order
    print thisInfo
else: print 'user cancelled'
