#test psychopy.gui
from psychopy import gui

#DlgFromDict
info = {'Observer':'jwp', 'GratingOri':45, 'ExpVersion': 1.1}
infoDlg = gui.DlgFromDict(dictionary=info, title='TestExperiment', fixed=['ExpVersion'])
if infoDlg.OK:
    print info
else: 
    print infoDlg.OK
    print 'User Cancelled'

#this alternative uses a Dlg and you manually extract the data (maybe more control?!)
myDlg = gui.Dlg(title="JWP's experiment")
myDlg.addText('Subject info')
myDlg.addField('Name:')
myDlg.addField('Age:', 21)
myDlg.addText('Experiment Info')
myDlg.addField('Grating Ori:',45)
myDlg.show()
if myDlg.OK:
    thisInfo = myDlg.data
    print thisInfo
else: print 'user cancelled'
