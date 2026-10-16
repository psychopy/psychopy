"""Test that ioHub Server processes don't outlive the psychopy process that
started them, e.g. when an experiment is killed rather than quitting cleanly.
"""
import json
import os
import socket
import subprocess
import sys
import textwrap
import time

import psutil
import pytest

from psychopy.iohub import IOHUB_DIRECTORY
from psychopy.iohub.client import killOrphanedServers
from psychopy.iohub.devices.computer import Computer
from psychopy.iohub.net import UDPClientConnection

SERVER_SCRIPT = os.path.join(IOHUB_DIRECTORY, 'start_iohub_process.py')

# stands in for an experiment, starting an ioHub Server the same way
# ioHubConnection does and then idling until it is killed
PARENT_SCRIPT = textwrap.dedent("""
    import os, subprocess, sys, time
    script, config, pidFile, logFile = sys.argv[1:]
    with open(logFile, 'w') as log:
        proc = subprocess.Popen(
            [sys.executable, script, '0.0', os.path.dirname(config), config,
             str(os.getpid())],
            cwd=os.path.dirname(script), stdout=log, stderr=subprocess.STDOUT)
    with open(pidFile + '.tmp', 'w') as f:
        f.write(str(proc.pid))
    os.replace(pidFile + '.tmp', pidFile)
    time.sleep(600)
""")

# custom task which blocks the ioHub Server's event loop
WEDGE_TASK = textwrap.dedent("""
    import time
    import gevent

    class Wedge(gevent.Greenlet):
        def _run(self):
            time.sleep(600)
""")


def _waitFor(condition, timeout, interval=0.1):
    deadline = time.time() + timeout
    while time.time() < deadline:
        if condition():
            return True
        time.sleep(interval)
    return condition()


def _freeUdpPort():
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        sock.bind(('127.0.0.1', 0))
        return sock.getsockname()[1]


def _portIsFree(port):
    # bind without SO_REUSEADDR, as with it the bind would succeed on Linux
    # even with the port still in use
    with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
        try:
            sock.bind(('', port))
        except OSError:
            return False
    return True


def _writeConfig(folder):
    port = _freeUdpPort()
    configPath = os.path.join(folder, 'iohub_config.yaml')
    with open(configPath, 'w') as f:
        json.dump({'monitor_devices': [], 'udp_port': port}, f)
    return configPath, port


def _sendToServer(port, request, timeout=0.1):
    conn = UDPClientConnection(remote_port=port, timeout=timeout)
    try:
        conn.sendTo(request)
        reply = conn.receive()
    finally:
        conn.close()
    return reply[0] if reply else None


def _waitForServerPid(port, timeout=60):
    """Wait for the ioHub Server on port to be running and return its pid."""
    deadline = time.time() + timeout
    while time.time() < deadline:
        reply = _sendToServer(port, ('GET_IOHUB_STATUS',))
        if reply and reply[1] == 'RUNNING':
            return reply[2]
        time.sleep(0.1)
    raise AssertionError("ioHub Server did not start")


def _kill(*procs):
    for proc in procs:
        try:
            proc.kill()
        except (OSError, psutil.Error):
            pass


def testParseIohubServerCmdline():
    parse = Computer.parseIohubServerCmdline
    script = os.path.join('some', 'dir', 'start_iohub_process.py')
    assert parse(['python', script, '0.0', 'root', 'config', '123']) == 123
    # interpreter options before the script
    assert parse(['python', '-u', '-X', 'dev', script, '0.0', 'r', 'c', '5']) == 5
    # windows paths can differ in case
    assert parse(['python.exe', 'Start_IOHub_Process.py', '0', 'r', 'c', '7']) == 7
    # not an ioHub Server, or malformed
    assert parse(['python', 'experiment.py', '0.0', 'r', 'c', '123']) is None
    assert parse(['python', script, '0.0', 'r']) is None
    assert parse(['python', script, '0.0', 'r', 'c', 'nan']) is None
    assert parse(['python', script, '0.0', 'r', 'c', '0']) is None
    assert parse([]) is None
    assert parse(None) is None


def testIsProcessGone():
    assert not Computer.isProcessGone(os.getpid())
    # a pid created after the given time has been reused
    assert Computer.isProcessGone(os.getpid(), createdBefore=time.time() - 3600)

    proc = subprocess.Popen([sys.executable, '-c', 'pass'])
    if os.name == 'posix':
        # exited but not reaped, so a zombie
        assert _waitFor(lambda: proc.poll() is not None or
                        psutil.Process(proc.pid).status() == psutil.STATUS_ZOMBIE,
                        timeout=30)
        assert Computer.isProcessGone(proc.pid)
    proc.wait()
    assert Computer.isProcessGone(proc.pid)


