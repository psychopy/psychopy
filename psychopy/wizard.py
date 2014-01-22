#!/usr/bin/env python2
# -*- coding: utf-8 -*-

"""Libraries for wizards, currently firstrun configuration and benchmark."""

# Part of the PsychoPy library
# Copyright (C) 2014 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

# Author: Jeremy Gray, Oct 2012

from pyglet.gl import gl_info
from psychopy import info, data, visual, gui, core, __version__, web, prefs, event
import os, sys, time
import wx
import numpy as np
import platform
import tempfile, pickle


class ConfigWizard(object):
    """Walk through configuration diagnostics & generate report."""
    def __init__(self, firstrun=False):
        """Check drivers, show GUIs, run diagnostics, show report."""
        self.firstrun = firstrun
        self.prefs = prefs
        self.appName = 'PsychoPy2'
        self.name = self.appName + ' Configuration Wizard'
        self.reportPath = os.path.join(self.prefs.paths['userPrefsDir'], 'firstrunReport.html')
        #self.iconfile = os.path.join(self.prefs.paths['resources'], 'psychopy.png')
        #dlg.SetIcon(wx.Icon(self.iconfile, wx.BITMAP_TYPE_PNG)) # no error but no effect

        dlg = gui.Dlg(title=self.name)
        dlg.addText('')
        if firstrun:
            dlg.addText("Welcome! It looks like you are running PsychoPy for the first time.")
            dlg.addText("This wizard will help you get started quickly and smoothly.")
        else:
            dlg.addText("Welcome to the configuration wizard.")

        # test for fatal configuration errors:
        fatalItemsList = []
        if not driversOkay():
            cardInfo = gl_info.get_renderer().replace('OpenGL Engine', '').strip()
            dlg.addText('')
            dlg.addText("The first configuration check is your video card's drivers. The current", color='red')
            dlg.addText("drivers cannot support PsychoPy, so you'll need to update the drivers.", color='red')
            msg = """<p>Critical issue:\n</p><p>Your video card (%s) has drivers
                that cannot support the high-performance features that PsychoPy depends on.
                Fortunately, its typically free and straightforward to get new drivers
                directly from the manufacturer.</p>
                <p><strong>To update the drivers:</strong>
                <li> You'll need administrator privileges.
                <li> On Windows, don't use the windows option to check for updates
                  - it can report that there are no updates available.
                <li> If your card is made by NVIDIA, go to
                  <a href="http://www.nvidia.com/Drivers">the NVIDIA website</a>
                  and use the 'auto detect' option. Try here for
                  <a href="http://support.amd.com/">ATI / Radeon drivers</a>. Or try
                  <a href="http://www.google.com/search?q=download+drivers+%s">
                  this google search</a> [google.com].
                <li> Download and install the driver.
                <li> Reboot the computer.
                <li> Restart PsychoPy.</p>
                <p>If you updated the drivers and still get this message, you'll
                  need a different video card to use PsychoPy. Click
                <a href="http://www.psychopy.org/installation.html#recommended-hardware">here
                for more information</a> [psychopy.org].</p>
            """ % (cardInfo, cardInfo.replace(' ', '+'))
            fatalItemsList.append(msg)
        if not cardOkay():
            cardInfo = gl_info.get_renderer().replace('OpenGL Engine', '').strip()
            msg = """<p>Critical issue:\n</p>"""
            msg += cardInfo
            fatalItemsList.append(msg)
            pass
        # other fatal conditions? append a 'Critical issue' msg to itemsList
        if not fatalItemsList:
            dlg.addText("We'll go through a series of configuration checks in about 10 seconds. ")
            dlg.addText('')
            if firstrun:  # explain things more
                dlg.addText('Note: The display will switch to full-screen mode and will ')
                dlg.addText("then switch back. You don't need to do anything.")
            dlg.addText('Optional: For best results, please quit all email programs, web-browsers, ')
            dlg.addText('Dropbox, backup or sync services, and the like.')
            dlg.addText('')
            dlg.addText('Click OK to start, or Cancel to skip.')
            if not self.firstrun:
                dlg.addField(label='Full details', initial=self.prefs.app['debugMode'])
        else:
            dlg.addText('')
            dlg.addText('Click OK for more information, or Cancel to skip.')

        # show the first dialog:
        dlg.addText('')
        dlg.show()
        if fatalItemsList:
            self.htmlReport(fatal=fatalItemsList)
            self.save()
            # user ends up in browser:
            url='file://' + self.reportPath
            wx.LaunchDefaultBrowser(url)
            return
        if not dlg.OK:
            return  # no configuration tests run

        # run the diagnostics:
        verbose = not self.firstrun and dlg.data[0]
        win = visual.Window(fullscr=True, allowGUI=False, monitor='testMonitor')
        itemsList = self.runDiagnostics(win, verbose)  # sets self.warnings
        win.close()
        self.htmlReport(itemsList)
        self.save()

        # display summary & options:
        dlg = gui.Dlg(title=self.name)
        dlg.addText('')
        dlg.addText('Configuration testing complete!')
        summary = self.summary(items=itemsList)
        numWarn = len(self.warnings)
        if numWarn == 0:
            msg = 'All values seem reasonable (no warnings).'
        elif numWarn == 1:
            msg = '1 suboptimal value was detected (%s)' % self.warnings[0]
        else:
            msg = '%i suboptimal values were detected (%s, ...)' % (len(self.warnings), self.warnings[0])
        dlg.addText(msg)
        for item in summary:
            dlg.addText(item[0], item[1])  # (key, color)
        dlg.addText('')
        dlg.addText('Click OK for full details (will open in a web-browser),')
        dlg.addText('or Cancel to stay in PsychoPy.')
        dlg.addText('')
        dlg.show()
        if dlg.OK:
            url = 'file://' + self.reportPath
            wx.LaunchDefaultBrowser(url)

    def runDiagnostics(self, win, verbose=False):
        """Return list of (key, val, msg) tuple, set self.warnings

        All tuple elements will be of <type str>.

        msg can depend on val; msg starts with 'Warning:' to indicate a concern.
        Plain text is returned, expected to be used in html <table>.
        Hyperlinks can be embedded as <a href="...">
        """

        report = []  # add item tuples in display order

        # get lots of info and do quick-to-render visual (want no frames drop):
        #     for me, grating draw times are: mean 0.53 ms, SD 0.77 ms
        items = info.RunTimeInfo(win=win, refreshTest='grating', verbose=True, userProcsDetailed=True)

        totalRAM, freeRAM = items['systemMemTotalRAM'], items['systemMemFreeRAM']
        if freeRAM == 'unknown':
            if totalRAM != 'unknown':
                totalRAM = "%.1fG" % (totalRAM / 1024.)
            msg = 'could not assess available physical RAM; total %s' % totalRAM
            report.append(('available memory', 'unknown', msg))
        else:
            msg = 'physical RAM available for configuration test (of %.1fG total)' % (totalRAM / 1024.)
            if freeRAM < 300:  # in M
                msg = 'Warning: low available physical RAM for configuration test (of %.1fG total)' % (totalRAM / 1024.)
            report.append(('available memory', str(freeRAM)+'M', msg))

        # ----- PSYCHOPY: -----
        report.append(('PsychoPy', '', ''))
        report.append(('psychopy', __version__, 'avoid upgrading during an experiment'))
        report.append(('locale', items['systemLocale'], 'can be set in <a href="http://www.psychopy.org/general/prefs.html#application-settings">Preferences -> App</a>'))
        msg = ''
        if items['pythonVersion'] < '2.5' or items['pythonVersion'] >= '3':
            msg = 'Warning: python 2.5, 2.6, or 2.7 required; 2.5 is iffy'
        if 'EPD' in items['pythonFullVersion']:
            msg += ' Enthought Python Distribution'
        elif 'PsychoPy2.app' in items['pythonExecutable']:
            msg += ' (PsychoPy StandAlone)'
        bits, linkage = platform.architecture()
        if not bits.startswith('32'):
            msg = 'Warning: 32-bit python required; ' + msg
        report.append(('python version', items['pythonVersion'] + ' &nbsp;(%s)' % bits, msg))
        if verbose:
            msg = ''
            if items['pythonWxVersion'] < '2.8.10':
                msg = 'Warning: wx 2.8.10 or higher required'
            report.append(('wx', items['pythonWxVersion'], ''))
            report.append(('pyglet', items['pythonPygletVersion'][:32], ''))
            report.append(('rush', str(items['psychopyHaveExtRush']), 'for high-priority threads'))

        # ----- VISUAL: -----
        report.append(('Visual', '', ''))
        # openGL settings:
        msg = ''
        if items['openGLVersion'] < '2.':
            msg = 'Warning: <a href="http://www.psychopy.org/general/timing/reducingFrameDrops.html?highlight=OpenGL+2.0">OpenGL 2.0 or higher is ideal</a>.'
        report.append(('openGL version', items['openGLVersion'], msg))
        report.append(('openGL vendor', items['openGLVendor'], ''))
        report.append(('screen size', ' x '.join(map(str, items['windowSize_pix'])), ''))
        #report.append(('wait blanking', str(items['windowWaitBlanking']), ''))

        msg = ''
        if not items['windowHaveShaders']:
            msg = 'Warning: <a href="http://www.psychopy.org/general/timing/reducingFrameDrops.html?highlight=shader">Rendering of complex stimuli will be slow</a>.'
        report.append(('have shaders', str(items['windowHaveShaders']), msg))

        msg = 'during the drifting <a href="http://www.psychopy.org/api/visual/gratingstim.html">GratingStim</a>'
        if items['windowRefreshTimeMedian_ms'] < 3.3333333:
            msg = """Warning: too fast? visual sync'ing with the monitor seems unlikely at 300+ Hz"""
        report.append(('visual sync (refresh)', "%.2f ms/frame" % items['windowRefreshTimeMedian_ms'], msg))
        msg = 'SD < 0.5 ms is ideal (want low variability)'
        if items['windowRefreshTimeSD_ms'] > .5:
            msg = 'Warning: the refresh rate has high frame-to-frame variability (SD > 0.5 ms)'
        report.append(('refresh stability (SD)', "%.2f ms" % items['windowRefreshTimeSD_ms'], msg))

        # draw 100 dots as a minimally demanding visual test:
        # first get baseline frame-rate (safe as possible, no drawing):
        avg, sd, median = visual.getMsPerFrame(win)
        dots100 = visual.DotStim(win, nDots=100, speed=0.005, dotLife=12, dir=90,
            coherence=0.2, dotSize=8, fieldShape='circle')
        win.setRecordFrameIntervals(True)
        win.frameIntervals = []
        win.flip()
        for i in xrange(180):
            dots100.draw()
            win.flip()
        msg = 'during <a href="http://www.psychopy.org/api/visual/dotstim.html">DotStim</a> with 100 random dots'
        intervalsMS = np.array(win.frameIntervals) * 1000
        nTotal = len(intervalsMS)
        nDropped = sum(intervalsMS > (1.5 * median))
        if nDropped:
            msg = 'Warning: could not keep up during <a href="http://www.psychopy.org/api/visual/dotstim.html">DotStim</a> with 100 random dots.'
        report.append(('no dropped frames', '%i / %i' % (nDropped, nTotal), msg))
        win.setRecordFrameIntervals(False)
        try:
            from pyglet.media import avbin
            ver = avbin.get_version()
            if ver < 5 or ver >= 6:
                msg = 'Warning: version 5 recommended (for movies); Visit <a href="http://code.google.com/p/avbin">download page</a> [google.com]'
            else:
                msg = 'for movies'
            report.append(('pyglet avbin', str(ver), msg))
        except: # not sure what error to catch, WindowsError not found
            report.append(('pyglet avbin', 'import error', 'Warning: could not import avbin; playing movies will not work'))

        if verbose:
            report.append(('openGL max vertices', str(items['openGLmaxVerticesInVertexArray']), ''))
            keyList = ['GL_ARB_multitexture', 'GL_EXT_framebuffer_object', 'GL_ARB_fragment_program',
                'GL_ARB_shader_objects', 'GL_ARB_vertex_shader', 'GL_ARB_texture_non_power_of_two',
                'GL_ARB_texture_float', 'GL_STEREO']
            for key in keyList:
                val = items['openGLext.'+key]  # boolean
                if not val:
                    val = '<strong>' + str(val) + '</strong>'
                report.append((key, str(val), ''))

        # ----- AUDIO: -----
        report.append(('Audio', '', ''))
        msg = ''
        if not 'systemPyoVersion' in items:
            msg = 'Warning: pyo is needed for sound and microphone.'
            items['systemPyoVersion'] = '(missing)'
        elif items['systemPyoVersion'] < '0.6.2':
            msg = 'pyo 0.6.2 compiled with --no-messages will suppress start-up messages'
        report.append(('pyo', items['systemPyoVersion'], msg))
        # sound latencies from portaudio; requires pyo svn r1024
        try:
            sndInputDevices = items['systemPyo.InputDevices']
            if len(sndInputDevices.keys()):
                key = sndInputDevices.keys()[0]
                mic = sndInputDevices[key]
                if mic['name'].endswith('icroph'):
                    mic['name'] += 'one'  # portaudio (?) seems to clip to 16 chars
                msg = '"%s"' % mic['name']
                if mic['latency'] > 0.003:
                    msg = 'Warning: "%s" latency > 3ms' % mic['name']
                report.append(('microphone latency', "%.4f s" % mic['latency'], msg))
            else:
                report.append(('microphone', '(not detected)',''))
            sndOutputDevices = items['systemPyo.OutputDevices']
            if len(sndOutputDevices.keys()):
                key = sndOutputDevices.keys()[0]
                spkr = sndOutputDevices[key]
                msg = '"%s"' % spkr['name']
                if spkr['latency'] > 0.003:
                    msg = 'Warning: "%s" latency > 3ms' % spkr['name']
                report.append(('speakers latency', "%.4f s" % spkr['latency'], msg))
            else:
                report.append(('speakers', '(not detected)',''))
        except KeyError:
            pass
        s2t = '<a href="http://www.psychopy.org/api/microphone.html?highlight=Speech2Text">speech-to-text</a>'
        msg = 'audio codec for %s' % s2t
        if not 'systemFlacVersion' in items:
            msg = 'Warning: flac is needed for using %s features. <a href="http://flac.sourceforge.net/download.html">Download</a> [sourceforge.net].' % s2t
            items['systemFlacVersion'] = '(missing)'
        if verbose:
            report.append(('flac', items['systemFlacVersion'].lstrip('flac '), msg))
        # TO-DO: add microphone + playback as sound test

        # ----- NUMERIC: -----
        report.append(('Numeric', '', ''))
        report.append(('numpy', items['pythonNumpyVersion'], 'vector-based (fast) calculations'))
        report.append(('scipy', items['pythonScipyVersion'], 'scientific / numerical'))
        report.append(('matplotlib', items['pythonMatplotlibVersion'], 'plotting; fast contains(), overlaps()'))

        # ----- SYSTEM: -----
        report.append(('System', '', ''))
        report.append(('platform', items['systemPlatform'], ''))
        msg = 'for online help, usage statistics, software updates, and google-speech'
        if items['systemHaveInternetAccess'] is not True:
            items['systemHaveInternetAccess'] = 'False'
            msg = 'Warning: could not connect (no proxy attempted)'
            # TO-DO: dlg to query whether to try to auto-detect (can take a while), or allow manual entry of proxy str, save into prefs
        val = str(items['systemHaveInternetAccess'])
        report.append(('internet access', val, msg))
        report.append(('auto proxy', str(self.prefs.connections['autoProxy']), 'try to auto-detect a proxy if needed; see <a href="http://www.psychopy.org/general/prefs.html#connection-settings">Preferences -> Connections</a>'))
        if not self.prefs.connections['proxy'].strip():
            prx = '&nbsp;&nbsp--'
        else:
            prx = str(self.prefs.connections['proxy'])
        report.append(('proxy setting', prx, 'current manual proxy setting from <a href="http://www.psychopy.org/general/prefs.html#connection-settings">Preferences -> Connections</a>'))

        msg = ''
        items['systemUserProcFlagged'].sort()
        self.badBgProc = [p for p,pid in items['systemUserProcFlagged']]
        val = ("%s ..." % self.badBgProc[0]) if len(self.badBgProc) else 'No bad background processes found.'
        msg = 'Warning: Some <a href="http://www.psychopy.org/general/timing/reducingFrameDrops.html?highlight=background+processes">background processes</a> can adversely affect timing'
        report.append(('background processes', val, msg))
        if verbose and 'systemSec.OpenSSLVersion' in items:
            report.append(('OpenSSL', items['systemSec.OpenSSLVersion'].lstrip('OpenSSL '), 'for <a href="http://www.psychopy.org/api/encryption.html">encryption</a>'))
        report.append(('CPU speed test', "%.3f s" % items['systemTimeNumpySD1000000_sec'], 'numpy.std() of a million data points'))
            # TO-DO: more speed benchmarks
            # - load large image file from disk
            # - transfer image to GPU

        # ----- IMPORTS (relevant for developers & non-StandAlone): -----
        if verbose:  # always False for a real first-run
            report.append(('Packages', '', ''))
            packages = ['PIL', 'openpyxl', 'lxml', 'setuptools', 'pytest', 'sphinx',
                        'psignifit', 'pyserial', 'pp',
                        'pynetstation', 'ioLabs', 'labjack'
                        ]
            if sys.platform == 'win32':
                packages.append('pywin32')
                packages.append('winioport')
            for pkg in packages:
                try:
                    if pkg == 'PIL':
                        exec('import PIL.Image')
                        ver = PIL.Image.VERSION
                    #elif pkg == 'lxml':
                    #
                    elif pkg == 'pp':
                        exec('import pp; ver = pp.version')
                    elif pkg == 'pynetstation':
                        exec('from psychopy.hardware import egi')
                        ver = 'import ok'
                    elif pkg == 'pyserial':
                        exec('import serial')
                        ver = serial.VERSION
                    else:
                        exec('import ' + pkg)
                        try: ver = eval(pkg+'.__version__')
                        except: ver = 'import ok'
                    report.append((pkg, ver, ''))
                except (ImportError, AttributeError):
                    report.append((pkg, '&nbsp;&nbsp--', 'could not import %s' % pkg))

        self.warnings = list(set([key for key, val, msg in report if msg.startswith('Warning')]))
        return report

    def summary(self, items=None):
        """Return a list of (item, color) for gui display. For non-fatal items."""
        config = {}
        for item in items:
            config[item[0]] = [item[1], item[2]]
        green = '#009933'
        red = '#CC3300'
        check = u"\u2713   "
        summary = [(check + "video card drivers", green)]
        ofInterest = ['python version', 'available memory', 'openGL version',
            'visual sync (refresh)', 'refresh stability (SD)', 'no dropped frames',
            'pyglet avbin', 'microphone latency', 'speakers latency',
            'internet access']
        ofInterest.append('background processes')
        for item in ofInterest:
            if not item in config:
                continue  # eg, microphone latency
            if config[item][1].startswith('Warning:'):
                summary.append(("X   " + item, red))
            else:
                summary.append((check + item, green))
        return summary

    def htmlReport(self, items=None, fatal=False):
        """Return an html report given a list of (key, val, msg) items.

        format triggers: 'Critical issue' in fatal gets highlighted
                         'Warning:' in msg -> highlight key and val
                         val == msg == '' -> use key as section heading
        """

        imgfile = os.path.join(self.prefs.paths['resources'], 'psychopySplash.png')
        self.header = '<html><head></head><a href="http://www.psychopy.org"><image src="%s" width=396 height=156></a>' % imgfile
        #self.iconhtml = '<a href="http://www.psychopy.org"><image src="%s" width=48 height=48></a>' % self.iconfile
        self.footer = '<font size=-1><center>This page auto-generated by the PsychoPy configuration wizard on %s</center></font>' % data.getDateStr(format="%Y-%m-%d, %H:%M")

        htmlDoc = self.header
        if fatal:
            # fatal is a list of strings:
            htmlDoc += '<h2><font color="red">Configuration problem</font></h2><hr>'
            for item in fatal:
                item = item.replace('Critical issue', '<p><strong>Critical issue</strong>')
                htmlDoc += item + "<hr>"
        else:
            # items is a list of tuples:
            htmlDoc += '<h2><font color="green">Configuration report</font></h2>\n'
            numWarn = len(self.warnings)
            if numWarn == 0:
                htmlDoc += '<p>All values seem reasonable (no warnings, but there might still be room for improvement).</p>\n'
            elif numWarn == 1:
                htmlDoc += '<p><font color="red">1 suboptimal value was detected</font>, see details below (%s).</p>\n' % (self.warnings[0])
            elif numWarn > 1:
                htmlDoc += '<p><font color="red">%i suboptimal values were detected</font>, see details below (%s).</p>\n' % (numWarn, ', '.join(self.warnings))
            htmlDoc += '''<script type="text/javascript">
                // Loops through all rows in document and changes display property of rows with a specific ID
                // toggle('ok', '') will display all rows
                // toggle('ok', 'none') hides ok rows, leaving Warning rows shown
                function toggle(ID, display_value) {
                    tr=document.getElementsByTagName('tr');
                    for (i=0;i<tr.length;i++) {
                        if (tr[i].id == ID) tr[i].style.display = display_value;
                    }
                }
                </script>
                <p>
                <button onClick="toggle('ok', 'none');">Only show suboptimal values</button>
                <button onClick="toggle('ok', '');">Show all information</button></p>
                '''
            htmlDoc += '''<p>Resources:
                  Contributed <a href="http://upload.psychopy.org/benchmark/report.html">benchmarks</a>
                | <a href="http://www.psychopy.org/documentation.html">On-line documentation</a>
                | Download <a href="http://www.psychopy.org/PsychoPyManual.pdf">PDF manual</a>
                | <a href="http://groups.google.com/group/psychopy-users">Search the user-group archives</a>
                </p>'''
            htmlDoc += '<hr><p></p>    <table cellspacing=8 border=0>\n'
            htmlDoc += '    <tr><td><font size=+1><strong>Configuration test</strong> or setting</font></td><td><font size=+1><strong>Version or value</strong></font></td><td><font size=+1><em>Notes</em></font></td>'
            for (key, val, msg) in items:
                if val == msg == '':
                    key = '<font color="darkblue" size="+1"><strong>' + key + '</strong></font>'
                else:
                    key = '&nbsp;&nbsp;&nbsp;&nbsp;' + key
                if msg.startswith('Warning'):
                    key = '<font style=color:red><strong>' + key + '</strong></font>'
                    val = '<font style=color:red><strong>' + val + '</strong></font>'
                    id = 'Warning'
                else:
                    id = 'ok'
                htmlDoc += '        <tr id="%s"><td>' % id
                htmlDoc += key + '</td><td>' + val + '</td><td><em>' + msg + '</em></td></tr>\n'
            htmlDoc += '    </table><hr>'
        htmlDoc += self.footer
        if not fatal and numWarn:
            htmlDoc += """<script type="text/javascript">toggle('ok', 'none'); </script>"""
        htmlDoc += '</html>'

        self.reportText = htmlDoc

    def save(self):
        """Save the html text as a file."""
        f = open(self.reportPath, 'w+b')
        f.write(self.reportText)
        f.close()

