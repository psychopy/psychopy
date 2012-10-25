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
import obci_connection
from psychopy.app.builder.amp_launcher.retriever import AmplifierInfo
import time

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
            self.amp_list.SetColumnWidth(column, wx.LIST_AUTOSIZE_USEHEADER)

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
                parent, size=(760, 640), title="Amp Launcher", style=wx.DEFAULT_DIALOG_STYLE)
        self.connection = obci_connection.OBCIConnection(("192.168.0.104", 12012))
        if not retriever:
            retriever = AmpListRetriever(self.connection)
        self.init_info(retriever)
        self.init_panels()
        self.init_sizer()
        self.init_buttons()
        #self.disable_editing()

    def init_info(self, retriever):
        self.retriever = retriever
        try:
            self.amp_info = self.retriever.fetch_amp_list()
        except Exception as e:
            self.amp_info = AmplifierInfo()

    def init_panels(self):
        self.amp_list_panel = AmpListPanel(self, self.amp_info)
        self.amp_config = AmpConfigPanel(self)
        self.Bind(wx.EVT_LIST_ITEM_SELECTED, self.select_amplifier, self.amp_list_panel.amp_list)
        self.Bind(wx.grid.EVT_GRID_CELL_CHANGE, self.channel_update)

    def init_buttons(self):
        self.Bind(wx.EVT_BUTTON, self.run_click, id=wx.ID_OK)
        self.FindWindowById(wx.ID_OK).Disable()

    def init_sizer(self):
        sizer = wx.BoxSizer(wx.VERTICAL)
        flags0 = wx.SizerFlags().Border(wx.ALL, 12)
        flags1 = wx.SizerFlags().Border(wx.LEFT | wx.RIGHT | wx.BOTTOM, 12)
        sizer.AddF(self.amp_list_panel, flags0.Proportion(1).Expand())
        sizer.AddF(self.amp_config, flags1.Proportion(1).Expand())
        #sizer.Add(self.saving_config, proportion=0, flag=wx.EXPAND | wx.ALL, border=8)
        sizer.AddF(self.CreateButtonSizer(wx.OK | wx.CANCEL), flags1.Proportion(0))
        self.SetSizer(sizer)

    def channel_update(self, event):
        if self.amp_config.Validate():
            self.FindWindowById(wx.ID_OK).Enable()
        else:
            self.FindWindowById(wx.ID_OK).Disable()

    def select_amplifier(self, event):
        index = event.GetIndex()
        amp_entry = self.amp_info.get_entry(index)
        self.amp_config.select_amplifier(amp_entry)

    def disable_editing(self):
        self.amp_list_panel.disable_editing()
        self.amp_config.Disable()
        self.launch_button.Disable()

    def get_experiment_contact(self):
        return self.experiment_contact

    def get_scenario(self):
        exec_path = self.amp_config.get_exec_file()
        sampling_rate = self.amp_config.get_param("sampling_rate") or 16
        active_channels = self.amp_config.get_active_channels()
        channel_names = self.amp_config.get_channel_names()
        amplifier_peer = {
            'config': {
                'config_sources': {},
                'external_params': {},
                'launch_dependencies': {},
                'local_params': {
                    'active_channels': active_channels,
                    'channel_names': channel_names,
                    'sampling_rate': str(sampling_rate)
                }
            },
            'path': exec_path
        }
        tag_saver = {
            'config': {},
            'config_sources': {'signal_saver': 'signal_saver'},
             'launch_dependencies': {'signal_saver': 'signal_saver'},
            'path': 'acquisition/tag_saver_peer.py'
        }
        info_saver = {
            'config': {},
            'config_sources': {
                'amplifier': 'amplifier',
                'signal_saver': 'signal_saver'
            },
            'launch_dependencies': {
                'amplifier': 'amplifier',
                'signal_saver': 'signal_saver'
            },
            'path': 'acquisition/info_saver_peer.py'
        }
        signal_saver = {
            'config': {
                'config_sources': {'amplifier': ''},
                'external_params': {},
                'launch_dependencies': {'amplifier': ''},
                'local_params': {
                    'save_file_name': 'psychopy_signal_' + str(int(time.time()))
                }
            },
            'config_sources': {'amplifier': 'amplifier'},
            'launch_dependencies': {'amplifier': 'amplifier'},
            'path': 'acquisition/signal_saver_peer.py'
        }
        peers = {
            'amplifier': amplifier_peer,
            'tag_saver': tag_saver,
            'info_save': info_saver,
            'signal_saver': signal_saver,
            'scenario_dir': '',
            'config_server': {'config':{}, 'path':'obci_control/peer/config_server.py'},
            'mx': {'config': {}, u'path': 'multiplexer-install/bin/mxcontrol'}
        }
        return {'peers': peers}

    def run_click(self, event):
        if not self.amp_config.Validate():
            return
        server = self.amp_config.get_server()
        launch_file_path = self.amp_config.get_launch_file()
        # TODO read port from server list
        client = obci_connection.ObciClient("tcp://" + server + ":54654")
        experiment = client.create_experiment("Psychopy Experiment")
        experiment_address = experiment['rep_addrs'][-1]
        experiment_manager = obci_connection.ObciExperimentClient(experiment_address)
        scenario = self.get_scenario()
        experiment_manager.set_experiment_scenario(launch_file_path, scenario)
        experiment_manager.start_experiment()
        experiment_manager.close()
        client.uuid = experiment["uuid"]
        self.experiment_contact = client
        event.Skip()

if __name__ == "__main__":
    app = wx.App()
    dialog = AmpLauncherDialog(None)
    dialog.Show()
    app.SetExitOnFrameDelete(True)
    app.SetTopWindow(dialog)
    app.MainLoop()
