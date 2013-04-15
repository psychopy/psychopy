from obci.control.common.message import OBCIMessageTool
from obci.control.launcher import launcher_messages
import obci_connection
import threading
import zmq
import json
import time
import os

class TimeoutException(Exception):
    pass


class LaunchFailedException(Exception):
    pass 


class ObciScanner(object):
    pass

class ObciLauncher(object):
    """
    TODO: docs
    """
    def __init__(self, server_address):
        self.server_address = server_address
    
    def create_experiment(self, name="Unnamed Experiment"):
        connection = obci_connection.ObciClient("tcp://" + self.server_address + ":54654")
        experiment = connection.create_experiment(name)
        connection.close()
        experiment_address = experiment['rep_addrs'][-1]
        uuid = experiment["uuid"]
        return ObciExperiment(experiment_address, uuid, self.server_address)
        

class ObciExperiment(object):
    T1 = 7.0
    T2 = 11.0
    
    def __init__(self, experiment_address, uuid, server_address):
        self.experiment_address = experiment_address
        self.uuid = uuid
        self.server_address = server_address
    
    def apply_config(self, config):
        self.config = config
        connection = obci_connection.ObciExperimentClient(self.experiment_address)
        connection.set_experiment_scenario(self.config.launch_file, self.config.generate_scenario())
        connection.close()
    
    def create_monitor(self, status_handler):
        return ExperimentMonitor(self.server_address, self.uuid, status_handler)
    
    def start(self):        
        connection = obci_connection.ObciExperimentClient(self.experiment_address)
        connection.start_experiment()
        connection.close()
    
    def cancel(self):
        pass
    
    def stop(self):
        connection = obci_connection.ObciClient("tcp://" + self.server_address + ":54654")
        connection.kill_experiment(self.uuid)
        connection.close()


class ExperimentMonitor(threading.Thread):
    def __init__(self, server_address, uuid, status_handler):
        self.server_address = server_address
        self.uuid = uuid
        self.pipe = None
        self.failed = False
        self.alive = False
        self.status_handler = status_handler or (lambda *_: None)
        super(ExperimentMonitor, self).__init__(group=None, target=None, name="exp-monitor")
    
    def run(self):
        context = zmq.Context().instance()
        sub_socket = context.socket(zmq.SUB)
        sub_socket.connect("tcp://" + self.server_address + ":34234")
        sub_socket.setsockopt(zmq.SUBSCRIBE, "")
        
        listener = context.socket(zmq.PAIR)
        print(str(id(self)))
        listener.bind("inproc://" + str(id(self)))
        
        readable = []
        while listener not in readable:
            readable, _, _ = zmq.select([sub_socket, listener], [], [])
            if sub_socket in readable:
                published = json.loads(sub_socket.recv())
                if published.get("uuid") == self.uuid:
                    if not self.failed and published.get("status_name") == "failed":
                        self.failed = True
                        self.status_handler(self.alive, self.failed)
                    elif not self.alive and published.get("peers") and "mx" in published['peers']:
                        self.alive = True
                        self.status_handler(self.alive, self.failed)
        listener.recv()
        listener.close()
        sub_socket.close()
    
    def start(self):
        super(ExperimentMonitor, self).start()
        time.sleep(2)
        context = zmq.Context().instance()
        self.connector = context.socket(zmq.PAIR)
        self.connector.connect("inproc://" + str(id(self)))
    
    def interrupt(self):
        self.connector.send("!")


class ExperimentSettings(object):
    def __init__(self, launch_file, amp_config):
        self.launch_file = launch_file
        self.amp_config = amp_config
    
    def generate_scenario(self):
        amplifier_peer = {
            'config': {
                'config_sources': {},
                'external_params': {},
                'launch_dependencies': {},
                'local_params': {
                    'active_channels': self.amp_config["active_channels"],
                    'channel_names': self.amp_config["channel_names"],
                    'sampling_rate': self.amp_config["params"]["sampling_rate"],
                    "console_log_level": "info",
                    "file_log_level": "debug",
                    "mx_log_level": "info",
                    "log_dir": "~/.obci/logs"
                }
            },
            'path': self.amp_config["exec_file"]
        }

        try:
            amplifier_peer['config']['local_params']['usb_device'] = self.amp_config["additional_params"]['usb_device']
            amplifier_peer['config']['local_params']['bluetooth_device'] = self.amp_config["additional_params"]['bluetooth_device']
        except KeyError:
            pass

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
        if self.amp_config["save_signal"]:
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
                        'save_file_name': self.amp_config["data_file_name"],
                        'save_file_path': self.amp_config["obci_data_dir"], 
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
