"""Platform specific extensions (using ctypes)"""
import sys.platform

if sys.platform=='win32':
	from win32 import *
if sys.platform=='darwin':
	from darwin import *
#if sys.platform=='posix':
	#from posix import *
	