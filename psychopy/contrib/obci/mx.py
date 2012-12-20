'''
Module for Psychopy and Multiplexer integration.
'''
import multiplexer
from multiplexer import multiplexer_constants
from obci.utils.tags_helper import pack_tag

class MXAdapter(object):
    def __init__(self, address):
        client_type = multiplexer_constants.peers.TAGS_SENDER
        self.client = multiplexer.clients.Client(addresses=[address], type=client_type)
    
    def close(self):
        self.client = None
    
    def send_tag(self, start_timestamp, stop_timestamp, name, description):
        packed_tag = pack_tag(start_timestamp, stop_timestamp, name, description)
        self.client.send_message(message=packed_tag, type=multiplexer_constants.types.TAG, flush=True)
