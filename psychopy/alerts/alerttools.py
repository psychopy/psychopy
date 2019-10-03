import sys
import ast
from esprima import parseScript
from numpy import array

from psychopy.monitors import Monitor
from psychopy.tools import monitorunittools
from psychopy.alerts._alerts import alert


class TestWin(object):
    """
    Creates a false window with necessary attributes for converting component
    Parameters to pixels.
    """
    def __init__(self, exp, monitor):
        self.useRetina = True
        self.exp = exp
        self.monitor = Monitor(monitor)
        self.size = self.monitor.getSizePix()


def runTest(component):
    """
    Run integrity checks and sends output to the AlertLog system.

    Parameters
    ----------
    component : Component
        The PsychoPy component being tested
    """
    win = TestWin(component.exp, component.exp.settings.params['Monitor'].val)
    units = component.exp.settings.params['Units'].val
    testSize(component, win, units)
    testPos(component, win, units)
    testDisabled(component)
    testTiming(component)

def convertParamToPix(value, win, units):
    """
    Convert value to numpy array
    Parameters
    ----------
    value : str, int, float, list, tuple
        Parameter value to be converted to pixels
    win : TestWin object
        A false window with necessary attributes for converting component
        parameters to pixels
    units : str
        Screen units

    Returns
    -------
    numpy array
        Parameter converted to pixels in numpy array
    """
    if isinstance(value, str):
        value = array(ast.literal_eval(value))
    else:
        value = array(value)
    return monitorunittools.convertToPix(value, array([0, 0]), units=units, win=win) * 2

def testSize(component, win, units):
    """
    Runs size testing for component

    Parameters
    ----------
    component: Component
        The component used for size testing
    win : TestWin object
        Used for testing component size in bounds
    units : str`
        Screen units
    """
    if 'size' not in component.params:
        return

    try:
        size = convertParamToPix(component.params['size'].val, win, units)
    except Exception:  # Use of variables fails check
        alert(9000, component)
        return

    # Test X
    if size[0] > win.size[0]:
        alert(1001, component, {'dimension': 'X'})
    # Test Y
    if size[1] > win.size[1]:
        alert(1001, component, {'dimension': 'Y'})

    # Test if smaller than 1 pixel (X dimension)
    if size[0] < 1:
        alert(1002, component, {'dimension': 'X'})
    # Test if smaller than 1 pixel (Y dimension)
    if size[1] < 1:
        alert(1002, component, {'dimension': 'Y'})

def testPos(component, win, units):
    """
    Runs position testing for component

    Parameters
    ----------
    component: Component
        The component used for size testing
    win : TestWin object
        Used for testing component position in bounds
    units : str`
        Screen units
    """
    if 'pos' not in component.params:
        return

    try:
        pos = convertParamToPix(component.params['pos'].val, win, units)
    except Exception:  # Use of variables fails check
        alert(9000, component)
        return

    # Test X position
    if abs(pos[0]) > win.size[0]:
        alert(1003, component, {'dimension': 'X'})
    # Test Y position
    if abs(pos[1]) > win.size[1]:
        alert(1003, component, {'dimension': 'Y'})

def testTiming(component):
    """
    Tests stimuli starts before end time.

    Parameters
    ----------
    component: Component
        The component used for size testing
    """

    if "startType" not in component.params or "stopType" not in component.params :
        return

    if (component.params['startType'] not in ["time (s)", "frame N"]
        or component.params['stopType'] not in ["time (s)", "frame N"]):
            return

    start = {'type': component.params['startType'].val, 'val' : component.params['startVal'].val}
    stop = {'type': component.params['stopType'].val, 'val' : component.params['stopVal'].val}

    try:
        float(start['val'])
        float(stop['val'])
    except Exception:
        alert(9000, component)
        return

    if [start['type'], stop['type']] == ["time (s)", "time (s)"]:
        if float(start['val']) > float(stop['val']):
            alert(1004, component, {'type': 'time'})
    if [start['type'], stop['type']] == ["frame N", "frame N"]:
        if int(float(start['val'])) > int(float(stop['val'].strip())):
            alert(1004, component, {'type': 'frame'})

def testDisabled(component):
    """
    Tests whether a component is enabled.

    Parameters
    ----------
    component: Component
        The component used for testing
    """
    if "disabled" not in component.params:
        return

    if component.params['disabled'].val:
        alert(1005, component)

def checkPythonSyntax(component, tab):
    """
    Checks each Python code component tabs for syntax errors.
    Note, catalogue message is formatted using a dict that contains:
            {
            'codeTab': The code component tab as string,
            'code': The code containing the error,
            'lineNumber': The line number of error as string
            }

    Parameters
    ----------
    component: Component
        The code component being tested
    tab: str
        The name of the code component tab being tested
    """
    try:
        compile(str(component.params[tab]), "path", 'exec')
    except Exception as err:
        strFormat = {'codeTab': tab, 'lineNumber': err.lineno, 'code': err.text.strip()}
        alert(2000, component, strFormat)

def checkJavaScriptSyntax(component, tab):
    """
    Checks each JS code component tabs for syntax errors.
    Note, catalogue message is formatted using a dict that contains:
        {
        'codeTab': The code component tab as string,
        'lineNumber': The line number and error msg as string
        }

    Parameters
    ----------
    component: Component
        The code component being tested
    tab: str
        The name of the code component tab being tested
    """
    try:
        parseScript(str(component.params[tab]))
    except Exception as err:
        strFormat = {'codeTab': tab, 'lineNumber': err.message}
        alert(2001, component, strFormat)