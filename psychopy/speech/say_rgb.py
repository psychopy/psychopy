#!/usr/bin/env python

"""demo: voice capture with google speech recognition"""

import os, sys, time, random
from psychopy import microphone
from psychopy.google_speech import GoogleSpeech, gsOptions

# set speech options:
# on windows, if flac does not install into C:\Program Files\FLAC\flac.exe
# you have to set its install path explicitly
# gsOptions.flac = 'c:\\path\\to\\flac.exe'
# gsOptions.lang = 'en-UK'

def classifyRGB(utterance, conf=0, default='red'):
    """Classify an utterance, using sets of words.
    
    Can greatly enhance accuracy, especially under suboptimal conditions such as
    speeded responses. The default should be the word that is the hardest for
    google to recognize.
    """
    
    if not utterance: # google had no ideas
        print 'None'
        return None
    keyOrder = ['green', 'blue', 'red']
    if utterance[0] in keyOrder:
        print 'best', conf
        return utterance[0]
    utterance = set(utterance)
    match = list(utterance.intersection(set(keyOrder)))
    if match:
        print 'match'
        return match[0]
    # otherwise work a little harder:
    _wordSets = {
        'en-US': # optimized for JRG as a speaker
            {'red': ['red',  'reds', 'rest', 'bread', 'fred', 'breast', 
                'arrest', 'read', 'earth', 'good', 'burt', 'breakfast', 'reddit',
                'rated', 'rooted', 'rent', 'ribs', 'ray', 'bed', 'berg', 'first',
                'craig'],
            'green': ['green', 'greens', 'greene', 'clean', 'cream', 'free', 'greece', 
                'bring', 'french', 'dream', 'print', u'dreams', u'pranks'], 
            'blue': ['blue', 'blues', 'ok', 'book', 'glue', 'hulu', 'boo', 'porn',
                 'both', 'foot', 'boat', 'wood', 'luke', 'food', 'boobs', 'believe',
                 'book', 'look', 'liz', 'voice', 'sports', 'blitz',
                 'quick', 'bird', 'bert', 'was', 'words']}
            # green or red = bird, brent, rent, sprint, chris, great, grant, ring, friend, friends
            # green or blue = please, live
            # red or blue = well
        }
    wordSet = _wordSets['en-US']
    wordCount = {}
    max = (0,None)
    for key in keyOrder:
        wordCount[key] = len(utterance.intersection(set(wordSet[key])))
        if wordCount[key] > max[0]:
            max = (wordCount[key], key)
    if max[0]:
        print max
        return max[1]
    print
    if conf > 0.5: # something was said pretty clearly, but its not in target sets
        return None
    if default:
        return default # something was said, no idea what

captureTime = 1.8

def getSpeechSample():
    rgb = ['red', 'green', 'blue']
    random.shuffle(rgb)
    print '\n  "%s" ' % rgb[0],
    sys.stdout.flush()
    mic = microphone.SimpleAudioCapture() # set-up
    mic.record(captureTime) # capture, save to file
    
    return mic.savedFile, rgb[0] # name of saved file

try:
    microphone.switchOn(sampleRate=16000)
    # 16000 is a good rate for google speech recognition
    # could record faster for archiving, then down-sample to 16K
    
    print "voice capture with google speech recognition, needs internet access"
    print "when you see a color word, say it out loud. this will repeat 10 times."
    score = 0
    for i in xrange(10):
        wavFile, word = getSpeechSample()
        print '.',
        sys.stdout.flush()
        gs = GoogleSpeech(wavFile, gsOptions) # prepare only
        guess = gs.getResponse() # actually query google
        best = classifyRGB(guess.words, guess.confidence)
        correct = [' 0', '+1'][word == best]
        score += eval(correct)
        print correct, best, guess.words, guess.confidence, 'score: %d / %d' % (score, i+1)
        os.remove(wavFile)
finally:
    # try-except is useful to prevent pyo from exploding with a bus error,
    # which its prone to do if any exception is raised, eg KeyboardInterrupt
    time.sleep(captureTime)
    microphone.switchOff()
    

