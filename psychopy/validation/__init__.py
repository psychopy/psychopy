"""
This module contains classes for validating stimulus presentation times using a variety of methods.
"""

from .voicekey import VoiceKeyValidator, VoiceKeyValidationError
from .photodiode import PhotodiodeValidator, PhotodiodeValidationError
