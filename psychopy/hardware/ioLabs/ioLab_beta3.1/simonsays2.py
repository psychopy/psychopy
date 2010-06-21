
from ioLabs import USBBox, REPORT
import time

# run a basic "simon says" program

BUTTON_COLORS=['black','red','orange','yellow','green','blue','purple','white']

def flash(usbbox,led_mask=0xFF,rate=1,count=1):
    '''flash (turn off/on/off) the LEDs indicated by the mask (default it all LEDs)'''
    
    # ensure light off first
    usbbox.leds.state=0x00
    for i in xrange(count):
        usbbox.leds.state=led_mask
        time.sleep(rate/2.0)
        usbbox.leds.state=0x00
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
        flash(usbbox,led_mask=(1<<i))
    time.sleep(0.25)
    
    # turn on LEDs
    usbbox.leds.state=0xFF
    time.sleep(0.5)
    
    # lights off signals start
    usbbox.leds.state=0x00
    
    # enable loopback (LEDs turn on in response to user button presses)
    usbbox.enable_loopback()
    
    # reset clock
    usbbox.reset_clock()
    
    # get new events and look to see what keys the user has pressed
    correct = True
    
    # wait for key down events and see whether the
    # key code matches the order we specified earlier
    keyevents=[]
    for i in order:
        while True:
            keydown=usbbox.wait_for_keydown()
            if keydown is None:
                continue # no key pressed yet
            elif i != keydown.key_code:
                correct=False
            keyevents.append(keydown)
            break
        
        if not correct:
            break
    
    # reset the loop back
    usbbox.disable_loopback()
    
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
usbbox.leds.logic=0xFF
# and turn off the LEDs
usbbox.leds.state=0x00
# ensure loop back isn't set
usbbox.disable_loopback()
    
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

