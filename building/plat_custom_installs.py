
import subprocess
import sys

if sys.platform == 'win32':
    subprocess.call(
        'pip install pyWinHook --extra-index-url https://www.lfd.uci.edu/~gohlke/pythonlibs'
        )
