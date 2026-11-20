# evoloop

evoloop improves a project's code by evolutionary search. You mark the parts of the code that may
change. Language-model agents write new versions of those parts; code decides what gets tried next,
trains each design once, keeps the score, and records everything.

It is not one loop. A search is put together from a few choices, made when it is set up and
changeable while it runs.

| Choice | Options | Set with |
|---|---|---|
| Run type | `explore_then_exploit`, `refine`, `survey`, `discovery`, `settings_only`, `custom` | `run.type` |
| Evolution strategy | `lineage`, `archive`, `tournament`, `greedy`; any of them on islands | `strategy.mechanism`, `strategy.islands` |
| Schedule | shares of new designs, crossover and local moves by phase; fixed or adaptive | `schedule.phases` |
| Crossover | `block_swap`, `graft`, `hybrid` | `crossover.kinds` |
| Search space | settings only, one module, the architecture, the architecture and the recipe, your own list | `space.preset` |
| Harness | `minimal`, `standard`, `full`; slots chosen by code or by a coordinator agent | `harness.level`, `harness.coordinator` |
| Audit | a scorecard by code; reviews of each agent at the points you choose | `audit.reviews` |

The [menu](menu.md) lists every option with what it does, and what each preset sets.

## The loop in one picture

```
            you                                  the run's records
   brief.yaml  +  steering  ───────────────►  ledger (every change, by whom)
                                                      │
                                                      ▼
   ┌──────────────────────────  a job slot is free  ──────────────────────────┐
   │                                                                          │
   │  schedule      which kind of slot?      new · novel · cross · local      │
   │  strategy      which parents?           from the results alone           │
   │  writer        writes the blocks        an agent, or code                │
   │  checks        only open blocks, parses, not a copy, nothing forbidden   │
   │  job           trains it once           one job per design               │
   │                                                                          │
   └────────────────────────────────┬─────────────────────────────────────────┘
                                    ▼
        results (models, recipes, runs)  ──►  report · scorecard · study file
```

Three things hold everywhere:

- **Agents never talk to each other.** Each call is a fresh context built from the run's records, and
  whatever a role returns is checked by code and written to those records.
- **A strategy keeps no state.** Its population is worked out from the results each time, which is why
  the strategy can be changed in the middle of a run.
- **Nothing is filled in by guessing.** A required field that is empty becomes a question, and a run
  does not start until you have confirmed the brief by name.

## Where to go next

- [First run](quickstart.md): the built-in example, with stub agents, at no cost.
- [Setting up a search](setting-up.md): the search folder, marking the code, the brief.
- [How a search works](how-it-works.md): the schedule, the strategies, crossover, novelty.
- [Steering a run](steering.md): changing settings, notes to the agents, stopping, without a restart.
- [Auditing the agents](auditing.md): the scorecard and the reviews.
- [Status and limits](status.md): what has been tested, what is not built, what is known to be weak.
