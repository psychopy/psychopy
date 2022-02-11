import re
from ..utils import _q, _lb, _rb, _d, _sl
from psychopy.experiment import Param, utils as exputils


def test_param_str():
    """
    Test that params convert to str as expected in both Python and JS
    """

    cases = [
        # Regular string
        {"obj": Param("Hello there", "str"),
         "py": f"{_q}Hello there{_q}",
         "js": f"{_q}Hello there{_q}"},
        # Enforced string
        {"obj": Param("\\, | or /", "str", canBePath=False),
         "py": f"{_q}{_sl}, | or /{_q}",
         "js": f"{_q}{_sl}, | or /{_q}"},
        # Dollar string
        {"obj": Param("$win.color", "str"),
         "py": f"win.color",
         "js": f"psychoJS.window.color"},
        # Integer
        {"obj": Param("1", "int"),
         "py": f"1",
         "js": f"1"},
        # Float
        {"obj": Param("1", "num"),
         "py": f"1.0",
         "js": f"1.0"},
        # File path
        {"obj": Param("C://Downloads//file.ext", "file"),
         "py": f"{_q}C:/Downloads/file.ext{_q}",
         "js": f"{_q}C:/Downloads/file.ext{_q}"},
        # Table path
        {"obj": Param("C://Downloads//file.csv", "table"),
         "py": f"{_q}C:/Downloads/file.csv{_q}",
         "js": f"{_q}C:/Downloads/file.csv{_q}"},
        # Color
        {"obj": Param("red", "color"),
         "py": f"{_q}red{_q}",
         "js": f"{_q}red{_q}"},
        # RGB Color
        {"obj": Param("0.7, 0.7, 0.7", "color"),
         "py": f"{_lb}0.7, 0.7, 0.7{_rb}",
         "js": f"{_lb}0.7, 0.7, 0.7{_rb}"},
        # Code
        {"obj": Param("win.color", "code"),
         "py": f"win.color",
         "js": f"psychoJS.window.color"},
        # Extended code
        {"obj": Param("for x in y:\n\tprint(y)", "extendedCode"),
         "py": f"for x in y:\n\tprint(y)",
         "js": f"for x in y:\n\tprint(y)"},  # this will change when snipped2js is fully working
        # List
        {"obj": Param("1, 2, 3", "list"),
         "py": f"{_lb}1, 2, 3{_rb}",
         "js": f"{_lb}1, 2, 3{_rb}"},
        # Extant file path marked as str
        {"obj": Param(__file__, "str"),
         "py": f"{_q}{__file__.replace(_sl, '/')}{_q}",
         "js": f"{_q}{__file__.replace(_sl, '/')}{_q}"},
        # Nonexistent file path marked as str
        {"obj": Param("C:\\\\Downloads\\file.csv", "str"),
         "py": f"{_q}C:/Downloads/file.csv{_q}",
         "js": f"{_q}C:/Downloads/file.csv{_q}"},
        # Underscored file path marked as str
        {"obj": Param("C:\\\\Downloads\\_file.csv", "str"),
         "py": f"{_q}C:/Downloads/_file.csv{_q}",
         "js": f"{_q}C:/Downloads/_file.csv{_q}"},
        # Escaped $ in str
        {"obj": Param("This costs \\$4.20", "str"),
         "py": f"{_q}This costs $4.20{_q}",
         "js": f"{_q}This costs $4.20{_q}"},
        # Unescaped \ in str
        {"obj": Param("This \\ that", "str"),
         "py": f"{_q}This \\\\ that{_q}",
         "js": f"{_q}This \\\\ that{_q}"},
        # Name containing "var" (should no longer return blank as of #4336)
        {"obj": Param("variableName", "code"),
         "py": f"variableName",
         "js": f"variableName"},
        # Color param with a $
        {"obj": Param("$letterColor", "color"),
         "py": f"letterColor",
         "js": f"letterColor"},
        # Double quotes naked list
        {'obj': Param("\"left\", \"down\", \"right\"", "list"),
         'py': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}",
         'js': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}"},
        # Single quotes naked list
        {'obj': Param("\'left\', \'down\', \'right\'", "list"),
         'py': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}",
         'js': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}"},
        # Single quotes tuple syntax
        {'obj': Param("(\'left\', \'down\', \'right\')", "list"),
         'py': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}",
         'js': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}"},
        # Single quotes list syntax
        {'obj': Param("[\'left\', \'down\', \'right\']", "list"),
         'py': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}",
         'js': f"{_lb}{_q}left{_q}, {_q}down{_q}, {_q}right{_q}{_rb}"},
        # Single value
        {'obj': Param("\"left\"", "list"),
         'py': f"{_lb}{_q}left{_q}{_rb}",
         'js': f"{_lb}{_q}left{_q}{_rb}"},
        # Single value list syntax
        {'obj': Param("[\"left\"]", "list"),
         'py': f"{_lb}{_q}left{_q}{_rb}",
         'js': f"{_lb}{_q}left{_q}{_rb}"},
        # Variable name
        {'obj': Param("$left", "list"),
         'py': r"left",
         'js': r"left"},
    ]

    # Take note of what the script target started as
    initTarget = exputils.scriptTarget
    # Try each case
    for case in cases:
        # Test Python
        exputils.scriptTarget = "PsychoPy"
        assert (re.fullmatch(case['py'], str(case['obj'])),
                f"`{repr(case['obj'])}` should match the regex `{case['py']}`, but it was `{case['obj']}`")
        # Test JS
        exputils.scriptTarget = "PsychoJS"
        assert (re.fullmatch(case['js'], str(case['obj'])),
                f"`{repr(case['obj'])}` should match the regex `{case['js']}`, but it was `{case['obj']}`")
    # Set script target back to init
    exputils.scriptTarget = initTarget


