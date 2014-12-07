Localization (I18N, translation)
==================================

PsychoPy is used worldwide. Starting with v1.81, many parts of PsychoPy itself (the app) can be translated into any language that has a unicode character set. A translation affects what the experimenter sees while creating and running experiments; it is completely separate from what is shown to the subject. Translations of the online documentation will need a completely different approach.

In the app, translation is handled by a function, ``_translate()``, which takes a string argument. (The standard name is ``_()``, but unfortunately this conflicts with _ as used in some external packages that PsychoPy depends on.) The ``_translate()`` function returns a translated, unicode version of the string in the locale / language that was selected when starting the app. If no translation is available for that locale, the original string is returned (= English).

A locale setting (e.g., 'ja_JP' for Japanese) allows the end-user (= the experimenter) to control the language that will be used for display within the app itself. (It can potentially control other display conventions as well, not just the language.) PsychoPy will obtain the locale from the user preference (if set), or the OS.

Workflow: 1) Make a translation from English (en_US) to another language. You'll need a strong understanding of PsychoPy, English, and the other language. 2) In some cases it will be necessary to adjust PsychoPy's code, but only if new code has been added to the app and that code displays text. Then re-do step 1 to translate the newly added strings.

See notes in ``psychopy/app/localization/readme.txt``.

Make a translation (.po file)
------------------------------

As a translator, you will likely introduce many new people to PsychoPy, and your translations will greatly influence their experience. Try to be completely accurate; it is better to leave something in English if you are unsure how PsychoPy is supposed to work.

To translate a given language, you'll need to know the standard 5-character code (see `psychopy/app/localization/mappings`). E.g., for Japanese, wherever LANG appears in the documentation here, you should use the actual code, i.e., "ja_JP" (without quotes).

A free app called poedit is useful for managing a translation. For a given language, the translation mappings (from en_US to LANG) are stored in a .po file (a text file with extension `.po`); after editing with poedit, these are converted into binary format (with extension `.mo`) which are used when the app is running.

- Start translation (do these steps once):

  Start a translation by opening `psychopy/app/locale/LANG/LC_MESSAGE/messages.po` in Poedit. If there is no such .po file, create a new one:

    - make a new directory `psychopy/app/locale/LANG/LC_MESSAGE/` if needed. Your `LANG` will be auto-detected within PsychoPy only if you follow this convention. You can copy metadata (such as the project name) from another .po file.

  Set your name and e-mail address from "Preferences..." of "File" menu. Set translation properties (such as project name, language and charset) from Catalog Properties Dialog, which can be opened from "Properties..." of "Catalog" menu.

  In poedit's properties dialog, set the "source keywords" to include '_translate'. This allows poedit to find the strings in PsychoPy that are to be translated.

  To add paths where Poedit scans .py files, open "Sources paths" tab on the Catalog Properties Dialog, and set "Base path:" to "../../../../../" (= psychopy/psychopy/). Nothing more should be needed.
  If you've created new catalog, save your catalog to `psychopy/app/locale/LANG/LC_MESSAGE/messages.po`.

  Probably not needed, but check anyway: Edit the file containing language code and name mappings, `psychopy/app/localization/mappings`, and fill in the name for your language. Give a name that should be familiar to people who read that language (i.e., use the name of the language as written in the language itself, not in en_US). About 25 are already done.

- Edit a translation:

  Open the .po file with Poedit and press "Update" button on the toolbar to update newly added / removed strings that need to be translated. Select a string you want to translate and input your translation to "Translation:" box. If you are unsure where string is used, point on the string in "Source text" box and right-click. You can see where the string is defined.

- Technical terms should not be translated: Builder, Coder, PsychoPy, Flow, Routine, and so on. (See the Japanese translation for guidance.)

- If there are formatting arguments in the original string (``%s``, ``%(first)i``), the same number of arguments must also appear in the translation (but their order is not constrained to be the original order). If they are named (e.g., ``%(first)i``), that part should not be translated--here ``first`` is a python name.

- If you think your translation might have room for improvement, indicate that it is "fuzzy". (Saving Notes does not work for me on Mac, seems like a bug in poedit.)

- After making a new translation, saving it in poedit will save the .po file and also make an associated .mo file. You need to update the .mo file if you want to see your changes reflected in PsychoPy.

- The start-up tips are stored in separate files, and are not translated by poedit. Instead:

 * copy the default version (named `psychopy/app/Resources/tips.txt`) to a new file in the same directory, named `tips_LANG.txt`. Then replace English-language tips with translated tips. Note that some of the humor might not translate well, so feel free to leave out things that would be too odd, or include occasional mild humor that would be more appropriate. Humor must be respectful and suitable for using in a classroom, laboratory, or other professional situation. Don't get too creative here. If you have any doubt, best leave it out. (Hopefully it goes without saying that you should avoid any religious, political, disrespectful, or sexist material.)

 * in poedit, translate the file name: translate "tips.txt" as "tips_LANG.txt"

- Commit both the .po and .mo files to github (not just one or the other), and any changed files (e.g., `tips_LANG`, `localization/mappings`).


Adjust PsychoPy's code
----------------------------

This is mostly complete (as of 1.81.00), but will be needed for new code that displays text to users of the app (experimenters, not study participants).

There are a few things to keep in mind when working on the app's code to make it compatible with translations. If you are only making a translation, you can skip this section.

- In PsychoPy's code, the language to be used should always be English with American spellings (e.g., "color").

- Within the app, the return value from ``_translate()`` should be used only for display purposes: in menus, tooltips, etc. A translated value should never be used as part of the logic or internal functioning of PsychoPy. It is purely a "skin". Internally, everything must be in en_US.

- Basic usage is exactly what you expect: ``_translate("hello")`` will return a unicode string at run-time, using mappings for the current locale as provided by a translator in a .mo file. (Not all translations are available yet, see above to start a new one.) To have the app display a translated string to the experimenter, just display the return value from the underscore translation function.

- The strings to be translated must appear somewhere in the app code base as explicit strings within ``_translate()``. If you need to translate a variable, e.g., named ``str_var`` using the expression ``_translate(str_var)``, somewhere else you need to explicitly give all the possible values that ``str_var`` can take, and enclose each of them within the translate function. It is okay for that to be elsewhere, even in another file, but not in a comment. This allows poedit to discover of all the strings that need to be translated. (This is one of the purposes of the `_localized` dict at the top of some modules.)

- ``_translate()`` should not be given a null string to translate; if you use a variable, check that it is not '' to avoid invoking ``_translate('')``.

- Strings that contain formatting placeholders (e.g., %d, %s, %.4f) require a little more thought. Single placeholders are easy enough: ``_translate("hello, %s") % name``.

- Strings with multiple formatting placeholders require named arguments, because positional arguments are not always sufficient to disambiguate things depending on the phrase and the language to be translated into: ``_translate("hello, %(first)s %(last)s") % {'first': firstname, 'last': lastname}``

- Localizing drop-down menus is a little more involved. Such menus should display localized strings, but return selected values as integers (``GetSelection()`` returns the position within the list). Do not use ``GetStringSelection()``, because this will return the localized string, breaking the rule about a strict separation of display and logic. See Builder ParamDialogs for examples.

Other notes
-------------

When there are more translations (and if they make the app download large) we might want to manage things differently (e.g., have translations as a separate download from the app).
