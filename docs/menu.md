# Options and presets

Every option a search can be given, and what each preset sets. Written from the code (`evoloop menu --markdown`), so it lists exactly what the brief accepts.

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

### Settings of each run type

It is a bundle of settings. Anything you set yourself in the brief wins over it.

**`explore_then_exploit`**

```
harness.level = "full"
strategist.mode = "act"
strategy.mechanism = "lineage"
```

**`refine`**

```
harness.level = "full"
population.lineages = 3
schedule.novel_share = 0.0
schedule.phases = [{"until": 1.0, "new": 0.1, "cross": 0.2, "local": 0.7}]
space.preset = "template"
strategist.mode = "act"
strategy.mechanism = "lineage"
```

**`survey`**

```
harness.level = "standard"
schedule.phases = [{"until": 1.0, "new": 0.75, "cross": 0.1, "local": 0.15}]
strategist.mode = "act"
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

## Skills: the kind of optimization

Set with `run.skill`.

| Option | What it does |
|---|---|
| `model-performance` | Raise the validation score by whatever the open blocks allow. Size and speed are not weighed unless you set limits. |
| `model-distillation` | Train a smaller or faster student to match a teacher. The student's architecture and its training recipe (loss, optimizer, learning rate, regularization, augmentation) are both open. |
| `model-efficiency` | Design a smaller or faster student and train it to match the model you already have. The original model is the teacher. The student's architecture and its training against the teacher are both searched. |
| `model-ensemble-members` | Find models that are each good and that make different errors from one another, so that averaging them gains more than averaging copies of the best one. |
| `model-finetuning` | Start from a pretrained model and search over how to adapt it (what to freeze, what to add, the learning rates by layer, how long to train). |
| `model-mechanistic` | Improve a model that is interpretable by design, where the parameters stand for something (motifs in filters, a graph of interactions, rates and affinities in a biophysical model). The structure that carries the meaning is kept. |
| `model-size-frontier` | Find the best model at each size (or speed), from very small to large, so that the result is a whole trade-off curve to choose from and not one winner. |
| `model-training-recipe` | The architecture is fixed; the training recipe is open (the loss, the optimizer, the learning-rate schedule, regularization, augmentation). Between tuning numbers and changing the model. |
| `algorithm-runtime` | Speed up a piece of code (or cut its memory) while its output stays correct. The score is a measured time; a design whose output is wrong is rejected, not scored. |
| `bioinformatics-algorithm` | Improve a method that analyses biological data (an aligner, a caller, a peak finder, a quantifier, a scoring function) against a truth set, without breaking the conventions of the formats and coordinates it works in. |
| `data-pipeline` | Speed up a multi-step data pipeline (reading, transforming, joining, writing) or cut its memory and cost, with its output unchanged. |
| `settings-tuning` | An agent tunes the hyperparameters of a fixed model, the architecture's (depth, widths, kernel sizes) and the training's (learning rate, weight decay, schedule), reading the results of earlier trials before choosing the next. |
| `settings-tuning-bayesian` | A built-in Bayesian optimizer (TPE) draws each set of hyperparameters from the results of earlier trials. No agent is called, so the search costs compute only. |

A skill says what kind of problem the search is; the run type says how to search. Skills can be combined (`run.skill: [a, b]`), and a search gets its own editable copy of each in its `skills/` folder. `evoloop skills NAME` shows a skill in full, and `evoloop skills NAME --copy DIR` writes it out as a folder to edit and use as your own (`run.skill: DIR`).

### Settings of each skill

It is a bundle of settings. Anything you set yourself in the brief wins over it.

**`model-performance`**

Sets nothing itself.

**`model-distillation`**

```
report.columns = ["speed"]
space.preset = "architecture_and_recipe"
variation.approach_seeds = ["Change how the student is trained before changing the student: the loss against the teacher, the weight between teacher and measured targets, the augmentations the teacher labels.", "Give the student inputs the measured data does not contain (perturbed, shuffled, synthetic) and let the teacher label them.", "Match the student's capacity to the gap: if it underfits the teacher, widen or deepen; if it matches the teacher on training inputs and not on held-out ones, regularize or add teacher-labelled data.", "Train longer at a lower learning rate before concluding a student is too small."]
variation.approaches = "fixed"
```

**`model-efficiency`**

```
report.columns = ["speed"]
schedule.local_mix = {"edit": 0.5, "settings": 0.3, "ablation": 0.2}
space.preset = "architecture_and_recipe"
strategy.mechanism = "pareto"
strategy.second_direction = "minimize"
strategy.second_metric = "parameters"
```

**`model-ensemble-members`**

```
schedule.novelty = 0.6
schedule.novelty_measure = "behaviour"
schedule.phases = [{"until": 0.6, "new": 0.6, "cross": 0.1, "local": 0.3}, {"until": 1.0, "new": 0.25, "cross": 0.15, "local": 0.6}]
strategy.descriptors = ["behaviour"]
strategy.mechanism = "archive"
```

**`model-finetuning`**

```
schedule.local_mix = {"edit": 0.4, "settings": 0.45, "ablation": 0.15}
schedule.novelty = 0.25
```

**`model-mechanistic`**

```
schedule.local_mix = {"edit": 0.45, "settings": 0.25, "ablation": 0.3}
schedule.novelty = 0.2
space.must_keep = ["Every learned parameter keeps a stated meaning (a motif, an interaction, a rate, an affinity, a concentration). Do not add a component whose parameters cannot be read this way, such as a dense network between the interpretable parts and the output.", "Keep the constraints that make the parts readable: signs, non-negativity, normalisation, saturation, conservation, units."]
space.preset = "template"
```

**`model-size-frontier`**

```
report.columns = ["speed"]
schedule.novelty = 0.6
schedule.phases = [{"until": 0.5, "new": 0.5, "cross": 0.15, "local": 0.35}, {"until": 1.0, "new": 0.2, "cross": 0.25, "local": 0.55}]
strategy.descriptors = ["size"]
strategy.mechanism = "archive"
```

**`model-training-recipe`**

```
schedule.local_mix = {"edit": 0.55, "settings": 0.35, "ablation": 0.1}
space.preset = "custom"
space.roles = {"loss": "open", "optimizer": "open", "schedule": "open", "augmentation": "open", "training": "open", "recipe": "open"}
```

**`algorithm-runtime`**

```
evaluation.screen_keep = 1.0
schedule.local_mix = {"edit": 0.75, "settings": 0.1, "ablation": 0.15}
schedule.novelty = 0.3
```

**`bioinformatics-algorithm`**

```
schedule.local_mix = {"edit": 0.6, "settings": 0.25, "ablation": 0.15}
schedule.novelty = 0.3
```

**`data-pipeline`**

```
evaluation.screen_keep = 1.0
schedule.local_mix = {"edit": 0.7, "settings": 0.2, "ablation": 0.1}
schedule.novelty = 0.3
```

**`settings-tuning`**

```
audit.reviews = "end"
harness.conductor = "code"
harness.coordinator = "code"
harness.level = "standard"
schedule.local_mix = {"edit": 0.0, "settings": 1.0, "ablation": 0.0}
schedule.novel_share = 0.0
schedule.phases = [{"until": 1.0, "new": 0.0, "cross": 0.0, "local": 1.0}]
space.preset = "settings_only"
strategist.mode = "off"
strategy.mechanism = "greedy"
variation.proposals_per_slot = 1
variation.settings_by = "agent"
variation.step_adaptation = false
```

**`settings-tuning-bayesian`**

```
audit.reviews = "none"
harness.conductor = "code"
harness.coordinator = "code"
harness.level = "minimal"
schedule.local_mix = {"edit": 0.0, "settings": 1.0, "ablation": 0.0}
schedule.novel_share = 0.0
schedule.phases = [{"until": 1.0, "new": 0.0, "cross": 0.0, "local": 1.0}]
space.preset = "settings_only"
strategist.mode = "off"
strategy.mechanism = "greedy"
variation.proposals_per_slot = 1
variation.settings_by = "tpe"
variation.step_adaptation = false
```

## Autonomy: agentic first, or strongly harnessed

Set with `harness.autonomy`.

| Option | What it does |
|---|---|
| `harnessed` | Code decides where the search goes: the schedule picks each slot, there is no strategist, settings moves are drawn by code, one proposal per slot. Agents write the designs and the lessons. The fewest agent calls of the three. |
| `guided` | Code runs the schedule and a strategist may change its course within the bounds you set. The middle. |
| `agentic` | Agents choose each slot and steer the search: an agent coordinator, a strategist that meets more often with wider bounds and asks first for nothing, three proposals per slot. Code still keeps the budget, the floor on new designs, the frozen problem and the records. The most agent calls of the three. |

Left empty, the run type decides. What you set yourself in the brief is kept at every level. `evoloop plan` and `evoloop estimate` show what the agents are likely to cost at each of the three.

### Settings of each level of autonomy

It is a bundle of settings. Anything you set yourself in the brief wins over it.

**`harnessed`**

```
audit.reviews = "end"
harness.coordinator = "code"
harness.level = "full"
strategist.mode = "off"
variation.proposals_per_slot = 1
variation.settings_by = "sampler"
```

**`guided`**

```
harness.coordinator = "code"
harness.level = "full"
strategist.mode = "act"
variation.settings_by = "agent"
```

**`agentic`**

```
audit.reviews = "thirds"
harness.analyst_every = 5
harness.coordinator = "agent"
harness.level = "full"
strategist.ask_first = []
strategist.every = 10
strategist.force_max = 8
strategist.max_share_shift = 0.3
strategist.mode = "act"
strategist.plateau = 8
variation.proposals_per_slot = 3
variation.settings_by = "agent"
```

## Models

Set with `agents.default_model`.

| Option | What it does |
|---|---|
| `claude-opus-5-5` | Claude Opus 5.5. $4 in, $20 out per million tokens. Effort: low, medium, high, xhigh, max (its own default: medium). The current Opus. |
| `claude-sonnet-5-5` | Claude Sonnet 5.5. $2 in, $10 out per million tokens. Effort: low, medium, high, xhigh, max (its own default: high). The current Sonnet: faster and cheaper. |
| `claude-haiku-5-5` | Claude Haiku 5.5. $0.1 in, $0.5 out per million tokens. Effort: low, medium, high, xhigh, max (its own default: medium). The cheapest; the price is for prompts up to 100K tokens. |
| `claude-fable-5-2` | Claude Fable 5.2. $8 in, $40 out per million tokens. Effort: low, medium, high, xhigh, max (its own default: high). The most capable; single calls can take minutes. |
| `claude-fable-5-1` | Claude Fable 5.1. $10 in, $50 out per million tokens. Effort: low, medium, high, xhigh, max (its own default: high). |
| `claude-opus-5` | Claude Opus 5. $5 in, $25 out per million tokens. Effort: low, medium, high, xhigh, max (its own default: high). |
| `claude-opus-4-8` | Claude Opus 4.8. $5 in, $25 out per million tokens. Effort: low, medium, high, xhigh, max (its own default: high). |
| `claude-opus-4-7` | Claude Opus 4.7. $5 in, $25 out per million tokens. Effort: low, medium, high, xhigh, max (its own default: high). |
| `claude-sonnet-5` | Claude Sonnet 5. $2 in, $10 out per million tokens. Effort: low, medium, high, xhigh, max (its own default: high). |
| `claude-opus-4-6` | Claude Opus 4.6. $5 in, $25 out per million tokens. Effort: low, medium, high, max (its own default: high). |
| `claude-sonnet-4-6` | Claude Sonnet 4.6. $3 in, $15 out per million tokens. Effort: low, medium, high, max (its own default: high). |
| `claude-haiku-4-5` | Claude Haiku 4.5. $1 in, $5 out per million tokens. Effort: none. Takes no effort setting. |

The default is `claude-opus-5-5` for every role; `agents.models` sets a model per role. Any other model id can be given: it is then priced only if you give `agents.prices`. Prices are Anthropic's first-party API rates as of 2026-11-03 and may have changed; a price in `agents.prices` always wins.

## Effort

Set with `agents.effort`.

| Option | What it does |
|---|---|
| `low` | The least reasoning and the fewest tokens. For simple, high-volume calls. |
| `medium` | The default for every role but the writer: a cost-saving step where quality holds. |
| `high` | The default for the writer, whose designs are where judgment matters most. |
| `xhigh` | Between high and max. Not accepted by the 4.6 models. |
| `max` | The most reasoning, for when correctness matters more than cost. |
| `model_default` | Send no effort: the model uses its own default. |

`agents.effort` is for every role and `agents.efforts` sets one per role, e.g. {writer: xhigh, analyst: low}. Reasoning is billed as output tokens, so higher effort costs more; the estimate does not count it, and a run's measured cost does.

## Evolution strategies

Set with `strategy.mechanism`.

| Option | What it does |
|---|---|
| `lineage` | Species kept alive side by side. A new lineage gets a protected trial, the best few are active, none takes more than its quota of the local slots, and one that stops gaining retires to the bench. |
| `archive` | The best of each kind of design on a grid (by family and size). Parents are drawn across the grid, the less visited cells favoured in proportion to `schedule.novelty`. |
| `tournament` | Draw a few of the most recent designs and build on the best of them. Older designs leave the population however good they were, so one lucky score cannot dominate for long. |
| `pareto` | Build on the designs that are best on the score and a second figure at once (`strategy.second_metric`: size, speed, or a metric the runs report). Parents come from that trade-off front, the designs standing alone on it favoured; a crossover pairs designs from different parts of it. |
| `greedy` | Always build on the current best (or one tied with it within the noise). The right choice when the budget is too small for a population. |

Set `strategy.islands` above 1 to run that many separate populations of the chosen strategy. Each sees its own results only; every `strategy.migrate_every` scored runs the best design of another island is brought in as a parent. With `strategy.reset_every` above 0, every so many scored runs the weaker half of the islands start again from the best design of an island that was kept (as in FunSearch); what they held stays in the record.

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

## Who runs the search

Set with `harness.conductor`.

| Option | What it does |
|---|---|
| `code` | The deterministic option. The schedule and the strategy run the search exactly as set; nothing changes course unless you change it. |
| `agent` | An agent runs the search and you talk to it (`evoloop chat`). It answers from the records, changes course from a bounded menu when you ask or when the results call for it, and reports what it did. Code still enforces the budget, the limits and the share of new designs, and records every action. |

## Who picks each slot

Set with `harness.coordinator`.

| Option | What it does |
|---|---|
| `code` | The schedule picks the kind of slot and the strategy picks the parents. |
| `agent` | An agent picks each slot from options code prepares; what the schedule alone would have picked is recorded beside every choice. |

## The strategist

Set with `strategist.mode`.

| Option | What it does |
|---|---|
| `off` | No strategist. The schedule runs as set unless you change it. |
| `advise` | The strategist meets and decides, and every decision waits for your yes or no. |
| `act` | Small decisions are applied at once and recorded; large ones wait for your yes or no. |

## What the strategist may do

Set with `strategist.ask_first`.

| Option | What it does |
|---|---|
| `stay` | Change nothing. Often the right decision. |
| `shares` | The shares of new designs, crossover and local moves for the phase in force. New designs never below `strategist.min_new_share`; a share more than `strategist.max_share_shift` from where you left it waits. |
| `novelty` | The novelty dial, and the novel share of new designs. |
| `local_mix` | The shares of the local moves: edit, settings, ablation. |
| `crossover_kinds` | Which kinds of crossover are used; at least one. |
| `force` | The next few slots (at most `strategist.force_max` on order in all) go to one mode, and if named to one kind of crossover or local move. |
| `retire` | Take a lineage out of the active set. Never the one that holds the best design. |
| `revive` | Give a retired or benched lineage a second chance: active again until it has gone as long without a gain. |
| `direction` | A standing note to the writers, such as where new designs should look. At most three stand at once. |
| `strategy` | Change the evolution strategy. Waits for you by default (`strategist.ask_first`). |
| `question` | Ask you something. The run does not wait for the answer. |

Every decision is a ledger entry with the gain it expects, scored `strategist.horizon` designs later.

## Spend policies

Set with `budget.spend_policy`.

| Option | What it does |
|---|---|
| `pace` | When the agents' cost per design puts the run on course to pass `budget.model_dollars`, the run is made cheaper one step at a time: one proposal fewer per slot; slots chosen by code; the analyst half as often; the strategist half as often; reviews at the end only; settings moves drawn by code. |
| `none` | Nothing is adjusted. The cap still stops agent calls when it is reached. |

The last `budget.reserve_share` of the cap is kept for writing designs: the analyst, the strategist, the reviews and the coordinator agent stop when it is reached.

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
