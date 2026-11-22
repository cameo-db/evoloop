# How it works

evoloop is a controller process, a set of LLM agent roles it calls, and a folder of files it writes.
This page first follows one design through the loop, then describes each part with the code that
implements it.

## One design, traced

???+ note "A local move from the built-in example, step by step"

    Take the built-in demo, a search for a small classifier, after 16 designs have been scored. A job
    finishes and a slot is free.

    **1. What kind of move?** The search is 40% through its budget, where the plan gives 65% of
    evaluations to new designs, 10% to crossover and 25% to local moves. So far local moves are furthest
    behind their share, so this slot is a local move. [Schedule](schedule.md) explains the
    shares.

    **2. Which parents?** The search keeps several families of designs. The family built on inputs that
    vary along the radius leads, at 0.967, and its best design is chosen as the parent.
    [Parent selection](parents.md) explains how.

    **3. Write it.** A local move is an edit, a settings move or an ablation. This one is an edit: the
    writer is sent the parent's code, the leaderboard, recent results and the lessons so far, and asked for
    one change. It adds a second hidden layer.

    ```python
    HIDDEN = [12]        ->        HIDDEN = [12, 8]
    ```

    In the demo the writer is a script. In a real search it is an agent, and the exchange looks like this:

    ??? note "The request and the reply (abridged)"
        The request:

        ```json
        {"request": {"mode": "local", "move": "structural_change", "step": "normal",
                     "instruction": "ONE attributable change to the parent's structure..."},
         "blocks_you_may_change": {"model": {"kind": "structure", "role": "network"},
                                   "fit": {"kind": "params", "role": "optimizer"}},
         "parents": [{"candidate": "C14", "score": 0.967, "family": "periodic features",
                      "blocks": {"model": "HIDDEN = [12]\nACTIVATION = \"tanh\"\n\ndef features(x): ..."}}],
         "leaderboard": ["..."], "recent": ["..."], "lessons": ["..."]}
        ```

        The reply, with the new code and a forecast:

        ```json
        {"proposals": [{"name": "a second layer", "family": "periodic features",
                        "hypothesis": "A second layer lets the network combine the radial waves with the coordinates.",
                        "expected_gain": {"gain": 0.8, "probability_better": 0.4},
                        "change_summary": "added a narrower layer on top",
                        "blocks": {"model": "HIDDEN = [12, 8]\nACTIVATION = \"tanh\"\n\ndef features(x): ..."}}]}
        ```


    Some moves need no agent: a block swap between two parents, and settings drawn by a sampler, are made
    in code. [Moves](moves.md) lists them.

    **4. Check it.** Before anything is trained, Python checks that only the marked blocks changed, that
    the code parses, that no forbidden term appears, and that the design is not a copy of one already
    tried. A design that fails goes back to step 3 or is dropped; it costs nothing.

    **5. Run and score it.** The design runs as its own job: your evaluator trains it and writes a
    `result.json` with the score. Here it scores 0.970. If the evaluator reports progress, a design that is
    clearly behind can be stopped part way ([Early stopping](early-stopping.md)).

    **6. Record.** The design, its code, its parent, the agent's forecast and the result are appended to
    the run's files. The next slot is chosen from those files, and so is everything an agent is shown
    later.


## The controller

`evoloop run` starts one Python process, the controller
([controller.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py)). It repeats the same turn every few seconds until the budget is
spent:

| | In each turn the controller |
|---|---|
| 1 | reads any steering requests you sent (`evoloop set`, `note`, `stop`) and applies or refuses them |
| 2 | checks the running jobs: collects results, stops a candidate that is behind at an early-stopping point or outside a limit |
| 3 | records the candidates the agents have finished writing, after checking them |
| 4 | calls the periodic agents if they are due (analyst, strategist, assessor), and retrains the leader on a new seed if due |
| 5 | for each free job slot, while budget remains, starts a new candidate (below) |
| 6 | writes `status.json` |

The controller keeps no state that is not on disk. If it stops, `evoloop run` with the same name
continues from the files, including jobs that were still running.

## Starting one design

