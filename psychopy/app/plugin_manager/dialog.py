import wx

from psychopy.app import getAppInstance
from psychopy.app.plugin_manager import PluginManagerPanel, PackageManagerPanel, InstallStdoutPanel
from psychopy.localization import _translate
import psychopy.tools.pkgtools as pkgtools
import psychopy.app.jobs as jobs
import sys
import os
import subprocess as sp
import psychopy.plugins as plugins

pkgtools.refreshPackages()  # build initial package cache


class EnvironmentManagerDlg(wx.Dialog):
    def __init__(self, parent):
        wx.Dialog.__init__(
            self, parent=parent,
            title=_translate("Plugins & Packages"),
            size=(1080, 720),
            style=wx.RESIZE_BORDER | wx.DEFAULT_DIALOG_STYLE | wx.CENTER | wx.TAB_TRAVERSAL | wx.NO_BORDER
        )
        self.SetMinSize((980, 520))
        self.app = getAppInstance()
        # Setup sizer
        self.border = wx.BoxSizer(wx.VERTICAL)
        self.SetSizer(self.border)
        self.sizer = wx.BoxSizer(wx.HORIZONTAL)
        self.border.Add(self.sizer, proportion=1, border=6, flag=wx.EXPAND | wx.ALL)
        # Create notebook
        self.notebook = wx.Notebook(self)
        self.sizer.Add(self.notebook, border=6, proportion=1, flag=wx.EXPAND | wx.ALL)
        # Output panel
        self.output = InstallStdoutPanel(self.notebook)
        self.notebook.AddPage(self.output, text=_translate("Output"))
        # Plugin manager
        self.pluginMgr = PluginManagerPanel(self.notebook, dlg=self)
        self.notebook.InsertPage(0, self.pluginMgr, text=_translate("Plugins"))
        # Package manager
        self.packageMgr = PackageManagerPanel(self.notebook, dlg=self)
        self.notebook.InsertPage(1, self.packageMgr, text=_translate("Packages"))
        # Buttons
        self.btns = self.CreateStdDialogButtonSizer(flags=wx.HELP | wx.CLOSE)
        self.border.Add(self.btns, border=12, flag=wx.EXPAND | wx.ALL)

        self.pipProcess = None  # handle to the current Job

        self.notebook.ChangeSelection(0)


    @staticmethod
    def getPackageVersionInfo(packageName):
        """Query packages for available versions.

        This function invokes the `pip index versions` ins a subprocess and
        parses the results.

        Parameters
        ----------
        packageName : str
            Name of the package to get available versions of.

        Returns
        -------
        dict
            Mapping of versions information. Keys are `'All'` (`list`),
            `'Current'` (`str`), and `'Latest'` (`str`).

        """
        cmd = [sys.executable, "-m", "pip", "index", "versions", packageName,
               '--no-input', '--no-color']
        # run command in subprocess
        output = sp.Popen(
            cmd,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            shell=False,
            universal_newlines=True)
        stdout, stderr = output.communicate()  # blocks until process exits
        nullVersion = {'All': [], 'Installed': '', 'Latest': ''}

        # if stderr:  # error pipe has something, give nothing
        #     return nullVersion

        # parse versions
        if stdout:
            allVersions = installedVersion = latestVersion = None
            for line in stdout.splitlines(keepends=False):
                line = line.strip()  # remove whitespace
                if line.startswith("Available versions:"):
                    allVersions = (line.split(': ')[1]).split(', ')
                elif line.startswith("LATEST:"):
                    latestVersion = line.split(': ')[1].strip()
                elif line.startswith("INSTALLED:"):
                    installedVersion = line.split(': ')[1].strip()

            if installedVersion is None:  # not present, use first entry
                installedVersion = allVersions[0]
            if latestVersion is None:  # ditto
                latestVersion = allVersions[0]

            toReturn = {
                'All': allVersions,
                'Installed': installedVersion,
                'Latest': latestVersion}

            return toReturn

        return nullVersion

    def _writeOutput(self, text, flush=True):
        """Write out bytes coming from the current subprocess.

        Parameters
        ----------
        text : str or bytes
            Text to write.
        flush : bool
            Flush text so it shows up immediately on the pipe.

        """
        if isinstance(text, bytes):
            text = text.decode('utf-8')

        self.output.write(text)

    def _onInputCallback(self, streamBytes):
        """Callback to process data from the input stream of the subprocess.
        This is called when `~psychopy.app.jobs.Jobs.poll` is called and only if
        there is data in the associated pipe.

        Parameters
        ----------
        streamBytes : bytes or str
            Data from the 'stdin' streams connected to the subprocess.

        """
        self._writeOutput(streamBytes)

    def _onErrorCallback(self, streamBytes):
        """Callback to process data from the error stream of the subprocess.
        This is called when `~psychopy.app.jobs.Jobs.poll` is called and only if
        there is data in the associated pipe.

        Parameters
        ----------
        streamBytes : bytes or str
            Data from the 'sdterr' streams connected to the subprocess.

        """
        self._onInputCallback(streamBytes)

    def _onTerminateCallback(self, pid, exitCode):
        """Callback invoked when the subprocess exits.

        Parameters
        ----------
        pid : int
            Process ID number for the terminated subprocess.
        exitCode : int
            Program exit code.

        """
        # write a close message, shows the exit code
        closeMsg = " Package installation complete "
        closeMsg = closeMsg.center(80, '#') + '\n'
        self._writeOutput(closeMsg)

        self.pipProcess = None  # clear Job object

        pkgtools.refreshPackages()
        plugins.scanPlugins()
        self.packageMgr.packageList.refresh()

    @property
    def isBusy(self):
        """`True` if there is currently a `pip` subprocess running.
        """
        return self.pipProcess is not None

    def uninstallPackage(self, packageName):
        """Uninstall a package.

        This deletes any bundles in the user's package directory, or uninstalls
        packages from `site-packages`.

        Parameters
        ----------
        packageName : str
            Name of the package to install. Should be the project name but other
            formats may work.

        """
        if self.isBusy:
            msg = wx.MessageDialog(
                self,
                ("Cannot remove package. Wait for the installation already in "
                 "progress to complete first."),
                "Uninstallation Failed", wx.OK | wx.ICON_WARNING
            )
            msg.ShowModal()
            return

        self.notebook.SetSelection(2)  # go to console page

        if pkgtools._isUserPackage(packageName):
            msg = 'Uninstalling package bundle for `{}` ...\n'.format(
                packageName)
            self._writeOutput(msg)

            success = pkgtools._uninstallUserPackage(packageName)
            if success:
                msg = 'Successfully removed package `{}`.\n'.format(
                    packageName)
            else:
                msg = ('Failed to remove package `{}`, check log for '
                       'details.\n').format(packageName)

            self._writeOutput(msg)

            return

        # interpreter path
        pyExec = sys.executable

        # build the shell command to run the script
        command = [pyExec, '-m', 'pip', 'uninstall', packageName, '--yes']

        # create a new job with the user script
        self.pipProcess = jobs.Job(
            self,
            command=command,
            # flags=execFlags,
            inputCallback=self._onInputCallback,  # both treated the same
            errorCallback=self._onErrorCallback,
            terminateCallback=self._onTerminateCallback
        )
        self.pipProcess.start()

    def installPackage(self, packageName, version=None):
        """Install a package.

        Calling this will invoke a `pip` command which will install the
        specified package. Packages are installed to bundles and added to the
        system path when done.

        During an installation, the UI will make the console tab visible. It
        will display any messages coming from the subprocess. No way to cancel
        and installation midway at this point.

        Parameters
        ----------
        packageName : str
            Name of the package to install. Should be the project name but other
            formats may work.
        version : str or None
            Version of the package to install. If `None`, the latest version
            will be installed.

        """
        if self.isBusy:
            msg = wx.MessageDialog(
                self,
                ("Cannot install package. Wait for the installation already in "
                 "progress to complete first."),
                "Installation Failed", wx.OK | wx.ICON_WARNING
            )
            msg.ShowModal()
            return

        self.notebook.SetSelection(2)  # go to console page

        # interpreter path
        pyExec = sys.executable

        # determine installation path for bundle, create it if needed
        bundlePath = plugins.getBundleInstallTarget(packageName)
        if not os.path.exists(bundlePath):
            self._writeOutput(
                "Creating bundle path `{}` for package `{}`.\n".format(
                    bundlePath, packageName))
            os.mkdir(bundlePath)  # make the directory
        else:
            self._writeOutput(
                "Using existing bundle path `{}` for package `{}`.\n".format(
                    bundlePath, packageName))

        # add the bundle to path, refresh makes it discoverable after install
        if bundlePath not in sys.path:
            sys.path.insert(0, bundlePath)

        # build the shell command to run the script
        command = [pyExec, '-m', 'pip', 'install', packageName, '--target',
                   bundlePath]

        # create a new job with the user script
        self.pipProcess = jobs.Job(
            self,
            command=command,
            # flags=execFlags,
            inputCallback=self._onInputCallback,  # both treated the same
            errorCallback=self._onErrorCallback,
            terminateCallback=self._onTerminateCallback
        )
        self.pipProcess.start()

    def onClose(self, evt=None):
        # Get changes to plugin states
        pluginChanges = self.pluginMgr.pluginList.getChanges()

        # If any plugins have been uninstalled, prompt user to restart
        if any(["uninstalled" in changes for changes in pluginChanges.values()]):
            msg = _translate(
                "It looks like you've uninstalled some plugins. In order for this to take effect, you will need to "
                "restart the PsychoPy app.\n"
            )
            dlg = wx.MessageDialog(
                None, msg,
                style=wx.ICON_WARNING | wx.OK
            )
            dlg.ShowModal()

        # Repopulate component panels
        for frame in self.app.getAllFrames():
            if hasattr(frame, "componentButtons") and hasattr(frame.componentButtons, "populate"):
                frame.componentButtons.populate()

