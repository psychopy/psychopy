# -*- coding: utf-8 -*-

import wx
import wx.xrc
from psychopy.localization import _translate

###########################################################################
## Class ColorPickerDialog
###########################################################################

class ColorPickerDialog ( wx.Dialog ):

	def __init__( self, parent ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = "Color Picker", pos = wx.DefaultPosition, size = wx.Size( 640,480 ), style = wx.DEFAULT_DIALOG_STYLE )

		self.SetSizeHints( wx.Size( -1,-1 ), wx.DefaultSize )

		szrMain = wx.BoxSizer( wx.VERTICAL )

		self.pnlColorSelector = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		szrColorSelector = wx.BoxSizer( wx.HORIZONTAL )

		self.pnlColorPreview = wx.Panel( self.pnlColorSelector, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.pnlColorPreview.SetBackgroundColour( wx.SystemSettings.GetColour( wx.SYS_COLOUR_HIGHLIGHT ) )
		self.pnlColorPreview.SetMaxSize( wx.Size( 120,-1 ) )

		szrColorSelector.Add( self.pnlColorPreview, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 5 )

		self.nbColorSelector = wx.Notebook( self.pnlColorSelector, wx.ID_ANY, wx.DefaultPosition, wx.Size( -1,-1 ), 0 )
		self.pnlRGBPage = wx.Panel( self.nbColorSelector, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		szrRGBPage = wx.BoxSizer( wx.VERTICAL )

		fraRGBChannels = wx.StaticBoxSizer( wx.StaticBox( self.pnlRGBPage, wx.ID_ANY, _translate(" RGB Channels ") ), wx.VERTICAL )

		szrRGBChannels = wx.FlexGridSizer( 3, 3, 5, 10 )
		szrRGBChannels.AddGrowableCol( 1 )
		szrRGBChannels.SetFlexibleDirection( wx.BOTH )
		szrRGBChannels.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.lblRedChannel = wx.StaticText( fraRGBChannels.GetStaticBox(), wx.ID_ANY, u"R:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lblRedChannel.Wrap( -1 )

		szrRGBChannels.Add( self.lblRedChannel, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0 )

		self.sldRedChannel = wx.Slider( fraRGBChannels.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		szrRGBChannels.Add( self.sldRedChannel, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0 )

		self.spnRedChannel = wx.SpinCtrlDouble( fraRGBChannels.GetStaticBox(), wx.ID_ANY, u"0.0", wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, -1, 1, 0.000000, 0.01 )
		self.spnRedChannel.SetDigits( 4 )
		szrRGBChannels.Add( self.spnRedChannel, 0, wx.ALL|wx.EXPAND, 0 )

		self.lblGreenChannel = wx.StaticText( fraRGBChannels.GetStaticBox(), wx.ID_ANY, u"G:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lblGreenChannel.Wrap( -1 )

		szrRGBChannels.Add( self.lblGreenChannel, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0 )

		self.sldGreenChannel = wx.Slider( fraRGBChannels.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		szrRGBChannels.Add( self.sldGreenChannel, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0 )

		self.spnGreenChannel = wx.SpinCtrlDouble( fraRGBChannels.GetStaticBox(), wx.ID_ANY, u"0.0", wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, -1, 1, 0.000000, 0.01 )
		self.spnGreenChannel.SetDigits( 4 )
		szrRGBChannels.Add( self.spnGreenChannel, 0, wx.ALL|wx.EXPAND, 0 )

		self.lblBlueChannel = wx.StaticText( fraRGBChannels.GetStaticBox(), wx.ID_ANY, u"B:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lblBlueChannel.Wrap( -1 )

		szrRGBChannels.Add( self.lblBlueChannel, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0 )

		self.sldBlueChannel = wx.Slider( fraRGBChannels.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		szrRGBChannels.Add( self.sldBlueChannel, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 0 )

		self.spnBlueChannel = wx.SpinCtrlDouble( fraRGBChannels.GetStaticBox(), wx.ID_ANY, u"0.0", wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, -1, 1, 0, 0.01 )
		self.spnBlueChannel.SetDigits( 4 )
		szrRGBChannels.Add( self.spnBlueChannel, 0, wx.ALL|wx.EXPAND, 0 )


		fraRGBChannels.Add( szrRGBChannels, 1, wx.EXPAND, 5 )


		szrRGBPage.Add( fraRGBChannels, 0, wx.ALL|wx.EXPAND, 5 )

		szrLowerRGBPage = wx.BoxSizer( wx.HORIZONTAL )

		fraHexRGB = wx.StaticBoxSizer( wx.StaticBox( self.pnlRGBPage, wx.ID_ANY, _translate("Hex/HTML") ), wx.VERTICAL )

		self.txtHexRGB = wx.TextCtrl( fraHexRGB.GetStaticBox(), wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		fraHexRGB.Add( self.txtHexRGB, 0, wx.ALL|wx.EXPAND, 5 )


		szrLowerRGBPage.Add( fraHexRGB, 1, wx.ALL, 5 )

		fraRGBFormat = wx.StaticBoxSizer( wx.StaticBox( self.pnlRGBPage, wx.ID_ANY, _translate("RGB Format") ), wx.VERTICAL )

		self.rdoRGBModePsychoPy = wx.RadioButton( fraRGBFormat.GetStaticBox(), wx.ID_ANY, u"PsychoPy RGB [-1:1]", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.rdoRGBModePsychoPy.SetValue( True )
		fraRGBFormat.Add( self.rdoRGBModePsychoPy, 0, wx.ALL, 2 )

		self.rdoRGBModeNormalized = wx.RadioButton( fraRGBFormat.GetStaticBox(), wx.ID_ANY, u"Normalized RGB [0:1]", wx.DefaultPosition, wx.DefaultSize, 0 )
		fraRGBFormat.Add( self.rdoRGBModeNormalized, 0, wx.ALL, 2 )

		self.rdoRGBMode255 = wx.RadioButton( fraRGBFormat.GetStaticBox(), wx.ID_ANY, u"8-Bit RGB [0:255]", wx.DefaultPosition, wx.DefaultSize, 0 )
		fraRGBFormat.Add( self.rdoRGBMode255, 0, wx.ALL, 2 )


		szrLowerRGBPage.Add( fraRGBFormat, 1, wx.BOTTOM|wx.RIGHT|wx.TOP, 5 )


		szrRGBPage.Add( szrLowerRGBPage, 1, wx.EXPAND, 5 )


		self.pnlRGBPage.SetSizer( szrRGBPage )
		self.pnlRGBPage.Layout()
		szrRGBPage.Fit( self.pnlRGBPage )
		self.nbColorSelector.AddPage( self.pnlRGBPage, u"RGB", True )
		self.pnlHSVPage = wx.Panel( self.nbColorSelector, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		szrHSVPage = wx.BoxSizer( wx.VERTICAL )

		fraHSVChannels = wx.StaticBoxSizer( wx.StaticBox( self.pnlHSVPage, wx.ID_ANY, _translate(" HSV Channels ") ), wx.VERTICAL )

		szrHSVChannels = wx.FlexGridSizer( 3, 3, 5, 10 )
		szrHSVChannels.AddGrowableCol( 1 )
		szrHSVChannels.SetFlexibleDirection( wx.BOTH )
		szrHSVChannels.SetNonFlexibleGrowMode( wx.FLEX_GROWMODE_SPECIFIED )

		self.lblHueChannel = wx.StaticText( fraHSVChannels.GetStaticBox(), wx.ID_ANY, u"H:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lblHueChannel.Wrap( -1 )

		szrHSVChannels.Add( self.lblHueChannel, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0 )

		self.sldHueChannel = wx.Slider( fraHSVChannels.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		szrHSVChannels.Add( self.sldHueChannel, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0 )

		self.spnHueChannel = wx.SpinCtrlDouble( fraHSVChannels.GetStaticBox(), wx.ID_ANY, u"0.0", wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, 0, 360, 0, 1 )
		self.spnHueChannel.SetDigits( 0 )
		szrHSVChannels.Add( self.spnHueChannel, 0, wx.ALL|wx.EXPAND, 0 )

		self.lblSaturationChannel = wx.StaticText( fraHSVChannels.GetStaticBox(), wx.ID_ANY, u"S:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lblSaturationChannel.Wrap( -1 )

		szrHSVChannels.Add( self.lblSaturationChannel, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0 )

		self.sldStaturationChannel = wx.Slider( fraHSVChannels.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		szrHSVChannels.Add( self.sldStaturationChannel, 0, wx.ALL|wx.EXPAND|wx.ALIGN_CENTER_VERTICAL, 0 )

		self.spnSaturationChannel = wx.SpinCtrlDouble( fraHSVChannels.GetStaticBox(), wx.ID_ANY, u"0.0", wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, -1, 1, 0.000000, 0.01 )
		self.spnSaturationChannel.SetDigits( 4 )
		szrHSVChannels.Add( self.spnSaturationChannel, 0, wx.ALL|wx.EXPAND, 0 )

		self.lblValueChannel = wx.StaticText( fraHSVChannels.GetStaticBox(), wx.ID_ANY, u"V:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lblValueChannel.Wrap( -1 )

		szrHSVChannels.Add( self.lblValueChannel, 0, wx.ALL|wx.ALIGN_RIGHT|wx.ALIGN_CENTER_VERTICAL, 0 )

		self.sldValueChannel = wx.Slider( fraHSVChannels.GetStaticBox(), wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		szrHSVChannels.Add( self.sldValueChannel, 0, wx.ALL|wx.ALIGN_CENTER_VERTICAL|wx.EXPAND, 0 )

		self.spnValueChannel = wx.SpinCtrlDouble( fraHSVChannels.GetStaticBox(), wx.ID_ANY, u"0.0", wx.DefaultPosition, wx.DefaultSize, wx.SP_ARROW_KEYS, -1, 1, 0.000000, 0.001 )
		self.spnValueChannel.SetDigits( 4 )
		szrHSVChannels.Add( self.spnValueChannel, 0, wx.ALL|wx.EXPAND, 0 )


		fraHSVChannels.Add( szrHSVChannels, 0, wx.EXPAND, 5 )


		szrHSVPage.Add( fraHSVChannels, 0, wx.ALL|wx.EXPAND, 5 )


		self.pnlHSVPage.SetSizer( szrHSVPage )
		self.pnlHSVPage.Layout()
		szrHSVPage.Fit( self.pnlHSVPage )
		self.nbColorSelector.AddPage( self.pnlHSVPage, u"HSV", False )

		szrColorSelector.Add( self.nbColorSelector, 1, wx.EXPAND|wx.TOP, 5 )

		lstColorPresetsChoices = []
		self.lstColorPresets = wx.ListBox( self.pnlColorSelector, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, lstColorPresetsChoices, 0|wx.ALWAYS_SHOW_SB )
		self.lstColorPresets.SetMinSize( wx.Size( 140,-1 ) )

		szrColorSelector.Add( self.lstColorPresets, 1, wx.EXPAND|wx.LEFT|wx.RIGHT|wx.TOP, 5 )


		self.pnlColorSelector.SetSizer( szrColorSelector )
		self.pnlColorSelector.Layout()
		szrColorSelector.Fit( self.pnlColorSelector )
		szrMain.Add( self.pnlColorSelector, 1, wx.EXPAND, 0 )

		# Output space chooser
		self.pnlOutputSelector = wx.Panel(self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		szrOutputSelector = wx.BoxSizer(wx.HORIZONTAL)
		szrOutputSelector.AddStretchSpacer(1)

		self.lblOutputSpace = wx.StaticText( self.pnlOutputSelector, wx.ID_ANY, _translate("Output Space:"), wx.DefaultPosition, wx.DefaultSize, 0 )
		self.lblOutputSpace.Wrap( -1 )
		szrOutputSelector.Add( self.lblOutputSpace, 0, wx.ALIGN_CENTER_VERTICAL|wx.BOTTOM|wx.LEFT|wx.TOP, 0 )

		cboOutputSpaceChoices = [u"PsychoPy RGB (rgb)"]
		self.cboOutputSpace = wx.Choice(self.pnlOutputSelector, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize,
										cboOutputSpaceChoices, 0)
		self.cboOutputSpace.SetSelection(0)
		szrOutputSelector.Add(self.cboOutputSpace, 0, wx.ALL | wx.EXPAND, 5)

		self.cmdCopy = wx.Button( self.pnlOutputSelector, wx.ID_ANY, _translate("Copy"), wx.DefaultPosition, wx.DefaultSize, 0 )
		szrOutputSelector.Add( self.cmdCopy, 0, wx.BOTTOM|wx.LEFT|wx.TOP, 5 )

		self.cmdInsert = wx.Button( self.pnlOutputSelector, wx.ID_ANY, _translate("Insert"), wx.DefaultPosition, wx.DefaultSize, 0 )
		szrOutputSelector.Add( self.cmdInsert, 0, wx.ALL, 5 )

		self.pnlOutputSelector.SetSizer(szrOutputSelector)
		szrMain.Add(self.pnlOutputSelector, 0, wx.ALL | wx.EXPAND, 5)

		# Dialog buttons
		szrDlgButtons = self.CreateStdDialogButtonSizer(flags=wx.CANCEL)
		#self.cmdCancel = szrDlgButtons.AddButton(wx.ID_CANCEL)
		szrMain.Add( szrDlgButtons, 0, wx.ALL|wx.EXPAND, 5 )

		# Layout
		self.SetSizer( szrMain )
		self.Layout()

		self.Centre( wx.BOTH )

		# Connect Events
		self.Bind( wx.EVT_CLOSE, self.OnClose )
		self.sldRedChannel.Bind( wx.EVT_SCROLL, self.OnRedScroll )
		self.spnRedChannel.Bind( wx.EVT_SPINCTRLDOUBLE, self.OnRedSpin )
		self.spnRedChannel.Bind( wx.EVT_TEXT_ENTER, self.OnRedTextEnter )
		self.sldGreenChannel.Bind( wx.EVT_SCROLL, self.OnGreenScroll )
		self.spnGreenChannel.Bind( wx.EVT_SPINCTRLDOUBLE, self.OnGreenSpin )
		self.spnGreenChannel.Bind( wx.EVT_TEXT_ENTER, self.OnGreenTextEnter )
		self.sldBlueChannel.Bind( wx.EVT_SCROLL, self.OnBlueScroll )
		self.spnBlueChannel.Bind( wx.EVT_SPINCTRLDOUBLE, self.OnBlueSpin )
		self.spnBlueChannel.Bind( wx.EVT_TEXT_ENTER, self.OnBlueTextEnter )
		self.txtHexRGB.Bind( wx.EVT_KEY_DOWN, self.OnHexRGBKeyDown )
		self.rdoRGBModePsychoPy.Bind( wx.EVT_RADIOBUTTON, self.OnRGBModePsychoPy )
		self.rdoRGBModeNormalized.Bind( wx.EVT_RADIOBUTTON, self.OnRGBModeNormalized )
		self.rdoRGBMode255.Bind( wx.EVT_RADIOBUTTON, self.OnRGBMode255 )
		self.sldHueChannel.Bind( wx.EVT_SCROLL, self.OnHueScroll )
		self.spnHueChannel.Bind( wx.EVT_SPINCTRLDOUBLE, self.OnHueSpin )
		self.spnHueChannel.Bind( wx.EVT_TEXT_ENTER, self.OnHueTextEnter )
		self.sldStaturationChannel.Bind( wx.EVT_SCROLL, self.OnSaturationScroll )
		self.spnSaturationChannel.Bind( wx.EVT_SPINCTRLDOUBLE, self.OnSaturationSpin )
		self.spnSaturationChannel.Bind( wx.EVT_TEXT_ENTER, self.OnSaturationTextEnter )
		self.sldValueChannel.Bind( wx.EVT_SCROLL, self.OnValueScroll )
		self.spnValueChannel.Bind( wx.EVT_SPINCTRLDOUBLE, self.OnValueSpin )
		self.spnValueChannel.Bind( wx.EVT_TEXT_ENTER, self.OnValueTextEnter )
		self.lstColorPresets.Bind( wx.EVT_LISTBOX, self.OnPresetSelect )
		self.cmdCopy.Bind( wx.EVT_BUTTON, self.OnCopy )
		self.cmdInsert.Bind( wx.EVT_BUTTON, self.OnInsert )

	def __del__( self ):
		pass


	# Virtual event handlers, override them in your derived class
	def OnClose( self, event ):
		event.Skip()

	def OnRedScroll( self, event ):
		event.Skip()

	def OnRedSpin( self, event ):
		event.Skip()

	def OnRedTextEnter( self, event ):
		event.Skip()

	def OnGreenScroll( self, event ):
		event.Skip()

	def OnGreenSpin( self, event ):
		event.Skip()

	def OnGreenTextEnter( self, event ):
		event.Skip()

	def OnBlueScroll( self, event ):
		event.Skip()

	def OnBlueSpin( self, event ):
		event.Skip()

	def OnBlueTextEnter( self, event ):
		event.Skip()

	def OnHexRGBKeyDown( self, event ):
		event.Skip()

	def OnRGBModePsychoPy( self, event ):
		event.Skip()

	def OnRGBModeNormalized( self, event ):
		event.Skip()

	def OnRGBMode255( self, event ):
		event.Skip()

	def OnHueScroll( self, event ):
		event.Skip()

	def OnHueSpin( self, event ):
		event.Skip()

	def OnHueTextEnter( self, event ):
		event.Skip()

	def OnSaturationScroll( self, event ):
		event.Skip()

	def OnSaturationSpin( self, event ):
		event.Skip()

	def OnSaturationTextEnter( self, event ):
		event.Skip()

	def OnValueScroll( self, event ):
		event.Skip()

	def OnValueSpin( self, event ):
		event.Skip()

	def OnValueTextEnter( self, event ):
		event.Skip()

	def OnPresetSelect( self, event ):
		event.Skip()

	def OnCancel( self, event ):
		event.Skip()

	def OnCopy( self, event ):
		event.Skip()

	def OnInsert( self, event ):
		event.Skip()


