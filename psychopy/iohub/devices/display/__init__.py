# coding=utf-8
"""
ioHub
.. file: ioHub/devices/display/__init__.py

Copyright (C) 2012-2013 iSolver Software Solutions

Distributed under the terms of the GNU General Public License 
(GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com> + contributors
.. fileauthor:: Sol Simpson <sol@isolver-software.com>
"""

import wx
import sys

from psychopy import misc

from .. import Device,Computer
from ...constants import DeviceConstants
from ...util import ioHubDialog, print2err,printExceptionDetailsToStdErr, createErrorResult, win32MessagePump

currentSec=Computer.currentSec
            
class Display(Device):
    _coord_type_mappings=dict( pix='pix', pixel='pix', pixels='pix',
                               deg='deg', degree='deg', degrees='deg',
                               cm='cm',# mm='mm', inch='inch', inches='inch',
                               norm='norm', normalize='norm', normalized='norm',
                               #perc='perc',percent='perc', percentage='perc'
                               )
    _supported_origin_types=['center',]#,'top_left','bottom_left']
                           
    _enabled_display_instances=[]
    _computer_display_runtime_info_list=None    
    EVENT_CLASS_NAMES=[]
    DEVICE_TYPE_ID=DeviceConstants.DISPLAY
    DEVICE_TYPE_STRING='DISPLAY'
    
    __slots__=['_pixels_per_degree','_pix2coord','_coord2pix','_xwindow','_psychopy_monitor']
    def __init__(self,*args,**kwargs):
        Device.__init__(self,*args,**kwargs['dconfig'])
        self._psychopy_monitor=None
        self._coord2pix=None
        self._pix2coord=None
        
        if sys.platform == 'linux2':
            self._xwindow=None
            
        if Display._computer_display_runtime_info_list is None:
            Display._computer_display_runtime_info_list=\
                                        Display._createAllRuntimeInfoDicts()

        self._addRuntimeInfoToDisplayConfig()
        
