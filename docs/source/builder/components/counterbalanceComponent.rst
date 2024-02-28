.. _counterbalanceComponent:

Counterbalance component
-------------------------------

Parameters
~~~~~~~~~~~~

Basic
====================

Name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
Groups from... : Specify how many groups you want in your experiment
    Choosing from ``Num. groups`` allows you to specify the number of groups and what their caps are. However, this cap is the same as for every group.

    Choosing from ``Condition file`` allows maximum flexibility in setting up groups. By using an excel spreadsheet, the probability of each group occuring, cap per group and any other additional parameters can be speficied.

If finished... : The behaviour once counterbalancing is complete.
    ``Raise error`` would present an error message at the beginning of the task when additional participants try to run the task and they won't be allowed to start the task.

    Once the cap for any group has been reached, ``Reset participant caps`` would allow continuous testing as the cap will return to the original value.

    When counterbalancing is complete, the attribute ``counterbal.finished`` will be ``True``. An error message would also be presented at the start of the task when using ``Just set as finished`` but researchers can set specific behaviour within the task such as presenting a specific message within the task or redirecting participants to another link.


Data
====================
Save data 
    Save the group and associated parameters to the csv output

Save remaining cap 
    Save how many more participants are left to be tested for the group that was selected.


Example
=======
Click here for an example on how to use the Counterbalance Routine.