| Step | What happens | Code |
|---|---|---|
| Kind of move | `next_mode` returns `new`, `novel`, `cross` or `local`: whichever is furthest behind its share of the budget in `schedule.phases`. With `harness.coordinator: agent`, an agent picks among the possible kinds | [schedule.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/schedule.py) |
| Parents | the strategy's `choose` returns the parent designs for that kind of move | [strategies/](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies) |
| Write | for a local move, the kind is chosen to keep to `schedule.local_mix` (edit, settings, ablation); for a crossover, from `crossover.kinds`. The writer agent is called with the parents' code and the results so far, and returns new block contents with a forecast. A block swap, or hyperparameters from the sampler or the Bayesian optimizer, is made in code with no call | [design.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/design.py) |
| Check | only blocks that are open may change, the code must parse, forbidden terms are refused, an exact copy of an earlier design is refused | [space.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py) |
| Run | a working copy of your code is made with the new blocks, and your evaluator runs in it as a local process or a Slurm job | [jobs.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py) |
| Score | the controller reads `result.json`. A result outside a limit, or missing a metric that a limit names, is rejected | [controller.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py) |

## The agents

Each role is one LLM call with its own instructions. Roles do not call each other; each is sent data
from the run's files. The instructions are in [agents.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/agents.py).

| Role | Called | Sent | Returns |
|---|---|---|---|
| writer | once per candidate written by an agent | `task.md`, the parents' blocks, the top of the leaderboard, the last 10 results, the analyst's lessons, your notes, the skill's text | one or more proposals: block contents, a hypothesis, a forecast of the gain |
| analyst | every 8 finished designs (`harness.analyst_every`), unless `harness.level` is `minimal` | the results since its last call, the leaderboard, earlier lessons | lessons, each citing runs. A lesson is marked supported only if its evidence spans two families |
| strategist | every 15 scored designs and on a plateau, if `strategist.mode` is `advise` or `act` | counts worked out by code: gains by kind of move, diversity, budget left, its earlier decisions | up to two decisions from a fixed list. Code checks each against limits before applying it |
| coordinator | once per slot, if `harness.coordinator: agent` | the possible kinds of move with the parents code would use | the index of one option |
| assessor | at the points in `audit.reviews` | each role's calls with what followed | a written review per role, for you |
| translator | when you run `evoloop steer` | your words and the current settings | setting changes and notes, shown to you before anything is applied |

The LLM is called through the Anthropic API or the Claude Code command (`agents.backend`), or replaced
by a script for dry runs (`stub`). Backends are in [model/](https://github.com/cameo-db/evoloop/blob/main/evoloop/model).

## What a skill does

A skill is optional. Without one, the settings come from the run type and the defaults, and the agents are
sent your `task.md` and notes only. A skill is a YAML file ([skills/](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills), loaded by [skill.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/skill.py)). It affects a search in
two places in the code.

1. **Settings.** When the brief is read, the skill's `settings` are applied over the run type's and
   the autonomy level's, and under anything you set yourself (`form.resolve` in [form.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/form.py)).
   This is how `model-efficiency` makes the strategy `pareto`.
2. **Agent calls.** On every call to a writer, analyst, strategist or coordinator, the skill's
   `guidance` for that role is added to what the agent is sent, with its `diagnose` rules for the
   writer and analyst (`Agents._call` in [agents.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/agents.py)).

Its `needs` are checked too: the plan lists what your evaluator must report, and the report warns if a
required metric or reference row is missing.

## Where a setting's value comes from

The first source in this list that sets a value wins. `evoloop plan` prints the source of every value.

| Priority | Source |
|---|---|
| 1 | changes you make while the search runs |
| 2 | your brief |
| 3 | skill |
| 4 | autonomy level |
| 5 | run type |
| 6 | defaults for the size of the budget |
| 7 | site file for this machine (compute settings only) |
| 8 | built-in default |

## What code enforces

These hold under every setting, because they are checks in code and not instructions to an agent:

- the budget in evaluations and the cap on agent spend;
- `limits` on any metric your evaluator reports;
- only marked, open blocks change, and the rest of your code is checked by hash at every start;
- at least 10% of evaluations go to new designs when a strategist is adjusting the schedule;
- every design, score, agent call and setting change is appended to files in the run's folder.

## Files

A run's folder holds `runs.jsonl`, `models.jsonl`, `calls.jsonl`, `ledger.jsonl` and others, one JSON
object per line. [Files of a run](records.md) lists them. The search state is rebuilt from these files
on every turn ([store.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py)).

## More detail

[Schedule](schedule.md) · [Parent selection](parents.md) · [Moves](moves.md) ·
[Early stopping](early-stopping.md) · [Comparing scores](comparable.md) · [Agents](agents.md) ·
[Comparison with FunSearch and AlphaEvolve](compared.md) · [Glossary](glossary.md)
