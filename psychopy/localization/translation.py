import logging
import gettext
from pathlib import Path
import locale


__all__ = [
    "localedir",
    "getLocale",
    "setLocale",
    "_translate"
]


# work out localedir
localedir = str(Path(__file__).parent / "locales")
# setup locales
gettext.bindtextdomain(
    "messages", 
    localedir=localedir
)
# global for settable locale
currentLocale = None
translator = None


def getLocale():
    """
    Get the current locale
    """
    return currentLocale


def setLocale(value):
    """
    Set the current locale
    """
    global currentLocale
    global translator
    # if requested system, get system locale
    if value in (None, "system locale", "system"):
        value = locale.getlocale()[0]
    # use English as a fallback if locale is undetectable
    if value is None:
        logging.warning(
            "Could not detect system locale, using en-US"
        )
        value = "en-US"
    # sanitize
    value = value.replace("_", "-")
    # set
    currentLocale = value
    # recreate translator
    try:
        translator = gettext.translation(
            "messages", 
            localedir=localedir, 
            languages=[currentLocale]
        )
    except FileNotFoundError:
        # if there's no translations for this language, don't translate
        translator = None

def _translate(value):
    """
    Wrapper around i18next.trans which translates to the current locale
    """
    if translator:
        return translator.gettext(value)
    else:
        return value


# default to system locale
setLocale(None)
