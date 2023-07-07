import re
import inspect
from pathlib import Path
from ..utils import _q, _lb, _rb, _d, _sl
from psychopy import experiment
from psychopy.experiment import Param, utils as exputils


class TestStyle:
    """
    Tests for grammar, spelling, case conventions & PsychoPy-isms in user-facing
    strings
    """

    keywords = {
        # PsychoPy keywords
        'routine': "Routine",
        'component': "Component",
        'param': "Param",
        'parameter': "Parameter",
        'standalone routine': "Standalone Routine",
        'Standalone routine': "Standalone Routine",
        # our brand names
        'psychopy': "PsychoPy",
        'psychojs': "PsychoJS",
        'pavlovia': "Pavlovia",
        'surveyjs': "SurveyJS",
        # other brand names
        'python': "Python",
        'excel': "Excel",
        'gazepoint': "GazePoint",
        'eyelink': "EyeLink",
        'opengl': "OpenGL",
        # initialisms
        'json': "JSON",
        'rtl': "RTL",
        'ltr': "LTR",
        'url': "URL",
        'html': "HTML",
        'js': "JS",
        'ip': "IP",
        'rt': "RT",
    }
    # add sentence start versions
    for kw in keywords.copy():
        keywords[kw.capitalize()] = keywords[kw]

    def setup_class(self):
        # dummy experiment to dump class instances in
        exp = experiment.Experiment()
        # list of dicts:
        # - 'name': element name
        # - 'instance': element instance
        # - 'class': element class
        # - 'file': def file
        self.cases = []
        # populate cases list
        for name, cls in experiment.getAllElements().items():
            # create basic instance of class
            try:
                emt = cls(exp=exp)
            except TypeError:
                emt = cls(exp=exp, parentName="")
            # get file in which class was defined
            file = Path(inspect.getfile(cls))
            # append to cases
            self.cases.append({
                'name': name,
                'instance': emt,
                'class': cls,
                'file': file
            })

    @staticmethod
    def capitalizeKeywords(phrase):
        """
        Appropriately capitalize any uses of keywords (e.g. PsychoPy rather
        than psychopy) in a given phrase

        Parameters
        ----------
        phrase : str, re.Match
            Phrase to process. If called from `re.sub`, will extract first match.
        """
        # if being called from re.sub, use the first match
        if isinstance(phrase, re.Match):
            phrase = phrase[1]

        for pattern, repl in TestStyle.keywords.items():
            # replace any keywords which are an entire word
            phrase = re.sub(pattern=(
                f"(?<= )({pattern})(?= )"  # space before and after
                f"|(?<= )({pattern})$"  # space before and line end after
                f"|(?<= )({pattern})(?=[^\w\s]+)"  # space before and punctuation after
                f"|^({pattern})(?= )"  # line start before and space after
                f"|^({pattern})(?=[^\w\s]+)"  # line start before and punctuation after
                f"|^({pattern})$"  # line start before and line end after
            ), string=phrase, repl=repl)

        return phrase

    def test_case(self):
        """
        Labels should all be in `Sentence case` - first word (and first word after
        full stop) capitalized, the rest lower. Apart from keywords.
        """
        def _validate(compName, paramName, value, sanitized):
            # # uncomment this and comment the assertion to make substitutions now
            # content = case['file'].read_text()
            # content = re.sub(
            #     pattern=(
            #         r"(?<=_translate\()[\"']"
            #         + re.escape(value) +
            #         r"[\"'](?=\))"
            #     ),
            #     string=content,
            #     repl='"' + sanitized + '"'
            # )
            # case['file'].write_text(content)
            # check value
            assert value == sanitized, (
                f"Found incorrect case in label/hint for param {paramName} "
                f"of {compName}: wanted '{sanitized}', got '{value}'."
            )
        for case in self.cases:
            # iterate through params from instance
            for paramName, param in case['instance'].params.items():
                # check that hint has keywords capitalized
                sanitizedHint = self.capitalizeKeywords(param.hint)
                _validate(
                    compName=case['name'],
                    paramName=paramName,
                    value=param.hint,
                    sanitized=sanitizedHint,
                )
                # check that label is in sentence case with keywords capitalized
                sanitizedLabel = self.capitalizeKeywords(param.label.capitalize())
                _validate(
                    compName=case['name'],
                    paramName=paramName,
                    value=param.label,
                    sanitized=sanitizedLabel,
                )

    def test_localized_deprecation(self):
        """
        Make sure that new components are using _translate rather than _localized
        """
        for case in self.cases:
            # get file contents
            content = case['file'].read_text()
            # look for _localized
            isLocalized = re.compile(
                r"(_localized\[)"
                r"([^\]]*)"
                r"(\])"
            )
            # make sure we don't use _localize
            assert not re.findall(
                pattern=isLocalized,
                string=content
            ), "Use of _localized found in %(file)s." % case


