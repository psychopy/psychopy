.. _counterbalanceroutine:

-------------------------------
Counterbalance Routine
-------------------------------

The counterbalance standalone routine is available to use locally and online. This component allows you to automatically assign participants to groups based on defined number of groups and how many participants you want per group (slots). You can find the component in the "Custom" section of Builder. Once you add the component, do remember to select "Insert Routine" > name of your counterbalance routine and insert it into your flow!

.. image:: /images/counterbalance-standalone.png
    :width: 50%
    :alt: A screenshot of the counterbalance standalone routine once it has been inserted on the PsychoPy Builder flow. The "Basic" tab is open and it has the settings "Name" = counterbalance, "Num.groups" = 2, "Slots per group" = 10, "Num. repeats" = 1, "End experiment on depletion" = True (checkbox). 

Categories:
    Custom
Works in:
    PsychoPy, PsychoJS


Parameters
-------------------------------

Basic
===============================

The required attributes of the stimulus, controlling its basic function and behaviour


.. _counterbalanceroutine-name:
Name
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
.. _counterbalanceroutine-specMode:
Groups from...
    Specify groups using an Excel file (for fine tuned control), specify as a variable name, or specify a number of groups to create equally likely groups with a uniform cap.
    
    Options:
    
    * Num. groups: Specify the number of groups and what their caps are. However, this cap is the same as for every group. The groups and caps you use here are only *reflected for local use*. For **Pavlovia**, you would need to set the number of groups and their caps via Shelf. Click `here <https://www.psychopy.org/online/shelf.html#counterbalanceshelf>`_ for an example on how to do that.
    
    * Conditions file (local only): Allows maximum flexibility in setting up groups. By using an excel spreadsheet, the probability of each group occuring, slots per group and any other additional parameters can be speficied. *Note: This is currently not supported for online studies*

    * Variable (local only): Similar to "Conditions file", but using a variable name rather than a file name (the variable should contain the same kind of information as would come from reading a conditions file via e.g. `pandas.read_csv <https://pandas.pydata.org/docs/reference/api/pandas.read_csv.html>_`)
    
.. _counterbalanceroutine-conditionsFile:
Conditions (*if :ref:`_counterbalanceroutine-specMode` is "Conditions file"*)
    Name of a file specifying the parameters for each group (.csv, .xlsx, or .pkl). Browse to select a file. Right-click to preview file contents, or create a new file.
    
.. _counterbalanceroutine-nGroups:
Num. groups (*if :ref:`_counterbalanceroutine-specMode` is "Num. groups"*)
    Number of groups to use.
    
.. _counterbalanceroutine-nSlots:
Slots per group (*if :ref:`_counterbalanceroutine-specMode` is "Num. groups"*)
    Max number of participants in each group for each repeat.
    
.. _counterbalanceroutine-nReps:
Num. repeats (*if :ref:`_counterbalanceroutine-specMode` is "Num. groups"*)
    How many times to run slots down to depletion?
    
.. _counterbalanceroutine-endExperimentOnDepletion:
End experiment on depletion
    When all slots and repetitions are depleted, should the experiment end or continue with .finished on this Routine as True?
    
.. _counterbalanceroutine-conditionsVariable:
Conditions (*if :ref:`_counterbalanceroutine-specMode` is "Variable"*)
    Name of a variable specifying the parameters for each group. Should be a list of dicts, like the output of data.conditionsFromFile
    
Data
===============================

What information about this Component should be saved?


.. _counterbalanceroutine-saveData:
Save data
    Save chosen group and associated params this repeat to the data file
    
.. _counterbalanceroutine-saveRemaining:
Save remaining cap
    Save the remaining cap for the chosen group this repeat to the data file
    
Testing
===============================

Tools for testing, debugging and checking the performance of this Component.


.. _counterbalanceroutine-disabled:
Disable Routine
    Disable this Routine
    