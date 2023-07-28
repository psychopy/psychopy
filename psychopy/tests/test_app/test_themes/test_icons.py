import pytest
from pathlib import Path
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

    def testIconParity(self):
        """
        Test that the same icons exist for all themes
        """
        # Get root icons folder
        from psychopy.app.themes.icons import resources as root
        # Iterate through all png files in light
        for file in (root / "light").glob("**/*.png"):
            # Ignore @2x
            if file.stem.endswith("@2x"):
                file = file.parent / (file.stem[:-3] + ".png")
            # Ignore size numbers
            while file.stem[-1].isnumeric():
                file = file.parent / (file.stem[:-1] + ".png")
            # Get location relative to light folder
            file = file.relative_to(root / "light")
            # Create versions of file with size suffices
            variants = [
                file,
                file.parent / (file.stem + "16.png"),
                file.parent / (file.stem + "32.png"),
                file.parent / (file.stem + "48.png"),
            ]
            # Check that equivalent file exists in all themes
            for theme in ("light", "dark", "classic"):
                # Check that file or variant exists
                assert any(
                    (root / theme / v).is_file() for v in variants
                ), f"Could not find file '{file}' for theme '{theme}'"
