# Write the evaluator

The evaluator is the one piece of code you write for evoloop. It is a script, `adapter/run.py`, that
trains one design and writes its score to a file. The search runs it once per design, as its own job.

## A complete example

This one is for a PyTorch project whose code has a `model.build()` and a few training functions. Yours
will call your own.

```python
"""adapter/run.py: train one design and write its score."""
import json
import os
import sys

sys.path.insert(0, os.getcwd())      # the job's working copy of your code

import torch
import model                         # your modules, with this design's blocks already in place
import train

out = os.environ["EVO_OUT_DIR"]                          # where to write
epochs = int(float(os.environ["EVO_ALLOWANCE"]))         # how long to train
torch.manual_seed(int(os.environ["EVO_SEED"]))

net = model.build()
data = train.loaders()
parameters = sum(p.numel() for p in net.parameters())


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
            torch.save(net.state_dict(), os.path.join(os.environ["EVO_CHECKPOINT_DIR"], "best.pt"))
        progress.write(json.dumps({"step": epoch, "metric": val, "parameters": parameters}) + "\n")
        progress.flush()
        if stop_requested():
            break

net.load_state_dict(torch.load(os.path.join(os.environ["EVO_CHECKPOINT_DIR"], "best.pt")))
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

That is the whole contract in practice:

- read three variables: where to write, how long to train, the seed;
- write `result.json` with `valid` and `score`;
- optionally append a line to `progress.jsonl` each epoch and check `control.json`, which lets the
  search stop a weak design early;
- optionally report more (the parameter count, the held-out score), which the leaderboard, limits and
  some skills use.

The demo's evaluator is a working example of the same thing in NumPy:
`evoloop/examples/tiny_classifier/adapter/run.py`.

## Where it runs

For each design, evoloop makes a working copy: the contents of `base/` with that design's blocks
spliced in, and your `adapter/` folder beside them. The script starts in that folder, so `import model`
finds the design's version of your code. `base/` itself is never modified.

The whole of `base/` is copied for every design, so keep data and pretrained weights out of it and
refer to them by absolute path.

## Try it by hand first

Before any search, run the evaluator on your unchanged code exactly as a job would:

```
mkdir trial && cp -r mysearch/base/. trial/ && cp -r mysearch/adapter trial/
cd trial
EVO_OUT_DIR=out EVO_SEED=0 EVO_ALLOWANCE=2 EVO_CHECKPOINT_DIR=out python adapter/run.py
cat out/result.json
```

If that prints a score, the search can run it. Then dry-run the search itself with scripted proposals
and a tiny budget (`agents.backend: stub`, `budget.evaluations: 4`) to see jobs start and finish on
your machine before paying for agents or GPUs.

## Things that go wrong

**The score goes the wrong way.** `objective.direction` says whether higher or lower is better. A loss
reported with `maximize` makes the search look for the worst model.

**The score is the test score.** The search optimizes whatever is in `score`, and agents are shown it.
Report validation there and put held-out results under `diagnostics.hidden`.

**The seed does nothing.** If two runs with different `EVO_SEED` give identical scores, your training
code is not using it. See [Measure your noise](noise.md).

**A design crashes with a shape error.** That is normal: agents write designs that do not fit. Add a
quick check (`evaluation.quick_check: python adapter/check.py`) that builds the model and passes one
batch through it. A design that fails it is dropped in seconds without being trained.

**A limit is set on something not reported.** If `limits` names `examples_per_s` and the result does
not carry it, the search pauses. Report every figure a limit or a skill needs.

## More you can report

| In `result.json` | What it enables |
|---|---|
| `parameters` | limits on size, the size bands of the archive, the size trade-off |
| `inference_speed: {"examples_per_s": n}` | limits on speed, the speed trade-off, a leaderboard column |
| `signature: [numbers]` | where the model's errors fall: tells designs that fail differently apart |
| `diagnostics: {...}` | any metric: shown to the agents and available as a leaderboard column |
| `diagnostics.hidden: {...}` | held-out results: stored, never shown to an agent |
| `captured: {...}` | package versions and training settings, for the study file |

[Evaluator interface](project-contract.md) is the full reference: every variable, every key, the exit
codes, and how jobs run on Slurm.
