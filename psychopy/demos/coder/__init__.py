from pathlib import Path


class PluginDemos:
    """
    Use this class in a plugin to add demos to PsychoPy:
    - Create a subclass of PluginDemos in your plugin
    - Overload the `demos` attribute with a dict of demos added by your plugin, like the output 
      of `listDemos`
    - Overload the `label` attribute with a label for the subheading your demos will be displayed 
      under (e.g. the name of your plugin)
    - Create an entry point connecting your subclass of PluginDemos to "psychopy.demos.coder"

    The easiest way to make sure your `demos` attribute is formatted properly is to import 
    `psychopy.demos.coder:scanFolder` and use that on the folder with your demos in.
    """
    label = None
    demos = {}

    def __init_subclass__(cls):
        # if subclass doesn't have a label, use its name
        if cls.label is None:
            cls.label = cls.__name__
        # add demos
        PluginDemos.demos[cls.label] = cls.demos


def scanFolder(folder):
    """
    Scan a given folder recursively for Coder demos

    Parameters
    ----------
    folder : str or Path
        Folder to look in

    Returns
    -------
    dict[str: str or dict]
        Dict of demo files against their file paths; demo categories (i.e. folders) will be a dict of the demos within against the folder name
    """
    # path-ise folder
    folder = Path(folder)
    # start with blank output
    output = {}
    # iterate through entries in this folder
    for file in folder.iterdir():
        # ignore files starting with _ (__init__, __pycache__, etc.)
        if file.stem.startswith("_"):
            continue
        # if looking at a category, recur
        if file.is_dir():
            output[file.stem] = scanFolder(file)
            continue
        # skip non-Python files
        if file.suffix != ".py":
            continue
        # add Python scripts
        output[file.stem] = str(file.absolute())

    return output


def listDemos():
    """
    List all coder demos

    Returns
    -------
    dict[str: str or dict]
        Dict of demo files against their file paths; demo categories (i.e. folders) will be a dict of the demos within against the folder name
    """
    # get demos from the demos folder
    demos = scanFolder(
        Path(__file__).parent
    )
    # get demos from plugins
    demos.update(
        PluginDemos.demos
    )
    
    return demos
