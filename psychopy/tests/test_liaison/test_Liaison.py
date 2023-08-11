from psychopy import liaison, session
import logging
from psychopy.tests import utils
from pathlib import Path
import time
import json
import asyncio


class DummyWebsocket:
    def __init__(self, server):
        self.server = server

    async def send(self, msg):
        self.server.
        print("FROM WEBSOCKET", msg)


class TestLiaison:
    def setup(self):
        # create liaison server
        self.server = liaison.WebSocketServer()
        # add session to liaison server
        self.server.registerClass(session.Session, "session")
        # make a dummy websocket to receive communications
        self.dummy = DummyWebsocket(self.server)
        self.server._connections = [self.dummy]
        # start Liaison
        self.server.run("localhost", 8100)
        # initialise Session
        self.runInLiaison("session", "init", str(Path(utils.TESTS_DATA_PATH) / "test_session" / "root"))
        # register methods
        self.runInLiaison("session", "registerMethods")
        # start session
        self.runInLiaison("session", "start")

    def runInLiaison(self, object, method, *args):
        cmd = {'object': object, 'method': method, 'args': args}
        asyncio.run(
            self.server._processMessage(self.dummy, json.dumps(cmd))
        )

    def test_session_init(self):
        assert "session" in self.server._methods
        assert isinstance(self.server._methods['session'][0], session.Session)

    def test_window_init(self):
        self.runInLiaison("session", "setupWindowFromParams", "{}", "false")
