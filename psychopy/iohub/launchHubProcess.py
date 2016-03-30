# -*- coding: utf-8 -*-
# Part of the psychopy.iohub library.
# Copyright (C) 2012-2016 iSolver Software Solutions
# Distributed under the terms of the GNU General Public License (GPL).

import gevent
import json
import os
import sys
try:
    import iohub
    from iohub import load, Loader, IOHUB_DIRECTORY, EXP_SCRIPT_DIRECTORY
    from iohub.devices import Computer
    Computer.is_iohub_process = True
    from iohub.errors import print2err, printExceptionDetailsToStdErr
    from iohub.server import ioServer
    from iohub import util
    from iohub.util import updateDict
except ImportError:
    import psychopy.iohub
    from psychopy.iohub import load, Loader, IOHUB_DIRECTORY, EXP_SCRIPT_DIRECTORY
    from psychopy.iohub.devices import Computer
    Computer.is_iohub_process = True
    from psychopy.iohub.errors import print2err, printExceptionDetailsToStdErr
    from psychopy.iohub.server import ioServer
    from psychopy.iohub import util
    from psychopy.iohub.util import updateDict


def run(rootScriptPathDir, configFilePath):
    global EXP_SCRIPT_DIRECTORY
    EXP_SCRIPT_DIRECTORY = rootScriptPathDir

    import tempfile
    tdir = tempfile.gettempdir()
    cdir, cfile = os.path.split(configFilePath)
    if tdir == cdir:
        tf = open(configFilePath)
        ioHubConfig = json.loads(tf.read())
        tf.close()
        os.remove(configFilePath)
    else:
        ioHubConfig = load(file(configFilePath, 'r'), Loader=Loader)

    hub_defaults_config = load(
        file(
            os.path.join(
                IOHUB_DIRECTORY,
                'default_config.yaml'),
            'r'),
        Loader=Loader)
    updateDict(ioHubConfig, hub_defaults_config)
    try:
        s = ioServer(rootScriptPathDir, ioHubConfig)
    except Exception as e:
        printExceptionDetailsToStdErr()
        sys.stdout.flush()

        try:
            s.shutdown()
        except Exception:
            pass

        return -1

    try:
        s.log('Receiving datagrams on :9000')
        s.udpService.start()

        if Computer.system == 'win32':
            gevent.spawn(
                s.pumpMsgTasklet,
                s.config.get(
                    'windows_msgpump_interval',
                    0.00375))

        if hasattr(gevent, 'run'):
            for m in s.deviceMonitors:
                m.start()

            gevent.spawn(s.processEventsTasklet, 0.01)

            sys.stdout.write('IOHUB_READY\n\r\n\r')

            #print2err("Computer.psychopy_process: ", Computer.psychopy_process)
            if Computer.psychopy_process:
                gevent.spawn(s.checkForPsychopyProcess, 0.5)

            sys.stdout.flush()

            gevent.run()
        else:
            glets = []
            if Computer.system == 'win32':
                glets.append(
                    gevent.spawn(
                        s.pumpMsgTasklet,
                        s.config.get(
                            'windows_msgpump_interval',
                            0.00375)))

            for m in s.deviceMonitors:
                m.start()
                glets.append(m)
            glets.append(gevent.spawn(s.processEventsTasklet, 0.01))

            sys.stdout.write('IOHUB_READY\n\r\n\r')
            sys.stdout.flush()

            #print2err("Computer.psychopy_process: ", Computer.psychopy_process)
            if Computer.psychopy_process:
                glets.append(gevent.spawn(s.checkForPsychopyProcess, 0.5))

            gevent.joinall(glets)

        s.log('Server END Time Offset: {0}'.format(
            Computer.global_clock.getLastResetTime()), 'DEBUG')

    except Exception as e:
        print2err('Error occurred during ioServer.start(): ', str(e))
        printExceptionDetailsToStdErr()
        print2err('------------------------------')

        sys.stdout.write('IOHUB_FAILED\n\r\n\r')
        sys.stdout.flush()

        try:
            s.shutdown()
        except Exception:
            pass

    return -1

if __name__ == '__main__':
    prog = sys.argv[0]
    if len(sys.argv) >= 2:
        initial_offset = float(sys.argv[1])
    if len(sys.argv) >= 3:
        rootScriptPathDir = sys.argv[2]
    if len(sys.argv) >= 4:
        configFileName = sys.argv[3]
    if len(sys.argv) >= 5:
        psychopy_pid = int(sys.argv[4])
    if len(sys.argv) < 2:
        psychopy_pid = None
        configFileName = None
        rootScriptPathDir = None
        initial_offset = Computer.getTime()

    try:
        if psychopy_pid:
            import psutil
            Computer.psychopy_process = psutil.Process(psychopy_pid)
    except Exception:
        pass

    Computer.global_clock = util.clock.MonotonicClock(initial_offset)

    run(rootScriptPathDir=rootScriptPathDir, configFilePath=configFileName)
