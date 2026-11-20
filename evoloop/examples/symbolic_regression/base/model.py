"""The functional form that is fitted."""
import numpy as np

# EVOLVE-BLOCK-START name=model kind=structure role=form
N_CONSTANTS = 3


def predict(x, c):
    return c[0] + c[1] * x[:, 0] + c[2] * x[:, 1]
# EVOLVE-BLOCK-END
