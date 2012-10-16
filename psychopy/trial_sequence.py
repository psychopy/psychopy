'''
Module implements additional generator of trial sequences.
'''

import random
import numpy

def random_no_repeat(trial_list, repeats):
    sequences = []
    exclude = None
    for _ in xrange(repeats):
        indices = range(len(trial_list))
        if exclude is not None:
            indices.remove(exclude)
        initial = random.choice(indices)
        sequence = [initial]
        indices.remove(initial)
        if exclude is not None:
            indices.append(exclude)
        random.shuffle(indices)
        sequence.extend(indices)
        exclude = sequence[-1]
        sequences.append(sequence)
    return numpy.transpose(sequences)

def full_random_no_repeat(trial_list, repeats):
    sequences = []
    exclude = None
    for _ in xrange(repeats):
        sequence = []
        for _ in xrange(len(trial_list)):
            index = random.randrange(len(trial_list) - (1 if exclude is not None else 0))
            if exclude is not None and index >= exclude:
                index = index + 1
            sequence.append(index)
            exclude = index
        sequences.append(sequence)
    return numpy.transpose(sequences)
            

METHODS = {"no-repeat random": random_no_repeat, "no-repeat full random": full_random_no_repeat}
