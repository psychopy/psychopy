# -*- coding: utf-8 -*-
"""
Tests timestamp accuracy and event delay of the keyboard event handling
backend specified by KB_BACKEND using a MilliKey device.

* This test / demo requires that a MilliKey device is connected to the computer being tested.

KB_BACKEND must be one of:

    - 'psychopy.event': Use PsychoPy's original pyglet based event handling backend.
    - 'psychopy.keyboard': Use keyboard.Keyboard class running PsychHID based backend.
    - 'psychopy.keyboard.iohub': Use keyboard.Keyboard class running iohub based backend.
    - 'psychopy.iohub': Use the psychopy.iohub event framewok directly.
    - 'psychhid': Use an alternative implementation using PsychHID, only for testing.
"""
import os
import string
from psychopy import core, visual, event
import serial
import numpy
import json
import time

# KB_BACKEND = 'psychopy.event'
KB_BACKEND = 'psychopy.keyboard'
# KB_BACKEND = 'psychopy.keyboard.iohub'
# KB_BACKEND = 'psychopy.iohub'
# KB_BACKEND = 'psychhid'

# Used by 'psychopy.keyboard' and 'psychopy.keyboard.iohub' backends
psychopy_keyboard_waitRelease = False

# Number of keyboard events to generate.
kgen_count = 10

# min, max msec duration for generated keypresses.
min_dur, max_dur = 50, 300

# Update the display each loop
# while waiting for event ...
update_display_while_waiting = True

# Sleep sleep_while_wait each loop
# while waiting for event.
# 0 == no call to sleep
sleep_while_wait = 0


#
# Helper functions
#


def getSerialPorts():
    available = []
    if os.name == 'nt':  # Windows
        for i in range(1, 256):
            try:
                sport = 'COM' + str(i)
                s = serial.Serial(sport, baudrate=128000)
                available.append(sport)
                s.close()
            except (serial.SerialException, ValueError):
                pass
    else:  # Mac / Linux
        from serial.tools import list_ports
        available = [port[0] for port in list_ports.comports()]
    return available


def getMilliKeyDevices():
    devices = []
    available = getSerialPorts()
    for p in available:
        try:
            mkey_sport = serial.Serial(p, baudrate=128000, timeout=1.0)
            while mkey_sport.readline():
                pass
            mkey_sport.write(b"GET CONFIG\n")
            rx_data = mkey_sport.readline()
            if rx_data:
                rx_data = rx_data[:-1].strip()
                try:
                    mkconf = json.loads(rx_data)
                    mkconf['port'] = p
                    devices.append(mkconf)
                except:
                    raise RuntimeError("ERROR: {}".format(rx_data))
            mkey_sport.close()
        except:
            pass
    return devices

#
# Run Test
#


