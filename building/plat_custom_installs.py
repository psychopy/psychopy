
import subprocess
import sys

if sys.platform == 'win32':
    subprocess.call(
        'pip install pyWinhook --extra-index-url https://www.lfd.uci.edu/~gohlke/pythonlibs'
        )
