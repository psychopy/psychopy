.. _pluginDevGuide:

Creating Plugins for PsychoPy
=============================

Plugins provide a means for developers to extend PsychoPy, adding new features
and customizations without directly modifying the PsychoPy installation. Read
:ref:`usingplugins` for more information about plugins before proceeding
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
metadata. The metadata of the package defines "entry points" which tells the
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
dictionary when defining entry point metadata with the `setup()` function in
the plugin project's `setup.py` file::

    setup(
        ...
        entry_points={'psychopy.visual': 'MyStim = psychopy_plugin:MyStim'},
        ...
    )

.. note::

    Plugins can load and assign entry points to names anywhere in PsychoPy's
    namespace. However, plugin developers should place them where they make
    most sense. In the last example, we put `MyStim` in `psychopy.visual`
    because that's where users would expect to find it if it was part of the
    base PsychoPy installation.

If we have additional classes we'd like to add to `psychopy.visual`, entry
entry points for that group can be given as a list of specifiers::

    setup(
        ...
        entry_points={
        'psychopy.visual': ['MyStim = psychopy_plugin:MyStim',
                            'MyStim2 = psychopy_plugin:MyStim2']
        },
        ...
    )

For more complex (albeit contrived) example to demonstrate how to modify unbound
class attributes (ie. methods and properties), say we have a plugin which
provides a custom interface to some display hardware called
`psychopy-display` that needs to alter the existing ``flip()`` method of the
``psychopy.visual.Window`` class to work. Furthermore, we want to add a class to
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

The __register__ attribute
~~~~~~~~~~~~~~~~~~~~~~~~~~

Plugin modules can define a optional attribute named ``__register__`` which
specifies a callable object. The purpose of ``__register__`` is to allow the
module to perform tasks before loading entry points based on arguments passed to
it by the plugin loader. The arguments passed to the target of ``__register__``,
come from the ``**kwargs`` given to ``loadPlugins()``. The value of this
attribute can be a string of the name or a reference to a callable object (ie.
function or method).

.. note::

    The ``__register__`` attribute should only ever be used for running routines
    pertinent to setting up entry points. The referenced object is only called
    on a module once per session.

As an example, consider a case where an entry point is defined as ``doThis`` in
plugin `python-foobar`. There are two possible behaviors which are `foo` and
`bar` that ``dothis`` can have. We can implement both behaviors in separate
functions, and use arguments passed to the ``__register__`` target to assign
which to use to as the entry point::

    __register__ = 'register'

    doThis = None

    def foo():
        return 'foo'

    def bar():
        return 'bar'

    def register(**kwargs):
        global dothis
        option = kwargs.get('option', 'foo')
        if option == 'bar':
            dothis = bar
        else:
            dothis = foo

