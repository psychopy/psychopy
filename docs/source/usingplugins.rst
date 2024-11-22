.. _usingplugins:

Using Plugins to Extend PsychoPy
================================

Plugins are packages which can be loaded to extend core |PsychoPy|, allowing
third-party developers to add optional features and customizations.

PsychoPy's plugin system functions as a dynamic import mechanism where modules
define some objects (classes, functions, variables) and specify which namespaces
to export them to. This process is handled automatically by the plugin loader
and is more convenient than attempting to do the same using ``import``
statements.

Why use plugins?
----------------

Plugins are the easiest way to extend and modify PsychoPy's default behaviour,
without making permanent changes to the installed program files or contributing
the changes to the |PsychoPy| project. You can use plugins created by others, or
make them yourself for whatever purpose. For instance, plugins can be used to
add new stimulus classes to `psychopy.visual`, or modify the behaviour of
existing classes and modules. This can be leveraged to add new features or to
fix bugs between release cycles. Since plugins are standard Python packages,
changes can be easily applied across multiple systems and shared with the
|PsychoPy| community.

Consider using plugins to distribute code which cannot be contributed to the
main |PsychoPy| project for reasons that may include:

* **Niche use**, not many people use the feature and will add bloat to
  |PsychoPy| which increases workload when testing and packaging.
* Uses a **GPL incompatible license or contains proprietary** code. This allows
  users to distribute code with any licence they chose and permits compliance
  to non-disclosure agreements for companies. Using a plugin allows you to
  maintain complete ownership over your code.
* **Requires special or uncommon configurations** to use (software or hardware).
  This includes features which are limited to specific operating systems, or
  requires hardware which the |PsychoPy| dev team does not have regular access to.
* **Under heavy development** where PsychoPy's release cycle is inadequate to
  keep up with changes and bug fixes. Furthermore, the code may not be mature
  enough for inclusion with core |PsychoPy|. Plugins provide an excellent way of
  field testing features before attempting to contribute it to the main project.
* **Contains changes that can possibly break PsychoPy** which can accidentally
  affect existing experiments. If something breaks, users can simply disable the
  plugin.
* **Cannot be maintained long-term** by the |PsychoPy| developers.

Where can I find plugins?
-------------------------

Plugins are essentially Python packages and can be distributed, installed, and
used like any other Python library. |PsychoPy| plugin packages can be uploaded to
The Python Package Index (PyPI) and installed using `pip`. You can also
distribute and download plugins as ZIP archives which can be installed or
accessed from a local repository.

Are plugins safe?
-----------------

Like any Python package, plugins are capable of injecting and executing
arbitrary code which can seriously harm your system, data, security and privacy.
Therefore, the following precautions can be taken by users when using plugins:

* Only use plugins that come from reliable and reputable sources. Only obtain
  packages from sources explicitly sanctioned by the author and not third-party
  websites.
* Use anti-virus software to scan files in plugins which cannot be opened and
  read (i.e. compiled binaries) or request the author provide the source code.
* Request a checksum from the plugin author to verify the integrity of the
  package you've obtained to detect possible tampering. Plugin authors who make
  their packages publicly available should be ready to provide checksum data
  associated with their packages to users who request it.
* Audit the source code of plugins yourself (or by a trusted third-party) before
  installing a plugin. Ensure that the routines contained in the package appear
  to do only what the author describes.
* If concerned about privacy, ensure that the plugin does not contain code that
  performs unsolicited file operations, modifications to system settings, or
  data transmission over a network (ie. internet). If unsure, request details
  from the author of the plugin or have the source code audited.

If you have or find any potential security or privacy issues regarding a plugin
which arise from features that **have not been disclosed by the author**, you
can contact the author regarding the issues and request clarification. **Be
respectful** as the author may not be aware of the issue, believed that what
they were doing was innocuous (eg. collecting anonymous usage data to better the
software), or cannot divulge details about some aspect of their software (due to
a non-disclosure agreement or proprietary third-party interface). If the author
is unable to address your concerns in a timely or satisfactory manner,
discontinue use of the plugin and remove it from your system.

How do I install plugins?
-------------------------

Plugins can be installed either by using ``pip`` or by running the `setup.py`
file in the package. For instance, a plugin with project name `psychopy-plugin`
the author uploaded to the The Python Package Index (PyPI) repository can be
downloaded and installed by calling::

    python -m pip install psychopy-plugin

You can also install packages contained in zip/egg files using the same command
but substituting `psychopy-plugin` for the file name::

    python -m pip install psychopy-plugin-1.0.win-amd64.zip

How do I use a plugin?
----------------------

From Builder, all plugins are loaded by the compiled Python code when you run an 
experiment - you don't need to do anything!

From Coder, an individual plugin can be loaded by calling the 
``psychopy.plugins.loadPlugin()`` function, or you can call 
``psychopy.plugins.activatePlugins()`` to load all installed plugins at once. 
The name of the plugin to load is provided as a string, which should reflect 
the project name of the package. Note that a plugin can override the effects of 
other plugins loaded before it. Once a plugin is loaded, it cannot be unloaded 
until the Python session is restarted.

Calling ``loadPlugin()`` should preferably happen *after* importing `psychopy`
and all other ``import`` statements for |PsychoPy| modules. An example of loading
a plugin called `psychopy-plugin` looks like this::

    import psychopy
    from psychopy import plugins
    plugins.loadPlugin('psychopy-plugin')

Or, to load all at once::

    import psychopy
    from psychopy import plugins
    plugins.activatePlugins()

Some plugins may accept arguments for setup prior to attaching objects to
|PsychoPy|. You can pass positional and keyword arguments to ``loadPlugin()`` if
you wish. Here is an example where we pass arguments to the plugin when loading
it::

    plugins.loadPlugin('psychopy-plugin', 9600, debug=True)

You can also have specific plugins loaded automatically when |PsychoPy| starts
by specifying their names in Preferences. This can be done in programmatically
by calling::

    from psychopy.preferences import prefs
    prefs.general['startUpPlugins'].append('plugin-name')
    prefs.saveUserPrefs()

How do I find installed plugins?
--------------------------------

The ``psychopy.plugins.listPlugins()`` function can be used to find all packages
installed on the system which advertise themselves as |PsychoPy| plugins. The
function returns a list of strings indicating the project names of the plugin
packages. You can then pass each of these strings to ``loadPlugins()`` to load
them into the current session.

As an example, you can check if a plugin named `psychopy-plugin` is installed
using the following code::

    import psychopy
    import psychopy.plugins as plugins
    isInstalled = 'psychopy-plugin' in plugins.listPlugins()

    # load it if installed
    if isInstalled:
        plugins.loadPlugin('psychopy-plugin')

How do I make a plugin?
-----------------------

Have a cool idea you want to share with the world (or at least |PsychoPy| users)?
See :ref:`pluginDevGuide` in the developer documentation section for information
about creating your own plugins.