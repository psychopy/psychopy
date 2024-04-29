Cedrus (response boxes)
=============================================

The pyxid package, written by Cedrus, is included in the Standalone |PsychoPy| distributions.

Example usage::

	import pyxid2 as pyxid

    # get a list of all attached XID devices
    devices = pyxid.get_xid_devices()

    dev = devices[0] # get the first device to use
    if dev.is_response_device():
        dev.reset_base_timer()
        dev.reset_rt_timer()

        while True:
            dev.poll_for_response()
            if dev.response_queue_size() > 0:
                response = dev.get_next_response()
                # do something with the response

See https://github.com/cedrus-opensource/pyxid for further info.
