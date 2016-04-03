# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).
from __future__ import division, absolute_import

import json
import os
import sys
import tempfile

import gevent
import psutil

try:
    import iohub
    from iohub import IOHUB_DIRECTORY, _ispkg
    from iohub.devices import Computer
    Computer.is_iohub_process = True
    from iohub.errors import printExceptionDetailsToStdErr
    from iohub.server import ioServer
    from iohub import util
    from iohub.util import updateDict, yload, yLoader
except ImportError:
    import psychopy.iohub
    from psychopy.iohub import IOHUB_DIRECTORY, _ispkg
    from psychopy.iohub.devices import Computer
    Computer.is_iohub_process = True
    from psychopy.iohub.errors import printExceptionDetailsToStdErr
    from psychopy.iohub.server import ioServer
    from psychopy.iohub import util
    from psychopy.iohub.util import updateDict, yload, yLoader


def run(rootScriptPathDir, configFilePath):
    s = None
    try:
        if _ispkg:
            iohub.EXP_SCRIPT_DIRECTORY = rootScriptPathDir
        else:
            psychopy.iohub.EXP_SCRIPT_DIRECTORY = rootScriptPathDir

        tdir = tempfile.gettempdir()
        cdir, _ = os.path.split(configFilePath)
        if tdir == cdir:
            tf = open(configFilePath)
            ioHubConfig = json.loads(tf.read())
            tf.close()
            os.remove(configFilePath)
        else:
            ioHubConfig = yload(file(configFilePath, 'r'), Loader=yLoader)

        hub_defaults_config = yload(file(os.path.join(IOHUB_DIRECTORY,
                                                      'default_config.yaml'),
                                         'r'),
                                    Loader=yLoader)
        updateDict(ioHubConfig, hub_defaults_config)

        s = ioServer(rootScriptPathDir, ioHubConfig)
        udp_port = s.config.get('udp_port', 9000)
        s.log("Receiving diagram's on: {}".format(udp_port))
        s.udpService.start()

        msgpump_interval = s.config.get('windows_msgpump_interval', 0.005)
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

        sys.stdout.write('IOHUB_READY\n\r\n\r')
        sys.stdout.flush()

        if hasattr(gevent, 'run'):
            gevent.run()
            glets = []
        else:
            gevent.joinall(glets)

        lrtime = Computer.global_clock.getLastResetTime()
        s.log('Server END Time Offset: {0}'.format(lrtime), 'DEBUG')
    except Exception: # pylint: disable=broad-except
        printExceptionDetailsToStdErr()
        sys.stdout.write('IOHUB_FAILED\n\r\n\r')
        sys.stdout.flush()
        if s:
            s.shutdown()

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
    Computer.global_clock = util.clock.MonotonicClock(initial_offset)

    run(rootScriptPathDir=scriptPathDir, configFilePath=configFileName)
