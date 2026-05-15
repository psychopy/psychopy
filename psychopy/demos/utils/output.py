from pathlib import Path
import os.path

__all__ = [
    "outputFolder"
]

# folder for demos to save their data to
outputFolder = Path(
    os.path.expanduser("~/psychopy-demos/output")
)
# make sure folder exists
if not outputFolder.is_dir():
    outputFolder.mkdir(parents=True)
