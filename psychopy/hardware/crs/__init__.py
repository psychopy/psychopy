from psychopy import logging
from bits import BitsSharp, BitsPlusPlus
from colorcal import ColorCAL
# Monkey-patch our metadata into CRS class.
setattr(ColorCAL,"longName","CRS ColorCAL")
setattr(ColorCAL,"driverFor",["colorcal"])
