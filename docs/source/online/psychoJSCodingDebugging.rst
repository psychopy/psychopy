.. _psychoJSCodingDebugging:
.. role:: darkorange

Troubleshooting Online Studies
==============================

Sometimes experiments might work perfectly locally, when created and run in the PsychoPy application, but the same experiment might not behave as you expect when you try to run them online, through pavlovia.org. While this page cannot hope to address all of the possible issues you may encounter, it should help you understand the different types of errors and help you give more detailed information if you ask for support on the PsychoPy forums.

Getting Started
-----------------------

PsychoPy Builder is your friend
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
1. Check whether the features you are using are supported online via our :ref:`onlineStatus` page.
2. Don’t try to code in PsychoJS directly.
3. Don’t try to edit JavaScript files on Pavlovia directly. Make changes via Builder.
4. Each Builder (psyexp) file should be in its own dedicated local folder, which should not be in an area currently under version control  (e.g.a github project,  Google drive or Onedrive). This folder should only contain subfolders that pertain to the experiment.
5. Upload your files to Gitlab by synchronising using PsychoPy Builder, rather than using Git commands.
6. Code components should be set to Auto translate ("Code Type" > Auto > JS) unless you know why you need to use different code for Python and JavaScript.
7. Code components should normally be moved to the top of their respective routines. Your code is executed in order from left to right (in the flow) and from top to bottom (within each routine).
8. Experiment Settings / Online / Output path should be blank.
9. Resources (spreadsheets, images, etc.) should be in the same folder as the psyexp file or a sub-folder. Resources that are selected via code components should be added via Experiment Settings / Online / Additional Resources (see how to :ref:`configureOnline`) or a Resource Manager Component. See :ref:`handlingOnlineResources` for more information.

Running the latest version of your experiment
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
When you synchronise changes to your experiment, you may need to clear your browser cache  to see those changes online (using Ctrl-F5, Ctrl-Shift-R or equivalent). If this does not work use an incognito browser tab. A participant will not need to do this, so long as they have not already tried a previous version of your experiment.

Developer Tools
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Use Developer Tools (Ctl-Shift-I in Windows/Chrome, Cmd-Opt-J or Cmd-Opt-I in Mac/Chrome, F12 in IE/Edge, Ctrl-Shift-J in Windows/Safari, Ctrl-Opt-J in Mac/Safari) to view errors via the browser console if you aren’t getting sufficient information from PsychoPy. You can also add :code:`print(X)` (which translates to :code:`console.log(X)`; where :code:`X` refers to the name of your variable) to check the value of a variable :code:`X` at a particular point.

:darkorange:`Tutorial` `tutorial_js_console_log <https://gitlab.pavlovia.org/tpronk/tutorial_js_console_log>`_

.. _errorTypes:
Types of Errors
-----------------------
Errors in your experiment can manifest in multiple ways. The easiest way to categorise the different types of error message is based on where they appear.

- `Builder Errors <_builderErrors>`_
   - Python syntax errors
   - Builder runtime errors
   - Synchronisation errors
- `Browser Errors <_browserErrors>`_
   - Launch errors
   - Resource errors
   - Semantic errors
- `Unexpected Behaviour <_unexpected-behaviour>`_

.. _builderErrors:
Python Syntax Errors (seen in Auto-translate code components)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. figure:: /images/syntaxError.png
    :scale: 90%

    A code component used in PsychoPy Builder. In this example, "Code Type" is set to "Auto > JS" meaning python code (on the left) will transpile to JavaScript (on the right). In this example there is a python coding error, which means the transpilation cannot occur.

One of the advantages of using auto translate code components is that the transpiler is continuously checking your code in order to translate it to JavaScript. If you have a syntax error in your Python code, the JavaScript translation will be :code:`/* Syntax Error: Fix Python code */`. If you get this type of error then your Python code probably won’t run locally, and no translated code will be added to the JavaScript version.

.. note:: "Old style" string formatting (using a % operator) works in Python but gives a syntax error in JavaScript but string interpolation (f-strings) is fine.

Synchronisation Errors (seen in the PsychoPy Runner Stdout)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. figure:: /images/runnerSyncError.png
    :scale: 70%

    An example "synchronisation error" as shown in PsychoPy Runner. In this example the experimenter is attempting to synchronise an experiment while logged into a different Pavlovia account in PsychoPy Builder.

Errors that occur here during synchronisation are often related to the connection to the gitlab repository on Pavlovia. The Stdout will contain a number of messages. Focus on errors (not warnings) which appear near the top or bottom of the output that has just been generated. If you need to recreate a new project then you may need to delete the local hidden .git folder to sever the old connection. If the error message is not related to the git connection, this `flow chart <https://i.imgur.com/WRuJV6r.png>`_ might be helpful.

Synchronisation Errors (seen in a pop-up when synchronising)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. figure:: /images/syncError.png
    :scale: 90%

    An example "synchronisation error" as shown in PsychoPy Builder. In this example the experimenter has set the *Allowed keys* of a keyboard component as a variable, which is not yet supported in PsychoJS.

Errors occur here when PsychoPy is unable to create a JavaScript file from your Builder file. They are usually related to your custom code components, but can be caused by unexpected parameters in your other components. These errors will prevent your JavaScript files from being created and therefore stop you making any changes to previous versions you may have successfully synchronised. See :ref:`usingPavlovia` for more information.

.. _browserErrors:
Launch Errors (stuck on "initialising the experiment")
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. figure:: /images/initialising.png
    
    The "initialising the experiment" message shown when launching and experiment in pavlovia.org.

