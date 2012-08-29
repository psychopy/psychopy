'''
Created on 28-08-2012

@author: piwaniuk
'''

import socket
from obci.obci_control.launcher import launcher_messages
from obci.obci_control.common.message import OBCIMessageTool

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
        buffer_size = length + 1 # TODO make it power of 2
        text_buffer = socket.recv(buffer_size)
        if text_buffer[-1] != self.delimiter:
            raise Exception("Missing message delimiter")
        return text_buffer[:-1]


class OBCIConnection(object):
    def __init__(self, address):
        templates = launcher_messages.message_templates
        self.msg_factory = OBCIMessageTool(msg_templates=templates)
        self.netstring_codec = NetstringCodec()
        self.address = address
        self.experiment_uuid = None
    
    def close(self):
        self.connection.close()
    
    def open(self):
        self.connection = socket.create_connection(self.address, timeout=5)
    
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
        print response_text
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
    
    def get_nearby_servers(self):
        response = self.send_recv("list_nearby_machines")
        return response