#        self._createPsychopyCalibrationFile()

    @classmethod
    def getDisplayIndexForNativePixelPosition(cls,pixel_pos):
        """
        Returns the index of the display that the native OS pixel position would
        fall within, based on the bounds information that ioHub has for each 
        active computer display.
        
        Args: 
            pixel_pos (tuple): the native x,y position to query the display index of.
            
        Returns:
            int: The index of the display that the pixel_pos falls within based on each display's bounds.
        """
        px,py=pixel_pos
        for d in cls.getComputerDisplayRuntimeInfoList():
            left,top,right,bottom=d['bounds']
            
            if (px>=left and px<right) and (py>=top and py<bottom):
                return d['index']
                
        return -1

    @classmethod
    def getComputerDisplayCount(cls):
        """
        Returns the number of Displays connected to the Computer that are also active.
        For example, a Computer may have 3 Displays connected to it, but the video card
        may only support having two displays active at a time.
        
        Args: 
            None
            
        Returns:
            int: active computer display count.
        """
        return len(cls._computer_display_runtime_info_list)

    @classmethod
    def getEnabledDisplayCount(cls):
        """
        Returns the number of Display Device instances that the ioHub Server has 
        been informed about. Currently, only one Display instance can be created,
        representing any of the computer's physical active displays. This display
        will be used to create the full screen window used for stimulus presentation.
        
        Args: 
            None
            
        Returns:
            int: ioHub Display Device count. Currently limited to 1.
        """        
        return len(cls._enabled_display_instances)

    @classmethod
    def getConfigurationByIndex(cls,display_index):
        """
        Returns full configuration dictionary for the Display device created with 
        the specified display_index (called device_number in the device configuration settings).
        
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
    def getComputerDisplayRuntimeInfoList(cls):
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
          
        The length of the list will equal getComputerDisplayCount().
        
        Args: 
            None
            
        Returns:
            list: Each element being a dict of run-time attributes for the associated display index; determined when the Display device was created.
        """
        return cls._computer_display_runtime_info_list

    @classmethod
    def getRuntimeInfoByIndex(cls,display_index):
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
            display_index >= cls.getComputerDisplayCount()):
            return None
                            
        for i in cls._computer_display_runtime_info_list:
            if i['index'] == display_index:
                return i
        
        return None
                    
    def getRuntimeInfo(self):
        """
        Returns a dictionary containing run-time determined settings for the 
        current display based on querying the video card settings. The keys of the dict are:

            #. index: see getIndex().
            #. pixel_width: the horizontal pixel resolution of the Display.
            #. pixel_height: the vertical pixel resolution of the Display.            
            #. pixel_resolution: pixel_width,pixel_height
            #. bounds: see getBounds()
            #. retrace_rate: The vertical retrace rate of the Display in Hz., as reported by the OS.
            #. bits_per_pixel: Number if bits being used to represent all channels of a pixel by the OS. 
            #. primary: True if the current Monitor is also the primary monitor reported by the OS.
                  
        Args: 
            None
            
        Returns:
            dict: run-time attributes of the Display, determined when the Display device was created.
        """
        return self.getConfiguration()['runtime_info']

    def getDeviceNumber(self):
        """
        Returns the display index. In a single display configuration, this will always
        equal 0. In a multiple display configuration, valid index's range from
        0 - N-1, where N equals the number of display's connected and active
        on the Computer being used.
        
        Args: 
            None
            
        Returns:
            int: display index, 0 to N-1, where N equals the number connected and active display's. 
        """
        return self.device_number
        
    def getIndex(self):
        """
        Returns the display index. In a single display configuration, this will always
        equal 0. In a multiple display configuration, valid index's range from
        0 - N-1, where N equals the number of display's connected and active
        on the Computer being used.
        
        Args: 
            None
            
        Returns:
            int: display index, 0 to N-1, where N equals the number connected and active display's. 
        """
        return self.device_number

    def getCoordinateType(self):
        """
        Returns the coordinate, or reporting unit, type specified for the Display.
        
        Args: 
            None
            
        Returns:
            str: Currently only 'pix' is supported.
        """       
        return self.getConfiguration()['reporting_unit_type']        
                               
    def getPixelsPerDegree(self):
        """
        Returns the Display's horizontal and vertical pixels per degree calculation
        based on the physical Display settings provided by the monitor in the device's
        configuration file settings and the resolution of the Display reported by the
        OS.
        
        Args: 
            None
            
        Returns:
            tuple: (ppd_x, ppd_y) given the monitors current resolution and the physical settings provided in the device's configuration file.
        """
        try:
            return self.getConfiguration()['runtime_info']['pixels_per_degree']
        except Exception:
            print2err("ERROR GETTING PPD !")
            printExceptionDetailsToStdErr()
            return createErrorResult("DEVICE_ATTRIBUTE_ERROR",
                    error_message="An error occurred while calling a display \
                                    instances getPixelsPerDegree() method.",
                    method="Display.getPixelsPerDegree")

        
    def getPixelResolution(self):
        """
        Get the monitor's pixel resolution based on the current graphics mode.

        Args: 
            None
            
        Returns:
            tuple: (width,height) of the monitor based on it's current graphics mode.
        """
        return self.getConfiguration()['runtime_info']['pixel_resolution']

    def getOrigin(self):
        """
        Get the Displays origin in for the coordinate space. Valid options are:
            #. center: The 0.0, 0.0 point of the coord space is at the display center.
            #. top_left: The 0.0, 0.0 point of the coord space the top, left corner of the display.
            #. bottom_right: The 0.0, 0.0 point of the coord space the bottom, left corner of the display.

        Args: 
            None

        Returns:
            str: The origin value selected for the display.
        """
        return self.getConfiguration()['origin']

    def getRetraceInterval(self):
        """
        Get the display's reported retrace 'interval' (1000.0/retrace_rate)*0.001
        based on the current graphics mode.

        Args: 
            None
            
        Returns:
            float: retrace interval of Monitor reported by OS in sec.msec format
        """
        return (1000.0/self.getConfiguration()['runtime_info']['retrace_rate'])*0.001

    def getBounds(self):
        """
        Get the display's pixel bounds representing the left,top,right,and bottom 
        edge of the the monitor in native pixel units. 
        
        **Note:** (left, top, right, bottom) bounds will 'not' always be 
        (0, 0, pixel_width, pixel_height). If a multiple display setup is 
        being used, (left, top, right, bottom) indicates the actual absolute 
        pixel bounds assigned to that monitor by the OS. It can be assumed that
        right = left + display_pixel_width and bottom =  top + display_pixel_height

        Args: 
            None
            
        Returns:
            tuple: (left, top, right, bottom) pixel bounds for the Display.
        """
        return self.getConfiguration()['runtime_info']['bounds']

    def getCoordBounds(self):
        """
        Get the display's left,top,right,and bottom bounds in the Display
        devices coordinate space. 

        Args: 
            None
            
        Returns:
            tuple: (left, top, right, bottom) coordinate bounds for the Display.
        """
        return self.getConfiguration()['runtime_info']['coordinate_bounds']

    def pixel2DisplayCoord(self,px,py,display_index=None):
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
            return self._pix2coord(self,px,py,display_index)
        return 0,0

    def displayCoord2Pixel(self,cx,cy,display_index=None):
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
            return self._coord2pix(self,cx,cy,display_index)
        return 0,0

    def getDefaultEyeDistance(self):
        """
        Returns the default  distance from the particpant's eye to the Display's
        physical screen surface, as specified in the ioHub Display device's
        configuration settings. Currently this is the distance from the  participant's
        eye of interest, or the average of both eyes when binocular data is being obtained,
        to the center of the Display screen being used for stimulus presentation.
        
        Args: 
            None
            
        Returns:
            int: Default display in mm from the participant to the display screen surface. 
        """
        return self.getConfiguration()['default_eye_distance']\
                                        ['surface_center']
    
    def getPhysicalDimensions(self):
        """
        Returns the Display's physical screen area ( width and height ) as 
        specified in the ioHub Display devices configuration settings.
        
        Args: 
            None
            
        Returns:
            dict: A dict containing the screen 'width' and 'height' as keys, as well as the 'unit_type' the width and height are specified in. Currently on 'mm' is supported for unit_type.
        """
        return self.getConfiguration()['physical_dimensions']

    def getPsychopyMonitorName(self):
        """
        Returns the name of the psychoPy Monitor configuration being used for the Display.
        
        This method is only of meaning when psychoPy is being used as the Python
        framework driving stimulus presentation in the Experiment process script.
        (which is usually the case).
        
        Args: 
            None
            
        Returns:
            str: Name of the PsychoPy Monitor configuration being used for the Display.
        """
        return self.getConfiguration().get('psychopy_monitor_name')
        
    @classmethod
    def _getEnabledDisplays(cls):
        return cls._enabled_display_instances
    
    @classmethod
    def _createAllRuntimeInfoDicts(cls):
        tempd=ioHubDialog()
        display_count=wx.Display.GetCount()

        runtime_info_list=[]
        
        for i in range(display_count):
            d=wx.Display(i)
            mode=d.GetCurrentMode()
            x,y,w,h=d.GetGeometry()
            primary=d.IsPrimary()
            #ok=d.IsOk()
            runtime_info=dict()
            runtime_info['index']=i
            runtime_info['pixel_width']=w
            runtime_info['pixel_height']=h            
            runtime_info['bounds']=(x,y,x+w,y+h)
            runtime_info['retrace_rate']=mode.refresh
            runtime_info['bits_per_pixel']=mode.bpp
            runtime_info['primary']=primary
            runtime_info['pixel_resolution']=mode.w,mode.h
                                                
            runtime_info_list.append(runtime_info)

            #ioHub.print2err("Display {0} runtime info: {1}".format(i,runtime_info))
            del d
            
        tempd.Destroy()
        tempd=None
        
        return runtime_info_list

    def _addRuntimeInfoToDisplayConfig(self):
        
        if self not in Display._enabled_display_instances:
            Display._enabled_display_instances.append(self)
            
        display_config=self.getConfiguration()

        runtime_info=display_config.get('runtime_info',None)
        if runtime_info is None:        
            runtime_info=self.getRuntimeInfoByIndex(self.device_number)        
            display_config['runtime_info']=runtime_info

            self._createPsychopyCalibrationFile()
            
            
            pixel_width=runtime_info['pixel_width']
            pixel_height=runtime_info['pixel_height']
            
            
            phys_width=display_config["physical_dimensions"]['width']
            phys_height=display_config["physical_dimensions"]['height']
            phys_unit_type=display_config["physical_dimensions"]['unit_type']
            
             
            # add pixels_per_degree to runtime info
            ppd_x=misc.deg2pix(1.0,self._psychopy_monitor)#math.tan(math.radians(0.5))*2.0*viewing_distance*pixel_width/phys_width
            ppd_y=misc.deg2pix(1.0,self._psychopy_monitor)#math.tan(math.radians(0.5))*2.0*viewing_distance*pixel_height/phys_height
            runtime_info['pixels_per_degree']=ppd_x,ppd_y            
                    
            self. _calculateCoordMappingFunctions(pixel_width,pixel_height,phys_unit_type, phys_width,phys_height)
            
            left,top,right,bottom=runtime_info['bounds']
            coord_left,coord_top=self.pixel2DisplayCoord(left,top,self.device_number)
            coord_right,coord_bottom=self.pixel2DisplayCoord(right,bottom,self.device_number)
            runtime_info['coordinate_bounds']= coord_left,coord_top,coord_right,coord_bottom

            
    def _calculateCoordMappingFunctions(self,pixel_width,pixel_height,phys_unit_type, phys_width,phys_height):
        # calculate transform matrix
        coord_type=self.getCoordinateType()
        if coord_type in Display._coord_type_mappings:
            coord_type=Display._coord_type_mappings[coord_type]
        else:   
            print2err(" *** Display device error: Unknown coordinate type: {0}".format(coord_type))
            return

        # for now, use psychopy unit conversions so that drawing positions match device positions exactly
        l,t,r,b=self.getBounds() 
        w=r-l
        h=b-t
                
        def display2psychopyPix(x,y):
            x=x-l
            y=y-t
            #x=math.fabs(x/w)*w
            #y=math.fabs(y/h)*h           
            return (x-w/2),-y+h/2

        def psychopy2displayPix(cx,cy):
            return l+(cx+w/2),t+(cy-h/2) 
             
        if coord_type=='pix':
            def pix2coord(self, x,y,display_index=None):
                if display_index == self.getIndex(): 
                    return display2psychopyPix(x,y)
                return x,y
            self._pix2coord=pix2coord
        
            def coord2pix(self,cx,cy,display_index=None):
                if display_index == self.getIndex():
                    return psychopy2displayPix(cx,cy)             
                return cx,cy
            self._coord2pix=coord2pix
            
        elif coord_type=='cm':
            def pix2cmcoord(self, x,y,display_index=None):
                #print2err('Display {0} bounds: {1}'.format(display_index,self.getBounds()))
                if display_index == self.getIndex():      
                    ppx,ppy=display2psychopyPix(x,y)
                    return misc.pix2cm(ppx,self._psychopy_monitor),misc.pix2cm(ppy,self._psychopy_monitor)
                return x,y
            self._pix2coord=pix2cmcoord
        
            def cmcoord2pix(self,cx,cy,display_index=None):
                if display_index == self.getIndex():
                    return psychopy2displayPix(misc.cm2pix(cx,self._psychopy_monitor),misc.cm2pix(cy,self._psychopy_monitor))  
                return cx,cy
            self._coord2pix=cmcoord2pix
            
        elif coord_type=='deg':
            def pix2degcoord(self, x,y,display_index=None):
                if display_index == self.getIndex():      
                    ppx,ppy=display2psychopyPix(x,y)
