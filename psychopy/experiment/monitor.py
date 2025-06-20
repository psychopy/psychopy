from psychopy.experiment.devices import DeviceBackend
from psychopy.experiment.params import Param
from psychopy.localization import _translate


class MonitorDeviceBackend(DeviceBackend):
    # name of this backend to display in Device Manager
    backendLabel = "Monitor"
    # icon to use for this backend (relative to current file path, leave as None for no icon)
    icon = "../app/Resources/light/monitors32@2x.png"
    # class of the device which this backend corresponds to
    deviceClass = "psychopy.hardware.monitor.MonitorDevice"

    def getParams(self):
        """
        Get parameters from this backend to add to each new device from this backend.

        Returns
        -------
        dict[str:Param]
            Dict of Param objects for controlling devices in this backend
        list[str]
            List of param names, defining the order in which params should appear
        """
        params = {}
        order = [
            "width",
            "distance",
            "gamma",
            "gammaGrid"
        ]
        params['width'] = Param(
            "", valType="code", inputType="single",
            label=_translate("Width (cm)"),
            hint=_translate(
                "Width of the screen in cm"
            )
        )
        params['distance'] = Param(
            "", valType="code", inputType="single",
            label=_translate("Distance (cm)"),
            hint=_translate(
                "Distance (cm) between the monitor and the participant, for calculating positions "
                "in degrees of visual angle"
            )
        )
        params['gamma'] = Param(
            1, valType="code", inputType="single",
            label=_translate("Gamma"),
            hint=_translate(
                "Single gamma value for the monitor"
            )
        )
        params['gammaGrid'] = Param(
            [
                [0, 1, 1],
                [0, 1, 1],
                [0, 1, 1],
                [0, 1, 1]
            ], valType="code", inputType="gamma",
            label=_translate("Gamma grid"),
            hint=_translate(
                "Gamma calibration grid for the monitor"
            )
        )
        
        return params, order
    
    def writeDeviceCode(self, buff):
        """
        Write the code to create a device for this backend. This method must be overloaded by device backend subclasses.

        To write the basics of device initialisation, you can do: ::
            # this opens a call to DeviceManager.addDevice with the basic necessary arguments included, and does not close the brackets so you can add more
            self.writeBaseDeviceCode(buff, close=False)
            code = (
                # write any param-specific inits here (e.g. "threshold=%(threshold)s,\n")
                ")\n"
            )
            buff.writeIndentedLines
        
        To use just the basic device initialisation code, you can just do: ::
            return self.writeBaseDeviceCode(buff, close=True)
        """
        # write core code
        DeviceBackend.writeBaseDeviceCode(self, buff, close=False)
        # add params
        code = (
            "    width=%(width)s,\n"
            "    distance=%(distance)s,\n"
            "    gamma=%(gamma)s\n"
            ")\n"
        )
        buff.writeIndentedLines(code)
