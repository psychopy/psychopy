#!/usr/bin/env python
# -*- coding: utf-8 -*-

import pytest
from psychopy import event, core, iohub, visual
from psychopy.preferences import prefs
from psychopy.hardware import keyboard
from psychopy.visual import Window

from pyglet.window.key import (MOD_SHIFT,
                               MOD_CTRL,
                               MOD_ALT,
                               MOD_CAPSLOCK,
                               MOD_NUMLOCK,
                               MOD_WINDOWS,
                               MOD_COMMAND,
                               MOD_OPTION,
                               MOD_SCROLLLOCK)


@pytest.mark.keyboard
class TestKeyboardEvents():

    def test_keyname(self):
        """Test that a key name is correctly returned."""
        event._onPygletKey('a', 0, emulated=True)
        keys = event.getKeys()
        assert len(keys) == 1
        assert keys[0] == 'a'

    def test_modifiers(self):
        """Test that key modifier flags are correctly returned"""
        event._onPygletKey('a', MOD_CTRL|MOD_SHIFT, emulated=True)
        keys = event.getKeys(modifiers=True)
        assert len(keys) == 1
        assert len(keys[0]) == 2
        assert keys[0][0] == 'a'
        assert keys[0][1]['ctrl']
        assert keys[0][1]['shift']
        assert not keys[0][1]['alt']

    def test_timestamp(self):
        """Test that a keypress timestamp is correctly returned"""
        event._onPygletKey('a', 0, emulated=True)
        keys = event.getKeys(timeStamped=True)
        assert len(keys) == 1
        assert len(keys[0]) == 2
        assert keys[0][0] == 'a'
        assert isinstance(keys[0][1], float)
        assert keys[0][1] > 0.0

    def test_modifiers_and_timestamp(self):
        """Test that both key modifiers and timestamp are returned"""
        event._onPygletKey('a', MOD_ALT, emulated=True)
        keys = event.getKeys(modifiers=True, timeStamped=True)
        assert len(keys) == 1
        assert len(keys[0]) == 3
        assert keys[0][0] == 'a'
        assert keys[0][1]['alt']
        assert isinstance(keys[0][2], float)

    def test_invalid_modifiers(self):
        """Modifiers must be integers."""
        key = 'a'
        modifiers = None

        with pytest.raises(ValueError):
            event._onPygletKey(key, modifiers, emulated=True)

    def test_german_characters(self):
        """Test that event can handle German characters"""
        # 824633720832 = ö as pyglet symbol string
        # need to use emulated = False to execute the lines that actually
        # fix the German characters handling
        event._onPygletKey(824633720832, 0, emulated=False)
        event._onPygletText('ö', emulated=True)
        keys = event.getKeys(modifiers=False, timeStamped=True)
        assert len(keys) == 1
        assert len(keys[0]) == 2
        assert keys[0][0] == 'ö'
        assert isinstance(keys[0][1], float)

    def test_german_characters_with_modifiers(self):
        """Test that event can handle German characters with modifiers"""
        # 824633720832 = ö as pyglet symbol string
        # need to use emulated = False to execute the lines that actually
        # fix the German characters handling
        event._onPygletKey(824633720832, MOD_SHIFT | MOD_SCROLLLOCK, emulated=False)
        event._onPygletText('ö', emulated=True)
        keys = event.getKeys(modifiers=True, timeStamped=True)
        assert len(keys) == 1
        assert len(keys[0]) == 3
        assert keys[0][0] == 'ö'
        assert keys[0][1]['shift']
        assert keys[0][1]['scrolllock']
        assert isinstance(keys[0][2], float)


