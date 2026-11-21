# evoloop

[![Documentation](https://readthedocs.org/projects/evoloop/badge/?version=latest)](https://evoloop.readthedocs.io/en/latest/)

**Documentation: <https://evoloop.readthedocs.io>**

Evolutionary search over marked blocks of a project's code. Language-model agents write the designs;
code does the selection, the schedule, the budget, the checks and the records.

It is not one loop. A search is put together from a few choices, made when it is set up and
changeable while it runs:

| Choice | Options |
|---|---|
| Run type | `explore_then_exploit` (the default), `refine`, `survey`, `discovery`, `settings_only`, `custom` |
| Skill | what kind of optimisation it is: `performance`, `distillation`, `tuning` (Bayesian, no agent calls), `efficiency`, `mechanistic`, or your own |
| Evolution strategy | `lineage`, `archive`, `tournament`, `pareto` (a trade-off front), `greedy`; any of them on several islands, with or without resets |
| Early stopping | a single screen of new designs, or a promotion ladder (successive halving) over all designs |
| Diversity | by family and size, or by what the trained model does (where its errors fall) |
| Schedule | shares of new designs, crossover and local moves by phase; fixed or adaptive |
| Crossover | `block_swap`, `graft`, `hybrid` |
| Search space | settings only, one module, the architecture, the architecture and the training recipe, your own list |
| Harness | `minimal`, `standard`, `full`; slots chosen by code or by a coordinator agent |
| Model and effort | any Claude model, at any effort level, for every role or role by role; defaults you can change |
| Writers | one model or a mix by share; whole blocks or find-and-replace edits; approaches kept or dropped by their record |
| Who runs it | code (deterministic), or an agent you talk to with `evoloop chat` |
| Autonomy | `harnessed`, `guided` or `agentic`: how much the agents decide, with the likely cost of each shown in the plan |
| Strategist | an agent that reviews the search at intervals and may change its course, within bounds you set |
| Spend | a dollar cap on the agents, with the run made cheaper by code when it is heading past the cap |
| Audit | a scorecard by code; reviews of each agent at the points you choose |

`evoloop menu` prints every option with what it does, what each preset sets, and every field of the brief.

## A first run, at no cost

```
pip install -e .
evoloop example demo                        # a small formula search with stub agents
evoloop plan demo                           # every setting, with where it came from
evoloop brief demo --confirm "Your Name"    # your agreement to the plan
evoloop run demo --name first
evoloop report demo --name first
```

## Your own search, in short

```
evoloop init mysearch --source path/to/project   # brief.yaml, task.md, base/, adapter/run.py
```

1. **Mark the code** in `base/`: `# EVOLVE-BLOCK-START name=trunk kind=structure role=trunk` ... `# EVOLVE-BLOCK-END`.
2. **Write `task.md` and `adapter/run.py`** (how one design is trained; it writes `result.json`).
3. **Answer the questions**: `evoloop setup mysearch` in the terminal, `evoloop form mysearch` for a form in a
   browser, or an agent in a chat. Each shows its best guess where it has one and where you are in the list.
   Fields you leave take their value from the run type, then the guidance for the size of
   the budget, then the default. A guess is only ever a suggestion: you see it and can change it.
4. **Read `evoloop plan mysearch`, then confirm** with `evoloop brief mysearch --confirm "Your Name"`.
5. **Run**: `evoloop run mysearch --name r1`.

## Steering, without a restart

```
evoloop set   mysearch --name r1 schedule.novelty=0.6 budget.evaluations=300 --by "Your Name"
evoloop note  mysearch --name r1 "No attention layers." --roles writer --by "Your Name"
evoloop steer mysearch --name r1 "more novelty from here, and keep models small" --by "Your Name"
evoloop chat  mysearch --name r1 --by "Your Name"     # with harness.conductor: agent, talk to the agent that runs the search
evoloop stop  mysearch --name r1 --by "Your Name"
```

Every change is checked by code and recorded in the run's ledger, applied or refused, with your name,
the old value and the new one.

## Documentation

The full documentation is at <https://evoloop.readthedocs.io>. The same pages are in [`docs/`](docs/index.md):

- [Overview](docs/index.md) and [first run](docs/quickstart.md)
- [Setting up a search](docs/setting-up.md)
- [Skills](docs/skills.md): performance, distillation, tuning, efficiency, mechanistic models, or your own
- [How a search works](docs/how-it-works.md): the schedule, the strategies, crossover, novelty
- [Model and effort](docs/models.md) and [agentic or harnessed, and what it costs](docs/autonomy.md)
- [Steering a run](docs/steering.md), [the strategist and the budget](docs/strategist.md), [auditing the agents](docs/auditing.md)
- [The project's code](docs/project-contract.md): the adapter, `result.json`, Slurm
- [Records and the study file](docs/records.md) (CAMEO entry format 0.4)
- Reference: [menu of choices and presets](docs/menu.md), [fields of the brief](docs/fields.md),
  [commands](docs/commands.md)
- [Status and limits](docs/status.md): what has been tested, what is not built

## Status

Version 0.2. It passes its tests on the built-in example with stub agents and has run that example on
a real Slurm cluster. It has not yet been run with a real agent or on a real training task; see
[Status and limits](docs/status.md) before relying on it.

## Tests

```
pytest tests        # about two minutes on eight cores; run it on a compute node, not a login node
```
