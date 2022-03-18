.. _psychoJSCodingDebugging:
==============================
Troubleshooting Online Studies
==============================

Experiments rarely work online the first time you try them, even if they work perfectly locally. While this page cannot hope to address all of the possible issues you may encounter, it should help you understand the different types of errors and help you give more detailed and useful information if you ask for support on the PsychoPy forums.

Getting Started
-----------------------

PsychoPy Builder is your friend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Don’t try to code in PsychoJS directly.
2. Don’t try to edit JavaScript files on Pavlovia directly. Make changes via Builder.
3. Each Builder (psyexp) file should be in its own dedicated local folder, which should not be on a cloud drive (e.g. Google drive or Onedrive). This folder should only contain subfolders that pertain to the experiment.
4. Upload your files to Gitlab by synchronising using PsychoPy Builder, rather than using Git commands.
5. Code components should be set to Auto translate unless you know why you need to use different code for Python and JavaScript. All complex custom code should be in code components rather than in the parameters of other components.
6. Code components should normally be moved to the top of their respective routines. Your code is executed in order from left to right (in the flow) and from top to bottom (within each routine).
7. Experiment Settings / Online / Output path should be blank.
8. Resources (spreadsheets, images, etc.) should be in the same folder as the psyexp file or a sub-folder. Resources that are selected via code components should be added via Experiment Settings / Online / Additional Resources or a Resource Manager Component. See :ref:`handlingOnlineResources` for more information.
9. Check whether the features you are using are supported online via our :ref:`onlineStatus` page.

Running the latest version
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When you synchronise changes to your experiment, you will only see those changes online if you clear the cache (using Ctrl-F5, Ctrl-Shift-R or equivalent). If this does not work, for example because you have made a change to a spreadsheet rather than the experiment file, use an incognito browser tab. A participant will not need to do this, so long as they have not already tried a previous version of your experiment. 

Developer Tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Use Developer Tools (Ctl-Shift-I in Windows/Chrome, Cmd-Opt-J or Cmd-Opt-I in Mac/Chrome, F12 in IE/Edge, Ctrl-Shift-J in Windows/Safari, Ctrl-Opt-J in Mac/Safari) to view errors via the browser console if you aren’t getting sufficient information from PsychoPy. You can also add print(var) (which translates to console.log(var); ) to check the value of a variable var at a particular point. N.B. If you need to stop your participants viewing trial variables you may be loading from Excel, add log4javascript.setEnabled(false); to a JavaScript code component. This will prevent cheating on experiments with a performance based reward.
:darkorange:`Tutorial` `tutorial_js_console_log <https://gitlab.pavlovia.org/tpronk/tutorial_js_console_log>`_

.. _errorTypes:
Types of Errors
-----------------------
Errors in you experiment can manifest in multiple ways. The easiest way to categorise the different types of error message is based on where they appear.

- `Builder Errors <_builderErrors>`_
  - Python syntax errors
  - Builder runtime errors
  - Synchronisation errors
- `Browser Errors <_browserErrors>`_
  - Launch errors
  - Resource errors
  - Semantic errors
- `Unexpected behaviour`_

.. _builderErrors:
Python Syntax Errors (seen in Auto-translate code components)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. image:: /images/syntaxError.png
|One of the advantages of using auto translate code components is that the transpiler is continuously checking your code in order to translate it to JavaScript. If you have a syntax error in your Python code, the JavaScript translation will be /* Syntax Error: Fix Python code */. If you get this type of error then your Python code probably won’t run locally, and no translated code will be added to the JavaScript version. 
|N.B. "Old style" string formatting (using a % operator) works in Python but gives a syntax error in JavaScript but string interpolation (f-strings) is fine.

Builder Runtime Errors (seen in the PsychoPy Runner Stdout)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Errors that occur here will usually also prevent your experiment from synchronising your experiment with Pavlovia. The Stdout will contain a number of messages. Focus on errors (not warnings) which appear near the top or bottom of the output that has just been generated.

Synchronisation Errors (seen in a pop-up when synchronising)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Errors occur here when PsychoPy is unable to create a JavaScript file from your Builder file. They are usually related to your custom code components, but can be caused by unexpected parameters in your other components. These errors will prevent your JavaScript files from being created and therefore stop you making any changes to previous versions you may have successfully synchronised.
|See :ref:`usingPavlovia` for more information.

.. _browserErrors:
Launch Errors (stuck on "initialising the experiment")
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
If, when you try to launch your experiment, it is stuck on "initialising the experiment" then Pavlovia has encountered a syntax error in your JavaScript file that wasn't caught by the checks during synchronisation. The most common cause for this error is that you are trying to import a Python library, such as random or numpy, which don’t exist in JavaScript. Use Developer Tools to look for more information.