When the user calls ``loadPlugin('python-foobar', option='bar')``, the plugin
will assign function ``bar()``` to ``doThis``. If `option` is not specified or
given as 'foo', the behavior of ``doThis`` will be that of ``foo()``.

Plugin example project
----------------------

This section will demonstrate how to create a plugin project and package it for
distribution. For this example, we will create a plugin called
`psychopy-rect-area` which adds a method to the ``psychopy.visual.Rect``
stimulus class called `getArea()` that returns the area of the shape when
called.

Project files
~~~~~~~~~~~~~

First, we need to create a directory called `psychopy-rect-area` which all our
Python packages and code will reside. Inside that directory, we create the
following files and directories::

    psychopy-rect-area/
        psychopy_rect_area/
            __init__.py
        MANIFEST.in
        README.md
        setup.py

The implementation for the `getArea()` method will be defined in a file called
``psychopy_rect_area/__init__.py``, it should contain the following::

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-
    """Plugin entry points for `psychopy-rect-area`."""

    def get_area(self):
        """Compute the area of a `Rect` stimulus in `units`.

        Returns
        -------
        float
            Area in units^2.

        """
        return self.size[0] * self.size[1]

.. note::

    The `get_area()` function needs to have `self` as the first argument because
    were are going to assign it as class method. All class methods get a
    reference to the class as the first argument. You can name this whatever you
    like (eg. `cls`).

The ``setup.py`` script is used to generate an installable plugin package. This
should contain something like the following::

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-
    from setuptools import setup

    setup(name='psychopy-rect-area',
        version='1.0',
        description='Compute the area of a Rect stimulus.',
        long_description='',
        url='http://repo.example.com',
        author='Nobody',
        author_email='nobody@example.com',
        license='GPL3',
        classifiers=[
            'Development Status :: 4 - Beta',
            'License :: OSI Approved :: GLP3 License',
            'Programming Language :: Python :: 2.7',
            'Programming Language :: Python :: 3'
        ],
        keywords='psychopy stimulus',
        packages=['psychopy_rect_area'],
        install_requires=['psychopy'],
        include_package_data=True,
        entry_points={
            'psychopy.visual.Rect': ['getArea = psychopy_rect_area:get_area']
        },
        zip_safe=False)

Looking at ``entry_points`` we can see that were assigning
``psychopy_rect_area.get_area`` to ``psychopy.visual.Rect.getArea``. Attributes
assigned to entry points should follow the naming conventions of PsychoPy (camel
case), however plugins are free to use internally whatever style the author
chooses (eg. PEP8). You should also use appropriate classifiers for your plugin,
a full list can be found here (https://pypi.org/pypi?%3Aaction=list_classifiers).

You can also specify ``install_requires`` to indicate which versions of PsychPy
are compatible with your plugin. Visit
https://packaging.python.org/discussions/install-requires-vs-requirements/ for
more information.

One should also include a ``README.md`` file which provides detailed information
about the plugin. This file can be read and passed to the ``long_description``
argument of ``setup()`` in `setup.py` if desired by inserting the following into
the setup script::

    from setuptools import setup

    def get_readme_text():
        with open('README.md') as f:
            return f.read()

    setup(
        ...
        long_description=get_readme_text(),
        ...
    )

Finally, we need specify ``README.md`` in our ``MANIFEST.in`` file to tell the
packaging system to include the file when packaging. Simply put the following
line in ``MANIFEST.in``::

    README.md

Building packages
~~~~~~~~~~~~~~~~~

PsychoPy plugin packages are built like any other Python package. We can build
a `wheel` distribution by calling the following console command::

    python setup.py sdist bdist_wheel

The resulting ``.whl`` files will appear in directory `psychopy-rect-area/dist`.
The generated packages can be installed with `pip` or uploaded to the `Python
Package Index <https://pypi.org/>`_. for more information about building and
uploading packages, visit: https://packaging.python.org/tutorials/packaging-projects/

If uploaded to PyPI, other PsychoPy users can install your plugin by entering
the following into their command prompt::

    python -m pip install psychopy-rect-area

Using the plugin
~~~~~~~~~~~~~~~~

Once installed the plugin can be activated by using the
`psychopy.plugins.loadPlugin()` function. This function should be called after
the import statements in your script::

    from psychopy import visual, core, plugins
    plugins.loadPlugin('psychopy-demo-plugin')  # load the plugin

After calling ``loadPlugin()``, all instances of ``Rect`` will have the method
``getArea()``::

    rectStim = visual.Rect(win)
    rectArea = rectStim.getArea()

Plugins as patches
------------------

A special use case of plugins is to apply and distribute "patches". Using entry
points to override module and class attributes, one can create patches to fix
minor bugs in extant PsychoPy installations between releases, or backport fixes
and features to older releases (that support plugins) that cannot be upgraded
for some reason. Patches can be distributed like any other Python package, and
can be installed and applied uniformly across multiple PsychoPy installations.

Plugins can also patch other plugins that have been previously loaded by
``loadPlugin()`` calls. This is done by defining entry points to module and
class attributes that have been created by a previously loaded plugin.

Creating patches
~~~~~~~~~~~~~~~~

