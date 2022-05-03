import numpy as np

factor = 1


class Scaled:
    """
    Class for easily applying a global app scale to individual values, with protections against duplicating scaling.

    Accepts any number of float, int, tuple, list or np.ndarray values as inputs and will return in the same format
    given. Resulting values are of special classes which mark them as already scaled, so they aren't scaled again. For
    example, `Scaled(Scaled(8))` will return 16, not 32.
    """

    class _ScaledFloat(float):
        pass

    class _ScaledInt(int):
        pass

    class _ScaledTuple(tuple):
        pass

    class _ScaledList(list):
        pass

    class _ScaledNdarray(np.ndarray):
        pass

    map = {
        float: _ScaledFloat,
        int: _ScaledInt,
        tuple: _ScaledTuple,
        np.ndarray: _ScaledNdarray,
    }

    def __new__(cls, *args):
        # Blank array for output arguments
        argout = []
        # Iterate through all arguments given
        for value in args:
            # Don't scale -1 as it's used by wx
            if value == -1:
                argout.append(value)
                continue
            # Don't re-scale something already scaled
            if type(value) in (cls.map.values()):
                argout.append(value)
                continue
            # If given a float or int, multiply by factor
            if isinstance(value, (int, float)):
                value *= factor
            # If given a list/tuple, make a new list/tuple with each (non-special) value multiplied by factor
            if isinstance(value, (tuple, list, np.ndarray)):
                buffer = []
                for subval in value:
                    if value == -1:
                        buffer.append(subval)
                    else:
                        buffer.append(subval * 2)
                value = type(value)(buffer)
            # If possible, make special scaled object to mark as already scaled
            if type(value) in cls.map:
                value = cls.map[type(value)](value)
            # Append to new arg array
            argout.append(value)
        # Convert to tuple
        argout = tuple(argout)
        # If only given one value, remove extraneous list
        if len(argout) == 1:
            argout = argout[0]

        return argout
