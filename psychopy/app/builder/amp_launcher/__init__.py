"""
Module contains amp launcher feature.
"""

import wx
import wx.grid
from retriever import AmpListRetriever
from psychopy.app.builder.amp_launcher.amplifier_panels import ChannelsPanel,\
    ParametersPanel, AmpConfigPanel
from obci.obci_control.common.message import OBCIMessageTool
from obci.obci_control.launcher import launcher_messages
from psychopy.app.builder.amp_launcher.obci_connection import OBCIConnection

class AmpListPanel(wx.Panel):
    """A panel control with a refreshable list of amplifiers"""
    def __init__(self, parent, amp_info):
        super(AmpListPanel, self).__init__(parent, wx.ID_ANY)
        self.amp_info = amp_info
        self.init_controls()         
        self.init_sizer()

    def init_controls(self):
        self.label = wx.StaticText(self, wx.ID_ANY, "Amplifier list:")
        #self.refresh_button = wx.Button(self, wx.ID_ANY, label="refresh")
        #self.refresh_button.SetSizeWH(2, 2)
        self.amp_list = wx.ListView(self, wx.ID_ANY)
        self.amp_list.InsertColumn(0, "address")
        self.amp_list.InsertColumn(1, "experiment")
        self.amp_list.InsertColumn(2, "amplifier")
        self.amp_list.InsertColumn(3, "status")
        for entry in self.amp_info.get_summary():
            self.amp_list.Append(entry)
        for column in xrange(4):
            self.amp_list.SetColumnWidth(column, wx.LIST_AUTOSIZE)

    def disable_editing(self):
        self.refresh_button.Hide()
        self.amp_list.Disable()

    def init_sizer(self):
        sizer = wx.GridBagSizer()
        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(1)
        sizer.Add(self.label, (0, 0))
        #sizer.Add(self.refresh_button, (0, 1))
        sizer.Add(self.amp_list, (1, 0), (1, 2), flag=wx.EXPAND, border=8)
        self.SetSizer(sizer)


class SavingConfigPanel(wx.Panel):
    def __init__(self, parent):
        super(SavingConfigPanel, self).__init__(parent)
        self.init_controls()
        self.init_sizer()

    def init_controls(self):
        self.do_save = wx.CheckBox(self, label="save amplifier output to:")
        self.save_path = wx.TextCtrl(self)
        self.save_path.SetValue("/tmp")
        self.do_trig = wx.CheckBox(self, label="send trigs to:")
        self.trig_path = wx.TextCtrl(self)
        self.trig_path.SetValue("/dev/ttyUSB0")
        self.do_send_tags = wx.CheckBox(self, label="send experiment tags to the server")
        self.do_save_tags = wx.CheckBox(self, label="save experiment tags locally")
    
    def init_sizer(self):
        sizer = wx.GridBagSizer()
        sizer.AddGrowableCol(1)

        sizer.Add(self.do_save, (0, 0), border=4)
        sizer.Add(self.save_path, (0, 1), flag=wx.EXPAND, border=4)
        sizer.Add(self.do_trig, (1, 0), border=4)
        sizer.Add(self.trig_path, (1, 1), flag=wx.EXPAND, border=8)
        
        sizer.Add(self.do_send_tags, (2, 0), (1, 2), border=8)
        sizer.Add(self.do_save_tags, (3, 0), (1, 2), border=8)
        
        self.SetSizer(sizer)


class AmpLauncherDialog(wx.Dialog):
    """Main amplifier laucher dialog."""
    def __init__(self, parent, retriever = None):
        super(AmpLauncherDialog, self).__init__(
                parent, size=(760, 720), title="Amp Launcher", style=wx.DEFAULT_DIALOG_STYLE)
        self.connection = OBCIConnection(("192.168.50.104", 12012))
        if not retriever:
            retriever = AmpListRetriever(self.connection)
        self.init_info(retriever)
        self.init_panels()
        self.init_buttons()
        self.init_sizer()
        #self.disable_editing()

    def init_info(self, retriever):
        self.retriever = retriever
        self.amp_info = self.retriever.fetch_amp_list()
    
    def init_panels(self):
        self.amp_list_panel = AmpListPanel(self, self.amp_info)
        self.amp_config = AmpConfigPanel(self)
        self.saving_config = SavingConfigPanel(self)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.select_amplifier, self.amp_list_panel.amp_list)

    def init_buttons(self):
        self.button_panel = wx.Panel(self)
        self.close_button = wx.Button(self.button_panel, label="close")
        self.launch_button = wx.Button(self.button_panel, label="run")
        self.Bind(wx.EVT_BUTTON, self.close_click, self.close_button)
        self.Bind(wx.EVT_BUTTON, self.run_click, self.launch_button)
        sizer = wx.BoxSizer(wx.HORIZONTAL)
        sizer.Add(self.close_button, proportion=0, flag=wx.ALIGN_RIGHT, border=8)
        sizer.Add(self.launch_button, proportion=0, flag=wx.ALIGN_RIGHT, border=8)
        self.button_panel.SetSizer(sizer)

    def init_sizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        sizer.Add(self.amp_list_panel, proportion=1, flag=wx.EXPAND, border=8)
        sizer.Add(self.amp_config, proportion=1, flag=wx.EXPAND, border=8)
        sizer.Add(self.saving_config, proportion=0, flag=wx.EXPAND, border=8)
        sizer.Add(self.button_panel, proportion=0, flag=wx.EXPAND | wx.ALIGN_RIGHT, border=8)
        self.SetSizer(sizer)
    
    def select_amplifier(self, event):
        index = event.GetIndex()
        amp_entry = self.amp_info.get_entry(index)
        self.amp_config.select_amplifier(amp_entry)
    
    def disable_editing(self):
        self.amp_list_panel.disable_editing()
        self.amp_config.Disable()
        self.launch_button.Disable()
    
    def close_click(self, event):
        self.experiment_contact = None
        self.EndModal(1)
        
    def get_experiment_contact(self):
        return self.experiment_contact
    
    def run_click(self, event):
        server = self.amp_config.get_server()
        sampling_rate = self.amp_config.get_param("sampling_rate")
        active_channels = self.amp_config.get_active_channels()
        channel_names = self.amp_config.get_channel_names()
        launch_file = self.amp_config.get_launch_file()
        name = "Psychopy Experiment"
        amplifier_params = {
            "channel_names": channel_names, "active_channels": active_channels,
            "sampling_rate": sampling_rate, "additional_params": {}
        }
        remote_connection = OBCIConnection((server, 12012))
        contact_uuid = remote_connection.start_eeg_signal(name, launch_file, amplifier_params)
        remote_connection.get_experiment_contact(contact_uuid)
        self.experiment_contact = remote_connection
        self.EndModal(0)

if __name__ == "__main__":
    app = wx.App()
    dialog = AmpLauncherDialog(None)
    dialog.Show()
    app.SetExitOnFrameDelete(True)
    app.SetTopWindow(dialog)
    app.MainLoop()