#                    print2err('pix2degcoord: ',(x,y),( ppx,ppy),( misc.pix2deg(ppx,self._psychopy_monitor),misc.pix2deg(ppy,self._psychopy_monitor)))
                    return misc.pix2deg(ppx,self._psychopy_monitor),misc.pix2deg(ppy,self._psychopy_monitor)
                return x,y
            self._pix2coord=pix2degcoord
        
            def degcoord2pix(self,degx,degy,display_index=None):
                if display_index == self.getIndex():
                    return psychopy2displayPix(misc.deg2pix(degx,self._psychopy_monitor),misc.cm2pix(degy,self._psychopy_monitor))   
                return degx,degy
            self._coord2pix=degcoord2pix
            
        elif coord_type=='norm':
            def pix2ncoord(self, x,y,display_index=None):
                #print2err('Display {0} bounds: {1}'.format(display_index,self.getBounds()))
                if display_index == self.getIndex():      
                    ppx,ppy=display2psychopyPix(x,y)
                    return ppx/((r-l)/2.0),ppy/((b-t)/2.0)
                return x,y
            self._pix2coord=pix2ncoord
        
            def ncoord2pix(self,nx,ny,display_index=None):
                if display_index == self.getIndex():
                    return psychopy2displayPix(nx*((r-l)/2.0),ny*((b-t)/2.0)) 
                return nx,ny
            self._coord2pix=ncoord2pix
            
