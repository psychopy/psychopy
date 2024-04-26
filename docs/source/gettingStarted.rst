.. _gettingStarted:

Getting Started
===============

As an application, |PsychoPy| has two main views: the :doc:`Builder <builder/index>` view, and the :doc:`Coder <coder/index>` view. It also has a underlying :ref:`api` that you can call directly.

#. :doc:`Builder <builder/index>`. You can generate a wide range of experiments easily from the Builder using its intuitive, graphical user interface (GUI). This might be all you ever need to do. But you can always compile your experiment into a python script for fine-tuning, and this is a quick way for experienced programmers to explore some of PsychoPy's libraries and conventions. **Note: if you are taking a study online we highly advise even experienced coders use Builder view, as the JS version of your experiment will also be generated**

.. figure:: /images/builderApril24.png
  :width: 80%
  :align: center
  :alt: The Builder view

#. :doc:`Coder <coder/index>`. For those comfortable with programming, the Coder view provides a basic code editor with syntax highlighting, code folding, and so on. Importantly, it has its own output window and Demo menu. The demos illustrate how to do specific tasks or use specific features; they are not whole experiments. The :doc:`Coder tutorials <coder/index>` should help get you going, and the :ref:`api` will give you the details.

.. figure:: /images/coderApril24.png
  :width: 80%
  :align: center
  :alt: The Coder view

.. _python : http://www.python.org

The Builder and Coder views are the two main aspects of the |PsychoPy| application. If you've installed the StandAlone version of |PsychoPy| on **MS Windows** then there should be an obvious link to |PsychoPy| in your > Start > Programs. If you installed the StandAlone version on **macOS** then the application is where you put it (!). On these two platforms you can open the Builder and Coder views from the View menu and the default view can be set from the preferences. **On Linux**, you can start |PsychoPy| from a command line, or make a launch icon (which can depend on the desktop and distro). If the |PsychoPy| app is started with flags ----coder (or -c), or ----builder (or -b), then the preferences will be overridden and that view will be created as the app opens.

For experienced python programmers, it's possible to use |PsychoPy| without ever opening the Builder or Coder. Install the |PsychoPy| libraries and dependencies, and use your favorite IDE instead of the Coder.

Builder
------------

When learning a new computer language, `the classic first program <http://en.wikipedia.org/wiki/Hello_world_program>`_ is simply to print or display "Hello world!". Lets do it.

A first program
~~~~~~~~~~~~~~~

Start |PsychoPy|, and be sure to be in the Builder view.

* If you have poked around a bit in the Builder already, be sure to start with a clean slate. To get a new Builder view, type `Ctrl-N` on Windows or Linux, or `Cmd-N` on Mac.
* Click on a Text component and a Text Properties dialog will pop up.

  .. image:: /images/textComponentApril24.png
    :width: 80%
    :align: center

* In the `Text` field, replace the default text with your message. When you run the program, the text you type here will be shown on the screen.
* Click OK (near the bottom of the dialog box). (Properties dialogs have a link to online help---an icon at the bottom, near the OK button.)
* Your text component now resides in a routine called `trial`. You can click on it to view or edit it. (Components, Routines, and other Builder concepts are explained in the :doc:`Builder documentation <builder/index>`.)
* Back in the main Builder, type `Ctrl-R` (Windows, Linux) or `Cmd-R` (Mac), or use the mouse to click the `Run` icon.

.. image:: /images/run32.png

Assuming you typed in "Hello world!", your screen should have looked like this (briefly):

.. image:: /images/helloworld.png
  :width: 80%
  :align: center

If nothing happens or it looks wrong, recheck all the steps above; be sure to start from a new Builder view.

What if you wanted to display your cheerful greeting for longer than the default time?

* Click on your Text component (the existing one, not a new one).
* Edit the `Stop duration (s)` to be `3.2`; times are in seconds.
* Click OK.
* And finally `Run`.

When running an experiment, you can quit by pressing the `escape` key (this can be configured or disabled). You can quit |PsychoPy| from the File menu, or typing `Ctrl-Q` / `Cmd-Q`.

Getting beyond Hello
~~~~~~~~~~~~~~~~~~~~

To do more, you can try things out and see what happens. You may want to consult the :doc:`Builder documentation<builder/index>`. Many people find it helpful to explore the Builder demos, in part to see what is possible, and especially to see how different things are done.

A good way to develop your own first |PsychoPy| experiment is to base it on the Builder demo that seems closest. Copy it, and then adapt it step by step to become more and more like the program you have in mind. Being familiar with the Builder demos can only help this process.

You could stop here, and just use the Builder for creating your experiments. It provides a lot of the key features that people need to run a wide variety of studies. But it does have its limitations. When you want to have more complex designs or features, you'll want to investigate the Coder. As a segue to the Coder, lets start from the Builder, and see how Builder programs work.


Builder-to-coder
---------------------

Whenever you run a Builder experiment, |PsychoPy| will first translate it into python code, and then execute that code.

To get a better feel for what was happening "behind the scenes" in the Builder program above:

* In the Builder, load or recreate your "hello world" program.
* Instead of running the program, explicitly convert it into python: Type `F5`, or click the `Compile` icon:

.. image:: /images/compile_py.png

The view will automatically switch to the Coder, and display the python code. If you then save and run this code, it would look the same as running it directly from the Builder.

It is always possible to go from the Builder to python code in this way. You can then edit that code and run it as a python program. However, you **cannot go from code back to a Builder representation** editing in coder is a one-way street, so, in general, we advise compiling to code is good for understanding what exists but, where possible, make code tweaks in builder itself using code components.

To switch quickly between Builder and Coder views, you can type `Ctrl-L` / `Cmd-L`.

Coder
--------------

Being able to inspect Builder-generated code is nice, but it's possible to write code yourself, directly. With the Coder and various libraries, you can do virtually anything that your computer is capable of doing, using a full-featured modern programming language (python).

For variety, lets say hello to the Spanish-speaking world. |PsychoPy| knows Unicode (UTF-8).

If you are not in the Coder, switch to it now.

* Start a new code document: `Ctrl-N` / `Cmd-N`.
* Type (or copy & paste) the following::

    from psychopy import visual, core

    win = visual.Window()
    msg = visual.TextStim(win, text=u"\u00A1Hola mundo!")

    msg.draw()
    win.flip()
    core.wait(1)
    win.close()

* Save the file (the same way as in Builder).

* Run the script.

Note that the same events happen on-screen with this code version, despite the code being much simpler than the code generated by the Builder. (The Builder actually does more, such as prompt for a subject number.)

**Coder Shell**

The shell provides an interactive python interpreter, which means you can enter commands here to try them out. This provides yet another way to send your salutations to the world. By default, the Coder's output window is shown at the bottom of the Coder window. Click on the Shell tab, and you should see python's interactive prompt, `>>>`::

    PyShell in |PsychoPy| - type some commands!

    Type "help", "copyright", "credits" or "license" for more information.
    >>>

At the prompt, type::

    >>> print(u"\u00A1Hola mundo!")

You can do more complex things, such as type in each line from the Coder example directly into the Shell window, doing so line by line::

    >>> from psychopy import visual, core

and then::

    >>> win = visual.Window()

and so on---watch what happens each line::

    >>> msg = visual.TextStim(win, text=u"\u00A1Hola mundo!")
    >>> msg.draw()
    >>> win.flip()

and so on. This lets you try things out and see what happens line-by-line (which is how python goes through your program).
