
global app
from psychopy.app.psychopyApp import PsychoPyApp
app=PsychoPyApp()

def teardown_module():
    global app
    app.quit()#this currently uses sys.exit() which ends testing :-(