#        if coord_type=='pix':
            
#        origin=self.getOrigin()
#        if origin not in Display._supported_origin_types:   
#            print2err(" *** Display device error: Unknown origin type: {0}".format(origin))
#            return
#        
#        x1,y1,x2,y2=self.getBounds()     
#        print2err('getBounds: ',self.getBounds(),  )
#
#        bounds_matrix=np.matrix([[x1,y1,1,0],[-y1,x1,0,1],[x2,y2,1,0],[-y2,x2,0,1]])                
#        
#        cx1=None
#        cy1=None            
#        cx2=None
#        cy2=None
#                                    
##        if coord_type == 'org':
##            cx1=x1
##            cy1=y1            
##            cx2=x2
##            cy2=y2
#        if coord_type == 'pix':
#            if origin == 'center':
#                cx1=-pixel_width/2.0
#                cy1=pixel_height/2.0
#                cx2=pixel_width/2.0
#                cy2=-pixel_height/2.0
##            elif origin == 'top_left':
##                cx1=0
##                cy1=0
##                cx2=pixel_width
##                cy2=pixel_height
##            elif origin == 'bottom_left':
##                cx1=0
##                cy1=pixel_height
##                cx2=pixel_width
##                cy2=0
#        elif coord_type in ['mm','cm','inch']:
#            phys_to_coord_ratio=1.0                
##            if coord_type == 'mm':
##                if phys_unit_type == 'cm':
##                    phys_to_coord_ratio=10.0
##                elif phys_unit_type == 'inch':
##                    phys_to_coord_ratio=25.4
#            if coord_type == 'cm':
#                if phys_unit_type == 'mm':
#                    phys_to_coord_ratio=0.1
#                elif phys_unit_type == 'inch':
#                    phys_to_coord_ratio=2.54
##            elif coord_type == 'inch':
##                if phys_unit_type == 'mm':
##                    phys_to_coord_ratio=0.0393701
##                elif phys_unit_type == 'cm':
##                    phys_to_coord_ratio=0.393701
#                    
#            if origin == 'center':
#                phys_to_coord_ratio=2.0*phys_to_coord_ratio                
#                cx1=-phys_width/phys_to_coord_ratio
#                cy1=phys_height/phys_to_coord_ratio
#                cx2=phys_width/phys_to_coord_ratio
#                cy2=-phys_height/phys_to_coord_ratio
##            elif origin == 'top_left':
##                cx1=0.0
##                cy1=0.0
##                cx2=phys_width*phys_to_coord_ratio
##                cy2=phys_height*phys_to_coord_ratio
##            elif origin == 'bottom_left':
##                cx1=0.0
##                cy1=phys_height*phys_to_coord_ratio
##                cx2=phys_width*phys_to_coord_ratio
##                cy2=0.0
#        elif coord_type == 'norm':
#            if origin == 'center':
#                cx1=-1.0
#                cy1=1.0
#                cx2=1.0
#                cy2=-1.0
##            elif origin == 'top_left':
##                cx1=0.0
##                cy1=0.0
##                cx2=1.0
##                cy2=1.0
##            elif origin == 'bottom_left':
##                cx1=0.0
##                cy1=1.0
##                cx2=1.0
##                cy2=0.0
##        elif coord_type == 'percent':
##            if origin == 'center':
##                cx1=-50.0
##                cy1=50.0
##                cx2=50.0
##                cy2=-50.0
##            elif origin == 'top_left':
##                cx1=0.0
##                cy1=0.0
##                cx2=100.0
##                cy2=100.0
##            elif origin == 'bottom_left':
##                cx1=0.0
##                cy1=100.0
##                cx2=100.0
##                cy2=0.0
#        elif coord_type == 'deg':
#            if origin == 'center':
#                cx1=-degree_width/2.0
#                cy1=degree_height/2.0
#                cx2=degree_width/2.0
#                cy2=-degree_height/2.0
##            elif origin == 'top_left':
##                cx1=0.0
##                cy1=0.0
##                cx2=degree_width
##                cy2=degree_height
##            elif origin == 'bottom_left':
##                cx1=0.0
##                cy1=degree_height
##                cx2=degree_width
##                cy2=0.0
#        
#        if cx1 is not None and cy1 is not None  and cx2 is not None and cy2 is not None :                
#            coord_matrix=np.matrix( [[cx1],[cy1],[cx2],[cy2]] )               
#            abcd = np.linalg.solve(bounds_matrix, coord_matrix)
#            a,b,c,d=np.array(abcd)[:,0]
#            #print2err('abcd: {0}\n a={1}, b={2} , c={3}, d={4}'.format(abcd,a,b,c,d))
#        
#        
#            def pix2coord(self, x,y,display_index=None):
#                #print2err('Display {0} bounds: {1}'.format(display_index,self.getBounds()))
#                if display_index == self.getIndex(): 
#                    return a*x+b*y+c, b*x-a*y+d
#                return x,y
#                
#            self._pix2coord=pix2coord
#        
#            def coord2pix(self,cx,cy,display_index=None):
#                if display_index == self.getIndex():
#                    aabb=(a**2+b**2)
#                    return (a*cx+b*cy-b*d-a*c)/aabb, (b*cx-a*cy-b*c+a*d)/aabb                    
#                return cx,cy
#        
#            self._coord2pix=coord2pix
                    
    def _createPsychopyCalibrationFile(self):
        display_config=self.getConfiguration()
        
        override_using_psycho_settings=display_config.get('override_using_psycho_settings',False)
        psychopy_monitor_name=display_config.get('psychopy_monitor_name',None)
        if psychopy_monitor_name is None or psychopy_monitor_name == 'None':
            return False
            
        from psychopy import monitors#,misc
        
        existing_monitors=monitors.getAllMonitors()

        psychoMonitor=None
        
        if override_using_psycho_settings is True and psychopy_monitor_name in existing_monitors: 
            print2err('**** Updating ioHub Display settings based on PsychoPy Monitor config...')

            
