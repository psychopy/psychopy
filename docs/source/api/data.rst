:mod:`psychopy.data` - functions for storing/saving/analysing data
==============================================================================

.. automodule:: psychopy.data

Contents:

- :class:`ExperimentHandler` - to combine multiple loops in one study
- :class:`TrialHandler` - basic predefined trial matrix
- :class:`TrialHandler2` - similar to TrialHandler but with ability to update mid-run
- :class:`StairHandler` - for basic up-down (fixed step) staircases
- :class:`QuestHandler` - for traditional QUEST algorithm
- :class:`QuestPlusHandler` - for the updated QUEST+ algorithm (Watson, 2017)
- :class:`PsiHandler` - the Psi staircase of Kontsevich & Tyler (1999)
- :class:`MultiStairHandler` - a wrapper to combine interleaved staircases of any sort

Utility functions:

- :func:`importConditions` - to load a list of dicts from a csv/excel file
- :func:`functionFromStaircase`- to convert a staircase into its psychopmetric function
- :func:`bootStraps` - generate a set of bootstrap resamples from a dataset

Curve Fitting:

- :class:`FitWeibull`
- :class:`FitLogistic`
- :class:`FitNakaRushton`
- :class:`FitCumNormal`

-----------------------

:class:`ExperimentHandler`
---------------------------------------------------------------------------
.. autoclass:: psychopy.data.ExperimentHandler
    :members:
    :undoc-members:
    :inherited-members:
    
:class:`TrialHandler`
---------------------------------------------------------------------------
.. autoclass:: psychopy.data.TrialHandler
    :members:
    :undoc-members:
    :inherited-members:

:class:`TrialHandler2`
---------------------------------------------------------------------------
.. autoclass:: psychopy.data.TrialHandler2
    :members:
    :undoc-members:
    :inherited-members:

:class:`StairHandler`
---------------------------------------------------------------------------
.. autoclass:: psychopy.data.StairHandler
    :members:
    :undoc-members:
    :inherited-members:

:class:`PsiHandler`
---------------------------------------------------------------------------
.. autoclass:: psychopy.data.PsiHandler
    :members:
    :undoc-members:
    :inherited-members:

:class:`QuestHandler`
---------------------------------------------------------------------------
.. autoclass:: psychopy.data.QuestHandler
    :members:
    :undoc-members:
    :inherited-members:

:class:`QuestPlusHandler`
---------------------------------------------------------------------------
.. autoclass:: psychopy.data.QuestPlusHandler
    :members:
    :undoc-members:
    :inherited-members:

:class:`MultiStairHandler`
---------------------------------------------------------------------------
.. autoclass:: psychopy.data.MultiStairHandler
    :members:
    :undoc-members:
    :inherited-members:

:class:`FitWeibull`
---------------------------------------------------------------------------------
.. autoclass:: psychopy.data.FitWeibull
    :members:
    :undoc-members:
    :inherited-members:
    
:class:`FitLogistic`
---------------------------------------------------------------------------------
.. autoclass:: psychopy.data.FitLogistic
    :members:
    :undoc-members:
    :inherited-members:

:class:`FitNakaRushton`
---------------------------------------------------------------------------------
.. autoclass:: psychopy.data.FitNakaRushton
    :members:
    :undoc-members:
    :inherited-members:

:class:`FitCumNormal`
---------------------------------------------------------------------------------
.. autoclass:: psychopy.data.FitCumNormal
    :members:
    :undoc-members:
    :inherited-members:
    
:func:`importConditions`
----------------------------------
.. autofunction:: psychopy.data.importConditions

:func:`functionFromStaircase`
----------------------------------
.. autofunction:: psychopy.data.functionFromStaircase

:func:`bootStraps`
--------------------------------
.. autofunction:: psychopy.data.bootStraps