"""
Module contains amp launcher feature.
"""

import wx
import wx.grid
from retriever import AmpListRetriever
from psychopy.app.builder.amp_launcher.amplifier_panels import ChannelsPanel,\
    ParametersPanel, AmpConfigPanel
from obci.control.common.message import OBCIMessageTool
from obci.control.launcher import launcher_messages
import obci_connection
from psychopy.app.builder.amp_launcher import retriever
import os.path
import zmq
import json
import threading
from wx.lib import throbber
import time


class AmpListPanel(wx.Panel):
    """A panel control with a refreshable list of amplifiers"""
    COLUMN_PROPORTIONS = [1, 2, 2, 1]
    def __init__(self, parent):
        super(AmpListPanel, self).__init__(parent, wx.ID_ANY)
        self.amp_info = None
        self.proportions_sum = reduce(lambda x, y: x + y, self.COLUMN_PROPORTIONS)
        self.init_controls()
        self.init_sizer()

    def init_controls(self):
        self.label = wx.StaticText(self, wx.ID_ANY, "Amplifier list:")
        #self.refresh_button = wx.Button(self, wx.ID_ANY, label="refresh")
        #self.refresh_button.SetSizeWH(2, 2)
        throbber_bitmap = wx.ArtProvider.GetBitmap("amp-launcher-throbber", wx.ART_OTHER)
        self.throbber = throbber.Throbber(self, -1, bitmap=throbber_bitmap, frames=4, frameWidth=43)
        self.amp_list = wx.ListView(self, wx.ID_ANY)
        self.amp_list.InsertColumn(0, "address")
        self.amp_list.InsertColumn(1, "experiment")
        self.amp_list.InsertColumn(2, "amplifier")
        self.amp_list.InsertColumn(3, "status")
        self.refresh_amp_info()

    def lock_list(self):
        self.amp_list.Disable()
        self.throbber.Start()
    
    def unlock_list(self):
        self.amp_list.Enable()
        self.throbber.Rest()

    def init_sizer(self):
        sizer = wx.GridBagSizer()
        sizer.AddGrowableCol(0)
        sizer.AddGrowableRow(1)
        sizer.Add(self.label, (0, 0))
        sizer.Add(self.throbber, (0, 1))
        #sizer.Add(self.refresh_button, (0, 1))
        sizer.Add(self.amp_list, (1, 0), (1, 2), flag=wx.EXPAND, border=8)
        self.SetSizer(sizer)
        
    def set_amp_info(self, amp_info):
        self.amp_info = amp_info
        self.refresh_amp_info()

    def refresh_amp_info(self):
        if self.amp_info:
            for pos, entry in enumerate(self.amp_info.get_summary()):
                self.amp_list.InsertStringItem(pos, entry[0][1])
                self.amp_list.SetStringItem(pos, 1, entry[1])
                self.amp_list.SetStringItem(pos, 2, entry[2])
                self.amp_list.SetStringItem(pos, 3, entry[3])
            for column in xrange(4):
                min_width = self.GetClientSize().width * self.COLUMN_PROPORTIONS[column] / self.proportions_sum
                self.amp_list.SetColumnWidth(column, wx.LIST_AUTOSIZE)
                self.amp_list.SetColumnWidth(column, max(min_width, self.amp_list.GetColumnWidth(column)))


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
    def __init__(self, parent, retriever_instance=None):
        super(AmpLauncherDialog, self).__init__(
                parent, size=(760, 640), title="Amp Launcher", style=wx.DEFAULT_DIALOG_STYLE)
        self.amp_info = None
        self.old_index = None
        self.connection = obci_connection.OBCIConnection(("127.0.0.1", 12012))
        self.retriever = retriever_instance or AmpListRetriever(self.connection)
        self.retriever_thread = threading.Thread(group=None, target=self.init_info, name="retriever-thread")
        self.init_panels()
        self.init_sizer()
        self.init_buttons()
        self.Bind(retriever.EVT_RETRIEVER_STARTED, self.retriever_started)
        self.Bind(retriever.EVT_RETRIEVER_FINISHED, self.retriever_finished)
        self.retriever_thread.start()

    def init_info(self):
        wx.PostEvent(self, retriever.RetrieverStartedEvent())
        try:
            amp_info = self.retriever.fetch_amp_list()
            print amp_info.amplifier_list
        except Exception as _:
            #wx.MessageBox("Failed to fetch a list of amplifiers:\n" + str(e), "Amp Launcher", wx.ICON_WARNING)
            amp_info = retriever.AmplifierInfo() # empty amp list
        wx.PostEvent(self, retriever.RetrieverFinishedEvent(amp_info=amp_info))

    def retriever_started(self, event):
        self.amp_list_panel.lock_list()
    
    def retriever_finished(self, event):
        self.amp_info = event.amp_info
        self.amp_list_panel.set_amp_info(event.amp_info)
        self.amp_list_panel.unlock_list()

    def init_panels(self):
        self.amp_list_panel = AmpListPanel(self)
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
        sizer.AddF(self.CreateButtonSizer(wx.OK | wx.CANCEL), flags1.Proportion(0))
        self.SetSizer(sizer)

    def channel_update(self, event):
        if self.amp_config.Validate():
            self.FindWindowById(wx.ID_OK).Enable()
        else:
            self.FindWindowById(wx.ID_OK).Disable()

    def select_amplifier(self, event):
        new_index = event.GetIndex()
        if new_index != self.old_index:
            amp_entry = self.amp_info.get_entry(new_index)
            self.amp_config.select_amplifier(amp_entry)
            self.amp_config.presets_panel.on_name_select(None) #reload preset if it is active
            self.old_index =  new_index

    def disable_editing(self):
        self.amp_list_panel.disable_editing()
        self.amp_config.Disable()
        self.launch_button.Disable()

    def get_experiment_contact(self):
        return self.experiment_contact

    def get_scenario(self):
        exec_path = self.amp_config.get_exec_file()
        sampling_rate = self.amp_config.get_param("sampling_rate")
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
                    'sampling_rate': sampling_rate,
                    "console_log_level": "info",
                    "file_log_level": "debug",
                    "mx_log_level": "info",
                    "log_dir": "~/.obci/logs"
                }
            },
            'path': exec_path
        }
        local_log_params = {                    
            "console_log_level": "info",
            "file_log_level": "debug",
            "mx_log_level": "info",
            "log_dir": "~/.obci/logs"
        }
        peers = {
            'amplifier': amplifier_peer,
            'scenario_dir': '',
            'config_server': {'config':{"local_params": local_log_params, 'external_params': {}, 'config_sources': {}, "launch_dependencies": {}}, 'path':'control/peer/config_server.py'},
            'mx': {'config': {'external_params': {}, 'config_sources': {}, 'launch_dependencies': {}, 'local_params': {}}, u'path': 'multiplexer-install/bin/mxcontrol'}
        }
        if self.GetParent().exp.settings.params['saveSignal'].val:
            save_file_name = 'psychopy_signal_' + str(int(time.time()))
            save_file_dir = self.GetParent().exp.settings.params['obciDataDirectory'].val
            print save_file_name, save_file_dir
            tag_saver = {
                'config': {
                    "local_params": local_log_params,
                    'external_params': {},
                    'config_sources': {'signal_saver': ''},
                    'launch_dependencies': {'signal_saver': ''}
                },
                'config_sources': {'signal_saver': 'signal_saver'},
                'launch_dependencies': {'signal_saver': 'signal_saver'},
                'path': 'acquisition/tag_saver_peer.py'
            }
            info_saver = {
                'config': {
                    "local_params": local_log_params,
                    'external_params': {},
                    'config_sources': {'amplifier': '', 'signal_saver': ''},
                    'launch_dependencies': {'amplifier': '', 'signal_saver': ''}
                },
                'config_sources': {'amplifier': 'amplifier', 'signal_saver': 'signal_saver'},
                'launch_dependencies': {'amplifier': 'amplifier', 'signal_saver': 'signal_saver'},
                'path': 'acquisition/info_saver_peer.py'
            }
            signal_saver = {
                'config': {
                    'config_sources': {'amplifier': ''},
                    'external_params': {},
                    'launch_dependencies': {'amplifier': ''},
                    'local_params': {
                        'save_file_name': save_file_name,
                        'save_file_path': save_file_dir,
                        "console_log_level": "info",
                        "file_log_level": "debug",
                        "mx_log_level": "info",
                        "log_dir": "~/.obci/logs"
                    }
                },
                'config_sources': {'amplifier': 'amplifier'},
                'launch_dependencies': {'amplifier': 'amplifier'},
                'path': 'acquisition/signal_saver_peer.py'
            }
            peers['tag_saver'] = tag_saver
            peers['info_saver'] = info_saver
            peers['signal_saver'] = signal_saver
        return {'peers': peers}


    def wait_for_status_change(self, experiment_manager):
        context = zmq.Context().instance()
        sub_socket = context.socket(zmq.SUB)
        sub_socket.connect("tcp://" + self.amp_config.get_server() + ":34234")
        sub_socket.setsockopt(zmq.SUBSCRIBE, "")
        experiment_manager.start_experiment()
        while True:
            published = json.loads(sub_socket.recv())
            if published.get("peers") and published['peers'].has_key("mx"):
                return
    
    
    def run_click(self, event):
        if not self.amp_config.Validate():
            return
        launch_file_path = self.amp_config.get_launch_file()
        # TODO read port from server list
        client = obci_connection.ObciClient("tcp://" + self.amp_config.get_server() + ":54654")
        experiment = client.create_experiment("Psychopy Experiment")
        experiment_address = experiment['rep_addrs'][-1]
        experiment_manager = obci_connection.ObciExperimentClient(experiment_address)
        scenario = self.get_scenario()
        experiment_manager.set_experiment_scenario(launch_file_path, scenario)
        
        #wait until MX starts
        self.wait_for_status_change(experiment_manager)
        
        #get MX address
        peer_invitation = experiment_manager.join_experiment("psychopy")
        self.mx_address = peer_invitation["params"]["mx_addr"].split(':')
        
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
