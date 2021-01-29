.. _outputs:

Data outputs
====================================

There are a number of different forms of output that PsychoPy can generate, depending on the study and your preferred analysis software. Multiple file types can be output from a single experiment (e.g. :ref:`excelFile` for a quick browse, :ref:`logFile` to check for error messages and :ref:`psydatFile` for detailed analysis)

.. _logFile:

Log file
-----------
Log files are actually rather difficult to use for data analysis but provide a chronological record of everything that happened during your study. The level of content in them depends on you. See :ref:`codeLogging` for further information.


.. _psydatFile:

PsychoPy data file (.psydat)
------------------------------------
This is actually a :class:`~psychopy.data.TrialHandler` or :class:`~psychopy.data.StairHandler` object that has been saved to disk with the python `cPickle <http://docs.python.org/library/pickle.html#module-cPickle>`_ module.

.psydat files can be useful for retrieving data that you forgot to explicitly tell PsychoPy to save. They can also be more directly used by experienced users with previous experience of python and, probably, matplotlib. The contents of the file can be explored with dir(), as any other python object.

.psydat files are ideal for batch analysis with a python script and plotting via `matplotlib`. They contain more information than the Excel or csv data files, and can even be used to (re)create those files.

Of particular interest might be the following attributes and methods of the Handler:
    :entries: a list of dictionaries. Each entry/dictionary in the list represents a single trial's (a single routine 'run'/iteration) data.
    :saveAsPickle(): a method for saving all of the entries' data in a Python pickle file
    :saveAsWideText(): a method for saving all of the entrie's data in a .csv file.

If you just want to recover data or first wish to try things out in a familiar format you can put all of the data in a .csv file, very similar to the .csv files that are produced by default when running PsychoPy experiments. The following script assumes you're using a command-line interface (e. g. Terminal on Mac, or the Command Prompt on Windows) where you've opened up a Python shell, and that you have installed PsychoPy as a Python package::

    # import PsychoPy function for loading Pickle/JSON data
    from psychopy.misc import fromFile
    # (replace with the file path to your .psydat file)
    fpath = '/Users/my_user/myexperiments/myexperiment/participant_expname_date.psydat'
    # load in the data
    psydata = fromFile(fpath)
    # (replace with the file path to where you want the resulting .csv
    # to be saved)
    save_path = '/Users/my_user/Desktop/test_out.csv'
    # save the data as a .csv file, ie separating the values with a
    # comma. 'CSV' simply means 'comma-separated values'
    psydata.saveAsWideText(save_path, delim=',')

To get started using the data directly in Python, you can try opening a psydat file and printing all its entries::

    from psychopy.misc import fromFile
    # (replace with the file path to your .psydat file)
    fpath = 'path/to/file.psydat'
    psydata = fromFile(fpath)
    for entry in psydata.entries:
        print(entry)

Ideally, we should provide a demo script here for fetching and plotting some data (feel free to :ref:`contribute <contribute>`).

.. _longWide:

Long-wide data file
-----------------------

This form of data file is the default data output from Builder experiments as of v1.74.00. Rather than summarising data in a spreadsheet where one row represents all the data from a single condition (as in the summarised data format), in long-wide data files the data is not collapsed by condition, but written chronologically with one row representing one trial (hence it is typically longer than summarised data files). One column in this format is used for every single piece of information available in the experiment, even where that information might be considered redundant (hence the format is also 'wide').

Although these data files might not be quite as easy to read quickly by the experimenter, they are ideal for import and analysis under packages such as R, SPSS or Matlab.

.. _excelFile:

Excel data file
--------------------

Excel 2007 files (.xlsx) are a useful and flexible way to output data as a spreadsheet. The file format is open and supported by nearly all spreadsheet applications (including older versions of Excel and also OpenOffice). N.B. because .xlsx files are widely supported, the older Excel file format (.xls) is not likely to be supported by PsychoPy unless a user contributes the code to the project.

Data from PsychoPy are output as a table, with a header row. Each row represents one condition (trial type) as given to the :class:`~psychopy.data.TrialHandler`. Each column represents a different type of data as given in the header. For some data, where there are multiple columns for a single entry in the header. This indicates multiple trials. For example, with a standard data file in which response time has been collected as 'rt' there will be a heading `rt_raw` with several columns, one for each trial that occurred for the various trial types, and also an `rt_mean` heading with just a single column giving the mean reaction time for each condition.

If you're creating experiments by writing scripts then you can specify the sheet name as well as file name for Excel file outputs. This way you can store multiple sessions for a single subject (use the subject as the filename and a date-stamp as the sheetname) or a single file for multiple subjects (give the experiment name as the filename and the participant as the sheetname).

Builder experiments use the participant name as the file name and then create a sheet in the Excel file for each loop of the experiment. e.g. you could have a set of practice trials in a loop, followed by a set of main trials, and these would each receive their own sheet in the data file.

.. _textFile:

Delimited text files (.csv, .tsv, .txt)
-------------------------------------------------
For maximum compatibility, especially for legacy analysis software, you can choose to output your data as a delimited text file. Typically this would be comma-separated values (.csv file) or tab-delimited (.tsv file). The format of those files is exactly the same as the Excel file, but is limited by the file format to a single sheet.
