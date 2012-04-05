import sys,nose
from contextlib import nested
import psychopy.hardware as hw

try:
    import mock
except:
    def require_mock(fn):
        def _inner():
            raise nose.plugins.skip.SkipTest("Can't test without Mock")
        _inner.__name__ = fn.__name__
        return _inner
else:
    def require_mock(fn):
        return fn

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
def testGetWindowsSerialPorts():
    should_have = ["COM0","COM5","COM10"]
    with mock.patch("sys.platform","win32"):
        assertPorts(should_have,hw.getSerialPorts())

@require_mock
def testGetLinuxSerialPorts():
    should_have = ["/dev/ttyS1","/dev/ttyACM1","/dev/ttyUSB1"]
    with nested(mock.patch("sys.platform","linux2"),
                mock.patch("glob.iglob",globMock)):
       assertPorts(should_have,hw.getSerialPorts())

@require_mock
def testGetDarwinSerialPorts():
    should_have = ["/dev/tty.USAMOCK1","/dev/tty.KeyMOCK1","/dev/tty.modemMOCK1","/dev/cu.usbmodemMOCK1"]
    with nested(mock.patch("sys.platform","darwin"),
                mock.patch("glob.iglob",globMock)):
        assertPorts(should_have,hw.getSerialPorts())

@require_mock
def testGetCygwinSerialPorts():
    should_have = ["/dev/ttyS1"]
    with nested(mock.patch("sys.platform","cygwin"),
                mock.patch("glob.iglob",globMock)):
        assertPorts(should_have,hw.getSerialPorts())