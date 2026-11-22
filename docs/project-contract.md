---
search:
  boost: 1.5
---

# Evaluator interface

This is the contract between the loop and the code it runs.

## Working directory

Each training run gets its own working copy: `base/` with the design's blocks spliced in, and
`adapter/` beside it. The run command (`run_command`, `python adapter/run.py` by default) starts
there. `base/` itself is never modified.

The whole of `base/` is copied for every run. Keep data and weights out of it: point to them by
absolute path from the evaluator.

## Environment variables

| Variable | Meaning |
|---|---|
| `EVO_OUT_DIR` | where to write the files below |
| `EVO_SEED` | the seed |
| `EVO_ALLOWANCE` | the length of this run, in your own unit |
| `EVO_DATA_FRACTION` | the share of the training data to use (`data.fraction`) |
| `EVO_CHECKPOINT_DIR` | a folder kept for this design, seed and period: the same run started again finds its checkpoint there |
| `EVO_RESTART_COUNT` | 0 on the first start; above 0 when the run was started again after the machine ended it |
| `EVO_CONTINUE_FROM` | set when the run is to continue an earlier run's checkpoint (after the run length was raised) |
| `EVO_PARENT_CHECKPOINT_DIR` | with `evaluation.inherit_weights`: the checkpoint folder of the design's parent, to start from |
| `EVO_LARGER_GPU` | set when `compute.larger_gpu_type` names a larger GPU the design could be moved to (see exit 76 below) |
| `EVO_RUN_ID`, `EVO_CPUS` | the run's id; the processors it may use |
| your own | every name in `evaluation.variables`, as you set it |

Variables whose names look like credentials (KEY, TOKEN, SECRET, PASSWORD, CREDENTIAL) are removed from the job's
environment, because designs are model-written code.

## Output files

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
| `valid`, `score` | yes | whether the run produced a score, and the number the search optimizes (on validation data) |
| `rejected` | no | with `valid: false`, the reason the evaluator rejected the design (too slow, too large); it is then not a failure |
| `diagnostics` | no | numbers here are shown to the agents and can be leaderboard columns |
| `diagnostics.hidden` | no | test-set results: stored and written to the study file, never shown to an agent |
| `parameters` | no | trainable parameter count; used for the archive's size bin, for `limits`, and as the second figure of the `pareto` strategy |
| `signature` | no | a list of numbers saying where the model's errors fall (per class, per range, per example); used to pair designs for crossover, to group designs by behaviour in the archive, and to choose what a novel slot is shown |
| `inference_speed` | no | `{"examples_per_s": n}`: for the study file, for a limit on `examples_per_s`, the `speed` column, and the second figure of the `pareto` strategy |
| `best_epoch`, `epochs_run` | no | where the best score was reached and how far the run went; leaderboard columns |
| `resource_used` | no | how much of the allowance the run used, in your own unit |
| `captured` | no | the environment, and the training settings read from the objects the script built; for the study file |

A figure named in `limits` must be in the final result: a result without it is rejected and the run pauses
([Limits](steering.md#limits)).

## Progress and stopping

To let weak designs be stopped part way, append lines to
`progress.jsonl` as training goes, `{"step": n, "metric": x}`, with `step` in the unit of the
allowance and `metric` the score or a faithful running estimate of it. At each report, read
`control.json`; if it says `{"action": "stop"}`, finish promptly and still write the result.

## Exit codes

Exit 75 says the machine failed, not the model: the run is started again, uncharged, at
most `compute.infrastructure_retries` times. A run that ends with no `result.json` is recorded as
failed, with the end of its log.

Exit 76 says the design is too large for the GPU it was given. If `compute.larger_gpu_type` is set (the job is
then told so through `EVO_LARGER_GPU`), the run is submitted again on that type, uncharged, once. Otherwise it
is recorded as failed with that reason.

## Parent checkpoint

With `evaluation.inherit_weights: true` (and `evaluation.keep_checkpoints: true`), the job of a design
that has a parent is given `EVO_PARENT_CHECKPOINT_DIR`: the folder where the parent's run kept its
checkpoint. What to do with it is the evaluator's business: typically, load every tensor whose name and
shape match the child's model and initialise the rest as usual. A child that changes little then
trains from where its parent stopped.

- It makes a child's score depend on its parent's training, so a child is no longer comparable with a
  design trained from scratch at the same length. The loop does not correct for this. Refit the
  designs you mean to report from scratch.
- Changing the setting during a run begins a new period, like a change of the run length.
- A new design, and the first parent's missing folder, get no variable: the evaluator must handle its
  absence.

## Quick check

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

### Controller as a job

```
evoloop controller mysearch --name r1 --partition cpu --time 1-00:00:00 --setup "source ~/envs/x/bin/activate"
sbatch mysearch/run_controller_r1.sbatch
```

writes a job script that runs the search. Shortly before its time limit Slurm signals it; the controller
stops cleanly, puts itself back in the queue, and finds its training jobs again by their ids when it
restarts. It requeues itself only at the time limit: not after the search has ended, paused or stalled,
and not after a crash.

## Agent inputs

`task.md`, the open blocks of the parents and of the designs shown beside them, the visible
diagnostics, the leaderboard, the lessons and your notes. They do not see the rest of your code, and
they never see anything under `diagnostics.hidden`.
