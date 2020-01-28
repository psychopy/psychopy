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
PsychoPy session at runtime. This is done by calling the
``psychopy.plugins.loadPlugin()`` function and passing the project name of the
desired plugin to it. Once ``loadPlugin()`` returns, imported objects are
immediately accessible. Any changes made to PsychoPy with plugins do not persist
across sessions, meaning if Python is restarted, PsychoPy will return to its
default behaviour unless ``loadPlugin()`` is called again.

Installed plugins for PsychoPy are discoverable on the system using package
metadata. The metadata of the package defines "entry points" which tell the
plugin loader where within PsychoPy's namespace to place objects exported by the
plugin. The loader also ensures plugins are compatible with the Python
environment (ie. operating system, CPU architecture, and Python version). Any
Python package can define entry points, allowing developers to add functionality
to PsychoPy without needing to create a separate plugin project.

Plugin packages
---------------

A plugin has a similar structure to Python package, see the official `Packaging
Python Projects` (https://packaging.python.org/tutorials/packaging-projects)
guide for details.

Naming plugin packages
~~~~~~~~~~~~~~~~~~~~~~

Standalone plugins, which are packages that exist only to extend PsychoPy should
adhere to the following naming convention to make PsychoPy plugins discernible
from any other package in public repositories. Plugin project names should
always be prefixed with `psychopy` with individual words separated with a `-` or
`_` symbol (i.e. `psychopy-quest-procedure` or `psychopy_quest_procedure` are
valid). What you chose to name the package is up to you, but keep it concise and
informative.

.. note::

    The plugin system does not use project names to identify plugins, rather relying
    on package metadata to identify if a package has entry points pertinent to
    PsychoPy. Therefore, projects do not need to be named a particular way to still
    be used as plugins. This allows packages which are not primarily used with
    PsychoPy to extend it, without the need for a separate plugin package. It also
    allows a single package to be used as a plugin for multiple projects unrelated
    to PsychoPy.

The module or sub-package which defines the objects which entry points refer to
should be some variant of the name to prevent possible namespace conflicts. For
instance, we would name our module `psychopy_quest_procedure` if our project
was called `psychopy-quest-procedure`.

Specifying entry points
~~~~~~~~~~~~~~~~~~~~~~~

Entry points reference objects in a plugin module that PsychoPy will attach
to itself. Packages advertise their entry points by having them in their
metadata. How entry points are defined and added to package metadata is
described in the section
`Dynamic Discovery of Services and Plugins <https://setuptools.readthedocs.io/en/latest/setuptools.html#dynamic-discovery-of-services-and-plugins>`_
of the documentation for `setuptools`.

When loading a specified plugin, the plugin loader searches for a distribution
matching the given project name, then gets the entry point mapping from its
metadata. Any entry point belonging to groups whose names start with `psychopy`
is loaded. Group names are fully-qualified names of modules or unbound classes
within PsychoPy's namespace to create links to the associated entry points in
the plugin module/package.

As an example, using entry point groups and specifiers, we can add a class called
`MyStim` defined in the plugin module `psychopy_plugin` to appear in
`psychopy.visual` when the plugin is loaded. To do this, we use the following
dictionary when defining entry point metadata using the `setup()` function::

    setup(
        ...
        entry_points={'psychopy.visual': ['MyStim = psychopy_plugin:MyStim']},
        ...
    )

For more complex (albeit contrived) example, say we have a plugin which
provides a custom interface to some display hardware called
`psychopy-display` that needs to alter the existing ``flip()`` method of the
``psychopy.visual.Window`` class to work. Also, we want to add a class to
`psychopy.hardware` called `DisplayControl` to give the user a way of setting up
and configuring the display. Entry points for both objects are defined in the
plugin's `psychopy_display` module. To get the effect we want, we specify entry
points using the following::

    setup(
        ...
        entry_points={
            'psychopy.visual.Window': ['flip = psychopy_display:flip'],
            'psychopy.hardware': ['DisplayControl = psychopy_display:DisplayControl']},
        ...
    )

After calling ``loadPlugin('psychopy-display')``, the user will be able to
create instances of ``psychopy.hardware.DisplayControl`` and new instances of
``psychopy.visual.Window`` will have the modified ``flip()`` method.

.. note::

    Plugins can load and assign entry points to names anywhere in PsychoPy's
    namespace. However, plugin developers should place them where they make
    most sense. In the last example, we put `DisplayControl` in
    `psychopy.hardware` because that's where users would expect to find it if
    it was part of the base PsychoPy installation.

