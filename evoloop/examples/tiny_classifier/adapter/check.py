"""The quick check: build the design and pass a few points through it. A design that fails here is not trained."""
import os
import sys

import numpy as np

sys.path.insert(0, os.getcwd())   # the job's copy of the code

import model   # noqa: E402

given = np.asarray(model.features(np.ones((4, 2)) * 0.5), dtype=float)
assert given.ndim == 2 and given.shape[0] == 4, "features(x) must return one row per example, got %s" % (given.shape,)
assert np.isfinite(given).all(), "features(x) must be finite"
assert model.ACTIVATION in ("tanh", "relu"), "ACTIVATION must be tanh or relu"
assert all(int(h) > 0 for h in model.HIDDEN) and len(model.HIDDEN) <= 6, "HIDDEN must be up to six positive widths"
