.. _appFromScript:

Building an application from your script
==============================================

A lot of people ask how they can build a standalone application from their Python script. Usually this is because they have a collaborator and want to just send them the experiment.

In general this is not advisable - the resulting bundle of files (single file on macOS) will be on the order of 100Mb and will not provide the end user with any of the options that they might need to control the task (for example, Monitor Center won't be provided so they can't to calibrate their monitor). A better approach in general is to get your collaborator to install the Standalone PsychoPy on their own machine, open your script and press run. (You don't send a copy of Microsoft Word when you send someone a document - you expect the reader to install it themself and open the document).

Nonetheless, it is technically possible to create exe files on Windows, and Ricky Savjani (savjani at bcm.edu) has kindly provided the following instructions for how to do it. A similar process might be possible on macOS using py2app - if you've done that then feel free to contribute the necessary script or instructions.


Using py2exe to build an executable
-----------------------------------------

Instructions:

   #. Download and install py2exe (http://www.py2exe.org/)
   #. Develop your PsychoPy script as normal
   #. Copy this setup.py file into the same directory as your script
   #. Change the Name of progName variable in this file to the Name of your desired executable program name
   #. Use cmd (or bash, terminal, etc.) and run the following in the directory of your the two files:
           python setup.py py2exe
   #. Open the 'dist' directory and run your executable


A example setup.py script::

    #   Created 8-09-2011
    #   Ricky Savjani
    #   (savjani at bcm.edu)
    
    #import necessary packages
    from distutils.core import setup
    import os, matplotlib
    import py2exe
    
    #the name of your .exe file
    progName = 'MultipleSchizophrenia.py'
    
    #Initialize Holder Files
    preference_files = []
    app_files = []
    my_data_files=matplotlib.get_py2exe_datafiles()
    
    #define which files you want to copy for data_files 
    for files in os.listdir('C:\\Program Files\\PsychoPy2\\Lib\\site-packages\\PsychoPy-1.65.00-py2.6.egg\\psychopy\\preferences\\'):
        f1 = 'C:\\Program Files\\PsychoPy2\\Lib\\site-packages\\PsychoPy-1.65.00-py2.6.egg\\psychopy\\preferences\\' + files
        preference_files.append(f1)
    
    #if you might need to import the app files
    #for files in os.listdir('C:\\Program Files\\PsychoPy2\\Lib\\site-packages\\PsychoPy-1.65.00-py2.6.egg\\psychopy\\app\\'):
    #    f1 = 'C:\\Program Files\\PsychoPy2\\Lib\\site-packages\\PsychoPy-1.65.00-py2.6.egg\\psychopy\\app\\' + files
    #    app_files.append(f1)
    
    #all_files = [("psychopy\\preferences", preference_files),("psychopy\\app", app_files), my_data_files[0]]
    
    #combine the files
    all_files = [("psychopy\\preferences", preference_files), my_data_files[0]]
    
    #define the setup
    setup(
                    console=[progName],
                    data_files = all_files,
                    options = {
                        "py2exe":{
                            "skip_archive": True,
                            "optimize": 2
                        }
                    }
    )
