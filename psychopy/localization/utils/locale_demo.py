"""demo for developers on how the localization function _( ) works
"""

from psychopy import localization
import sys

if not sys.platform.startswith('win'):
    langs = ['en_NZ', 'ja_JP', 'wonky']
else:
    langs = ['ENZ', 'JPN', 'wonky']

welcome = 'Welcome to PsychoPy2!'
for lang in langs:
    print 'Set language: >>', localization.init(lang), '<<'
    print _(welcome) # localized if a .mo file was found for lang during init()
    print _(welcome + '   *')  # not localized due to trailing stuff
    print _(welcome) + '   *'  # localize first then append stuff
    print _('pass through stuff that has not been translated')
    print 'normal print is a normal print'
    print