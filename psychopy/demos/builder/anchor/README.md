# Understanding Anchors

If you're familiar with graphic design software like GIMP, Inkscape or Adobe Photoshop/Illustrator, then you may have encountered the concept of an "anchor" before. This demo will help you understand how anchors work in PsychoPy.

## An anchor is...

...essentially a point within a shape from which it is positioned. Let's say, for example, you make a square Polygon component in PsychoPy. You set its position to `(0,0)`, meaning it appears in the centre of the screen. But which part of the square is in the centre of the screen? Its midpoint? Its top left corner? If you rotate the square, what point does it rotate around?

The answer to all of these questions is its anchor! If the square's anchor is at its centre (as it is by default), then setting position to `(0,0)` means that the centre of the square is in the centre of the screen and that rotating the square will rotate it around its centre. 

## This demo is...

...designed to give a simple visual explanation for this - allowing you to use a slider to change the anchor of a simple stimulus, to see how doing so will affect its position. Hopefully bringing this concept out of the abstract by giving you a real, tangible demonstration of how it can be used!