#            print2err('psychopy_monitor_name: ',psychopy_monitor_name)
#            print2err('existing_monitors: ',existing_monitors)
#            print2err(psychopy_monitor_name,' monitor exists: ',psychopy_monitor_name in existing_monitors)
            
            psychoMonitor = monitors.Monitor(psychopy_monitor_name)

            px,py=self.getPixelResolution()
            mwidth=psychoMonitor.getWidth()*10.0
            aspect_ratio=px/float(py)
            mheight=mwidth/aspect_ratio
            display_config['physical_dimensions']['width']=mwidth
            display_config['physical_dimensions']['height']=mheight
            display_config['physical_dimensions']['unit_type']='mm'

            display_config['default_eye_distance']['surface_center']=psychoMonitor.getDistance()*10.0
            display_config['default_eye_distance']['unit_type']='mm'
            
#            print2err('self.getDefaultEyeDistance(): ',self.getDefaultEyeDistance())
#            print2err('psychoMonitor.getDistance()*10.0: ',psychoMonitor.getDistance()*10.0)
#            print2err('mwidth: ' ,mwidth)
#            print2err('aspect_ratio: ', aspect_ratio)
#            print2err('px,py: ', (px,py))
#            print2err('mheight: ', mheight)
#            print2err('getPhysicalDimensions: ', self.getPhysicalDimensions())
        else:
            print2err('**** Setting / Creating PsychoPy Monitor Config based on ioHub Display settings...')

            stim_area=display_config.get('physical_dimensions')
            dwidth=stim_area['width']
            
            # switch from mm to cm if required
            dw_unit_type=stim_area['unit_type']
            if dw_unit_type == 'mm':
                dwidth=dwidth/10.0
    
            ddist= self.getDefaultEyeDistance()
            unit_type=self.getConfiguration()['default_eye_distance']\
                                            ['unit_type']                                        
            # switch from mm to cm if required
            if unit_type == 'mm':
                ddist=ddist/10.0
            
            psychoMonitor=monitors.Monitor(psychopy_monitor_name,
                                       width=dwidth, distance=ddist, gamma=1.0)
            # SS: I don't think this means the current screen resolution, so commenting out.
            #psychoMonitor.setSizePix(self.getPixelResolution())                                   
            psychoMonitor.saveMon()

        self._psychopy_monitor=psychoMonitor
