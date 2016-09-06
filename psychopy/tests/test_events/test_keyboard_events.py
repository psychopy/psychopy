import pytest

from pyglet.window.key import (
    MOD_SHIFT,
    MOD_CTRL,
    MOD_ALT,
    MOD_CAPSLOCK,
    MOD_NUMLOCK,
    MOD_WINDOWS,
    MOD_COMMAND,
    MOD_OPTION,
    MOD_SCROLLLOCK)

from psychopy import event

@pytest.mark.keyboard
class TestKeyboardEvents(object):

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
