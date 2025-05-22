import importlib
import json
from pathlib import Path


class DeviceConfig(dict):
    """
    Dict linked to a JSON file, used to store configuration parameters for devices in the Device 
    Manager.

    Parameters
    ----------
    file : str or pathlib.Path
        JSON file this dict is linked to
    """
    def __init__(self, file):
        # load file on init
        self.load(file)
    
    def copy(self):
        """
        Create a copy of this DeviceConfig, linked to the same file. Useful for making temporary 
        changes which can then be made permenant by calling `save`

        Returns
        -------
        DeviceConfig
            A new DeviceConfig loaded from the same file as this one.
        """
        return DeviceConfig(self.file)
    
    def reload(self):
        """
        Load this DeviceConfig again from its file, overwriting any local changes. Useful if you 
        have made and saved changes in a copy and want to make sure this DeviceConfig object 
        is up to date with the file.
        """
        self.load(self.file)
    
    def load(self, file):
        """
        Load configuration from a given file. Doing so will also set the file that this 
        DeviceConfig object is linked to.

        Parameters
        ----------
        file : str or pathlib.Path
            JSON file to load from
        """
        # start off empty
        self.clear()
        # store file path
        self.file = Path(file)
        # read file
        data = json.loads(
            self.file.read_text()
        )
        # apply
        for key, val in data.items():
            # get class from stored data
            mod = ".".join(
                val['__cls__'].split(".")[:-1]
            )
            name = val['__cls__'].split(".")[-1]
            cls = getattr(importlib.import_module(mod), name)
            # initialise class with profile from stored data
            self[key] = cls.fromJSON(val)
            # make sure device name and device key line up
            self[key].name = key
    
    def save(self):
        """
        Save the contents of this DeviceConfig object to its linked JSON file.
        """
        # save
        self.file.write_text(
            json.dumps({
                key: device.toJSON() for key, device in self.items()
            }, indent=True)
        )
