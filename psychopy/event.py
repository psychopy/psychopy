"""To handle from keyboard, mouse and joystick (joysticks require pygame to be installed).
See demo_mouse.py and i{demo_joystick.py} for examples
"""
# Part of the PsychoPy library
# Copyright (C) 2010 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

import sys, time
import psychopy.core, psychopy.misc
import string, numpy

#try to import pyglet & pygame and hope the user has at least one of them!
try:
    from pygame import mouse, locals, joystick, display
    import pygame.key
    import pygame.event as evt
    havePygame = True
except:
    havePygame = False
    
try:
    import pyglet.window
    havePyglet = True
except:
    havePyglet = False
if havePygame: usePygame=True#will become false later if win not initialised
else: usePygame=False   

if havePyglet:
    
    global _keyBuffer
    _keyBuffer = []
    global mouseButtons
    mouseButtons = [0,0,0]
    global mouseWheelRel
    mouseWheelRel = numpy.array([0.0,0.0])
    #global eventThread
    #eventThread = _EventDispatchThread()
    #eventThread.start()

def _onPygletKey(symbol, modifiers): 
    """handler for on_key_press events from pyglet 
    Adds a key event to global _keyBuffer which can then be accessed as normal 
    using event.getKeys(), .waitKeys(), clearBuffer() etc... 
    Appends a tuple with (keyname, timepressed) into the _keyBuffer""" 
    
    keyTime=psychopy.core.getTime() #capture when the key was pressed

    thisKey = pyglet.window.key.symbol_string(symbol).lower()#convert symbol into key string
    #convert pyglet symbols to pygame forms ( '_1'='1', 'NUM_1'='[1]')
    thisKey = (thisKey.lstrip('_').lstrip('NUM_'),keyTime) # modified to capture time of keypress so key=(keyname,keytime)
    
    _keyBuffer.append(thisKey)

def _onPygletMousePress(x,y, button, modifiers):
    global mouseButtons
    if button == pyglet.window.mouse.LEFT: mouseButtons[0]=1
    if button == pyglet.window.mouse.MIDDLE: mouseButtons[1]=1
    if button == pyglet.window.mouse.RIGHT: mouseButtons[2]=1
def _onPygletMouseRelease(x,y, button, modifiers):
    global mouseButtons
    if button == pyglet.window.mouse.LEFT: mouseButtons[0]=0
    if button == pyglet.window.mouse.MIDDLE: mouseButtons[1]=0
    if button == pyglet.window.mouse.RIGHT: mouseButtons[2]=0
def _onPygletMouseWheel(x,y,scroll_x, scroll_y):
    global mouseWheelRel
    mouseWheelRel = mouseWheelRel+numpy.array([scroll_x, scroll_y])

