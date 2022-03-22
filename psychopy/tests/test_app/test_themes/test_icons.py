import pytest
from psychopy.app.themes import icons
from psychopy.experiment.components.unknown import UnknownComponent


class TestIcons:
    @pytest.mark.usefixtures("get_app")
    def test_button_icons(self, get_app):
        # Create two button objects
        icon1 = icons.ButtonIcon("beta", size=32)
        icon2 = icons.ButtonIcon("beta", size=32)
        # Ensure that the underlying bitmap of each button is the same object
        assert icon1.bitmap is icon2.bitmap

    @pytest.mark.usefixtures("get_app")
    def test_button_icons(self, get_app):
        # Create two button objects
        icon1 = icons.ComponentIcon(UnknownComponent, size=32)
        icon2 = icons.ComponentIcon(UnknownComponent, size=32)
        # Ensure that the underlying bitmap of each button is the same object
        assert icon1.bitmap is icon2.bitmap
