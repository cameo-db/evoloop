# Menu

Every choice a run can make. This page is written from the code (`evoloop menu --markdown`), so it lists exactly what the brief accepts.

## Run types

Set with `run.type`.

| Option | What it does |
|---|---|
| `explore_then_exploit` | Most searches. Mostly new designs for the first 60% of the budget, then mostly local work and crossover on what was found. |
| `refine` | A known good model. Few lineages, mostly local moves, the overall shape of the model kept. |
| `survey` | A new problem. Mostly new designs throughout, kept on an archive so each kind stays in play. |
| `discovery` | Long runs with cheap evaluations, aiming for something unusual. Architecture and recipe both open, novelty high, the lightest harness. |
| `settings_only` | A hyperparameter search. No structure changes; every slot is a settings move. |
| `custom` | Your own choices. Describe the search in `run.description`; where you set nothing, the guidance for the size of the budget and then the defaults apply. |

### What each run type sets

A run type is a bundle of settings. Anything you set yourself in the brief wins over it.

**`explore_then_exploit`**

```
harness.level = "full"
strategy.mechanism = "lineage"
```

**`refine`**

```
harness.level = "full"
population.lineages = 3
schedule.novel_share = 0.0
schedule.phases = [{"until": 1.0, "new": 0.1, "cross": 0.2, "local": 0.7}]
space.preset = "template"
strategy.mechanism = "lineage"
```

**`survey`**

```
harness.level = "standard"
schedule.phases = [{"until": 1.0, "new": 0.75, "cross": 0.1, "local": 0.15}]
strategy.mechanism = "archive"
```

**`discovery`**

```
harness.level = "minimal"
schedule.novel_share = 0.5
schedule.novelty = 0.7
schedule.phases = [{"until": 1.0, "new": 0.6, "cross": 0.15, "local": 0.25}]
space.preset = "architecture_and_recipe"
strategy.mechanism = "archive"
```

**`settings_only`**

```
crossover.kinds = []
harness.level = "minimal"
schedule.local_mix = {"edit": 0.0, "settings": 1.0, "ablation": 0.0}
schedule.novel_share = 0.0
schedule.phases = [{"until": 1.0, "new": 0.0, "cross": 0.0, "local": 1.0}]
space.preset = "settings_only"
strategy.mechanism = "greedy"
```

**`custom`**

Sets nothing itself.

## Evolution strategies

Set with `strategy.mechanism`.

| Option | What it does |
|---|---|
| `lineage` | Species kept alive side by side. A new lineage gets a protected trial, the best few are active, none takes more than its quota of the local slots, and one that stops gaining retires to the bench. |
| `archive` | The best of each kind of design on a grid (by family and size). Parents are drawn across the grid, the less visited cells favoured in proportion to `schedule.novelty`. |
| `tournament` | Draw a few of the most recent designs and build on the best of them. Older designs leave the population however good they were, so one lucky score cannot dominate for long. |
| `greedy` | Always build on the current best (or one tied with it within the noise). The right choice when the budget is too small for a population. |

Set `strategy.islands` above 1 to run that many separate populations of the chosen strategy. Each sees its own results only; every `strategy.migrate_every` scored runs the best design of another island is brought in as a parent.

## Slot modes

Set with `schedule.phases`.

| Option | What it does |
|---|---|
| `new` | A new family from the known design space (broad exploration). Founds a lineage. |
| `novel` | A design built from or against designs that were rarely built on. Founds a lineage. |
| `cross` | A crossover of two lineages, of one of the kinds in `crossover.kinds`. |
| `local` | A local move on an existing lineage (exploitation), of one of the kinds in `schedule.local_mix`. |

## Crossover kinds

Set with `crossover.kinds`.

| Option | What it does |
|---|---|
| `block_swap` | Code takes whole marked blocks from each parent: the trunk of one with the heads of the other, or the model of one with the recipe of the other. No agent call. Needs two open blocks that differ. |
| `graft` | The one change that gained most in the donor's history, a recorded and measured difference, is applied to the recipient by an agent. The child stays in the recipient's lineage. |
| `hybrid` | An agent writes one design from the two parents and says which parts came from each. The child founds a new lineage with both parents on record. |

For every kind, the second parent is the candidate whose errors fall least like the first one's, when the adapter reports where a model's errors fall (`signature` in result.json); otherwise one of another family.

## Local moves

Set with `schedule.local_mix`.

| Option | What it does |
|---|---|
| `edit` | One attributable change to the parent's structure, so that the result has one cause. Recorded as `structural_change`. |
| `settings` | Only values in the params blocks change. Recorded as `settings_move`. |
| `ablation` | One component is removed and nothing else changes: shows what is dead weight. |

## Search spaces

Set with `space.preset`.

| Option | What it does |
|---|---|
| `settings_only` | Only params blocks are open. |
| `module` | Only the structure blocks whose role or name is listed in `space.modules`, and the params blocks. |
| `template` | Every model block is open, and writers are told to keep the overall shape of the baseline. |
| `open_architecture` | Every model block is open; the training recipe is fixed. |
| `architecture_and_recipe` | Every marked block is open: the model and the recipe (the roles in `space.recipe_roles`). |
| `custom` | Only what `space.roles` opens, role by role: {role: open \| settings \| fixed}. |

## Harness levels

Set with `harness.level`.

| Option | What it does |
|---|---|
| `minimal` | A writer only: no analyst, a short context. For cheap evaluations and long runs. |
| `standard` | Adds the analyst, which writes lessons from the results every `harness.analyst_every` runs. |
| `full` | Adds a re-check of the leader on a new seed every 20 designs (or `evaluation.recheck_every`). |

## Coordinator

Set with `harness.coordinator`.

| Option | What it does |
|---|---|
| `code` | The schedule picks the kind of slot and the strategy picks the parents. |
| `agent` | An agent picks each slot from options code prepares; what the schedule alone would have picked is recorded beside every choice. |

## Review schedules

Set with `audit.reviews`.

| Option | What it does |
|---|---|
| `none` | No reviews; the scorecard only. |
| `end` | One review, when the run ends. |
| `halfway` | At 50% of the budget and at the end. |
| `thirds` | At 33%, 67% and the end. |
| `quarterly` | At 25%, 50%, 75% and the end. |
| `on_demand` | Only when asked for with `evoloop review`. |

Or a list of shares of the budget, such as [0.1, 0.4, 0.8].

## Budget guidance

Applied below the run type and the brief, from `budget.evaluations`: under 45 is "about 30", under 180 "about 100", under 600 "about 300", otherwise "1,000 or more". When the guidance suggests a different strategy from the run type's, `evoloop plan` says so and the run type's stands.

**about 30 evaluations**

```
audit.reviews = "end"
crossover.kinds = ["graft"]
population.lineages = 3
population.trial_runs = 1
schedule.adaptive = 0.0
schedule.novel_share = 0.0
strategy.mechanism = "greedy"
variation.proposals_per_slot = 4
```

**about 100 evaluations**

```
audit.reviews = "halfway"
crossover.kinds = ["graft", "hybrid"]
population.lineages = 6
population.trial_runs = 2
schedule.novel_share = 0.15
variation.proposals_per_slot = 3
```

**about 300 evaluations**

```
audit.reviews = "quarterly"
population.lineages = 10
population.trial_runs = 2
schedule.novel_share = 0.33
variation.proposals_per_slot = 2
```

**1,000 or more evaluations**

```
audit.reviews = "on_demand"
harness.level = "minimal"
schedule.adaptive = 0.5
strategy.mechanism = "archive"
variation.proposals_per_slot = 1
```
