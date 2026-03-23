from i18next import config, trans
from pathlib import Path

__all__ = [
    "getLocale",
    "setLocale",
    "_translate"
]

# setup i18next config
config.fallback_lang = "en-US"
config.locale_path = Path(__file__).parent / "locales"


# settable locale
locale = "ja-JP"

# wrapper to translate to this locale
def _translate(value):
    return trans(value, lang=locale)


def setLocale(value):
    """
    Set the current locale
    """
    global locale
    locale = value


def getLocale():
    """
    Get the current locale
    """
    return locale

