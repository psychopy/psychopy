"""Set the key bindings for the PsychoPy app"""
#NB Ctrl- becomes Cmd- automatically on Apple platform
#All letter keys should be upper case 
import platform

open="Ctrl+O"
new = 'Ctrl+N'
save = "Ctrl+S"
saveas="Ctrl+Shift+S"
close='Ctrl+W'
quit='Ctrl+Q'

cut = 'Ctrl-X'
copy= 'Ctrl-C'
paste='Ctrl-V'
duplicate='Ctrl-D'#duplicate the current line
indent='Ctrl+]'#indent all the selected lines by 4 spaces
dedent='Ctrl+['
smartindent='Shift+Tab'
find = 'Ctrl+F'
findagain = 'Ctrl+G'
undo='Ctrl+Z'
if platform.system=='darwin': redo='Ctrl+Shift+Z'
else: redo='Ctrl+Y'
redo='Ctrl+Y'
runscript='F5'
stopscript='Shift+F5'
comment="Ctrl+'"
uncomment="Ctrl+Shift+'"
fold='Ctrl+Home'
analysecode='F4'

switchToBuilder="Ctrl+M"
switchToCoder="Ctrl+M"