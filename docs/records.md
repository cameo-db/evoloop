# Files of a run

Everything a run knows is in its folder, `runs/<name>/`, as plain files. The controller can be stopped
at any point and started again from them.

## Stores

One JSON-lines file per store; a later line with the same `id` updates the earlier one.

| File | One line per | Written by |
|---|---|---|
| `runs.jsonl` | training run: its model, recipe, settings, seed, where it came from, its performance | code |
| `models.jsonl` | architecture (the open model blocks) | code |
| `recipes.jsonl` | training recipe (the open recipe blocks) | code |
| `ledger.jsonl` | change to the run, or note, with who made it and when | you (through the steering commands), the strategist, the spend governor and the loop itself |
| `calls.jsonl` | agent call | code |
| `knowledge.jsonl` | lesson, with its evidence | the analyst, checked by code |
| `questions.jsonl` | question for you, with the default taken meanwhile | agents |
| `reviews.jsonl` | review of a role | the assessor |
| `references.jsonl` | a model shown on the leaderboard for comparison, not part of the search | you, through `evoloop reference` |
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
| `requests/`, `requests/done/` | steering requests waiting for the controller, and those it has dealt with |
| `controller.json` | what the controller keeps between turns |
| `skills/` (in the search folder) | the search's own copy of each skill it uses |

Working copies and checkpoints are not cleaned up; remove `work/` when a run has ended if space is short.

## History of a run

Every run records how it came about: its lineage, its parent (and second parent, for a crossover), the
mode and the move, the hypothesis and predicted effect the writer gave, its forecast, why the slot
went where it did, and the proposals that were weighed and not chosen.

