class BBTKForcePad:
    def __init__(self, server=None, port="COM5", interval=0.001):
        self.port = port
        self.interval = interval

        self.server = server

    def getEvents(self, clear=True):
        return self.device.getEvents(clearEvents=clear)

    @property
    def device(self):
        """
        ioHub device corresponding to this BBTK Force Pad
        """
        if self.server is not None:
            return self.server.getDevice("bbtk_force_pad")

    @property
    def config(self):
        """
        Configuration dict to pass to ioHub when starting up.
        """
        return {
            'serial.Serial':
                {
                    'name': 'bbtk_force_pad',
                    'monitor_event_types': [
                        'SerialInputEvent', 'SerialByteChangeEvent'
                    ],
                    'port': self.port,
                    'baud': 223300,
                    'bytesize': 8,
                    'parity': 'NONE',
                    'stopbits': 'ONE',
                    'event_parser': {
                        'fixed_length': 12,
                        'prefix': None,
                        'delimiter': None,
                        'byte_diff': False
                    },
                    'device_timer': {
                        'interval': self.interval
                    },
                    'enable': True,
                    'save_events': True,
                    'stream_events': True,
                    'auto_report_events': True,
                    'event_buffer_length': 1024,
                    'manufacturer_name': 'BlackBox Toolkit',
                    'model_name': 'Force Pad',
                    'device_number': 0
                }
        }
