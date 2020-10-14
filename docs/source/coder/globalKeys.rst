Global Event Keys
=================

Global event keys are single keys (or combinations of a single key and one or
more "modifier" keys such as Ctrl, Alt, etc.) with an associated Python
callback function. This function will be executed if the key (or
key/modifiers combination) was pressed.

.. note::

   Global event keys only work with the `pyglet` backend, which is the default.

PsychoPy fully automatically monitors and processes key presses during most
portions of the experimental run, for example during
`core.wait()` periods, or when calling `win.flip()`. If a global
event key press is detected, the specified function will be run
immediately. You are not required to manually poll and check for key
presses. This can be particularly useful to implement a global
"shutdown" key, or to trigger laboratory equipment on a key press
when testing your experimental script -- without cluttering the code.
But of course the application is not limited to these two scenarios.
In fact, you can associate any Python function with a global event key.

All active global event keys are stored in `event.globalKeys`.

Adding a global event key (simple)
----------------------------------
First, let's ensure no global event keys are currently set by calling
func:`event.globalKeys.clear`.
::
    >>> from psychopy import event
    >>> event.globalKeys.clear()

To add a new global event key, you need to invoke
func:`event.globalKeys.add`. This function has two required arguments: the
key name, and the function to associate with that key.
::
    >>> key = 'a'
    >>> def myfunc():
    ...     pass
    ...
    >>> event.globalKeys.add(key=key, func=myfunc)

Look at `event.globalKeys`, we can see that the global event key has indeed
been created.
::

    >>> event.globalKeys
    <_GlobalEventKeys :
        [A] -> 'myfunc' <function myfunc at 0x10669ba28>
    >

Your output should look similar. You may happen to spot
We can take a closer look at the specific global key event we added.
::

    >>> event.globalKeys['a']
    _GlobalEvent(func=<function myfunc at 0x10669ba28>, func_args=(), func_kwargs={}, name='myfunc')

This output tells us that

- our key `a` is associated with our function `myfunc`

- `myfunc` will be called without passing any positional or keyword
  arguments (`func_args` and `func_kwargs`, respectively)

- the event name was automatically set to the name of the function.

.. note::

   Pressing the key won't do anything unless a :class:`psychopy.visual.Window`
   is created and and its :func:~`psychopy.visual.Window.flip` method or
   :func:`psychopy.core.wait` are called.

Adding a global event key (advanced)
------------------------------------
We are going to associate a function with a more complex calling signature
(with positional and keyword arguments) with a global event key. First, let's
create the dummy function:
::

    >>> def myfunc2(*args, **kwargs):
    ...     pass
    ...

Next, compile some positional and keyword arguments and a custom name for this
event. Positional arguments must be passed as tists or uples, and keyword
arguments as dictionaries.
::

    >>> args = (1, 2)
    >>> kwargs = dict(foo=3, bar=4)
    >>> name = 'my name'

.. note::

   Even when intending to pass only a single positional argument, `args` must be
   a list or tuple, e.g., `args = [1]` or `args = (1,)`.


Finally, specify the key and a combination of modifiers. While key names are
just strings, modifiers are lists or tuples of modifier names.
::

    >>> key = 'b'
    >>> modifiers = ['ctrl', 'alt']

.. note::

   Even when specifying only a single modifier key, `modifiers` must be a list
   or tuple, e.g., `modifiers = ['ctrl']` or `modifiers = ('ctrl',)`.

We are now ready to create the global event key.
::

    >>> event.globalKeys.add(key=key, modifiers=modifiers,
    ... func=myfunc2, func_args=args, func_kwargs=kwargs,
    ... name=name)

Check that the global event key was successfully added.
::

    >>> event.globalKeys
    <_GlobalEventKeys :
        [A] -> 'myfunc' <function myfunc at 0x10669ba28>
        [CTRL] + [ALT] + [B] -> 'my name' <function myfunc2 at 0x112eecb90>
    >

The key combination `[CTRL] + [ALT] + [B]` is now associated with the function
`myfunc2`, which will be called in the following way:
::

    myfunc2(1, 2, foo=2, bar=4)

.. _indexing:

Indexing
--------
`event.globalKeys` can be accessed like an ordinary dictionary. The index keys
are `(key, modifiers)` namedtuples.
::

    >>> event.globalKeys.keys()
    [_IndexKey(key='a', modifiers=()), _IndexKey(key='b', modifiers=('ctrl', 'alt'))]

To access the global event associated with the key combination
`[CTRL] + [ALT] + [B]`, we can do

    >>> event.globalKeys['b', ['ctrl', 'alt']]
    _GlobalEvent(func=<function myfunc2 at 0x112eecb90>, func_args=(1, 2), func_kwargs={'foo': 3, 'bar': 4}, name='my name')

