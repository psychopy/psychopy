"""
This module provides read/write access to the parallel port
for Linux or Windows.
"""

import sys
if sys.platform == 'linux2':
    from parallel_linux import *
else:
    from parallel_windows import *

