'''
Created on 27-08-2012

@author: Piotr Iwaniuk
'''

import wx.grid
from StringIO import StringIO

class ChannelsPanel(wx.Panel):
    def __init__(self, parent):
        super(ChannelsPanel, self).__init__(parent)
        self.init_list()
        self.init_sizer()

    def init_list(self):
        self.channel_grid = wx.grid.Grid(self)
        self.channel_grid.CreateGrid(0, 2)
        self.channel_grid.SetColLabelValue(0, "label")
        self.channel_grid.SetColLabelValue(1, "selected")
        self.channel_grid.SetColFormatBool(1)
        self.grid_rows = 0;

    def init_sizer(self):
        sizer = wx.BoxSizer()
        sizer.Add(self.channel_grid, proportion=1, flag=wx.EXPAND, border=8)
        self.SetSizer(sizer)

    def fill(self, channels):
        self.channel_grid.BeginBatch()
        pos = 0
        self.channel_grid.DeleteRows(0, self.grid_rows)
        for channel_entry in channels:
            self.channel_grid.InsertRows(pos)
            self.channel_grid.SetRowLabelValue(pos, str(pos))
            self.channel_grid.SetCellValue(pos, 0, str(channel_entry))
            pos += 1
        self.grid_rows = pos
        self.channel_grid.SetRowLabelSize(wx.grid.GRID_AUTOSIZE)
        self.channel_grid.SetColSize(0, 300)
        self.channel_grid.EndBatch()
    
    def get_channel_list(self, info_fun):
        """
        Build semicolon-separated list of values corresponding with selected channels.
        """
        ret = StringIO()
        if self.channel_grid.GetCellValue(0, 1):
            ret.write(info_fun(0))
        for pos in xrange(1, self.channel_grid.GetNumberRows()):
            if self.channel_grid.GetCellValue(pos, 1):
                ret.write(";")
                ret.write(info_fun(pos))
        return ret.getvalue()
    
    def get_active_channels(self):
        """
        Build semicolon-separated list of channels selected to record during experiment.
        """
        return self.get_channel_list(lambda pos: str(pos))
    
    def get_channel_names(self):
        """
        Build a list of names of selected channels.
        """
        return self.get_channel_list(lambda pos: self.channel_grid.GetCellValue(pos, 0))


class ParametersPanel(wx.Panel):
    def __init__(self, parent):
        super(ParametersPanel, self).__init__(parent)
        self.init_list()
        self.init_sizer()

    def init_list(self):
        self.param_grid = wx.grid.Grid(self)
        self.param_grid.CreateGrid(0, 1)
        self.param_grid.SetColLabelValue(0, "")

    def init_sizer(self):
        sizer = wx.BoxSizer()
        sizer.Add(self.param_grid, proportion=1, flag=wx.EXPAND, border=8)
        self.SetSizer(sizer)
    
    def fill(self, parameters):
        self.param_grid.BeginBatch()
        self.param_grid.DeleteRows(0, self.param_grid.GetNumberRows())
        pos = 0
        for param_entry in parameters:
            self.param_grid.InsertRows(pos)
            self.param_grid.SetRowLabelValue(pos, param_entry[0])
            self.param_grid.SetCellValue(pos, 0, param_entry[1])
            pos += 1
        self.param_grid.EndBatch()
    
    def get_param(self, param_name):
        # TODO ;-)
        return "128"


class AmpConfigPanel(wx.Panel):
    """A panel control with configuration of a selected amp."""
    def __init__(self, parent):
        super(AmpConfigPanel, self).__init__(parent, style=wx.EXPAND)

        tabs = wx.Notebook(self, style=wx.BK_DEFAULT)
        self.amp_entry = None
        self.channels_panel = ChannelsPanel(tabs)
        self.parameters_panel = ParametersPanel(tabs)
        tabs.AddPage(self.channels_panel, "channels")
        tabs.AddPage(self.parameters_panel, "properties")

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(tabs, proportion=1, flag=wx.EXPAND, border=8)
        self.SetSizer(sizer)

    def select_amplifier(self, amp_entry):
        # fill channel & parameter lists
        self.amp_entry = amp_entry
        self.channels_panel.fill(amp_entry.get_channels())
        self.parameters_panel.fill(amp_entry.get_parameters())
    
    def get_active_channels(self):
        return self.channels_panel.get_active_channels()
    
    def get_channel_names(self):
        return self.channels_panel.get_channel_names()
    
    def get_param(self, param_name):
        return self.parameters_panel.get_param(param_name)
    
    def get_launch_file(self):
        return self.amp_entry.get_launch_file()
    
    def get_server(self):
        return self.amp_entry.get_server()