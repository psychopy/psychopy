"""Platform specific extensions (using ctypes)"""
import sys

if sys.platform=='win32':
	from win32 import *
elif sys.platform=='darwin':
	from darwin import *
elif sys.platform.startswith('linux'):#normally 'linux2'
	from linux import *
elif sys.platform=='posix':#ever?!
	from posix import *
	