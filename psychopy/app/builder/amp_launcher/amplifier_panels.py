'''
Created on 27-08-2012

@author: Piotr Iwaniuk
'''

import wx.grid
from StringIO import StringIO
from psychopy.app.builder.amp_launcher import amp_settings
from wx._core import EVT_BUTTON

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
        col_attr = wx.grid.GridCellAttr()
        col_attr.SetEditor(wx.grid.GridCellBoolEditor())
        col_attr.SetRenderer(wx.grid.GridCellBoolRenderer())
        self.channel_grid.SetColAttr(1, col_attr)
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
    
    def build_channel_list(self, info_fun):
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
        return self.build_channel_list(lambda pos: str(pos))
    
    def get_channel_names(self):
        """
        Build a list of names of selected channels.
        """
        return self.build_channel_list(lambda pos: self.channel_grid.GetCellValue(pos, 0))
    
    def get_preset_channels(self):
        """
        Build a dict which is used to serialize a preset.
        """
        channel_names = []
        active_channels = set()
        for pos in xrange(0, self.channel_grid.GetNumberRows()):
            channel_names.append(self.channel_grid.GetCellValue(pos, 0))
            if self.channel_grid.GetCellValue(pos, 1):
                active_channels.add(pos)
        return {"channelNames": channel_names, "activeChannels": active_channels}

    
    def set_preset_channels(self, channel_names, active_channels):
        for pos in xrange(0, self.channel_grid.GetNumberRows()):
            if pos < len(channel_names):
                self.channel_grid.SetCellValue(pos, 0, channel_names[pos])
            if pos in active_channels:
                active = "1"
            else:
                active = ""
            self.channel_grid.SetCellValue(pos, 1, active)


class ParametersPanel(wx.Panel):
    def __init__(self, parent):
        super(ParametersPanel, self).__init__(parent)
        self.init_controls()
        self.init_sizer()

    def init_controls(self):
        self.sampling_rate_label = wx.StaticText(self, label="sampling rate")
        self.sampling_rate = wx.TextCtrl(self, value="128")

    def init_sizer(self):
        sizer = wx.GridBagSizer()
        sizer.AddGrowableCol(1)
        
        sizer.Add(self.sampling_rate_label, (0,0), flag=wx.EXPAND)
        sizer.Add(self.sampling_rate, (0, 1), flag=wx.EXPAND)
        
        self.SetSizer(sizer)
    
    def fill(self, parameters):
        pass
    
    def get_param(self, param_name):
        if param_name == "samplingRate":
            return self.sampling_rate.GetValue()
        else:
            return None
    
    def get_preset_params(self):
        return {"params": {"samplingRate": self.get_param("samplingRate")}}

    
    def set_preset_params(self, params):
        self.sampling_rate.SetValue(str(params["samplingRate"]))


class PresetsPanel(wx.Panel):
    """
    A set of controls for controlling amp presets.
    """
    def __init__(self, parent):
        wx.Panel.__init__(self, parent)
        self.preset_list = wx.ComboBox(self)
        self.Bind(wx.EVT_TEXT, self.on_name_update, self.preset_list)
        sizer = wx.BoxSizer()
        sizer.Add(self.preset_list, proportion=1, flag=wx.EXPAND)
        buttons = [("load", self.on_load_click), ("save", self.on_add_click), ("remove", self.on_remove_click)]
        self.buttons = {}
        for (label, handler) in buttons:
            self.buttons[label] = wx.Button(self, label=label)
            sizer.Add(self.buttons[label], flag=wx.EXPAND)
            self.Bind(EVT_BUTTON, handler, self.buttons[label])
        self.SetSizer(sizer)
        self.load_presets()
    
    def load_presets(self):
        """
        Load fresh preset data from preset manager.
        """
        self.preset_manager = amp_settings.PresetManager.get_instance()
        preset_names = self.preset_manager.get_preset_names()
        self.preset_list.Clear()
        self.preset_list.AppendItems(preset_names)
        self.update_buttons()

    def get_preset_name(self):
        return self.preset_list.GetValue()

    def on_add_click(self, event):
        """
        Handler for the add button.
        @param event: associated event
        """
        preset = self.GetParent().get_preset()
        name = self.get_preset_name()
        self.preset_manager.add_preset(name, preset)
        self.preset_manager.save_to_file()
        self.load_presets()
    
    def clear_name(self):
        """
        Set an empty name in preset list.
        """
        self.preset_list.SetValue("")
        self.update_buttons()
    
    def on_remove_click(self, event):
        """
        Handler for the remove button.
        @param event: associated event
        """
        name = self.get_preset_name()
        self.preset_manager.remove_preset(name)
        self.preset_manager.save_to_file()
        self.load_presets()
        self.clear_name()
    
    def on_load_click(self, event):
        """
        Handler for the load button.
        @param event: associated event
        """
        name = self.get_preset_name()
        preset = self.preset_manager.get_preset(name)
        self.GetParent().load_preset(preset)
    
    def on_name_update(self, event):
        self.update_buttons()
    
    def update_buttons(self):
        if len(self.get_preset_name()) == 0:
            self.buttons["load"].Disable()
            self.buttons["save"].Disable()
            self.buttons["remove"].Disable()
        elif self.get_preset_name() in self.preset_manager.get_preset_names():
            self.buttons["load"].Enable()
            self.buttons["save"].Disable()
            self.buttons["remove"].Enable()
        else:
            self.buttons["load"].Disable()
            self.buttons["save"].Enable()
            self.buttons["remove"].Disable()


class AmpConfigPanel(wx.Panel):
    """A panel control with configuration of a selected amp."""
    def __init__(self, parent):
        super(AmpConfigPanel, self).__init__(parent, style=wx.EXPAND)

        self.amp_entry = None
        self.channels_panel = ChannelsPanel(self)
        self.parameters_panel = ParametersPanel(self)
        self.presets_panel = PresetsPanel(self)

        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.channels_panel, proportion=1, flag=wx.EXPAND, border=2)
        sizer.Add(self.parameters_panel, flag=wx.EXPAND, border=2)
        sizer.Add(self.presets_panel, flag=wx.EXPAND, border=2)
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

    def get_preset(self):
        """
        Extract a preset from the form.
        """ 
        preset_dict = {}
        preset_dict.update(self.channels_panel.get_preset_channels())
        preset_dict.update(self.parameters_panel.get_preset_params())
        preset = amp_settings.Preset(preset_dict)
        return preset
    
    def load_preset(self, preset):
        """
        Use a preset in the form.
        """
        self.channels_panel.set_preset_channels(preset.get_channel_names(), preset.get_active_channels())
        self.parameters_panel.set_preset_params(preset.get_parameters())
