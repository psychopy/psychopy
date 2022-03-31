import ast
from collections import OrderedDict

import esprima
import pandas as pd
from copy import deepcopy
from pathlib import Path


def measure_js_parity(pypath, jspath, outpath=None):
    """
    Get all methods and attributes for classes in psychopy.visual and psychojs.visual, for comparison
    """
    def _listcomp(a, b):
        """
        Convenience function for quickly getting arrays of differences between two lists (a and b).

        Returns
        ===
        justa : list
            Elements only present in list a
        justb : list
            Elements only present in b
        both : list
            Elements present in both lists
        """
        # Get as sets
        a = set(a)
        b = set(b)
        # Do comparison
        justa = list(a.difference(b))
        justb = list(b.difference(a))
        both = list(a & b)
        either = list(a | b)

        return justa, justb, both, either

    # Pathify paths
    pypath = Path(pypath)
    jspath = Path(jspath)
    # Dict with classes & filenames for visual components which exist in PsychoPy and PsychoJS
    attrs = {
        "ButtonStim": {
            'js': {'file': 'ButtonStim.js', 'cls': "ButtonStim"},
            'py': {'file': 'button.py', 'cls': "ButtonStim"},
        },
        "Form": {
            'js': {'file': 'Form.js', 'cls': "Form"},
            'py': {'file': 'form.py', 'cls': "Form"},
        },
        "ImageStim": {
            'js': {'file': 'ImageStim.js', 'cls': "ImageStim"},
            'py': {'file': 'image.py', 'cls': "ImageStim"},
        },
        "MovieStim3": {
            'js': {'file': 'MovieStim.js', 'cls': "MovieStim"},
            'py': {'file': 'movie3.py', 'cls': "MovieStim3"},
        },
        "Polygon": {
            'js': {'file': 'Polygon.js', 'cls': "Polygon"},
            'py': {'file': 'polygon.py', 'cls': "Polygon"}
        },
        "Rect": {
            'js': {'file': 'Rect.js', 'cls': "Rect"},
            'py': {'file': 'rect.py', 'cls': "Rect"}
        },
        "ShapeStim": {
            'js': {'file': 'ShapeStim.js', 'cls': "ShapeStim"},
            'py': {'file': 'shape.py', 'cls': "ShapeStim"}
        },
        "Slider": {
            'js': {'file': 'Slider.js', 'cls': "Slider"},
            'py': {'file': 'slider.py', 'cls': "Slider"}
        },
        "TextBox2": {
            'js': {'file': 'TextBox.js', 'cls': "TextBox"},
            'py': {'file': 'textbox2/textbox2.py', 'cls': "TextBox2"}
        },
        "TextStim": {
            'js': {'file': 'TextStim.js', 'cls': "TextStim"},
            'py': {'file': 'text.py', 'cls': "TextStim"}
        },
        "BaseVisualStim": {
            'js': {'file': 'VisualStim.js', 'cls': "VisualStim"},
            'py': {'file': 'basevisual.py', 'cls': "BaseVisualStim"}
        },
    }
    # Create blank output arrays
    for name in attrs:
        # Create output array
        arr = {'init': [], 'methods': {}, 'attribs': {}}
        # Append to js and py
        attrs[name]['js'].update(deepcopy(arr))
        attrs[name]['py'].update(deepcopy(arr))

    # For each class, get dicts of methods and attributes
    for name in attrs:

        # --- Parse JS file ---
        
        with open(jspath / attrs[name]['js']['file'], 'r') as f:
            code = f.read()
        tree = esprima.parse(code, sourceType='module')
        # Get class def
        cls = None
        for node in tree.body:
            if node.type == "ExportNamedDeclaration":
                if node.declaration.type == "ClassDeclaration" and node.declaration.id.name == attrs[name]['js']['cls']:
                    cls = node
        if cls is None:
            raise ValueError(f"Could not find class def for {attrs[name]['js']['cls']} in {attrs[name]['js']['file']}")
        # Get methods & properties
        for node in cls.declaration.body.body:
            if node.value.type == "FunctionExpression":
                # Get flattened list of params
                paramNames = []
                for param in node.value.params:
                    if param.type == "AssignmentPattern":
                        # If parameter is a dict style assignment pattern, break it apart
                        if param.left.type == "ObjectPattern":
                            for prop in param.left.properties:
                                paramNames.append(prop.key.name)
                        # If parameter is an expression, store name
                        elif param.left.type == "Identifier":
                            paramNames.append(param.left.name)
                    elif param.type == "Identifier":
                        paramNames.append(param.name)

                # Skip protected methods
                if node.key.name is None or node.key.name.startswith("_"):
                    continue
                # If it's the constructor method, store params
                if node.kind == "constructor":
                    attrs[name]['js']['init'] = paramNames
                # If it's a getter, store its name & whether it's settable
                elif node.kind == "get":
                    attrs[name]['js']['attribs'][node.key.name] = node.key.name in attrs[name]['js']['attribs']
                # If it's a setter, store its name & the fact that it's settable
                elif node.kind == "set":
                    attrs[name]['js']['attribs'][node.key.name] = True
                # If it's regular method, store its name and params
                elif node.kind == "method":
                    attrs[name]['js']['methods'][node.key.name] = paramNames

        # --- Parse Py file ---
        
        with open(pypath / attrs[name]['py']['file'], 'r') as f:
            code = f.read()
        tree = ast.parse(code)
        # Get class def
        cls = None
        for node in tree.body:
            if isinstance(node, ast.ClassDef) and node.name == attrs[name]['py']['cls']:
                cls = node
        if cls is None:
            raise ValueError(f"Could not find class def for {attrs[name]['py']['cls']} in {attrs[name]['py']['file']}")
        # Get methods and attributes
        for node in cls.body:
            if isinstance(node, ast.FunctionDef):
                # Get flattened list of params
                paramNames = []
                for param in node.args.args:
                    if param.arg == "self":
                        continue
                    paramNames.append(param.arg)

                # Get string list of decorators
                decorators = []
                for dec in node.decorator_list:
                    if isinstance(dec, ast.Name):
                        decorators.append(dec.id)
                    if isinstance(dec, ast.Attribute):
                        decorators.append(dec.attr)

                # If it's the constructor method, store params
                if node.name == "__init__":
                    attrs[name]['py']['init'] = paramNames
                # Skip protected methods
                elif node.name is None or node.name.startswith("_"):
                    continue
                # If it's a getter, store its name & whether it's settable
                elif "property" in decorators:
                    attrs[name]['py']['attribs'][node.name] = node.name in attrs[name]['py']['attribs']
                # If it's a setter, store its name & the fact that it's settable
                elif "setter" in decorators:
                    attrs[name]['py']['attribs'][node.name] = True
                # If it's regular method, store its name and params
                else:
                    attrs[name]['py']['methods'][node.name] = paramNames

    # --- Compare ---

    compr = {}
    # Iterate through components
    for name in attrs:
        # Add field to comparison dict
        compr[name] = OrderedDict({})

        # Compare init params, attributes and method names
        for key in ('init', 'attribs', 'methods'):
            # Get lists
            py = attrs[name]['py'][key]
            js = attrs[name]['js'][key]
            # Do comparison
            justpy, justjs, both, either = _listcomp(py, js)
            # Store in dict
            compr[name][f'{key}_both'] = both
            compr[name][f'{key}_py'] = justpy
            compr[name][f'{key}_js'] = justjs

        # Add empty column
        compr[name]['|||'] = []

        # Compare params for each method
        for key in compr[name][f'methods_both']:
            # Get lists
            py = attrs[name]['py']['methods'][key]
            js = attrs[name]['js']['methods'][key]
            # Do comparison
            justpy, justjs, both, either = _listcomp(py, js)
            # Store in dict
            compr[name][f'{key}_both'] = both
            compr[name][f'{key}_py'] = justpy
            compr[name][f'{key}_js'] = justjs

        # If asked to, save to a table
        if outpath:
            # Pathify output path
            outpath = Path(outpath)
            # Save csv's
            for name, data in compr.items():
                # Pad columns to max
                ncols = max([len(val) for val in data.values()])
                for n in range(ncols):
                    for key in data:
                        while len(data[key]) < ncols:
                            data[key].append(None)
                # Make a pandas dataframe
                df = pd.DataFrame(data)
                # Write to csv
                df.to_csv(outpath / f"{name}.csv")

    return attrs, compr