if __name__ == "__main__":
    millikeys = getMilliKeyDevices()
    if len(millikeys) == 0:
        print("No Millikey device detected. Exiting test...")
        core.quit()
    
    mk_serial_port = millikeys[0]['port']
    # min, max msec MilliKey will wait before issuing the requested key press event.
    min_delay, max_delay = 1, 3
    possible_kgen_chars = string.ascii_lowercase + string.digits
    io = None
    ptb_kb = None
    getKeys = None

    # psychhid event timestamps are in psychtoolbox.GetSecs
    # so make test use that timebase.
    getTime = core.getTime
    if KB_BACKEND in ['psychhid', 'psychopy.keyboard']:
        from psychtoolbox import GetSecs
        getTime = GetSecs

    # psychopy.event is used as a secondary backend in case the primary backend
    # being tested (KB_BACKEND) fails to detect a keypress event.
    # Only used if KB_BACKEND != psychopy.event
    backup_getKeys = None
    if KB_BACKEND != 'psychopy.event':
        def backup_getKeys():
            return event.getKeys(timeStamped=True)

    # Create getKeys function to test desired keyboard backend     
    if KB_BACKEND == 'psychopy.event':
        def getKeys():
            return event.getKeys(timeStamped=True)
    elif KB_BACKEND == 'psychopy.keyboard':
        from psychopy.hardware.keyboard import Keyboard as ptbKeyboard
        ptb_kb = ptbKeyboard()
        def getKeys():
            keys = ptb_kb.getKeys(waitRelease=psychopy_keyboard_waitRelease)
            return [(k.name, k.tDown) for k in keys]
    elif KB_BACKEND == 'psychopy.iohub':
        from psychopy.iohub import launchHubServer
        io = launchHubServer()
        def getKeys():
            keys = io.devices.keyboard.getPresses()
            return [(k.key, k.time) for k in keys]
    elif KB_BACKEND == 'psychopy.keyboard.iohub':
        from psychopy.iohub import launchHubServer
        io = launchHubServer()
        from psychopy.hardware.keyboard import Keyboard as ptbKeyboard
        ptb_kb = ptbKeyboard()
        def getKeys():
            keys = ptb_kb.getKeys(waitRelease=psychopy_keyboard_waitRelease)
            return [(k.name, k.tDown) for k in keys]
    elif KB_BACKEND == 'psychhid':
        from psychtoolbox import PsychHID
        ptb_keys = [1] * 256
        PsychHID('KbQueueCreate', [], ptb_keys)
        PsychHID('KbQueueStart')
        
        def getKeys():
            keys = []
            while PsychHID('KbQueueFlush'):
                evt = PsychHID('KbQueueGetEvent')[0]
                if evt['Pressed']:
                    K = chr(int(evt['CookedKey'])).lower()
                    keys.append((K, evt['Time']))
            return keys
    
    def close_backend():
        if KB_BACKEND == 'psychhid':
            PsychHID('KbQueueStop')
        elif io:
            io.quit()

    win = visual.Window([800, 400])  #, fullscr=True, allowGUI=False)
    r = win.getMsPerFrame(60)

    print()
    print("Test Settings: ")
    print("\tEvent backend: ", KB_BACKEND)
    if KB_BACKEND.find('psychopy.keyboard') >= 0:
        print("\tpsychopy_keyboard_waitRelease: ", psychopy_keyboard_waitRelease)
    print("\tupdate_display_while_waiting: ", update_display_while_waiting)
    print("\tsleep_while_wait (sec): ", sleep_while_wait)
    print("\tmin_delay, max_delay (msec): ", (min_delay, max_delay))
    print("\tmin_dur, max_dur (msec): ", (min_dur, max_dur))
    print("\twin.getMsPerFrame(): ", r)
    print()

    ts_errors = numpy.zeros(kgen_count, dtype=numpy.float64)
    evt_delays = numpy.zeros(kgen_count, dtype=numpy.float64)

    mk_sconn = serial.Serial(mk_serial_port, baudrate=128000, timeout=0.01)
    

    txt1 = "Testing %s backend.\nMilliKey Generating Key Press:\n Key: [%s], Duration: %d msec.\n%d of %d events."
    msg = visual.TextStim(win, text=txt1)
    dotPatch = visual.DotStim(win, color=(0.0, 1.0, 0.0), dir=270,
                              nDots=223, fieldShape='sqr',
                              fieldPos=(0.0, 0.0), fieldSize=1.5,
                              dotLife=50, signalDots='same',
                              noiseDots='direction', speed=0.01,
                              coherence=0.9)
    
    def drawAndFlip(txt=None):
        if txt:
            msg.text = txt
        dotPatch.draw()
        msg.draw()
        return win.flip()
    
    drawAndFlip()
    print()
    count = 0
    no_event_count = 0
    while count < kgen_count:
        kchar = possible_kgen_chars[count % (len(possible_kgen_chars))]
        press_duration = int(numpy.random.randint(min_dur, max_dur))
        delay_evt_usec = int(numpy.random.randint(min_delay, max_delay))*1000
        evt_delay_sec = delay_evt_usec/1000.0/1000.0

        drawAndFlip(txt1 % (KB_BACKEND, kchar, press_duration, count+1, kgen_count))

        if ptb_kb:
            ptb_kb.clock.reset()

        # Instruct MilliKey device to:
        #  - generate a key press delay_evt_usec after receiving the KGEN command
        #  - generate key release event press_duration after press event is sent.
        kgen_cmd = "KGEN {} {} {}\n".format(kchar, press_duration, delay_evt_usec).encode()
        mk_sconn.write(kgen_cmd)
        mk_sconn.flush()
        # stime is the time the KGEN command was sent to the MilliKey device.
        # plus the event offset the device is using.
        stime = getTime()+evt_delay_sec

        # Keep checking for key press events until one is received
        kb_presses = getKeys()
        last_check_time = ctime = getTime()
        while not kb_presses:
            if getTime() - ctime > 2.0:
                # Report missed event.
                print("*WARNING: {} did not detect key press '{}' of duration {}.".format(KB_BACKEND, kchar, press_duration))
                if backup_getKeys:
                    presses = backup_getKeys()
                    if presses:
                        print("\tHowever, event.getKeys() received: ", presses)
                no_event_count += 1
                break
            if update_display_while_waiting:
                drawAndFlip()
            if sleep_while_wait > 0:
                time.sleep(sleep_while_wait)
            kb_presses = getKeys()
            last_check_time = getTime()

        # to clear backup getKeys()
        if backup_getKeys:
            _ = backup_getKeys()

        if kb_presses:
            if len(kb_presses) > 1:
                txt = "Error: {} keypress events detected at once: {}\n"
                txt += "Was a keyboard key or MilliKey button pressed during the test?"
                print(txt.format(len(kb_presses), kb_presses))
                close_backend()
                core.quit()
            
            # Get the key name and timestamp of event
            kpress, ktime = kb_presses[0]
        
            # Ensure we got the key we were expecting.....
            if kchar == kpress:
                ts_errors[count] = ktime - stime
                evt_delays[count] = last_check_time-stime
                count += 1
            else:
                txt = "Error: Keyboard Key != Key Press Issued ([{}] vs [{}]).\n"
                txt += "Was a keyboard key or MilliKey button pressed during the test?"
                print(txt.format(kchar, kpress))
                close_backend()
                core.quit()
        
            # Wait until after MilliKey has issued associated key release event.
            ctime = getTime()
            while getTime() - ctime < (press_duration/1000.0)*1.25:
                if update_display_while_waiting:
                    drawAndFlip()
                if sleep_while_wait > 0:
                    time.sleep(sleep_while_wait)
                getKeys()
    
    # Done test, close backend if needed
    close_backend()
    
    mk_sconn.close()
    win.close()
    
    # Print Results
    if no_event_count > 0:
        print()
        print("** WARNING: '%s' missed %d keypress events (%.6f percent)." % (KB_BACKEND, no_event_count,
                                                                              (no_event_count/count)*100))
        print()
    # Convert times to msec.
    evt_results = ts_errors[:count] * 1000.0
    print("%s Timestamp Accuracy Stats" % KB_BACKEND)
    print("\tCount: {}".format(evt_results.shape))
    print("\tAverage: {:.3f} msec".format(evt_results.mean()))
    print("\tMedian: {:.3f} msec".format(numpy.median(evt_results)))
    print("\tMin: {:.3f} msec".format(evt_results.min()))
    print("\tMax: {:.3f} msec".format(evt_results.max()))
    print("\tStdev: {:.3f} msec".format(evt_results.std()))
    print()
    # Convert times to msec.
    evt_results = evt_delays[:count] * 1000.0
    print("%s Keypress Event Delays" % KB_BACKEND)
    print("\tCount: {}".format(evt_results.shape))
    print("\tAverage: {:.3f} msec".format(evt_results.mean()))
    print("\tMedian: {:.3f} msec".format(numpy.median(evt_results)))
    print("\tMin: {:.3f} msec".format(evt_results.min()))
    print("\tMax: {:.3f} msec".format(evt_results.max()))
    print("\tStdev: {:.3f} msec".format(evt_results.std()))
    
    core.quit()