If, when you try to launch your experiment, it is stuck on "initialising the experiment" then Pavlovia has encountered a syntax error in your JavaScript file that wasn't caught by the checks during synchronisation. The most common cause for this error is that you are trying to import a Python library, such as random or numpy, which don’t exist in JavaScript. Use Developer Tools to look for more information.

:darkorange:`Tutorial` `tutorial_js_syntax_error experiment <https://gitlab.pavlovia.org/tpronk/tutorial_js_syntax_error>`_

Resource Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. figure:: /images/networkError.png
    :scale: 70%

    An example "unknown resource" error message as shown in pavlovia.org. In this example the experiment cannot locate an image.

To understand resource errors it is really important to understand :ref:`handlingOnlineResources` - and we recommend you check out this information to understand how to properly load resources in your experiment. This occurs when an additional resource such as a spreadsheet or image file hasn’t been made available to the experiment. This can either occur because the file couldn't be found when requested, or because there was an attempt to use the file without downloading  it first. These errors are often referred to as network errors, but this does not mean that they are caused by general connectivity issues.

:darkorange:`Tutorial` `tutorial_js_network_error experiment <https://gitlab.pavlovia.org/tpronk/tutorial_js_network_error>`_

Semantic Errors
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
.. figure:: /images/referenceError.png
    :scale: 50%

    An example "semantic error" where something is not defined (Typically a variable name).

These errors occur when a variable has not been defined or declared in the JavaScript version of your experiment. There are typically two reasons for this error.

1. You may have used a python library of PsychoPy object that does not exist, and is therefore not defined, in JavaScript. For example if you used :code:`np.average([1, 2, 3])` in a code component, you would get the error message "np is not defined" (to avoid this specific error use :code:`average([1, 2, 3])` - dropping the reference to numpy).
2. To define a variable in simply add something like :code:`X = 1` in the Begin Experiment or Begin Routine tab of an auto translate code component.

Most semantic errors can be solved by searching for the text of the error message on the `discourse forum <discourse.psychopy.org>`_. You can also use the Developer Tools to help identify which command is causing the error.

:darkorange:`Tutorial` `tutorial_js_semantic_error experiment <https://gitlab.pavlovia.org/tpronk/tutorial_js_semantic_error>`_

Unexpected Behaviour
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Sometimes your experiment will run without any error messages but something will be missing or wrong. This can occur if:

1. you try to use a component that doesn’t yet work online
2. you have code components set to Python only.
3. you use a python function that might work subtly differently in python and JavaScript (for example :code:`pop(0)` will remove the first thing from a list in python, but the last thing from a list in Javascript.

If you're using code components, it's useful to think about the positions of your code components and how they are executed relative to your other components. Since **Begin Routine** code tabs are executed at the same time as **set every repeat** component parameters in top to bottom order. Did you set the parameter before or after it was used? If you something to change during a routine, it needs to be in an **Each Frame** code tab or a **set every frame** component parameter.

Getting Help
--------------------
Once you have identified the error message or behaviour you are trying to fix, search the `PsychoPy forum <discourse.psychopy.org>`_ for other threads discussing the same issue, using keywords from your error message or issue. Some threads are marked with a tick before the name to indicate that they contain a solution. You may also find the solution in Wakefield Morys-Carter's `PsychoPy to JS crib sheet <https://docs.google.com/document/d/183xmwDgSbnJZHMGf3yWpieV9Bx8y7fOCm3QKkMOOXFQ/edit?usp=sharing>`_.

If your issue is solved thanks to a solution you found in a thread, we recommend adding a +1 or like reaction to the post that helped you (remember many of those who support our forum are volunteers! so it's useful to show appreciation and indicate to others seeking help which answer was used by others). If a post you create is solved by a suggestion please mark that response with as the "solution".

If you are unable to solve the problem with existing solutions already posted on the forum then either add a post to a thread which refers to the same issue and doesn't have a solution or start a new thread and include a link to the solution you tried or the most similar thread you have come across in your search.

Creating a New Topic on the forum
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Select an appropriate *category*:

- **Online experiments** if you are planning to run your experiment online.
- **Builder** if you are using PsychoPy Builder for a local experiment.
- **Coding** if you are using PsychoPy Coder for a local experiment.
- **Other** if you are having issues that aren't related to a particular experiment.

Give your new topic a useful *title* such as the text of the error message and/or a short clear description of what is going wrong.

Include the *version of PsychoPy* you are using and a usable link to your experiment.

If you have a Browser error near the beginning of your experiment, it is helpful to allow people to try it for themselves. Since Pilot tokens expire, the easiest way to allow others to view your experiment is to set it to RUNNING and allocate it a small number of credits. Add a final routine with a text component that doesn't end (possibly unless you press a key such as =  which isn't typically used). You should also set your experiment not to save incomplete results using the Dashboard entry for your project so no credits are consumed during testing.

Since most of the JavaScript code is generated automatically, either from Builder components or by Auto translations in code components it is most useful to show screen shots from Builder (the flow and the relevant routine, plus the contents of the component with the issue). If the issue is with an Auto code component, then you should paste the contents of the Python side as preformatted text, as well as showing the screenshot. Only paste JavaScript from Both and JS only code components to clarify that these have been manually edited. 

What next?
--------------------

We will try to give as much support as possible for free in the public space. However if you are still stuck we can offer paid consultancy options to help debug. You can contact our team directly  at consultancy@opensciencetools.org. Consultancy is part of our sustainable model for Open Source Tools and allows us to keep creating free and accessible tools (see :ref:`overview` and read more on `Open Science Tools <https://opensciencetools.org/>`_). Our Science team will be happy to help via one-to-one technical support hours or larger consultancy projects.