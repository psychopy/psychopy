# -*- coding: utf-8 -*-
# Part of the PsychoPy library
# Copyright (C) 2012-2020 iSolver Software Solutions (C) 2021 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import sys
from .. import Device, Computer
from ...constants import DeviceConstants
from ...errors import print2err, printExceptionDetailsToStdErr
import pyglet
currentSec = Computer.getTime

class Display(Device):
    """The ioHub Display Device represents a 2D visual stimulus presentation
    surface that is connected to the computer running ioHub and PsychoPy.

    The Display Device
    can be queries for several run-time properties that are read when the device is created,
    and is also used for transforming the physical Display surface area and pixel resolution
    into alternative coordinate system types that can be used during an experiment.

    """
    _coord_type_mappings = dict(pix='pix', pixel='pix', pixels='pix',
                                deg='deg', degree='deg', degrees='deg', cm='cm',
                                norm='norm', normalize='norm', normalized='norm',
                                height='height'
                                )
    _supported_origin_types = ['center', ]

    _enabled_display_instances = []
    _computer_display_runtime_info_list = None
    EVENT_CLASS_NAMES = []
    DEVICE_TYPE_ID = DeviceConstants.DISPLAY
    DEVICE_TYPE_STRING = 'DISPLAY'

    __slots__ = [
        '_pixels_per_degree',
        '_pix2coord',
        '_coord2pix',
        '_xwindow',
        '_psychopy_monitor']

    def __init__(self, *args, **kwargs):
        Device.__init__(self, *args, **kwargs['dconfig'])
        self._psychopy_monitor = None
        self._coord2pix = None
        self._pix2coord = None

        if sys.platform.startswith('linux'):
            self._xwindow = None

        if Display._computer_display_runtime_info_list is None:
            Display._computer_display_runtime_info_list = Display._createAllRuntimeInfoDicts()

        if self.getIndex() >= self.getDisplayCount():
            # Requested Display index is invalid. Use Display / Screen index 0.
            print2err("WARNING: Requested display index does not exist. Using display index 0.")
            self.device_number = 0

        self._addRuntimeInfoToDisplayConfig()

    def getDeviceNumber(self):
        """Same as Display.getIndex(). All ioHub devices have a device_number,
        so for the Display Device it makes sense to map device_number to the
        Display index.

        See Display.getIndex().

        """
        return self.device_number

    def getIndex(self):
        """
        Returns the display index. In a single display configuration, this will always
        equal 0. In a multiple display configuration, valid index's range from
        0 to N-1, where N equals the number of display's connected and active
        on the Computer being used.

        Args:
            None

        Returns:
            int: Current Display Index; between 0 and getDisplayCount()-1
        """
        return self.device_number

    @classmethod
    def getDisplayCount(cls):
        """Returns the number of monitors connected to the computer that are
        also active. For example, a Computer may have 3 Displays connected to
        it, but the video card may only support having two displays active at a
        time.

        Args:
            None

        Returns:
            int: Total number of displays active on the computer.

        """
        return len(cls._computer_display_runtime_info_list)

    @classmethod
    def getAllDisplayBounds(cls):
        """
        Returns pixel display bounds (l,t r,b) for each detected display.
        
        :return: list of (l,t r,b) tuples
        """
        return [d.get('bounds') for d in cls._computer_display_runtime_info_list]

    def getRuntimeInfo(self, display_index = None):
        """
        Returns a dictionary containing run-time determined settings for the
        Display Device,  based on querying system settings regarding the
        Monitor.

        A Display's run-time properties consist of:

        * index: see getIndex().
        * pixel_width: The horizontal pixel resolution of the Display.
        * pixel_height: The vertical pixel resolution of the Display.
        * pixel_resolution: ( pixel_width, pixel_height )
        * bounds: See getBounds()
        * retrace_rate: The vertical retrace rate of the Display in Hz., as reported by the OS.
        * bits_per_pixel: Number if bits being used to represent all channels of a pixel by the OS.
        * primary: True if the current Monitor is also the primary monitor reported by the OS.

        Args:
            display_index (int): Optional screen index to return info about.

        Returns:
            dict: Run-time attributes of the Display specified by
            display_index. If display_index is None, use full screen window
            display_index.
        """
        if display_index is None or display_index == self.getIndex():
            return self.getConfiguration()['runtime_info']
        return self._getRuntimeInfoByIndex(display_index)

    def getCoordinateType(self):
        """
        Returns the coordinate, or reporting unit, being used by the Display.
        Supported types match the PsychoPy unit_types for Monitors, with the
        exception of the height option:

        * pix   : Equivalent names for this type are *pixel* and *pixels*.
        * cm    : There are no equivalent alternatives to this coordinate type name.
        * norm  : Equivalent names for this type are *normalize* and *normalized*.
        * deg   : Equivalent names for this type are *degree* and *degrees*.

        Please refer to the psychoPy documentation for a detailed description of
        coordinate type.

        Args:
            None

        Returns:
            str: The coordinate, or unit, type being used to define the Display stimulus area.
        """
        return self.getConfiguration()['reporting_unit_type']

    def getColorSpace(self):
        """
        Returns the color space to use for PsychoPy Windows.

        Please refer to the psychoPy documentation for a detailed description of
        supported color spaces.

        Args:
            None

        Returns:
            str: Display color space
        """
        return self.getConfiguration()['color_space']

    def getPixelsPerDegree(self):
        """Returns the Display's horizontal and vertical pixels per degree This
        is currently calculated using the PsychoPy built in function. Therefore
        PPD x and PPD y will be the same value, as only the monitor width and
        participants viewing distance is currently used.

        The physical characteristics of the Display and the Participants viewing distance
        will either be based on the ioHub settings specified, or based on the information
        saved in the PsychoPy Monitor Configuration file that can be optionally
        given to the Display Device before it is instantiated.

        Args:
            None

        Returns:
            tuple: (ppd_x, ppd_y)

        """
        try:
            return self.getConfiguration()['runtime_info']['pixels_per_degree']
        except Exception:
            print2err('ERROR GETTING PPD !')
            printExceptionDetailsToStdErr()

    def getPixelResolution(self):
        """Get the Display's pixel resolution based on the current graphics
        mode.

        Args:
            None

        Returns:
            tuple: (width,height) of the monitor in pixels based.

        """
        return self.getConfiguration()['runtime_info']['pixel_resolution']

    def getRetraceInterval(self):
        """
        Get the Display's *reported* retrace interval (1000.0/retrace_rate)*0.001
        based on the current graphics mode.

        Args:
            None

        Returns:
            float: Current retrace interval of Monitor reported by the OS in sec.msec format.
        """
        return (1000.0 / self.getConfiguration()
                ['runtime_info']['retrace_rate']) * 0.001

    def getBounds(self):
        """Get the Display's pixel bounds; representing the left,top,right,and
        bottom edge of the display screen in native pixel units.

        .. note:: (left, top, right, bottom) bounds will 'not' always be (0, 0, pixel_width, pixel_height). If a multiple display setup is being used, (left, top, right, bottom) indicates the actual absolute pixel bounds assigned to that monitor by the OS. It can be assumed that right = left + display_pixel_width and bottom =  top + display_pixel_height

        Args:
            None

        Returns:
            tuple: (left, top, right, bottom) Native pixel bounds for the Display.

        """
        return self.getConfiguration()['runtime_info']['bounds']

    def getCoordBounds(self):
        """Get the Display's left, top, right, and bottom border bounds,
        specified in the coordinate space returned by Display.getCoordinateType()

        Args:
            None

        Returns:
            tuple: (left, top, right, bottom) coordinate bounds for the Display represented in Display.getCoordinateType() units.

        """
        return self.getConfiguration()['runtime_info']['coordinate_bounds']

    def getDefaultEyeDistance(self):
        """Returns the default  distance from the particpant's eye to the
        Display's physical screen surface, as specified in the ioHub Display
        device's configuration settings or the PsychoPy Monitor Configuration.
        Currently this is the distance from the participant's eye of interest (
        or the average distance of both eyes when binocular data is being
        obtained ) to the center of the Display screen being used for stimulus
        presentation.

        Args:
            None

        Returns:
            int: Default distance in mm from the participant to the display screen surface.

        """
        return self.getConfiguration()['default_eye_distance']\
            ['surface_center']

    def getPhysicalDimensions(self):
        """Returns the Display's physical screen area ( width,  height ) as
        specified in the ioHub Display devices configuration settings or by a
        PsychoPy Monitor Configuration file.

        Args:
            None

        Returns:
            dict: A dict containing the screen 'width' and 'height' as keys, as well as the 'unit_type' the width and height are specified in. Currently only 'mm' is supported for unit_type.

        """
        return self.getConfiguration()['physical_dimensions']

    def getPsychopyMonitorName(self):
        """Returns the name of the PsychoPy Monitor Configuration file being
        used with the Display.

        Args:
            None

        Returns:
            str: Name of the PsychoPy Monitor Configuration being used with the Display.

        """
        return self.getConfiguration().get('psychopy_monitor_name')

    # Private Methods ------>

    def _pixel2DisplayCoord(self, px, py, display_index=None):
        """
        Converts the given pixel position (px, py), to the associated Display
        devices x, y position in the display's coordinate space. If display_index
        is None (the default), then it is assumed the px,py value is for the
        display index specified for the display configured with ioHub. If
        display_index is not None, then that display index is used in the computation.
        If the display_index matches the ioHub enable Display devices index, then
        the method converts from the px,py value to the DIsplay devices
        coordinate / unit space type (Currently also only pix is supported), factoring
        in the origin specified in the Display device configuration. If the
        display_index does not match the ioHub Display device that is being used,
        then px,py == the output x,y value.

        Args:
            display_index (int or None): the display index the px,py value should be relative to. None == use the currently enabled ioHub Display device's index.

        Returns:
            tuple: (x,y), the mapped position based on the 'logic' noted in the description of the method.
        """
        if self._pix2coord:
            return self._pix2coord(self, px, py, display_index)
        return 0, 0

    def _displayCoord2Pixel(self, cx, cy, display_index=None):
        """
        Converts the given display position (dx, dy), to the associated pixel
        px, py position in the within the display's bounds. If display_index
        is None (the default), then it is assumed the dx,dy value is for the
        display index specified for the display configured with ioHub. If
        display_index is not None, then that display index is used in the computation.
        If the display_index matches the ioHub enable Display devices index, then
        the method converts from the dx,dy value (which would be in the Display's
        coordinate / unit space type) to the pixel position within the displays bounds,
        factoring in the origin specified in the Display device configuration. If the
        display_index does not match the ioHub Display device that is being used,
        then dx,dy == the output x,y value.

        Args:
            display_index (int or None): the display index the dx,dy value should be relative to. None == use the currently enabled ioHub Display device's index.

        Returns:
            tuple: (px,py), the mapped pixel position based on the 'logic' noted in the description of the method.
        """
        if self._coord2pix:
            return self._coord2pix(self, cx, cy, display_index)
        return 0, 0

    @classmethod
    def _getComputerDisplayRuntimeInfoList(cls):
        """
        Returns a list of dictionaries containing run-time determined settings for
        each active computer display; based on querying the video card settings.

        The keys of each dict are:

            #. index: see getIndex().
            #. pixel_width: the horizontal pixel resolution of the Display.
            #. pixel_height: the vertical pixel resolution of the Display.
            #. pixel_resolution: pixel_width,pixel_height
            #. bounds: see getBounds()
            #. retrace_rate: The vertical retrace rate of the Display in Hz., as reported by the OS.
            #. bits_per_pixel: Number if bits being used to represent all channels of a pixel by the OS.
            #. primary: True if the current Monitor is also the primary monitor reported by the OS.

        The length of the list will equal getDisplayCount().

        Args:
            None

        Returns:
            list: Each element being a dict of run-time attributes for the associated display index; determined when the Display device was created.
        """
        return cls._computer_display_runtime_info_list

    @classmethod
    def _getConfigurationByIndex(cls, display_index):
        """Returns full configuration dictionary for the Display device created
        with the specified display_index (called device_number in the device
        configuration settings).

        Args:
            display_index (int): display number to return the configuration dictionary for.

        Returns:
            dict: The configuration settings used to create the ioHub Display Device instance.

        """
        if display_index is None or display_index < 0:
            return None

        for d in cls._getEnabledDisplays():
            if d.getConfiguration()['device_number'] == display_index:
                return d

        return None

    @classmethod
    def _getRuntimeInfoByIndex(cls, display_index):
        """
        Returns a dictionary containing run-time determined settings for the
        display that has the associated display_index. Run-time settings are
        based on querying the video card settings of the system.
        The keys of the dict are:

            #. index: see getIndex().
            #. pixel_width: the horizontal pixel resolution of the Display.
            #. pixel_height: the vertical pixel resolution of the Display.
            #. pixel_resolution: pixel_width,pixel_height
            #. bounds: see getBounds()
            #. retrace_rate: The vertical retrace rate of the Display in Hz., as reported by the OS.
            #. bits_per_pixel: Number if bits being used to represent all channels of a pixel by the OS.
            #. primary: True if the current Monitor is also the primary monitor reported by the OS.

        Args:
            display_index (int): The index of the display to get run-time settings for. Valid display indexes are 0 - N-1, where N is the number of active physically connected displays of the computer in use.

        Returns:
            dict: run-time attributes of display that has index display_index.
        """

        if (display_index is None or
                display_index < 0 or
                display_index >= cls.getDisplayCount()):
            return None

        for i in cls._computer_display_runtime_info_list:
            if i['index'] == display_index:
                return i

        return None

    @classmethod
    def _getDisplayIndexForNativePixelPosition(cls, pixel_pos):
        """Returns the index of the display that the native OS pixel position
        would fall within, based on the bounds information that ioHub has for
        each active computer display.

        Args:
            pixel_pos (tuple): the native x,y position to query the display index of.

        Returns:
            int: The index of the display that the pixel_pos falls within based on each display's bounds.

        """
        px, py = pixel_pos
        for d in cls._getComputerDisplayRuntimeInfoList():
            left, top, right, bottom = d['bounds']

            if (px >= left and px < right) and (py >= top and py < bottom):
                return d['index']

        return -1

    @classmethod
    def _getEnabledDisplayCount(cls):
        """Returns the number of Display Device instances that the ioHub Server
        has been informed about. Currently, only one Display instance can be
        created, representing any of the computer's physical active displays.
        This display will be used to create the full screen window used for
        stimulus presentation.

        Args:
            None

        Returns:
            int: ioHub Display Device count. Currently limited to 1.

        """
        return len(cls._enabled_display_instances)

    @classmethod
    def _getEnabledDisplays(cls):
        return cls._enabled_display_instances

    @classmethod
    def _createAllRuntimeInfoDicts(cls):
        runtime_info_list = []
        try:
            default_screen = pyglet.canvas.get_display().get_default_screen()
            dx, dy = default_screen.x, default_screen.y
            dw, dh = default_screen.width, default_screen.height
            dbounds = (dx, dy, dx + dw, dy + dh)
            pyglet_screens = pyglet.canvas.get_display().get_screens()
            display_count = len(pyglet_screens)
            for i in range(display_count):
                d = pyglet_screens[i]
                mode = d.get_mode()
                x, y, w, h = d.x, d.y, d.width, d.height
                runtime_info = dict()
                runtime_info['index'] = i
                runtime_info['pixel_width'] = w
                runtime_info['pixel_height'] = h
                runtime_info['bounds'] = (x, y, x + w, y + h)
                runtime_info['primary'] = runtime_info['bounds'] == dbounds
                if mode:
                    rate = mode.rate
                    if rate == 0.0:
                        rate = 60
                    runtime_info['retrace_rate'] = rate
                    runtime_info['bits_per_pixel'] = mode.depth
                    if mode and mode.width > 0 and mode.height > 0:
                        runtime_info['pixel_resolution'] = mode.width, mode.height
                else:
                    runtime_info['retrace_rate'] = 60
                    runtime_info['bits_per_pixel'] = 32
                    runtime_info['pixel_resolution'] = w, h
                runtime_info_list.append(runtime_info)
            return runtime_info_list
        except Exception:
            printExceptionDetailsToStdErr()

    def _addRuntimeInfoToDisplayConfig(self):

        if self not in Display._enabled_display_instances:
            Display._enabled_display_instances.append(self)

        display_config = self.getConfiguration()

        runtime_info = display_config.get('runtime_info', None)
        if runtime_info is None:
            runtime_info = self._getRuntimeInfoByIndex(self.device_number)
            display_config['runtime_info'] = runtime_info

            self._createPsychopyCalibrationFile()

            pixel_width = runtime_info['pixel_width']
            pixel_height = runtime_info['pixel_height']

            phys_width = display_config['physical_dimensions']['width']
            phys_height = display_config['physical_dimensions']['height']
            phys_unit_type = display_config['physical_dimensions']['unit_type']

            # add pixels_per_degree to runtime info
            try:
                from psychopy import misc
                # math.tan(math.radians(0.5))*2.0*viewing_distance*pixel_width/phys_width
                ppd_x = misc.deg2pix(1.0, self._psychopy_monitor)
                # math.tan(math.radians(0.5))*2.0*viewing_distance*pixel_height/phys_height
                ppd_y = misc.deg2pix(1.0, self._psychopy_monitor)
                runtime_info['pixels_per_degree'] = ppd_x, ppd_y
            except ImportError as e:
                pass

            self. _calculateCoordMappingFunctions(
                pixel_width, pixel_height, phys_unit_type, phys_width, phys_height)

            left, top, right, bottom = runtime_info['bounds']
            coord_left, coord_top = self._pixel2DisplayCoord(
                left, top, self.device_number)
            coord_right, coord_bottom = self._pixel2DisplayCoord(
                right, bottom, self.device_number)
            runtime_info[
                'coordinate_bounds'] = coord_left, coord_top, coord_right, coord_bottom

    def _calculateCoordMappingFunctions(
            self,
            pixel_width,
            pixel_height,
            phys_unit_type,
            phys_width,
            phys_height):
        '''
        For the screen index the  full screen psychopy window is created
        over, this function maps from psychopy coord space (pix, norm, deg,
        all with center = 0,0) to system pix position.

        For any other screen indices, mapping is not done,
        so x_in, y_in == x_out, y_out.
        '''
        coord_type = self.getCoordinateType()
        if coord_type in Display._coord_type_mappings:
            coord_type = Display._coord_type_mappings[coord_type]
        elif coord_type is None:
            print2err(' *** iohub warning: Display / Monitor unit type has not been set.')
            return
        else:
            print2err(' *** iohub error: Unknown Display / Monitor coordinate type: {0}'.format(coord_type))
            return

        self._pix2coord = None

        # For now, use psychopy unit conversions so that drawing positions match
        # device positions exactly
        l, t, r, b = self.getBounds()
        w = r - l
        h = b - t

        def display2psychopyPix(x, y):
            x = x - l
            y = y - t
            return (x - w / 2), -y + h / 2

        def psychopy2displayPix(cx, cy):
            return l + (cx + w / 2), b - (cy + h / 2)

        if coord_type == 'pix':
            def pix2coord(self, x, y, display_index=None):
                if display_index == self.getIndex():
                    return display2psychopyPix(x, y)
                return x, y
            self._pix2coord = pix2coord

            def coord2pix(self, cx, cy, display_index=None):
                if display_index == self.getIndex():
                    return psychopy2displayPix(cx, cy)
                return cx, cy
            self._coord2pix = coord2pix

        elif coord_type == 'norm':
            def pix2ncoord(self, x, y, display_index=None):
                #print2err('Display {0} bounds: {1}'.format(display_index,self.getBounds()))
                if display_index == self.getIndex():
                    ppx, ppy = display2psychopyPix(x, y)
                    return ppx / ((r - l) / 2.0), ppy / ((b - t) / 2.0)
                return x, y
            self._pix2coord = pix2ncoord

            def ncoord2pix(self, nx, ny, display_index=None):
                if display_index == self.getIndex():
                    return psychopy2displayPix(
                        nx * ((r - l) / 2.0), ny * ((b - t) / 2.0))
                return nx, ny
            self._coord2pix = ncoord2pix

        if self._pix2coord is None:
            try:
                from psychopy import misc
                if coord_type == 'cm':
                    def pix2cmcoord(self, x, y, display_index=None):
                        #print2err('Display {0} bounds: {1}'.format(display_index,self.getBounds()))
                        if display_index == self.getIndex():
                            ppx, ppy = display2psychopyPix(x, y)
                            return misc.pix2cm(
                                ppx, self._psychopy_monitor), misc.pix2cm(
                                ppy, self._psychopy_monitor)
                        return x, y
                    self._pix2coord = pix2cmcoord

                    def cmcoord2pix(self, cx, cy, display_index=None):
                        if display_index == self.getIndex():
                            return psychopy2displayPix(
                                misc.cm2pix(
                                    cx, self._psychopy_monitor), misc.cm2pix(
                                    cy, self._psychopy_monitor))
                        return cx, cy
                    self._coord2pix = cmcoord2pix

                elif coord_type == 'height':
                    def pix2heightcoord(self, x, y, display_index=None):
                        if display_index == self.getIndex():
                            ppx, ppy = display2psychopyPix(x, y)
                            return ppx / h, ppy / h
                        return x, y
                    self._pix2coord = pix2heightcoord

                    def height2pix(self, x, y, display_index=None):
                        if display_index == self.getIndex():
                            if False: #TODO: Deal with win.useRetina when we don't have a win.
                                x = x * h / 2.0
                                y = y * h / 2.0
                            else:
                                x = x * h
                                y = y * h
                            return psychopy2displayPix(x, y)

                        return x, y
                    self._coord2pix = height2pix

                elif coord_type == 'deg':
                    def pix2degcoord(self, x, y, display_index=None):
                        if display_index == self.getIndex():
                            ppx, ppy = display2psychopyPix(x, y)
                            return misc.pix2deg(
                                ppx, self._psychopy_monitor), misc.pix2deg(
                                ppy, self._psychopy_monitor)
                        return x, y
                    self._pix2coord = pix2degcoord

                    def degcoord2pix(self, degx, degy, display_index=None):
                        if display_index == self.getIndex():
                            return psychopy2displayPix(
                                misc.deg2pix(
                                    degx, self._psychopy_monitor), misc.cm2pix(
                                    degy, self._psychopy_monitor))
                        return degx, degy
                    self._coord2pix = degcoord2pix
            except:
                print2err('Error during _calculateCoordMappingFunctions')
                printExceptionDetailsToStdErr()


    def _createPsychopyCalibrationFile(self):
        display_config = self.getConfiguration()

        override_using_psycho_settings = display_config.get(
            'override_using_psycho_settings', False)
        psychopy_monitor_name = display_config.get(
            'psychopy_monitor_name', None)
        if psychopy_monitor_name is None or psychopy_monitor_name == 'None':
            return False

        from psychopy import monitors

        existing_monitors = monitors.getAllMonitors()

        psychoMonitor = None

        override = override_using_psycho_settings is True
        if override and psychopy_monitor_name in existing_monitors:
            psychoMonitor = monitors.Monitor(psychopy_monitor_name)

            px, py = self.getPixelResolution()
            mwidth = psychoMonitor.getWidth() * 10.0
            aspect_ratio = px / float(py)
            mheight = mwidth / aspect_ratio
            display_config['physical_dimensions']['width'] = mwidth
            display_config['physical_dimensions']['height'] = mheight
            display_config['physical_dimensions']['unit_type'] = 'mm'

            display_config['default_eye_distance'][
                'surface_center'] = psychoMonitor.getDistance() * 10.0
            display_config['default_eye_distance']['unit_type'] = 'mm'

        else:
            stim_area = display_config.get('physical_dimensions')
            dwidth = stim_area['width']

            # switch from mm to cm if required
            dw_unit_type = stim_area['unit_type']
            if dw_unit_type == 'mm':
                dwidth = dwidth / 10.0

            ddist = self.getDefaultEyeDistance()
            unit_type = self.getConfiguration()['default_eye_distance']\
                ['unit_type']
            # switch from mm to cm if required
            if unit_type == 'mm':
                ddist = ddist / 10.0

            psychoMonitor = monitors.Monitor(
                psychopy_monitor_name, width=dwidth, distance=ddist, gamma=1.0)

            psychoMonitor.setSizePix(list(self.getPixelResolution()))
            psychoMonitor.save()

        self._psychopy_monitor = psychoMonitor
        return True

    def _close(self):
        Device._close(self)
