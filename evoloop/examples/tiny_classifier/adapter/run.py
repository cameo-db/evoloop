"""How one design of the example is run: it trains the classifier and writes what the search needs.

Started inside a job's working copy (base/ with a design's blocks spliced in, and this folder). It reads the
EVO_ variables, reports progress so that a weak design can be stopped early, honours a stop request, and
writes result.json."""
import json
import os
import sys

sys.path.insert(0, os.getcwd())   # the job's copy of the code

import train   # noqa: E402


def main():
    out_dir = os.environ.get("EVO_OUT_DIR", "evo_out")
    os.makedirs(out_dir, exist_ok=True)
    steps = float(os.environ.get("EVO_ALLOWANCE", "300"))
    seed = int(os.environ.get("EVO_SEED", "0"))
    progress = open(os.path.join(out_dir, "progress.jsonl"), "a")

    def report(step, val, train_accuracy):
        progress.write(json.dumps({"step": step, "metric": val, "train_accuracy": train_accuracy}) + "\n")
        progress.flush()
        try:
            with open(os.path.join(out_dir, "control.json")) as handle:
                return json.load(handle).get("action") != "stop"
        except (OSError, ValueError):
            return True

    try:
        found = train.fit(steps, seed=seed, report=report)
        result = {"valid": True, "score": found["score"], "parameters": found["parameters"],
                  "best_epoch": found["best_step"], "epochs_run": found["steps"],
                  "inference_speed": {"examples_per_s": found["examples_per_s"]},
                  "signature": found["errors_by_ring"],          # where its errors fall: by distance from the centre
                  "diagnostics": {"train_accuracy": found["train_accuracy"],
                                  "generalization_gap": found["train_accuracy"] - found["score"],
                                  "hidden": {"test_accuracy": found["test_accuracy"]}}}   # never shown to an agent
    except Exception as exc:      # a design that cannot be trained is a failed design, with the reason
        result = {"valid": False, "score": None, "diagnostics": {"error": "%s: %s" % (type(exc).__name__, exc)}}
    with open(os.path.join(out_dir, "result.json"), "w") as handle:
        json.dump(result, handle)


if __name__ == "__main__":
    main()
