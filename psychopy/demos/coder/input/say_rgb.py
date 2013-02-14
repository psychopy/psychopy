#!/usr/bin/env python

"""demo: Voice capture with "red / green / blue" classification via google speech API.

For this demo to work, you need:
    - pyo and flac installed
    - internet access
    - a microphone, turned on (e.g., a built-in microphone on a laptop); full volume seems best
    - a visible text "output" window (especially if running from the Coder)
To work well, you should:
    - wait for the word prompt, say the word clearly and deliberately, avoiding extra noises
    - be in quiet surroundings with no music, random noise, and so on
    - ideally: run this from the command-line, not Coder (can skip first trials)"""

import os, sys, time, random
from psychopy import microphone, core

__author__ = "Jeremy R. Gray"

core.checkPygletDuringWait = False

options = {}
# set speech options:
# on windows, if flac does not install into C:\Program Files\FLAC\flac.exe
# you have to set its install path explicitly
# options['flac_exe'] = 'c:\\path\\to\\flac.exe'
#options['lang'] = 'en-UK'


def classifyRGB(utterance, conf=0, default='red', defaultConf=0.3):
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
            {'red': ['red',  'reds', 'rest', 'bread', 'fred', 'breast', 'craig', 'red red',
                'arrest', 'read', 'earth', 'good', 'burt', 'breakfast', 'reddit', 'ruth', 'rude',
                'rated', 'rooted', 'rent', 'ribs', 'ray', 'bed', 'berg', 'first', 'ray'],
            'green': ['green', 'greens', 'greene', 'clean', 'cream', 'greece', 
                'bring', 'french', 'dream', 'print', 'dreams', 'pranks'], 
            'blue': ['blue', 'blues', 'ok', 'book', 'glue', 'hulu', 'boo', 'blue blue', 'bluetooth',
                 'both', 'foot', 'boat', 'wood', 'luke', 'food', 'believe', 'was', 'words',
                 'book', 'look', 'liz', 'voice', 'sports', 'blitz', 'quick', 'bird', 'bert', 'soup',
                 'hey luv', 'hey luke', 'call luke', 'hi luke', 'balloon', 'loon', 'once', 'bloons']}
            # green or red = bird, brent, rent, sprint, chris, great, grant, ring, friend, friends, free
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
    if conf > defaultConf: # something was said pretty clearly, but its not in target sets
        return None
    if default:
        return default # something was said, no idea what

microphone.switchOn(sampleRate=16000)
# 16000 is a good rate for google speech recognition (16000 or 8000 only)
# could record faster for archiving, then down-sample to 16K

mic = microphone.AudioCapture() # set things up
captureTime = 2

print "\nVoice capture with google speech recognition, needs a microphone and internet access."
print "\nWhen you see a color word, say it out loud (before the '].' appears)."
print "This will repeat 10 times. Your score increases +1 for every word said correctly."
print "\nReady?"
sys.stdout.flush() # not flush()ing reliably for me in Coder

score = 0
rgb = ['red', 'green', 'blue'] * 4
random.shuffle(rgb)
for i in xrange(10):
    # show a random word:
    word = rgb[i]
    print '\n  "%s"  [  ' % word,
    sys.stdout.flush()
    
    # get a voice sample:
    wavFile = mic.record(captureTime)
    print '].',
    sys.stdout.flush()
    
    # get google's interpretation:
    gs = microphone.Speech2Text(wavFile, **options) # prepare
    guess = gs.getResponse() # query google, wait for response; data appear in guess
    # connection lost if you get: WARNING <urlopen error [Errno 8] nodename nor servname provided, or not known>
    
    # classify as most likely to have been red, green, or blue:
    likelyWord = classifyRGB(guess.words, guess.confidence)
    
    # update the score:
    correct = [' 0', '+1'][word == likelyWord]
    score += int(word == likelyWord)
    print correct, likelyWord, guess.words, guess.confidence, 'score: %d / %d' % (score, i+1)
    sys.stdout.flush()
    os.remove(wavFile)

# clean-up sound temp file if present:
try: os.remove(wavFile)
except: pass

print '\nFinal score: %d / %d' % (score, i+1)

core.quit()

