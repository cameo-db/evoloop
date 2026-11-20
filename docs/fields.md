# Fields of the brief

Every field of `brief.yaml`, its default, and whether it can change while a run is going. This page is written from the code (`evoloop menu fields --markdown`).

A value comes from the first of: a change made during the run, the brief, the run type, the guidance for the size of the budget, the default. `evoloop plan` shows which, for every field.

Fields marked **asked** are asked whenever they are empty; the others are never asked unless you run `evoloop brief --all`.


## objective

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `objective.goal` **asked** | `null` | no | What is being improved and why. Every agent reads it on every call. |
| `objective.metric` | `"score"` | no | The name of the score, for the records. |
| `objective.direction` **asked** | `null` | no | maximize or minimize. |
| `objective.constraints` | `[]` | no | Limits on a solution, as text. Shown to the writers; not enforced by code. |
| `objective.success_threshold` | `null` | no | A score at which the search stops designing and ends. |

## run

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `run.type` **asked** | `null` | yes | The named bundle of settings to start from. See the run types. |
| `run.description` | `""` | yes | Your own description of the search. Kept as the first note the agents read. |

## space

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `space.preset` | `"open_architecture"` | yes | Which marked blocks are open. See the search spaces. |
| `space.modules` | `[]` | yes | With preset `module`: the roles or block names that are open. |
| `space.roles` | `{}` | yes | Per role (or block name): open, settings or fixed. Overrides the preset for that role. |
| `space.settings` | `"open"` | yes | The params blocks: open, fixed, or a list of block names that may move. |
| `space.recipe_roles` | `["loss", "optimizer", "schedule", "augmentation", "training", "recipe"]` | yes | The roles that make up the training recipe; other structure blocks make up the model. |
| `space.forbidden` | `[]` | yes | What must not be done, as text. Shown to the writers; not checked by code. |
| `space.must_keep` | `[]` | yes | What must be kept, as text. Shown to the writers; not checked by code. |
| `space.forbidden_terms` | `[]` | yes | Strings a block may not contain. Enforced by code: a design that has one is not run. |

## strategy

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `strategy.mechanism` | `"lineage"` | yes | How parents are chosen and what stays in the population. See the strategies. |
| `strategy.islands` | `1` | yes | Separate populations of the strategy; 1 for none. |
| `strategy.migrate_every` | `12` | yes | With islands: scored runs of an island between migrations into it. |
| `strategy.tournament_size` | `3` | yes | With `tournament`: how many are drawn for each parent. |
| `strategy.window` | `24` | yes | With `tournament`: how many of the most recent designs make up the population. |
| `strategy.descriptors` | `["family", "size"]` | yes | With `archive`: what makes a cell: `family`, `size`, or the name of a metric the runs report. |

## schedule

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `schedule.phases` | `[{"until": 0.6, "new": 0.65, "cross": 0.1, "local": 0.25}, {"until": 1.0, "new": 0.15, "cross": 0.25, "local": 0.6}]` | yes | The shares of new designs, crossover and local moves, by phase: each phase holds until that share of the budget is spent. |
| `schedule.novel_share` | `0.33` | yes | The part of the `new` share that goes to `novel` slots. |
| `schedule.novelty` | `0.3` | yes | 0 to 1. How much a design far from everything tried is favoured: in the choice among several proposals, and in the archive's draw of a parent. |
| `schedule.adaptive` | `0.0` | yes | 0 to 1. 0 follows the phases exactly; above 0 blends in what each mode has returned. |
| `schedule.floor` | `0.05` | yes | With an adaptive schedule: the least share any mode keeps. |
| `schedule.founder_credit` | `0.5` | yes | With an adaptive schedule: the part of each gain credited to the slot that founded the lineage, rather than to the move that made the gain. |
| `schedule.local_mix` | `{"edit": 0.5, "settings": 0.35, "ablation": 0.15}` | yes | The shares of the local moves: edit, settings, ablation. |

