#!/usr/bin/env python
# -*- coding: utf-8 -*-

# Various string functions for working with strings.
#

# Part of the PsychoPy library
# Copyright (C) 2002-2018 Jonathan Peirce (C) 2019-2020 Open Science Tools Ltd.
# Distributed under the terms of the GNU General Public License (GPL).

import re
import ast

__all__ = ["prettyname"]

# Regex for identifying a valid Pavlovia project name
valid_proj_name = re.compile(r'(\w|-)+')


def makeValidVarName(name, case="camel"):
    """
    Transform a string into a valid variable name

    Parameters
    ----------
    name : str
        Original name to be transformed
    case : str
        Case style for variable name to be in. Options are:
        upper: UPPERCASE
        title: TitleCase
        camel: camelCase
        snake: snake_case
        lower: lowercase
    """
    # Mark which underscores which need preserving
    private = name.startswith("_")
    protected = name.startswith("__")
    core = name.endswith("__")
    # Replace all different wordbreaks with _
    for wb in (" ", ".", ","):
        name = name.replace(wb, "_")
    # Insert a _ between lower/upper pairs and char/number pairs
    lastChar = ""
    processed = ""
    for c in name:
        # Insert a _ if...
        if any([
            lastChar.islower() and c.isupper(),  # previous char was lower and this is upper
            lastChar.isnumeric() and c.isalpha(),  # previous char was a number and this is a letter
            lastChar.isalpha() and c.isnumeric(),  # previous char was a letter and this is a number
        ]):
            processed += "_"
        # Append char
        processed += c
        # Store last char
        lastChar = c
    name = processed
    # Remove non-word characters
    processed = ""
    for c in name:
        if c.isidentifier() or c.isdecimal():
            processed += c
        else:
            processed += "_"
    name = processed
    # Split by underscore
    name = name.split("_")
    name = [word for word in name if len(word)]
    # Remove numbers from start
    while name[0].isnumeric():
        name = name[1:]
    # Process each word
    processed = []
    for i, word in enumerate(name):
        # Handle case
        word = word.lower()
        if case in ("upper"):
            word = word.upper()
        if case in ("title", "camel"):
            if case == "camel" and i == 0:
                word = word.lower()
            else:
                word = word.title()
        if case in ("snake", "lower"):
            word = word.lower()
        # Append word
        processed.append(word)
    name = processed
    # Recombine
    if case == "snake":
        name = "_".join(name)
    else:
        name = "".join(name)
    # Add special underscores
    if private:
        # If private, prepend _
        name = "_" + name
    if protected:
        # If also protected, prepend another _
        name = "_" + name
    if core:
        # If styled like a core variable (e.g. __file__), append __
        name = name + "__"
    return name



def prettyname(name, wrap=False):
    """Convert a camelCase, TitleCase or underscore_delineated title to Full Title Case"""
    # Replace _ with space
    name = name.replace("_", " ")
    # Put a space before any capital letter, apart from at the beginning, or already after a space
    name = name[0] + re.sub('(?<![ -.])([A-Z])', r' \1', name[1:])
    # Capitalise first letter of each word
    name = name.title()
    # Treat the word "PsychoPy" as a special case
    name = name.replace("Psycho Py", "PsychoPy")
    # Split into multiple lines if wrap is requested
    if wrap:
        sentence = []
        letter = 0
        # Iterate through each word
        for n, word in enumerate(name.split(" ")):
            # Count its letters
            letter += len(word)
            if letter > wrap and n > 0:
                # If this brings the current letters this line to more than the wrap limit, insert a line break
                sentence.append("\n")
                letter = len(word)
            # Insert word
            sentence.append(word)
        # Recombine name
        name = " ".join(sentence)
        # Remove spaces after line
        name = re.sub(r" *\n *", "\n", name)

    return name


def _actualizeAstValue(item):
    """
    Convert an AST value node to a usable Python object
    """
    if isinstance(item, ast.Str):
        # Handle ast string
        return item.s
    elif hasattr(ast, 'Bytes') and isinstance(item, ast.Bytes):
        # Handle ast bytes
        return item.s
    elif isinstance(item, ast.Num):
        # Handle ast numbers
        return item.n
    elif isinstance(item, ast.Tuple):
        # Handle ast array
        return tuple(_actualizeAstValue(i) for i in item.elts)


def getVariables(code):
    """
    Use AST tree parsing to convert a string of valid Python code to a dict containing each variable created and its
    value.
    """
    assert isinstance(code, str), "First input to `getArgs()` must be a string"
    # Make blank output dict
    vars = {}
    # Construct tree
    tree = compile(code, '', 'exec', flags=ast.PyCF_ONLY_AST)
    # Iterate through each line
    for line in tree.body:
        if hasattr(line, "targets") and hasattr(line, "value"):
            # Append targets and values this line to arguments dict
            for target in line.targets:
                if hasattr(target, "id"):
                    vars[target.id] = _actualizeAstValue(line.value)

    return vars


def getArgs(code):
    """
    Use AST tree parsing to convert a string of valid Python arguments to a dict containing each argument used and its
    value.
    """
    assert isinstance(code, str), "First input to `getArgs()` must be a string"
    # Make blank output dict
    args = {}
    # Add outer brackets if needed
    if not (code.startswith("(") and code.endswith(")")):
        code = "(" + code + ")"
    # Move it all to one line
    code = code.replace("\n", "")
    # Append dict constructor
    code = "dict" + code
    # Construct tree
    tree = compile(code, '', 'exec', flags=ast.PyCF_ONLY_AST)
    # Get keywords
    keywords = tree.body[0].value.keywords
    for kw in keywords:
        if hasattr(kw, "arg") and hasattr(kw, "value"):
            # Append keyword and value to arguments dict
            args[kw.arg] = _actualizeAstValue(kw.value)

    return args
