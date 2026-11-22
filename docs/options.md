# Search options on one page

Every choice that shapes a search, with the setting that makes it and the file that implements it.
[Choose a skill and a run type](which-search.md) helps you pick; this page is the full list.

## One iteration

Each time a job slot is free, evoloop does this. The last column is the file that implements the step.

| Step | What happens | Decided by | Setting | Code |
|---|---|---|---|---|
| 1 | Pick the kind of move: a new design, a crossover of two designs, or a local move on one (an edit, a hyperparameter change, an ablation) | the schedule, in code. Optionally a coordinator agent picks among the options code prepares | `schedule.phases`, `harness.coordinator` | [schedule.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/schedule.py) |
| 2 | Pick the parent design or designs | the search strategy, in code | `strategy.mechanism` | [strategies/](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies) |
| 3 | Write the candidate: new contents for the marked blocks | a writer agent (LLM). Code alone for a block swap or sampled hyperparameters | `agents.default_model`, `variation.settings_by` | [design.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/design.py), prompts in [agents.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/agents.py) |
| 4 | Check it: only marked blocks changed, it parses, it is not a copy of an earlier design | code | `space.preset`, `space.forbidden_terms` | [space.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/space.py) |
| 5 | Run your evaluator on it as its own job, locally or on Slurm. Optionally stop it early if it is behind | your script; early stopping by code | `evaluation.allowance`, `evaluation.ladder` | [jobs.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/jobs.py), [controller.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/controller.py) |
| 6 | Record the design, its parent, its score and the agent's forecast | code | | [store.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/store.py) |

Every 8 designs an analyst agent summarizes what the results show, and the writers are given that
summary. [How it works](how-it-works.md) has the full loop.

## Search strategies

The strategy is the rule for step 2: which earlier designs are built on. Set it with
`strategy.mechanism`.

| Strategy | Parents are chosen from | Method it follows | Code |
|---|---|---|---|
| `lineage` (default) | the best design of each of several lineages. A new lineage gets protected evaluations before it competes, and no lineage gets more than 40% of the local moves | speciation with protected niches, as in NEAT | [strategies/lineage.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/lineage.py) |
| `archive` | the best design in each cell of a grid. A cell is a family and a size band, or a group of models whose errors fall alike | MAP-Elites. With islands, the program database of AlphaEvolve | [strategies/archive.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/archive.py) |
| `tournament` | the best of 3 drawn from the 24 most recent designs. Older designs drop out | regularized (aging) evolution, Real et al. 2019 | [strategies/tournament.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/tournament.py) |
| `pareto` | designs not beaten on both the score and a second metric such as parameter count | non-dominated sorting, as in NSGA-II | [strategies/pareto.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/pareto.py) |
| `greedy` | the single best design | hill climbing | [strategies/greedy.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/greedy.py) |

Any strategy can run as several separate populations (`strategy.islands`), and the weaker populations
can be restarted from the best one (`strategy.reset_every`), as in FunSearch
([strategies/islands.py](https://github.com/cameo-db/evoloop/blob/main/evoloop/strategies/islands.py)).

Other mechanisms, each an option:

| Mechanism | Setting | Method it follows |
|---|---|---|
| Marked regions of a program evolved by an LLM | `EVOLVE-BLOCK` markers in your code | FunSearch, AlphaEvolve |
| Explore first, then exploit: shares of new designs, crossover and local moves by phase of the budget | `schedule.phases` | |
| Stop weak candidates part way through training | `evaluation.ladder` | successive halving, ASHA |
| A cheap model for most candidates and a strong one for some | `agents.writer_mix` | AlphaEvolve |
| Candidates returned as diffs | `variation.edit_format: diff` | AlphaEvolve |
| Hyperparameters drawn by a Bayesian optimizer, with no agent | `variation.settings_by: tpe` | TPE (Optuna, Hyperopt) |
| Designs grouped by where their errors fall | `strategy.descriptors: [behaviour]` | FunSearch's signature clusters |

To search in the manner of FunSearch: `archive` with `strategy.descriptors: [behaviour]`,
`strategy.islands: 4`, `strategy.reset_every: 40`. In the manner of AlphaEvolve: `archive` on
`strategy.islands: 3` with `agents.writer_mix`, `variation.edit_format: diff` and
`evaluation.ladder`. These are approximations.
[Comparison with other AutoResearch methods](compared.md) lists the differences.

## Harness and autonomy

Two settings decide which agents run and how much they control.

`harness.level` sets which agent roles run alongside the writer:

| `harness.level` | Agents that run |
|---|---|
| `minimal` | writer |
| `standard` | writer, and an analyst that summarizes results every 8 designs |
| `full` (default) | writer and analyst, and the leading design is retrained on a new seed every 20 designs |

`harness.autonomy` is a preset for how much the agents decide. More autonomy means more LLM calls.

| | `harnessed` | `guided` | `agentic` |
|---|---|---|---|
| Kind of move for each slot | schedule (code) | schedule (code) | a coordinator agent, from options code prepares |
| Parents | strategy (code) | strategy (code) | strategy (code) |
| Strategist agent that can shift the schedule | off | on, within limits | on, more often, wider limits |
| Hyperparameter moves | random sampler (code) | writer agent | writer agent |
| Proposals written per slot | 1 | set by budget size | 3 |
| LLM calls for 100 designs, estimated | about 110 | about 140 | about 270 |

With any of these, code enforces the budget, the limits, the checks in step 4 and a minimum share of new
designs. `harness.conductor: agent` additionally lets you talk to the strategist with `evoloop chat`.
[Agents](agents.md) has the detail.

## Run types

A run type is a preset for the strategy, the harness and the schedule.

| `run.type` | Strategy | Agents | New / crossover / local |
|---|---|---|---|
| `explore_then_exploit` (default) | `lineage` | full harness, strategist on | 65 / 10 / 25 for the first 60% of the budget, then 15 / 25 / 60 |
| `refine` | `lineage`, 3 lineages | full harness, strategist on | 10 / 20 / 70 |
| `survey` | `archive` | writer and analyst, strategist on | 75 / 10 / 15 |
| `discovery` | `archive` | writer only | 60 / 15 / 25, novelty raised |
| `settings_only` | `greedy` | writer only | hyperparameter moves only |

## Skills

Skills are optional. evoloop runs without one: the settings then come from the run type and the defaults,
and the agents see only your `task.md` and any notes you send. A skill saves you supplying that guidance
yourself. It adapts the general search to one goal, and is
a YAML file with three parts: settings for the choices in the tables above, text that is added to
every agent call, and the list of measurements your evaluator must report.

You name a skill in the brief (`run.skill: model-efficiency`). evoloop copies its file into your search
folder as soon as you choose it and reads that copy. You can [edit it during setup](skills.md), or merge
several into one file. This table is generated from the files.

--8<-- "generated/skills-table.md"

Each skill's page shows its settings, the exact text it sends to each agent, and the file.
[Edit, merge or write a skill](skills.md) · [Skill file format](skill-format.md)

