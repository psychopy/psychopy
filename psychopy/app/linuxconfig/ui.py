# -*- coding: utf-8 -*-

###########################################################################
## Python code generated with wxFormBuilder (version 3.10.1-0-g8feb16b)
## http://www.wxformbuilder.org/
##
## PLEASE DO *NOT* EDIT THIS FILE!
###########################################################################

import wx
import wx.xrc

###########################################################################
## Class BaseLinuxConfigDialog
###########################################################################

class BaseLinuxConfigDialog ( wx.Dialog ):

    def __init__( self, parent ):
        wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = u"Additional configuration needed ...", pos = wx.DefaultPosition, size = wx.Size( 640,420 ), style = wx.DEFAULT_DIALOG_STYLE )

        self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )

        szrMain = wx.BoxSizer( wx.VERTICAL )

        self.lblIntro = wx.StaticText( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
        self.lblIntro.Wrap( 640 )

        szrMain.Add( self.lblIntro, 0, wx.ALL|wx.EXPAND, 5 )

        szrCommands = wx.FlexGridSizer( 3, 2, 5, 5 )
        szrCommands.AddGrowableCol( 0 )
        szrCommands.AddGrowableRow( 0 )
        szrCommands.SetFlexibleDirection( wx.BOTH )
        szrCommands.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.txtCmdList = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.TE_DONTWRAP|wx.TE_MULTILINE|wx.TE_READONLY )
        szrCommands.Add( self.txtCmdList, 1, wx.EXPAND, 5 )

        self.cmdCopyLine = wx.Button( self, wx.ID_ANY, u"Copy", wx.DefaultPosition, wx.DefaultSize, 0 )
        szrCommands.Add( self.cmdCopyLine, 0, 0, 5 )


        szrMain.Add( szrCommands, 1, wx.ALL|wx.EXPAND, 10 )

        szrButtons = wx.FlexGridSizer( 0, 4, 0, 0 )
        szrButtons.AddGrowableCol( 1 )
        szrButtons.SetFlexibleDirection( wx.BOTH )
        szrButtons.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

        self.cmdOpenTerminal = wx.Button( self, wx.ID_ANY, u"Open Terminal ...", wx.DefaultPosition, wx.DefaultSize, 0 )
        szrButtons.Add( self.cmdOpenTerminal, 0, 0, 0 )


        szrButtons.Add( ( 0, 0), 1, wx.EXPAND, 5 )

        self.cmdDone = wx.Button( self, wx.ID_ANY, u"Done", wx.DefaultPosition, wx.DefaultSize, 0 )
        szrButtons.Add( self.cmdDone, 0, 0, 0 )


        szrMain.Add( szrButtons, 0, wx.ALL|wx.EXPAND, 10 )


        self.SetSizer( szrMain )
        self.Layout()

        self.Centre( wx.BOTH )

        # Connect Events
        self.cmdCopyLine.Bind( wx.EVT_BUTTON, self.OnCopy )
        self.cmdOpenTerminal.Bind( wx.EVT_BUTTON, self.OnOpenTerminal )
        self.cmdDone.Bind( wx.EVT_BUTTON, self.OnDone )

    def __del__( self ):
        pass


    # Virtual event handlers, override them in your derived class
    def OnCopy( self, event ):
        event.Skip()

    def OnOpenTerminal( self, event ):
        event.Skip()

    def OnDone( self, event ):
        event.Skip()


