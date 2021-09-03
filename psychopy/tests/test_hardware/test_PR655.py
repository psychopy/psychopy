from psychopy import core, logging, hardware
import pytest

logging.console.setLevel(logging.DEBUG)

def test_PR655():
    pr655 = hardware.findPhotometer(device='PR655')
    if pr655 is None:
        logging.warning('no device found')
    else:
        print(('type:', pr655.type))
        print(('SN:', pr655.getDeviceSN()))
        #on linux we do actually find a device that returns 'D'
        if pr655.type=='D':
            pytest.skip()
        pr655.measure()
        print(('lum', pr655.lastLum))
        print(('uv',pr655.lastUV))
        print(('xy', pr655.lastXY))
        print(('tristim', pr655.lastTristim))
        nm, spec = pr655.getLastSpectrum()
        print(('nm', nm))
        print(('spec', spec))
        print(('temperature', pr655.lastColorTemp))

    print('DONE')
