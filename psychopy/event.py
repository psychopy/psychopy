"""To handle events such as keyboard and mouse.
Also imported is pygame's JOYSTICK package:
    
    http://www.pygame.org/docs/ref/pygame_joystick.html

See demo_mouse.py and i{demo_joystick.py} for examples
"""
#try to import pyglet & pygame and hope the user has at least one of them!
try:
    from pygame import mouse, locals, joystick, display
    import pygame.key
    import pygame.event as evt
    havePygame = True
except: 
    havePygame = False
    
try:
    from pyglet.window import key
    havePyglet = False
except:
    havePyglet = False
    pass

from psychopy import core
import string

global _openWindows
_openWindows=[]
global _keyBuffer
_keyBuffer = []

def _onPygletKey(symbol, modifiers):
    """handler for on_key_press events from pyglet
    Adds a key event to global _keyBuffer which can then be accessed as normal
    using event.getKeys(), .waitKeys(), clearBuffer() etc..."""         
    thisKey = key.symbol_string(symbol).lower()#convert symbol into key string
    #convert pyglet symbols to pygame forms ( '_1'='1', 'NUM_1'='[1]')
    thisKey = thisKey.lstrip('_').lstrip('NUM_')
    _keyBuffer.append(thisKey)

def getKeys():
    """Returns a list of names of recently pressed keys
    """
    keyNames=[]
    
    #for each (pyglet) window, dispatch its events before checking event buffer
    global _openWindows
    for win in _openWindows: win.dispatch_events()
            
    global _keyBuffer
    if len(_keyBuffer)>0:
        #then pyglet is running - just use this
        keyNames = _keyBuffer
        _keyBuffer = []#set a new empty list
        
    elif havePygame and display.get_init():#see if pygame has anything instead (if it exists)            
        for evts in evt.get(locals.KEYDOWN):
            keyNames.append(pygame.key.name(evts.key))
            
    return keyNames

def waitKeys(maxWait = None, keyList=None):
    """
    Halts everything (including drawing) while awaiting
    input from keyboard. Then returns *list* of keys pressed. Implicitly clears
    keyboard, so any preceding keypresses will be lost.
    
    Optional arguments specify maximum wait period and which keys to wait for. 
    
    Returns None if times out.
    """
    
    #NB pygame.event does have a wait() function that will
    #do this and maybe leave more cpu idle time?
    key=None
    clearEvents('keyboard')#so that we only take presses from here onwards.
    if maxWait!=None and keyList!=None:
        #check keylist AND timer
        timer = core.Clock()
        while key==None and timer.getTime()<maxWait:            
            for win in _openWindows: win.dispatch_events()#pump events on pyglet windows
            keys = getKeys()
            #check if we got a key in list
            if len(keys)>0 and (keys[0] in keyList): 
                key = keys[0]
            
    elif keyList!=None:
        #check the keyList each time there's a press
        while key==None:
            for win in _openWindows: win.dispatch_events()#pump events on pyglet windows
            keys = getKeys()
            #check if we got a key in list
            if len(keys)>0 and (keys[0] in keyList): 
                key = keys[0]
            
    elif maxWait!=None:
        #onyl wait for the maxWait 
        timer = core.Clock()
        while key==None and timer.getTime()<maxWait:
            for win in _openWindows: win.dispatch_events()#pump events on pyglet windows
            keys = getKeys()
            #check if we got a key in list
            if len(keys)>0: 
                key = keys[0]
            
    else: #simply take the first key we get
        while key==None:
            for win in _openWindows: 
                win.dispatch_events()#pump events on pyglet windows
            keys = getKeys()
            #check if we got a key in list
            if len(keys)>0: 
                key = keys[0]
        
    #after the wait period or received a valid keypress
    if key:
        return [key]#need to convert back to a list
    else: 
        return None #no keypress in period
    
class Mouse:
    """Easy way to track what your mouse is doing.
    It needn't be a class, but since Joystick works better
    as a class this may as well be one too for consistency
    
    Simple wrapper for the pygame mouse package
    """
    def __init__(self,
                 visible=True,
                 newPos=None):
        self.visible=visible
        if newPos is not None: self.setPos(newPos)
        
    def setPos(self,newPos=(0,0)):
        """Sets the current postiion of the mouse
        """
        mouse.set_pos(newPos)
        
    def getPos(self):
        """Returns the current postiion of the mouse
        """
        return mouse.get_pos()
    
    def getRel(self):
        """Returns the new postiion of the mouse relative to the
        last call to getRel
        """
        return mouse.get_rel()
    
    def getVisible(self):
        """Gets the visibility of the mouse (1 or 0)
        """
        mouse.get_visible()
        
    def setVisible(self,nowVisible):
        """Sets the visibility of the mouse to 1 or 0
        
        NB when the mouse is not visible its absolute position is held
        at (0,0) to prevent it from going off the screen and getting lost!
        You can still use getRel() in that case.
        """
        mouse.set_visible(nowVisible)
    
    def getPressed(self):
        """Returns a 3-item list indicating whether or not buttons
        1,2,3 are currently pressed
        """
        return mouse.get_pressed()

        
             



def clearEvents(eventType=None):
    """Clears all events currently in the event buffer.
    Optional argument, eventType, specifies only certain types to be
    cleared 
    
    *eventType* can be:      
        - None (default) all events wil be cleared
        - 'mouse', 'joystick', 'keyboard' will remove only events of that type
    """
    #pyglet
    if not havePygame or not display.get_init():
        _keyBuffer = []
        return
    
    #for pygame
    if eventType=='mouse':
        junk = evt.get([locals.MOUSEMOTION, locals.MOUSEBUTTONUP,
                        locals.MOUSEBUTTONDOWN])
    elif eventType=='keyboard':
        junk = evt.get([locals.KEYDOWN, locals.KEYUP])
    elif eventType=='joystick':
        junk = evt.get([locals.JOYAXISMOTION, locals.JOYBALLMOTION, 
              locals.JOYHATMOTION, locals.JOYBUTTONUP, locals.JOYBUTTONDOWN])
    else:
        junk = evt.get()