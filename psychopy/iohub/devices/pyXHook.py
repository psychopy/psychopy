
# pyxhook -- an extension to emulate some of the PyHook library on linux.
#
#    Copyright (C) 2008 Tim Alexander <dragonfyre13@gmail.com>
#
#    This program is free software; you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation; either version 2 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program; if not, write to the Free Software
#    Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA
#
#    Thanks to Alex Badea <vamposdecampos@gmail.com> for writing the Record
#    demo for the xlib libraries. It helped me immensely working with these
#    in this library.
#
#    Thanks to the python-xlib team. This wouldn't have been possible without
#    your code.
#
#    This requires:
#    at least python-xlib 1.4
#    xwindows must have the "record" extension present, and active.
#
#    This file has now been somewhat extensively modified by
#    Daniel Folkinshteyn <nanotube@users.sf.net>
#    So if there are any bugs, they are probably my fault. :)
#
#   January 2013: File modified by
#      Sol Simpson (sol@isolver-software.com), with some cleanup done and
#      modifications made so it integrated with the ioHub module more effecively
#     ( but therefore making this version not useful for general application usage)
#
# March, 2013: -Fixed an existing bug that caused capslock not to have an effect,
#              -Added tracking of what keys are pressed and how many auto repeat
#              press events each has received.
# April, 2013: - Modified to directly return ioHub device event arrays
#             - optimized keysym lookup by loading into a dict cache
#             - started adding support for reporting unicode keys

import threading
import unicodedata
from Xlib import X, XK, display
from Xlib.ext import record
from Xlib.protocol import rq
from keyboard.keysym2ucs import keysym2ucs
from .. import print2err
from ..devices import Computer
from ..constants import EventConstants,MouseConstants, ModifierKeyCodes

jdumps = lambda x : str(x)
try:
    import ujson
    jdumps = ujson.dumps
except:
    import json
    jdumps = json.dumps   
    
getTime = Computer.getTime

#######################################################################
########################START CLASS DEF################################
#######################################################################

def event2json(event):
    """
    Instance Variable: KeyButtonPointerEvent time
        The server X time when this event was generated.
    Instance Variable: KeyButtonPointerEvent root
        The root window which the source window is an inferior of.
    Instance Variable: KeyButtonPointerEvent window
        The window the event is reported on.
    Instance Variable: KeyButtonPointerEvent same_screen
        Set to 1 if window is on the same screen as root, 0 otherwise.
    Instance Variable: KeyButtonPointerEvent child
        If the source window is an inferior of window, child is set to the child of window that is the ancestor of (or is) the source window. Otherwise it is set to X.NONE.
    Instance Variable: KeyButtonPointerEvent root_x
        Instance Variable: KeyButtonPointerEvent root_y
    The pointer coordinates at the time of the event, relative to the root window.
        Instance Variable: KeyButtonPointerEvent event_x
    Instance Variable: KeyButtonPointerEvent event_y
        The pointer coordinates at the time of the event, relative to window. If window is not on the same screen as root, these are set to 0.
    Instance Variable: KeyButtonPointerEvent state
        The logical state of the button and modifier keys just before the event.
    Instance Variable: KeyButtonPointerEvent detail
        For KeyPress and KeyRelease, this is the keycode of the event key.
        For ButtonPress and ButtonRelease, this is the button of the event.
        For MotionNotify, this is either X.NotifyNormal or X.NotifyHint.
    """    
    return jdumps(dict(type=event.type,
                send_event=event.send_event,
                time=event.time,
                root=str(event.root),
                window=str(event.window),
                same_screen=event.same_screen,
                child=str(event.child),
                root_x=event.root_x,
                root_y=event.root_y,
                event_x=event.event_x,
                event_y=event.event_y,
                state=event.state,
                detail=event.detail))

