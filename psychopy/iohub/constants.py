# -*- coding: utf-8 -*-
"""
Created on Thu Nov 08 15:13:55 2012

@author: Sol

"""

try:
    from .util import print2err
    
    class Constants(object):
        UNDEFINED=0
        _keys=None
        _names=None
        _classes=None
    
        _initialized=False
    
        @classmethod
        def getName(cls,id):
            return cls._names.get(id,cls._names[cls.UNDEFINED])
     
        @classmethod
        def getID(cls,name):
            return cls._names.get(name,None)
    
        @classmethod
        def getClass(cls,id):
            return cls._classes.get(id,None)
    
        @classmethod
        def initialize(cls,starting_index=1):
            if cls._initialized:
                return
    
            [setattr(cls,a,i+starting_index) for i,a in enumerate(dir(cls)) if ((a[0] != '_') and (not callable(getattr(cls,a))) and (getattr(cls,a) < 0))]
            cls._names=dict([(getattr(cls,a),a) for a in dir(cls) if ((a[0] != '_') and (not callable(getattr(cls,a))))])
            cls._keys=list(cls._names.keys())
            cls._names.update(dict([(v,k) for k,v in cls._names.iteritems()]))
            cls._initialized=True
     
    class EventConstants(Constants):
        KEYBOARD_INPUT=20
        KEYBOARD_KEY=21
        KEYBOARD_PRESS=22
        KEYBOARD_RELEASE=23
        KEYBOARD_CHAR=24
    
        MOUSE_INPUT=30
        MOUSE_BUTTON=31
        MOUSE_BUTTON_PRESS=32
        MOUSE_BUTTON_RELEASE=33
        # deprecated for MOUSE_MULTI_CLICK in 0.6RC1
        MOUSE_DOUBLE_CLICK=34
        MOUSE_MULTI_CLICK=34
        MOUSE_SCROLL=35
        MOUSE_MOVE=36
        MOUSE_DRAG=37
        
        EYETRACKER=50
        MONOCULAR_EYE_SAMPLE=51
        BINOCULAR_EYE_SAMPLE=52
        FIXATION_START=53
        FIXATION_END=54
        SACCADE_START=55
        SACCADE_END=56
        BLINK_START=57
        BLINK_END=58
    
        GAMEPAD_STATE_CHANGE=81
        GAMEPAD_DISCONNECT=82
    
        MULTI_CHANNEL_ANALOG_INPUT=122
    
        MESSAGE=151
        LOG=152
        
        @classmethod
        def addClassMappings(cls,device_class,device_event_ids,event_classes):
            if cls._classes is None:
                cls._classes={}
    
            #import iohub
            #iohub.print2err("Adding Device Event Mappings for device: ",device_class.__name__)
   
            for event_id in device_event_ids:
                event_constant_string=cls.getName(event_id)
                event_class=None
                for event_class in event_classes.values():
                    if event_class.EVENT_TYPE_ID == event_id:
                        cls._classes[event_id]=event_class
                        cls._classes[event_class]=event_id
                        #iohub.print2err("\tAdding Event Class Mapping: ",event_constant_string, " = ",event_id)
                        break
                
                if event_id not in cls._classes.keys():
                        print2err("\t*** ERROR ADDING EVENT CLASSS MAPPING: Could not find class: ",event_constant_string, " = ",event_id)
    
    EventConstants.initialize()
    
    class DeviceConstants(Constants):
        OTHER = 1
        KEYBOARD = 20
        MOUSE = 30
    #    KB_MOUSE_COMBO = 25
        EYETRACKER = 50
        XINPUT= 70
        GAMEPAD=80
    #    PARALLEL_PORT = 102
    #    SERIAL=104
        ANALOGINPUT = 120
    #    MBED=130
        EXPERIMENT = 150
        DISPLAY = 190
        COMPUTER = 200
    #    FILTER = 210
    #    STAMPE_FILTER=219
    
        @classmethod
        def addClassMapping(cls,device_class):
            if cls._classes is None:
                cls._classes={}
    
            
            device_constant_string=device_class.__name__.upper()
            device_id=getattr(cls,device_constant_string)
            #import iohub
            #iohub.print2err("Adding Device Class Mapping: ",device_constant_string, " = ",device_id)
            cls._classes[device_id]=device_class
            cls._classes[device_class]=device_id
    
    DeviceConstants.initialize()
    
    class MouseConstants(Constants):
        MOUSE_BUTTON_NONE=0
        MOUSE_BUTTON_LEFT=1
        MOUSE_BUTTON_RIGHT=2
        MOUSE_BUTTON_MIDDLE=4
        MOUSE_BUTTON_4=8
        MOUSE_BUTTON_5=16
        MOUSE_BUTTON_6=32
        MOUSE_BUTTON_7=64
        MOUSE_BUTTON_8=128
        MOUSE_BUTTON_9=256
    
        MOUSE_BUTTON_STATE_RELEASED=10 # event has a  button released state
        MOUSE_BUTTON_STATE_PRESSED=11 # event has a  button pressed state
        MOUSE_BUTTON_STATE_DOUBLE_CLICK=12 # a button double click event
        MOUSE_BUTTON_STATE_MULTI_CLICK=12 # a button double click event
    
    MouseConstants.initialize()
    
    import sys    
    if sys.platform == 'win32':
        
        class AsciiConstants(Constants):
            # Mainly from the pyHook lookup Table, some from Pyglet
        
            BACKSPACE = 0x08
            TAB = 0x09
            LINEFEED = 0x0A
            CLEAR = 0x0B
            RETURN = 0x0D
            SYSREQ = 0x15
            ESCAPE = 0x1B
        
            SPACE = 0x20
            EXCLAMATION = 0x21
            DOUBLEQUOTE = 0x22
            POUND = 0x23
            DOLLAR = 0x24
            PERCENT = 0x25
            AMPERSAND = 0x26
            APOSTROPHE = 0x27
            PARENLEFT = 0x28
            PARENRIGHT = 0x29
            ASTERISK = 0x2A
            PLUS = 0x2B
            COMMA = 0x2C
            MINUS = 0x2D
            PERIOD = 0x2E
            SLASH = 0x2F
        
            n0_=0x30
            n1_=0x31
            n2_=0x32
            n3_=0x33
            n4_=0x34
            n5_=0x35
            n6_=0x36
            n7_=0x37
            n8_=0x38
            n9_=0x39
        
            COLON = 0x3A
            SEMICOLON = 0x3B
            LESS = 0x3C
            EQUAL = 0x3D
            GREATER = 0x3E
            QUESTION = 0x3F
            AT = 0x40
        
            A=0x41
            B=0x42
            C=0x43
            D=0x44
            E=0x45
            F=0x46
            G=0x47
            H=0x48
            I=0x49
            J=0x4A
            K=0x4B
            L=0x4C
            M=0x4D
            N=0x4E
            O=0x4F
            P=0x50
            Q=0x51
            R=0x52
            S=0x53
            T=0x54
            U=0x55
            V=0x56
            W=0x57
            X=0x58
            Y=0x59
            Z=0x5A
        
            BRACKETLEFT = 0x5B
            BACKSLASH = 0x5C
            BRACKETRIGHT = 0x5D
            ASCIICIRCUM = 0x5E
            UNDERSCORE = 0x5F
            GRAVE = 0x60
        
            a = 0x61
            b = 0x62
            c = 0x63
            d = 0x64
            e = 0x65
            f = 0x66
            g = 0x67
            h = 0x68
            i = 0x69
            j = 0x6A
            k = 0x6B
            l = 0x6C
            m = 0x6D
            n = 0x6E
            o = 0x6F
            p = 0x70
            q = 0x71
            r = 0x72
            s = 0x73
            t = 0x74
            u = 0x75
            v = 0x76
            w = 0x77
            x = 0x78
            y = 0x79
            z = 0x7A
        
            BRACELEFT = 0x7B
            BAR = 0x7C
            BRACERIGHT = 0x7D
            ASCIITILDE = 0x7E
        
            @classmethod
            def getName(cls,id):
                return cls._names.get(id,None)
        
        AsciiConstants.initialize()
    
        class VirtualKeyCodes(Constants):
                # Mainly from the pyHook lookup Table, some from Pyglet
                VK_CANCEL  =  0x03
                VK_BACK  =  0x08
                VK_TAB  =  0x09
                VK_CLEAR  =  0x0C
                VK_RETURN  =  0x0D
            
                VK_SHIFT  =  0x10
                VK_CONTROL  =  0x11
                VK_MENU  =  0x12
                VK_PAUSE  =  0x13
                VK_CAPS_LOCK  =  0x14
                VK_CAPITAL  =  0x14
                VK_HANGUL  =  0x15
                VK_JUNJA  =  0x17
                VK_FINAL  =  0x18
                VK_HANJA  =  0x19
                VK_ESCAPE  =  0x1B
                VK_CONVERT  =  0x1C
                VK_NONCONVERT  =  0x1D
                VK_ACCEPT  =  0x1E
                VK_MODECHANGE  =  0x1F
            
                VK_SPACE  =  0x20
                VK_PAGE_UP  =  0x21
                VK_PAGE_DOWN  =  0x22
                VK_END  =  0x23
                VK_HOME  =  0x24
                VK_LEFT  =  0x25
                VK_UP  =  0x26
                VK_RIGHT  =  0x27
                VK_DOWN  =  0x28
                VK_SELECT  =  0x29
                VK_PRINT  =  0x2A
                VK_EXECUTE  =  0x2B
                VK_PRINT_SCREEN  =  0x2C
                VK_INSERT  =  0x2D
                VK_DELETE  =  0x2E
                VK_HELP  =  0x2F
            
                VK_LEFT_CMD  =  0x5B
                VK_RIGHT_CMD  =  0x5C
                VK_APPS  =  0x5D
            
                VK_NUMPAD0  =  0x60
                VK_NUMPAD1  =  0x61
                VK_NUMPAD2  =  0x62
                VK_NUMPAD3  =  0x63
                VK_NUMPAD4  =  0x64
                VK_NUMPAD5  =  0x65
                VK_NUMPAD6  =  0x66
                VK_NUMPAD7  =  0x67
                VK_NUMPAD8  =  0x68
                VK_NUMPAD9  =  0x69
                VK_MULTIPLY  =  0x6A
                VK_ADD  =  0x6B
                VK_SEPARATOR  =  0x6C
                VK_SUBTRACT  =  0x6D
                VK_DECIMAL  =  0x6E
                VK_DIVIDE  =  0x6F
            
                VK_F1  =  0x70
                VK_F2  =  0x71
                VK_F3  =  0x72
                VK_F4  =  0x73
                VK_F5  =  0x74
                VK_F6  =  0x75
                VK_F7  =  0x76
                VK_F8  =  0x77
                VK_F9  =  0x78
                VK_F10  =  0x79
                VK_F11  =  0x7A
                VK_F12  =  0x7B
                VK_F13  =  0x7C
                VK_F14  =  0x7D
                VK_F15  =  0x7E
                VK_F16  =  0x7F
                VK_F17  =  0x80
                VK_F18  =  0x81
                VK_F19  =  0x82
                VK_F20  =  0x83
                VK_F21  =  0x84
                VK_F22  =  0x85
                VK_F23  =  0x86
                VK_F24  =  0x87
            
                VK_NUMLOCK  =  0x90
                VK_SCROLL  =  0x91
            
                VK_LEFT_SHIFT  =  0xA0
                VK_RIGHT_SHIFT  =  0xA1
                VK_LEFT_CTRL  =  0xA2
                VK_RIGHT_CTRL  =  0xA3
                VK_LEFT_ALT  =  0xA4
                VK_RIGHT_ALT  =  0xA5
                VK_BROWSER_BACK  =  0xA6
                VK_BROWSER_FORWARD  =  0xA7
                VK_BROWSER_REFRESH  =  0xA8
                VK_BROWSER_STOP  =  0xA9
                VK_BROWSER_SEARCH  =  0xAA
                VK_BROWSER_FAVORITES  =  0xAB
                VK_BROWSER_HOME  =  0xAC
                VK_VOLUME_MUTE  =  0xAD
                VK_VOLUME_DOWN  =  0xAE
                VK_VOLUME_UP  =  0xAF
            
                VK_MEDIA_NEXT_TRACK  =  0xB0
                VK_MEDIA_PREV_TRACK  =  0xB1
                VK_MEDIA_STOP  =  0xB2
                VK_MEDIA_PLAY_PAUSE  =  0xB3
                VK_LAUNCH_MAIL  =  0xB4
                VK_LAUNCH_MEDIA_SELECT  =  0xB5
                VK_LAUNCH_APP1  =  0xB6
                VK_LAUNCH_APP2  =  0xB7
            
                VK_PROCESSKEY  =  0xE5
                VK_PACKET  =  0xE7
                VK_ATTN  =  0xF6
                VK_CRSEL  =  0xF7
                VK_EXSEL  =  0xF8
                VK_EREOF  =  0xF9
                VK_PLAY  =  0xFA
                VK_ZOOM  =  0xFB
                VK_NONAME  =  0xFC
                VK_PA1  =  0xFD
                VK_OEM_CLEAR  =  0xFE
            
                @classmethod
                def getName(cls,id):
                    return cls._names.get(id,None)
    
        VirtualKeyCodes.initialize()
            
    elif sys.platform == 'linux2':
        
        class VirtualKeyCodes(Constants):
        
            @classmethod
            def getName(cls,id):
                return cls._names.get(id,None)
        
        VirtualKeyCodes.initialize()


    
    elif sys.platform == 'darwin':
        class AnsiKeyCodes(Constants):
            ANSI_Equal    = 0x18 
            ANSI_Minus    = 0x1B 
            ANSI_RightBracket         = 0x1E 
            ANSI_LeftBracket          = 0x21 
            ANSI_Quote    = 0x27 
            ANSI_Semicolon            = 0x29 
            ANSI_Backslash            = 0x2A 
            ANSI_Comma    = 0x2B 
            ANSI_Slash    = 0x2C 
            ANSI_Period   = 0x2F 
            ANSI_Grave    = 0x32 
            ANSI_KeypadDecimal        = 0x41 
            ANSI_KeypadMultiply       = 0x43 
            ANSI_KeypadPlus           = 0x45 
            ANSI_KeypadClear          = 0x47 
            ANSI_KeypadDivide         = 0x4B 
            ANSI_KeypadEnter          = 0x4C 
            ANSI_KeypadMinus          = 0x4E 
            ANSI_KeypadEquals         = 0x51 
            ANSI_Keypad0  = 0x52 
            ANSI_Keypad1  = 0x53 
            ANSI_Keypad2  = 0x54 
            ANSI_Keypad3  = 0x55 
            ANSI_Keypad4  = 0x56 
            ANSI_Keypad5  = 0x57 
            ANSI_Keypad6  = 0x58 
            ANSI_Keypad7  = 0x59 
            ANSI_Keypad8  = 0x5B
            ANSI_Keypad9  = 0x5C

            @classmethod
            def getName(cls,id):
                return cls._names.get(id,None)
        
        AnsiKeyCodes.initialize()
        AnsiKeyCodes._keys.remove(AnsiKeyCodes.getID('UNDEFINED'))

        class UnicodeChars(Constants):
            VK_RETURN=0x0003
            RETURN=0x000D
            VK_DELETE= 0x007F # "Delete"
            TAB= 0x0009 # "Tab"
            ESCAPE= 0x001b # "Escape"
            UP= 0xf700 # "Up"
            DOWN= 0xF701 # "Down"
            LEFT= 0xF702 # "Left"
            RIGHT= 0xF703 # "Right"
            F1= 0xF704 # "F1"
            F2= 0xF705 # "F2"
            F3= 0xF706 # "F3"
            F4= 0xF707 # "F4"
            F5= 0xF708 # "F5"
            F6= 0xF709 # "F6"
            F7= 0xF70A # "F7"
            F8= 0xF70B # "F8"
            F9= 0xF70C # "F9"
            F10= 0xF70D # "F10"
            F11= 0xF70E # "F11"
            F12= 0xF70F # "F12"
            F13= 0xF710 # "F13"
            F14= 0xF711 # "F14"
            F15= 0xF712 # "F15"
            F16= 0xF713 # "F16"
            F17= 0xF714 # "F17"
            F18= 0xF715 # "F18"
            F19= 0xF716 # "F19"
            F20= 0xF717 # "F20"
            F21= 0xF718 # "F21"
            F22= 0xF719 # "F22"
            F23= 0xF71A # "F23"
            F24= 0xF71B # "F24"
            F25= 0xF71C # "F25"
            F26= 0xF71D # "F26"
            F27= 0xF71E # "F27"
            F28= 0xF71F # "F28"
            F29= 0xF720 # "F29"
            F30= 0xF721 # "F30"
            F31= 0xF722 # "F31"
            F32= 0xF723 # "F32"
            F33= 0xF724 # "F33"
            F34= 0xF725 # "F34"
            F35= 0xF726 # "F35"
            INSERT= 0xF727 # "Insert"
            DELETE= 0xF728 # "Delete"
            HOME= 0xF729 # "Home"
            BEGIN= 0xF72A # "Begin"
            END= 0xF72B # "End"
            PAGE_UP= 0xF72C # "PageUp"
            PAGE_DOWN= 0xF72D # "PageDown"
            PRINT= 0xF72E # "PrintScreen"
            SCROLL_LOCK= 0xF72F # "ScrollLock"
            PAUSE= 0xF730 # "Pause"
            SYSREQ= 0xF731 # "SysReq"
            BREAK= 0xF732 # "Break"
            RESET= 0xF733 # "Reset"
            STOP= 0xF734 # "Stop"
            MENU= 0xF735 # "Menu"
            VK_MENU = 0x0010 # Menu key on non-apple US keyboards
            USER= 0xF736 # "User"
            SYSTEM= 0xF737 # "System"
            PRINT= 0xF738 # "Print"
            CLEAR_LINE= 0xF739 # "ClearLine"
            CLEAR= 0xF73A # "ClearDisplay"
            INSERT_LINE= 0xF73B # "InsertLine"
            DELETE_LINE= 0xF73C # "DeleteLine"
            INSERT= 0xF73D # "InsertChar"
            DELETE= 0xF73E # "DeleteChar"
            PREV= 0xF73F # "Prev"
            NEXT= 0xF740 # "Next"
            SELECT= 0xF741 # "Select"
            EXECUTE= 0xF742 # "Execute"
            UNDO= 0xF743 # "Undo"
            REDO= 0xF744 # "Redo"
            FIND= 0xF745 # "Find"
            HELP= 0xF746 # "Help"
            MODE= 0xF747 # "ModeSwitch"
            SHIFT     = 0x21E7 # Unicode UPWARDS WHITE ARROW*/
            CONTROL   = 0x2303 # Unicode UP ARROWHEAD*/
            OPTION    = 0x2325 # Unicode OPTION KEY*/
            COMMAND   = 0x2318 # Unicode PLACE OF INTEREST SIGN*/
            PENCIL_RIGHT    = 0x270E # Unicode LOWER RIGHT PENCIL; actually pointed left until Mac OS X 10.3*/
            PENCIL_LEFT= 0xF802 # Unicode LOWER LEFT PENCIL; available in Mac OS X 10.3 and later*/
            CHECK     = 0x2713 # Unicode CHECK MARK*/
            DIAMOND   = 0x25C6 #  Unicode BLACK DIAMOND*/
            BULLET   = 0x2022 # Unicode BULLET*/
            APPLE_LOGO = 0xF8FF# Unicode APPLE LOGO*/    
            
            @classmethod
            def getName(cls,id):
                return cls._names.get(id,None)
        
        UnicodeChars.initialize()
        UnicodeChars._keys.remove(UnicodeChars.getID('UNDEFINED'))


        class VirtualKeyCodes(Constants):
            F1=145 #Keycode on Apple wireless kb
            F2=144 #Keycode on Apple wireless kb
            F3=160 #Keycode on Apple wireless kb
            F4=131 #Keycode on Apple wireless kb
            VK_ISO_SECTION   = 0x0A
            VK_JIS_YEN  = 0x5D
            VK_JIS_UNDERSCORE = 0x5E,
            VK_JIS_KEYPAD_COMMA  = 0x5F,
            VK_JIS_EISU = 0x66,
            VK_JIS_KANA = 0x68
            VK_RETURN   = 0x24
            VK_TAB      = 0x30
            VK_SPACE    = 0x31
            VK_DELETE    = 0x33
            VK_ESCAPE   = 0x35
            VK_COMMAND  = 0x37
            VK_SHIFT    = 0x38
            VK_CAPS_LOCK      = 0x39
            VK_OPTION   = 0x3A
            VK_CONTROL  = 0x3B
            VK_SHIFT_RIGHT    = 0x3C
            VK_OPTION_RIGHT   = 0x3D
            VK_CONTROL_RIGHT  = 0x3E
            VK_FUNCTION      = 0x3F
            VK_F17      = 0x40
            VK_VOLUME_UP     = 0x48
            VK_VOLUME_DOWN   = 0x49
            VK_VOLUME_MUTE   = 0x4A
            VK_F18      = 0x4F
            VK_F19      = 0x50
            VK_F20      = 0x5A
            VK_F5       = 0x60
            VK_F6       = 0x61
            VK_F7       = 0x62
            VK_F3       = 0x63
            VK_F8       = 0x64
            VK_F9       = 0x65
            VK_F11      = 0x67
            VK_F13      = 0x69
            VK_F16      = 0x6A
            VK_F14      = 0x6B
            VK_F10      = 0x6D
            VK_MENU     = 0x6E
            VK_F12      = 0x6F
            VK_F15      = 0x71
            VK_HELP     = 0x72
            VK_HOME     = 0x73
            VK_PAGE_UP  = 0x74
            VK_DEL   = 0x75
            VK_F4       = 0x76
            VK_END      = 0x77
            VK_F2       = 0x78
            VK_PAGE_DOWN     = 0x79
            VK_LEFT     = 0x7B
            VK_UP       = 0x7E
            VK_RIGHT    = 0x7C
            VK_DOWN     = 0x7D      
            VK_F1       = 0x7A
            KEY_EQUAL = 24 
            KEY_MINUS = 27 
            KEY_RIGHT_SQUARE_BRACKET = 30 
            KEY_LEFT_SQUARE_BRACKET = 33 
            KEY_RETURN = 36 
            KEY_SINGLE_QUOTE = 39 
            KEY_SEMICOLAN  = 41 
            KEY_BACKSLASH = 42 
            KEY_COMMA = 43 
            KEY_FORWARD_SLASH = 44 
            KEY_PERIOD = 47 
            KEY_TAB = 48 
            KEY_SPACE = 49 
            KEY_LEFT_SINGLE_QUOTE = 50 
            KEY_DELETE = 51 
            KEY_ENTER = 52 
            KEY_ESCAPE = 53 
            KEYPAD_PERIOD = 65 
            KEYPAD_MULTIPLY = 67 
            KEYPAD_PLUS = 69 
            KEYPAD_CLEAR = 71 
            KEYPAD_DIVIDE = 75 
            KEYPAD_ENTER = 76   # numberpad on full kbd
            KEYPAD_EQUALS = 78 	
            KEYPAD_EQUAL = 81 
            KEYPAD_0 = 82 
            KEYPAD_1 = 83 
            KEYPAD_2 = 84 
            KEYPAD_3 = 85 
            KEYPAD_4 = 86 
            KEYPAD_5 = 87 
            KEYPAD_6 = 88 
            KEYPAD_7 = 89 	
            KEYPAD_8 = 91 
            KEYPAD_9 = 92 
            KEY_F5 = 96 
            KEY_F6 = 97 
            KEY_F7 = 98 
            KEY_F3 = 99 
            KEY_F8 = 100 
            KEY_F9 = 101 	
            KEY_F11 = 103 	
            KEY_F13 = 105 	
            KEY_F14 = 107 	
            KEY_F10 = 109	
            KEY_F12 = 111 
            KEY_F15 = 113 
            KEY_HELP = 114 
            KEY_HOME = 115 
            KEY_PGUP = 116 
            KEY_DELETE = 117 
            KEY_F4 = 118 
            KEY_END = 119 
            KEY_F2 = 120 
            KEY_PGDN = 121 
            KEY_F1 = 122 
            KEY_LEFT = 123 
            KEY_RIGHT = 124 
            KEY_DOWN = 125 
            KEY_UP = 126 
	
	        
            @classmethod
            def getName(cls,id):
                return cls._names.get(id,None)
        
        VirtualKeyCodes.initialize()
        VirtualKeyCodes._keys.remove(VirtualKeyCodes.getID('UNDEFINED'))
    
    class ModifierKeyCodes(Constants):
        _mod_names=['CONTROL_LEFT','CONTROL_RIGHT','SHIFT_LEFT',
                   'SHIFT_RIGHT','ALT_LEFT','ALT_RIGHT',
                   'COMMAND_LEFT','COMMAND_RIGHT','CAPS_LOCK',
                   'MOD_SHIFT','MOD_ALT','MOD_CTRL','MOD_CMD','NUMLOCK','MOD_FUNCTION','MOD_HELP']
        CONTROL_LEFT = 1
        CONTROL_RIGHT = 2
        SHIFT_LEFT = 4
        SHIFT_RIGHT = 8
        ALT_LEFT = 16
        ALT_RIGHT = 32
        COMMAND_LEFT = 64
        COMMAND_RIGHT = 128
        CAPS_LOCK = 256
        MOD_SHIFT=512
        MOD_ALT=1024
        MOD_CTRL=2048
        MOD_CMD=4096
        NUMLOCK=8192
        MOD_FUNCTION=16384
        MOD_HELP=32768            
    ModifierKeyCodes.initialize()
    ModifierKeyCodes._keys.remove(ModifierKeyCodes.getID('UNDEFINED'))
    
    class KeyboardConstants(Constants):
        '''
        Stores internal windows hook constants including hook types, mappings from virtual
        keycode name to value and value to name, and event type value to name.
        '''
    
        _virtualKeyCodes=VirtualKeyCodes()
        
        if sys.platform == 'win32':
            _asciiKeyCodes=AsciiConstants()
        if sys.platform == 'darwin':
            _unicodeChars=UnicodeChars()
            _ansiKeyCodes=AnsiKeyCodes()
            
        _modifierCodes=ModifierKeyCodes()
          
        @classmethod
        def getName(cls,id):
            return cls._names.get(id,None)
    
        @classmethod
        def _getKeyNameAndModsForEvent(cls,keyEvent):
    
            mods= cls.getModifiersForEvent(keyEvent)
    
            vcode_name=KeyboardConstants._virtualKeyCodes.getName(keyEvent.KeyID)
            if vcode_name:
                return vcode_name[3:],mods
    
            if mods is None or ('CONTROL_LEFT' not in mods and 'CONTROL_RIGHT' not in mods):
                ascii_name=KeyboardConstants._asciiKeyCodes.getName(keyEvent.Ascii)
                if ascii_name:
                    if ascii_name[-1] == '_': # it is a number between 0 and 9
                        return ascii_name[1],mods
                    return ascii_name,mods
    
            # TODO: When key mapper falls to this stage, clean up OEM_XXXX mappings that pyHook has.
    
            return keyEvent.GetKey().upper(),mods
    
    
        @classmethod
        def getModifiersForEvent(cls,event):
            return cls._modifierCodes2Labels(event.Modifiers)

        @classmethod
        def _modifierCodes2Labels(cls,mods):
            if mods == 0:
                return []
    
            modconstants=cls._modifierCodes
            modNameList=[]
            for k in modconstants._keys:
                mc=modconstants._names[k]
                if mods&k == k:
                    modNameList.append(mc)
                    mods=mods-k
                    if mods==0:
                        return modNameList
            return modNameList
    
    KeyboardConstants.initialize()
    
    class EyeTrackerConstants(Constants):
        
        FILTER_LEVEL_OFF=0
        FILTER_OFF=0
        FILTER_LEVEL_1=1
        FILTER_LEVEL_2=2
        FILTER_LEVEL_3=3
        FILTER_LEVEL_4=4
        FILTER_LEVEL_5=5
        FILTER_ON=9
    
        FILTER_FILE=10
        FILTER_NET=11
        FILTER_SERIAL=12
        FILTER_ANALOG=13
        FILTER_ALL=14
    
        LEFT_EYE=21
        RIGHT_EYE=22
        UNKNOWN_MONOCULAR=24
        BINOCULAR=23
        BINOCULAR_AVERAGED=25
        BINOCULAR_CUSTOM=26
        SIMULATED_MONOCULAR=27
        SIMULATED_BINOCULAR=28
    
        NO_POINTS=40
        ONE_POINT=41
        TWO_POINTS=42
        THREE_POINTS=43
        FOUR_POINTS=44
        FIVE_POINTS=45
        SEVEN_POINTS=47
        EIGHT_POINTS=48
        NINE_POINTS=49
        THIRTEEN_POINTS=53
        SIXTEEN_POINTS=56
        TWENTYFIVE_POINTS=65
        CUSTOM_POINTS=69
        
        PUPIL_AREA = 70
        PUPIL_DIAMETER = 71
        PUPIL_WIDTH = 72
        PUPIL_HEIGHT = 73
        PUPIL_MAJOR_AXIS = 74
        PUPIL_MINOR_AXIS = 75
        PUPIL_RADIUS = 76
        PUPIL_DIAMETER_MM = 77
        PUPIL_WIDTH_MM = 78
        PUPIL_HEIGHT_MM = 79
        PUPIL_MAJOR_AXIS_MM = 80
        PUPIL_MINOR_AXIS_MM = 81
        PUPIL_RADIUS_MM = 82
    
        AUTO_CALIBRATION_PACING=90
        MANUAL_CALIBRATION_PACING=91
    
        DEFAULT_SETUP_PROCEDURE=100
        TRACKER_FEEDBACK_STATE=101
        CALIBRATION_STATE=102
        VALIDATION_STATE=103
        DRIFT_CORRECTION_STATE=104
        
        CIRCLE_TARGET=121
        CROSSHAIR_TARGET=122
        IMAGE_TARGET=123
        MOVIE_TARGET=124
    
        CALIBRATION_HORZ_1D=130
        CALIBRATION_VERT_1D=131
        CALIBRATION_2D=132
        CALIBRATION_3D=133
    
        PUPIL_CR_TRACKING=140
        PUPIL_ONLY_TRACKING=141
    
        ELLIPSE_FIT=146
        CIRCLE_FIT = 147
        CENTROID_FIT = 148
    
        EYETRACKER_OK=200
        # EYETRACKER_ERROR deprecated for EYETRACKER_UNDEFINED_ERROR
        EYETRACKER_ERROR=201
        EYETRACKER_UNDEFINED_ERROR=201
        # FUNCTIONALITY_NOT_SUPPORTED deprecated for 
        # EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED
        FUNCTIONALITY_NOT_SUPPORTED=202
        EYETRACKER_INTERFACE_METHOD_NOT_SUPPORTED=202
        EYETRACKER_CALIBRATION_ERROR=203
        EYETRACKER_VALIDATION_ERROR=204
        EYETRACKER_SETUP_ABORTED=205
        EYETRACKER_NOT_CONNECTED=206
        EYETRACKER_MODEL_NOT_SUPPORTED=207
        EYETRACKER_RECEIVED_INVALID_INPUT=208
        
    EyeTrackerConstants.initialize()
    
    
    #
    ## Gamepad related
    #
    
    class XInputBatteryTypeConstants(Constants):
        BATTERY_TYPE_DISCONNECTED = 0x00       # The device is not connected. 
        BATTERY_TYPE_WIRED = 0x01              # The device is a wired device and does not 
                                               # have a battery. 
        BATTERY_TYPE_ALKALINE = 0x02           # The device has an alkaline battery. 
        BATTERY_TYPE_NIMH = 0x03	               # The device has a nickel metal hydride battery. 
        BATTERY_TYPE_UNKNOWN = 0xFF            # The device has an unknown battery type. 
    XInputBatteryTypeConstants.initialize() 
    try:
        XInputBatteryTypeConstants._keys.remove(XInputBatteryTypeConstants.getID('UNDEFINED'))
    except:
        pass
    
    class XInputBatteryLevelConstants(Constants):
        # BatteryLevels
        BATTERY_LEVEL_EMPTY = 0x00
        BATTERY_LEVEL_LOW = 0x01
        BATTERY_LEVEL_MEDIUM = 0x02
        BATTERY_LEVEL_FULL = 0x03
    
    XInputBatteryLevelConstants.initialize()
    try:
        XInputBatteryLevelConstants._keys.remove(XInputBatteryLevelConstants.getID('UNDEFINED'))
    except:
        pass
    
    class XInputGamePadConstants(Constants):
        DPAD_UP = 0x0001
        DPAD_DOWN = 0x0002
        DPAD_LEFT = 0x0004
        DPAD_RIGHT = 0x0008
        START = 0x0010
        BACK = 0x0020
        LEFT_THUMB = 0x0040
        RIGHT_THUMB = 0x0080
        LEFT_SHOULDER = 0x0100
        RIGHT_SHOULDER = 0x0200
        A = 0x1000
        B = 0x2000
        X = 0x4000
        Y = 0x8000
    
        _batteryTypes=XInputBatteryTypeConstants()
        _batteryLevels=XInputBatteryLevelConstants()
        
    XInputGamePadConstants.initialize()
    try:
        XInputGamePadConstants._keys.remove(XInputGamePadConstants.getID('UNDEFINED'))
    except:
        pass
            
except:
    from . import printExceptionDetailsToStdErr
    printExceptionDetailsToStdErr()
    
#class SerialConstants(Constants):
#    import serial
#    XON=serial.XON
#    XOFF=serial.XOFF
#
#    CR=serial.CR
#    LF=serial.LF
#
#    PARITY_NONE=serial.PARITY_NONE
#    PARITY_EVEN=serial.PARITY_EVEN
#    PARITY_ODD=serial.PARITY_ODD
#    PARITY_MARK=serial.PARITY_MARK
#    PARITY_SPACE=serial.PARITY_SPACE
#
#    STOPBITS_ONE=serial.STOPBITS_ONE
#    STOPBITS_ONE_POINT_FIVE=serial.STOPBITS_ONE_POINT_FIVE
#    STOPBITS_TWO=serial.STOPBITS_TWO
#
#    FIVEBITS=serial.FIVEBITS
#    SIXBITS=serial.SIXBITS
#    SEVENBITS=serial.SEVENBITS
#    EIGHTBITS=serial.EIGHTBITS
#
#SerialConstants.initialize()
#SerialConstants._keys.remove(SerialConstants.getID('UNDEFINED'))