## population

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `population.lineages` | `8` | yes | With `lineage`: how many lineages are active at once. |
| `population.quota` | `0.4` | yes | With `lineage`: the largest share of the local slots one lineage may take. |
| `population.trial_runs` | `2` | yes | With `lineage`: runs a new lineage gets before it is compared with others. |
| `population.retire_after` | `6` | yes | With `lineage`: local moves in a row without a gain after which a lineage retires. |
| `population.tie_margin` | `1.0` | yes | Candidates within this many noise floors of a lineage's best count as tied for parent. |
| `population.specialist_rate` | `0.15` | yes | How often the parent is the candidate best on one of `evaluation.speciality_metrics`. |

## crossover

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `crossover.kinds` | `["block_swap", "graft", "hybrid"]` | yes | The kinds of crossover that may be used. Only these are used. |

## variation

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `variation.proposals_per_slot` | `2` | yes | How many proposals the writer returns for a slot; one is chosen and trained. |
| `variation.step_adaptation` | `true` | yes | Ask for bolder local edits when a lineage's recent ones gain often, smaller when rarely. |
| `variation.settings_by` | `"agent"` | yes | Who makes a settings move: an agent, or a sampler in code (no call). |

## harness

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `harness.level` | `"full"` | yes | How much oversight runs beside the writer. See the harness levels. |
| `harness.coordinator` | `"code"` | yes | Who picks each slot: code or an agent. |
| `harness.analyst_every` | `8` | yes | Finished runs between two analyses. |

## evaluation

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `evaluation.allowance` **asked** | `null` | yes, and a new period begins | The length of one training run, in the project's own unit. Passed to every job. |
| `evaluation.allowance_unit` | `"steps"` | yes, and a new period begins | The name of that unit (steps, epochs, seconds), for the records. |
| `evaluation.seed` | `0` | yes, and a new period begins | The seed of every design's first fit. |
| `evaluation.noise` **asked** | `null` | no | How much the score differs between two fits of one model. A smaller difference is no difference. |
| `evaluation.screen_fraction` | `0.5` | yes | The point of a new design's first run at which it is compared with earlier new designs. |
| `evaluation.screen_keep` | `0.5` | yes | The share of new designs that goes on past that point; 1 switches screening off. |
| `evaluation.screen_min_pool` | `4` | yes | Earlier new designs needed before any is stopped at the screen. |
| `evaluation.recheck_every` | `0` | yes | Designs between two fits of the leader on a new seed; 0 leaves it to the harness level. |
| `evaluation.speciality_metrics` | `{}` | yes | Metrics a run reports, with their direction, by which a specialist parent is chosen. |
| `evaluation.schedule_depends_on_length` | `true` | no | Whether the learning-rate schedule depends on the run's length. If not, a longer run can continue a checkpoint. |
| `evaluation.keep_checkpoints` | `false` | no | Whether the adapter keeps checkpoints that a later run can continue. |
| `evaluation.on_length_change` | `"auto"` | yes | When the run length changes: auto, continue, rerun, or compare_anyway. |
| `evaluation.leaders_refit` | `4` | yes | When a new period begins: how many lineages' leaders are fitted again. |
| `evaluation.test_set` | `"held_out"` | no | `held_out` when test scores are kept from the search. Recorded in the study file. |
| `evaluation.quick_check` | `null` | no | A command that tests a design in seconds. A design that fails it is not trained. |

## budget

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `budget.evaluations` **asked** | `null` | yes | How many models may be trained in all. |
| `budget.model_dollars` **asked** | `null` | yes | The most the agents may cost. No call is made once it is reached. |
| `budget.model_calls` | `null` | yes | The most agent calls, as a second cap. |
| `budget.wall_clock_hours` | `null` | yes | After this long the search starts nothing more and ends when its jobs do. |
| `budget.max_uncounted_failures` | `10` | yes | Failed or invalid designs that are not charged; beyond it each is charged. |