def test_param_str():
    """
    Test that params convert to str as expected in both Python and JS
    """
    sl = "\\"
    cases = [
        # Regular string
        {"obj": Param("Hello there", "str"),
         "py": f"{_q}Hello there{_q}",
         "js": f"{_q}Hello there{_q}"},
        # Enforced string
        {"obj": Param("\\, | or /", "str", canBePath=False),
         "py": f"{_q}{_sl}, \| or /{_q}",
         "js": f"{_q}{_sl}, \| or /{_q}"},
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
        {"obj": Param("C:/Downloads/file.ext", "file"),
         "py": f"{_q}C:/Downloads/file.ext{_q}",
         "js": f"{_q}C:/Downloads/file.ext{_q}"},
        # Table path
        {"obj": Param("C:/Downloads/file.csv", "table"),
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
         "py": f"for x in y:\n\tprint{_lb}y{_rb}",
         "js": f"for x in y:\n\tprint{_lb}y{_rb}"},  # this will change when snipped2js is fully working
        # List
        {"obj": Param("1, 2, 3", "list"),
         "py": f"{_lb}1, 2, 3{_rb}",
         "js": f"{_lb}1, 2, 3{_rb}"},
        # Extant file path marked as str
        {"obj": Param(__file__, "str"),
         "py": f"{_q}{__file__.replace(sl, '/')}{_q}",
         "js": f"{_q}{__file__.replace(sl, '/')}{_q}"},
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
         "py": f"{_q}This costs {_d}4.20{_q}",
         "js": f"{_q}This costs {_d}4.20{_q}"},
        # Unescaped \ in str
        {"obj": Param("This \\ that", "str"),
         "py": f"{_q}This {_sl} that{_q}",
         "js": f"{_q}This {_sl} that{_q}"},
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
         'py': f"{_lb}{_q}left{_q}{_rb}"},
        # Single value list syntax
        {'obj': Param("[\"left\"]", "list"),
         'py': f"{_lb}{_q}left{_q}{_rb}"},
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
        if "py" in case:
            exputils.scriptTarget = "PsychoPy"
            assert re.fullmatch(case['py'], str(case['obj'])), \
                f"`{repr(case['obj'])}` should match the regex `{case['py']}`, but it was `{case['obj']}`"
        # Test JS
        if "js" in case:
            exputils.scriptTarget = "PsychoJS"
            assert re.fullmatch(case['js'], str(case['obj'])), \
                f"`{repr(case['obj'])}` should match the regex `{case['js']}`, but it was `{case['obj']}`"
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
        {'val': "$hello \\$there",
         'ans': r"hello \\\$there",
         'valid': False},
        # Just redundant dollar
        {'val': "hello $there",
         'ans': f"hello {_d}there",
         'valid': False},
        # Just escaped dollar
        {'val': "\\$hello there",
         'ans': r"\\\$hello there",
         'valid': True},
        # Dollar in comment
        {'val': "#$hello there",
         'ans': r"#\$hello there",
         'valid': False},
        # Comment after dollar
        {'val': "$#hello there",
         'ans': r"#hello there",
         'valid': True},
        # Dollar and comment
        {'val': "$hello #there",
         'ans': r"hello #there",
         'valid': True},
        # Valid dollar and redundtant dollar in comment
        {'val': "$hello #$there",
         'ans': r"hello #\$there",
         'valid': True},
        # Valid dollar and escaped dollar in escaped d quotes
        {'val': "$hello \"\\$there\"",
         'ans': f"hello {_q}" + r"\\\$" + f"there{_q}",
         'valid': True},
        # Valid dollar and escaped dollar in escaped s quotes
        {'val': "$hello \'\\$there\'",
         'ans': f"hello {_q}" + r"\\\$" + f"there{_q}",
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
