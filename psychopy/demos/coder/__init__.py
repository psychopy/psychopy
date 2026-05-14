from pathlib import Path


def listDemos():
    """
    List all coder demos

    Returns
    ===============
    dict[str: str or dict]
        Dict of demo files against their file paths; demo categories (i.e. folders) will be a dict of the demos within against the folder name
    """

    def scanFolder(folder):
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
    
    return scanFolder(
        Path(__file__).parent
    )
