#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""Configuration GUI wizard with html report, for first-run"""

# Part of the PsychoPy library
# Copyright (C) 2012 Jonathan Peirce
# Distributed under the terms of the GNU General Public License (GPL).

from pyo import pa_get_devices_infos
from pyglet.gl import gl_info
from psychopy import info, data, visual, gui, core, __version__
import os, sys, time
import wx
import numpy as np
import platform


class ConfigWizard(object):
    def __init__(self, app):
        """Walk user through first-time diagnostics, generate html report."""
        self.app = app
        self.prefs = self.app.prefs
        self.name = 'PsychoPy2 configuration wizard'
        self.version = __version__  # psychopy version
        self.reportPath = os.path.join(self.app.prefs.paths['userPrefsDir'], 'configurationReport.html')
        self.iconfile = os.path.join(self.app.prefs.paths['resources'], 'psychopy.png')
        
        dlg = gui.Dlg(title=self.name)
        #dlg.SetIcon(wx.Icon(self.iconfile, wx.BITMAP_TYPE_PNG)) # no error but no effect
        dlg.addText('')
        dlg.addText("Welcome to the configuration wizard.")
        
        # test for fatal error, and show initial dialog:
        vendor = gl_info.get_vendor().lower()
        cardInfo = gl_info.get_renderer().replace('OpenGL Engine', '').strip()
        badDrivers = False
        badDriversMfg = 'Microsoft'  # to test: replace with nvidia etc
        if vendor.find(badDriversMfg.lower()) > -1:
            dlg.addText('Before we can do a series of configuration checks,')
            dlg.addText("you'll need to update your video card's drivers.", color='red')
            dlg.addText('(The current drivers are inadequate for PsychoPy.)')
            badDrivers = True
        else:
            #dlg.addText('>> Your video card drivers are OK <<', color='dark green')
            dlg.addText("We'll go through a series of checks in about 10 seconds")
            dlg.addText('and display the results in your default web-browser.')
            dlg.addText('')
        dlg.addText('Click OK to proceed, or Cancel to skip.')
        dlg.addText('')
        dlg.show()
        if not dlg.OK and not badDrivers:
            return  # no configuration tests
        
        fatalItemsList = []
        if badDrivers: # leave the app, show page with more info and links
            msg = """<p>Critical issue:\n</p><p>Your video card (%s) has drivers from %s. 
            These drivers cannot support the high-performance features that PsychoPy depends on.
            Fortunately, its typically free and straightforward to get new drivers
            directly from the manufacturer.</p>
            <p><strong>Update the drivers, then restart PsychoPy.</strong> To find the right drivers,
            try <a href="http://www.google.com/search?q=download+drivers+%s">this google search</a> [google.com].</p>
            <p>If you updated the drivers and still get this message, you'll need a different video  
            card to use PsychoPy. Click <a href="http://www.psychopy.org/installation.html#recommended-hardware">here for more information</a> [psychopy.org].</p>
            """ % (cardInfo, badDriversMfg, cardInfo.replace(' ', '+'))
            fatalItemsList.append(msg)
            fatal = True
        # possibly other fatal conditions? append to itemsList
        if fatalItemsList:
            self.htmlReport(fatal=fatalItemsList)
            self.save()
            # user ends up in browser, psychopy shuts down:
            self.app.followLink(url='file://' + self.reportPath)
            # remove lastVersion so wizard will be triggered again on start-up
            del self.prefs.appData['lastVersion']
            self.prefs.saveAppData()
            sys.exit()
        
        itemsList = self.runDiagnostics()
        self.htmlReport(itemsList)
        self.save()
        
        dlg = gui.Dlg(title=self.name)
        dlg.addText('')
        dlg.addText('Configuration report complete!')
        dlg.addText('Click OK to view in a browser,')
        dlg.addText('or Cancel to stay in PsychoPy.')
        dlg.addText('')
        dlg.show()
        if dlg.OK:
            self.app.followLink(url='file://' + self.reportPath)

    def runDiagnostics(self):
        """Return list of (key, val, msg) tuple, all elements of <type str>.
        
        msg can depend on val; msg starts with 'Warning:' to indicate a concern.
        Plain text is returned, expected to be used in html <table>.
        Hyperlinks can be embedded as <a href="">
        """
        
        report = []  # add item tuples in display order
        
        # get a window first:
        win = visual.Window(fullscr=True, allowGUI=False, monitor='testMonitor')
        win.setRecordFrameIntervals(True)
        
        # lots of info, easy visual:
        items = info.RunTimeInfo(win=win, refreshTest='grating', verbose=True, userProcsDetailed=True)
        
        # PSYCHOPY:
        report.append(('PsychoPy', '', ''))
        report.append(('psychopy', __version__, 'avoid upgrading during an experiment'))
        report.append(('locale', items['systemLocale'], 'can be set in Preferences -> App'))
        msg = ''
        if items['pythonVersion'] < '2.6' or items['pythonVersion'] > '2.8':
            msg = 'Warning: python 2.6 or 2.7 required'
        if items['pythonFullVersion'].find('EPD') > -1:
            msg += ' Enthought Python Distribution'
        elif items['pythonExecutable'].find('PsychoPy2.app') > -1:
            msg += ' (StandAlone)'
        bits, linkage = platform.architecture()
        if not bits.startswith('32'):
            msg = 'Warning: 32-bit python expected; ' + msg
        report.append(('python', items['pythonVersion'] + ' &nbsp;(%s)' % bits, msg))
        
        msg = ''
        if items['pythonWxVersion'] < '2.8.10':
            msg = 'Warning: wx 2.8.10 or higher required'
        report.append(('wx', items['pythonWxVersion'], ''))
        report.append(('pyglet', items['pythonPygletVersion'][:32], ''))
        report.append(('rush', str(items['psychopyHaveExtRush']), 'for high-priority threads'))
        
        # VISUAL:
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
        
        msg = 'during <a href="http://www.psychopy.org/api/visual/gratingstim.html">drifting grating</a>'
        if items['windowRefreshTimeMedian_ms'] < 5:
            msg = """Warning: visual sync'ing with the monitor is unlikely"""
        report.append(('refresh rate', "%.2f ms/frame" % items['windowRefreshTimeMedian_ms'], msg))
        msg = ''
        if items['windowRefreshTimeSD_ms'] > .5:
            msg = 'Warning: high variability in the refresh rate'
        report.append(('refresh SD', "%.2f ms" % items['windowRefreshTimeSD_ms'], msg))
        
        # a minimally demanding visual test:
        dots100 = visual.DotStim(win, nDots=100, dotSize=8, fieldShape='circle')
        win.flip()
        win.fps() # reset
        for i in xrange(120):
            dots100.draw()
            win.flip()
        self.dots100fps = round(win.fps())
        win.close()
        msg = 'during <a href="http://www.psychopy.org/api/visual/dotstim.html">DotStim</a> with 100 random dots'
        expectedFps = round(1000./items['windowRefreshTimeMedian_ms'])
        if self.dots100fps < expectedFps:
            msg = 'Warning: expected %i frames per second; <a href="http://www.psychopy.org/api/visual/elementarraystim.html">ElementArrayStim</a> performance may be poor.' % expectedFps
        report.append(('100 dots', str(self.dots100fps)+' frames/sec', msg))
        
        report.append(('openGL max vertices', str(items['openGLmaxVerticesInVertexArray']), ''))
        report.append(('openGL gl stereo', str(items['openGLext.GL_STEREO']), ''))
        
        # AUDIO:
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
                if mic['latency'] > 0.001:
                    msg = 'Warning: "%s" latency > 1ms' % mic['name']
                report.append(('microphone latency', "%.4f s" % mic['latency'], msg))
            else:
                report.append(('microphone', '(not detected)',''))
            sndOutputDevices = items['systemPyo.OutputDevices']
            if len(sndOutputDevices.keys()):
                key = sndOutputDevices.keys()[0]
                spkr = sndOutputDevices[key]
                msg = '"%s"' % spkr['name']
                if spkr['latency'] > 0.001:
                    msg = 'Warning: "%s" latency > 1ms' % spkr['name']
                report.append(('speakers latency', "%.4f s" % spkr['latency'], msg))
            else:
                report.append(('speakers', '(not detected)',''))
        except KeyError:
            pass
        s2t = '<a href="http://www.psychopy.org/api/microphone.html?highlight=Speech2Text">speech-to-text</a>'
        msg = 'audio codec for %s' % s2t
        if not 'systemFlacVersion' in items:
            msg = 'Warning: flac is needed for using %s features.' % s2t
            items['systemFlacVersion'] = '(missing)'
        report.append(('flac', items['systemFlacVersion'].lstrip('flac '), msg))
        # TO-DO: add microphone + playback as sound test
        
        # NUMERIC:
        report.append(('Numeric', '', ''))
        report.append(('numpy', items['pythonNumpyVersion'], '<a href="http://numpy.scipy.org">fast calculations</a>'))
        report.append(('scipy', items['pythonScipyVersion'], ''))
        report.append(('matplotlib', items['pythonMatplotlibVersion'], 'for <a href="http://matplotlib.org">plotting</a>'))
        if 'systemRavailable' in items:
            report.append(('R', items['systemRavailable'].split()[2], 'for <a href="http://www.r-project.org">advanced stats</a>'))
        
        # SYSTEM:
        report.append(('System', '', ''))
        msg = 'used for online help, usage stats, updates, google-speech'
        if items['systemHaveInternetAccess'] is not True:
            items['systemHaveInternetAccess'] = 'False'
            msg = 'Warning: could not connect (without a proxy)'
            # TO-DO: dlg to query whether to try to auto-detect (can take a while), or allow manual entry of proxy str, save into prefs
        val = str(items['systemHaveInternetAccess'])
        report.append(('internet access', val, msg))
        report.append(('proxy setting', str(self.prefs.connections['proxy']), 'current proxy setting from Preferences'))
        report.append(('auto proxy', str(self.prefs.connections['autoProxy']), 'try to auto-detect a proxy; see <a href="http://www.psychopy.org/general/prefs.html#connection-settings">Preferences -> Connections</a>'))
        # CPU speed (will depend on system busy-ness)
        d = np.array(np.linspace(0.,1.,1000000))
        t0 = time.time()
        np.std(d)
        t = time.time() - t0
        report.append(('CPU speed test', "%.3f s" % t, 'numpy.std() of a million data points'))
        # TO-DO: more speed benchmarks
        # - load large image file from disk
        # - transfer image to GPU
        msg = ''
        if 'systemUserProcFlagged' in items:
            items['systemUserProcFlagged'].sort()
            badProc = [p for p,pid in items['systemUserProcFlagged']]
            msg = 'Warning: Some <a href="http://www.psychopy.org/general/timing/reducingFrameDrops.html?highlight=background+processes">background processes</a> can adversely affect timing'
            report.append(('bad background procs', badProc[0]+' ...', msg))
        if 'systemSec.OpenSSLVersion' in items:
            report.append(('OpenSSL', items['systemSec.OpenSSLVersion'].lstrip('OpenSSL '), 'for <a href="http://www.psychopy.org/api/encryption.html">encryption</a>'))
        
        self.warnings = [key for key, val, msg in report if msg.startswith('Warning')]
        return report
        
    def htmlReport(self, items=None, fatal=False):
        """Return an html report given a list of (key, val, msg) items."""
        
        imgfile = os.path.join(self.app.prefs.paths['resources'], 'psychopySplash.png')
        self.header = '<html><head></head><a href="http://www.psychopy.org"><image src="%s" width=396 height=156></a>' % imgfile
        self.iconhtml = '<a href="http://www.psychopy.org"><image src="%s" width=48 height=48></a>' % self.iconfile
        self.name = self.app.GetAppName()
        self.footer = '<hr><font size=-1><center>This page auto-generated by the configuration wizard on %s</center></font></html>' % data.getDateStr(format="%Y-%m-%d, %H:%M")

        htmlDoc = self.header
        if fatal:
            # fatal is a list of strings:
            htmlDoc += '<h2><font color="red">Configuration problem</font></h2><hr>'
            for item in fatal:
                item = item.replace('Critical issue', '<p><strong>Critical issue</strong>')
                htmlDoc += item
        else:
            # items is a list of tuples:
            htmlDoc += '<h2><font color="green">Configuration report</font></h2>\n'
            htmlDoc += '<p>%s (v%s) configuration report run on %s (y-m-d).</p>\n' % (self.name, self.version, data.getDateStr(format="%Y-%m-%d"))
            numWarn = len(self.warnings)
            if numWarn == 0:
                htmlDoc += '<p>No suboptimal values were detected.</p>\n'
            elif numWarn == 1:
                htmlDoc += '<p><font color="red">%i suboptimal value was detected</font>, see details below (%s).</p>\n' % (numWarn, ', '.join(self.warnings))
            elif numWarn > 1:
                htmlDoc += '<p><font color="red">%i suboptimal values were detected</font>, see details below (%s).</p>\n' % (numWarn, ', '.join(self.warnings))
            htmlDoc += '''<p>Resources: <a href="http://www.psychopy.org/documentation.html">On-line documentation</a>\n
                | Download <a href="http://www.psychopy.org/PsychoPyManual.pdf">PDF manual</a>
                | <a href="http://groups.google.com/group/psychopy-users">Search the user-group archives</a>
                </p><hr><p></p>'''
            htmlDoc += '    <table>'
            htmlDoc += '    <tr><td></td><td><font size=+1><strong>Version or value</strong></font></td><td><font size=+1><strong>Notes</strong></font></td>'
            for (key, val, msg) in items:
                if val == msg == '':
                    key = '<font color="darkblue" size="+1"><strong>' + key + '</strong></font>'
                else:
                    key = '&nbsp;&nbsp;&nbsp;&nbsp;' + key
                if msg.startswith('Warning'):
                    val = '<font style=color:red><strong>' + val + '</strong></font>'
                htmlDoc += '        <tr><td>' + key + '</td><td>' + val + '</td><td><em>' + msg + '</em></td></tr>\n'
            htmlDoc += '    </table>'
        htmlDoc += self.footer
        
        self.reportText = htmlDoc
        
    def save(self):
        """Save the html text as a file."""
        f = open(self.reportPath, 'w+b')
        f.write(self.reportText)
        f.close()