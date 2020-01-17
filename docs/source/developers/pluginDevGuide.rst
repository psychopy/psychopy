.. _pluginDevGuide:

Extending PsychoPy with Plugins
===============================

Plugins provide a means for developers to extend PsychoPy, adding new features
and customizations without directly modifying the PsychoPy installation. Read
:ref:`usingplugins` for more information about about plugins before proceeding
on this page.

How plugins work
----------------

The plugin system in PsychoPy functions as a dynamic importer, which imports
additional executable code from plugin packages then patches them into an active
PsychoPy session. This is done by calling the ``psychopy.plugins.loadPlugins()``
function and passing the names of the desired plugin modules to it. Once
``loadPlugins()`` returns, imported objects are immediately accessible. Any
changes made to PsychoPy with plugins do not persist across sessions unless
``loadPlugins()`` is called again. If Python is restarted, PsychoPy will return
to its default behaviour. While you can do this using conventional ``import``
statements, the plugin loader also automatically handles patching objects
exported by the plugin into PsychoPy's modules and classes.

To demonstrate why plugins are advantageous over ``import``, let's consider a
case where we want to add support for some display related hardware. This
requires overriding the default behaviour of the
``psychopy.visual.Window.flip()`` method and adding a new class to
`psychopy.hardware` called ``DisplayDriver``. These objects reside in a package
called `psychopy_display` installed alongside PsychoPy. The following two code
snippets yield the same result:

Using ``import`` statements::

    import psychopy
    import psychopy.visual as visual
    import psychopy.hardware as hardware
    import psychopy_display

    visual.Window.flip = psychopy_display.flip
    hardware.DisplayDriver = psychopy_display.DisplayDriver

    win = visual.Window()  # create a window
    hw = hardware.DisplayDriver(win)  # initialize our class

Equivalent to above using a plugin::

    import psychopy
    import psychopy.visual as visual
    import psychopy.hardware as hardware
    plugins.loadPlugins("psychopy_display")

    win = visual.Window()  # create a window
    hw = hardware.DisplayDriver(win)

As we can see, using the plugin does not require the user to manually specify
which attributes to assign the imported objects. The plugin loader knows where
to put objects because the modules defines an ``__extends__`` attribute and does
so automatically. Other than the ``__extends__`` statement, the code in
`psychopy_display` is exactly the same in both cases. While you could have the
module apply patches when imported by doing the assignments from within the
module, the plugin system does some bookkeeping to keep track of what parts of
PsychoPy have been modified, warning the user when multiple plugins attempt
to modify the same attributes. For instance, if another plugin is loaded and
attempts to modify ``psychopy.visual.Window.flip()``, the plugin system will
identify the conflict and inform the user. This safeguards against possible
undefined behaviour arising from the conflict which affects the operation of
previously loaded plugins.

Plugins can contain executable code which could run when loaded. For instance,
a routine to initialize something so the user doesn't have to explicitly.

Plugin packages
---------------

