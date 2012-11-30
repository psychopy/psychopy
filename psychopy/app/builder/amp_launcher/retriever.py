'''
Created on 22-08-2012

@author: Piotr Iwaniuk
'''
from psychopy.app.builder.amp_launcher.obci_connection import OBCIConnection
import os.path

class AmpListRetrieverException(Exception):
    pass

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
        self.server = entry[0]

    def get_channels(self):
        for entry in self.entry_dict["amplifier_params"]["channels_info"]["channels"]:
            yield str(entry["name"])

    def get_parameters(self):
        yield ("sampling_rate", "128")
    
    def get_launch_file(self):
        return self.entry_dict['experiment_info']['launch_file_path']
    
    def get_exec_file(self):
        return self.entry_dict['amplifier_peer_info']['path']

    def get_server(self):
        return self.server
    
    def load_preset(self, name):
        raise NotImplementedError("load_preset")

    def save_preset(self, name):
        raise NotImplementedError("save_preset")


class AmpListRetriever(object):
    """Fetches a list of amplifiers from OpenBCI server."""
    def __init__(self, obci_connection):
        self.obci_connection = obci_connection
    
    def get_server_list(self):
        response = self.obci_connection.get_nearby_servers()
        contacts_dict = response["nearby_machines"]
        ret = []
        for contact in contacts_dict.itervalues():
            ret.append(contact["ip"])
        return ret
    
    def fetch_amp_list(self):
        """
        Fetch amp list synchronously.
        """
        server_list = self.get_server_list()
        amp_list = []
        for server in server_list:
            try:
                remote_connection = OBCIConnection((server, 12012))
                remote_amp_list = remote_connection.get_amp_list()
                amp_list.extend([(server, entry) for entry in remote_amp_list])
            except Exception:
                raise AmpListRetrieverException("problems with sever: " + str(server))
        return AmplifierInfo(amp_list)

if __name__ == "__main__":
    retriever = AmpListRetriever(OBCIConnection(("192.168.50.104", 12012)))
    print retriever.get_server_list()