class BenchmarkWizard(ConfigWizard):
    """Class to get system info, run benchmarks, optional upload to psychopy.org"""
    def __init__(self, fullscr=True):
        self.firstrun = False
        self.prefs = prefs
        self.appName = 'PsychoPy2'
        self.name = self.appName + ' Benchmark Wizard'

        dlg = gui.Dlg(title=self.name)
        dlg.addText('')
        dlg.addText('Benchmarking takes ~20-30 seconds to gather')
        dlg.addText('configuration and performance data. Begin?')
        dlg.addText('')
        dlg.show()
        if not dlg.OK:
            return

        self._prepare()
        win = visual.Window(fullscr=fullscr, allowGUI=False, monitor='testMonitor')

        # do system info etc first to get fps, add to list later because
        # its nicer for benchmark results to appears at top of the report:
        diagnostics = self.runDiagnostics(win, verbose=True)
        info = {}
        for k, v, m in diagnostics:  # list of tuples --> dict, ignore msg m
            info[k] = v
        fps = 1000./float(info['visual sync (refresh)'].split()[0])

        itemsList = [('Benchmark', '', '')]
        itemsList.append(('benchmark version', '0.1', 'dots & configuration'))
        itemsList.append(('full-screen', str(fullscr), 'visual window for drawing'))

        if int(info['no dropped frames'].split('/')[0]) != 0:  # eg, "0 / 180"
            start = 50  # if 100 dots had problems earlier, here start lower
        else:
            start = 200
        for shape in ['circle', 'square']:  # order matters: circle crashes first
            dotsList = self.runLotsOfDots(win, fieldShape=shape, starting=start, baseline=fps)
            itemsList.extend(dotsList)
            start = int(dotsList[-1][1])  # start square where circle breaks down
        itemsList.extend(diagnostics)
        win.close()

        itemsDict = {}
        for itm in itemsList:
            if itm[0].find('proxy setting') > -1 or not itm[1]:
                continue
            itemsDict[itm[0]] = itm[1].replace('<strong>', '').replace('</strong>', '').replace('&nbsp;', '').replace('&nbsp', '')
            print itm[0]+': ' + itemsDict[itm[0]]

        # present dialog, upload only if opt-in:
        dlg = gui.Dlg(title=self.name)
        dlg.addText('')
        dlg.addText('Benchmark complete! (See the Coder output window.)')
        dlg.addText('Are you willing to share your data at psychopy.org?')
        dlg.addText('Only configuration and performance data are shared;')
        dlg.addText('No personally identifying information is sent.')
        dlg.addText('(Sharing requires an internet connection.)')
        dlg.show()
        if dlg.OK:
            status = self.uploadReport(itemsDict)
            dlg = gui.Dlg(title=self.name + ' result')
            dlg.addText('')
            if status and status.startswith('success good_upload'):
                dlg.addText('Configutation data were successfully uploaded to')
                dlg.addText('http://upload.psychopy.org/benchmark/report.html')
                dlg.addText('Thanks for participating!')
            else:
                if not eval(info['internet access']):
                    dlg.addText('Upload error: maybe no internet access?')
                else:
                    dlg.addText('Upload error status: %s' % status[:20])
            dlg.show()

        self.htmlReport(itemsList)
        self.reportPath = os.path.join(self.prefs.paths['userPrefsDir'], 'benchmarkReport.html')
        self.save()
        dlg = gui.Dlg(title=self.name)
        dlg.addText('')
        dlg.addText('Click OK to view full configuration and benchmark data.')
        dlg.addText('Click Cancel to stay in PsychoPy.')
        dlg.addText('')
        dlg.show()
        if dlg.OK:
            url = 'file://' + self.reportPath
            wx.LaunchDefaultBrowser(url)

    def _prepare(self):
        """Prep for bench-marking; currently just RAM-related on mac"""
        if sys.platform == 'darwin':
            try:
                core.shellCall('purge')  # free up physical memory if possible
            except OSError:
                pass
        elif sys.platform == 'win32':
            # This will run in background, perhaps best to launch it to run overnight the day before benchmarking:
            # %windir%\system32\rundll32.exe advapi32.dll,ProcessIdleTasks
            # rundll32.exe advapi32.dll,ProcessIdleTasks
            pass
        elif sys.platform.startswith('linux'):
            # as root: sync; echo 3 > /proc/sys/vm/drop_caches
            pass
        else:
            pass

    def runLotsOfDots(self, win, fieldShape, starting=100, baseline=None):
        """DotStim stress test: draw increasingly many dots until drop lots of frames

        report best dots as the highest dot count at which drop no frames at all
        fieldShape = circle or square
        starting = initial dot count; increases until failure
        baseline = known frames per second; None means measure it here
        """

        win.setRecordFrameIntervals(True)
        secs = 1  # how long to draw them for, at least 1s

        # baseline frames per second:
        if not baseline:
            for i in xrange(5):
                win.flip() # wake things up
            win.fps() # reset
            for i in xrange(60):
                win.flip()
            baseline = round(win.fps())
        maxFrame = round(baseline * secs)

        dotsInfo = []
        win.flip()
        bestDots = starting  # this might over-estimate the actual best
        dotCount = starting
        count = visual.TextStim(win, text=str(dotCount))
        count.draw()
        win.flip()
        dots = visual.DotStim(win, color=(1.0, 1.0, 1.0),
                        fieldShape=fieldShape, nDots=dotCount)
        win.fps() # reset
        frameCount = 0
        while True:
            dots.draw()
            win.flip()
            frameCount += 1
            if frameCount > maxFrame:
                fps = win.fps()  # get frames per sec
                if len(event.getKeys(['escape'])):
                    sys.exit()
                if fps < baseline * 0.6:
                    # only break when start dropping a LOT of frames (80% or more)
                    dotsInfo.append(('dots_' + fieldShape, str(bestDots), ''))
                    break
                frames_dropped = round(baseline-fps)  # can be negative
                if frames_dropped < 1:  # can be negative
                    # only set best if no dropped frames:
                    bestDots = dotCount
                # but do allow to continue in case do better with more dots:
                dotCount += 100
                if dotCount > 1200:
                    dotCount += 100
                if dotCount > 2400:
                    dotCount += 100
                # show the dot count:
                count.setText(str(dotCount))
                count.draw()
                win.flip()
                dots = visual.DotStim(win, color=(1.0, 1.0, 1.0),
                        fieldShape=fieldShape, nDots=dotCount)
                frameCount = 0
                win.fps()  # reset
        win.setRecordFrameIntervals(False)
        win.flip()
        return tuple(dotsInfo)

    def uploadReport(self, itemsList):
        """Pickle & upload data to psychopy.org

        Windows compatibility added by Sol Simpson (need a closed file)
        """

        tmp = tempfile.NamedTemporaryFile(delete=False)
        pickle.dump(itemsList, tmp)
        tmp.close()

        # Upload the data:
        selector = 'http://upload.psychopy.org/benchmark/'
        basicAuth = 'psychopy:open-sourc-ami'
        status = None
        try:
            status = web.upload(selector, tmp.name, basicAuth)
        except:
            status = "Exception occurred during web.upload"
        finally:
            os.unlink(tmp.name)
        return status

def driversOkay():
    """Returns True if drivers should be okay for PsychoPy"""
    return gl_info.get_vendor().lower().find('microsoft') == -1

def cardOkay():
    """Returns string: okay, maybe, bad"""

    return True  # until we have a list of known-good cards

    card = gl_info.get_renderer()
    knownGoodList = []  # perhaps load from a file
    if card in knownGoodList:
        return True
    knownBadList = []
    if card in knownBadList:
        return False

if __name__ == '__main__':
    if '--config' in sys.argv:
        ConfigWizard(firstrun=bool('--firstrun' in sys.argv))
    elif '--benchmark' in sys.argv:
        BenchmarkWizard()
    else:
        print "need to specify a wizard in sys.argv, e.g., --benchmark"
