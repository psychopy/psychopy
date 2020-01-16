.. _pluginGuide:

Using Plugins to Extend PsychoPy
================================

Plugins are packages which can be loaded to extend core PsychoPy, allowing
third-party developers to add features and customizations.

PsychoPy's plugin system allows for modifications to the coder API by taking
advantage of Python's flexibility. A plugin can add new objects to the namespace
(eg. `psychopy.visual`) or manipulate the code (eg. monkey patching) of an
existing module.

Why use plugins?
----------------

One may consider using plugins if they wish to distribute code which cannot be
contributed to the main project. Reasons for this may include:

* **Niche use**, not many people use the feature and will add bloat to
  PsychoPy which increases workload when testing and packaging.
* Uses a **GPL incompatible license or contains proprietary** code. This allows
  users to distribute code with any licence they chose and permits compliance
  to non-disclosure agreements for companies.
* **Requires special or uncommon configurations** to use (software or hardware).
  This includes features which are limited to specific operating systems, or
  requires hardware which the PsychoPy dev team does not have regular access to.
* **Under heavy development** where PsychoPy's release cycle is inadequate to
  keep up with changes and bug fixes. Furthermore, the code may not be mature
  enough for inclusion with core PsychoPy. Plugins provide an excellent way of
  field testing features before contributing it to the main project.
* **Contains changes that can possibly break PsychoPy** which can accidentally
  affect existing experiments. If something breaks, users can simply disable the
  plugin.
* **Cannot be maintained long-term** by the PsychoPy developers.
* **Patches or hotfixes** to customize or fix bugs in the installed version of
  PsychoPy without needing to edit the code directly, or wait for PsychoPy
  core developers to apply the changes. Patches can easily be applied across
  entire sites using the standard Python packaging system.

Caveats
-------

While plugins are useful, there are some issues and limitations associated with
them. Here are a few examples of issues one may encounter when using plugins:

* Since plugins are loaded dynamically, definitions and docstrings associated
  with objects exported by them will not be readily accessible to IDEs.
  Plugin developers should consider generating documentation pages (eg. with
  Sphinx) and putting them somewhere easily accessible on the internet. At the
  very least, put the source code somewhere accessible and easy to access.
* Namespace conflicts may arise if multiple plugins attempt to create objects
  using the same name. In most cases, the previous object will be reassigned to
  the newer one. Care must be taken to ensure that namespace conflicts do not
  happen by ensuring names are unique, however this becomes more difficult as
  the number of available plugins grows.

Where can I find plugins?
-------------------------

Plugins are essentially Python packages and can be distributed, installed, and
used like any other Python library. PsychoPy plugin packages can be uploaded to
The Python Package Index (PyPI) and installed using `pip`. You can also
distribute and download plugins as ZIP archives. The names of plugins should
follow a convention specified in the `Plugin packages` section below.

**WARNING!** Ensure that your are downloading and installing plugins from
reputable and legitimate sources as they may contain malware that can seriously
harm your computer! Plugins usually consist of text files containing Python
source code executed by the interpreter, this may not be recognizable as a threat
to anti-virus scanners.

Loading plugins
---------------

A plugin can be loaded by calling the `psychopy.plugins.loadPlugins()`
function. The names of the plugins to load are provided as a list of strings.
Plugins will be loaded in the order they appear in the list. Note that a plugin
can override the effects of other plugins loaded before it.

Calling `loadPlugins()` should happen *AFTER* importing `psychopy` and preferably
after all other `import` statements for PsychoPy modules.

``TODO - Provide examples of this``

Plugin packages
---------------

A plugin has a similar structure to Python package, see the official `Packaging
Python Projects` (https://packaging.python.org/tutorials/packaging-projects/)
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

The `__extends__` module attribute is **required** by all PsychoPy plugins. The
plugin loader imports the module and looks for this attribute to not only
identify whether a module is a plugin, but to determine which module namespaces
within PsychoPy to extend. The `__extends__` statement should be located at the
top of the file used as the entry point for your plugin module.

The value of `__extends__` is always either a dictionary or `None`. Dictionary
keys are strings specifying the fully qualified path of a PsychoPy module to
extend (eg. `psychopy.visual`) and items are lists of strings specifying the
names of objects to place in the associated namespace. For example, an
`__extends__` statement may look like this::

    __extends__ = {'psychopy.core': ["MyTimer"],
                   'psychopy.visual': ["MyStimClass", "myFunc"]}

Where "MyTimer", "MyStimClass", and "myFunc" are objects defined in the
namespace of the plugin module. When the plugin is loaded, "MyTimer" will be
placed in `psychopy.core`, and "MyStimClass" and "myFunc" in `psychopy.visual`.
Users can then access these objects as if they were part of the module (eg.
``psychopy.visual.myFunc()``).

In a some cases a plugin may not extend any namespaces, but still contains code
to modify PsychoPy. This is the case for patches and code which alters the
Builder interface (eg. add a menu item). If so, the file must still contain a
`__extends__` directive but it may be set to `None` or an empty dictionary.

The ``__requires__`` statement
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Some plugins may need other plugins to be loaded first to take advantage of
their features. The ``__requires__`` statement ensures that those plugins are
also loaded.

``TODO``

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





