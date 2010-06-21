# USB Button Box Python API #

To get started simply import the ioLabs module and create a USBBox instance:

    from ioLabs import USBBox
    
    usbbox=USBBox()

If the physical box is not connected (or cannot be detected for some reason) an 
exception will be raised when you create this USBBox instance.

## USBBox structure ##

See the accompanying `rbox_structure` document about the high-level structure of the box.
This document specified the more object oriented API for accessing the USBBox.

## Sending Commands ##

Once you have the USBBox instance you can send commands to the USBBox.  Commands are
sent via the `commands` member variable and are named after IDs specified in the
boxes manual, only in lower case.  e.g.

    usbbox.commands.resrtc() # send RESRTC (reset realtime clock) command
    usbbox.commands.p2set(0x00) # send P2SET with value 0 (should turn on LEDs)
    usbbox.commands.dirset(1,0,0) # enable loopback mode (button presses turn on LED)

## Receiving reports ##

You can register call-back functions on the `commands` object to receive notification
about reports received from the box.  The actual reports are delivered asynchronously,
but to avoid thread safety issues they are stored on a queue until `process_received_reports`
is called.  As most events are time-stamped they can be processed as needed.

To register a call-back and have it called whenever a key is pressed one can doing something
like:

    import time
    from ioLabs import USBBox, REPORT
    # REPORT contains the report IDs
    
    usbbox=USBBox()
    def mycallback(report):
        print "got a report: %s" % report
    # register callback just for KEYDN reports
    usbbox.commands.add_callback(REPORT.KEYDN,mycallback)
    
    while True:
        usbbox.process_received_reports()
        time.sleep(0.1)

Calling `process_received_reports` in this way ensures that out call-back will be called on the
same thread as the rest of the program - avoiding any nasty surprises with asynchronous data
access.  This should also make it easier for integrating with GUI toolkits.

## Recording reports ##

Instead of registering call-backs one can instead opt to have commands sent to a file, using
the `start_recording` method on the USBBox object.  This takes a list of report IDs to record
and a file to output them to:

    import time
    from ioLabs import USBBox, REPORT

    usbbox=USBBox()
    outfile=open('output.txt')
    # record all events
    usbbox.start_recording(REPORT.ALL_IDS(),outfile)
    time.sleep(30)
    usbbox.stop_recording()
    # output.txt should now contain last 30 seconds or so events

## Miscellaneous ##

The underlying HID device for the USB Button Box is stored in `device` on the USBBox instance.
It can be accessed to manually send commands to the device using it's `set_report(report_data)`
command - simply passing a string of the bytes that should be sent in the report.