#        print2err("psychopy dist: ",psychoMonitor.getDistance())
#        print2err("psychopy getSizePix: ",psychoMonitor.getSizePix())
#        print2err("psychopy getWidth: ",psychoMonitor.getWidth())
#        print2err("misc.deg2pix(1,psychoMonitor): ", misc.deg2pix(1,psychoMonitor))
#        print2err("misc.pix2deg(1920,psychoMonitor): ",misc.pix2deg(1920,psychoMonitor))
#        print2err("misc.pix2deg(1080,psychoMonitor): ",misc.pix2deg(1080,psychoMonitor))

        return True        

    def _close(self):
        Device._close(self) 
            
    ################################################
    #
    # distToPixel
    #
    # Convert between distance coordinates and pixel coordinates.
    #
    # Distance coordinates are 2D Cartesian coordinates, measured from an origin at the
    # center pixel,  and are real distance units (inches, centimeters, etc.) along horizontal and
    # vertical screen axes.
    #
#    @staticmethod
#    def distToPixel(hpix_per_dist_unit, vpix_perdist_unit, pixHres, pixVres, distH, distV):
#        r = ucs.distToPixel(hpix_per_dist_unit,vpix_perdist_unit,pixHres, pixVres,distH,distV)
#        return r

#    @staticmethod
#    def pixelToDist(hpix_per_dist_unit,vpix_perdist_unit,pixHres, pixVres, pixH, pixV):
#        r = ucs.pixelToDist(hpix_per_dist_unit,vpix_perdist_unit,pixHres, pixVres, pixH, pixV)
#        return r

    #
    # All of following assume a nominal eye point 'eye2display' distance units from display
    # with line-of-gaze normal to the display at the display center.  Angle variable are
    # assumed to have units of degrees.
    #
    # Since the Python math lib trig functions work with radians,
    # a radian to angle conversion factor (deg/rad = 57.2958) is included to give angle
    # variables 'degree' units.
    #

    #
    # Convert between distance coordinates (distH, distV) and 'normalized Cartesian
    # coordinates' (ndH, ndV).
    #
    # 'Normalized Cartesian coordinates' are Cartesian distance coordinates, normalized by
    # by the distance from the nominal eye point to the display.  For very small distances
    # from the origin, these values coorespond to visual angle from the origin along the
    # horizontal and vertical display axes. A factor of 57.2958 is used so that the values
    # correspond to degrees rather than radians.
    #
    
