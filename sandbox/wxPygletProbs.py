import pyglet
import wx

#create simple app with a single dialog window
app = wx.PySimpleApp()
dlg = wx.Dialog(parent=None, id=-1, title='testDlg')
sizer = wx.BoxSizer()

choiceBox = wx.Choice(dlg, -1, choices=['one','two'])
sizer.Add(choiceBox)

#add an OK button and show
OK = wx.Button(dlg, wx.ID_OK, " OK ")
OK.SetDefault()
sizer.Add(OK)
dlg.SetSizerAndFit(sizer)
dlg.ShowModal()
