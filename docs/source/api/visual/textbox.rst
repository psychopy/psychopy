:class:`TextBox`
-----------------

.. warning::

    TextBox is deprecated. Please use :class:`~psychopy.visual.TextBox2` instead which supports similar
    editable high-performance rendering of text but also supports non-monospaced
    fonts and a wider range of formatting and alignment options. This is a lazy-imported class, therefore
    import using full path `from psychopy.visual.textbox import TextBox` when inheriting from it.

Attributes
==========

.. currentmodule:: psychopy.visual

.. autosummary::

    TextBox

**The following `set______()` attributes all have equivalent `get______()`
attributes:**

.. autosummary::

    TextBox.setText
    TextBox.setPosition
    TextBox.setHorzAlign
    TextBox.setVertAlign
    TextBox.setHorzJust
    TextBox.setVertJust
    TextBox.setFontColor
    TextBox.setBorderColor
    TextBox.setBackgroundColor
    TextBox.setTextGridLineColor
    TextBox.setTextGridLineWidth
    TextBox.setInterpolated
    TextBox.setOpacity
    TextBox.setAutoLog
    TextBox.draw

**TextBox also provides the following read-only functions:**

.. autosummary::

    TextBox.getSize
    TextBox.getName
    TextBox.getDisplayedText
    TextBox.getValidStrokeWidths
    TextBox.getLineSpacing
    TextBox.getGlyphPositionForTextIndex
    TextBox.getTextGridCellPlacement

Helper Functions
================

**getFontManager()**

`FontManager` provides a simple API for finding and loading font files (.ttf)
via the FreeType library.

The FontManager finds supported font files on the computer and initially creates
a dictionary containing the information about available fonts. This can be used
to quickly determine what font family names are available on the computer and
what styles (bold, italic) are supported for each family.

This font information can then be used to create the resources necessary to
display text using a given font family, style, size, color, and dpi.

The `FontManager` is currently used by the psychopy.visual.TextBox stim type. A
user script can access the `FontManager` via::

    font_mngr=visual.textbox.getFontManager()

Once a font of a given size and dpi has been created; it is cached by the
`FontManager` and can be used by all `TextBox` instances created within the
experiment.


Details
=======

.. autoclass:: TextBox
    :members:
    :undoc-members:
    :inherited-members:
