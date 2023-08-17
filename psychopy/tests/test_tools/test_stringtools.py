# -*- coding: utf-8 -*-
"""Tests for psychopy.tools.mathtools
"""

from psychopy.tools import stringtools as tools
import pytest

@pytest.mark.stringtools
def test_name_wrap():
    exemplars = [
        {"text": "Hello There", "wrap": 12, "ans": "Hello There"},  # No wrap
        {"text": "Hello There", "wrap": 8, "ans": "Hello \nThere"},  # Basic wrap
        {"text": "Hello There Hello There Hello There", "wrap": 11, "ans": "Hello There \nHello There \nHello There"},  # Multiple wraps
    ]
    tykes = [
        {"text": "Eyetracker Calibration", "wrap": 10, "ans": "Eyetracker \nCalibration"},  # One word longer than wrap length
        {"text": "Hello There", "wrap": 1, "ans": "Hello \nThere"},  # Wrap = 1
        {"text": "Hello There", "wrap": 0, "ans": "Hello \nThere"},  # Wrap = 0
    ]
    for case in exemplars + tykes:
        assert tools.wrap(case['text'], case['wrap']) == case['ans']


@pytest.mark.stringtools
def test_get_variables():
    exemplars = [
        {"code": "x=1\ny=2", "ans": {'x': 1, 'y': 2}},  # numbers
        {"code": "x=\"a\"\ny=\"b\"", "ans": {'x': "a", 'y': "b"}},  # double quotes
        {"code": "x='a'\ny='b'", "ans": {'x': "a", 'y': "b"}},  # single quotes
        {"code": "x=(1, 2)\ny=(3, 4)", "ans": {'x': (1, 2), 'y': (3, 4)}},  # arrays
    ]
    tykes = [
        {"code": "x='(1, 2)'\ny='(3, 4)'", "ans": {'x': "(1, 2)", 'y': "(3, 4)"}},  # string representation of array (single)
        {"code": "x=\"(1, 2)\"\ny=\"(3, 4)\"", "ans": {'x': "(1, 2)", 'y': "(3, 4)"}},  # string representation of array (double)
    ]
    for case in exemplars + tykes:
        assert tools.getVariables(case['code']) == case['ans']


@pytest.mark.stringtools
def test_get_arguments():
    exemplars = [
        {"code": "x=1,y=2", "ans": {'x': 1, 'y': 2}},  # numbers
        {"code": "x=\"a\",y=\"b\"", "ans": {'x': "a", 'y': "b"}},  # double quotes
        {"code": "x='a',y='b'", "ans": {'x': "a", 'y': "b"}},  # single quotes
        {"code": "x=(1, 2), y=(3, 4)", "ans": {'x': (1, 2), 'y': (3, 4)}},  # arrays

    ]
    tykes = [
        {"code": "(x=1, y=2)", "ans": {'x': 1, 'y': 2}},  # outer brackets
        {"code": "x='(1, 2)', y='(3, 4)'", "ans": {'x': "(1, 2)", 'y': "(3, 4)"}},  # string representation of array (single)
        {"code": "x=\"(1, 2)\", y=\"(3, 4)\"", "ans": {'x': "(1, 2)", 'y': "(3, 4)"}},  # string representation of array (double)
    ]
    for case in exemplars + tykes:
        assert tools.getArgs(case['code']) == case['ans']


