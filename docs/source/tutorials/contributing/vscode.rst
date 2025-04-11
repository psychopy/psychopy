:orphan:

.. _contrib_vscode:

Contributing with Microsoft Visual Studio Code
================================================

This guide will walk you through setting up a development environment for PsychoPy in VS Code, a flexible multi-language IDE from Microsoft.

Set up the software
------------------------------------------------

To run PsychoPy via VS Code, you'll need a few things installed:

* `VS Code <https://code.visualstudio.com/download>`_ itself
* `Python 3.10.11 <https://www.python.org/downloads/release/python-31011/>`_ to run PsychoPy
* `Git <https://git-scm.com/downloads>`_ to sync with GitHub

There are also a few VS Code addons which, while you don't necessarily *need*, will make your life easier. Click `here <https://psychopy.org/tutorials/contributing/PsychoPy.code-profile>`_ to download a `VS Code profile <https://code.visualstudio.com/docs/configure/profiles>`_ with all of these installed already, or install as you like from the list below: 

* `Python <https://marketplace.visualstudio.com/items/?itemName=ms-python.python>`_: This adds a graphical interface for managing Python environments and running/debugging Python files
* `GitLens <https://marketplace.visualstudio.com/items/?itemName=eamodio.gitlens>`_: This adds a graphical interface for managing git syncing
* `autoDocstring <https://marketplace.visualstudio.com/items/?itemName=njpwerner.autodocstring>`_: This will pre-populate docstrings on methods and classes, offering a number of different styles (PsychoPy uses numpy-style documentation)

From here it's a matter of personal taste - VS Code has a *huge* library of add ons, everything from `an Excel-like csv viewer <https://marketplace.visualstudio.com/items/?itemName=GrapeCity.gc-excelviewer>`_ to `a panel with cute pets <https://marketplace.visualstudio.com/items/?itemName=tonybaloney.vscode-pets>`_ - so explore and have fun!

Setup a local folder
------------------------------------------------

Once you're happy with your VS Code setup, it's time to get PsychoPy from GitHub and make a "clone" of it on your computer.

#. Create a new, empty folder called "psychopy" in the location you want to sync PsychoPy to
#. Open this folder in VS Code (File -> Open Folder)
#. Open a terminal in VS Code (Terminal -> New Terminal)
#. Run the following commands in terminal to clone the repository to your folder:

   .. code-block::
       
       cd ..
       git clone https://github.com/psychopy/psychopy

#. Run the following commands in a new terminal to add your own `fork of PsychoPy <https://docs.github.com/en/pull-requests/collaborating-with-pull-requests/working-with-forks/fork-a-repo>`_ as the "origin" remote (and set the main repo as the "upstream" remote):
   
   .. code-block::
       
       git remote rename origin upstream
       git remote add origin https://github.com/<your username>/psychopy


Create a virtual environment
------------------------------------------------

While you can run PsychoPy from your system's root Python, it's best to create a virtual environment so that you can install/uninstall packages as you need without affecting other programs. If you're comfortable doing so, you can do this via the terminal, but this tutorial will assume you have the `Python <https://marketplace.visualstudio.com/items/?itemName=ms-python.python>`_ extension installed.

#. Open the "Run and Debug" tab on the sidebar, its icon looks like this:
   
   .. image:: ./vscode_debug_icon.png

#. Under "Environment Managers" click on the + button on the section labelled "venv" (short for "Virtual ENVironment")
#. Select "Custom" and then "Python 3.10" to create a venv from the Python you installed earlier
#. You can name it whatever you like, but it's advisable to call it something specified in the file ".gitignore" so that git doesn't try to sync your personal environment to the PsychoPy repo, such as ".venv310"
#. If you go back to the "Environment Managers -> venv" section there should now be an item for your new venv - if not, try refreshing the panel
#. Click the :octicon:`check` button on this item to set it as the default environment for running Python files
#. Click the :octicon:`copy` button to copy the location of your venv's "python.exe" file to the clipboard
#. Run the following commands in a new terminal to install PsychoPy (as an editable packeg) and all its required packages to your venv:
   
   .. code-block::
       
       <pasted from clipboard> -m pip install -e .

Create a virtual environment
------------------------------------------------

Once you have a virtual environment, you should be able to run PsychoPy! You can do so by opening the file "psychopyApp.py" and pressing the :octicon:`play` button in the top right corner, but it's a good idea to setup a run profile so you can run the app with debugging tools from the "Run and debug" tab.

Go to Run -> Open Configurations to view the JSON file which defines run configurations for this project. Copy this to the "configurations" section to add a configuration for running the PsychoPy app:

.. code-block:: json
    {
        "name": "PsychoPy",
        "type": "debugpy",
        "request": "launch",
        "program": "psychopy/app/psychopyApp.py",
        "console": "integratedTerminal"
    }

You can also add configurations to run PsychoPy with a specific frame open (e.g. only opening Builder, not Coder) with the following:

.. code-block:: json
    {
        "name": "PsychoPy: Builder",
        "type": "debugpy",
        "request": "launch",
        "program": "psychopy/app/psychopyApp.py",
        "console": "integratedTerminal",
        "args": [
            "-b"
        ]
    },
    {
        "name": "PsychoPy: Coder",
        "type": "debugpy",
        "request": "launch",
        "program": "psychopy/app/psychopyApp.py",
        "console": "integratedTerminal",
        "args": [
            "-c"
        ]
    },
    {
        "name": "PsychoPy: Runner",
        "type": "debugpy",
        "request": "launch",
        "program": "psychopy/app/psychopyApp.py",
        "console": "integratedTerminal",
        "args": [
            "-r"
        ]
    }

Once you save this file, you can go to the Run & debug section and choose any of the configurations you just added, then simply click run to start the app from your local code.