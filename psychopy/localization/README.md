# Writing code with translated strings

## When to translate?

Most strings don't need translation. Strings defined and used within code won't be visible to the user, and translating them into a different language could break the code (e.g. a `TextBox2` checking whether `direction == "horiz"` wouldn't work if the value of `direction` was translated into a different language). Strings which need translating are ones visible to the user, most often the value of `hint` or `label` in a `Param` object, as these are used in the interface of PsychoPy Studio. 

## How to translate?

To translate a string, just use the `_translate` function from `psychopy/localization`, like so:

```python
from psychopy.localization import _translate


myTranslatedString = _translate("This string will be translated")
```

This means that, when you run your code, the value of `myTranslatedString` will be whatever translation has been defined for `"This string will be translated"` in the language you point to in your prefs file (or your system locale). If there is no translation, the string is used as-is, just the same as if you'd not called `_translate`. So even if you're not sure whether a translation is available, you should still use the `_translate` function for any user-facing strings.

# Adding translations

## Cloning the PsychoPy repo

In order to edit translations, you need to be able to edit the code of PsychoPy. You can find instructions for downloading and editing PsychoPy in the [contributor's section of our website](https://psychopy.org/developers/).

## Key extraction

The first step to translation is to work out what strings need to be translated; this is called "key extraction". We can scan the PsychoPy codebase for any instances where the `_translate` function is called, so by doing so and storing the values it's called on we can compile a list of strings which need translations writing. 

We've already written the code to do this, so to extract keys you just need to run the file "extract.py" as a script. We try to run this ourselves fairly regularly, so there's a good chance all the strings will already be found and so this script will have no effect.

## Translation files

Translation files are `.json` files containing an entry for each string in PsychoPy which neeeds translating, with the value being its translation in a given language. These files are named for the language they correspond to, by their ISO [language code](https://en.wikipedia.org/wiki/List_of_ISO_639_language_codes) and [country code](https://en.wikipedia.org/wiki/List_of_ISO_3166_country_codes), separated by a hyphen (e.g. `en-GB.json` contains translations into English, as spoken in Great Britain). These files are located in `psychopy/localization/locales`.

## Adding translations

As the translation files are `.json` files, you can open and edit them in any text editor. However, there are tools available which offer an easy, visual interface for editing translation files. We recommend [poedit](https://poedit.net/) as it's free, easy to use, and has cross-system support. To add translations, simply open the file for the language you want to provide translations for in your choice of program, and add your translation to the relevant string.

Blank entries in the translation files are strings which we don't have a translation for yet in that language. If you want to contribute to PsychoPy's translations, these are your targets!

## Submitting translations

Once you've made your changes, use git to commit and push the change to your branch of PsychoPy, then you can submit the change as a pull request. See [our guide for opening a pull request](https://psychopy.org/developers/pullrequest). The commit/pull request messages for a change to translations should always begin with `DOC:`.

# Known limitations

- PsychoPy uses a non-standard name (`_translate`) for its translation function; this is to avoid a name conflict with `_` which is often used as a "dummy variable".
- This style of translation just translates the strings it's given; it doesn't affect how the text is positioned on the page or the order in which distinct sentences are presented (which may matter in some, particularly right-to-left, languages)
- This is only for translating labels and other user-facing strings which we can know about in advance, this translation system doesn't apply to user's scripts