# Blocking trials in PsychoPy Builder

This demo shows you how to use image files (with a **relative** reference to the file path. It also shows you how to arrange trials by block. People often want to create blocks of trials and randomise the order of the blocks. This shows you how to do that 

## The experiment: 

This isn't really an experiment - within each `trial` we just present an image for a short period and then carry on. In this case there is a block of 3 `trials` about faces and then a block of 3 trials about houses. The blocks are randomised as are the images within each block (although you could set either to have a fixed order if you prefer).

## Using images:

The images are being changed each trial just like any other variable attribute (if they're very large then load them in a `Static Period` but that isn't the topic here. You can see the way the files are specified in the facesBlock.csv file (or equivalent houses file). I've put all the image files into a subfolder to keep things neat.

## Creating blocks:

The thing that people get wrong here is they try to create a Routine for each block. In the case here it would be tempting to have a Routine called `PresentHouse` and another for `PresentFace`. What you should really do is:
- create a single Routine for `presentImage`
- use an inner `trials` loop that selects the image to present based on an excel file that varies according to the block (facesBlock.csv and housesBlock.csv conditions files)
- add an extra `blocks` loop that chooses each time which of the file to load using a variable called `trialConds` (see that in the chooseBlock.csv file)