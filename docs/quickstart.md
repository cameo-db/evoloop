# First run

The package carries a small example: a search for a formula that fits a dataset, with stub agents.
It makes no model call and needs no GPU, and it exercises every part of the loop.

## Install

```
pip install -e .              # Python 3.9 or later; needs pyyaml
pip install -e .[anthropic]   # for the Anthropic API backend
```

The example's training code uses NumPy.

## Run the example

```
evoloop example demo                        # copies the example to ./demo
evoloop plan demo                           # every setting, with where it came from
evoloop brief demo --confirm "Your Name"    # your agreement to the plan
evoloop run demo --name first
evoloop report demo --name first
```

`evoloop run` returns when the budget of 24 models is spent, which takes well under a minute.

## What to look at

The run's folder is `demo/runs/first/`.

| File | Holds |
|---|---|
| `report.md` | the leaderboard, the population, what each mode and move returned, the ledger, the agents' spend |
| `status.json` | the same in brief, rewritten every turn while the run goes |
| `runs.jsonl`, `models.jsonl`, `recipes.jsonl` | every training run, architecture and recipe |
| `ledger.jsonl` | every change to the run and every note, with who made it |
| `calls.jsonl`, `replies/` | every agent call: what it was shown, what it answered, what it cost |
| `study.json` | the run in the CAMEO entry format |

## Try steering it

Start a second, longer run and change it while it goes:

```
evoloop brief demo --answer budget.evaluations=80 --confirm "Your Name"
evoloop run demo --name second &
evoloop set demo --name second schedule.novelty=0.8 --by "Your Name" --reason "try wider"
evoloop note demo --name second "Prefer forms with few constants." --roles writer --by "Your Name"
evoloop status demo --name second
```

The example's models train in a fraction of a second, so the run may end before a request arrives. A
request made to a run that has ended waits, and is applied when the run is continued with the same
`evoloop run` command.

The report's *Steering ledger* section shows both entries, the number of evaluations at which each was
applied, and how many agent calls were shown the note.

## Next

To run a search on your own code, see [Setting up a search](setting-up.md). Before spending on real
agents, dry-run your project with `agents.backend: stub`.
