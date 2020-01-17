.. _usingplugins:

Using Plugins to Extend PsychoPy
================================

Plugins are packages which can be loaded to extend core PsychoPy, allowing
third-party developers to add optional features and customizations.

PsychoPy's plugin system functions as a dynamic import mechanism where modules
define some objects (classes, functions, variables) and specify which namespaces
to export them to. This process is handled automatically by the plugin loader
and is more convenient than attempting to do the same using ``import``
statements.

Why use plugins?
----------------

Plugins are used to extend and modify PsychoPy's default behaviour at runtime
without making permanent changes to the installed program files. This works by
importing objects from plugin module then patching them into PsychoPy, either by
creating or reassigning attributes within PsychoPy's module namespaces/scope to
reference them. While this process can be done conventionally using ``import``
statements and "monkey patching", the plugin loader automates this based on
metadata the plugin package contains.

One may use plugins to add new classes and functions to PsychoPy, for instance
creating a new stimulus class and have it appear in `psychopy.visual`. Other
users can then download and install your plugin package and use it too. Another
use of plugins is to modify existing PsychoPy code to add or replace extant
attributes of modules and classes. This can be leveraged to add new features or
to fix bugs between release cycles. Since plugins are standard Python packages
changes can be easily applied across multiple systems.

Consider using plugins to distribute code which cannot be contributed to the
main project. Reasons for this may include:

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

Where can I find plugins?
-------------------------

Plugins are essentially Python packages and can be distributed, installed, and
used like any other Python library. PsychoPy plugin packages can be uploaded to
The Python Package Index (PyPI) and installed using `pip`. You can also
distribute and download plugins as ZIP archives which can be installed or
accessed from a local repository.

Are plugins safe?
-----------------

Like any Python package, plugins are capable of injecting and
executing arbitrary code which can seriously harm your system and data.
Therefore, the following precautions should be taken by users when using
plugins:

* Only use plugins that come from reliable and reputable sources. Only obtain
  packages from sources explicitly sanctioned by the author and not third-party
  websites.
* Request a checksum from the plugin author to verify the integrity of the
  package you've obtained to detect possible tampering. Plugin authors who make
  their packages publicly available should be ready to provide checksum data
  associated with their packages to users who request it.
* Audit the source code of plugins before installing a plugin. Ensure that the
  routines contained in the package appear to do only what the author describes.
* Use anti-virus software to scan files in plugins which cannot be opened and
  read (i.e. compiled binaries) or request the author provide the source code.

The above list is not exhaustive and guaranteed to avoid security issues.

How do I install plugins?
-------------------------

Plugins can be installed either by using ``pip`` or by running the `setup.py`
file in the package. For instance, a plugin named `psychopy_plugin` the author
uploaded to the The Python Package Index (PyPI) repository can be downloaded and
installed by calling::

    python -m pip install psychopy_plugin

You can also install packages contained in zip/egg files using the same command
but substituting `psychopy_plugin` for the file name.

How do I use a plugin?
----------------------

A plugin can be loaded by calling the ``psychopy.plugins.loadPlugins()``
function. The names of the plugins to load are provided as either a single
string or list of strings. Plugins will be loaded in the order they appear in
the list. Note that a plugin can override the effects of other plugins loaded
before it. Once a plugin is loaded, it cannot be unloaded until the Python
session is restarted.

Calling ``loadPlugins()`` should always happen *AFTER* importing `psychopy` and
preferably after all other ``import`` statements for PsychoPy modules. An
example of loading a plugin called `psychopy_plugin` looks like this::

    import psychopy
    import psychopy.plugins as plugins
    plugins.loadPlugins('psychopy_plugin')

You can also load multiple plugins by specifying a list::

    plugins.loadPlugins(['psychopy_plugin', 'psychopy_plugin2'])

Plugins can also reside in some local or network drive as ZIP archives and can
be loaded by specifying the ``path`` argument::

    plugins.loadPlugins('psychopy_plugin', path='/path/to/plugin/')

How do I make a plugin?
-----------------------

For instructions on how to make plugins, see :ref:`pluginDevGuide` for
more information.