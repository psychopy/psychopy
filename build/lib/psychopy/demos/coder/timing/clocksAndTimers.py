from psychopy import core
core.wait(0.5)#give the system time to settle

#create a clock
clock=core.Clock()
clock.reset()#whenever you like

#to create a timer you can 'add' time to the zero point
#and wait to get back to zero
timer=core.Clock()
timer.add(3)

#there's also a countdown timer (just a flip of the clock)
countDown = core.CountdownTimer()
countDown.add(3)

another = core.Clock()

print "down       up          clock"
while countDown.getTime()>0:
    print "%.4f   %.4f   %.4f" %(countDown.getTime(), timer.getTime(), clock.getTime())
    core.wait(0.2)#this combined with the print will allow a gradual timing 'slip'

#use the timer, rather than wait(), to prevent the slip
print "\ndown          clock"
timer.reset()
timer.add(0.2)
countDown.add(3)
while countDown.getTime()>0:
    print "%.4f   %.4f" %(countDown.getTime(), clock.getTime())
    while timer.getTime()<0: #includes the time taken to print
        pass
    timer.add(0.2)
print "The last run should have been precise to the microsecond? :-)"
