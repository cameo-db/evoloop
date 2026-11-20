"""The quick check of the example: build the candidate, pass one small input through it, print its size.

Recorded in project.yaml as `run.check_command`; this version of evoloop does not run it. Run it by
hand inside a job's copy: `python adapter/check.py`."""
import json
import os
import sys

import numpy as np

sys.path.insert(0, os.getcwd())   # the job's copy of the code

import model   # noqa: E402


def main():
    n = int(model.N_CONSTANTS)
    out = np.asarray(model.predict(np.zeros((4, 2)), np.ones(n)))
    assert out.shape == (4,), "predict must return one value per row, got shape %s" % (out.shape,)
    print(json.dumps({"n_constants": n}))


if __name__ == "__main__":
    main()
