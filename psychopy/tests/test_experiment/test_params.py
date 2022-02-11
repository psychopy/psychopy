from psychopy.experiment import Param, utils as exputils


def test_param_str():
    exemplars = [
        # Regular string
        {"obj": Param("Hello there", "str"),
         "py": "'Hello there'",
         "js": "'Hello there'"},
        # Enforced string
        {"obj": Param("\\, | or /", "str", canBePath=False),
         "py": "'\\\\, | or /'",
         "js": "'\\\\, | or /'"},
        # Dollar string
        {"obj": Param("$win.color", "str"),
         "py": "win.color",
         "js": "psychoJS.window.color"},
        # Integer
        {"obj": Param("1", "int"),
         "py": "1",
         "js": "1"},
        # Float
        {"obj": Param("1", "num"),
         "py": "1.0",
         "js": "1.0"},
        # File path
        {"obj": Param("C://Downloads//file.ext", "file"),
         "py": "'C:/Downloads/file.ext'",
         "js": "'C:/Downloads/file.ext'"},
        # Table path
        {"obj": Param("C://Downloads//file.csv", "table"),
         "py": "'C:/Downloads/file.csv'",
         "js": "'C:/Downloads/file.csv'"},
        # Color
        {"obj": Param("red", "color"),
         "py": "'red'",
         "js": "'red'"},
        # RGB Color
        {"obj": Param("0.7, 0.7, 0.7", "color"),
         "py": "[0.7, 0.7, 0.7]",
         "js": "[0.7, 0.7, 0.7]"},
        # Code
        {"obj": Param("win.color", "code"),
         "py": "win.color",
         "js": "psychoJS.window.color"},
        # Extended code
        {"obj": Param("for x in y:\n\tprint(y)", "extendedCode"),
         "py": "for x in y:\n\tprint(y)",
         "js": "for x in y:\n\tprint(y)"},  # this will change when snipped2js is fully working
        # List
        {"obj": Param("1, 2, 3", "list"),
         "py": "[1, 2, 3]",
         "js": "[1, 2, 3]"},
    ]
    _slash = "\\"
    tykes = [
        # Extant file path marked as str
        {"obj": Param(__file__, "str"),
         "py": f"'{__file__.replace(_slash, '/')}'",
         "js": f"'{__file__.replace(_slash, '/')}'"},
        # Nonexistent file path marked as str
        {"obj": Param("C:\\\\Downloads\\file.csv", "str"),
         "py": "'C:/Downloads/file.csv'",
         "js": "'C:/Downloads/file.csv'"},
        # Underscored file path marked as str
        {"obj": Param("C:\\\\Downloads\\_file.csv", "str"),
         "py": "'C:/Downloads/_file.csv'",
         "js": "'C:/Downloads/_file.csv'"},
        # Escaped $ in str
        {"obj": Param("This costs \\$4.20", "str"),
         "py": "'This costs $4.20'",
         "js": "'This costs $4.20'"},
        # Unescaped \ in str
        {"obj": Param("This \\ that", "str"),
         "py": "'This \\\\ that'",
         "js": "'This \\\\ that'"},
        # Name containing "var" (should no longer return blank as of #4336)
        {"obj": Param("variableName", "code"),
         "py": "variableName",
         "js": "variableName"},
        # Color param with a $
        {"obj": Param("$letterColor", "color"),
         "py": "letterColor",
         "js": "letterColor"},
    ]

    # Take note of what the script target started as
    initTarget = exputils.scriptTarget
    # Try each case
    for case in exemplars + tykes:
        # Check Python compiles as expected
        if "py" in case:
            exputils.scriptTarget = "PsychoPy"
            assert str(case['obj']) == case['py']
        # Check JS compiles as expected
        if "js" in case:
            exputils.scriptTarget = "PsychoJS"
            assert str(case['obj']) == case['js']
    # Set script target back to init
    exputils.scriptTarget = initTarget