import ast

from numpy import array
from esprima import parseScript

from psychopy.tools import monitorunittools
from psychopy.alerts._alerts import alert
from psychopy.tools.fontmanager import FontManager

fontMGR = FontManager()

class TestWin:
    """
    Creates a false window with necessary attributes for converting component
    Parameters to pixels.
    """
    def __init__(self, exp):
        self.useRetina = True
        self.exp = exp
        self.monitor = self.exp.settings.monitor
        winSize = self.exp.settings.params['Window size (pixels)'].val

        if winSize and isinstance(winSize, str):
            self.size = ast.literal_eval(winSize)
        elif winSize and (isinstance(winSize, list) or isinstance(winSize, tuple)):
            self.size = winSize
        else:
            self.size = (1024, 768)

def validDuration(t, hz, toleranceFrames=0.01):
    """Test whether this is a possible time duration given the frame rate"""
    # best not to use mod operator for floats. e.g. 0.5%0.01 gives 0.00999
    # (due to a float round error?)
    # nFrames = t*hz so test if round(nFrames)==nFrames but with a tolerance
    nFrames = float(t) * hz  # t might not be float if given as "0.5"?
    return abs(nFrames - round(nFrames)) < toleranceFrames


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


def testFloat(val):
    """
    Test value for float.
    Used to detect use of variables, strings and none types, which cannot be checked.
    """
    try:
        return type(float(val)) == float
    except Exception:
        return False


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
        return

    # Test X
    if size[0] > win.size[0]:
        alert(2115, component, {'dimension': 'X'})
    # Test Y
    if size[1] > win.size[1]:
        alert(2115, component, {'dimension': 'Y'})

    # Test if smaller than 1 pixel (X dimension)
    if size[0] < 1:
        alert(2120, component, {'dimension': 'X'})
    # Test if smaller than 1 pixel (Y dimension)
    if size[1] < 1:
        alert(2120, component, {'dimension': 'Y'})

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
        return

    # Test X position
    if abs(pos[0]) > win.size[0]:
        alert(2155, component, {'dimension': 'X'})
    # Test Y position
    if abs(pos[1]) > win.size[1]:
        alert(2155, component, {'dimension': 'Y'})

def testStartEndTiming(component):
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

    # Check for string / variable
    if not all([testFloat(start['val']), testFloat(stop['val'])]):
        return

    if [start['type'], stop['type']] == ["time (s)", "time (s)"]:
        if float(start['val']) > float(stop['val']):
            alert(4105, component, {'type': 'time'})
    if [start['type'], stop['type']] == ["frame N", "frame N"]:
        if int(float(start['val'])) > int(float(stop['val'].strip())):
            alert(4105, component, {'type': 'frame'})

def testAchievableVisualOnsetOffset(component):
    """Test whether start and end times are less than 1 screen refresh.
    """

    if component.type not in ["Text", "Aperture", "Dots", "EnvGrating", "Form",
                              "Grating", "Image", "Movie", "NoiseStim", "Polygon"]:
        return

    if "startType" not in component.params or "stopType" not in component.params:
        return

    startVal = component.params['startVal'].val
    stopVal = component.params['stopVal'].val

    if testFloat(startVal):
        if component.params['startType'] == "time (s)":
            # Test times are greater than 1 screen refresh for 60Hz and 100Hz monitors
            if not float.is_integer(float(startVal)) and float(startVal) < 1.0 / 60:
                alert(3110, component, {'type': 'start', 'time': startVal, 'Hz': 60})
            if not float.is_integer(float(startVal)) and float(startVal) < 1.0 / 100:
                alert(3110, component, {'type': 'start', 'time': startVal, 'Hz': 100})

    if testFloat(stopVal):
        if component.params['stopType'] == "duration (s)":
            # Test times are greater than 1 screen refresh for 60Hz and 100Hz monitors
            if not float.is_integer(float(stopVal)) and float(stopVal) < 1.0 / 60:
                alert(3110, component, {'type': 'stop', 'time': stopVal, 'Hz': 60})
            if not float.is_integer(float(stopVal)) and float(stopVal) < 1.0 / 100:
                alert(3110, component, {'type': 'stop', 'time': stopVal, 'Hz': 100})

def testValidVisualStimTiming(component):
    """Test whether visual stimuli presented accurately for times requested,
    relative to screen refresh rate of 60 and 100Hz monitors.
    """
    if component.type not in ["Text", "Aperture", "Dots", "EnvGrating", "Form",
                              "Grating", "Image", "Movie", "NoiseStim", "Polygon"]:
        return

    if "startType" not in component.params or "stopType" not in component.params:
        return

    # Check for string / variable
    startVal = component.params['startVal'].val
    stopVal = component.params['stopVal'].val

    if testFloat(startVal):
        if component.params['startType'] == "time (s)":
            # Test times are valid multiples of screen refresh for 60Hz and 100Hz monitors
            if not validDuration(startVal, 60):
                alert(3115, component, {'type': 'start', 'time': startVal, 'Hz': 60})

    if testFloat(stopVal):
        if component.params['stopType'] == "duration (s)":
            # Test times are valid multiples of screen refresh for 60Hz and 100Hz monitors
            if not  validDuration(stopVal, 60):
                alert(3115, component, {'type': 'stop', 'time': stopVal, 'Hz': 60})

def testFramesAsInt(component):
    """
    Test whole numbers are used for frames.
    """

    if "startType" not in component.params or "stopType" not in component.params :
        return

    startVal = component.params['startVal'].val
    stopVal = component.params['stopVal'].val

    if testFloat(startVal):
        if component.params['startType'] in ["frame N", "duration (frames)"]:
            # Test frames are whole numbers
            if not float.is_integer(float(startVal)):
                alert(4115, component, {'type': 'start', 'frameType': component.params['startType']})

    if testFloat(stopVal):
        if component.params['stopType'] in ["frame N", "duration (frames)"]:
            # Test frames are whole numbers
            if not float.is_integer(float(stopVal)):
                alert(4115, component, {'type': 'stop', 'frameType': component.params['stopType']})

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
        alert(4305, component, strFields={'name': component.params['name']})

def testFont(component):
    """
    Tests whether font is stored locally or whether it needs to be retrieved from Google Fonts

    Parameters
    ----------
    component: Component
        The component used for testing
    """
    if 'font' in component.params:
        fontInfo = fontMGR.getFontsMatching(component.params['font'].val, fallback=False)
        if not fontInfo:
            alert(4320, strFields={'param': component.params['font']})

def testDollarSyntax(component):
    """
    Tests that use of dollar signs in Builder components to denote literal interpretation are used correctly

    Parameters
    ----------
    component: Component
        The component used for testing
    """
    valid = {}
    for (key, param) in component.params.items():
        if not param.dollarSyntax()[0]:
            alert(4315, strFields={'component': component, 'param': param})
    return valid

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
        compile(str(component.params[tab].val), "path", 'exec')
    except Exception as err:
        strFields = {'codeTab': tab, 'lineNumber': err.lineno, 'code': err.text}
        # Dont sent traceback because strFields gives better localisation of error
        alert(4205, component, strFields)

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
        parseScript(str(component.params[tab].val))
    except Exception as err:
        strFields = {'codeTab': tab, 'lineNumber': err.message}
        # Dont sent traceback because strFields gives better localisation of error
        alert(4210, component, strFields)
