'''
Created on 28-08-2012

@author: piwaniuk
'''

import socket
from obci.obci_control.launcher import launcher_messages
from obci.obci_control.common.message import OBCIMessageTool
from StringIO import StringIO
import zmq
import json

class NetstringCodec(object):
    def __init__(self, separator = ":", delimiter=","):
        self.separator = separator
        self.delimiter = delimiter
    
    def encode(self, text):
        text = text.encode("utf-8")
        length = len(text)
        return str(length) + self.separator + text + self.delimiter;
    
    def decode(self, socket):
        digit = socket.recv(1)
        len_string = ""
        while digit != self.separator:
            len_string += digit
            digit = socket.recv(1)
        length = int(len_string)
        buffer_size = length + 1
        text_buffer = StringIO()
        while text_buffer.len < buffer_size:
            text_buffer.write(socket.recv(buffer_size - text_buffer.len))
        if text_buffer.getvalue()[-1] != self.delimiter:
            raise Exception("Missing message delimiter")
        return text_buffer.getvalue()[:-1]


class OBCIConnection(object):
    """
    Synchronous OBCI connection.
    """
    def __init__(self, address):
        templates = launcher_messages.message_templates
        self.msg_factory = OBCIMessageTool(msg_templates=templates)
        self.netstring_codec = NetstringCodec()
        self.address = address
        self.experiment_uuid = None
    
    def close(self):
        self.connection.close()
    
    def open(self):
        self.connection = socket.create_connection(self.address, timeout=30)
    
    def send_recv(self, message_name, **kwargs):
        message_json = self.msg_factory.fill_msg(message_name, **kwargs)
        message_netstring = self.netstring_codec.encode(message_json)
        self.open()
        self.connection.send(message_netstring)
        response_json = self.netstring_codec.decode(self.connection)
        self.close()
        response_dict = self.msg_factory.decode_msg(response_json)
        return response_dict
    
    def get_amp_list(self):
        message = self.msg_factory.fill_msg("find_eeg_amplifiers")
        message = self.netstring_codec.encode(message)
        self.open()
        self.connection.send(message)
        response_text = self.netstring_codec.decode(self.connection)
        response = self.msg_factory.decode_msg(response_text)
        self.close()
        amp_list = response["amplifier_list"]
        return amp_list
    
    def start_eeg_signal(self, name, launch_file, amplifier_params):
        message = self.msg_factory.fill_msg("start_eeg_signal", launch_file=launch_file, amplifier_params=amplifier_params, name=name)
        message_text = self.netstring_codec.encode(message)
        self.open()
        self.connection.send(message_text)
        response_text = self.netstring_codec.decode(self.connection)
        response = self.msg_factory.decode_msg(response_text)
        self.close()
        return response["sender"]
    
    def get_experiment_contact(self, name):
        response = self.send_recv("get_experiment_contact", strname=name)
        self.experiment_uuid = response["uuid"]
        return self.experiment_uuid
    
    def stop_experiment(self, experiment_uuid=None):
        if not experiment_uuid:
            experiment_uuid = self.experiment_uuid
        message = self.msg_factory.fill_msg("kill_experiment", strname=experiment_uuid)
        message_text = self.netstring_codec.encode(message)
        self.open()
        self.connection.send(message_text)
        response_text = self.netstring_codec.decode(self.connection)
        self.close()
        response = self.msg_factory.decode_msg(response_text)
        return response
    
    def create_experiment(self, name="unnamed"):
        message = self.msg_factory.fill_msg("create_experiment", name=name)
        message_text = self.netstring_codec.encode(message)
        self.open()
        self.connection.send(message_text)
        response_text = self.netstring_codec.decode(self.connection)
        self.close()
        return self.msg_factory.decode_msg(response_text)
    
    def set_experiment_scenario(self, launch_file_path="", scenario=""):
        return self.send_recv("set_experiment_scenario", launch_file_path=launch_file_path, scenario=scenario)
    
    def start_experiment(self):
        return self.send_recv("start_experiment")
    
    def get_nearby_servers(self):
        response = self.send_recv("list_nearby_machines")
        return response
    
class ObciBaseClient(object):
    """
    Base class for communicating with OBCI peers.
    """
    def __init__(self, address):
        self.context = zmq.Context.instance()
        templates = launcher_messages.message_templates
        self.msg_factory = OBCIMessageTool(msg_templates=templates)
        self.socket = self.context.socket(zmq.REQ)
        self.socket.connect(address)
        self.open = True

    def close(self):
        if self.open:
            self.socket.close()
            self.open = False

    def send_recv(self, message_name, **kwargs):
        data = self.msg_factory.fill_msg(message_name, **kwargs)
        self.socket.send(data)
        response = self.socket.recv()
        return json.loads(response)


class ObciClient(ObciBaseClient):
    """
    Client for OBCI Server.
    """
    def create_experiment(self, name="unnamed"):
        return self.send_recv("create_experiment", name=name)

    def kill_experiment(self, experiment_uuid=None):
        experiment_uuid = experiment_uuid or self.uuid
        return self.send_recv("kill_experiment", strname=experiment_uuid)


class ObciExperimentClient(ObciBaseClient):
    """
    Class which sends request to experiment manager.
    """
    def set_experiment_scenario(self, launch_file_path, scenario):
        scenario_json=json.dumps(scenario)
        return self.send_recv("set_experiment_scenario", launch_file_path=launch_file_path, scenario=scenario_json)
    
    def get_experiment_info(self):
        return self.send_recv("get_experiment_info")
    
    def get_peer_info(self, peer_id):
        return self.send_recv("get_peer_info", peer_id=peer_id)
    
    def join_experiment(self, peer_id):
        return self.send_recv("join_experiment", peer_id=peer_id, peer_type="obci_peer")

    def start_experiment(self):
        return self.send_recv("start_experiment")
