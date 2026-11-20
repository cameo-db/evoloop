# The project's code

This is the contract between the loop and the code it runs.

## Where a design runs

Each training run gets its own working copy: `base/` with the design's blocks spliced in, and
`adapter/` beside it. The run command (`run_command`, `python adapter/run.py` by default) starts
there. `base/` itself is never modified.

The whole of `base/` is copied for every run. Keep data and weights out of it: point to them by
absolute path from the adapter.

## Variables the job is given

| Variable | Meaning |
|---|---|
| `EVO_OUT_DIR` | where to write the files below |
| `EVO_SEED` | the seed |
| `EVO_ALLOWANCE` | the length of this run, in your own unit |
| `EVO_DATA_FRACTION` | the share of the training data to use (`data.fraction`) |
| `EVO_CHECKPOINT_DIR` | a folder kept for this design, seed and period: the same run started again finds its checkpoint there |
| `EVO_RESTART_COUNT` | 0 on the first start; above 0 when the run was started again after the machine ended it |
| `EVO_CONTINUE_FROM` | set when the run is to continue an earlier run's checkpoint (after the run length was raised) |
| `EVO_RUN_ID`, `EVO_CPUS` | the run's id; the processors it may use |

Variables whose names look like credentials (KEY, TOKEN, SECRET, PASSWORD) are removed from the job's
environment, because designs are model-written code.

## What the job writes

`result.json`, in `EVO_OUT_DIR`:

```json
{"valid": true,
 "score": 0.71,
 "diagnostics": {"val_loss": 0.42, "profile_r": 0.66, "hidden": {"test_r": 0.70}},
 "parameters": 1200000,
 "best_epoch": 14, "epochs_run": 20,
 "signature": [0.12, -0.03, 0.4],
 "inference_speed": {"examples_per_s": 5000},
 "captured": {"environment": {"python": "3.11", "framework": "PyTorch 2.4"},
              "training": {"loss": {"kind": "mse"}, "early_stopping": false}}}
```

| Field | Needed | Meaning |
|---|---|---|
| `valid`, `score` | yes | whether the run produced a score, and the number the search optimises (on validation data) |
| `diagnostics` | no | numbers here are shown to the agents and can be leaderboard columns |
| `diagnostics.hidden` | no | test-set results: stored and written to the study file, never shown to an agent |
| `parameters` | no | trainable parameter count; also used for the archive's size bin |
| `signature` | no | a list of numbers saying where the model's errors fall (per class, per range, per example); used to pair designs for crossover |
| `inference_speed` | no | for the study file |
| `captured` | no | the environment, and the training settings read from the objects the script built; for the study file |

**Progress and stopping.** To let weak new designs be stopped part way, append lines to
`progress.jsonl` as training goes, `{"step": n, "metric": x}`, with `step` in the unit of the
allowance and `metric` the score or a faithful running estimate of it. At each report, read
`control.json`; if it says `{"action": "stop"}`, finish promptly and still write the result.

**Exit codes.** Exit 75 says the machine failed, not the model: the run is started again, uncharged, at
most `compute.infrastructure_retries` times. A run that ends with no `result.json` is recorded as
failed, with the end of its log.

## The quick check

`evaluation.quick_check` is a command that tests a design in seconds, for instance building the model
and passing one batch through it. It runs first in the job; a design that fails it is not trained and
is recorded as invalid.

## On Slurm

With `compute.scheduler: slurm`, each run is its own job, submitted with `--requeue` and followed by
its job id.

- The controller can stop and start again without touching the jobs; it finds them again by id.
- A job Slurm requeues after a preemption keeps its id and its log.
- `compute.setup` holds shell lines run first in each job, such as activating an environment.
- `compute.qos` may be a list in order of preference, `[{name: a, max_jobs: 8}, {name: b}]`: each job
  goes to the first with room.
- No new design is written while `compute.max_waiting` jobs (1 by default) are waiting for their first
  start, so on a busy cluster designs are not written long before they can run.
- Each start of a job is recorded in `starts.jsonl` with its node and GPU.

The controller itself is light and can run as a small CPU job.

## What the agents see

`task.md`, the open blocks of the parents and of the designs shown beside them, the visible
diagnostics, the leaderboard, the lessons and your notes. They do not see the rest of your code, and
they never see anything under `diagnostics.hidden`.
