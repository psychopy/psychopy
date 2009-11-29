Generating outputs (datafiles)
-------------------------------

There are (or will be - as at version 1.51.00 the log file is generally empty) 3 main forms of output file from PsychoPy: 
   - text data files (one for each :ref:`loop <loops>`)
   - binary data files (as text files but with greater detail)
   - log files (one per experiment)

Text data files (.dlm)
========================
    One tab-delimitted text file is typically output for each loop within the experiment. These are useful for providing a human-readable summary of the responses tabulated by trial type. In such files, each row contains information for a single trial type. The columns then contain different variables; either predetermined (the variables that define the trials, as set in the :ref:`csv file <trialTypes>` for a method of constants experiment) or recorded during the experiment (responses and response times from the keyboard). 
    For variables such as responses where there may have been multiple trials, there is a column giving the mean response, as well as a set of columns providing each of the raw responses. For instance, if responses were being recorded by a :ref:`keyboard` object called `resp`, and there were 5 repeats of the 6 different trial types using a :ref:`method of constants  <trialTypes>`, then the resulting .dlm file would contain 6 data rows (one for each trial type) and would include columns labelled `resp_mean` (the mean response), resp_raw (5 columns providing the individual responses from trials 1-5).
    

Binary data files (.psydat)
===============================
    These files are very similar to the above files, in that they are saved from the loops in the same way, but are a special python-specific format (pickle files). They can be used by python scripts as an easier way to load data for plotting and analysis. They can be loaded using e.g.::

        from psychopy import misc
        thisRun = misc.fromFile('myDat.psydat')
        data = thisRun.data
    
These files are designed to be used by experienced users with previous experience of python and, probably, matplotlib. The contents of the file can be explored with dir(), as any other python object. All should be self-explanatory. Ideally, we should provide a demo script here for fetching and plotting some data feel (free to :ref:`contribute <contribute>`).

Log files (.log)
========================
 
 # Todo