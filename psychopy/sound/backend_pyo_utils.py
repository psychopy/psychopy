import sounddevice


def get_devices_infos():
    devices = sounddevice.query_devices()
    in_devices = {}
    out_devices = {}
    for id, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            param = {'host api index':device['hostapi'],
                     'latency':device['default_low_input_latency'],
                     'default sr':device['default_samplerate'],
                     'name':device['name']}
            in_devices[id] = param
        if device['max_output_channels'] > 0:
            param = {'host api index':device['hostapi'],
                     'latency':device['default_low_output_latency'],
                     'default sr':device['default_samplerate'],
                     'name':device['name']}
            out_devices[id] = param
    return (in_devices, out_devices)

def get_output_devices():
    devices = sounddevice.query_devices()
    names = []
    ids = []
    for id, device in enumerate(devices):
        if device['max_output_channels'] > 0:
            names.append(device['name'])
            ids.append(id)
    return (names, ids)

def get_input_devices():
    devices = sounddevice.query_devices()
    names = []
    ids = []
    for id, device in enumerate(devices):
        if device['max_input_channels'] > 0:
            names.append(device['name'])
            ids.append(id)
    return (names, ids)