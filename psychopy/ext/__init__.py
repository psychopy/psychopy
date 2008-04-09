"""C extensions (platform specific). Not needed by most users"""

import sys
#imports all available c extensions

if sys.platform=='win32':
	from win32 import *
if sys.platform=='darwin':
	from darwin import *
#if sys.platform=='posix':
	#from posix import *
	