from psychopy import logging
from bits import BitsBox
try:
    from pycrsltd.colorcal import ColorCAL
except ImportError:
    logging.warning("Couldn't import pycrsltd. ColorCAL will not be available")
