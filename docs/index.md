# evoloop

evoloop improves a project's code by evolutionary search. You mark the parts of the code that may
change. Language-model agents write new versions of those parts; code decides what gets tried next,
trains each design once, keeps the score, and records everything.

It is built for searches where one evaluation is a training run: tens to hundreds of evaluations, each
costing GPU time, with scores that differ between two fits of the same model. And it is not one loop. A
search is put together from choices made when it is set up, and changeable while it runs.

## The two choices that decide most of the rest

| Choice | It says | Options |
|---|---|---|
| **Skill** (`run.skill`) | what kind of problem this is | `performance`, `distillation`, `tuning`, `efficiency`, `mechanistic`, or [your own](skills.md) |
| **Run type** (`run.type`) | how to search | `explore_then_exploit`, `refine`, `survey`, `discovery`, `settings_only`, `custom` |

## Everything else, by what it is for

| For | Choice | Options | Set with |
|---|---|---|---|
| Selection | Evolution strategy | `lineage`, `archive`, `tournament`, `pareto`, `greedy`; any of them on islands, with or without resets | `strategy.mechanism`, `strategy.islands`, `strategy.reset_every` |
| | A second objective | the score with size, speed or any reported figure | `strategy.second_metric` |
| Exploration | Schedule | shares of new designs, crossover and local moves by phase; fixed or adaptive | `schedule.phases` |
| | Novelty | how far a design far from everything tried is favoured; measured on code or on behaviour | `schedule.novelty`, `schedule.novelty_measure` |
| | Crossover | `block_swap`, `graft`, `hybrid` | `crossover.kinds` |
| What may change | Search space | settings only, one module, the architecture, the architecture and the recipe, your own list | `space.preset` |
| Cost of an evaluation | Early stopping | one screen of new designs, or a promotion ladder over all designs | `evaluation.ladder` |
| | Starting point | from scratch, or from the parent's weights | `evaluation.inherit_weights` |
| The writers | Model and effort | any Claude model and effort level, for every role or role by role; several models by share | `agents.default_model`, `agents.effort`, `agents.writer_mix` |
| | How a change is returned | whole blocks, or find-and-replace edits | `variation.edit_format` |
| | Ways of working | approaches handed to the writers, kept or dropped by their record | `variation.approaches` |
| | Settings moves | an agent, a sampler, or a Bayesian estimator in code | `variation.settings_by` |
| Who decides | Who runs the search | code (deterministic), or an agent you talk to | `harness.conductor` |
| | Strategist | off, advising, or acting within bounds you set | `strategist.mode` |
| | Autonomy | `harnessed`, `guided`, `agentic`: how much the agents decide | `harness.autonomy` |
| | Harness | `minimal`, `standard`, `full`; slots chosen by code or by a coordinator agent | `harness.level`, `harness.coordinator` |
| Oversight | Spend | a dollar cap on the agents, paced by code | `budget.model_dollars`, `budget.spend_policy` |
| | Limits | hard bounds on size, speed or any reported figure | `limits` |
| | Audit | a scorecard by code; reviews of each agent at the points you choose | `audit.reviews` |

The [menu](menu.md) lists every option with what it does, and what each preset sets.
[How it compares with established methods](compared.md) says where each mechanism comes from.

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
- **A guess is only ever a suggestion.** The tool and an agent propose answers with their reasons; you see
  every one and can change it. A required field with no answer stays a question, and a run
  does not start until you have confirmed the brief by name.

## Where to go next

- [First run](quickstart.md): the built-in example, with stub agents, at no cost.
- [Setting up a search](setting-up.md): the search folder, marking the code, the brief.
- [Skills](skills.md): the kind of optimisation, and the guidance each gives the agents.
- [How a search works](how-it-works.md): the schedule, the strategies, crossover, novelty, early stopping, the writers.
- [How it compares with established methods](compared.md): FunSearch, AlphaEvolve, regularized evolution, and what differs here.
- [Steering a run](steering.md): changing settings, notes to the agents, stopping, without a restart.
- [Model and effort](models.md): which model each role runs on and how hard it reasons, with defaults you can change.
- [Agentic or harnessed, and what it costs](autonomy.md): how much the agents decide, with an estimate of the cost of each level.
- [The strategist and the budget](strategist.md): an agent that can change the course of a search or run it and talk to you, and the spend cap.
- [Auditing the agents](auditing.md): the scorecard and the reviews.
- [The project's code](project-contract.md): what your adapter is given and what it writes.
- [Records and the study file](records.md): what a run leaves behind.
- [Status and limits](status.md): what has been tested, what is not built, what is known to be weak.
