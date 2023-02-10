#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Copyright (c) 2009-2012 Valentin Haenel <valentin.haenel@gmx.de>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

import psychopy.logging as logging

try:
    from psychopy_crs.optical import OptiCAL
except (ModuleNotFoundError, ImportError):
    logging.error(
        "Support for Cambridge Research Systems OptiCAL is not available this "
        "session. Please install `psychopy-crs` and restart the session to "
        "enable support.")
except Exception as e:
    logging.error(
        "Error encountered while loading `psychopy-crs`. Check logs for more "
        "information.")
else:
    # Monkey-patch our metadata into CRS class if missing required attributes
    if not hasattr(OptiCAL, "longName"):
        setattr(OptiCAL, "longName", "CRS OptiCal")

    if not hasattr(OptiCAL, "driverFor"):
        setattr(OptiCAL, "driverFor", ["optical"])

if __name__ == "__main__":
    pass
