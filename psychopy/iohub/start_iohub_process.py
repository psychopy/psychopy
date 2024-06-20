# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).
import json
import os
import sys
import tempfile
import gevent
try:
    if os.name == 'nt':
        # Try to get gevent to use libev, not the default libuv.
        # Libuv only has 1 msec loop resolution (at least on Windows
        # not sure about other OS'es)
        gevent.config.loop = "libev-cext"
except ValueError:
    # libev-cext is not available on the gevent build being used
    pass
except Exception:
    pass

import psutil
import psychopy
import psychopy.clock as clock
from psychopy.iohub import IOHUB_DIRECTORY
from psychopy.iohub.devices import Computer
Computer.is_iohub_process = True
from psychopy.iohub.errors import printExceptionDetailsToStdErr
from psychopy.iohub.server import ioServer
from psychopy.iohub.util import updateDict, yload, yLoader


def run(rootScriptPathDir, configFilePath):
    s = None
    try:
        psychopy.iohub.EXP_SCRIPT_DIRECTORY = rootScriptPathDir

        tdir = tempfile.gettempdir()
        cdir, _ = os.path.split(configFilePath)
        if tdir == cdir:
            tf = open(configFilePath)
            ioHubConfig = json.loads(tf.read())
            tf.close()
            os.remove(configFilePath)
        else:
            ioHubConfig = yload(open(configFilePath, 'r'), Loader=yLoader)

        hub_config_path = os.path.join(IOHUB_DIRECTORY, 'default_config.yaml')

        hub_defaults_config = yload(open(hub_config_path, 'r'), Loader=yLoader)
        updateDict(ioHubConfig, hub_defaults_config)

        s = ioServer(rootScriptPathDir, ioHubConfig)
        udp_port = s.config.get('udp_port', 9000)
        s.log("Receiving diagram's on: {}".format(udp_port))
        s.udpService.start()
        s.setStatus("INITIALIZING")
        msgpump_interval = s.config.get('msgpump_interval', 0.001)
        glets = []

        tlet = gevent.spawn(s.pumpMsgTasklet, msgpump_interval)
        glets.append(tlet)
        for m in s.deviceMonitors:
            m.start()
            glets.append(m)

        tlet = gevent.spawn(s.processEventsTasklet, 0.01)
        glets.append(tlet)

        if Computer.psychopy_process:
            tlet = gevent.spawn(s.checkForPsychopyProcess, 0.5)
            glets.append(tlet)

        s.setStatus("RUNNING")

        if hasattr(gevent, 'run'):
            gevent.run()
            glets = []
        else:
            gevent.joinall(glets)

        # Wait for the server to be ready to shutdown
        gevent.wait()

        lrtime = Computer.global_clock.getLastResetTime()
        s.log('Server END Time Offset: {0}'.format(lrtime), 'DEBUG')
        return True

    except Exception: # pylint: disable=broad-except
        printExceptionDetailsToStdErr()
        if s:
            s.shutdown()
        return False

if __name__ == '__main__':
    psychopy_pid = None
    initial_offset = 0.0
    scriptPathDir = None
    configFileName = None

    prog = sys.argv[0]

    if len(sys.argv) >= 2:
        initial_offset = float(sys.argv[1])
    if len(sys.argv) >= 3:
        scriptPathDir = sys.argv[2]
    if len(sys.argv) >= 4:
        configFileName = sys.argv[3]
    if len(sys.argv) >= 5:
        psychopy_pid = int(sys.argv[4])
    if len(sys.argv) < 2:
        psychopy_pid = None
        configFileName = None
        scriptPathDir = None
        initial_offset = Computer.getTime()

    if psychopy_pid:
        Computer.psychopy_process = psutil.Process(psychopy_pid)
    Computer.global_clock = clock.MonotonicClock(initial_offset)

    run(rootScriptPathDir=scriptPathDir, configFilePath=configFileName)
