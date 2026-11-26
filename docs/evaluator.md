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
held-out score puts them on the leaderboard and lets limits use them. Saving its state after every
epoch lets the run continue when its job is ended early.

`evojob.py` is a small file with no dependencies that `evoloop init` puts beside the evaluator. It
reads the variables, writes the progress lines and the result, and keeps the state.

```python
"""adapter/run.py: train one design, report progress, resume after an interruption, write its score."""
import os
import sys

sys.path.insert(0, os.getcwd())
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import torch
import evojob
import model
import train

job = evojob.Job()
torch.manual_seed(job.seed)

net = model.build()
optimizer = train.optimizer(net)
data = train.loaders()
parameters = sum(p.numel() for p in net.parameters())

state = job.load_state() or {"epoch": 0, "best": None, "best_epoch": 0}
if state["epoch"] > 0:  # started again: go on from the last finished epoch
    saved = torch.load(job.path("last.pt"))
    net.load_state_dict(saved["net"])
    optimizer.load_state_dict(saved["optimizer"])

for epoch in range(state["epoch"] + 1, int(job.allowance) + 1):
    train.one_epoch(net, optimizer, data["train"])
    val = train.evaluate(net, data["val"])  # the number the search optimizes
    job.report(epoch, val, parameters=parameters)
    finite = val == val and abs(val) != float("inf")
    if finite and (state["best"] is None or val > state["best"]):
        state.update(best=val, best_epoch=epoch)
        torch.save(net.state_dict(), job.path("best.pt"))
    torch.save({"net": net.state_dict(), "optimizer": optimizer.state_dict()}, job.path("last.pt"))
    state["epoch"] = epoch
    job.save_state(state)  # after the weights, so it never points past them
    if not finite or job.should_stop():  # diverged, or the search asked this run to end
        break
    if job.out_of_time():  # the time limit is near, or the job was told to end
        job.pause()  # submitted again; continues from here

net.load_state_dict(torch.load(job.path("best.pt")))
job.finish(
    score=state["best"],  # on validation data
    parameters=parameters,
    best_epoch=state["best_epoch"],
    epochs_run=state["epoch"],
    diagnostics={"hidden": {"test": train.evaluate(net, data["test"])}},  # never shown to an agent
)
```

The best weights are saved apart from the latest ones, so an epoch that diverges does not cost the run
the score it had reached.

## Interruptions

A job can end before its training run is done: it reaches its time limit, the cluster preempts it, or
a node fails. evoloop then starts the run again, uncharged, in the same checkpoint folder. The example
above continues from its last finished epoch, so an interruption costs one epoch at most.

That is also what lets a search ask for short jobs. A job with a four-hour limit starts sooner on a
busy cluster than one with a two-day limit, and a run that needs twenty hours becomes five jobs in a
row. `job.out_of_time()` is true when the limit is closer than one more epoch would take, and
`job.pause()` leaves cleanly before the scheduler has to kill the job.

A run is started again for as long as each start gets further than the last. A run that is ended
several times in a row at the same step is recorded as failed, which is what happens to an evaluator
that starts over when the time limit is shorter than its training run.
[Getting GPUs](servers.md#getting-gpus) · [Evaluator interface](project-contract.md#exit-codes)

## Evaluator check

```
evoloop check mysearch
```

runs the evaluator once on your unchanged code, where the search's jobs will run, and interrupts it on
purpose. After the first progress report the job is killed, as a preemption would kill it, and started
again. Then it is asked to stop.

```
Evaluator check for mysearch: one training run of the code as it stands, interrupted on purpose. Nothing is charged.
  started               reported step 1 after 212 s
  killed and restarted  went on at step 2 (it had reached step 1): it resumes
  asked to stop         ended 190 s later with a score of 0.412
The evaluator does what a search needs.
```

When the evaluator begins again after the restart, ignores the stop, or stops without a score, the
check says so and says what to change. Each of these costs GPU days when it is found during a search:
a run that begins again loses its work at every preemption, and a run that ignores a stop is killed and
loses the score it had reached.

The demo's evaluator writes the files itself, without `evojob.py`, and is known to run:
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
and list what else is measured on every design: the validation metrics to track, and the test
evaluations to run.

```yaml
objective:
  metric: pearson_r
evaluation:
  metrics:
    pearson_r: Pearson correlation between predicted and measured signal, per peak, averaged
    count_r2: R squared of predicted against measured log counts
  test_metrics:
    test_pearson_r: pearson_r on the held-out chromosomes
    test_count_r2: count_r2 on the held-out chromosomes
    other_cell_line_r: {definition: pearson_r on HepG2 peaks, dataset: HepG2 ATAC-seq}
```

The names under `metrics` are the ones the evaluator writes under `diagnostics`. The agents see them.
The names under `test_metrics` are the ones it writes under `diagnostics.hidden`. They are recorded for
you and never shown to an agent or used to choose parents. Run as many test evaluations as you want to
follow, on the held-out split or on other data. Which evaluations count as validation and which as test
is your decision.

Both lists become columns of the leaderboard and go into the study file, where they are what lets
someone compare this search with another or start a search from it. The report warns when a metric
named here is missing from the results.
