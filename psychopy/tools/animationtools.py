import numpy as np


def sinusoidalGrowth(startSize, apexSize, duration, time):
    """
    Grow or shrink a stimulus over time by a sinusoidal function.

    startSize : layout.Size
        Size of the stimulus at the start of the animation
    stopSize : layout.Size
        Size of the stimulus at the apex of the animation
    duration : int, float
        How long (in seconds) should the animation take to go from its start to its apex?
    time : float
        How long (in seconds) has passed since the animation started?
    """
    # Convert sizes to numpy arrays
    if isinstance(startSize, (list, tuple)):
        startSize = np.array(startSize)
    if isinstance(apexSize, (list, tuple)):
        apexSize = np.array(apexSize)
    # Get total size change
    delta = apexSize - startSize
    # Adjust time according to duration
    time = time / duration % 2
    # Get proportion of delta to adjust by
    time = time - 0.5
    adj = np.sin(time * np.pi)
    adj = (adj + 1) / 2
    # Adjust
    return startSize + (delta * adj)


def sinusoidalMovement(startPos, apexPos, duration, time):
    """
    Move a stimulus over time by a sinusoidal function.

    startPos : layout.Position
        Position of the stimulus at the start of the animation
    apexPos : layout.Position
        Position of the stimulus at the apex of the animation
    duration : int, float
        How long (in seconds) should the animation take to go from its start to its apex?
    time : float
        How long (in seconds) has passed since the animation started?
    """

    # Position and Size are both Vectors, so growth and movement are the same calculation
    return sinusoidalGrowth(startPos, apexPos, duration, time)
