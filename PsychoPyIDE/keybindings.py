"""Set the key bindings for your PsychoPyIDE"""
#NB Ctrl- becomes Cmd- automatically on Apple platform
#All letter keys should be upper case 
from sys import platform

key_cut = 'Ctrl-X'
key_copy= 'Ctrl-C'
key_paste='Ctrl-V'
key_duplicate='Ctrl-D'#duplicate the current line
key_indent='Ctrl+]'#indent all the selected lines by 4 spaces
key_dedent='Ctrl+['
key_smartindent='Shift+Tab'
key_find = 'Ctrl+F'
key_findagain = 'Ctrl+G'
key_undo='Ctrl+Z'
if platform=='darwin': key_redo='Ctrl+Shift+Z'
else: key_redo='Ctrl+Y'
key_runscript='F5'
key_stopscript='Shift+F5'
key_comment="Ctrl+'"
key_uncomment="Ctrl+Shift+'"
key_fold='Ctrl+Home'
key_analysecode='F4'

key_open="Ctrl+O"
key_new = 'Ctrl+N'
key_save = "Ctrl+S"
key_saveas="Ctrl+Shift+S"
key_close='Ctrl+W'
key_quit='Ctrl+Q'