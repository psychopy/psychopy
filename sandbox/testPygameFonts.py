from psychopy import *
import pygame

myWin = visual.Window([600,600])
print pygame.font.get_init()

print pygame.font.get_default_font()
myFont = pygame.font.SysFont('freesansbold.ttf', 15)
messge = myFont.render('hello', 0, [1,1,1,1])

myWin.update()
core.wait(5)