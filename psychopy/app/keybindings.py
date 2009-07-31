"""Set the key bindings for your PsychoPyIDE"""
#NB Ctrl- becomes Cmd- automatically on Apple platform
#All letter keys should be upper case 
import platform

key_cut = 'Ctrl-X'
key_copy= 'Ctrl-C'
key_paste='Ctrl-V'
key_duplicate='Ctrl-D'#duplicate the current line
key_find = 'Ctrl+F'
key_findagain = 'Ctrl+G'
key_undo='Ctrl+Z'
if platform.system=='Darwin': key_redo='Ctrl+Shift+Z'
else: key_redo='Ctrl+Y'
key_runscript='F5'
key_stopscript='Shift+F5'

key_open="Ctrl+O"
key_new = 'Ctrl+N'
key_save = "Ctrl+S"
key_saveas="Ctrl+Shift+S"
key_close='Ctrl+W'
key_quit='Ctrl+Q'