@pytest.mark.stringtools
def test_make_valid_name():
    cases = [
        # Already valid names
        {"in": "ALREADYVALIDUPPER", "case": "upper", "out": "ALREADYVALIDUPPER"},
        {"in": "AlreadyValidTitle", "case": "title", "out": "AlreadyValidTitle"},
        {"in": "alreadyValidCamel", "case": "camel", "out": "alreadyValidCamel"},
        {"in": "already_valid_snake", "case": "snake", "out": "already_valid_snake"},
        {"in": "alreadyvalidlower", "case": "lower", "out": "alreadyvalidlower"},
        # Sentence style names
        {"in": "make upper", "case": "upper", "out": "MAKEUPPER"},
        {"in": "make title", "case": "title", "out": "MakeTitle"},
        {"in": "make camel", "case": "camel", "out": "makeCamel"},
        {"in": "make snake", "case": "snake", "out": "make_snake"},
        {"in": "make lower", "case": "lower", "out": "makelower"},
        # Numbers on end
        {"in": "upper case 1", "case": "upper", "out": "UPPERCASE1"},
        {"in": "title case 2", "case": "title", "out": "TitleCase2"},
        {"in": "camel case 3", "case": "camel", "out": "camelCase3"},
        {"in": "snake case 4", "case": "snake", "out": "snake_case_4"},
        {"in": "lower case 5", "case": "lower", "out": "lowercase5"},
        # Numbers at start
        {"in": "1 upper case", "case": "upper", "out": "UPPERCASE"},
        {"in": "2 title case", "case": "title", "out": "TitleCase"},
        {"in": "3 camel case", "case": "camel", "out": "camelCase"},
        {"in": "4 snake case", "case": "snake", "out": "snake_case"},
        {"in": "5 lower case", "case": "lower", "out": "lowercase"},
        # Numbers inbetween
        {"in": "upper 1 case", "case": "upper", "out": "UPPER1CASE"},
        {"in": "title 2 case", "case": "title", "out": "Title2Case"},
        {"in": "camel 3 case", "case": "camel", "out": "camel3Case"},
        {"in": "snake 4 case", "case": "snake", "out": "snake_4_case"},
        {"in": "lower 5 case", "case": "lower", "out": "lower5case"},
        # Invalid chars
        {"in": "exclamation!mark", "case": "snake", "out": "exclamation_mark"},
        {"in": "question?mark", "case": "snake", "out": "question_mark"},
        # Protected/private/core syntax
        {"in": "_privateAttribute", "case": "snake", "out": "_private_attribute"},
        {"in": "_privateAttribute", "case": "camel", "out": "_privateAttribute"},
        {"in": "__protectedAttribute", "case": "snake", "out": "__protected_attribute"},
        {"in": "__protectedAttribute", "case": "camel", "out": "__protectedAttribute"},
        {"in": "__core__", "case": "snake", "out": "__core__"},
        {"in": "__core__", "case": "lower", "out": "__core__"},
        # Known tykes
    ]

    for case in cases:
        assert tools.makeValidVarName(name=case['in'], case=case['case']) == case['out']


def test_CaseSwitcher():

    cases = [
        # to camel
        {'fcn': "pascal2camel", 'in': "alreadyValidCamel", 'out': "alreadyValidCamel"},
        {'fcn': "title2camel", 'in': "alreadyValidCamel", 'out': "alreadyValidCamel"},
        {'fcn': "snake2camel", 'in': "alreadyValidCamel", 'out': "alreadyValidCamel"},
        {'fcn': "pascal2camel", 'in': "MakeCamel", 'out': "makeCamel"},
        {'fcn': "title2camel", 'in': "Make Camel", 'out': "makeCamel"},
        {'fcn': "snake2camel", 'in': "make_camel", 'out': "makeCamel"},
        # to pascal
        {'fcn': "camel2pascal", 'in': "AlreadyValidPascal", 'out': "AlreadyValidPascal"},
        {'fcn': "title2pascal", 'in': "AlreadyValidPascal", 'out': "AlreadyValidPascal"},
        {'fcn': "snake2pascal", 'in': "AlreadyValidPascal", 'out': "AlreadyValidPascal"},
        {'fcn': "camel2pascal", 'in': "makePascal", 'out': "MakePascal"},
        {'fcn': "title2pascal", 'in': "Make Pascal", 'out': "MakePascal"},
        {'fcn': "snake2pascal", 'in': "make_pascal", 'out': "MakePascal"},
        # to title
        {'fcn': "camel2title", 'in': "Already Valid Title", 'out': "Already Valid Title"},
        {'fcn': "pascal2title", 'in': "Already Valid Title", 'out': "Already Valid Title"},
        {'fcn': "snake2title", 'in': "Already Valid Title", 'out': "Already Valid Title"},
        {'fcn': "camel2title", 'in': "makeTitle", 'out': "Make Title"},
        {'fcn': "pascal2title", 'in': "MakeTitle", 'out': "Make Title"},
        {'fcn': "snake2title", 'in': "make_title", 'out': "Make Title"},
        # to snake
        {'fcn': "camel2snake", 'in': "already_valid_snake", 'out': "already_valid_snake"},
        {'fcn': "pascal2snake", 'in': "already_valid_snake", 'out': "already_valid_snake"},
        {'fcn': "title2snake", 'in': "already_valid_snake", 'out': "already_valid_snake"},
        {'fcn': "camel2snake", 'in': "makeSnake", 'out': "make_snake"},
        {'fcn': "pascal2snake", 'in': "MakeSnake", 'out': "make_snake"},
        {'fcn': "title2snake", 'in': "Make Snake", 'out': "make_snake"},
    ]

    for case in cases:
        # get function
        fcn = getattr(tools.CaseSwitcher, case['fcn'])
        # call function
        case['result'] = fcn(case['in'])
        # check result
        assert case['result'] == case['out'], "CaseSwitcher.{fcn}({in}) should be {out}, was {result}.".format(**case)
