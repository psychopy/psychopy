.. _cedrusButtonBox:

Cedrus Button Box Component
---------------------------------

This component allows you to connect to a Cedrus Button Box to collect key presses.

Before using your Cedrus response box make sure to install the `required drivers <https://cedrus.com/support/rbx30/tn1042_install_rbx30_win.htm>`_. From there, your response box should plug straight into your USB port! 

Properties
~~~~~~~~~~~~

Name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).

Start :
    The time that the button box is first read. See :ref:`startStop` for details.

Stop :
    Governs the duration for which the button box is first read. See :ref:`startStop` for details.

Force end of Routine : true/false
    If this is checked, the first response will end the routine.

Data
====
What information to save, how to lay it out and when to save it.

Allowed keys : None, or an integer, list, or tuple of integers 0-7
    This field lets you specify which buttons (None, or some or all of 0 through 7) to listen to.

Store : (choice of: first, last, all, nothing)
    Which button events to save in the data file. Events and the response times are saved, with RT being recorded by the button box (not by |PsychoPy|).

Store correct : true/false
    If selected, a correctness value will be saved in the data file, based on a match with the given correct answer.

Discard previous : true/false
    If selected, any previous responses will be ignored (typically this is what you want).

Hardware
========
Parameters for controlling hardware.

Device number: integer
    This is only needed if you have multiple Cedrus devices connected and you need to specify which to use.

Use box timer : true/false
    Set this to True to use the button box timer for timing information (may give better time resolution)

Data output
~~~~~~~~~~~~

buttonBox.keys : A list of keys that were pressed (e.g. 0, 1, 2 ...)

buttonBox.rt : A list of response times for each keypress


Special use cases
~~~~~~~~~~~~~~~~~~~~~

If you want to detect both key presses and key lifts from your cedrus response box, at the moment you will need to use custom code. Add a code component to your Routine and in the Begin Experiment use:

.. code-block::
    
    import pyxid2 as pyxid

    # get a list of all attached XID devices
    devices = pyxid.get_xid_devices()

    dev = devices[0] # get the first device to use


Then in the Each Frame tab use:

.. code-block::
    
    dev.poll_for_response()
    if dev.response_queue_size() > 0:
        response = dev.get_next_response()
        print(response)


The printed response will return if the key is being pressed (i.e. a key down event) or not (i.e. a key up event):

.. code-block::

    {'port': 0, 'key': 0, 'pressed': True, 'time': 953}
    {'port': 0, 'key': 0, 'pressed': False, 'time': 1298}
    {'port': 0, 'key': 0, 'pressed': True, 'time': 2051}
    {'port': 0, 'key': 0, 'pressed': False, 'time': 3140}


.. seealso::

	API reference for :class:`~psychopy.hardware.iolab`
