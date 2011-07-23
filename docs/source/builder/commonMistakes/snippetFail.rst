.. _snippetFail:

The code snippet I've entered doesn't do anything
-------------------------------------------------

-	Have you remembered to put a $ symbol at the beginning (this isn't necessary, and should be avoided in a :ref:`code`)?
-	A dollar sign as the first character of a line indicates to PsychoPy that the rest of the line is code. It does not indicate a variable name (unlike in perl or php). This means that if you are, for example, using variables to determine position, enter $[x,y]. The temptation is to use [$x,$y], which will not work.