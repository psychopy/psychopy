import pytest
from psychopy.app.themes import icons
from psychopy.experiment.components.unknown import UnknownComponent


class TestIcons:
    @pytest.mark.usefixtures("get_app")
    def test_button_icons(self, get_app):
        exemplars = [
            # File open, 32px
            (icons.ButtonIcon("fileopen", size=32),
             icons.ButtonIcon("fileopen", size=32)),
            # Clear, 16px
            (icons.ButtonIcon("clear", size=32),
             icons.ButtonIcon("clear", size=32)),
        ]
        tykes = [
            # File open, no size
            (icons.ButtonIcon("fileopen", size=32),
             icons.ButtonIcon("fileopen", size=32)),
            # File open, wrong size
            (icons.ButtonIcon("fileopen", size=48),
             icons.ButtonIcon("fileopen", size=48)),
        ]

        for case in exemplars + tykes:
            # Ensure that the underlying bitmap of each button is the same object
            assert case[0].bitmap is case[1].bitmap

    @pytest.mark.usefixtures("get_app")
    def test_component_icons(self, get_app):
        exemplars = [
            # Unknown component, 48px
            (icons.ComponentIcon(UnknownComponent, size=48),
             icons.ComponentIcon(UnknownComponent, size=48)),
        ]
        tykes = [
            # Unknown component, no size
            (icons.ComponentIcon(UnknownComponent, size=48),
             icons.ComponentIcon(UnknownComponent, size=48)),
            # Unknown component, wrong size
            (icons.ComponentIcon(UnknownComponent, size=32),
             icons.ComponentIcon(UnknownComponent, size=32)),
        ]

        for case in exemplars + tykes:
            # Ensure that the underlying bitmap of each button is the same object
            assert case[0].bitmap is case[1].bitmap
