"""The run wrapper of the example: how one candidate is run.

It is started inside a job's working copy (the snapshot in base/ with a candidate's blocks spliced
in, plus this adapter folder). It calls the original code's own `train.fit` and does everything the
run contract asks for, so that the original code needs no change: it reads the `EVO_` variables,
reports progress and the cost figures, honours a stop request and an extension, and writes the
result."""
import json
import os
import sys
import time

sys.path.insert(0, os.getcwd())   # the job's copy of the code

import model   # noqa: E402
import train   # noqa: E402


def main():
    out_dir = os.environ.get("EVO_OUT_DIR", "evo_out")
    os.makedirs(out_dir, exist_ok=True)
    seed = int(os.environ.get("EVO_SEED", "0"))
    state = {"allowance": float(os.environ.get("EVO_ALLOWANCE", "1500")), "stop": False, "base": 0, "step": 0}
    started = time.time()
    progress = open(os.path.join(out_dir, "progress.jsonl"), "a")
    n = int(model.N_CONSTANTS)

    def control():
        try:
            with open(os.path.join(out_dir, "control.json")) as handle:
                told = json.load(handle)
        except (OSError, ValueError):
            return
        state["stop"] = state["stop"] or told.get("action") == "stop"
        state["allowance"] = max(state["allowance"], float(told.get("allowance", 0)))   # an extension

    def report(step, score, train_mse):
        state["step"] = state["base"] + step
        # The cost figures the brief sets limits on go into every report, the first included.
        progress.write(json.dumps({"step": state["step"], "metric": score, "train_mse": train_mse, "n_constants": n,
                                   "seconds_per_step": round((time.time() - started) / state["step"], 6)}) + "\n")
        progress.flush()
        control()
        return not state["stop"]

    # The first report goes out before any fitting, with the cost figures: a form that breaks a limit of
    # the brief is then stopped at once, not after its first, slow, steps. Its metric is the score of
    # the form with every constant at zero.
    import numpy as np
    xv, yv = train.load()["val"]
    with np.errstate(all="ignore"):
        untrained = train.mse(np.zeros(n), xv, yv) + train.PENALTY_PER_CONSTANT * n
    progress.write(json.dumps({"step": 0, "metric": untrained if np.isfinite(untrained) else 1e30, "n_constants": n}) + "\n")
    progress.flush()
    control()
    found = {"constants": None, "score": None, "steps": 0}
    if not state["stop"]:
        found = train.fit(steps=state["allowance"], seed=seed, report=report)
    state["base"] = state["step"] = found["steps"]
    control()
    # An extension (a raised allowance) continues the best fit.
    while not state["stop"] and found["constants"] is not None and state["step"] < state["allowance"]:
        more = train.fit(steps=state["allowance"] - state["step"], seed=seed, report=report, start=found["constants"])
        state["base"] = state["step"] = state["base"] + more["steps"]
        if more["score"] is not None and more["score"] < found["score"]:
            found = more
        control()

    result = {"valid": False, "score": None, "resource_used": state["step"],
              "diagnostics": {"error": "no restart produced a finite fit", "n_constants": n}}
    if found["score"] is not None:
        result = {"valid": True, "score": found["score"], "resource_used": state["step"],
                  "diagnostics": {"train_mse": found["train_mse"], "val_mse": found["val_mse"],
                                  "generalization_gap": found["val_mse"] - found["train_mse"], "n_constants": n,
                                  "seconds_per_step": round((time.time() - started) / max(1, state["step"]), 6),
                                  "constants": [round(float(v), 5) for v in found["constants"]],
                                  "residuals_by_range": found["residuals_by_range"],
                                  "hidden": {"test_mse": found["test_mse"]}},   # never shown to an agent
                  # Where this form's errors fall: used to pair designs that fail in different places.
                  "signature": [v["mean_residual"] for _, v in sorted(found["residuals_by_range"].items())],
                  "parameters": n}
    with open(os.path.join(out_dir, "result.json"), "w") as handle:
        json.dump(result, handle)


if __name__ == "__main__":
    main()
