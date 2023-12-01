from psychopy import liaison, session, hardware
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