:darkorange:`Tutorial` `tutorial_js_syntax_error experiment <https://gitlab.pavlovia.org/tpronk/tutorial_js_syntax_error>`_

Resource Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. image:: /images/networkError.png
|This occurs when an additional resource such as a spreadsheet or image file hasn’t been made available to the experiment. This can either occur because the file couldn't be found when requested, or because there was an attempt to use the file without downloading  it first. These errors are often referred to as network errors, but this does not mean that they are caused by general connectivity issues.  See :ref:`handlingOnlineResources` for more information.
|:darkorange:`Tutorial` `tutorial_js_network_error experiment <https://gitlab.pavlovia.org/tpronk/tutorial_js_network_error>`_

Semantic Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. image:: /images/referenceError.png
|Well done! You have successfully synchronised your experiment and launched it online. These errors can often be solved by searching for the text of the error message on the discourse forum. You can also use the Developer Tools to help identify which command is causing the error.
|:darkorange:`Tutorial` `tutorial_js_semantic_error experiment <https://gitlab.pavlovia.org/tpronk/tutorial_js_semantic_error>`_

Unexpected Behaviour
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sometimes your experiment will run without any error messages but something will be missing or wrong. This can occur if you try to use a component that doesn’t yet work online or have code components set to Python only. There can also be issues caused by colours, sizes and units which might prevent something being seen because it is too small, too big, or the same colour as the background. The positions of your code components are also important here, since **Begin Routine** code tabs are executed at the same time as **set every repeat** component parameters in top to bottom order. Did you set the parameter before or after it was used? If you something to change during a routine, it needs to be in an **Each Frame** code tab or a **set every frame** component parameter. 

Getting Help
--------------------
Once you have identified the error message or behaviour you are trying to fix, search the PsychoPy forums for other threads discussing the same issue, using keywords from your error message or issue. Some threads are marked with a tick before the name to indicate that they contain a solution. You may also find the solution in Wakefield Morys-Carter's `PsychoPy to JS crib sheet <https://docs.google.com/document/d/183xmwDgSbnJZHMGf3yWpieV9Bx8y7fOCm3QKkMOOXFQ/edit?usp=sharing>`_.

If your issue is solved thanks to a solution you found in a thread that was already marked with a solution, I would recommend adding a +1 or like reaction to the post that helped you, but not actually posting.

If your issue is solved thanks to a solution you found in a thread that has not yet been marked with a solution, I would recommend adding a +1 or like reaction to the post that helped you, and also posting to the thread to tell other people which post helped you.

If you are unable to solve the problem with existing solutions already posted on the forum then either:

Add a post to a thread which refers to the same issue and doesn't have a solution.
Start a new thread and include a link to the solution you tried or the most similar thread you have come across in your search.

Please do not add to threads that already have a marked solution.

Creating a New Topic on the forum
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Select an appropriate category:
|**Online experiments** if you are planning to run your experiment online.
|**Builder** if you are using PsychoPy Builder for a local experiment.
|**Coding** if you are using PsychoPy Coder for a local experiment.
|**Other** if you are having issues that aren't related to a particular experiment.

Give your new topic a useful title such as the text of the error message and/or a short clear description of what is going wrong.

Include the version of PsychoPy you are using and a usable link to your experiment. If your link ends on /html then I would recommend deleting the local git and html folders and then recreating a new online experiment with a blank output path.

If you have a Browser error near the beginning of your experiment, it is helpful to allow people to try it for themselves. Since Pilot tokens expire, the easiest way to allow others to view your experiment is to set it to RUNNING and allocate it a small number of credits. Add a final routine with a text component that doesn't end (possibly unless you press a key such as =  which isn't typically used). You should also set your experiment not to save incomplete results using the Dashboard entry for your project so no credits are consumed during testing.

Since most of the JavaScript code is generated automatically, either from Builder components or by Auto translations in code components it is most useful to show screen shots from Builder (the flow and the relevant routine, plus the contents of the component with the issue). If the issue is with an Auto code component, then you should paste the contents of the Python side as preformatted text, as well as showing the screenshot. Only paste JavaScript from Both and JS only code components to clarify that these have been manually edited. 

What next?
--------------------
If you solve the issue that's to a solution or suggestion posted on the forum, please mark the most relevant post as the solution. If you found the solution elsewhere, then please add a post saying how you solved the issue and mark that as the solution.

If you are still stuck, feel free to reach out to Open Science Tools at consultancy@opensciencetools.org. Our Science team will be happy to help via one-to-one technical support hours or larger consultancy projects.