from psychopy.experiment.devices import DeviceBackend
from psychopy.experiment.params import Param
from psychopy.experiment import getInitVals
from psychopy.localization import _translate


class BasePhotometerDeviceBackend(DeviceBackend):
    """
    Subclass common to all Photometer Device Backend classes, so they can be identified in the 
    absence of a common Component.
    """
    icon = "../app/Resources/light/photometer.png"


class ScreenBufferPhotometerDeviceBackend(BasePhotometerDeviceBackend):
    """
    Represents an emulator photometer, which just returns the pixel values from the screen for 
    teaching / sanity checking purposes only.
    """
    backendLabel = "Photometer Emulator (debug)"
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



