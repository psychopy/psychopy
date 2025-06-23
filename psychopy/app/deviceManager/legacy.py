from pathlib import Path
import json

from psychopy.experiment.monitor import MonitorDeviceBackend
from psychopy.hardware.monitor import MonitorDevice
from psychopy.localization import _translate
from psychopy.preferences import prefs

def migrateLegacyMonitors(devices=prefs.devices):
    # are there legacy monitors?
    monitorsDir = Path(prefs.paths['userPrefsDir']) / "monitors"
    monitorFiles = [file for file in monitorsDir.glob("*.json")]
    # if not, there's nothing to migrate
    if not len(monitorFiles):
        return
    # are all legacy monitors already covered by device manager?
    if all([file.stem in devices for file in monitorFiles]):
        return
    # get first available monitor as old configs didn't distinguish
    profile = {}
    for profile in MonitorDevice.getAvailableDevices():
        break
    # iterate through legacy files
    for file in monitorFiles:
        # skip monitors already handled by device manager
        if file.stem in devices:
            continue
        # load legacy spec
        with file.open("r") as f:
            calibrations = json.load(f)
        # skip if no calibrations
        if not len(calibrations):
            continue
        # get latest calibration
        config = calibrations[list(calibrations)[0]]
        # create new monitor
        device = devices[file.stem] = MonitorDeviceBackend(
            profile=profile
        )
        # set simple params
        device.params['deviceLabel'].val = file.stem
        device.params['width'].val = config.get('width', 30)
        device.params['distance'].val = config.get('distance', 50)
        device.params['gamma'].val = config.get('gamma', 1)
        # get/construct gamma grid
        if "gammaGrid" in config:
            arr = config['gammaGrid'].get('__ndarray__', device.params['gamma'].val)
            device.params['gammaGrid'].val = [row[:3] for row in arr]
    # save
    devices.save()
