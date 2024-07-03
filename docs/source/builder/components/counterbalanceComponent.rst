.. _counterbalanceStandaloneRoutine:

Counterbalance Standalone Routine
-------------------------------

**Available from PsychoPy version 2024.1.0**

The counterbalance standalone routine is available to use locally and online.

Parameters
~~~~~~~~~~~~

Basic
====================

Name : string
    Everything in a |PsychoPy| experiment needs a unique name. The name should contain only letters, numbers and underscores (no punctuation marks or spaces).
    
Groups from... : Specify how many groups you want in your experiment
    Choosing from ``Num. groups`` allows you to specify the number of groups and what their caps are. However, this cap is the same as for every group. The groups and caps you use here are only *reflected for local use*. For **Pavlovia**, you would need to set the number of groups and their caps via Shelf. Click `here <https://www.psychopy.org/online/shelf.html#counterbalanceshelf>`_ for an example on how to that.

    Choosing from ``Condition file`` allows maximum flexibility in setting up groups. By using an excel spreadsheet, the probability of each group occuring, slots per group and any other additional parameters can be speficied. *Note: This is currently not support for online studies*

Num.repeats : integer
    How many times you want the sampling to repeat. For example, if you put 2, the experiment will finish collecting all the required participant based on the counterbalance groups and then repeat the same procedure the second time.   

End experiment on depletion : boolean
    If checked, this ends the experiment when all participants have filled all the counterbalance groups.


Data
====================
Save data 
    Save the group and associated parameters to the csv output

Save remaining cap 
    Save how many more participants are left to be tested for the group that was selected.
