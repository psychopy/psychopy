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
import urllib
from pathlib import Path

valid_proj_name = re.compile(r'(\w|-)+')


def is_url(source):
    """
    Check whether a string is a valid url.
    """
    # Make sure source is a string
    source = str(source)
    # Try to parse source, return False if it fails
    try:
        url = urllib.parse.urlparse(source)
    except ValueError:
        return False
    # If parsed successfully, return True if we have a scheme and net location
    return all((url.scheme, url.netloc))


def is_file(source):
    """
    Check whether a string or Path object is a valid file.
    """
    # If source is already a Path, just use its is_file method
    if isinstance(source, Path):
        return source.is_file()
    # Make sure source is a string
    source = str(source)
    # Try to create a Path object, return False if it fails
    try:
        path = Path(source)
    except ValueError:
        return False
    # If creates successfully, return True if is_file
    try:
        isFile = path.is_file()
    except OSError:
        isFile = False
    return isFile


class CaseSwitcher:
    """
    Collection of static methods for switching case in strings. Can currently convert between:
    - camelCase
    - PascalCase
    - Title Case
    """

    @staticmethod
    def camel2pascal(value):
        """
        Convert from camelCase to PascalCase
        """
        # capitalise first letter
        value = value[0].upper() + value[1:]

        return value

    @staticmethod
    def camel2title(value):
        """
        Convert from camelCase to Title Case
        """
        # convert to pascal
        value = CaseSwitcher.camel2pascal(value)
        # convert to title
        value = CaseSwitcher.pascal2title(value)

        return value

    @staticmethod
    def camel2snake(value):
        """
        Convert from camelCase to snake_case
        """
        # convert to title
        value = CaseSwitcher.camel2title(value)
        # convert to snake
        value = CaseSwitcher.title2snake(value)

        return value

    @staticmethod
    def pascal2camel(value):
        """
        Convert from PascalCase to camelCase
        """
        # decapitalise first letter
        value = value[0].lower() + value[1:]

        return value

    @staticmethod
    def pascal2title(value):
        """
        Convert from PascalCase to Title Case
        """
        def _titleize(match):
            """
            Replace a regex match for a lowercase letter followed by an uppercase letter with the same two letters, in
            uppercase, with a space inbetween.
            """
            # get matching text (should be a lower case letter then an upper case letter)
            txt = match[0]
            # add a space
            txt = txt[0] + " " + txt[1]

            return txt
        # make regex substitution
        value = re.sub(
            pattern=r"([a-z][A-Z])",
            repl=_titleize,
            string=value
        )

        return value

    @staticmethod
    def pascal2snake(value):
        """
        Convert from PascalCase to snake_case
        """
        # convert to title
        value = CaseSwitcher.pascal2title(value)
        # convert to snake
        value = CaseSwitcher.title2snake(value)

        return value

    @staticmethod
    def title2camel(value):
        """
        Convert from Title Case to camelCase
        """
        # convert to pascal
        value = CaseSwitcher.title2pascal(value)
        # convert to camel
        value = CaseSwitcher.pascal2camel(value)

        return value

    @staticmethod
    def title2pascal(value):
        """
        Convert from Title Case to PascalCase
        """
        # remove spaces
        value = value.replace(" ", "")

        return value

    @staticmethod
    def title2snake(value):
        """
        Convert from Title Case to snake_case
        """
        # lowercase
        value = value.lower()
        # replace spaces with underscores
        value = value.replace(" ", "_")

        return value

    @staticmethod
    def snake2camel(value):
        """
        Convert from snake_case to camelCase
        """
        # convert to pascal
        value = CaseSwitcher.snake2pascal(value)
        # convert to camel
        value = CaseSwitcher.pascal2camel(value)

        return value

    @staticmethod
    def snake2pascal(value):
        """
        Convert from snake_case to PascalCase
        """
        # convert to title
        value = CaseSwitcher.snake2title(value)
        # convert to pascal
        value = CaseSwitcher.title2pascal(value)

        return value

    @staticmethod
    def snake2title(value):
        """
        Convert from snake_case to Title Case
        """
        def _titleize(match):
            """
            Replace a regex match for a lowercase letter followed by an uppercase letter with the same two letters, in
            uppercase, with a space inbetween.
            """
            # get matching text (should be a lower case letter then an upper case letter)
            txt = match[0]
            # add a space and capitalise
            txt = " " + txt[1].upper()

            return txt
        # make regex substitution
        value = re.sub(
            pattern=r"(_[a-z])",
            repl=_titleize,
            string=value
        )
        # capitalise first letter
        value = value[0].upper() + value[1:]

        return value


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