class HookManager(threading.Thread):
    """
    Creates a seperate thread that starts the Xlib Record functionality,
    capturing keyboard and mouse events and transmitting them
    to the associated callback functions set.
    """
    DEVICE_TIME_TO_SECONDS = 0.001
    evt_types = [X.KeyRelease, X.KeyPress,X.ButtonRelease, X.ButtonPress, X.MotionNotify]
    def __init__(self, log_event_details=False):
        threading.Thread.__init__(self)
        self.finished = threading.Event()

        self.log_events = log_event_details
        self.log_events_file = None
        
        # Window handle tracking
        self.last_windowvar = None
        self.last_xwindowinfo = None
                        
        # Give these some initial values
        self.mouse_position_x = 0
        self.mouse_position_y = 0

         # Assign default function actions (do nothing).
        self.KeyDown = lambda x: True
        self.KeyUp = lambda x: True
        self.MouseAllButtonsDown = lambda x: True
        self.MouseAllButtonsUp = lambda x: True
        self.MouseAllMotion = lambda x: True
        self.contextEventMask = [X.KeyPress,X.MotionNotify]
        

        # Used to hold any keys currently pressed and the repeat count
        # of each key.
        # If a key str is not in the dict, it is not pressed.
        # If it is in the list, the value == the number of times
        # a press event has been reeived for the key and no
        # release event. So values >= 1 == auto repeat keys.
        self.key_states=dict()

        self.contextEventMask = [X.KeyPress,X.MotionNotify]

        # Hook to our display.
        self.local_dpy = display.Display()
        self.record_dpy = display.Display()

        self.ioHubMouseButtonMapping={1:'MOUSE_BUTTON_LEFT',
                                 2:'MOUSE_BUTTON_MIDDLE',
                                 3:'MOUSE_BUTTON_RIGHT'
                                }
        self.pressedMouseButtons=0
        self.scroll_y=0
        self.create_runtime_keysym_maps()

    def run(self):
        # Check if the extension is present
        if not self.record_dpy.has_extension("RECORD"):
            print2err("RECORD extension not found. ioHub can not use python Xlib. Exiting....")
            return False

        # Create a recording context; we only want key and mouse events
        self.ctx = self.record_dpy.record_create_context(
                0,
                [record.AllClients],
                [{
                        'core_requests': (0, 0),
                        'core_replies': (0, 0),
                        'ext_requests': (0, 0, 0, 0),
                        'ext_replies': (0, 0, 0, 0),
                        'delivered_events': (0, 0),
                        'device_events': tuple(self.contextEventMask), #(X.KeyPress, X.ButtonPress),
                        'errors': (0, 0),
                        'client_started': False,
                        'client_died': False,
                }])

        if self.log_events:
            import datetime
            cdate = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M")        
            with open("x11_events_{0}.log".format(cdate), "w") as self.log_events_file:	
                # Enable the context; this only returns after a call to record_disable_context,
                # while calling the callback function in the meantime
                self.record_dpy.record_enable_context(self.ctx, self.processevents)
                # Finally free the context
                self.record_dpy.record_free_context(self.ctx)
        else:
            self.record_dpy.record_enable_context(self.ctx, self.processevents)
            # Finally free the context
            self.record_dpy.record_free_context(self.ctx)       
            
    def cancel(self):
        self.finished.set()
        self.local_dpy.record_disable_context(self.ctx)
        self.local_dpy.flush()

    def printevent(self, event):
        print2err(event)

    def HookKeyboard(self):
        pass

    def HookMouse(self):
        pass

    def isKeyPressed(self,key_str_id):
        """
        Returns 0 if key is not pressed, otherwise a
        possitive int, representing the auto repeat count ( return val - 1)
        of key press events that have occurred for the key.
        """
        return self.key_states.get(key_str_id,0)

    def getPressedKeys(self,repeatCounts=False):
        """
        If repeatCounts == False (default), returns a list
        of all the key symbol strings currently pressed.

        If repeatCounts == True, returns the dict of key
        sybol strs, pressedCount.
        """
        if repeatCounts:
            return self.key_states.items()
        return self.key_states.keys()


    def processevents(self, reply):
        logged_time=getTime()
        if reply.category != record.FromServer:
            return
        if reply.client_swapped:
            print2err("pyXlib: * received swapped protocol data, cowardly ignored")
            return
        if not len(reply.data) or ord(reply.data[0]) < 2:
            # not an event
            return
        data = reply.data
            
        while len(data):
            event, data = rq.EventField(None).parse_binary_value(data, self.record_dpy.display, None, None)
            
            if self.log_events_file and event.type in self.evt_types:
                self.log_events_file.write(event2json(event)+'\n')
               
            event.iohub_logged_time=logged_time
            if event.type == X.KeyPress:
                hookevent = self.makekeyhookevent(event)
                self.KeyDown(hookevent)
            elif event.type == X.KeyRelease:
                hookevent = self.makekeyhookevent(event)
                self.KeyUp(hookevent)
            elif event.type == X.ButtonPress:
                hookevent = self.buttonpressevent(event)
            elif event.type == X.ButtonRelease and event.detail not in (4,5):
                # 1 mouse wheel scroll event was generating a button press
                # and a button release event for each single scroll, so allow
                # wheel scroll events through for buttonpressevent, but not for
                # buttonreleaseevent so 1 scroll action causes 1 scroll event.
                hookevent = self.buttonreleaseevent(event)
            elif event.type == X.MotionNotify:
                # use mouse moves to record mouse position, since press and release events
                # do not give mouse position info (event.root_x and event.root_y have
                # bogus info).
                hookevent=self.mousemoveevent(event)

    def buttonpressevent(self, event):
        r= self.makemousehookevent(event)
        return r

    def buttonreleaseevent(self, event):
        r= self.makemousehookevent(event)
        return r

    def mousemoveevent(self, event):
        self.mouse_position_x = event.root_x
        self.mouse_position_y = event.root_y
        r= self.makemousehookevent(event)
        return r

    def create_runtime_keysym_maps(self):
        self._XK_NAME2CODE=dict()
        for name in dir(XK):
            if name.startswith("XK_"):
                self._XK_NAME2CODE[name]=getattr(XK, name)

        # Create a CODE2NAMES dict, checking for duplicates and handling
        # them when found
        self._XK_CODE2NAMES=dict()
        for n,c in self._XK_NAME2CODE.iteritems():
            names=self._XK_CODE2NAMES.get(c,[])
            names.append(n)
            self._XK_CODE2NAMES[c]=names

        # Get the iohub name -> XK name mapping dict and put any associated
        # names a) in the _XK_NAME2CODE dict b) as element index 0 of the
        # codes _XK_CODE2NAMES name list.

        import keyboard.iohub2xk_names as io2xk

        for io_name in dir(io2xk):
            if io_name[0] != '_':
                xk_name=getattr(io2xk,io_name)
                try:
                    code=self._XK_NAME2CODE[xk_name]
                except:
                    pass

            self._XK_NAME2CODE[io_name]=code
            self._XK_CODE2NAMES[code].insert(0,io_name)


    def lookup_keysym(self, keysym):
       return self.code2iokeysym(keysym)

    def keysym2code(self,keysym):
        return self._XK_NAME2CODE.get(keysym,0)

    def code2iokeysym(self,keysym):
        return self._XK_CODE2NAMES.get(keysym,["[%d]"%(keysym),])[0]

    def updateKeysPressedState(self, key_str, pressed_event):       
        keyautocount=self.key_states.setdefault(key_str,-1)
        
        if pressed_event:
            self.key_states[key_str]=keyautocount+1
        else:
            del self.key_states[key_str]
                
    def makekeyhookevent(self, event):
        """
        Creates a ioHub keyboard event in list format, completing as much
        as possible from within pyXHook. 

        For xlib KeyPress and KeyRelease event attributes see: 
        http://python-xlib.sourceforge.net/doc/html/python-xlib_13.html
        """
        mod_mask = event.state
        key_code = event.detail

        uchar = u''
        ucode = 0
        modifier_key_state = 0
        is_pressed_key = True        
        auto_repeat_count=0
        key=None
        unshifteducode=0
                 
        if event.type == X.KeyPress:
            event_type_id=EventConstants.KEYBOARD_PRESS            
        elif event.type == X.KeyRelease:
            is_pressed_key = False
            event_type_id =EventConstants.KEYBOARD_RELEASE   
            auto_repeat_count = 0                 
            
        # Start by getting the default evt.key value for the event
        #
        unshifted_keysym = self.local_dpy.keycode_to_keysym(key_code, 0)
        unshifteducode=keysym2ucs(unshifted_keysym)
        if unshifteducode!=-1:
            key=unichr(unshifteducode).encode('utf-8')
        else:
            # If not, use the generated mapping tables to get a key label
            key=unicode(self.lookup_keysym(unshifted_keysym),encoding='utf-8')
            unshifteducode=0
        # May as well set the char field to == key to start,
        uchar=key
        ucode = unshifteducode
        
        # Now get char for the pressed key that factors in any active
        # shift modifiers, updating the evt char field.
        #
        shiftuchar=None       
        lockuchar = None
        if mod_mask & X.ShiftMask == X.ShiftMask:
            shiftkeysym = self.local_dpy.keycode_to_keysym(key_code, 1)
            shiftucode=keysym2ucs(shiftkeysym)
            if shiftucode!=-1:
                shiftuchar=unichr(shiftucode).encode('utf-8')
            else:
                shiftucode=0
                shiftuchar=unicode(self.lookup_keysym(shiftkeysym),encoding='utf-8')
            
            if shiftuchar:
                uchar = shiftuchar
                ucode = shiftucode        
        
        # If a shift modifier is active, capslock is skipped by iohub
        # right now. Not sure if this results in expected key vs char values
        # all the time; but looks good to me so far. If a shift mod
        # is not pressed, then act on the capslock being active and update.
        # char field
        #
        elif mod_mask & X.LockMask == X.LockMask:
            lockkeysym = self.local_dpy.keycode_to_keysym(key_code, 2)
            lockucode=keysym2ucs(lockkeysym)
            if lockucode!=-1:
                lockuchar=unichr(lockucode).encode('utf-8')
            else:
                lockucode=0
                lockuchar=unicode(self.lookup_keysym(lockkeysym),encoding='utf-8')

            if lockuchar:
                uchar = lockuchar
                ucode = lockucode

            if uchar and len(uchar) == 1:
                ucat = unicodedata.category(u''+uchar)
                if len(ucat)>=2:
                    if ucat[:2].lower() == 'll':
                        uchar = uchar.upper()


        # Finally, update char value if numlock is active.
        numlckuchar = None
        if mod_mask & 16 == 16:
            numlckkeysym = self.local_dpy.keycode_to_keysym(key_code, 3)
            numlckucode=keysym2ucs(numlckkeysym)
            if numlckucode!=-1:
                numlckuchar=unichr(numlckucode).encode('utf-8')
            else:
                numlckucode=0
                numlckuchar=unicode(self.lookup_keysym(numlckkeysym),encoding='utf-8')

            if numlckuchar and numlckuchar.lower().startswith('keypad_'):
                uchar =  u'num_'+numlckuchar.lower()[7:]
        
        # Clean up the labels for uchar and key fields
        # that do not have a natural glyph.
        if uchar and len(uchar)>1:
            uchar = uchar.lower()            
        if uchar and uchar.startswith('keypad_'):
            uchar =  u'num_'+uchar[7:]
        elif uchar and (uchar.startswith('vk_') or uchar.startswith('xk_')):
            uchar = u''+uchar[3:]
            if uchar.startswith('kp_'):
                uchar = u'num_'+uchar[3:]
        
        key = key.lower()        
        if key and key.startswith('keypad_'):
            key =  u'num_'+key[7:]
        elif key and (key.startswith('vk_') or key.startswith('xk_')):
            key = key[3:]
            if key.startswith('kp_'):
                key = u'num_'+key[3:]

        if uchar == u'[0]':
            uchar = key


        # Update currently active modifiers
        #
        if mod_mask & 2 == 2:
            # capslock is active:
            modifier_key_state+=ModifierKeyCodes.capslock

        if mod_mask & 16 == 16:
            # NUM_LOCK is active:
            modifier_key_state+=ModifierKeyCodes.numlock

        self.updateKeysPressedState(key,is_pressed_key)

        pressed_key_list = self.getPressedKeys()
        for pk in pressed_key_list:
            if pk not in ['capslock','numlock']:
                is_mod_id = ModifierKeyCodes.getID(pk.upper())
                if is_mod_id:
                    modifier_key_state+=is_mod_id


        #return event to iohub
        return [[0,
                0,
                0, #device id (not currently used)
                0, #to be assigned by ioHub server# Computer._getNextEventID(),
                event_type_id,
                event.time*self.DEVICE_TIME_TO_SECONDS,
                event.iohub_logged_time,
                event.iohub_logged_time,
                0.0, # confidence interval not set for keybaord or mouse devices.
                0.0, # delay not set for keybaord or mouse devices.
                0,   # filter level not used
                auto_repeat_count, # auto_repeat 
                unshifted_keysym,#scan / Keycode of event.
                event.detail, # KeyID / VK code for key pressed
                ucode,  # unicode value for char, otherwise, 0
                key, #psychpy key event val
                modifier_key_state,  # The logical state of the button and modifier keys just before the event.
                int(self.xwindowinfo()["handle"], base=16),
                uchar,# utf-8 encoded char or label for the key. (depending on whether it is a visible char or not)
                0.0,
                0
                ],]
    

    def makemousehookevent(self, event):
        """
        Creates an incomplete ioHub keyboard event in list format. It is incomplete
        as some of the elements of the array are filled in by the ioHub server when
        it receives the events.

        For event attributes see: http://python-xlib.sourceforge.net/doc/html/python-xlib_13.html

        time
        The server X time when this event was generated.

        root
        The root window which the source window is an inferior of.

        window
        The window the event is reported on.

        same_screen
        Set to 1 if window is on the same screen as root, 0 otherwise.

        child
        If the source window is an inferior of window, child is set to the child of window that is the ancestor of (or is) the source window. Otherwise it is set to X.NONE.

        root_x
        root_y
        The pointer coordinates at the time of the event, relative to the root window.

        event_x
        event_y
        The pointer coordinates at the time of the event, relative to window. If window is not on the same screen as root, these are set to 0.

        state
        The logical state of the button and modifier keys just before the event.

        detail
        For KeyPress and KeyRelease, this is the keycode of the event key.
        For ButtonPress and ButtonRelease, this is the button of the event.
        For MotionNotify, this is either X.NotifyNormal or X.NotifyHint.
        """
        px,py = event.root_x,event.root_y
        storewm = self.xwindowinfo()
        event_type_id=0
        event_state=[]
        event_detail=[]
        dy=0

        if event.type == 6:
            if event.state < 128:
                event_type_id=EventConstants.MOUSE_MOVE
            else:
                event_type_id=EventConstants.MOUSE_DRAG

        if event.type in [4,5]:
            if event.type == 5:
                event_type_id=EventConstants.MOUSE_BUTTON_RELEASE
            elif event.type == 4:
                event_type_id=EventConstants.MOUSE_BUTTON_PRESS

            if event.detail == 4 and event.type==4:
                event_type_id=EventConstants.MOUSE_SCROLL
                self.scroll_y+=1
                dy=1
            elif event.detail == 5 and event.type==4:
                event_type_id=EventConstants.MOUSE_SCROLL
                self.scroll_y-=1
                dy=-1

        if event.state&1 == 1:
            event_state.append('SHIFT')
        if event.state&4 == 4:
            event_state.append('ALT')
        if event.state&64 == 64:
            event_state.append('WIN_MENU')
        if event.state&8 == 8:
            event_state.append('CTRL')

            event_state.append('MOUSE_BUTTON_LEFT')
        if event.state&512 ==512:
            event_state.append('MOUSE_BUTTON_MIDDLE')
        if event.state&1024 == 1024:
            event_state.append('MOUSE_BUTTON_RIGHT')

        if event.detail==1:
            event_detail.append('MOUSE_BUTTON_LEFT')
        if event.detail==2:
            event_detail.append('MOUSE_BUTTON_MIDDLE')
        if event.detail==3:
            event_detail.append('MOUSE_BUTTON_RIGHT')

        # TODO implement mouse event to display index detection
        display_index=0

        currentButton=0
        pressed=0
        currentButtonID=0
        if event.type in [4,5] and event_type_id != EventConstants.MOUSE_SCROLL:

            currentButton=self.ioHubMouseButtonMapping.get(event.detail)
            currentButtonID=MouseConstants.getID(currentButton)

            pressed = event.type==4

            if pressed is True:
                self.pressedMouseButtons+=currentButtonID
            else:
                self.pressedMouseButtons-=currentButtonID

        return[ [0,
                0,
                0, #device id (not currently used)
                0, #to be assigned by ioHub server# Computer._getNextEventID(),
                event_type_id,
                event.time*self.DEVICE_TIME_TO_SECONDS ,
                event.iohub_logged_time,
                event.iohub_logged_time,
                0.0, # confidence interval not set for keybaord or mouse devices.
                0.0, # delay not set for keybaord or mouse devices.
                0,   # filter level not used
                display_index, #event.DisplayIndex,
            pressed,
            currentButtonID,
            self.pressedMouseButtons,
            px, #mouse x pos
            py, # mouse y post
            0, #scroll_dx not supported
            0, #scroll_x
            dy,
            self.scroll_y,
            0, #mod state, filled in when event received by iohub
            int(storewm["handle"], base=16)],]
        # TO DO: Implement multimonitor location based on mouse location support.
        # Currently always uses monitor index 0



    def xwindowinfo(self):
        try:
            windowvar = self.local_dpy.get_input_focus().focus
            wmname = windowvar.get_wm_name()
            wmclass = windowvar.get_wm_class()
            if wmname is None and wmclass is None:
                windowvar = windowvar.query_tree().parent
                wmname = windowvar.get_wm_name()
                wmclass = windowvar.get_wm_class()
            if self.last_windowvar == windowvar:
                return self.last_xwindowinfo
            else:
                self.last_windowvar=windowvar                
            wmhandle = str(windowvar).split('(')[-1][:-1]            
            if wmhandle is None:
                wmhandle = '0x00'
            if wmclass:
                wmclass = wmclass[0]
            self.last_xwindowinfo = {"name":wmname, "class":wmclass, "handle":wmhandle}
        except:
            self.last_windowvar=None
            self.last_xwindowinfo = {"name":None, "class":None, "handle":'0x00'}
        return self.last_xwindowinfo
 
#
#
#######################################################################