class TestIohubKeyboard:
    def setup(self):
        self.win = visual.Window()
        self.ioServer = iohub.launchHubServer(window=self.win)
        self.kb = keyboard.Keyboard(backend="iohub")

    def test_timestamps(self):
        # make global clock
        globalClock = core.Clock()
        # sync global clock with iohub
        self.ioServer.syncClock(globalClock)
        # get time from a variety of sources
        times = [
            # ioHub process time
            self.kb._iohubKeyboard.clock.getTime(),
            # ioHub time in current process
            iohub.Computer.global_clock.getTime(),
            # experiment time
            globalClock.getTime(),
        ]
        # confirm that all values are within 0.001 of eachother
        avg = sum(times) / len(times)
        deltas = [abs(t - avg) for t in times]
        same = [d < 0.001 for d in deltas]

        assert all(same)


@pytest.mark.keyboard
class TestGLobalEventKeys():
    @classmethod
    def setup_class(self):
        self.win = Window([128, 128], winType='pyglet', pos=[50, 50], autoLog=False)

    @classmethod
    def teardown_class(self):
        self.win.close()

    def setup_method(self, test_method):
        # Disable auto-creation of shutdown key.
        prefs.general['shutdownKey'] = ''

    def _func(self, *args, **kwargs):
        return [args, kwargs]

    def test_shutdownKey_prefs(self):
        key = 'escape'
        modifiers = ('ctrl', 'alt')

        prefs.general['shutdownKey'] = key
        prefs.general['shutdownKeyModifiers'] = modifiers

        global_keys = event._GlobalEventKeys()
        e = list(global_keys)[0]

        assert key, modifiers == e
        assert global_keys[e].func == core.quit

    def test_add(self):
        key = 'a'
        func = self._func

        global_keys = event._GlobalEventKeys()
        global_keys.add(key=key, func=func)

        assert global_keys[key, ()].func == func
        assert global_keys[key, ()].name == func.__name__

    def test_add_key_twice(self):
        key = 'a'
        func = self._func
        global_keys = event._GlobalEventKeys()
        global_keys.add(key=key, func=func)

        with pytest.raises(ValueError):
            global_keys.add(key=key, func=func)

    def test_add_name(self):
        key = 'a'
        name = 'foo'
        func = self._func

        global_keys = event._GlobalEventKeys()
        global_keys.add(key=key, func=func, name=name)
        assert global_keys[key, ()].name == name

    def test_add_args(self):
        key = 'a'
        func = self._func
        args = (1, 2, 3)

        global_keys = event._GlobalEventKeys()
        global_keys.add(key=key, func=func, func_args=args)

        assert global_keys[key, ()].func_args == args

    def test_add_kwargs(self):
        key = 'a'
        func = self._func
        kwargs = dict(foo=1, bar=2)

        global_keys = event._GlobalEventKeys()
        global_keys.add(key=key, func=func, func_kwargs=kwargs)

        assert global_keys[key, ()].func_kwargs == kwargs

    def test_add_args_and_kwargs(self):
        key = 'a'
        func = self._func
        args = (1, 2, 3)
        kwargs = dict(foo=1, bar=2)

        global_keys = event._GlobalEventKeys()
        global_keys.add(key=key, func=func, func_args=args,
                        func_kwargs=kwargs)

        assert global_keys[key, ()].func_args == args
        assert global_keys[key, ()].func_kwargs == kwargs

    def test_add_invalid_key(self):
        key = 'foo'
        func = self._func
        global_keys = event._GlobalEventKeys()

        with pytest.raises(ValueError):
            global_keys.add(key=key, func=func)

    def test_add_invalid_modifiers(self):
        key = 'a'
        modifiers = ('foo', 'bar')
        func = self._func
        global_keys = event._GlobalEventKeys()

        with pytest.raises(ValueError):
            global_keys.add(key=key, modifiers=modifiers, func=func)

    def test_remove(self):
        keys = ['a', 'b', 'c']
        modifiers = ('ctrl',)
        func = self._func

        global_keys = event._GlobalEventKeys()
        [global_keys.add(key=key, modifiers=modifiers, func=func)
         for key in keys]

        global_keys.remove(keys[0], modifiers)
        with pytest.raises(KeyError):
            _ = global_keys[keys[0], modifiers]

    def test_remove_modifiers_list(self):
        key = 'a'
        modifiers = ['ctrl', 'alt']
        func = self._func

        global_keys = event._GlobalEventKeys()
        global_keys.add(key=key, modifiers=modifiers, func=func)

        global_keys.remove(key, modifiers)
        with pytest.raises(KeyError):
            _ = global_keys[key, modifiers]

    def test_remove_invalid_key(self):
        key = 'a'
        global_keys = event._GlobalEventKeys()

        with pytest.raises(KeyError):
            global_keys.remove(key)

    def test_remove_all(self):
        keys = ['a', 'b', 'c']
        func = self._func

        global_keys = event._GlobalEventKeys()
        [global_keys.add(key=key, func=func) for key in keys]

        global_keys.remove('all')
        assert len(global_keys) == 0

    def test_getitem(self):
        key = 'escape'
        modifiers = ('ctrl', 'alt')
        func = self._func

        global_keys = event._GlobalEventKeys()
        global_keys.add(key=key, modifiers=modifiers, func=func)

        assert global_keys[key, modifiers] == global_keys._events[key, modifiers]

    def test_getitem_string(self):
        key = 'escape'
        func = self._func

        global_keys = event._GlobalEventKeys()
        global_keys.add(key=key, func=func)

        assert global_keys[key] == global_keys._events[key, ()]

    def test_getitem_modifiers_list(self):
        key = 'escape'
        modifiers = ['ctrl', 'alt']
        func = self._func

        global_keys = event._GlobalEventKeys()
        global_keys.add(key=key, modifiers=modifiers, func=func)

        assert (global_keys[key, modifiers] ==
                global_keys._events[key, tuple(modifiers)])

    def test_setitem(self):
        keys = 'a'
        modifiers = ()
        global_keys = event._GlobalEventKeys()

        with pytest.raises(NotImplementedError):
            global_keys[keys, modifiers] = None

    def test_delitem(self):
        key = 'escape'
        modifiers = ('ctrl', 'alt')
        func = self._func

        global_keys = event._GlobalEventKeys()
        global_keys.add(key=key, modifiers=modifiers, func=func)

        del global_keys[key, modifiers]
        with pytest.raises(KeyError):
            _ = global_keys[key, modifiers]

    def test_delitem_string(self):
        key = 'escape'
        func = self._func

        global_keys = event._GlobalEventKeys()
        global_keys.add(key=key, func=func)

        del global_keys[key]
        with pytest.raises(KeyError):
            _ = global_keys[key]

    def test_len(self):
        prefs.general['shutdownKey'] = ''
        key = 'escape'
        func = self._func

        global_keys = event._GlobalEventKeys()
        assert len(global_keys) == 0

        global_keys.add(key=key, func=func)
        assert len(global_keys) == 1

        del global_keys[key, ()]
        assert len(global_keys) == 0

    def test_event_processing(self):
        key = 'a'
        modifiers = 0
        func = self._func
        args = (1, 2, 3)
        kwargs = dict(foo=1, bar=2)

        event.globalKeys.add(key=key, func=func, func_args=args,
                             func_kwargs=kwargs)

        r = event._process_global_event_key(key, modifiers)
        assert r[0] == args
        assert r[1] == kwargs

    def test_index_keys(self):
        key = 'escape'
        modifiers = ('ctrl', 'alt')
        func = self._func

        global_keys = event._GlobalEventKeys()
        global_keys.add(key=key, modifiers=modifiers, func=func)

        index_key = list(global_keys.keys())[-1]
        assert index_key.key == key
        assert index_key.modifiers == modifiers

    def test_numlock(self):
        key = 'a'
        modifiers = ('numlock',)
        func = self._func

        global_keys = event._GlobalEventKeys()

        with pytest.raises(ValueError):
            global_keys.add(key=key, modifiers=modifiers, func=func)


if __name__ == '__main__':
    import pytest
    pytest.main()
