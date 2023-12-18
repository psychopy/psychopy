Why am I getting a variable not defined error?
===============================================

Receiving a "variable not defined" error in PsychoPy is a common issue, often resulting from a few specific causes. Here are some points to consider when troubleshooting this error:

**Capital Letters and Spaces in Variable Names:** Check your variable names for capital letters and spaces. PsychoPy is case-sensitive, meaning that "VariableName" and "variablename" are treated as different variables. Also, spaces in variable names are not allowed, so ensure your variable names are continuous strings.

**Variable Scope - 'Set Every Repeat':**

Ensure that your variables are set to update at the correct time. If a variable changes every trial, it should be set to ‘set every repeat’ in the component settings. This ensures the variable updates its value with each iteration of your experiment's loop, rather than right at the start of your experiment where it might not have been defined yet.

**Defining Variables in the 'Begin Experiment' Tab:**

A common mistake is placing code that relies on variables from condition files in the 'Begin Experiment' tab instead of the 'Begin Routine' tab. Variables read from condition files should typically be used in the 'Begin Routine' tab, as they are not yet available at the experiment’s start ('Begin Experiment'). Placing such code in the 'Begin Experiment' tab will result in a "variable not defined" error, as the variable has not been read in yet.

**Loop and Routine Configuration:**

Check if you’ve forgotten to wrap a loop around a routine or attach condition files correctly. Loops in PsychoPy are used to repeat a routine with different conditions. If your experiment expects a variable from a conditions file but the loop isn’t set up correctly, PsychoPy won’t be able to find the variable.