def test_dollar_sign_syntax():
    # Define some param values, along with values which Param.dollarSyntax should return
    cases = [
        # Valid dollar and redundant dollar
        {'val': f"$hello $there",
         'ans': f"hello {_d}there",
         'valid': False},
        # Valid dollar and scaped dollar
        {'val': f"$hello \$there",
         'ans': f"hello {_sl}{_sl}{_d}there",
         'valid': False},
        # Just redundant dollar
        {'val': f"hello $there",
         'ans': f"hello {_d}there",
         'valid': False},
        # Just escaped dollar
        {'val': f"\$hello there",
         'ans': f"{_sl}{_sl}{_d}hello there",
         'valid': True},
        # Dollar in comment
        {'val': f"#$hello there",
         'ans': f"#{_d}hello there",
         'valid': False},
        # Comment after dollar
        {'val': f"$#hello there",
         'ans': f"#hello there",
         'valid': True},
        # Dollar and comment
        {'val': f"$hello #there",
         'ans': f"hello #there",
         'valid': True},
        # Valid dollar and redundtant dollar in comment
        {'val': f"$hello #$there",
         'ans': f"hello #{_d}there",
         'valid': True},
        # Valid dollar and escaped dollar in escaped d quotes
        {'val': f"$hello \"\$there\"",
         'ans': f"hello {_q}{_sl}{_sl}{_d}there{_q}",
         'valid': True},
        # Valid dollar and escaped dollar in escaped s quotes
        {'val': f"$hello \'\$there\'",
         'ans': f"hello {_q}{_sl}{_sl}{_d}there{_q}",
         'valid': True},
    ]
    # Run dollar syntax on each case
    for case in cases:
        # Make str param from val
        param = Param(case['val'], "str")
        # Run dollar syntax method
        valid, ans = param.dollarSyntax()
        # Is the output correct?
        assert re.fullmatch(case['ans'], ans), (
            f"Dollar syntax for {repr(param)} should return `{case['ans']}`, but instead returns `{ans}`"
        )
        assert valid == case['valid'], (
            f"Dollar syntax function should consider validity of {repr(param)} to be {case['valid']}, but instead "
            f"received {valid}"
        )
