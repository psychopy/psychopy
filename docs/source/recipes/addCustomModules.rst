.. _addModules:

Adding external modules to Standalone PsychoPy
================================================================

You might find that you want to add some additional Python module/package to your Standalone version of PsychoPy. To do this you need to:

    * download a copy of the package (make sure it's for Python 2.7 on your particular platform)
    * unzip/open it into a folder
    * add that folder to the path of PsychoPy by one of the methods below

Avoid adding the entire path (e.g. the site-packages folder) of separate installation of Python, because that may contain conflicting copies of modules that PsychoPy is also providing.

Using preferences
--------------------------

As of version 1.70.00 you can do this using the PsychoPy preferences/general. There you will find a preference for :ref:`paths<generalSettings>` which can be set to a list of strings e.g. `['/Users/jwp/code', '~/code/thirdParty']`

These only get added to the Python path when you import psychopy (or one of the psychopy packages) in your script.


Adding a .pth file
--------------------------

An alternative is to add a file into the site-packages folder of your application. This file should be pure text and have the extension .pth to indicate to Python that it adds to the path.

On win32 the site-packages folder will be something like:

    C:/Program Files/PsychoPy2/lib/site-packages
    
On macOS you need to right-click the application icon, select 'Show Package Contents' and then navigate down to Contents/Resources/lib/pythonX.X. Put your .pth file here, next to the various libraries.

The advantage of this method is that you don't need to do the import psychopy step. The downside is that when you update PsychoPy to a new major release you'll need to repeat this step (patch updates won't affect it though).
