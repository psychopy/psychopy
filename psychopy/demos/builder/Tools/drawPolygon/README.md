# Drawing A Polygon

In PsychoPy, you can create Polygon components of any shape by setting their "vertices" attribute to an array of coordinates. This essentially is telling PsychoPy where to put the corners - it will then draw lines between them in order and fill in the middle.

This can be difficult to visualise, so this demo allows you to draw a Polygon using your mouse, then see how it's affected by changes to size, position and orientation. The data output from this demo contains a column "vertices" - this is the vertices of the Polygon you created, you can use this value in a Code component to set the vertices of polygons in your experiment by setting the `.vertices` attribute.