@pytest.mark.parametrize('reapParent', [True, False])
def testServerExitsWithParent(tmp_path, monkeypatch, reapParent):
    """Killing the psychopy process should shut down its ioHub Server and free
    its port."""
    # make sure the server shuts itself down rather than the backstop
    # stopping it
    monkeypatch.setenv('PSYCHOPY_IOHUB_ORPHAN_GRACE', '120')
    configPath, port = _writeConfig(str(tmp_path))
    pidFile = str(tmp_path / 'server.pid')
    logFile = str(tmp_path / 'server.log')
    parent = subprocess.Popen(
        [sys.executable, '-c', PARENT_SCRIPT,
         SERVER_SCRIPT, configPath, pidFile, logFile])
    serverPid = None
    try:
        assert _waitFor(lambda: os.path.exists(pidFile), timeout=30)
        with open(pidFile) as f:
            serverPid = int(f.read())
        assert _waitForServerPid(port) == serverPid

        parent.kill()
        if reapParent:
            parent.wait()

        assert _waitFor(lambda: Computer.isProcessGone(serverPid), timeout=20), \
            "ioHub Server still running after its psychopy process exited"
        assert _waitFor(lambda: _portIsFree(port), timeout=2)
    finally:
        _kill(parent)
        parent.wait()
        if serverPid is not None and not Computer.isProcessGone(serverPid):
            _kill(psutil.Process(serverPid))


def testServerBackstop(tmp_path, monkeypatch):
    """If the ioHub Server can't shut itself down, it should be force exited
    after the grace period."""
    monkeypatch.setenv('PSYCHOPY_IOHUB_ORPHAN_GRACE', '2')
    configPath, port = _writeConfig(str(tmp_path))
    (tmp_path / 'iohub_test_wedge.py').write_text(WEDGE_TASK)
    monkeypatch.setenv('PYTHONPATH', os.pathsep.join(
        filter(None, [str(tmp_path), os.environ.get('PYTHONPATH')])))
    psychopyProc = subprocess.Popen(
        [sys.executable, '-c', 'import time; time.sleep(600)'])
    with open(tmp_path / 'server.log', 'w') as log:
        server = subprocess.Popen(
            [sys.executable, SERVER_SCRIPT, '0.0', str(tmp_path), configPath,
             str(psychopyProc.pid)],
            cwd=IOHUB_DIRECTORY, stdout=log, stderr=subprocess.STDOUT)
    try:
        assert _waitForServerPid(port) == server.pid
        # block the server's event loop so it can't shut itself down
        reply = _sendToServer(
            port, ('CUSTOM_TASK', 'START', 'wedge',
                   'iohub_test_wedge.Wedge', {}),
            timeout=10)
        assert reply and reply[0] == 'CUSTOM_TASK_REPLY'
        assert _sendToServer(port, ('GET_IOHUB_STATUS',), timeout=1) is None

        psychopyProc.kill()
        psychopyProc.wait()

        assert server.wait(timeout=20) == 3
    finally:
        _kill(psychopyProc, server)
        psychopyProc.wait()
        server.wait()


def testServerExitsIfParentAlreadyGone(tmp_path):
    configPath, _ = _writeConfig(str(tmp_path))
    proc = subprocess.Popen([sys.executable, '-c', 'pass'])
    proc.wait()
    server = subprocess.Popen(
        [sys.executable, SERVER_SCRIPT, '0.0', str(tmp_path), configPath,
         str(proc.pid)],
        cwd=IOHUB_DIRECTORY, stdout=subprocess.DEVNULL,
        stderr=subprocess.STDOUT)
    try:
        assert server.wait(timeout=60) == 1
    finally:
        _kill(server)
        server.wait()


def testKillOrphanedServers():
    """Only servers whose psychopy process has exited should be stopped."""
    deadProc = subprocess.Popen([sys.executable, '-c', 'pass'])
    deadProc.wait()

    def fakeServer(psychopyPid):
        # matches an ioHub Server's command line without running one
        return subprocess.Popen(
            [sys.executable, '-c', 'import time; time.sleep(600)',
             'start_iohub_process.py', '0.0', 'root', 'config',
             str(psychopyPid)])

    orphan = fakeServer(deadProc.pid)
    live = fakeServer(os.getpid())
    try:
        # wait for the processes to have started
        assert _waitFor(lambda: all(
            Computer.parseIohubServerCmdline(psutil.Process(p.pid).cmdline())
            for p in (orphan, live)), timeout=30)

        stopped = killOrphanedServers()

        assert orphan.pid in stopped
        assert live.pid not in stopped
        assert orphan.wait(timeout=10) is not None
        assert live.poll() is None
    finally:
        _kill(orphan, live)
        orphan.wait()
        live.wait()
