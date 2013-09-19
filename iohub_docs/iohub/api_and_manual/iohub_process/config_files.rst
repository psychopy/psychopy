####################
ioHub Configuration
####################

The ioHub Event Framework has been designed to be highly configurable, ensuring 
that is can be tailored to the needs of a specific use case or experiment paradigm.

This section outlines how ioHub configuration works, what mechanisms are in 
place allowing a user to update configuration settings, and how configuration settings
are validated. There are two ways configuration settings can be specified, 
using configuration files for using configuration dictionaries within the experiment script.

ioHub tries to seperate experiment logic ( the python code that defines how your experimental
paradigm is implemented, how stimuli are read and presented, etc. ) from experiment configuration
( defining the experiment and experiment session metadata, experiment session variable input, 
and the configuration of the device hardware being used by the experiment ). 

By doing so, the experiment scripts will often become much reusable when switching between
device hardware for a given device type. The definition and collection of experiment
and experiment session information becomes more structured, easier to and understand visually,
and also can help to ensure different memebers of a lab are following the same or similar 
process when providing and collecting data about participants and the experiment devices used.
This can help in experiment reproducablity and result validaion if ever needed.

The current implementation state of ioHub is a work in process towards fully 
meeting the above goals and objectives; much more can be done to both improve 
and refine the existing functionailty provide as well as working towards a 
more functional implementation.

This section outlines:

* Areas of configuration within the ioHub Framework.
* Default configuration values and experiment defined confiuration values
* Using configuration files vs. python dictionaries.
* Experiment defined confiuration validation.
* Where to find confiuration setting options, and vailid values for each, within the documentation.


Areas of Configuration
#######################

The ioHub Event Framework supports the configuration of several 
different areas of the functionality. How the ioHub Framework is used defines which of
these areas can be taken advantage of by the experiment.

Configuration Options with ioHubExperimentRuntime Class
========================================================

* Experiment metadata.
* Experiment Session metadata definition, including custom session level variables.
* Device selection and configuration.
* Experiment Resource (condition variable files, images, audio files, vidio files, etc.) location specifiecation.
* Experiment Output File(s) (custom files, ioHub DataStore files, Native Device Data Files, ect) locations.
* Some Experiment and ioHub Process OS configuration     

Other than the ioHub device spcification, and any configuration settings needed for the devices being used, all other
items in the list are optional. By providing all the above information (at a level of detail you can choose),
your experiment logic script will be able to take advantage of the full fucntionality set
provided by the ioHub Framework.


When using the ioHubExperimentRuntime Class, aff configuration details provided are done so using
two configuration files that reside in the same directory as the experiment python script. 
These are descibed in detail later on this page.

Configuration Options with the launchHubProcess Function
=========================================================

* Experiment Code.
* Session Code.
* PsychoPy Monitor Configuration File Name.
* Defice configuration.

When using the launchHubProcess function to interface to the ioHub framework any configuration
information that is provided is done using kwargs to the fucntion, or a 
python dictionary for each device that needs configuration settings updated.

A default set of devices are enabled when the launchHubProcess function is used:

* Display
* Experiment
* Keyboard
* Mouse

Therefore the launchHubProcess can be very useful for quick initial setup of access to the 
ioHub Framework is is completely useable in many cases. However the trade-offs 
(you deside if they are possitive or negative) are:

* Access to all the extended functionality witin the ioHub Framework is significantly reduced 
* When devices are used that *require* a moderate degree of configuration, directly using python dictionaries to do so starts to become combersome and error prone. 
* This approach to using the ioHub Framework effectively voids any of the possible beneifits outlined at the start of this section regarding the speration of experiment logic and configuration.

Default and Custom Provided Configuration Settings
#######################################################

Regardless of which of the two approaches just described are used, all the possible
configuration options are set when the ioHUb Process starts. What can differ is which
are sets using default values and which are set using confiruation options
defined by the experiment designer. the following process is used when setting
configutation options:

#. Default settings are read from default configuration files which exist in the ioHub package directory structure.
#. Any custom settings or values specified by the PsychoPy Process are read. 
#. These two configuration sets are merged, where any settings not provided by the PsychoPy Process are given the default value specified by  the default configuration file in question.

    #. If the configuration group is for an ioHub Device, the combined confiuartion set for the device is validated against a spcification of what thhat device accepts for configuration options, whether it is manditory or not, and what the valid value set or range is for each option.
    #. If the configuration validator finds problems, an error is generated when the experiment starts and the device is not loaded.
    #. If the configuration of the device passes, the device is created and the full set of configuration otpns and values used can be read as a Python dictionary using the device.getConfiguration() method.

#. The configuation settings are used when initializing the ioHub Process and creating the ioHub runtime objects used within the PsychoPy script.


Default Configuration Settings
==================================

All default confiuration settings are specified in configuration files, as mentioned above. 

The default settings for the ioHub Process and DataStore are located in the
'default_config.yaml' file located in the root iohub module directory.

The default settings for each ioHub device are located in a file called 
default_<device_name>.yaml found in the device submodule
directory within the iohub package; where <device_name> is the unqualified class 
name of the defive in all lowercase form.  

For example, the default Mouse device settings are located in::

     psychopy.iohub.devices.mouse.default_mouse.yaml