## baseline

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `baseline.mode` **asked** | `null` | no | train (fitted inside the search), import (a finished fit) or skip. |
| `baseline.import_from` | `null` | no | With import: the folder holding the fit's result.json. |

## compute

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `compute.gpus` **asked** | `null` | yes | How many training jobs run at once. |
| `compute.scheduler` | `"local"` | no | local (processes on this machine) or slurm (each run its own job). |
| `compute.partition` | `null` | yes | Slurm partition. |
| `compute.qos` | `null` | yes | Slurm QoS: one name, or a list in order of preference, [{name: a, max_jobs: 8}, {name: b}]. |
| `compute.gpu_type` | `null` | no | Slurm gres type, e.g. a100; empty for any. |
| `compute.gpus_per_job` | `1` | yes | GPUs each job asks for; 0 for a CPU job. |
| `compute.cpus_per_job` | `4` | no | Processors each job asks for. |
| `compute.mem_gb` | `32` | no | Memory each job asks for. |
| `compute.time_limit` | `"2-00:00:00"` | yes | Slurm time limit, per start of a job. |
| `compute.setup` | `[]` | no | Shell lines run first in each job, e.g. activating an environment. |
| `compute.extra_sbatch` | `[]` | no | Further sbatch options. |
| `compute.infrastructure_retries` | `3` | no | How often a run ended by the machine is started again, uncharged. |
| `compute.max_running` | `null` | yes | A cap on jobs at once, below `compute.gpus`, that can be moved during a run. |
| `compute.max_waiting` | `1` | yes | On Slurm: no new design is written while this many jobs await their first start. |

## run_command

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `run_command` | `"python adapter/run.py"` | no | The command that trains one design, started in its working copy. |

## audit

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `audit.reviews` | `"halfway"` | yes | When the assessor reviews the agents. See the review schedules, or give a list of shares. |
| `audit.review_roles` | `"all"` | yes | `all`, or the list of roles to review. |

## agents

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `agents.backend` **asked** | `null` | no | stub (no cost), anthropic_api, or claude_code. |
| `agents.stub_module` | `null` | no | With stub: a Python file with respond(role, context); empty for the built-in stub. |
| `agents.default_model` | `null` | yes | The model every role uses unless `agents.models` names another. |
| `agents.models` | `{}` | yes | A model per role: {writer: ..., analyst: ...}. |
| `agents.max_tokens` | `16000` | no | The longest reply (anthropic_api only). |
| `agents.call_timeout_seconds` | `900` | no | How long one call may take. |
| `agents.max_concurrent_calls` | `4` | no | How many calls run side by side. |
| `agents.max_retries` | `2` | no | Retries of a call that failed for a passing reason; a refusal for the account's limit is never retried. |
| `agents.prices` | `{}` | no | Dollars per million tokens, {model: {input: x, output: y}} (anthropic_api only). Without it the spend cap cannot count the calls. |

## data

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `data.name` | `null` | no | The dataset's name. |
| `data.accession` | `null` | no | The dataset's DOI, accession or link. The study file earns no star without it. |
| `data.input` | `null` | no | What an input is. |
| `data.output` | `null` | no | What an output is. |
| `data.examples` | `null` | no | Counts: {train: n, valid: n, test: n}. |
| `data.preprocessing` | `null` | no | How the data was prepared. |
| `data.splits` | `null` | no | How the split was made, with its code or files. |
| `data.fraction` | `1.0` | yes, and a new period begins | The share of the training data a run uses. Passed to jobs as EVO_DATA_FRACTION. |

## depositor

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `depositor.name` | `null` | no | Who deposits the study. |
| `depositor.orcid` | `null` | no | Their ORCID. |
| `depositor.lab` | `null` | no | Their lab. |
| `depositor.institution` | `null` | no | Their institution. |

## license

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `license` | `"MIT"` | no | The licence of the study file. |

## report

| Field | Default | Changes in a run | What it is |
|---|---|---|---|
| `report.columns` | `[]` | yes | Further leaderboard columns: valid.<metric> or test.<metric>. |
