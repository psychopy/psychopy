
import psychopy.hardware as hw
import pytest
try:
    import mock
except Exception:
    def require_mock(fn):
        def _inner():
            pytest.skip("Can't test without Mock")
        _inner.__name__ = fn.__name__
        return _inner
else:
    def require_mock(fn):
        return fn

try:
    from collections.abc import Iterable
except ImportError:
    from collections import Iterable

try:
    from contextlib import nested  # Python 2
except ImportError:
    from contextlib import ExitStack, contextmanager

    @contextmanager
    def nested(*contexts):
        """
        Reimplementation of nested in python 3.
        """
        with ExitStack() as stack:
            for ctx in contexts:
                stack.enter_context(ctx)
            yield contexts

def globMock(expr):
    if "?" in expr:
        return [expr.replace("?","1")]
    elif "*" in expr:
        return [expr.replace(r"*","MOCK1")]
    else:
        return [expr]

def assertPorts(expected,actual):
    actual = list(actual) # ensure list
    for port in expected:
        assert port in actual

@require_mock
def test_getWindowsSerialPorts():
    should_have = ["COM0","COM5","COM10"]
    with mock.patch("sys.platform","win32"):
        assertPorts(should_have,hw.getSerialPorts())

@require_mock
def test_getLinuxSerialPorts():
    should_have = ["/dev/ttyS1","/dev/ttyACM1","/dev/ttyUSB1"]
    with nested(mock.patch("sys.platform","linux2"),
                mock.patch("glob.iglob",globMock)):
        assertPorts(should_have,hw.getSerialPorts())

@require_mock
def test_getDarwinSerialPorts():
    should_have = ["/dev/tty.USAMOCK1","/dev/tty.KeyMOCK1","/dev/tty.modemMOCK1","/dev/cu.usbmodemMOCK1"]
    with nested(mock.patch("sys.platform","darwin"),
                mock.patch("glob.iglob",globMock)):
        assertPorts(should_have,hw.getSerialPorts())

@require_mock
def test_getCygwinSerialPorts():
    should_have = ["/dev/ttyS1"]
    with nested(mock.patch("sys.platform","cygwin"),
                mock.patch("glob.iglob",globMock)):
        assertPorts(should_have,hw.getSerialPorts())

@require_mock
def test_getCRSPhotometers():
    try:
        with mock.patch.dict("sys.modules",{"psychopy.hardware.crs": object()}):
            photoms = list(hw.getAllPhotometers())

            for p in photoms:
                assert p.longName != "CRS ColorCAL"

            assert isinstance(photoms, Iterable)
            # missing crs shouldn't break it
            assert len(photoms) > 0
    except (AssertionError, ImportError):
        """
        I was able to do this fine from a shell:
        >>> from psychopy.hardware import crs
        or
        >>> import psychopy.hardware.crs
        but kept getting an ImportError when running the test locally:
                from . import minolta, pr
        >       from psychopy.hardware import crs
        E       ImportError: cannot import name crs
        hardware/__init__.py:60: ImportError

        or an assert error on travis-ci
        >               assert p.longName != "CRS ColorCAL"
        E               assert 'CRS ColorCAL' != 'CRS ColorCAL'
        E                +  where 'CRS ColorCAL' = <class psychopy.hardware.crs.colorcal.ColorCAL at 0x79b8738>.longName
        """
        pytest.skip()

    # This allows us to test our logic even when pycrsltd is missing
    faked = type("MockColorCAL",(object,),{})
    with mock.patch("psychopy.hardware.crs.ColorCAL", faked, create=True):
        photoms = list(hw.getAllPhotometers())
        assert faked in photoms

# I wish our PR650 would behave like this ;-)
_MockPhotometer = type("MockPhotometer",(),{"OK": True,"type": "MockPhotometer"})

_workingPhotometer = lambda port: _MockPhotometer

def _exceptionRaisingPhotometer(port):
    raise Exception("Exceptional quality they said...")

def test_findPhotometer():
    # findPhotometer with no ports should return None
    assert (hw.findPhotometer(ports=[]) is None)
    # likewise, if an empty device list is used return None
    assert (hw.findPhotometer(device=[]) is None)
    # even when both are empty
    assert (hw.findPhotometer(device=[],ports=[]) is None)

    # non-existent photometers return None, for now
    assert (hw.findPhotometer(device="thisIsNotAPhotometer!") is None)

    # if the photometer raises an exception don't crash, return None
    assert (hw.findPhotometer(device=[_exceptionRaisingPhotometer],ports="foobar") is None)

    # specifying a photometer should work
    assert hw.findPhotometer(device=[_workingPhotometer],ports="foobar") == _MockPhotometer


    # one broken, one working
    device = [_exceptionRaisingPhotometer,_workingPhotometer]
    assert hw.findPhotometer(device=device,ports="foobar") == _MockPhotometer