For the Keyboard::

     psychopy.iohub.devices.mouse.default_keyboard.yaml

For the different Eye Tracker implementations::

    psychopy.iohub.devices.eyetracker.hw.lc_technolgies.eyegaze.default_eyetracker.yaml
    
    psychopy.iohub.devices.eyetracker.hw.smi.iviewx.default_eyetracker.yaml

    psychopy.iohub.devices.eyetracker.hw.sr_research.eyelink.default_eyetracker.yaml

    psychopy.iohub.devices.eyetracker.hw.tobii.default_eyetracker.yaml

etc.

.. note:: The documentation page for each device includes the ioHub default
    settings for each device based on the latest default file settings for that device. 
    This can be used to quickly review the configuartion options available, 
    get a description of each, and see what the default value is.

    It is important to understand that if the default setting for a device 
    configuration option is satisfactory for the experiment being written, there is
    no need to provide it at the experiment confiuration setting level. However doing so
    does not hurt and provides a direct statement of what setting values are being 
    used for the experiment.


Custom Configuration Settings
===================================

Any configuration setting that need to use a non-default value are specified in
one of two ways, depending on whether the launchHubProcess function is used to
create the access point to the ioHub Process, or if the ioHubExperimentRuntime class
is being used to embed the experiment logic within the ioHub Framework.

**When using the launchHubProcess function:**

When the launchHubProcess function  is used, device configuratiions can be 
specified by creating a python dictionary for the device settings being specified.
One dictionary is created for each device that is needed.

.. note:: Remember that, as a convience, the launchHubProcess function will create
    four base device insatnces without the need to specify them as launchHubProcess
    function kwargs. These defaults use the default settings for the device. If 
    a configuration dictionary is provided for a device of the same Classs, then the
    default device that would have been created is created using the provided parameter
    dictionary instead 

Please see the launchHubProcess function documentation for more details.

**When using the ioHubExperimentRuntime class:**

When using the ioHubExperimentRuntime class, all experiment, session, process, 
and device configuation settings are specified in two configuratiion files that
are created in the same directory as the PsychoPy Python script file.

ioHub Configuration Files are defines using a simple subset of the `YAML synax <http://yaml.org/>`_ ,
which is parsed using the `PyYAML <http://pyyaml.org/wiki/PyYAMLDocumentation>`_ package.

The two configuartion files are:

#. experiment_config.yaml 
    * Specifies the experiment and session metadata for the experiment.
    * Defines any custom session variables, which allow custom input fields to be provided in the Session Information Input Dialog at the start of any experiment 
    * Can include experiment resource path information and result data file save locations.
    * Specifies the PsychoPy and ioHub Process OS settings (Windows and Linux only).
#. iohub_config.yaml
    * Specifies the ioHub Process UDP port number to use.
    * Defines the maximum number of events to store in the Global Event Buffer.
    * Specifies the list of ioHub devices to use within the experiment, allong with any configuration settings needed for each device specified.
    * Defines ioHub DataStore parameter settings.

Several of the ioHub examples use the ioHubExperimentRuntime class and two configuration files,
and they provide a good way to gain better insite into how the configuration options can be used.

.. note:: The documentation page for each device includes the ioHub default
    settings for each device based on the latest default file settings for that device. 
    This can be used to quickly review the configuartion options available, 
    get a description of each, and see what the default value is.


Example Configurations 
#######################

In YAML file Format
=====================

An example of a experiment_config.yaml file:

.. literalinclude:: ./example_experiment_config.yaml
    :language: yaml

An example of an iohub_config.yaml file:

.. literalinclude:: ./example_iohub_config.yaml
    :language: yaml

In Python Dictionary Format
---------------------------

The following example python code illustrates how the launchHubProcess function could
be used to to explitied specify the settings for the same device set listed in the
above iohub_config.yaml, but as Python dictionaries directly::

    # create the Display configuration
    display_config=dict(
                        name='display',
                        reporting_unit_type= 'pix',
                        device_number=0,
                        physical_dimensions = dict(
                                            width=500,
                                            height=281,
                                            unit_type='mm'
                                          ),
                        default_eye_distance=dict(
                                    surface_center=550,
                                    unit_type='mm'
                                    ),
                        psychopy_monitor_name= 'default',
                        override_using_psycho_settings=False
                    )

    # create the Keyboard configuration
    keyboard_config=dict(
                        name='keyboard',
                        monitor_event_types= ['KeyboardPressEvent', 'KeyboardReleaseEvent', 'KeyboardCharEvent'],
                        report_auto_repeat_press_events= False,
                        event_buffer_length= 256
                        )

    # create the XInput Gamnepad configuration
    gamepad_config=dict(
                        name='gamepad',
                        device_number=-1,
                        monitor_event_types= ['GamepadStateChangeEvent', 'GamepadDisconnectEvent'],
                        save_events= True,
                        stream_events= True,
                        event_buffer_length= 256,
                        device_timer= {interval:0.005}
                        )
    
    io=psychopy.iohub.launchHubProcess(Display=display_config,Keybaord=keyboard_config,Gamepad=gamepad_config)
    
    # resr of your script .....
    
.. note:: As previously mentioned, the example set provide for the ioHub is an excellent resource
    for further examples of confuration in ioHub.
