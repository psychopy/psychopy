#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Tests for Keyboard device with 'event' backend (Issue #7810).
Verifies that keypress events unpack name and timestamp properly,
preventing keyList filtering breakage and dropped events.
"""

import sys
import time
from unittest.mock import MagicMock

# Gracefully stub heavy optional monitor dependencies if absent in minimal test environment
if 'scipy' not in sys.modules:
    try:
        import scipy
    except ImportError:
        sys.modules['scipy'] = MagicMock()
        sys.modules['scipy.interpolate'] = MagicMock()

if 'json_tricks' not in sys.modules:
    try:
        import json_tricks
    except ImportError:
        sys.modules['json_tricks'] = MagicMock()

import pytest
from psychopy import event, core
from psychopy.hardware.keyboard import Keyboard, KeyboardDevice, KeyPress


@pytest.mark.keyboard
class TestKeyboardEventBackend:
    """Tests for Keyboard device using the 'event' backend (Issue #7810)."""

    def setup_method(self):
        self.kb = Keyboard(backend='event')
        event.clearEvents()
        self.kb.clearEvents()

    def teardown_method(self):
        event.clearEvents()
        self.kb.clearEvents()

    def test_key_name_and_value_are_strings(self):
        """Verify KeyPress.name and KeyPress.value are strings, not (name, timestamp) tuples."""
        event._onPygletKey('f', modifiers=0, emulated=True)
        keys = self.kb.getKeys(waitRelease=False, clear=True)
        assert len(keys) == 1
        press = keys[0]
        assert isinstance(press.name, str)
        assert press.name == 'f'
        assert isinstance(press.value, str)
        assert press.value == 'f'
        assert press == 'f'
        assert press != 'j'

    def test_key_filtering_with_keylist(self):
        """Verify getKeys(keyList=['f']) properly filters and returns matching keys."""
        event._onPygletKey('f', modifiers=0, emulated=True)
        keys = self.kb.getKeys(keyList=['f'], waitRelease=False, clear=True)
        assert len(keys) == 1
        assert keys[0].name == 'f'
        assert keys[0].value == 'f'

        # When requesting a different key, non-matching keys should be filtered out
        event._onPygletKey('f', modifiers=0, emulated=True)
        filtered = self.kb.getKeys(keyList=['j'], waitRelease=False, clear=False)
        assert len(filtered) == 0

        # Unmatched keys remain in buffer when clear=False
        all_keys = self.kb.getKeys(waitRelease=False, clear=True)
        assert len(all_keys) == 1
        assert all_keys[0].name == 'f'

    def test_multiple_keys_in_same_tick(self):
        """Verify multiple keys pressed in the same tick are all processed, not just the first one."""
        event._onPygletKey('a', modifiers=0, emulated=True)
        event._onPygletKey('b', modifiers=0, emulated=True)
        event._onPygletKey('c', modifiers=0, emulated=True)

        keys = self.kb.getKeys(waitRelease=False, clear=True)
        assert len(keys) == 3
        assert [k.name for k in keys] == ['a', 'b', 'c']
        assert [k.value for k in keys] == ['a', 'b', 'c']

    def test_timestamps_and_reaction_times(self):
        """Verify tDown and rt are accurately populated with proper time bases."""
        self.kb.clock.reset()
        time.sleep(0.05)
        event._onPygletKey('a', modifiers=0, emulated=True)
        time.sleep(0.03)
        event._onPygletKey('b', modifiers=0, emulated=True)

        keys = self.kb.getKeys(waitRelease=False, clear=True)
        assert len(keys) == 2
        k1, k2 = keys[0], keys[1]

        # Timestamps should be positive floats and strictly ascending
        assert isinstance(k1.tDown, float)
        assert isinstance(k2.tDown, float)
        assert k1.tDown < k2.tDown

        # Reaction times relative to kb.clock
        assert isinstance(k1.rt, float)
        assert isinstance(k2.rt, float)
        assert k1.rt < k2.rt
        assert 0.04 <= k1.rt <= 0.15
        assert 0.07 <= k2.rt <= 0.20

    def test_parse_message_shapes(self):
        """Verify parseMessage handles both (key, timestamp) pairs and bare strings."""
        device = self.kb.device

        # Pair / list from event.getKeys(timeStamped=True)
        resp_pair = device.parseMessage(['f', 123.456])
        assert resp_pair.name == 'f'
        assert resp_pair.value == 'f'
        assert resp_pair.tDown == 123.456
        assert isinstance(resp_pair.rt, float)

        # Bare string
        resp_str = device.parseMessage('space')
        assert resp_str.name == 'space'
        assert resp_str.value == 'space'
        assert resp_str == 'space'
        assert isinstance(resp_str.tDown, float)
        assert isinstance(resp_str.rt, float)


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
