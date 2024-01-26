from psychopy import liaison, session, hardware
from psychopy.hardware import DeviceManager
from psychopy.tests import utils, skip_under_vm
from pathlib import Path
import json
import asyncio
import time


class TestingProtocol:
    """
    Gives Liaison a protocol to communicate with, stores what it receives and raises any errors.
    """
    messages = []

    async def send(self, msg):
        # parse message
        msg = json.loads(msg)
        # store message
        self.messages.append(msg)
        # raise any errors
        if msg.get('type', None) == "error":
            raise RuntimeError(msg['msg'])

        return True

    def clear(self):
        self.messages = []


def runInLiaison(server, protocol, obj, method, *args):
    cmd = {'object': obj, 'method': method, 'args': args}
    asyncio.run(
        server._processMessage(protocol, json.dumps(cmd))
    )

@skip_under_vm
class TestLiaison:
    def setup_class(self):
        # create liaison server
        self.server = liaison.WebSocketServer()
        self.protocol = TestingProtocol()
        self.server._connections = [self.protocol]
        # add session to liaison server
        self.server.registerClass(session.Session, "session")
        runInLiaison(
            self.server, self.protocol, "session", "init",
            str(Path(utils.TESTS_DATA_PATH) / "test_session" / "root")
        )
        runInLiaison(
            self.server, self.protocol, "session", "registerMethods"
        )
        # add device manager to liaison server
        self.server.registerClass(hardware.DeviceManager, "DeviceManager")
        runInLiaison(
            self.server, self.protocol, "DeviceManager", "init"
        )
        runInLiaison(
            self.server, self.protocol, "DeviceManager", "registerMethods"
        )
        # start Liaison
        self.server.run("localhost", 8100)
        # start session
        runInLiaison(
            self.server, self.protocol, "session", "start"
        )
        # setup window
        runInLiaison(
            self.server, self.protocol, "session", "setupWindowFromParams", "{}", "false"
        )

    def test_session_init(self):
        assert "session" in self.server._methods
        assert isinstance(self.server._methods['session'][0], session.Session)

    def test_device_manager_init(self):
        assert "DeviceManager" in self.server._methods
        assert isinstance(self.server._methods['DeviceManager'][0], hardware.DeviceManager)

    def test_basic_experiment(self):
        runInLiaison(
            self.server, self.protocol, "session", "addExperiment",
            "exp1/exp1.psyexp", "exp1"
        )
        time.sleep(1)
        runInLiaison(
            self.server, self.protocol, "session", "runExperiment",
            "exp1"
        )

    def test_experiment_error(self):
        """
        Test that an error in an experiment is sent to Liaison properly
        """
        # run an experiment with an error in it
        runInLiaison(
            self.server, self.protocol, "session", "addExperiment",
            "error/error.psyexp", "error"
        )
        time.sleep(1)
        try:
            runInLiaison(
                self.server, self.protocol, "session", "runExperiment",
                "error"
            )
        except RuntimeError as err:
            # we expect an error from this experiment, so don't crash the whole process
            pass
        # check that the error looks right in Liaison's output
        assert self.protocol.messages[-1]['context'] == "error"

    def test_add_device_with_listener(self):
        # add keyboard
        runInLiaison(
            self.server, self.protocol, "DeviceManager", "addDevice",
            "psychopy.hardware.keyboard.KeyboardDevice", "defaultKeyboard"
        )
        # get keyboard from device manager
        kb = hardware.DeviceManager.getDevice("defaultKeyboard")
        # make sure we got it
        from psychopy.hardware.keyboard import KeyboardDevice, KeyPress
        assert isinstance(kb, KeyboardDevice)
        # add listener
        runInLiaison(
            self.server, self.protocol, "DeviceManager", "addListener",
            "defaultKeyboard", "liaison", "True"
        )
        time.sleep(1)
        # send dummy message
        kb.receiveMessage(
            KeyPress("a", 1234)
        )
        time.sleep(1)
        # check that message was sent to Liaison
        lastMsg = self.protocol.messages[-1]
        assert lastMsg['type'] == "hardware_response"
        assert lastMsg['class'] == "KeyPress"
        assert lastMsg['data']['t'] == 1234
        assert lastMsg['data']['value'] == "a"

    def test_actualize_session_win(self):
        """
        Test that attribute strings (e.g. "session.win") are actualized by Liaison to be the
        object they represent.
        """
        # add screen buffer photodiode
        runInLiaison(
            self.server, self.protocol, "DeviceManager", "addDevice",
            "psychopy.hardware.photodiode.ScreenBufferSampler", "screenBuffer",
            "session.win"
        )
        # get screen buffer photodidoe
        device = DeviceManager.getDevice("screenBuffer")
        # make sure its window is a window object
        from psychopy.visual import Window
        assert isinstance(device.win, Window)

    def test_device_by_name(self):
        """
        Test that adding a device by name to the device manager prior to running means Components
        using that named device use the one set up in device manager, rather than setting it up
        again according to the Component params.
        """
        # add experiment which creates a button box with different buttons
        runInLiaison(
            self.server, self.protocol, "session", "addExperiment",
            "testNamedButtonBox/testNamedButtonBox.psyexp", "testNamedButtonBox"
        )
        # setup generic devices (use exp1 as a template)
        runInLiaison(
            self.server, self.protocol, "session", "addExperiment",
            "exp1/exp1.psyexp", "exp1"
        )
        runInLiaison(
            self.server, self.protocol, "session", "setupDevicesFromExperiment",
            "exp1"
        )
        # add keyboard button box with abc as its buttons
        runInLiaison(
            self.server, self.protocol, "DeviceManager", "addDevice",
            "psychopy.hardware.button.KeyboardButtonBox", "testNamedButtonBox",
            '["a", "b", "c"]'
        )
        # run experiment
        runInLiaison(
            self.server, self.protocol, "session", "runExperiment",
            "testNamedButtonBox"
        )

    def test_device_JSON(self):
        cases = {
            'testMic': "psychopy.hardware.microphone.MicrophoneDevice",
            'testPhotodiode': "psychopy.hardware.photodiode.ScreenBufferSampler",
            'testButtonBox': "psychopy.hardware.button.KeyboardButtonBox"
        }
        for deviceName, deviceClass in cases.items():
            # get the first available device
            available = DeviceManager.getAvailableDevices(deviceClass)
            if not available:
                continue
            profile = available[0]
            # replace deviceName
            profile['deviceName'] = deviceName
            # setup device
            DeviceManager.addDevice(**profile)
            # call getDevice from Liaison
            runInLiaison(
                self.server, self.protocol, "DeviceManager", "getDevice",
                deviceName
            )
            # get message
            result = self.protocol.messages[-1]['result']
            # whatever is returned should be json serializable, load it to confirm that it is
            json.loads(result)
