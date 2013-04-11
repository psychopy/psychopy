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
from obci_client import obci_connection
from psychopy.app.builder.amp_launcher import retriever, amp_manager
import os.path
import json
from wx.lib import throbber, newevent
import time
import threading


MxAliveEvent, EVT_MX_ALIVE = newevent.NewEvent()
PeerFailedEvent, EVT_PEER_FAILED = newevent.NewEvent()

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
    def __init__(self, parent, retriever_instance=None, data_file_name="psychopy_data"):
        super(AmpLauncherDialog, self).__init__(
                parent, size=(760, 640), title="Amp Launcher", style=wx.DEFAULT_DIALOG_STYLE)
        self.data_file_name = data_file_name
        self.amp_info = None
        self.old_index = None
        self.amp_manager = None
        self.connection = obci_connection.OBCIConnection(("192.168.0.106", 12012))
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

    def get_persistent_config(self):
        return {
            "save_signal": self.GetParent().exp.settings.params['saveSignal'].val,
            "obci_data_dir": self.GetParent().exp.settings.params['obciDataDirectory'].val 
        }
    
    def run_click(self, event):
        if not self.amp_config.Validate():
            return
        #launching_thread = threading.Thread(group=None, target=self.start_amplifier, name="start-amplifier-thread")
        #launching_thread.start()
        #self.launching_dialog.ShowModal()
        #launching_thread.join()
        #if self.launching_dialog.GetReturnCode() != wx.OK:
        #    self.amp_manager.interrupt_monitor()
        #    return
        #launcher = obci_client.ObciLauncher("tcp://" + self.amp_config.get_server() + ":54654")
        #experiment = launcher.create_experiment("Psychopy Experiment")
        #amp_config = obci_client.ExperimentSettings(self.amp_config.get_launch_file(), amp_config_dict)
        #experiment.apply_config(amp_config)
        #experiment.start()
        self.amp_manager = self.start_amplifier()
        self.show_progress_dialog()
        event.Skip()
        
    def show_progress_dialog(self):
        self.launching_dialog = LaunchingDialog(self)
        self.launching_dialog.ShowModal()
    
    def start_amplifier(self):
        amp_config_dict = self.amp_config.get_config()
        amp_config_dict.update(self.get_persistent_config())
        manager = amp_manager.AmplifierManager(self.start_handler, amp_config_dict)
        manager.start_experiment()
        return manager
    
    def start_handler(self, status):
        """
        This may be called from outside of wx context.
        """
        wx.CallAfter(self.start_handler_wx)
    
    def start_handler_wx(self):
        self.launching_dialog.EndModal(wx.OK)


class LaunchingDialog(wx.Dialog):
    def __init__(self, parent):
        super(LaunchingDialog, self).__init__(parent, style=0)
        self.t1_passed = False
        self.mx_alive = False
        self.failed = True
        self.timer = wx.Timer(self)
        self.SetSizer(wx.BoxSizer(wx.VERTICAL))
        throbber_bitmap = wx.ArtProvider.GetBitmap("pop-tart-throbber", wx.ART_OTHER)
        self.throbber = throbber.Throbber(self, -1, bitmap=throbber_bitmap, frames=12, frameWidth=400)
        self.throbber.Start()
        self.GetSizer().Add(self.throbber)
        self.GetSizer().Add(wx.StaticText(self, label="Waiting for amplifier to start up..."), flag=wx.ALL | wx.ALIGN_CENTER, border=8)
        self.Fit()
