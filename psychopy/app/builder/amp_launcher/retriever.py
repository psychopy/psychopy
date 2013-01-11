'''
Created on 22-08-2012

@author: Piotr Iwaniuk
'''
from psychopy.app.builder.amp_launcher.obci_connection import OBCIConnection
import os.path
from wx.lib import newevent

class AmpListRetrieverException(Exception):
    pass

RetrieverStartedEvent, EVT_RETRIEVER_STARTED = newevent.NewEvent()
RetrieverFinishedEvent, EVT_RETRIEVER_FINISHED = newevent.NewEvent()

class AmplifierInfo(object):
    """Contains all interesting data about an amplifier discovered by AmpListRetriever
    """
    def __init__(self, amplifier_list=[]):
        # TODO copy object for correctness?
        self.amplifier_list = amplifier_list
        self.amplifier_config = [{} for _ in self.amplifier_list]
    
    def get_entry(self, entry_index):
        return AmplifierInfoEntry(self.amplifier_list[entry_index])
    
    def get_summary(self):
        for entry in self.amplifier_list:
            yield [
                entry[0],
                os.path.split(entry[1]["experiment_info"]["launch_file_path"])[1],
                entry[1]["amplifier_params"]["channels_info"]["name"],
                entry[1]["experiment_info"]["experiment_status"]["status_name"]
            ]
            
class AmplifierInfoEntry(object):
    def __init__(self, entry):
        self.entry_dict = entry[1]
        self.server = entry[0] # ip and hostname

    def get_channels(self):
        for entry in self.entry_dict["amplifier_params"]["channels_info"]["channels"]:
            yield str(entry["name"])

    def get_parameter_choices(self):
        return {"sampling_rate": self.entry_dict['amplifier_params']['channels_info']['sampling_rates']}
    
    def get_launch_file(self):
        return self.entry_dict['experiment_info']['launch_file_path']
    
    def get_exec_file(self):
        return self.entry_dict['amplifier_peer_info']['path']

    def get_additional_params(self):
        return self.entry_dict['amplifier_params']['additional_params']

    def get_server(self):
        return self.server[0] # only ip address


class AmpListRetriever(object):
    """Fetches a list of amplifiers from OpenBCI server."""
    def __init__(self, obci_connection):
        self.obci_connection = obci_connection
    
    def get_server_list(self):
        response = self.obci_connection.get_nearby_servers()
        contacts_dict = response["nearby_machines"]
        return [(contact["ip"], contact["hostname"]) for contact in contacts_dict.itervalues()]
    
    def fetch_amp_list(self):
        """
        Fetch amp list synchronously.
        """
        server_list = self.get_server_list()
        amp_list = []
        for server in server_list:
            try:
                remote_connection = OBCIConnection((server[0], 12012))
                remote_amp_list = remote_connection.get_amp_list()
                amp_list.extend([(server, entry) for entry in remote_amp_list])
            except Exception:
                print "problems with server: " + str(server)
                #raise AmpListRetrieverException("problems with sever: " + str(server))
        # if all servers failed, try localhost
        if not amp_list:
            server = ("127.0.0.1", "localhost")
            try:
                remote_connection = OBCIConnection((server[0], 12012))
                remote_amp_list = remote_connection.get_amp_list()
                amp_list.extend([(server, entry) for entry in remote_amp_list])
            except Exception:
                print "even localhost is not working!"
        return AmplifierInfo(amp_list)
