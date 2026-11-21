"""The classifier that is searched: what it is given, and its layers."""
import numpy as np

# EVOLVE-BLOCK-START name=model kind=structure role=network
HIDDEN = []            # the widths of the hidden layers; none is a linear classifier
ACTIVATION = "tanh"    # tanh or relu


def features(x):
    """What the network is given: here, the two coordinates as they are."""
    return x
# EVOLVE-BLOCK-END
