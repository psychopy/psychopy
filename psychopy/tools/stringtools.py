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