def getKeys(keyList=None, timeStamped=False):
    """Returns a list of keys that were pressed.
        
    :Parameters:
        keyList : **None** or []
            Allows the user to specify a set of keys to check for.
            Only keypresses from this set of keys will be removed from the keyboard buffer. 
            If the keyList is None all keys will be checked and the key buffer will be cleared
            completely. NB, pygame doesn't return timestamps (they are always 0)
        timeStamped : **False** or True or `Clock`
            If True will return a list of 
            tuples instead of a list of keynames. Each tuple has (keyname, time). 
            If a `core.Clock` is given then the time will be relative to the `Clock`'s last reset
            
    :Author:
        - 2003 written by Jon Peirce
        - 2009 keyList functionality added by Gary Strangman
        - 2009 timeStamped code provided by Dave Britton
    """
    keys=[]


    if havePygame and display.get_init():#see if pygame has anything instead (if it exists)
        for evts in evt.get(locals.KEYDOWN):
            keys.append( (pygame.key.name(evts.key),0) )#pygame has no keytimes

    elif havePyglet:
        #for each (pyglet) window, dispatch its events before checking event buffer
        wins = pyglet.window.get_platform().get_default_display().get_windows()
        for win in wins: win.dispatch_events()#pump events on pyglet windows

        global _keyBuffer
        if len(_keyBuffer)>0:
            #then pyglet is running - just use this
            keys = _keyBuffer
    #        _keyBuffer = []  # DO /NOT/ CLEAR THE KEY BUFFER ENTIRELY
    
    if keyList==None:
        _keyBuffer = [] #clear buffer entirely
        targets=keys  # equivalent behavior to getKeys()
    else:
        nontargets = []
        targets = []
        # split keys into keepers and pass-thrus
        for key in keys:
            if key[0] in keyList:
                targets.append(key)
            else:
                nontargets.append(key)
        _keyBuffer = nontargets  # save these
        
    #now we have a list of tuples called targets
    #did the user want timestamped tuples or keynames?
    if timeStamped==False:
        keyNames = [k[0] for k in targets]
        return keyNames
    elif hasattr(timeStamped, 'timeAtLastReset'):
        relTuple = [(k[0],k[1]-timeStamped.timeAtLastReset) for k in targets]
        return relTuple
    elif timeStamped==True:
        return targets

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
        timer = psychopy.core.Clock()
        while key==None and timer.getTime()<maxWait:     
            if havePyglet:       
                wins = pyglet.window.get_platform().get_default_display().get_windows()
                for win in wins: win.dispatch_events()#pump events on pyglet windows
            keys = getKeys()
            #check if we got a key in list
            if len(keys)>0 and (keys[0] in keyList): 
                key = keys[0]
            
    elif keyList!=None:
        #check the keyList each time there's a press
        while key==None:        
            if havePyglet:    
                wins = pyglet.window.get_platform().get_default_display().get_windows()
                for win in wins: win.dispatch_events()#pump events on pyglet windows
            keys = getKeys()
            #check if we got a key in list
            if len(keys)>0 and (keys[0] in keyList): 
                key = keys[0]
            
    elif maxWait!=None:
        #onyl wait for the maxWait 
        timer = psychopy.core.Clock()
        while key==None and timer.getTime()<maxWait:       
            if havePyglet:          
                wins = pyglet.window.get_platform().get_default_display().get_windows()
                for win in wins: win.dispatch_events()#pump events on pyglet windows
            keys = getKeys()
            #check if we got a key in list
            if len(keys)>0: 
                key = keys[0]
            
    else: #simply take the first key we get
        while key==None:      
            if havePyglet:           
                wins = pyglet.window.get_platform().get_default_display().get_windows()
                for win in wins: win.dispatch_events()#pump events on pyglet windows
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
    
    Create your `visual.Window` before creating a Mouse.
    
    :Parameters:
        visible : **True** or False
            makes the mouse invisbile if necessary
        newPos : **None** or [x,y]
            gives the mouse a particular starting position (pygame `Window` only)
        win : **None** or `Window`
            the window to which this mouse is attached (the first found if None provided)

    """
    def __init__(self,
                 visible=True,
                 newPos=None,
                 win=None):
        self.visible=visible
        self.lastPos = None
        self.win=win
        #if pygame isn't initialised then we must use pyglet
        if (havePygame and not pygame.display.get_init()):
            global usePygame
            usePygame=False
        
        if newPos is not None: self.setPos(newPos)
        
    def setPos(self,newPos=(0,0)):
        """Sets the current postiion of the mouse (pygame only), 
        in the same units as the :class:`~visual.Window` (0,0) is at centre
        
        :Parameters:
            newPos : (x,y) or [x,y]
                the new position on the screen

        """
        newPosPix = self._windowUnits2pix(numpy.array(newPos))
        if usePygame: 
            newPosPix[1] = self.win.size[1]/2-newPosPix[1]
            newPosPix[0] = self.win.size[0]/2+newPosPix[0]
            print newPosPix
            mouse.set_pos(newPosPix)
        else: print "pyglet does not support setting the mouse position yet"
        
    def getPos(self):
        """Returns the current postion of the mouse, 
        in the same units as the :class:`~visual.Window` (0,0) is at centre
        """
        if usePygame: #for pygame top left is 0,0
            lastPosPix = numpy.array(mouse.get_pos())
            #set (0,0) to centre
            lastPosPix[1] = self.win.size[1]/2-lastPosPix[1]
            lastPosPix[0] = lastPosPix[0]-self.win.size[0]/2
        else: #for pyglet bottom left is 0,0
            #use default window if we don't have one
            if self.win: w = self.win.winHandle
            else: w=pyglet.window.get_platform().get_default_display().get_windows()[0]       
            #get position in window
            lastPosPix= numpy.array([w._mouse_x,w._mouse_y])
            #set (0,0) to centre
            lastPosPix = lastPosPix-self.win.size/2
        self.lastPos = self._pix2windowUnits(lastPosPix)    
        return self.lastPos
        
    def getRel(self):
        """Returns the new position of the mouse relative to the
        last call to getRel or getPos, in the same units as the :class:`~visual.Window`.
        """
        if usePygame: 
            relPosPix=mouse.get_rel()
            return self._pix2windowUnits(self.relPosPix)
        else: 
            #NB getPost() resets lastPos so MUST retrieve lastPos first
            if self.lastPos is None: relPos = self.getPos()
            else: relPos = -self.lastPos+self.getPos()#DON't switch to (this-lastPos)
            return relPos
    
    def getWheelRel(self):
        """Returns the travel of the mouse scroll wheel since last call.
        Returns a numpy.array(x,y) but for most wheels y is the only
        value that will change (except mac mighty mice?)
        """
        global mouseWheelRel
        rel = mouseWheelRel
        mouseWheelRel = numpy.array([0.0,0.0])
        return rel
    def getVisible(self):
        """Gets the visibility of the mouse (1 or 0)
        """
        if usePygame: return mouse.get_visible()
        else: print "Getting the mouse visibility is not supported under pyglet, but you can set it anyway"
        
    def setVisible(self,visible):
        """Sets the visibility of the mouse to 1 or 0
        
        NB when the mouse is not visible its absolute position is held
        at (0,0) to prevent it from going off the screen and getting lost!
        You can still use getRel() in that case.
        """
        if usePygame: mouse.set_visible(visible)
        else:             
            if self.win: #use default window if we don't have one
                w = self.win.winHandle
            else: 
                w=pyglet.window.get_platform().get_default_display().get_windows()[0]  
            w.set_mouse_visible(visible)
    
    def getPressed(self):
        """Returns a 3-item list indicating whether or not buttons
        1,2,3 are currently pressed
        """
        if usePygame: return mouse.get_pressed()
        else: return mouseButtons
    def _pix2windowUnits(self, pos):
        if self.win.units=='pix': return pos
        elif self.win.units=='norm': return pos*2.0/self.win.size
        elif self.win.units=='cm': return psychopy.misc.pix2cm(pos, self.win.monitor)
        elif self.win.units=='deg': return psychopy.misc.pix2deg(pos, self.win.monitor)
    def _windowUnits2pix(self, pos):
        if self.win.units=='pix': return pos
        elif self.win.units=='norm': return pos*self.win.size/2.0
        elif self.win.units=='cm': return psychopy.misc.cm2pix(pos, self.win.monitor)
        elif self.win.units=='deg': return psychopy.misc.deg2pix(pos, self.win.monitor)
        
def clearEvents(eventType=None):
    """Clears all events currently in the event buffer.
    Optional argument, eventType, specifies only certain types to be
    cleared 
    
    :Parameters:
        eventType : **None**, 'mouse', 'joystick', 'keyboard' 
            If this is not None then only events of the given type are cleared
    """
    #pyglet
    if not havePygame or not display.get_init():
        
        #for each (pyglet) window, dispatch its events before checking event buffer    
        wins = pyglet.window.get_platform().get_default_display().get_windows()
        for win in wins: win.dispatch_events()#pump events on pyglet windows
        
        global _keyBuffer
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