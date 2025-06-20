from pathlib import Path
import wx
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
    # ask user if they'd like to migrate
    choices = [
        _translate("Convert and delete old configs"),
        _translate("Convert, but keep old configs"),
        _translate("Don't convert, but delete old configs"),
        _translate("Don't convert and keep old configs")
    ]
    dlg = wx.SingleChoiceDialog(None, _translate(
            "Legacy monitor configuration detected.\n"
            "\n"
            "From 2025.2.0 onwards, monitor configurations are handled by the Device Manager like any other hardware. \n"
            "It looks like you have some of the old style monitor configurations saved, would you like to convert them \n"
            "to device configurations so they appear in Device Manager?"
        ),
        _translate("Legacy monitor configurations"),
        choices=choices,
        style=wx.OK | wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.CENTRE
    )
    # only continue if they pressed OK
    if dlg.ShowModal() != wx.ID_OK:
        return
    # get choice
    choice = dlg.GetSelection()
    # migrate monitors
    if choice in (0, 1):
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
    # delete legacy config
    if choice in (0, 2):
        for file in monitorFiles:
            file.unlink()
