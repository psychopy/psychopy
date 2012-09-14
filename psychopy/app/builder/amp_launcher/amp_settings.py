'''
Module dealing with amplifier settings.
'''
import wx
import os
import json

class PresetManager(object):
    """
    Manages a collection of presets. Assumes permanent storage in a file.
    """
    FILENAME = "ampPresets.json"
    instance = None
    
    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = cls()
        return cls.instance

    def get_presets_dir(self):
        """
        Get location where presets should be stored.
        @return: existing directory where config will be saved
        """
        # get location of config files
        paths = wx.StandardPaths.Get()
        presets_dir = paths.GetUserDataDir()
        # ensure it exists
        if not os.path.exists(presets_dir):
            os.makedirs(presets_dir, 0775)
        if not os.path.isdir(presets_dir):
            raise Exception("Failed to access app config dir.")
        return presets_dir

    def load_from_file(self):
        presets_dir = self.get_presets_dir()
        presets_filename = os.path.join(presets_dir, PresetManager.FILENAME)
        presets_file = open(presets_filename, "a+")
        presets_file.seek(0)
        if os.fstat(presets_file.fileno()).st_size == 0:
            self.presets = {}
        else:
            self.presets = dict([(name, Preset(preset_dict)) for (name, preset_dict) in json.load(presets_file).items()])
        presets_file.close()

    def save_to_file(self):
        presets_dir = self.get_presets_dir()
        presets_filename = os.path.join(presets_dir, PresetManager.FILENAME)
        presets_file = open(presets_filename, "w")
        json.dump([(name, preset.get_preset_dict()) for (name, preset) in self.presets.items()], presets_file)

    def __init__(self):
        self.presets = {}
        self.load_from_file()

    def get_preset_names(self):
        return self.presets.keys();

    def get_preset(self, name):
        return self.presets.get(name)
    
    def add_preset(self, name, preset):
        self.presets[name] = preset
    
    def remove_preset(self, name):
        del self.presets[name]


class Preset(object):
    """
    Stores amplifier setting for reuse.
    """
    def __init__(self, preset_dict):
        self.channel_names = []
        self.active_channels = set()
        self.sampling_rate = preset_dict["params"]["samplingRate"]
        for channel_name in preset_dict["channelNames"]:
            self.channel_names.append(channel_name)
        for channel in preset_dict["activeChannels"]:
            self.active_channels.add(channel)
    
    def get_preset_dict(self):
        return {
            "channelNames": self.channel_names,
            "activeChannels": self.active_channels,
            "params": {"samplingRate": self.sampling_rate}
        }
