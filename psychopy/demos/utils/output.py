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
# print so the user knows where to look
print(
    f"This experiment uses the psychopy.demos.utils.output module, so you should look for any output in:\n"
    f"{outputFolder.absolute()}"
)
