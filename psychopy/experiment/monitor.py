from psychopy.experiment.devices import DeviceBackend
from psychopy.experiment.params import Param
from psychopy.experiment import getInitVals
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
            1, valType="code", inputType="single", categ="Calibration",
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
            ], valType="code", inputType="gamma", categ="Calibration",
            label=_translate("Gamma grid"),
            hint=_translate(
                "Gamma calibration grid for the monitor"
            ),
            ctrlParams={
                'rowLabels': ("lum", "R", "G", "B"),
                'colLabels': ("Min", "Max", "Gamma", "a", "b", "k")
            }
        )
        params['lmsGrid'] = Param(
            [
                [0, 0, 0],
                [0, 0, 0],
                [0, 0, 0],
            ], valType="code", inputType="grid", categ="Calibration",
            label=_translate("LMS -> RGB"),
            hint=_translate(
                "Conversion table for calculating RGB values from LMS"
            ),
            ctrlParams={
                'rowLabels': ("R", "G", "B"),
                'colLabels': ("L", "M", "S")
            }
        )
        params['dklGrid'] = Param(
            [
                [0, 0, 0],
                [0, 0, 0],
                [0, 0, 0],
            ], valType="code", inputType="grid", categ="Calibration",
            label=_translate("DKL -> RGB"),
            hint=_translate(
                "Conversion table for calculating RGB values from DKL"
            ),
            ctrlParams={
                'rowLabels': ("R", "G", "B"),
                'colLabels': ("Lum", "L-M", "L+M-S")
            }
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
            "    gamma=%(gamma)s,\n"
            "    otherCalib={\n"
            "        'gammaGrid': %(gammaGrid)s,\n"
            "        'lms_rgb': %(lmsGrid)s,\n"
            "        'dkl_rgb': %(dklGrid)s,\n"
            "    }"
            ")\n"
        )
        buff.writeIndentedLines(code % self.params)


class BasePhotometerDeviceBackend(DeviceBackend):
    """
    Subclass common to all Photometer Device Backend classes, so they can be identified in the 
    absence of a common Component.
    """
    pass


class ScreenBufferPhotometerDeviceBackend(BasePhotometerDeviceBackend):
    """
    Represents an emulator photometer, which just returns the pixel values from the screen for 
    teaching / sanity checking purposes only.
    """
    backendLabel = "Photometer Emulator (debug)"
    icon = "../app/Resources/light/photometer.png"
    deviceClass = "psychopy.hardware.photometer.ScreenBufferPhotometerDevice"

    def getParams(self):
        params = {}
        order = [
            "pos",
            "size",
            "units"
        ]

        params['pos'] = Param(
            (0, 0), valType="list", inputType="single",
            label=_translate("Position (x, y)"),
            hint=_translate(
                "Position of the patch of pixels to pretend there is a photometer looking at"
            )
        )
        params['size'] = Param(
            (16, 16), valType="list", inputType="single",
            label=_translate("Size (w, h)"),
            hint=_translate(
                "Size of the patch of pixels to pretend there is a photometer looking at"
            )
        )
        params['units'] = Param(
            "pix", valType="str", inputType="choice",
            allowedVals=[
                "from exp settings", "deg", "cm", "pix", "norm", "height", "degFlatPos", "degFlat"
            ],
            label=_translate("Spatial units"),
            hint=_translate(
                "Spatial units in which to interpret size and position"
            )
        )

        return params, order
    
    def writeDeviceCode(self, buff):
        # write core code
        DeviceBackend.writeBaseDeviceCode(self, buff, close=False)
        # get inits
        inits = getInitVals(self.params)
        # add params
        code = (
            "    win=win,\n"
            "    size=%(size)s,\n"
            "    pos=%(pos)s,\n"
            "    units=%(units)s\n"
            ")\n"
        )
        buff.writeIndentedLines(code % inits)



