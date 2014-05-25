"""
Localizing text strings in PsychoPy

Notes by Jeremy R. Gray

Sources:
  - http://www.supernifty.org/blog/2011/09/16/python-localization-made-easy/
  - http://bip.weizmann.ac.il/course/python/PyMOTW/PyMOTW/docs/gettext/
  - https://webtranslateit.com/en/docs/file_formats/gettext_po/
  - utils/{pygettext.py,msgfmt.py,makelocalealias.py} are from python 2.7 (PSF licence)
  - windows mappings: http://msdn.microsoft.com/en-us/goglobal/bb896001.aspx
  - python future: http://hg.python.org/cpython/file/ed62c4c70c4d/Lib/locale.py


Intended usage:
  - very early in loading the app, do:
    from psychopy import localization
  - this will: 1) detect the system default or preferred (pref) locale;
    2) intialize the locale setting globally; and 3) install _() function globally

Known limitations:
  - going forward, when adding more _() into the code there will be eventually be a name
    conflict with the existing dummy variable _, which is sometimes used as a placeholder
    when unpacking tuples or lists. find some of them with: git grep '_,'
    expected effect is that localization will fail, should raise because a string
    held in variable named _ is not callable
  - not sure how right-to-left languages work
  - use intended only for localizing the app (PsychoPy), not for localizing user
    scripts.

Files:
  - res means resource. res_po holds the text files and translations
  - utils/ holds helper scripts for managing localization files and workflow. called 
    manually, not by psychopy.

Process:
Do once:
- edit the .py files to add _() around text strings to be localized
  e.g.:  replace 'Welcome to PsychoPy2!' with _('Welcome to PsychoPy2!')
  (Hint: use git grep -n to find the target strings.)
- run utils/pygettext.py to discover all instances of _() and dump
  to a file messages.pot (name customizable)
    $ python utils/pygettext.py filename.py
  Or more usefully, from within psychopy/psychopy/localization directory:
    $ find .. -name '*.py' | grep -v tests | grep -v localization |  xargs python utils/pygettext.py
- edit messages.pot:
  "Content-Type: text/plain; charset=utf-8\n"
  fill in various fields for the app.
- messages.pot is now a template.

Do these multiple times / multiple files -- want a script to help with the
following for each supported language LANG (en, ja, de, el, ... -- see files):
script:
- cp messages.pot res_po/messages_LANG.po, where LANG is two-character code for language
human:
- find someone who can translate a specific language; that person does the following:
- edit res_po/messages_LANG.po to have the desired translations; e.g.: could use
  poEdit from http://poedit.net or (debian-based) "sudo apt-get install poedit"

scripted using utils/pomo.py:
- generate all .mo files: msgfmt -o res/messages_LANG.mo res_po/messages_LANG.po

Notes:
- could tar cz the res_po directory and utils -- not needed by end users

"""
