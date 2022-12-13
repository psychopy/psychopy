#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2022 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

"""This module provides read and write access to the parallel port for Linux or
Windows.

The :class:`~psychopy.parallel.Parallel` class described below will attempt to
load whichever parallel port driver is first found on your system and should
suffice in most instances. If you need to use a specific driver then, instead of
using :class:`~psychopy.parallel.ParallelPort` shown below you can use one of
the following as drop-in replacements, forcing the use of a specific driver:

    - `psychopy.parallel.PParallelInpOut`
    - `psychopy.parallel.PParallelDLPortIO`
    - `psychopy.parallel.PParallelLinux`

Either way, each instance of the class can provide access to a different
parallel port.

There is also a legacy API which consists of the routines which are directly in
this module. That API assumes you only ever want to use a single parallel port
at once.

These are optional components that can be obtained by installing the
`psychopy-connect` extension into the current environment.

"""

import psychopy.logging as logging

try:
    from psychopy_connect import (
        ParallelPort,
        PParallelInpOut,    # windows only
        PParallelDLPortIO,
        PParallelLinux,
        setPortAddress,
        setPin,
        setData,
        readPin)
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for parallel ports is not available this session. Please "
        "install `psychopy-connect` and restart the session to enable support."
    )

if __name__ == "__main__":
    pass