As an example, consider a fictional scenario where a bug was introduced in a
recent release of PsychoPy by a hardware vendor updating their drivers. As a
result, PsychoPy's builtin support for their devices provided by the
``psychopy.hardware.Widget`` class is now broken. You notice that it has been
fixed in a pending release of PsychoPy, and that it involves a single change to
the ``getData()`` method of the ``psychopy.hardware.Widget`` class to get it
working exactly as before. However, you cannot wait for the next release because
you are in the middle of running scheduled experiments, even worse, you have
dozens of test stations using the hardware.

In this case, you can create a plugin to not only fix the bug, but apply it
across multiple existing installations to save the day. Creating a package for
our patch is no different than a regular plugin (see the
`Plugin example project`_ section for more information), so you go about
creating a project for a plugin called `psychopy-hotfix` which defines the
working version of the ``getData()`` method in a sub-module called
``psychopy_hotfix`` like this::

    # method copy and pasted from the bug fix commit
    def getData(self):
        """This function reads data from the device."""
        # code here ...

In the `setup.py` file of the plugin package, specify the entry points like this
to override the defective method in our installations::

    setup(
        name='psychopy-hotfix'
        ...
        entry_points={
            'psychopy.hardware.Widget': ['getData = psychopy_patch:getData']
        },
        ...
    )

That's it, just build a distributable package and install it on all the systems
affected by the bug.

Applying patches
~~~~~~~~~~~~~~~~

Whether you create your own patch, or obtain one provided by the PsychoPy
community, they are applied using the `loadPlugin()` function after installing
them. Experiment scripts will need to have the following lines added under
the ``import`` statements at the top of the file for the plugin to take effect
(but it's considerably less work than manually patching in the code across many
separate installations)::

    import psychopy.plugin as plugin
    plugin.loadPlugin('psychopy-patch')

After ``loadPlugin`` is called, the behaviour of the ``getData()`` method of any
instances of the ``psychopy.hardware.Widget`` class will change to the correct
one.

Once a new release of PsychoPy comes out with the patch incorporated into
it and your installations are upgraded, you can remove the above lines.

Creating window backends
------------------------

Custom backends for the `Window` class can be implemented in plugins, allowing
one to create windows using frameworks other than Pyglet, GLFW, and PyGame that
can be enabled using the appropriate ``winType`` argument.

A plugin can add a ``winType`` by specifying class and module entry
points for ``psychopy.visual.backends``. If the entry point is a subclass of
``psychopy.visual.backends.BaseBackend`` and has ``winTypeName`` defined, it
will be automatically registered and can be used as a ``winType`` by instances
of ``psychopy.visual.Window``.

.. note::

    If a module is given as an entry point, the whole module will be added to
    ``backends`` and any class within it that is a subclass of ``BaseBackend``
    and defines ``winTypeName`` will be registered. This allows one to add
    multiple window backends to PsychoPy with a single plugin module.

Example
~~~~~~~

For example, say we have a backend class called ``CustomBackend`` defined in
module ``custom_backend`` in the plugin package `psychopy-custom-backend`.
We can tell the plugin loader to register it to be used when a ``Window``
instance is created with ``winType='custom'`` by adding the ``winTypeName``
class attribute to ``CustomBackend``::

    class CustomBackend(BaseBackend):
        winTypeName = 'custom'
        ...

.. note::

    If ``winTypeName`` is not defined, the entry points will still get added to
    ``backends`` but users will not be able to use it directly by specifying
    ``winType``.

We define the entry point for our custom backend in ``setup.py`` as::

    setup(
        ...
        entry_points={
        `'psychopy.visual.backends': 'custom_backend = custom_backend'},
        ...
    )

Optionally, we can point to the backend class directly::

    setup(
        ...
        entry_points={
            'psychopy.visual.backends':
                'custom_backend = custom_backend:CustomBackend'},
        ...
    )

After the plugin is installed and loaded, we can use our backend for creating
windows by specifying ``winType`` as ``winTypeName``::

    loadPlugin('psychopy-custom-backend')
    win = Window(winType='custom')

