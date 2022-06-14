#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Tools for interacting with the operating system
#

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

__all__ = ['systemProfilerMacOS']

import platform
import subprocess as sp


def systemProfilerMacOS(dataTypes=None, detailLevel='basic', timeout=180):
    """Call the MacOS system profiler and return data in a JSON format.

    Parameters
    ----------
    dataTypes : str, list or None
        Identifier(s) for the data to retrieve. All data types available will
        be returned if `None`. See output of shell command `system_profiler
        -listDataTypes` for all possible values. Specifying data types also
        speeds up the time it takes for this function to return as superfluous
        information is not queried.
    detailLevel : int or str
        Level of detail for the report. Possible values are `'mini'`, `'basic'`,
        or `'full'`. Note that increasing the level of detail will expose
        personally identifying information in the resulting report. Best
        practice is to use the lowest level of detail needed to obtain the
        desired information, or use `dataTypes` to limit what information is
        returned.
    timeout : float or int
        Amount of time to spend gathering data in seconds. Default is 180
        seconds, while specifying 0 means no timeout.

    Returns
    -------
    str
        Result of the `system_profiler` call as a JSON formatted string. You can
        pass the string to a JSON library to parse out what information is
        desired.

    Examples
    --------
    Get details about cameras attached to this system::

        dataTypes = "SPCameraDataType"  # data to query
        systemReportJSON = systemProfilerMacOS(dataTypes, detailLevel='basic')
        # >>> print(systemReportJSON)
        # {
        #   "SPCameraDataType" : [
        #     ...
        #   ]
        # }

    Parse the result using a JSON library::

        import json
        systemReportJSON = systemProfilerMacOS(
            "SPCameraDataType", detailLevel='mini')
        cameraInfo = json.loads(systemReportJSON)
        # >>> print(cameraInfo)
        # {'SPCameraDataType': [{'_name': 'Live! Cam Sync 1080p',
        # 'spcamera_model-id': 'UVC Camera VendorID_1054 ProductID_16541',
        # 'spcamera_unique-id': '0x2200000041e409d'}]

    """
    if platform.system() != 'Darwin':
        raise OSError(
            "Cannot call `systemProfilerMacOS`, detected OS is not 'darwin'."
        )

    if isinstance(dataTypes, (tuple, list)):
        dataTypesStr = " ".join(dataTypes)
    elif isinstance(dataTypes, str):
        dataTypesStr = dataTypes
    elif dataTypes is None:
        dataTypesStr = ""
    else:
        raise TypeError(
            "Expected type `list`, `tuple`, `str` or `NoneType` for parameter "
            "`dataTypes`")

    if detailLevel not in ('mini', 'basic', 'full'):
        raise ValueError(
            "Value for parameter `detailLevel` should be one of 'mini', 'basic'"
            " or 'full'."
        )

    # build the command
    shellCmd = ['system_profiler']
    if dataTypesStr:
        shellCmd.append(dataTypesStr)

    shellCmd.append('-json')  # ask for report in JSON formatted string
    shellCmd.append('-detailLevel')  # set detail level
    shellCmd.append(detailLevel)
    shellCmd.append('-timeout')  # set timeout
    shellCmd.append(str(timeout))

    # call the system profiler
    systemProfilerCall = sp.Popen(
        shellCmd,
        stdout=sp.PIPE)
    systemProfilerRet = systemProfilerCall.communicate()[0]  # bytes

    # We're going to need to handle errors from this command at some point, for
    # now we're leaving that up to the user.

    return systemProfilerRet.decode("utf-8")  # convert to string


if __name__ == "__main__":
    pass
