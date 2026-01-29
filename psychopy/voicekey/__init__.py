from psychopy.localization import _translate
from psychopy.plugins import PluginStub
from psychopy import logging


logging.warning(_translate(
    "psychopy.voicekey is no longer maintained, please use psychopy.hardware.soundSensor instead"
))


class VoiceKeyException(
    PluginStub, 
    plugin="psychopy-legacy", 
    docsHome="https://psychopy.github.io/psychopy-legacy"
):
    pass


class SimpleThresholdVoiceKey(
    PluginStub, 
    plugin="psychopy-legacy", 
    docsHome="https://psychopy.github.io/psychopy-legacy"
):
    pass


class OnsetVoiceKey(
    PluginStub, 
    plugin="psychopy-legacy", 
    docsHome="https://psychopy.github.io/psychopy-legacy"
):
    pass


class OffsetVoiceKey(
    PluginStub, 
    plugin="psychopy-legacy", 
    docsHome="https://psychopy.github.io/psychopy-legacy"
):
    pass


class Recorder(
    PluginStub, 
    plugin="psychopy-legacy", 
    docsHome="https://psychopy.github.io/psychopy-legacy"
):
    pass


class Player(
    PluginStub, 
    plugin="psychopy-legacy", 
    docsHome="https://psychopy.github.io/psychopy-legacy"
):
    pass
