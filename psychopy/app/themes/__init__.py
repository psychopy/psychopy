import json
from pathlib import Path

from ... import logging, prefs

_cache = {}


class Theme:
    # Tag pointing to code colors
    code = "PsychopyLight"
    # Tag pointing to app colors
    app = "light"
    # Tag pointing to app icons
    icons = "light"
    # Tooltip for theme menu
    info = ""

    def __init__(self, name):
        self.set(name)

    def set(self, name):
        # Get spec file from name
        specFile = Path(prefs.paths['themes']) / (name.replace(" ", "") + ".json")
        # Ensure spec file exists
        if not specFile.is_file():
            # If no file, use PsychopyLight
            logging.warn(f"Theme file for '{name}' not found, reverting to PsychopyLight")
            name = "PsychopyLight"
            specFile = Path(__file__).parent / "spec" / "PsychopyLight.json"
        # Load file
        spec = loadSpec(specFile)
        # Ensure code spec is present
        if "code" not in spec:
            # If no code spec, use PsychopyLight
            logging.warn(f"Code color spec for '{name}' not found, reverting to PsychopyLight")
            default = loadSpec(Path(__file__).parent / "spec" / "PsychopyLight.json")
            spec['code'] = default
        # Store theme name as code colors
        self.code = name
        # If spec file points to a set of app colors, update this object
        if "app" in spec:
            self.app = spec['app']
        # If spec file points to a set of app icons, update this object
        if "icons" in spec:
            self.icons = spec['icons']
        # If spec file contains tooltip, store it
        if "info" in spec:
            self.info = spec['info']

    def __repr__(self):
        return f"<{self.code}: app={self.app}, icons={self.icons}>"

    def __eq__(self, other):
        # If other is also a Theme, check that all its values are the same
        if isinstance(other, Theme):
            app = self.app == other.app
            icons = self.icons == other.icons
            code = self.code.replace(" ", "").lower() == other.code.replace(" ", "").lower()
            return app and icons and code

    def __deepcopy__(self, memo=None):
        return Theme(self.code)


def loadSpec(file):
    # Convert to path
    if isinstance(file, str):
        file = Path(file)
    # If filename is not already cached, load and cache the file
    if file.stem not in _cache:
        with open(file) as f:
            _cache[file] = json.load(f)
    # Return cached values
    return _cache[file]


theme = Theme("PsychopyLight")