To make access more convenient, specifying the modifiers is optional in case
none were passed to :func:`psychopy.event.globalKeys.add` when the global
event key was added, meaning the following commands are identical.
::

    >>> event.globalKeys['a', ()]
    _GlobalEvent(func=<function myfunc at 0x10669ba28>, func_args=(), func_kwargs={}, name='myfunc')
    >>> event.globalKeys['a']
    _GlobalEvent(func=<function myfunc at 0x10669ba28>, func_args=(), func_kwargs={}, name='myfunc')

All elements of a global event can be accessed directly.
::

    >>> index = ('b', ['ctrl', 'alt'])
    >>> event.globalKeys[index].func
    <function myfunc2 at 0x112eecb90>
    >>> event.globalKeys[index].func_args
    (1, 2)
    >>> event.globalKeys[index].func_kwargs
    {'foo': 3, 'bar': 4}
    >>> event.globalKeys[index].name
    'my name'

Number of active event keys
---------------------------
The number of currently active event keys can be retrieved by passing
`event.globalKeys` to the `len()` function.
::

    >>> len(event.globalKeys)
    2

Removing global event keys
--------------------------
There are three ways to remove global event keys:

- using :func:`psychopy.event.globalKeys.remove`,
- using `del`, and
- using :func:`psychopy.event.globalKeys.pop`.

:func:`psychopy.event.globalKeys.remove`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
To remove a single key, pass the key name and modifiers (if any) to
:func:`psychopy.event.globalKeys.remove`.
::

    >>> event.globalKeys.remove(key='a')

A convenience method to quickly delete *all* global event keys is to pass
`key='all'`
::

    >>> event.globalKeys.remove(key='all')

`del`
~~~~~
Like with other dictionaries, items can be removed from `event.globalKeys`
by using the `del` statement. The provided index key must be specified as
described in :ref:`indexing`.
::

    >>> index = ('b', ['ctrl', 'alt'])
    >>> del event.globalKeys[index]

:func:`psychopy.event.globalKeys.pop`
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~
Again, as other dictionaries, `event.globalKeys` provides a `pop` method to
retrieve an item and remove it from the dict. The first argument to `pop` is the
index key, specified as described in :ref:`indexing`. The second argument is
optional. Its value will be returned in case no item with the matching indexing
key could be found, for example if the item had already been removed previously.
::

    >>> r = event.globalKeys.pop('a', None)
    >>> print(r)
    _GlobalEvent(func=<function myfunc at 0x10669ba28>, func_args=(), func_kwargs={}, name='myfunc')
    >>> r = event.globalKeys.pop('a', None)
    >>> print(r)
    None

Global shutdown key
-------------------
The PsychoPy preferences for `shutdownKey` and `shutdownKeyModifiers`
(both unset by default) will be used to automatically create a global
shutdown key. To demonstrate this automated behavior, let us first change
the preferences programmatically (these changes will be lost when quitting the
current Python session).
::

    >>> from psychopy.preferences import prefs
    >>> prefs.general['shutdownKey'] = 'q'

We can now check if a global shutdown key has been automatically created.
::

    >>> from psychopy import event
    >>> event.globalKeys
    <_GlobalEventKeys :
        [Q] -> 'shutdown (auto-created from prefs)' <function quit at 0x10c171938>
    >

And indeed, it worked!

What happened behind the scences? When importing the `psychopy.event`
module, the initialization of `event.globalKeys` checked for valid shutdown key
preferences and automatically initialized a shutdown key accordingly.
This key is associated with the :func:~`psychopy.core.quit` function, which will
shut down PsychoPy.
::

   >>> from psychopy.core import quit
   >>> event.globalKeys['q'].func == quit
   True

Of course you can very easily add a global shutdown key manually, too. You
simply have to associate a key with :func:~`psychopy.core.quit`.
::

    >>> from psychopy import core, event
    >>> event.globalKeys.add(key='q', func=core.quit, name='shutdown')

That's it!

A working example
-----------------
In the above code snippets, our global event keys were not actually functional,
as we didn't create a window, which is required to actually collect the key
presses. Our working example will thus first create a window and then add
global event keys to change the window color and quit the experiment,
respectively.
::

    #!/usr/bin/env python
    # -*- coding: utf-8 -*-

    from __future__ import print_function
    from psychopy import core, event, visual


    def change_color(win, log=False):
        win.color = 'blue' if win.color == 'gray' else 'gray'
        if log:
            print('Changed color to %s' % win.color)


    win = visual.Window(color='gray')
    text = visual.TextStim(win,
                           text='Press C to change color,\n CTRL + Q to quit.')

    # Global event key to change window background color.
    event.globalKeys.add(key='c',
                         func=change_color,
                         func_args=[win],
                         func_kwargs=dict(log=True),
                         name='change window color')

    # Global event key (with modifier) to quit the experiment ("shutdown key").
    event.globalKeys.add(key='q', modifiers=['ctrl'], func=core.quit)

    while True:
        text.draw()
        win.flip()

