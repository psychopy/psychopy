import sys
import time
import webbrowser
import requests
from pathlib import Path
from subprocess import Popen, PIPE
from psychopy import logging
from psychopy import __version__ as currentVersion
from psychopy.tools import versionchooser


class Server:
    """
    Object representing a command-line HTTP server.
    """

    instances = {}

    def __new__(cls, cwd, port=12002):
        # if server already open at this port, return it instead
        if port in Server.instances:
            return Server.instances[port]
        # otherwise make a new one
        cls.instances[port] = super(Server, cls).__new__(cls)

        return cls.instances[port]

    def __init__(self, cwd, port=9002):
        # store details
        self.cwd = Path(cwd)
        self.port = port
        # construct command
        self.command = [sys.executable, "-m", "http.server", str(port)]
        # start process
        self.process = Popen(
            self.command,
            bufsize=1,
            cwd=cwd,
            stdout=PIPE,
            stderr=PIPE,
            shell=False,
            universal_newlines=True,
        )
        time.sleep(.1)
        # log server start
        logging.info(f"Local server started on port {port} in directory {cwd}")
    
    def kill(self):
        """
        Close this server by terminating its subprocess.
        """
        # we can only close if there is a process
        if self.port not in Server.instances:
            return
        # kill subprocess
        self.process.terminate()
        time.sleep(.1)
        # log server stopped
        logging.info(f"Local server on port {self.port} stopped")
        # remove reference to process
        del Server.instances[self.port]
    
    def openInBrowser(self, params=None):
        """
        Open this server's landing page in browser

        Parameters
        ----------
        params : dict
            Parameters to append to the URL
        """
        # construct url
        url = f"http://localhost:{self.port}"
        # append params
        if params:
            url += "?"
            for key, value in params.items():
                url += f"{key}={value}"
        # open
        webbrowser.open(url)
    
    def __del__(self):
        self.kill()


def getPsychoJS(cwd, useVersion=''):
    """
    Download and save the current version of the PsychoJS library.

    Useful for debugging, amending scripts.
    """
    ver = versionchooser.getPsychoJSVersionStr(currentVersion, useVersion)
    # pathify lib path
    libPath = Path(cwd) / "lib"
    # make sure lib path exists
    if not libPath.is_dir():
        libPath.mkdir(parents=True)
    # iterate through allowed extensions
    for ext in ['css', 'iife.js', 'iife.js.map', 'js', 'js.LEGAL.txt', 'js.map']:
        # work out final path to write to
        file = libPath / ("psychojs-{}.{}".format(ver, ext))
        # skip if it already exists
        if file.exists():
            continue
        # otherwise, get from url
        req = requests.get(f"https://lib.pavlovia.org/psychojs-{ver}.{ext}")
        # write to file
        file.write_bytes(req.content)

    print("##### PsychoJS libs downloaded to {} #####\n".format(libPath))