Drag and Drop Demo
==================
The demonstration uses a drag and drop puzzle game. 

## Updated demo
This task uses the `draggable` attribute to allow components such as polygons and images to be dragged across the window. Compared to the archived demo, this reduces the amount of code required to allow stimuli to be draggable.

**Note:** The `draggable` attribute currently can only be used locally (*available from 2023.2.0*) but will be available for online use in future versions.

This task saves which space the square is dropped in so you can then compare it with the original design.

To generate more designs, you can use `draw grid stim.py` from Coder which allows more flexible parameters when creating grids compared to the archived `shapeMaker.psyexp`.


## Archived demo - set nReps to 1 in archived_trials loop to run demo

The task requires you to drag and drop the black and white pieces into the empty square in order to match the puzzle presented above the empty square. 
When you have finished, press the "Continue" button to see whether or not you were correct, and how long the trial took.

To generate more designs, you can run the shapeMaker.psyexp task from Builder. When you run the shapeMaker task, you will be asked for a number of rows. You can choose either 2 or 3 rows for 4 or 9 piece shapes, respectively. Each shape consists of a grid in the following orders. 

### For 4 piece shapes
| 1 | 2 |
| --| --|
| 3 | 4 |

### For 9 piece shapes
| 1 | 2 | 3 |
| --| --| --|
| 4 | 5 | 6 |
| 7 | 8 | 9 |

The answers for each new shape need to be added the the conditions file, where columns `a1` to `a9` relate to the shape grid locations as described above. E.g., `a1` relates to space 1 in the grid. So, for an all white shape created using 2 rows (so a 4 piece shape),  you would enter `"white.png"` in columns `a1` to `a4` in the conditions file, 
and leave the rest of the cells for that row blank.

## Online demo of the task

You can try the online version of the task here https://run.pavlovia.org/demos/draganddrop/

**Note:** This currently uses the archived version of the demo.