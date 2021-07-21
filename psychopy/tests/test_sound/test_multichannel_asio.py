#  in this test we're deliberately changing the sound lib in preferences which needs to be done before importing sound
#  (otherwise the sound will be imported thinking it's a different preferred lib)
from psychopy import prefs
prefs.general['audioLib'] = ['sounddevice'] # noqa
from psychopy import sound
import numpy as np
from psychopy import core  # import some libraries from PsychoPy


fs = 44100
my_asio_device = 'ASIO Fireface USB'

all_devices = sound.backend.sd.query_devices()
device_found = np.any([_d['name'] == my_asio_device for _d in all_devices])
if not device_found:
    print('device {:} not found'.format(my_asio_device))
else:
    sound.backend.sd.default.device = my_asio_device
    sound.setDevice(my_asio_device)
    sound_device_channels = [1, 4, 5, 6]
    sound.backend.sd.default.device = 'ASIO Fireface USB'
    sound.backend.sd.mapping = None
    extra_settings = sound.backend.sd.AsioSettings(channel_selectors=sound_device_channels)
    sound.backend.sd.default.extra_settings = extra_settings
    y = np.sin(2 * np.pi * 500 * np.arange(0, 1, 1 / fs))
    y = np.vstack((y, y, y, y))
    a = sound.Sound(value=y.T, sampleRate=fs)
    a.play()
    core.wait(4.0)
    core.quit()
