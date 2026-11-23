---
search:
  boost: 2
---

# Write the evaluator

The evaluator is the script that scores one design. It lives at `adapter/run.py`, trains one design,
and writes that design's score to a file. The search runs it once per design, as a separate job.

An agent normally writes the evaluator with you ([Get started](get-started.md)). This page is for
checking what it wrote, or for writing one yourself.

## Minimal evaluator

```python
"""adapter/run.py: train one design and write its score."""
import json
import os
import sys

sys.path.insert(0, os.getcwd())      # the job's working copy of your code

import train                         # your own training code, with this design's blocks in place

out = os.environ["EVO_OUT_DIR"]
os.makedirs(out, exist_ok=True)

score = train.fit_and_validate(epochs=int(float(os.environ["EVO_ALLOWANCE"])),
                               seed=int(os.environ["EVO_SEED"]))

with open(os.path.join(out, "result.json"), "w") as handle:
    json.dump({"valid": True, "score": score}, handle)
```

It reads three variables (where to write, how long to train, the seed) and writes `result.json` with
`valid` and `score`. `train.fit_and_validate` stands for whatever your project calls to train a model
and return its validation score.

## Testing by hand

Run it on your unchanged code, the way a job would, before starting any search:

```
mkdir trial && cp -r mysearch/base/. trial/ && cp -r mysearch/adapter trial/
cd trial
EVO_OUT_DIR=out EVO_CHECKPOINT_DIR=checkpoints EVO_SEED=0 EVO_ALLOWANCE=2 python adapter/run.py
cat out/result.json
```

If that prints a score, the search can run it. The working copy has the contents of `base/` at its top
level and your `adapter/` folder beside them, which is why `import train` works.

## Full example

Reporting progress lets the search stop a weak design part way. Reporting the parameter count and a
held-out score puts them on the leaderboard and lets limits use them.

```python
"""adapter/run.py: train one design, report progress, and write its score."""
import json
import os
import sys

sys.path.insert(0, os.getcwd())

import torch
import model
import train

out, checkpoints = os.environ["EVO_OUT_DIR"], os.environ["EVO_CHECKPOINT_DIR"]
os.makedirs(out, exist_ok=True)
os.makedirs(checkpoints, exist_ok=True)
epochs = int(float(os.environ["EVO_ALLOWANCE"]))
torch.manual_seed(int(os.environ["EVO_SEED"]))

net = model.build()
data = train.loaders()
parameters = sum(p.numel() for p in net.parameters())
best_path = os.path.join(checkpoints, "best.pt")


def stop_requested():
    try:
        with open(os.path.join(out, "control.json")) as handle:
            return json.load(handle).get("action") == "stop"
    except (OSError, ValueError):
        return False


best, best_epoch, epoch = None, 0, 0
with open(os.path.join(out, "progress.jsonl"), "a") as progress:
    for epoch in range(1, epochs + 1):
        train.one_epoch(net, data["train"])
        val = train.evaluate(net, data["val"])           # the number the search optimizes
        if best is None or val > best:
            best, best_epoch = val, epoch
            torch.save(net.state_dict(), best_path)
        progress.write(json.dumps({"step": epoch, "metric": val, "parameters": parameters}) + "\n")
        progress.flush()
        if stop_requested():
            break

net.load_state_dict(torch.load(best_path))
result = {
    "valid": True,
    "score": best,                                       # on validation data
    "parameters": parameters,
    "best_epoch": best_epoch,
    "epochs_run": epoch,
    "diagnostics": {"hidden": {"test": train.evaluate(net, data["test"])}},   # never shown to an agent
}
with open(os.path.join(out, "result.json"), "w") as handle:
    json.dump(result, handle)
```

The demo's evaluator does the same in NumPy and is known to run:
`evoloop/examples/tiny_classifier/adapter/run.py`.

## Working directory

For each design, evoloop makes a working copy of `base/` with that design's blocks in place, puts your
`adapter/` folder beside it, and starts the script there. `base/` itself is never modified.

All of `base/` is copied for every design. Keep datasets and pretrained weights outside it and refer to
them by absolute path.

## Dry run

Once the script runs by hand, run a four-design search with scripted proposals. It costs nothing and
shows that jobs start and finish on your machine.

```
evoloop brief mysearch --answer agents.backend=stub --answer budget.evaluations=4 --confirm "Your Name"
evoloop run mysearch --name dry
```

## Quick check

Agents sometimes write a design whose shapes do not fit. A quick check catches these before any
training. Set `evaluation.quick_check: python adapter/check.py` to a script that builds the model and
passes one batch through it. A design that fails is dropped in seconds and costs no evaluation.
[Evaluator interface](project-contract.md#quick-check)

## Optional result fields

| In `result.json` | Used for |
|---|---|
| `parameters` | limits on size, the size bands of the archive, the score-and-size trade-off |
| `inference_speed: {"examples_per_s": n}` | limits on speed, the score-and-speed trade-off, a leaderboard column |
| `signature: [numbers]` | where the model's errors fall, to tell designs that fail differently apart |
| `diagnostics: {...}` | any metric: shown to the agents, available as a leaderboard column |
| `diagnostics.hidden: {...}` | held-out results: stored, never shown to an agent |
| `captured: {...}` | package versions and training settings, for the study file |

[Evaluator interface](project-contract.md) is the reference: every variable, every key, the exit codes,
and how jobs run on Slurm.

## Metric names

The search optimizes `score`. Give that metric its name in the brief (`objective.metric: pearson_r`),
and list every metric to track with how it is computed:

```yaml
objective:
  metric: pearson_r
evaluation:
  metrics:
    pearson_r: Pearson correlation between predicted and measured signal, per peak, averaged
    count_r2: R squared of predicted against measured log counts
    test_pearson_r: {definition: pearson_r on the held-out chromosomes, split: test}
```

The names are the ones the evaluator writes under `diagnostics` (validation) and `diagnostics.hidden`
(test). They go into the study file, where they are what lets someone compare this search with another
or start a search from it. The report warns when a metric named here is missing from the results.
