def setUp(self):
    global app
    from psychopy.app.psychopyApp import PsychoPyApp
    self.app=PsychoPyApp()

def tearDown():
    global app
    #this doesn't work, nor does any attempt to Destroy() an opened frame
    #either here or in setUp()
    #app.quit()#this currently uses sys.exit() which ends nose testing :-(
