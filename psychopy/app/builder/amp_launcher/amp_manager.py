import os
import threading
import obci_client
import time
from obci_client import obci_connection

class AmplifierManager(object):
    """
    Class which handles running a scenario on an amplifier
    """
    T1 = 9
    T2 = 11
    
    def __init__(self, listener_callback, amp_config):
        self.amp_config = amp_config
        self.listener_callback = listener_callback
        
        self.experiment = None
        self.mx_address = None
        self.failed, self.t1_passed, self.t2_passed = False, False, False
    
    def interrupt_monitor(self):
        if self.monitor:
            self.monitor.interrupt()
    
    def start_experiment(self):
        waiting_thread = threading.Thread(group=None, target=self.waiting_target, name="exp-wait")
        starter_thread = threading.Thread(group=None, target=self.starter_target, name="exp-starter")
        waiting_thread.daemon = True
        waiting_thread.start()
        starter_thread.start()
    
    def waiting_target(self):
        time.sleep(self.T1)
        self.t1_passed = True
        self.check_status()
        time.sleep(self.T2)
        self.t2_passed = True
        self.check_status()
    
    def starter_target(self):
        launcher = obci_client.ObciLauncher(self.amp_config["server_address"])
        self.experiment = launcher.create_experiment("Psychopy Experiment")
        amp_config = obci_client.ExperimentSettings(self.amp_config["launch_file"], self.amp_config)
        self.experiment.apply_config(amp_config)
        self.monitor = self.experiment.create_monitor(self.experiment_status_handler)
        self.monitor.start()
        self.experiment.start()
        
    def experiment_status_handler(self, alive, failed):
        if failed:
            self.failed = True
        if alive:
            connection = obci_connection.ObciExperimentClient(self.experiment.experiment_address)
            peer_invitation = connection.join_experiment("psychopy")
            connection.close()
            self.mx_address = peer_invitation["params"]["mx_addr"].split(':')
            self.alive = True
            self.check_status()
    
    def check_status(self):
        if self.failed:
            self.listener_callback("failed")
        elif self.t1_passed and self.alive:
            self.listener_callback("started")
        elif self.t2_passed and not self.alive:
            self.listener_callback("timedout")

    def stop_experiment(self):
        self.experiment.stop()
