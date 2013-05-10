###########################
The XInput Gamepad Device
###########################

**Platforms:** Windows

.. autoclass:: psychopy.iohub.devices.xinput.Gamepad
    :exclude-members: DEVICE_LABEL , ALL_EVENT_CLASSES, CLASS_ATTRIBUTE_NAMES, DEVICE_BUFFER_LENGTH_INDEX, DEVICE_CLASS_NAME_INDEX, DEVICE_MAX_ATTRIBUTE_INDEX, DEVICE_TIMEBASE_TO_SEC, DEVICE_TYPE_ID, DEVICE_TYPE_ID_INDEX, DEVICE_TYPE_STRING, DEVICE_USER_LABEL_INDEX, NUMPY_DTYPE, e, DEVICE_FIRMWARE_VERSION_INDEX, DEVICE_HARDWARE_VERSION_INDEX,DEVICE_MANUFACTURER_NAME_INDEX,DEVICE_MODEL_NAME_INDEX, DEVICE_MODEL_NUMBER_INDEX, DEVICE_NUMBER_INDEX, DEVICE_SERIAL_NUMBER_INDEX, DEVICE_SOFTWARE_VERSION_INDEX, EVENT_CLASS_NAMES
    :member-order: bysource
    
GamePad Device Configuration Settings
########################################

.. literalinclude:: default_yaml_configs/default_xinput.yaml
    :language: yaml
    
GamePad Event Types
########################

.. autoclass:: psychopy.iohub.devices.xinput.GamepadStateChangeEvent
    :exclude-members: DEVICE_ID_INDEX, filter_id, device_id, NUMPY_DTYPE, BASE_EVENT_MAX_ATTRIBUTE_INDEX, CLASS_ATTRIBUTE_NAMES, EVENT_CONFIDENCE_INTERVAL_INDEX, EVENT_DELAY_INDEX, EVENT_DEVICE_TIME_INDEX, EVENT_EXPERIMENT_ID_INDEX, EVENT_FILTER_ID_INDEX, EVENT_HUB_TIME_INDEX, EVENT_ID_INDEX, EVENT_LOGGED_TIME_INDEX, EVENT_SESSION_ID_INDEX, EVENT_TYPE_ID, EVENT_TYPE_ID_INDEX, EVENT_TYPE_STRING, IOHUB_DATA_TABLE, PARENT_DEVICE, createEventAsClass, createEventAsDict, createEventAsNamedTuple, e, namedTupleClass
    :member-order: bysource
    
Notes and Considerations
###########################

..note:: If gamepad thumbstick position data is going to be used to control 
    the position of a stim object on the PsychoPy Window, the following equation
    can be used to convert the normalized thumbstick data to Display coordinates::


        def normalizedValue2Coord(normalized_position,normalized_magnitude,display_coord_dim_size):
            x,y=normalized_position[0]*normalized_magnitude,normalized_position[1]*normalized_magnitude
            w,h=display_coord_dim_size
            return x*(w/2.0),y*(h/2.0)

        # example usage:

        display=io.devices.display
        gamepad=io.devices.gamepad
        keyboard=io.devices.keyboard

        # create a PsychoPy stim to move with each thumb stick
        # 
        # thumb_left_stim = .......
        # thumb_right_stim = .......

        dl,dt,dr,db=display.getCoordBounds()
        coord_size=dr-dl,dt-db

        io.clearEvents('all')

        while not keyboard.getEvents(): 
            # thumb stick state is returned as a 3 item lists (x , y , magnitude)
            x,y,mag=gamepad.getThumbSticks()['right_stick'] 
            xx,yy=self.normalizedValue2Coord((x,y),mag,coord_size)
            thumb_right_stim.setPos((xx, yy))
            
            # thumb stick state is returned as a 3 item lists (x , y , magnitude)
            x,y,mag=gamepad.getThumbSticks()['left_stick'] # sticks are 3 item lists (x,y,magnitude)
            xx,yy=self.normalizedValue2Coord((x,y),mag,coord_size)
            thumb_left_stim.setPos((xx, yy))

            thumb_right_stim.draw()
            thumb_left_stim.draw()

            io.clearEvents('all')

            window.flip()
            
* Ensure that XInput version 1.3 is installed on your computer.
* If using a wireless gamepad, ensure the gamepad has been powered on befor stating the experiment.
* For the supported Logitech gamepads, be sure that the switch on the gamepad is set to the 'X' position, indicating that the gamepad will use the XInput protocal.
