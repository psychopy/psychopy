
from ioLabs import USBBox, REPORT
import time

# run a basic "simon says" program

LED_MASKS=[0x01,0x02,0x04,0x08,0x10,0x20,0x40,0x80]
BUTTON_COLORS=['black','red','orange','yellow','green','blue','purple','white']

def flash(usbbox,led_mask=0xFF,rate=1,count=1):
    '''flash (turn off/on/off) the LEDs indicated by the mask (default it all LEDs)'''
    
    # ensure light off first
    usbbox.commands.p2set(0x00)
    for i in xrange(count):
        usbbox.commands.p2set(led_mask)
        time.sleep(rate/2.0)
        usbbox.commands.p2set(0x00)
        time.sleep(rate/3.0)


def simon_says(usbbox,num):
    '''
    show the user a sequence then see whether they repeat it
    correctly.
    works as follows
    1. flash all LEDs once to signal the sequence will be shown
    2. show sequence
    3. flash all LEDs once to signal sequence done
    4. let user enter sequence (exiting when done or an error spotted)
    5. flash LEDs once if user got sequence right or flash repeatedly if they didn't
    '''
    
    # create a random sequence (0-7)
    import random
    order=[random.choice(xrange(8)) for i in range(num)]
    print "simon says:", " ".join([BUTTON_COLORS[i] for i in order])
    
    # flash LEDs once
    flash(usbbox)
    time.sleep(0.25)
    # show sequence
    for i in order:
        flash(usbbox,led_mask=LED_MASKS[i])
    time.sleep(0.25)
    
    # turn on LEDs
    usbbox.commands.p2set(0xFF)
    time.sleep(0.5)
    # ensure we process anything pending on the queue
    usbbox.process_received_reports()
        
    # then setup the callbacks (so we only hear about reports that happen after this point)
    keyevents=[]
    def key_press(report):
        keyevents.append(report)
    def key_report(report):
        keyevents[:]=[] # clear list to ensure we only have key presses after the KEYREP
    usbbox.commands.add_callback(REPORT.KEYDN,key_press)
    usbbox.commands.add_callback(REPORT.KEYREP,key_report)
    
    # lights off signals start
    usbbox.commands.p2set(0x00)
    
    # enable loopback (LEDs turn on in response to user button presses)
    usbbox.commands.dirset(1,0,0)
        
    # reset clock (also triggers KEYREP)
    usbbox.commands.resrtc()
    
    # get new events and look to see what keys the user has pressed
    correct = False
    done = False
    while not done:
        usbbox.process_received_reports()
        for i,event in zip(order,keyevents):
            if i != event.key_code:
                # wrong key pressed
                done=True
                break
        if not done:
            if len(keyevents) == len(order):
                # got it right (as above check didn't fail)
                done=True
                correct=True
            elif len(keyevents) > len(order):
                # too many pressed (got it wrong)
                done=True
        time.sleep(0.1)
    
    # remove the callbacks installed earlier (they won't do anything outside this function call)
    usbbox.commands.remove_callback(REPORT.KEYDN,key_press)
    usbbox.commands.remove_callback(REPORT.KEYDN,key_report)
    
    # reset the loop back
    usbbox.commands.dirset(0,0,0)
    
    time.sleep(0.5)
    
    # show result to user on box
    if correct:
        # as we reset the clock after the lights went out
        # the "rtc" (real-time clock) value of the last pressed key
        # should tell us how long the user took to press all of the
        # buttons
        last_press=keyevents[-1].rtc
        print "correct (%dms)" % last_press
        flash(usbbox)
    else:
        print "user said:", " ".join([BUTTON_COLORS[event.key_code] for event in keyevents])
        print "wrong"
        flash(usbbox,rate=0.25,count=3)
    
    return correct

usbbox=USBBox()

print "Simon Says"
print "consists of several rounds of sequences being shown:"
print "1) LEDs will flash on box"
print "2) a sequence of LEDs will be shown"
print "3) after the sequence finishes the LEDs will flash again"
print "4) enter in the sequence previously shown (press the buttons that match the LEDs)"
print "5) if you get it right the LEDs will flash once and it'll repeat the cycle (with one more item to remember)"
print "6) if you get it wrong the LEDs will flash three times and you'll be asked if you want to play a new game"

# use logset so that 1 turns LED on and 0 turn LED off
usbbox.commands.logset(0xFF,0xFF)
# and turn off the LEDs
usbbox.commands.p2set(0x00)
# ensure loop back isn't set
usbbox.commands.dirset(0,0,0)
    
while True:
    command=raw_input("play game y/n [y]: ").strip()
    if command == '':
        command = 'y'
    if command.lower() != 'y':
        break
    
    for i in range(1,50):
        time.sleep(1)
        print "%d to remember" % i
        if not simon_says(usbbox,i):
            break

