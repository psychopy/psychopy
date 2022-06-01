.. _phidgetRelayComponent:

Phidget Relay Component
--------------

This component allows you to to control a Phidget Relay.

Please install the standard Phidgets (22) drivers, and install the python library Phidgets22

Properties
~~~~~~~~~~

Name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start :
    The time that the relay should turn "on"

Stop :
    The time that the relay should turn "off"

Sync to screen : bool
    Whether to synchronize the relay on/off to the screen refresh. 
    This ensures better synchronization with visual stimuli.

Hardware
========
Parameters for controlling hardware.


serialNumber : integer
    Phidgets have a unique serial number. If you have multiple Phidgets devices connected to your computer,
    it's important to specify which device you want this component to control. Otherwise, use -1.

channelList : list
    Phidget relay devices have more than one relay. Specify which ones you want this component to control
    using a list looking like [#,#,#] for multiple relays or [#] for a single relay
    
reversedRelay : boolean
    Relays have two circuits, one that is "normally closed" and one that is "normally open". In the unpowered, 
    disconnected state, the "normally closed" circuit is complete and current will flow through it. Typically, 
    turning a relay "on" changes the circle to the "normally open" circuit. In some cases, you want a relay to 
    default to the "Normally Open" circuit except for when it is activated (e.g., a relay that limits power to
    the rest of your setup). If you want a circuit to be in the "Normally Open" state except where specified
    you would "reverse the relay"
    