#    @staticmethod
#    def convertDistToNd(eye2display,distH,distV):
#        return ucs.convertDistToNd(eye2display,distH,distV)
        
#    @staticmethod
#    def convertNdToDist(eye2display, ndH, ndV):
#        return ucs.convertNdToDist(eye2display, ndH, ndV)

    #
    # Convert between distance coordinates (distH, distV) and
    # 'Cartesian Angles' (caH, caV).
    # 'Cartesian Angles' are visual angles (from nominal eye point) along
    # horizontal and vertical display axes.  In other words, the horizontal coordinate is the
    # visual angle between the origin and the intersection of the Cartesian
    # coordinate line with the horizontal axes.
    #
#    @staticmethod
#    def distToCa(eye2display, distH, distV):
#        return ucs.distToCa(eye2display, distH, distV)
    
#    @staticmethod
#    def caToDist(eye2display, caH, caV):
#        return ucs.caToDist(eye2display, caH, caV)

        
    #
    # Convert between distance coordinates (distH, distV) and Fick Coordinates (as,el)
    #
#    @staticmethod
#    def distToFick(eye2display,distH,distV):
#        return ucs.distToFick(eye2display,distH,distV)

#    @staticmethod
#    def fickToDist(eye2display, az, el):
#        return ucs.fickToDist(eye2display, az, el)

    #
    # Convert between distance coordinates (distH, distV) and 'symmetric angle'
    # coordinates (saH, saV).
    # 'Symmetric angles' are visual angles between a point on the display and the central
    # axes lines, measured along lines parallel to the display axes.  The vertical coordinate is
    # same as the Fick elevation angle.  The horizontal coordinate is measured in a
    # symmetrical fashion and is not the same as the Fick azimuth angle.
    #
#    @staticmethod
#    def distToSa(eye2display, distH, distV):
#        return ucs.distToSa(eye2display,distH,distV)
    
#    @staticmethod
#    def saToDist(self,eye2display, saH, saV):
#        return ucs.saToDist(eye2display, saH, saV)


            
######### Display Events ###########