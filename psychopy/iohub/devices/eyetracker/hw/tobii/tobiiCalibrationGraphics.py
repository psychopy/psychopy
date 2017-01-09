"""
ioHub
Common Eye Tracker Interface
.. file: ioHub/devices/eyetracker/hw/tobii/TobiiCalibrationGraphics.py

Copyright (C) 2012-2013 iSolver Software Solutions
Distributed under the terms of the GNU General Public License (GPL version 3 or any later version).

.. moduleauthor:: Sol Simpson <sol@isolver-software.com>
.. fileauthor:: Sol Simpson <sol@isolver-software.com>

"""

import psychopy
from psychopy import visual
import gevent
import time, Queue
import copy
import numpy as np

from ..... import print2err,printExceptionDetailsToStdErr,convertCamelToSnake
from .... import Computer,DeviceEvent
from .....constants import EventConstants
from . tobiiclasses import Point2D

currentTime=Computer.getTime

class TobiiPsychopyCalibrationGraphics(object):
    IOHUB_HEARTBEAT_INTERVAL=0.050   # seconds between forced run through of
                                     # micro threads, since one is blocking
                                     # on camera setup.
    WINDOW_BACKGROUND_COLOR=(128,128,128)
    CALIBRATION_POINT_LIST=[(0.5, 0.5),(0.1, 0.1),(0.9, 0.1),(0.9, 0.9),(0.1, 0.9),(0.5, 0.5)]

    TEXT_POS=[0,0]
    TEXT_COLOR=[0,0,0]
    TEXT_HEIGHT=36
    _keyboard_key_index = EventConstants.getClass(EventConstants.KEYBOARD_RELEASE).CLASS_ATTRIBUTE_NAMES.index('key')
    def __init__(self, eyetrackerInterface,screenColor=None,
                 calibrationPointList=None):
        self._eyetrackerinterface=eyetrackerInterface
        # The EyeX interface has to fake the other API's calibration stuff
        if eyetrackerInterface._isEyeX:
            self._tobii = eyetrackerInterface._tobii
        else:
            self._tobii = eyetrackerInterface._tobii._eyetracker
        self.screenSize = eyetrackerInterface._display_device.getPixelResolution()

        self.width=self.screenSize[0]
        self.height=self.screenSize[1]
        self._ioKeyboard=None

        self._msg_queue=Queue.Queue()
        self._lastCalibrationOK=False
        self._lastCalibrationReturnCode=0
        self._lastCalibration=None
        
        TobiiPsychopyCalibrationGraphics.WINDOW_BACKGROUND_COLOR=screenColor


        if calibrationPointList is not None:
            TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_LIST=calibrationPointList

        calibration_methods = dict(THREE_POINTS=3,
                                   FIVE_POINTS=5, 
                                   NINE_POINTS=9, 
                                   THIRTEEN_POINTS=13)

        cal_type=self._eyetrackerinterface.getConfiguration()['calibration']['type']

        if cal_type in calibration_methods:
            num_points=calibration_methods[cal_type]
            
            if num_points == 3:
                TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_LIST=[(0.5,0.1),
                                                                         (0.1,0.9),
                                                                         (0.9,0.9),
                                                                         (0.5,0.1)]
            elif num_points == 9:
                TobiiPsychopyCalibrationGraphics.CALIBRATION_POINT_LIST=[(0.5, 0.5),
                                                                         (0.1, 0.5),
                                                                         (0.9, 0.5),
                                                                         (0.1, 0.1),
                                                                         (0.5, 0.1),
                                                                         (0.9, 0.1),
                                                                         (0.9, 0.9),
                                                                         (0.5, 0.9),
                                                                         (0.1, 0.9),
                                                                         (0.5, 0.5)]
        display=self._eyetrackerinterface._display_device
        self.window=visual.Window(self.screenSize,monitor=display.getPsychopyMonitorName(),
                            units=display.getCoordinateType(),
                            fullscr=True,
                            allowGUI=False,
                            screen=display.getIndex(),
                            color=self.WINDOW_BACKGROUND_COLOR[0:3],
                            colorSpace='rgb255'
                            )       
        self.window.flip(clearBuffer=True)
        
        self._createStim()        
        self._registerEventMonitors()
        self._lastMsgPumpTime=currentTime()
        
        self.clearAllEventBuffers()

    def clearAllEventBuffers(self):
        self._eyetrackerinterface._iohub_server.eventBuffer.clear()
        for d in self._eyetrackerinterface._iohub_server.devices:
            d.clearEvents()

    def _registerEventMonitors(self):
        if self._eyetrackerinterface._iohub_server:
            for dev in self._eyetrackerinterface._iohub_server.devices:
                #ioHub.print2err("dev: ",dev.__class__.__name__)
                if dev.__class__.__name__ == 'Keyboard':
                    kbDevice=dev

        if kbDevice:
            eventIDs=[]
            for event_class_name in kbDevice.__class__.EVENT_CLASS_NAMES:
                eventIDs.append(getattr(EventConstants,convertCamelToSnake(event_class_name[:-5],False)))

            self._ioKeyboard=kbDevice
            self._ioKeyboard._addEventListener(self,eventIDs)
        else:
            print2err("Warning: Tobii Cal GFX could not connect to Keyboard device for events.")

    def _unregisterEventMonitors(self):
        if self._ioKeyboard:
            self._ioKeyboard._removeEventListener(self)
            
    def _handleEvent(self,ioe):
        event=copy.deepcopy(ioe)
        event_type_index=DeviceEvent.EVENT_TYPE_ID_INDEX
        if event[event_type_index] == EventConstants.KEYBOARD_RELEASE:
            if event[self._keyboard_key_index] == u' ':
                self._msg_queue.put("SPACE_KEY_ACTION")
                self.clearAllEventBuffers()
            elif event[self._keyboard_key_index] == u'escape':
                self._msg_queue.put("QUIT")
                self.clearAllEventBuffers()

    def MsgPump(self):
        #keep the psychopy window happy ;)
        if currentTime()-self._lastMsgPumpTime>self.IOHUB_HEARTBEAT_INTERVAL:                
            # try to keep ioHub from being blocked. ;(
            if self._eyetrackerinterface._iohub_server:
                for dm in self._eyetrackerinterface._iohub_server.deviceMonitors:
                    dm.device._poll()
                self._eyetrackerinterface._iohub_server.processDeviceEvents()
            self._lastMsgPumpTime=currentTime()

    def getNextMsg(self):
        try:
            msg=self._msg_queue.get(block=True,timeout=0.02)
            self._msg_queue.task_done()
            return msg
        except Queue.Empty:
            pass

    def _createStim(self):         
        """
            outer_diameter: 35
            outer_stroke_width: 5
            outer_fill_color: [255,255,255]
            outer_line_color: [255,255,255]
            inner_diameter: 5
            inner_stroke_width: 0
            inner_color: [0,0,0]
            inner_fill_color: [0,0,0]
            inner_line_color: [0,0,0]        
            calibration_prefs=self._eyetrackerinterface.getConfiguration()['calibration']['target_attributes']
        """
        coord_type=self._eyetrackerinterface._display_device.getCoordinateType()
        calibration_prefs=self._eyetrackerinterface.getConfiguration()['calibration']['target_attributes']
        self.calibrationPointOUTER = visual.Circle(self.window,pos=(0,0) ,
                                                   lineWidth=calibration_prefs['outer_stroke_width'],
                                                   radius=calibration_prefs['outer_diameter']/2.0,
                                                   name='CP_OUTER',
                                                   fillColor=calibration_prefs['outer_fill_color'],
                                                   lineColor=calibration_prefs['outer_line_color'],
                                                   fillColorSpace='rgb255',
                                                   lineColorSpace='rgb255',
                                                   opacity=1.0, 
                                                   interpolate=False,
                                                   edges=64,
                                                   units=coord_type)
                                                   
        self.calibrationPointINNER = visual.Circle(self.window,pos=(0,0),
                                                   lineWidth=calibration_prefs['inner_stroke_width'],
                                                   radius=calibration_prefs['inner_diameter']/2.0,
                                                    name='CP_INNER',
                                                   fillColor=calibration_prefs['inner_fill_color'],
                                                   lineColor=calibration_prefs['inner_line_color'],
                                                   fillColorSpace='rgb255',
                                                   lineColorSpace='rgb255',
                                                   opacity=1.0, 
                                                   interpolate=False,
                                                   edges=64,
                                                   units=coord_type)
        

        instuction_text="Press SPACE to Start Calibration; ESCAPE to Exit."
        self.textLineStim=visual.TextStim(self.window, 
                                                        text=instuction_text, 
                                                        pos = self.TEXT_POS, 
                                                        height=self.TEXT_HEIGHT, 
                                                        color=self.TEXT_COLOR, 
                                                        colorSpace='rgb255',
                                                        alignHoriz='center',
                                                        alignVert='center',
                                                        units='pix',
                                                        wrapWidth=self.width*0.9)
        
        # create Tobii eye position feedback graphics
        #
        sw,sh=self.screenSize
        self.hbox_bar_length=hbox_bar_length=sw/4
        hbox_bar_height=6
        marker_diameter=7
        self.marker_heights=(-sh/2.0*.7,-sh/2.0*.75,-sh/2.0*.8,-sh/2.0*.7,-sh/2.0*.75,-sh/2.0*.8)
        
        bar_vertices=[-hbox_bar_length/2,-hbox_bar_height/2],[hbox_bar_length/2,-hbox_bar_height/2],[hbox_bar_length/2,hbox_bar_height/2],[-hbox_bar_length/2,hbox_bar_height/2]
        
        self.feedback_resources=psychopy.iohub.OrderedDict()
                
        self.feedback_resources['hbox_bar_x'] = visual.ShapeStim(win=self.window, 
                                      lineColor='White', 
                                      fillColor='Firebrick', 
                                      vertices=bar_vertices, 
                                      pos=(0, self.marker_heights[0]))
        self.feedback_resources['hbox_bar_y'] = visual.ShapeStim(win=self.window, 
                                      lineColor='White', 
                                      fillColor='DarkSlateGray', 
                                      vertices=bar_vertices, 
                                      pos=(0, self.marker_heights[1]))
        self.feedback_resources['hbox_bar_z'] = visual.ShapeStim(win=self.window, 
                                      lineColor='White', 
                                      fillColor='GoldenRod', 
                                      vertices=bar_vertices, 
                                      pos=(0, self.marker_heights[2]))

        marker_vertices=[-marker_diameter,0],[0,marker_diameter],[marker_diameter,0],[0,-marker_diameter]
        self.feedback_resources['left_hbox_marker_x'] = visual.ShapeStim(win=self.window, 
                                      lineColor='White', fillColor='Black', 
                                      vertices= marker_vertices, 
                                      pos=(0, self.marker_heights[0]))
        self.feedback_resources['left_hbox_marker_y'] = visual.ShapeStim(win=self.window, 
                                      lineColor='White', fillColor='Black', 
                                      vertices= marker_vertices, 
                                      pos=(0, self.marker_heights[1]))
        self.feedback_resources['left_hbox_marker_z'] = visual.ShapeStim(win=self.window, 
                                      lineColor='White', fillColor='Black', 
                                      vertices= marker_vertices, 
                                      pos=(0, self.marker_heights[2]))
        self.feedback_resources['right_hbox_marker_x'] = visual.ShapeStim(win=self.window, 
                                      lineColor='White', fillColor='DimGray', 
                                      vertices= marker_vertices, 
                                      pos=(0, self.marker_heights[0]))
        self.feedback_resources['right_hbox_marker_y'] = visual.ShapeStim(win=self.window, 
                                      lineColor='White', fillColor='DimGray', 
                                      vertices= marker_vertices, 
                                      pos=(0, self.marker_heights[1]))
        self.feedback_resources['right_hbox_marker_z'] = visual.ShapeStim(win=self.window, 
                                      lineColor='White', fillColor='DimGray', 
                                      vertices= marker_vertices, 
                                      pos=(0, self.marker_heights[2]))


    def runCalibration(self):
        """
        Performs a simple calibration routine. 
        
        Args: 
            None
        
        Result:
            bool: True if calibration was successful. False if not, in which case exit the application.            
        """

        self._lastCalibrationOK=False
        self._lastCalibrationReturnCode=0
        self._lastCalibration=None
        
        calibration_sequence_completed=False        

        instuction_text="Press SPACE to Start Calibration; ESCAPE to Exit."
        continue_calibration=self.showSystemSetupMessageScreen(instuction_text,True)
        if not continue_calibration:
            return False
            
        auto_pace=self._eyetrackerinterface.getConfiguration()['calibration']['auto_pace']
        pacing_speed=self._eyetrackerinterface.getConfiguration()['calibration']['pacing_speed']

        randomize_points=self._eyetrackerinterface.getConfiguration()['calibration']['randomize']

        cal_target_list=self.CALIBRATION_POINT_LIST[1:-1]
        if randomize_points is True:
            import random
            random.seed(None)
            random.shuffle(cal_target_list)
            
        cal_target_list.insert(0,self.CALIBRATION_POINT_LIST[0])
        cal_target_list.append(self.CALIBRATION_POINT_LIST[-1])
                
        self._tobii.StartCalibration(self.on_start_calibration)   

        if hasattr(self._tobii,'ClearCalibration'):
            self._tobii.ClearCalibration()

        i=0
        for pt in cal_target_list:
            self.clearAllEventBuffers()
            left,top,right,bottom=self._eyetrackerinterface._display_device.getCoordBounds()
            w,h=right-left,top-bottom            
            x,y=left+w*pt[0],bottom+h*(1.0-pt[1])
            self.drawCalibrationTarget(i,(x,y))
            self.clearAllEventBuffers()
            stime=currentTime()

            def waitingForNextTargetTime():
                return True
            
            if auto_pace is True:
                def waitingForNextTargetTime():
                    return currentTime()-stime<float(pacing_speed)
                
            while waitingForNextTargetTime():
                msg=self.getNextMsg()
                if msg == 'SPACE_KEY_ACTION':
                    break
                elif msg == 'QUIT':
                    return False
                
                self.MsgPump()
                        
            pt2D=Point2D(pt[0],pt[1])
            self._tobii.AddCalibrationPoint(pt2D,self.on_add_calibration_point)
            time.sleep(0.5)            
            self.clearCalibrationWindow()
            self.clearAllEventBuffers()

            i+=1
            if i == len(cal_target_list):
                calibration_sequence_completed=True
        
        if calibration_sequence_completed:
            # The EyeX interface is slower to add calibration points,
            # have to give it a moment before computing
            if self._eyetrackerinterface._isEyeX:
                gevent.sleep(3.0)

            self._tobii.ComputeCalibration(self.on_compute_calibration)
 
            msg=1
            while msg not in ["CALIBRATION_COMPUTATION_COMPLETE","CALIBRATION_COMPUTATION_FAILED"]:        
                msg=self.getNextMsg()
            
        self._tobii.StopCalibration(self.on_stop_calibration)  
        msg=1
        while msg is not "CALIBRATION_FINISHED":        
            msg=self.getNextMsg()

        if self._lastCalibrationOK is True:
            self._tobii.GetCalibration(self.on_calibration_result)

            msg=1
            while msg is not "CALIBRATION_RESULT_RECEIVED":        
                msg=self.getNextMsg()
            
            cal_data_dict={}

            import math
                
            if self._lastCalibration:
                for cal_point_result in self._lastCalibration.plot_data:
                    left_eye_data=cal_point_result.left.map_point
                    
                    lval=None
                    if hasattr(cal_point_result.left,'validity'):
                        lval=cal_point_result.left.validity
                    elif hasattr(cal_point_result.left,'status'):
                        lval=cal_point_result.left.quality
                    left_eye_data=(left_eye_data.x*self.width,left_eye_data.y*self.height),lval
                    
                    rval=None
                    if hasattr(cal_point_result.right,'validity'):
                        rval=cal_point_result.right.validity
                    elif hasattr(cal_point_result.right,'status'):
                        rval=cal_point_result.right.status
                    right_eye_data=cal_point_result.right.map_point
                    right_eye_data=(right_eye_data.x*self.width,right_eye_data.y*self.height),rval
                    
                    target_pos=cal_point_result.true_point.x*self.width,cal_point_result.true_point.y*self.height
                    
                    if target_pos not in cal_data_dict:
                        cal_data_dict[target_pos]=[]
                    cal_data_dict[target_pos].append((left_eye_data,right_eye_data))
    
                cal_stats=dict()
                for (targ_x,targ_y),eye_cal_result_list in cal_data_dict.iteritems():
                    left_stats=dict(pos_sample_count=0,invalid_sample_count=0,avg_err=0.0,min_err=100000.0,max_err=0.0)
                    right_stats=dict(pos_sample_count=0,invalid_sample_count=0,avg_err=0.0,min_err=100000.0,max_err=0.0)
                    
                    for ((left_x,left_y),left_validity),((right_x,right_y),right_validity) in eye_cal_result_list:
                        left_stats['pos_sample_count']+=1.0
                        right_stats['pos_sample_count']+=1.0
                        
                        if left_validity==1:
                            x_err=targ_x-left_x
                            y_err=targ_y-left_y
                            left_err=math.sqrt(x_err*x_err+y_err*y_err)
                            if left_err<left_stats['min_err']:
                                left_stats['min_err']=left_err
                            elif left_err>left_stats['max_err']:
                                left_stats['max_err']=left_err
                            left_stats['avg_err']+=left_err
                        else:
                            left_stats['invalid_sample_count']+=1.0
    
                            
                        if right_validity==1:
                            x_err=targ_x-right_x
                            y_err=targ_y-right_y                        
                            right_err=math.sqrt(x_err*x_err+y_err*y_err)
                            if right_err<right_stats['min_err']:
                                right_stats['min_err']=right_err
                            elif right_err>right_stats['max_err']:
                                right_stats['max_err']=right_err
                            right_stats['avg_err']+=right_err
                        else:
                            right_stats['invalid_sample_count']+=1.0
                        
                    if right_stats['invalid_sample_count']==0:
                        right_stats['valid_sample_percentage']=100.0
                    else:
                        right_stats['valid_sample_percentage']=(1.0-right_stats['invalid_sample_count']/right_stats['pos_sample_count'])*100.0
                    
                    if left_stats['invalid_sample_count']==0:
                        left_stats['valid_sample_percentage']=100.0
                    else:
                        left_stats['valid_sample_percentage']=(1.0-left_stats['invalid_sample_count']/left_stats['pos_sample_count'])*100.0
                 
                    if int(right_stats['pos_sample_count']-right_stats['invalid_sample_count'])>0:
                        right_stats['avg_err']=right_stats['avg_err']/(right_stats['pos_sample_count']-right_stats['invalid_sample_count'])
                    else:
                        right_stats['avg_err']=-1.0
                        
                    if int(left_stats['pos_sample_count']-left_stats['invalid_sample_count'])>0:
                        left_stats['avg_err']=left_stats['avg_err']/(left_stats['pos_sample_count']-left_stats['invalid_sample_count'])
                    else:
                        left_stats['avg_err']=-1.0
                   
                    cal_stats[(targ_x,targ_y)]=dict(left=left_stats,right=right_stats)
            else:
                # EyeX doesn't return calibration stats
                if not self._eyetrackerinterface._isEyeX:
                    print2err("WARNING: Calibration results are NULL.")
            
            instuction_text="Calibration Passed. PRESS 'SPACE' KEY TO CONTINUE."     
            continue_method=self.showSystemSetupMessageScreen(instuction_text,True,msg_types=['SPACE_KEY_ACTION'])
            if continue_method is False:
                return False

        if self._lastCalibrationOK is False:
            instuction_text="Calibration Failed. Options: SPACE: Re-run Calibration; ESCAPE: Exit Setup"            
            continue_method=self.showSystemSetupMessageScreen(instuction_text,True,msg_types=['SPACE_KEY_ACTION','QUIT'])
            if continue_method is False:
                return False
        
        return True
           
    def clearCalibrationWindow(self):
        self.window.flip(clearBuffer=True)

    def showSystemSetupMessageScreen(self,text_msg="Press SPACE to Start Calibration; ESCAPE to Exit.",enable_recording=False,msg_types=['SPACE_KEY_ACTION','QUIT']):
        if enable_recording is True:
            self._eyetrackerinterface.setRecordingState(True)

        self.clearAllEventBuffers()

        while True:
            self.textLineStim.setText(text_msg)
            event_named_tuples=[]    
            for e in self._eyetrackerinterface.getEvents(EventConstants.BINOCULAR_EYE_SAMPLE):
                event_named_tuples.append(EventConstants.getClass(EventConstants.BINOCULAR_EYE_SAMPLE).createEventAsNamedTuple(e))
            #print2err(event_named_tuples)    
            leye_box_pos,reye_box_pos=self.getHeadBoxPosition(event_named_tuples)
            lx,ly,lz=leye_box_pos        
            rx,ry,rz=reye_box_pos
            eye_positions=(lx,ly,lz,rx,ry,rz)
            marker_names=('left_hbox_marker_x','left_hbox_marker_y','left_hbox_marker_z',
                          'right_hbox_marker_x','right_hbox_marker_y','right_hbox_marker_z')
            marker_heights=self.marker_heights
            hbox_bar_length=self.hbox_bar_length
            
            for i,p in enumerate(eye_positions):
                if p is not None:
                    mpoint=hbox_bar_length*p-hbox_bar_length/2.0,marker_heights[i]
                    self.feedback_resources[marker_names[i]].setPos(mpoint)
                    self.feedback_resources[marker_names[i]].setOpacity(1.0)
                else:
                    self.feedback_resources[marker_names[i]].setOpacity(0.0)
    
            self.textLineStim.draw()
            [r.draw() for r in self.feedback_resources.values()]
            self.window.flip()
                 
            msg=self.getNextMsg()
            if msg == 'SPACE_KEY_ACTION' and msg in msg_types:
                if enable_recording is True:
                    self._eyetrackerinterface.setRecordingState(False)
                self.clearAllEventBuffers()
                return True
            elif msg == 'QUIT' and msg in msg_types:
                if enable_recording is True:
                    self._eyetrackerinterface.setRecordingState(False)
                self.clearAllEventBuffers()
                return False                
            self.MsgPump()
            gevent.sleep()
            
        
    def getHeadBoxPosition(self,events):
        #KeyboardInputEvent.CLASS_ATTRIBUTE_NAMES.index('key_id')
        left_eye_cam_x=None
        left_eye_cam_y=None
        left_eye_cam_z=None
        right_eye_cam_x=None
        right_eye_cam_y=None
        right_eye_cam_z=None

        if len(events)==0:
            return (left_eye_cam_x,left_eye_cam_y,left_eye_cam_z),(right_eye_cam_x,right_eye_cam_y,right_eye_cam_z)
        
        event=events[-1]
        if abs(event.left_eye_cam_x) != 1.0 and abs(event.left_eye_cam_y) != 1.0:
            left_eye_cam_x=1.0-event.left_eye_cam_x
            left_eye_cam_y=event.left_eye_cam_y
        if event.left_eye_cam_z != 0.0:
            left_eye_cam_z=event.left_eye_cam_z
        if abs(event.right_eye_cam_x) != 1.0 and abs(event.right_eye_cam_y) != 1.0:
            right_eye_cam_x=1.0-event.right_eye_cam_x
            right_eye_cam_y=event.right_eye_cam_y
        if event.right_eye_cam_z != 0.0:
            right_eye_cam_z=event.right_eye_cam_z
        return (left_eye_cam_x,left_eye_cam_y,left_eye_cam_z),(right_eye_cam_x,right_eye_cam_y,right_eye_cam_z)

    def setTargetDefaults(self):
        """
            outer_diameter: 35
            outer_stroke_width: 5
            outer_fill_color: [255,255,255]
            outer_line_color: [255,255,255]
            inner_diameter: 5
            inner_stroke_width: 0
            inner_color: [0,0,0]
            inner_fill_color: [0,0,0]
            inner_line_color: [0,0,0]        
            calibration_prefs=self._eyetrackerinterface.getConfiguration()['calibration']['target_attributes']
        """
        calibration_prefs=self._eyetrackerinterface.getConfiguration()['calibration']['target_attributes']

        self.calibrationPointOUTER.radius = calibration_prefs['outer_diameter'] / 2.0
        self.calibrationPointOUTER.setLineColor(calibration_prefs['outer_line_color'])
        self.calibrationPointOUTER.setFillColor(calibration_prefs['outer_fill_color'])
        self.calibrationPointOUTER.lineWidth=int(calibration_prefs['outer_stroke_width'])

        self.calibrationPointINNER.radius = calibration_prefs['inner_diameter'] / 2.0
        self.calibrationPointINNER.setLineColor(calibration_prefs['inner_line_color'])
        self.calibrationPointINNER.setFillColor(calibration_prefs['inner_fill_color'])
        self.calibrationPointINNER.lineWidth=int(calibration_prefs['inner_stroke_width'])

        self.calibrationPointOUTER.draw()          
        self.calibrationPointINNER.draw()            
        return self.window.flip(clearBuffer=True)                                                   

    def moveTarget(self,start_pt,end_pt,TARG_VELOCITY):
        sx,sy=start_pt
        ex,ey=end_pt
        dist = np.linalg.norm(end_pt-start_pt)
        sec_dur=dist/TARG_VELOCITY
        num_retraces=sec_dur/self._eyetrackerinterface._display_device.getRetraceInterval()
        x_points=np.linspace(sx, ex, num=int(num_retraces))
        y_points=np.linspace(sy, ey, num=int(num_retraces))
        t_points=zip(x_points,y_points)
        for p in t_points:
            self.calibrationPointOUTER.setPos(p)            
            self.calibrationPointINNER.setPos(p)                                    
            self.calibrationPointOUTER.draw()          
            self.calibrationPointINNER.draw()            
            self.window.flip(clearBuffer=True)                                                                                       
        self.setTargetDefaults()            

    def expandTarget(self,TARG_RAD_MULTIPLIER,EXPANSION_RATE):
        calibration_prefs=self._eyetrackerinterface.getConfiguration()['calibration']['target_attributes']
        orad=calibration_prefs['outer_diameter']/2.0
        self.calibrationPointOUTER.lineWidth=int(calibration_prefs['outer_stroke_width'])
        if self.calibrationPointOUTER.lineWidth<1:
            self.calibrationPointOUTER.lineWidth=1

        max_osize=orad*TARG_RAD_MULTIPLIER        
        if EXPANSION_RATE<1:
            EXPANSION_RATE=1.0

        stime=Computer.getTime()
        self.calibrationPointOUTER.radius = orad
        self.calibrationPointOUTER.draw()          
        self.calibrationPointINNER.draw() 
        ftime=self.window.flip(clearBuffer=True)
        current_size=self.calibrationPointOUTER.radius
        while current_size<max_osize:
            sec_dur=ftime-stime
            if sec_dur<0.0:
                sec_dur=0.0
            stime=ftime
            current_size+= sec_dur*EXPANSION_RATE  
            self.calibrationPointOUTER.radius = current_size
            self.calibrationPointOUTER.draw()          
            self.calibrationPointINNER.draw()            
            ftime=self.window.flip(clearBuffer=True)

    def contractTarget(self,TARG_RAD_MULTIPLIER,EXPANSION_RATE):
        calibration_prefs=self._eyetrackerinterface.getConfiguration()['calibration']['target_attributes']
        orad=calibration_prefs['outer_diameter']/2.0
        self.calibrationPointOUTER.lineWidth=int(calibration_prefs['outer_stroke_width'])
        if self.calibrationPointOUTER.lineWidth<1:
            self.calibrationPointOUTER.lineWidth=1

        max_osize=orad*TARG_RAD_MULTIPLIER        
        if EXPANSION_RATE<1:
            EXPANSION_RATE=1.0

        stime=Computer.getTime()
        self.calibrationPointOUTER.radius = max_osize
        self.calibrationPointOUTER.draw()          
        self.calibrationPointINNER.draw() 
        ftime=self.window.flip(clearBuffer=True)
        current_size=max_osize
        while current_size>orad:
            sec_dur=ftime-stime
            if sec_dur<0.0:
                sec_dur=0.0
            stime=ftime
            current_size-= sec_dur*EXPANSION_RATE  
            self.calibrationPointOUTER.radius = current_size
            self.calibrationPointOUTER.draw()          
            self.calibrationPointINNER.draw()            
            ftime=self.window.flip(clearBuffer=True)
       
    def drawCalibrationTarget(self,target_number,tp): 
        """
            outer_diameter: 35
            outer_stroke_width: 5
            outer_fill_color: [255,255,255]
            outer_line_color: [255,255,255]
            inner_diameter: 5
            inner_stroke_width: 0
            inner_color: [0,0,0]
            inner_fill_color: [0,0,0]
            inner_line_color: [0,0,0]        
            calibration_prefs=self._eyetrackerinterface.getConfiguration()['calibration']['target_attributes']
        """
        try:
            calibration_prefs=self._eyetrackerinterface.getConfiguration()['calibration']['target_attributes']
            animate_prefs=calibration_prefs.get('animate',None)

            if animate_prefs:
                CONTRACT_ONLY=animate_prefs.get('contract_only',False)
                TARG_VELOCITY=animate_prefs.get('movement_velocity',300.0) # 200 pix / sec
                TARG_RAD_MULTIPLIER=animate_prefs.get('expansion_ratio',3.0)
                EXPANSION_RATE=animate_prefs.get('expansion_speed',30.0)

                if target_number==0:
                    # Do first point animation
                    self.calibrationPointOUTER.setPos(tp)          
                    self.calibrationPointINNER.setPos(tp)  
                    self.setTargetDefaults()
                    if CONTRACT_ONLY is False:
                        self.expandTarget(TARG_RAD_MULTIPLIER,EXPANSION_RATE)
                    self.contractTarget(TARG_RAD_MULTIPLIER,EXPANSION_RATE)
                else:
                    # Move from current point to new point
                    # then do point animation
                    spos=self.calibrationPointOUTER.pos
                    #self.calibrationPointOUTER.setPos(tp)            
                    #self.calibrationPointINNER.setPos(tp) 
                    if TARG_VELOCITY > 0.0:
                        self.moveTarget(spos,tp,TARG_VELOCITY)
                    else:
                        self.calibrationPointOUTER.setPos(tp)          
                        self.calibrationPointINNER.setPos(tp)                         
                    self.setTargetDefaults()
                    if CONTRACT_ONLY is False:
                        self.expandTarget(TARG_RAD_MULTIPLIER,EXPANSION_RATE)
                    self.contractTarget(TARG_RAD_MULTIPLIER,EXPANSION_RATE)
            else:
                self.calibrationPointOUTER.setPos(tp)          
                self.calibrationPointINNER.setPos(tp) 
                self.setTargetDefaults()
                
        except Exception:
            printExceptionDetailsToStdErr()                    

    def on_start_calibration(self,*args,**kwargs):
        #ioHub.print2err('on_start_calibration: ',args,kwargs)
        pass
    
    def on_add_calibration_point(self,*args,**kwargs):
        #ioHub.print2err('on_add_calibration_point: ',args,kwargs)
        self._msg_queue.put('DRAW_NEXT')

    def on_stop_calibration(self,*args,**kwargs):
        #ioHub.print2err('on_stop_calibration: ',args,kwargs)
        self._msg_queue.put("CALIBRATION_FINISHED")
        
    def on_compute_calibration(self,*args,**kwargs):
        self._lastCalibrationReturnCode=args[0]
        if self._lastCalibrationReturnCode!=0:
            print2err("ERROR: Tobii Calibration Calculation Failed. Error code: {0}".format(self._lastCalibrationReturnCode))
            self._lastCalibrationOK=False
            self._msg_queue.put("CALIBRATION_COMPUTATION_FAILED")
            
        else:
            self._msg_queue.put("CALIBRATION_COMPUTATION_COMPLETE")
            self._lastCalibrationOK=True

    def on_calibration_result(self,*args,**kwargs):
        self._lastCalibration=args[1]
        self._msg_queue.put("CALIBRATION_RESULT_RECEIVED")
        
