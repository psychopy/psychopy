#!/usr/bin/env python2
# -*- coding: utf-8 -*-

from distutils.version import StrictVersion

from .base import DataHandler
from .experiment import ExperimentHandler
from .trial import TrialHandler, TrialHandler2, TrialHandlerExt, TrialType
from .staircase import (StairHandler, QuestHandler, PsiHandler,
                        MultiStairHandler)

from .utils import (checkValidFilePath, isValidVariableName, importTrialTypes,
                    sliceFromString, indicesFromString, importConditions,
                    createFactorialTrialList, bootStraps, functionFromStaircase,
                    getDateStr)

from .fit import (FitFunction, FitCumNormal, FitLogistic, FitNakaRushton,
                  FitWeibull)

try:
    # import openpyxl
    import openpyxl
    if StrictVersion(openpyxl.__version__) >= StrictVersion('2.4.0'):
        # openpyxl moved get_column_letter to utils.cell
        from openpyxl.utils.cell import get_column_letter
    else:
        from openpyxl.cell import get_column_letter
    from openpyxl.reader.excel import load_workbook
    haveOpenpyxl = True
except ImportError:
    haveOpenpyxl = False

try:
    import xlrd
    haveXlrd = True
except ImportError:
    haveXlrd = False
