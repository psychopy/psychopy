.. _classroom:

Installing PsychoPy in a classroom (administrators)
======================================================

.. note:

    This document is aimed at network administrators in teaching departments, wanting to install PsychoPy with many identical computers. It is suitable for any version of MS Windows (for macOS other solutions are available).
    

For running PsychoPy in a classroom environment it is probably preferable to have a 'partial' network installation. The PsychoPy library features frequent new releases, including bug fixes and you want to be able to update machines with these new releases. But PsychoPy depends on many other python libraries (over 200Mb in total) that tend not to change so rapidly, or at least not in ways critical to the running of experiments. If you install the whole PsychoPy application on the network then all of this data has to pass backwards and forwards, and starting the app will take even longer than normal.

The basic aim of this document is to get to a state whereby;
    
    - Python and the major dependencies of PsychoPy are installed on the local machine (probably a disk image to be copied across your lab computers)
    - PsychoPy itself (only ~2Mb) is installed in a network location where it can be updated easily by the administrator
    - a file is created in the installation that provides the path to the network drive location
    - Start-Menu shortcuts need to be set to point to the local Python but the remote PsychoPy application launcher

Once this is done, the vast majority of updates can be performed simply by replacing the PsychoPy library on the network drive.

1. Install dependencies locally
-------------------------------------------------

Download the latest version of the Standalone PsychoPy distribution, and run as administrator. This will install a copy of Python and many dependencies to a default location of 
    
    `C:\\Program Files\\PsychoPy2\\`

2. Move the PsychoPy to the network
----------------------------------------------------------

You need a network location that is going to be available, with read-only access, to all users on your machines. You will find all the contents of PsychoPy itself at something like this (version dependent obviously):

    `C:\\Program Files\\PsychoPy2\\Lib\\site-packages\\PsychoPy-1.70.00-py2.6.egg`

Move that entire folder to your network location and call it psychopyLib (or similar, getting rid of the version-specific part of the name). Now the following should be a valid path:

    `<NETWORK_LOC>\\psychopyLib\\psychopy`

3. Update the Python path
-----------------------------------------

The Python installation (in C:\\Program Files\\PsychoPy2) needs to know about the network location. If Python finds a text file with extension `.pth` anywhere on its existing path then it will add to the path any valid paths it finds in the file. So create a text file that has one line in it:

    `<NETWORK_LOC>\\psychopyLib`

You can test if this has worked. Go to `C:\\Program Files\\PsychoPy2` and double-click on python.exe. You should get a Python terminal window come up. Now try:

    >>> import psychopy

If psychopy is not found on the path then there will be an import error. Try adjusting the .pth file, restarting python.exe and importing again.

4. Update the Start Menu
-----------------------------------------

The shortcut in the Windows Start Menu will still be pointing to the local (now non-existent) PsychoPy library. Right-click it to change properties and set the shortcut to point to something like::

    "C:\Program Files\PsychoPy2\pythonw.exe" "<NETWORK_LOC>\psychopyLib\psychopy\app\psychopyApp.py"
    
You probably spotted from this that the PsychoPy app is simply a Python script. You may want to update the file associations too, so that `.psyexp` and `.py` are opened with::

    "C:\Program Files\PsychoPy2\pythonw.exe" "<NETWORK_LOC>\psychopyLib\psychopy\app\psychopyApp.py" "%1"
    
Lastly, to make the shortcut look pretty, you might want to update the icon too. Set the icon's location to::

    "<NETWORK_LOC>\psychopyLib\psychopy\app\Resources\psychopy.ico"

5. Updating to a new version
--------------------------------

Fetch the latest .zip release. Unpack it and replace the contents of `<NETWORK_LOC>\\psychopyLib\\` with the contents of the zip file.
