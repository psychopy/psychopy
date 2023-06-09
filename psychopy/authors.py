"""
Author objects for everyone who has contributed to PsychoPy. Add yourself here and then you can credit
your contributions by importing `psychopy.authors` and pointing __author__ to your Author object.
"""

from psychopy.tools.authortools import Author

# OST staff
peircej = Author(
    forenames=["Jon"], surname="Peirce",
    email="jon@opensciencetools.org", github="peircej",
    other={'ORCiD': "0000-0002-9504-4342"}
)
TEParsons = Author(
    forenames=["Todd", "Ethan"], surname="Parsons",
    email="todd@opensciencetools.org", github="TEParsons",
    other={'ORCiD': "0000-0002-6192-8414",
           'Website': "toddparsons.co.uk"}
)
mdcutone = Author(
    forenames=["Matthew", "D"], surname="Cutone",
    email="matthew@opensciencetools.org", github="mdcutone"
)
isolver = Author(
    forenames=["Sol"], surname="Simpson",
    email="sol@opensciencetools.org", github="isolver"
)
RHirst = Author(
    forenames=["Rebecca"], surname="Hirst",
    email="becca@opensciencetools.org", github="RHirst"
)
kimDundas = Author(
    forenames=["Kimberley"], surname="Dundas",
    email="kim@opensciencetools.org", github="kimDundas"
)
suelynnmah = Author(
    forenames=["Sue", "Lynn"], surname="Mah",
    email="suelynn@opensciencetools.org", github="suelynnmah"
)
wakecarter = Author(
    forenames=["Wakefield"], surname="Morys-Carter",
    email="wakefield@opensciencetools.org", github="wakecarter",
    other={'Website': "https://moryscarter.com/"}
)
apitoit = Author(
    forenames=["Alain"], surname="Pitoit",
    email="alain@opensciencetools.org", github="apitoit"
),
lightest = Author(
    forenames=["Nikita"], surname="Agafonov",
    email="nikita@opensciencetools.org", github="lightest"
)

# former OST staff
dvbridges = Author(
    forenames=["David"], surname="Bridges",
    email="david-bridges@hotmail.co.uk", github="dvbridges"
)
tpronk = Author(
    forenames=["Thomas"], surname="Pronk",
    github="tpronk"
)
thewhodidthis = Author(
    forenames=["Sotiri"], surname="Bakagiannis",
    github="thewhodidthis"
)

# stakeholders
mmacaskill = Author(
    forenames=["Michael"], surname="MacAskill",
    github="m-macaskill",
    other={'Website': "http://www.nzbri.org/people/macaskill"}
)
jeremygray = Author(
    forenames=["Jeremy", "R"], surname="Gray",
    email="jrgray@gmail.com", github="jeremygray"
)
hoechenberger = Author(
    forenames=["Richard"], surname="Höchenberger",
    email="richard.hoechenberger@gmail.com", github="hoechenberger",
    other={'Website': "https://hoechenberger.net/",
           'Mastodon': "@hoechenberger@mastodon.social"}
)
AHaffey = Author(
    forenames=["Anthony"], surname="Haffey"
)

# other contributors
VHaenel = Author(
    forenames=["Valentin"], surname="Haenel"
)
RSharman = Author(
    forenames=["Rebecca"], surname="Sharman"
)
JRoberts = Author(
    forenames=["John"], surname="Roberts"
)

# gotta credit myself for this attribution system...
__author__ = TEParsons
