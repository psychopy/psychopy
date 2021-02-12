# Drag and drop demonstration

This task shows you the drag and drop capabilities of PsychoPy and PsychoJS. The demonstration uses a drag and drop puzzle game. 

The task requires you to drag and drop the black and white pieces into the empty square in order to match the puzzle presented above the empty square. When you have finished, press the "Continue" button to see whether or not you were correct, and how long the trial took.

To generate more designs, you can run the `shapeMaker.psyexp` task from Builder. When you run the `shapeMaker` task, you will be asked for a number of rows. You can choose either 2 or 3 rows for 4 or 9 piece shapes, respectively. Each shape consists of a grid in the following orders:

### For 4 piece shapes
```
| 1 | 2 |
| 3 | 4 |
```

### For 9 piece shapes
```
| 1 | 2 | 3 |
| 4 | 5 | 6 |
| 7 | 8 | 9 |
```

The answers for each new shape need to be added the the conditions file, where columns
a1 to a9 relate to the shape grid locations as described above. e.g. `a1` relates to space 1
in the grid. So, for an all white shape created using 2 rows (so a 4 piece shape), 
you would enter "white.png" in columns a1 to a4 in the conditions file, 
and leave the rest of the cells for that row blank.

You can run this task from Pavlovia by going to:

https://run.pavlovia.org/demos/draganddrop/html/