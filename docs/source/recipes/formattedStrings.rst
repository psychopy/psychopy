.. _formattedStrings:

Generating formatted strings
================================

A formatted string is a variable which has been converted into a string (text). In python the specifics of how this is done is determined by what kind of variable you want to print.

Example 1: You have an experiment which generates a string variable called `text`. You want to insert this variable into a string so you can print it. This would be achieved with the following code::

    message = 'The result is %s' %(text)
    
This will produce a variable `message` which if used in a text object would print the phrase 'The result is' followed by the variable `text`. In this instance %s is used as the variable being entered is a string. This is a marker which tells the script where the variable should be entered. `%text` tells the script which variable should be entered there.

Multiple formatted strings (of potentially different types) can be entered into one string object::

    longMessage = 'Well done %s that took %0.3f seconds' %(info['name'], time)
    
Some of the handy formatted string types::

    >>> x=5
    >>> x1=5124
    >>> z='someText'
    >>> 'show %s' %(z)
    'show someText'
    >>> '%0.1f' %(x)   #will show as a float to one decimal place
    '5.0'
    >>> '%3i' %(x) #an integer, at least 3 chars wide, padded with spaces
    '  5'
    >>> '%03i' %(x) #as above but pad with zeros (good for participant numbers)
    '005'

See the `python documentation <http://docs.python.org/library/stdtypes.html#string-formatting-operations>`_ for a more complete list.
