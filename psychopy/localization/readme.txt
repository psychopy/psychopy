"""
Localizing text strings in PsychoPy

Notes by Jeremy R. Gray

Sources:
  - https://www.supernifty.org/blog/2011/09/16/python-localization-made-easy/
  - https://bip.weizmann.ac.il/course/python/PyMOTW/PyMOTW/docs/gettext/
  - https://webtranslateit.com/en/docs/file_formats/gettext_po/
  - windows mappings: https://msdn.microsoft.com/en-us/goglobal/bb896001.aspx
  - python future: https://hg.python.org/cpython/file/ed62c4c70c4d/Lib/locale.py


Intended usage:
  - early in loading the app, e.g., in _psychopyApp.PsychoPyApp.OnInit(), do:
      from psychopy.app.localization import _translate
    This should be done after importing wx
  - this will: 1) detect the system default or preferred (pref) locale;
    2) initialize the locale setting globally; and 3) make _translate available
    in the module. (Feb 2016: move away from using __builtins__._translate)
  - currently both the standard gettext and wxPython version are used

Known limitations (July 2014):
  - only strings are localized, not number format (separator , or .), currency, etc
  - PsychoPy uses the nonstandard name, _translate(), to avoid a name conflict with
    a dummy variable _, which is sometimes used as a placeholder when unpacking
    tuples or lists. PsychoPy depends on several packages, and some of them use
    _ as a dummy variable, which is quite widespread as a practice, unfortunately.
  - not sure how right-to-left languages work
  - use for localizing the app (PsychoPy), not for localizing user scripts.

Files:
  - psychopy/app/locale/LANG/LC_MESSAGES/ holds the text files and translations,
    where LANG is a 5 letter code like en_UK or ja_JP. poedit will re-make *.mo
    next to *.po.
    Such directories will be auto-detected by PsychoPy in users prefs -> app -> locale

Process:
Do once:
- edit the .py files to add _translate() around text strings to be localized
  e.g.: replace 'Welcome to PsychoPy3!' with _translate('Welcome to PsychoPy3!')
  This process is mostly complete, but might be needed for new code.
- use poedit to open a specific message catalog (*.po file).
  In poedit "properties", add _translate as one of the "Sources keywords"
  To refresh the list of strings to be translated, in poedit click "Catalog menu > Update from sources"

  poedit will do the following automatically, and is much easier than doing by hand:
  To discover all instances of _translate() and dump to a file messages.pot (name customizable)
    $ pybabel extract --no-default-keywords -k _translate --no-wrap --project=PsychoPy --sort-by-file -o messages.pot ..
- edit messages.pot manually if needed, fill in various fields for the app.
- messages.pot is now a template, copy to each destination LANG directory:
   $ cp messages.pot ../app/locale/LANG/LC_MESSAGES/messages.po

human translation:
- doing a translation well requires a strong understanding of PsychoPy itself, especially
  to know what are technical terms (like Routine) and so should not be translated, and to
  know the context of messages and hints, which can be snippets
- edit psychopy/app/locale/LANG/LC_MESSAGES/messages.po to have the desired translations.
  Use poEdit from https://poedit.net/ or (debian-based) "sudo apt-get install poedit"

generate .mo (binary) from .po (text):
- use poedit (easiest): update catalog
- by hand (not recommended): use utils/msgfmt or utils/pomo.py (watch for _translate vs _)

Notes:
- *.po files and utils are not needed by end users
- could distribute translations separately from PsychoPy itself
"""
