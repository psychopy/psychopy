from psychopy import *
from psychopy import _parallel
import pygame

win=visual.Window([600,600])
win.update()

tick = sound.Sound('tada',secs=0.01)
LPT1 = 0x378#address for parallel port 
_parallel.out(LPT1, 0)#set all pins low

pygame.event.clear()

##this takes 22-26ms
#while True:
#    pygame.event.pump()
#    if len(event.getKeys()):#psychopy's event module
#        break

##this takes 22-24ms (not using  a buffer but direct current keys)
#while True:    
#    pygame.event.pump()
#    keys = pygame.key.get_pressed()[0:100]
#    if sum(keys)>0: break

##mouse is sometimes quicker, but more variable (ranges 15-25ms)
while True:
    pygame.event.pump()
    if sum(pygame.mouse.get_pressed())>0:
        break

tick.play()
_parallel.out(LPT1, 1)#set pin 2 high  
#print keys                   
core.wait(0.01)
_parallel.out(LPT1, 0)#set pin 2 high  

