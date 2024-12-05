"""
Utils for checking / making Component documentation
"""

from collections import OrderedDict
from psychopy import logging, experiment
from psychopy.tools import stringtools
from pathlib import Path
import jinja2


__folder__ = Path(__file__).parent
docsDir = __folder__.parent / "source" / "builder" / "components"


def checkMissing():
    """
    Check for missing Component documentation.

    Returns
    -------
    list[BaseComponent]
        A list of Component class handles which are missing documentation.
    """
    # list in which to store classes with missing docs
    missing = []
    # iterate through Components
    for name, cls in experiment.getAllElements().items():
        # skip hidden
        if cls.hidden or name in ("BaseComponent", "BaseStandaloneRoutine", "BaseValidatorRoutine"):
            continue
        # is there a docs file for it?
        if not (docsDir / f"{name}.rst").is_file():
            # add to missing list
            missing.append(cls)
            # log
            logging.error(
                f"No documentation for {name}"
            )
            continue
    
    return missing


def createFromTemplate(cls):
    """
    Use the information contained within a given Component/Routine class to populate a template and 
    create documentation. This won't be perfect, so please visual inspect after! This is a 
    time-saving tool to give you a starting point when documenting a new class.

    Parameters
    ----------
    cls : BaseComponent or BaseStandaloneRoutine
        Class to create documentation for, must be either a Component or a Standalone Routine.
    
    Returns
    -------
    pathlib.Path
        Path to the file where content was written
    str
        Content which was written
    """
    from psychopy.experiment.components import BaseComponent
    from psychopy.experiment.routines import BaseStandaloneRoutine
    # make an instance of given comp
    exp = experiment.Experiment()
    if issubclass(cls, BaseComponent):
        comp = cls(exp=exp, parentName="someRoutine")
    elif issubclass(cls, BaseStandaloneRoutine):
        comp = cls(exp=exp)
    else:
        raise TypeError(
            "Component class must be either a Component or a StandaloneRoutine"
        )
    # get clean component title
    cls.title = stringtools.CaseSwitcher.pascal2title(cls.__name__)
    # sort params by category
    params = OrderedDict()
    for param in comp.params.values():
        if param.categ not in params:
            params[param.categ] = []
        params[param.categ].append(param)
    # sort categories
    for categ in reversed(['Basic', 'Layout', 'Appearance', 'Formatting', 'Texture']):
        if categ in params:
            params.move_to_end(categ, last=False)
    for categ in ['Data', 'Custom', 'Hardware', 'Testing']:
        if categ in params:
            params.move_to_end(categ, last=True)
    # populate jinja template
    src = (__folder__ / "ComponentTemplate.rst").read_text(encoding="utf-8")
    template = jinja2.Template(source=src)
    content = template.render(
        cls=cls,
        params=params
    )
    # save
    target = docsDir / f"{cls.__name__}.rst"
    target.write_text(content, encoding="utf-8")
    logging.info(
        f"Written Component docs for {cls.__name__} in {target.absolute()}"
    )

    return target, content