A plugin has a similar structure to Python package, see the official `Packaging
Python Projects` (https://packaging.python.org/tutorials/packaging-projects)
guide for details.

To make PsychoPy plugins discernible from any other package in public
repositories, developers should adhere to the official naming convention. Plugin
names should always be prefixed with `psychopy` with individual words separated
with a `-` or `_` symbol (i.e. `psychopy-quest-procedure`). What you name the
package is up to you, but keep it concise and informative. The `name` argument
of the `setup()` function in `setup.py` file should be set to the name you've
chosen. Furthermore, the package directory or module file the plugin code
resides in should be named the same, but with `_` underscores separating words
(i.e. `psychopy_quest_procedure`). This convention is used to make plugin
packages easier to find once installed locally.

Below is an example of what a package's directory structure should look like:

```TODO```

The `__init__.py` in the sub-directory is the entry point for your plugin code.

The ``__extends__`` statement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The ``__extends__`` module attribute is **required** by all PsychoPy plugins. If
``__extends__`` is not defined in file used as the entry point for plugin
module, it cannot be loaded by ``loadPlugins()``. The plugin loader imports the
module and looks for this attribute to not only identify whether a module is a
plugin, but to determine where to assign objects within PsychoPy. Note that
objects can only be assigned to unbound classes and their methods.

The value of ``__extends__`` is always either a dictionary or `None`. Dictionary
keys are strings specifying the *fully qualified path* of a PsychoPy object
attribute to extend or modify. Target objects can be modules (eg.
`psychopy.visual`), classes (eg. `psychopy.visual.Window`) and their methods,
functions, or variables. Dictionary items are lists of strings specifying the
names of objects to place in the associated namespace. For example, an
``__extends__`` statement may look like this::

    __extends__ = {'psychopy.core': ["MyTimer"],
                   'psychopy.visual': ["MyStimClass", "myFunc"],
                   'psychopy.visual.Window.flip': "flip"}

Where "MyTimer", "MyStimClass", "flip" and "myFunc" are objects defined in the
namespace of the plugin module. When the plugin is loaded, "MyTimer" will be
placed in `psychopy.core`, and "MyStimClass" and "myFunc" in `psychopy.visual`.
The method ``psychopy.visual.Window.flip()`` will be replaced with "flip". Users
can then access these objects as if they were part of the module (eg.
calling ``psychopy.visual.myFunc()`` after loading the plugin).

In a some cases a plugin may not extend any namespaces, but still contains code
to modify PsychoPy. This is the case for patches and code which alters the
Builder interface (eg. add a menu item). If so, the file must still contain a
`__extends__` directive but it may be set to `None` or an empty dictionary.

Optional ``__load()`` and ``__shutdown()`` functions
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some plugins may need to execute code when loaded, or to clean up when PsychoPy
closes. You can indicate which code to run in either of these events by defining
optional ``__load()`` and ``__shutdown()`` functions in the same file
``__extends__`` is defined. If present, the ``__load()`` function is called
before assigning objects specified by ``__extends__`` and ``__shutdown()`` is
called when ``psychopy.core.quit()`` is invoked.

Style recommendations
~~~~~~~~~~~~~~~~~~~~~

Since plugins are not part of PsychoPy, developers are not compelled to
adhere to the official style guide. However, to provide a consistent
experience for users, it is highly recommended that any user facing objects
exported by the plugin do use the official style conventions. See
:ref:`demostyleguide` for more information. For documentation, PsychoPy
standardized on the `NumpyDoc` style for new code.

Creating a plugin example
-------------------------

This example will demonstrate how to create and package a plugin for
distribution. Here we would like to add a new stimulus class and function to
`psychopy.visual` called `MyStim` and `helperFunc`, respectively.

Setting up project files
~~~~~~~~~~~~~~~~~~~~~~~~

The source tree of the plugin resembles a typical Python package. The top-level
project directory is named `psychopy_mystim`, in it we have files `setup.py`,
`README.md`, and `LICENCE`, and module sub-directory named `psychopy_mystim`
with a `__init__.py` file inside it. This sub-directory defines the entry
point for the plugin.

Below is a diagram of what the project directory should look like when viewed
in a file manager:

``example``

Configuring `setup.py`
~~~~~~~~~~~~~~~~~~~~~~
``TODO``

Adding code
~~~~~~~~~~~

The Python file serving as the entry point for your package needs to define an
``__extends__`` statement which indicates which objects need to be placed into
which namespace. For our example, we want to put objects ``MyStim`` and
``helperFunc`` into `psychopy.visual`. Therefore our ``__extends__`` statement
should be placed in the `__init__.py` file in our module sub-directory and
defined as::

    __extends__ = {'psychopy.visual': ["MyStim", "helperFunc"]}

Optionally, we can also define an ``__all__`` statement to handle the case where
we import the plugin module directly (note that PsychoPy plugins must *always*
define ``__extends__`` even if ``__all__`` is present)::

    __all__ = ["MyStim", "helperFunc"]

Now we add our ``import`` statements. ``MyStim`` is a subclass of
``BaseShapeStim`` so we need to import it::

    import psychopy
    from psychopy.visual.shape import BaseShapeStim

You can also add additional import statements to bring in objects from other
files located in the module sub-directory. In our example, ``helperFunc`` is
defined in the file ``tools.py`` and we would like to make it exportable. To do
this, we add add an additional import statement which brings the function into
the module namespace::

    import psychopy
    from psychopy.visual.shape import BaseShapeStim
    from psychopy_mystim.tools import myFunc

We can now define our ``MyStim`` class which may look something like this::

    class MyStim(BaseShapeStim):
        def __init__(*args, **kwargs):
            pass

Packaging and testing
~~~~~~~~~~~~~~~~~~~~~
``TODO``


Plugins as patches
------------------

Plugins can also be used to install and distribute unofficial patches or
hotfixes to quickly fix bugs in current releases of PsychoPy without needing to
manually edit files in your existing PsychoPy installation. This also allows for
fixes to be applied across several installations too.

Note that not all features in PsychoPy can be patched and will require upstream
fixes. In any case make sure you report the bug to the developers!

Example patch
~~~~~~~~~~~~~
``TODO``





