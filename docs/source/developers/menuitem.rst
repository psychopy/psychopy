.. _addMenuItem:

Adding a new Menu Item
=====================================

Adding a new menu-item to the Builder (or Coder) is relatively straightforward, but there are several files that need to be changed in specific ways.

1. makeMenus()
--------------

The code that constructs the menus for the Builder is within a method named `makeMenus()`, within class builder.BuilderFrame(). Decide which submenu your new command fits under, and look for that section (e.g., File, Edit, View, and so on). For example, to add an item for making the Routine panel items larger, I added two lines within the View menu, by editing the `makeMenus()` method of class `BuilderFrame` within `psychopy/app/builder/builder.py` (similar for Coder)::

    self.viewMenu.Append(self.IDs.tbIncrRoutineSize, _("&Routine Larger\t%s") %self.app.keys['largerRoutine'], _("Larger routine items"))
    wx.EVT_MENU(self, self.IDs.tbIncrRoutineSize, self.routinePanel.increaseSize)

Note the use of the translation function, _(), for translating text that will be displayed to users (menu listing, hint).

2. wxIDs.py
------------------------
A new item needs to have a (numeric) ID so that `wx` can keep track of it. Here, the number is `self.IDs.tbIncrRoutineSize`, which I had to define within the file `psychopy/app/wxIDs.py`::

    tbIncrRoutineSize=180

It's possible that, instead of hard-coding it like this, it's better to make a call to `wx.NewIdRef()` -- wx will take care of avoiding duplicate IDs, presumably.

3. Key-binding prefs
--------------------------

I also defined a key to use to as a keyboard short-cut for activating the new menu item::

    self.app.keys['largerRoutine']

The actual key is defined in a preference file. Because psychopy is multi-platform, you need to add info to four different .spec files, all of them being within the `psychopy/preferences/` directory, for four operating systems (Darwin, FreeBSD, Linux, Windows). For `Darwin.spec` (meaning macOS), I added two lines. The first line is not merely a comment: it is also automatically used as a tooltip (in the preferences dialog, under key-bindings), and the second being the actual short-cut key to use::

    # increase display size of Routines
    largerRoutine = string(default='Ctrl++') # on Mac Book Pro this is good

This means that the user has to hold down the `Ctrl` key and then press the `+` key. Note that on Macs, 'Ctrl' in the spec is automatically converted into 'Cmd' for the actual key to use; in the .spec, you should always specify things in terms of 'Ctrl' (and not 'Cmd'). The default value is the key-binding to use unless the user defines another one in her or his preferences (which then overrides the default). Try to pick a sensible key for each operating system, and update all four .spec files.

4. Your new method
-----------------------------

The second line within `makeMenus()` adds the key-binding definition into wx's internal space, so that when the key is pressed, `wx` knows what to do. In the example, it will call the method `self.routinePanel.increaseSize`, which I had to define to do the desired behavior when the method is called (in this case, increment an internal variable and redraw the routine panel at the new larger size).

5. Documentation
----------------

To let people know that your new feature exists, add a note about your new feature in the CHANGELOG.txt, and appropriate documentation in .rst files.
