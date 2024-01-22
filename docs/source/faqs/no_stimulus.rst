Why is my stimulus not showing?
=====================================

If your stimulus in PsychoPy isn't displaying and there’s no error message, consider these often overlooked factors:

**Units Setting:**

The units used for your stimulus (e.g., pixels, height, norm) can significantly impact its display. If the units are set incorrectly, the stimulus might be too small or positioned off-screen. For example, specifying a stimulus size in pixels when your experiment uses height units could result in an inappropriately scaled stimulus.

**Duplicate Variable Names in Conditions File:**

Using the same name for a variable in your conditions file and a component in your experiment can lead to conflicts. For instance, if you have an image component named 'image' and also a column in your conditions file named 'image', PsychoPy may get confused when trying to present the 'image' variable. This doesn't typically generate an error, but it can result in your stimulus not being displayed as expected. To avoid this, ensure that your variable names in the conditions file are unique and not identical to any of your component names.