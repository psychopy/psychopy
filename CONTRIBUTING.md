For simple changes, and for users that aren't so confident with things like version control systems, you may just post your idead and changes to the [PsychoPy forum](https://discourse.psychopy.org).

If you want to make more substantial changes, please discuss them first on the in the [development section of the forum](https://discourse.psychopy.org/c/dev) or in a new [GitHub issue](https://github.com/psychopy/psychopy/issues).

The ideal model is to contribute via the PsychoPy GitHub repository. There is more information on that in the [developers](https://github.com/psychopy/psychopy/blob/master/docs/source/developers/developers.rst) section of the documentation.

Pleas not the importance of a good commit message and **please use the following tags in your commit**:

  - BF : bug fix
  - FF : ‘feature’ fix. This is for fixes to code that hasn’t been released
  - RF : refactoring
  - NF : new feature
  - ENH : enhancement (to existing code, but don't worry too much about the diff between this and NF)
  - DOC: for all kinds of documentation related commits
  - TEST: for adding or changing tests

Very importantly, **the difference between BF and FF** is that BF indicates a fix that is appropriate for back-porting to earlier release streams, whereas FF indicates a fix to code that has not been released, and so should not be back-ported. So, if you incorrectly tag a bug fix as FIX then it won't be included in a bug-fix release, only in the next major release.
If you're unsure whether one of your changes is a BF or FF, feel free to ask.
