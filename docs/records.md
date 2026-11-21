# Records and the study file

Everything a run knows is in its folder, `runs/<name>/`, as plain files. The controller can be stopped
at any point and started again from them.

## The stores

One JSON-lines file per store; a later line with the same `id` updates the earlier one.

| File | One line per | Written by |
|---|---|---|
| `runs.jsonl` | training run: its model, recipe, settings, seed, where it came from, its performance | code |
| `models.jsonl` | architecture (the open model blocks) | code |
| `recipes.jsonl` | training recipe (the open recipe blocks) | code |
| `ledger.jsonl` | change to the run, or note, with who made it and when | you, through the steering commands |
| `calls.jsonl` | agent call | code |
| `knowledge.jsonl` | lesson, with its evidence | the analyst, checked by code |
| `questions.jsonl` | question for you, with the default taken meanwhile | agents |
| `reviews.jsonl` | review of a role | the assessor |
| `approaches.jsonl` | approach handed to the writers, and whether it is active or retired | you (`variation.approach_seeds`) and the analyst |
| `chat.jsonl` | message to the agent that runs the search, its answer and what it asked for | you, through `evoloop chat` |

Beside them:

| Path | Holds |
|---|---|
| `run.json` | the brief the run started with, the hash of its frozen code, its state |
| `status.json` | budget used, the best so far, the mix now, agent spend; rewritten every turn |
| `report.md` | the report, written when the run stops or ends |
| `candidates/<id>/blocks.json` | the blocks of each design |
| `replies/<call>.json` | each agent's whole reply |
| `out/<run>/` | each job's `result.json`, `progress.jsonl`, log |
| `work/<run>/` | each job's working copy |
| `checkpoints/` | each design's checkpoint folder |

Working copies and checkpoints are not cleaned up; remove `work/` when a run has ended if space is short.

## A run's history

Every run records how it came about: its lineage, its parent (and second parent, for a crossover), the
mode and the move, the hypothesis and predicted effect the writer gave, its forecast, why the slot
went where it did, and the proposals that were weighed and not chosen.

## The study file

`study.json` is written when a run stops or ends, and by `evoloop study`. It is in the CAMEO entry
format, version 0.4, with four parts:

| Part | Holds |
|---|---|
| `experiment` | the objective, the data, the evaluation, the environment, the search, the conclusions |
| `models` | each architecture, with its code as text |
| `training` | each recipe: its settings and the training code as text |
| `runs` | each run: model, recipe, seed, history, performance |

The run's own stores are already in that shape, so the file is an export. What the run does not know
is written as `"not_reported"`; nothing is filled in. `evoloop study` prints the star the file is on
course for and what stands in the way of the next:

- no dataset link (`data.accession`): no star;
- the environment, inference speed, or the recipe's loss and stopping rule not reported by the adapter
  (`captured`, `inference_speed` in `result.json`): Silver rather than Gold.

Steering, modes and agent spend have no field in the format. They stay in the ledger beside the file,
and `experiment.search.method` says how many steering entries the run had.

The CAMEO kit's own check (`cameo.py check study.json`) is not run by evoloop; run it yourself before
depositing.
