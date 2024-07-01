import subprocess
from pathlib import Path

import wx

from psychopy import prefs
from psychopy.app import getAppInstance
from psychopy.app.plugin_manager import PluginManagerPanel, PackageManagerPanel, InstallStdoutPanel
from psychopy.experiment import getAllElements
from psychopy.localization import _translate
import psychopy.logging as logging
import psychopy.tools.pkgtools as pkgtools
import psychopy.app.jobs as jobs
import sys
import os
import subprocess as sp
import psychopy.plugins as plugins

pkgtools.refreshPackages()  # build initial package cache


# flag to indicate if PsychoPy needs to be restarted after installing a package
NEEDS_RESTART = False


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
        # store button handles
        self.closeBtn = self.helpBtn = None
        for btn in self.btns.Children:
            if not btn.Window:
                continue
            if btn.Window.GetId() == wx.ID_CLOSE:
                self.closeBtn = btn.Window
            if btn.Window.GetId() == wx.ID_HELP:
                self.helpBtn = btn.Window

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
        env = os.environ.copy()
        # run command in subprocess
        output = sp.Popen(
            cmd,
            stdout=sp.PIPE,
            stderr=sp.PIPE,
            shell=False,
            env=env,
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
        # alert if busy
        if self.isBusy:
            msg = wx.MessageDialog(
                self,
                ("Cannot remove package. Wait for the installation already in "
                 "progress to complete first."),
                "Uninstallation Failed", wx.OK | wx.ICON_WARNING
            )
            msg.ShowModal()
            return

        # tab to output
        self.output.open()

        if pkgtools._isUserPackage(packageName):
            msg = 'Uninstalling package bundle for `{}` ...'.format(
                packageName)
            self.output.writeStdOut(msg)

            success = pkgtools._uninstallUserPackage(packageName)
            if success:
                msg = 'Successfully removed package `{}`.'.format(
                    packageName)
            else:
                msg = ('Failed to remove package `{}`, check log for '
                       'details.').format(packageName)

            self.output.writeStdOut(msg)

            return

        # interpreter path
        pyExec = sys.executable
        env = os.environ.copy()

        # build the shell command to run the script
        command = [pyExec, '-m', 'pip', 'uninstall', packageName, '--yes']
        # write command to output panel
        self.output.writeCmd(" ".join(command))

        # create a new job with the user script
        self.pipProcess = jobs.Job(
            self,
            command=command,
            # flags=execFlags,
            inputCallback=self.output.writeStdOut,  # both treated the same
            errorCallback=self.output.writeStdErr,
            terminateCallback=self.onUninstallExit
        )
        self.pipProcess.start(env=env)

        global NEEDS_RESTART  # flag as needing a restart
        NEEDS_RESTART = True

    def installPackage(self, packageName, version=None, extra=None):
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
        extra : dict or None
            Dict of extra variables to be accessed by callback functions, use None
            for a blank dict.
        """
        # add version if given
        if version is not None:
            packageName += f"=={version}"
        # use package tools to install
        self.pipProcess = pkgtools.installPackage(
            packageName,
            upgrade=version is None,
            forceReinstall=version is not None,
            awaited=False,
            outputCallback=self.output.writeStdOut,
            terminateCallback=self.onInstallExit,
            extra=extra,
        )

    def installPlugin(self, pluginInfo, version=None):
        """Install a package.

        Calling this will invoke a `pip` command which will install the
        specified package. Packages are installed to bundles and added to the
        system path when done.

        During an installation, the UI will make the console tab visible. It
        will display any messages coming from the subprocess. No way to cancel
        and installation midway at this point.

        Parameters
        ----------
        pluginInfo : psychopy.app.plugin_manager.plugins.PluginInfo
            Info object of the plugin to install.
        version : str or None
            Version of the package to install. If `None`, the latest version
            will be installed.

        """
        # disable close buttons
        self.enableClose(False)
        # do install
        self.installPackage(
            packageName=pluginInfo.pipname,
            version=version,
            extra={
                'pluginInfo': pluginInfo
            }
        )

    def uninstallPlugin(self, pluginInfo):
        """Uninstall a plugin.

        This deletes any bundles in the user's package directory, or uninstalls
        packages from `site-packages`.

        Parameters
        ----------
        pluginInfo : psychopy.app.plugin_manager.plugins.PluginInfo
            Info object of the plugin to uninstall.

        """
        # disable close buttons
        self.enableClose(False)
        # do uninstall
        self.uninstallPackage(pluginInfo.pipname)

    def onInstallExit(self, pid, exitCode):
        """
        Callback function to handle a pip process exiting. Prints a termination statement
        to the output panel then, if installing a plugin, provides helpful info about that
        plugin.
        """
        # re-enable close buttons
        self.enableClose(True)
        if self.pipProcess is None:
            # if pip process is None, this has been called by mistake, do nothing
            return
        # write installation termination statement
        msg = "Installation complete"
        if 'pipname' in self.pipProcess.extra:
            msg = f"Finished installing %(pipname)s" % self.pipProcess.extra
        self.output.writeTerminus(msg)

        # if we have a plugin, write additional plugin information post-install
        if 'pluginInfo' in self.pipProcess.extra:
            # get plugin info object
            pluginInfo = self.pipProcess.extra['pluginInfo']
            # scan plugins
            plugins.scanPlugins()
            # enable plugin
            try:
                pluginInfo.activate()
                # plugins.loadPlugin(pluginInfo.pipname)
            except RuntimeError:
                prefs.general['startUpPlugins'].append(pluginInfo.pipname)
                self.output.writeStdErr(_translate(
                    "[Warning] Could not activate plugin. PsychoPy may need to restart for plugin to take effect."
                ))

            global NEEDS_RESTART  # flag as needing a restart
            NEEDS_RESTART = True
            showNeedsRestartDialog()

            # show list of components/routines now available
            emts = []
            for name, emt in getAllElements().items():
                if hasattr(emt, "plugin") and emt.plugin == pluginInfo.pipname:
                    cats = ", ".join(emt.categories)
                    emts.append(f"{name} ({cats})")
            if len(emts):
                msg = _translate(
                    "The following components/routines should now be visible in the Components panel (a restart may be "
                    "required in some cases):\n"
                )
                for emt in emts:
                    msg += (
                        f"    - {emt}\n"
                    )
                self.output.write(msg)
            # show info link
            if pluginInfo.docs:
                msg = _translate(
                    "For more information about the %s plugin, read the documentation at:"
                ) % pluginInfo.name
                self.output.writeStdOut(msg)
                self.output.writeLink(pluginInfo.docs, link=pluginInfo.docs)

        # clear pip process
        self.pipProcess = None
        # refresh view
        pkgtools.refreshPackages()
        self.pluginMgr.updateInfo()
    
    def onUninstallExit(self, pid, exitCode):
        # re-enable close buttons
        self.enableClose(True)
        # write installation termination statement
        msg = "Uninstall complete"
        if 'pipname' in self.pipProcess.extra:
            msg = f"Finished uninstalling %(pipname)s" % self.pipProcess.extra
        self.output.writeTerminus(msg)
        # clear pip process
        self.pipProcess = None
    
    def enableClose(self, enable):
        """
        Enable/disable close buttons.

        Parameters
        ----------
        enable : bool
            True to enable, False to disable
        """
        # enable dialog X button
        self.EnableCloseButton(enable)
        # enable Cancel button
        self.closeBtn.Enable(enable)

    def onClose(self, evt=None):
        # Get changes to plugin states
        # pluginChanges = self.pluginMgr.pluginList.getChanges()

        # # If any plugins have been uninstalled, prompt user to restart
        # if any(["uninstalled" in changes for changes in pluginChanges.values()]):
        #     msg = _translate(
        #         "It looks like you've uninstalled some plugins. In order for this to take effect, you will need to "
        #         "restart the PsychoPy app."
        #     )
        #     dlg = wx.MessageDialog(
        #         None, msg,
        #         style=wx.ICON_WARNING | wx.OK
        #     )
        #     dlg.ShowModal()

        # # Repopulate component panels
        # for frame in self.app.getAllFrames():
        #     if hasattr(frame, "componentButtons") and hasattr(frame.componentButtons, "populate"):
        #         frame.componentButtons.populate()

        if evt is not None:
            evt.Skip()


def showNeedsRestartDialog():
    """Show a dialog asking the user if they would like to restart PsychoPy.
    """
    msg = _translate("Please restart PsychoPy to apply changes.")

    # show a simple dialog that asks the user to restart PsychoPy
    dlg = wx.MessageDialog(
        None, msg, "Restart Required",
        style=wx.ICON_INFORMATION | wx.OK
    )
    dlg.ShowModal()
