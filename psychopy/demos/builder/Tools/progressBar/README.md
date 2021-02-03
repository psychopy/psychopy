# Progress Bar

This demo contains an easily reusable progress bar, which shows how far the participant has got through the current loop. Please feel free to copy this to your own experiments!

## How it works

The important parts are the Variable component `progress` and the Polygon component `progBar`. Each repeat, the variable `progress` is set to equal the current trial number divided by the number of trials - in other words, how far the participant has gotten, as a decimal. The width the `progBar` is set to the value `progress` each repeat, so it grows as trials progress. `progBar`'s x position also changes to be half of this value, meaning that the bar is essentially anchored by its left side.