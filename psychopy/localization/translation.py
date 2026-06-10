import logging
from i18next import config, trans
from pathlib import Path
import locale


__all__ = [
    "getLocale",
    "setLocale",
    "_translate"
]

# setup i18next config
config.fallback_lang = "en-US"
config.locale_path = Path(__file__).parent / "locales"
# global for settable locale
currentLocale = None


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
    # if requested system, get system locale
    if value in (None, "system locale", "system"):
        value = locale.getdefaultlocale()[0]
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


def _translate(value):
    """
    Wrapper around i18next.trans which translates to the current locale
    """
    return trans(value, lang=currentLocale)


# default to system locale
setLocale(None)
