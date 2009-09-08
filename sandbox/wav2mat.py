import pygame, numpy, scipy.io

pygame.mixer.init(44100, -8, 2) #44kHz, signed 16bit, stereo?
snd = pygame.mixer.Sound('pinknoiseburst.wav')
sndArray = pygame.sndarray.array(snd)

scipy.io.savemat('pinknoise.mat', {'pink':numpy.asarray(sndArray)}) #pink will be the variable name
