# Brief fields

Every field of `brief.yaml`: its default, the values it accepts, and whether it can change while a search is running. This page is written from the code (`evoloop menu fields --markdown`).

A field you leave empty takes its value from the first of these that has one: a change made during the search, the brief, the skill, the level of autonomy, the run type, the guidance for the size of the budget, the default. `evoloop plan` shows which, for every field.

Fields marked **asked** have no default and are asked during set-up. In the third column, *yes* means the field can be changed during a search; *yes, and a new period begins* that changing it also starts a new comparison period ([why](comparable.md#periods)), and *no* that it is fixed once a search starts.

Jump to: [objective](#objective) · [run](#run) · [space](#space) · [strategy](#strategy) · [schedule](#schedule) · [population](#population) · [crossover](#crossover) · [variation](#variation) · [harness](#harness) · [strategist](#strategist) · [evaluation](#evaluation) · [budget](#budget) · [baseline](#baseline) · [compute](#compute) · [run_command](#run_command) · [audit](#audit) · [agents](#agents) · [data](#data) · [depositor](#depositor) · [license](#license) · [report](#report) · [limits](#limits)

## objective

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="objective-goal"></a>`objective.goal` **asked** | `null` | no | What is being improved and why. Every agent reads it on every call. |
| <a id="objective-metric"></a>`objective.metric` | `"score"` | no | The name of the metric your evaluator reports as its score, such as pearson_r or val_loss. Recorded in the study file as the metric that was optimized. |
| <a id="objective-direction"></a>`objective.direction` **asked** | `null` | no | maximize or minimize. Accepts: `maximize`, `minimize`. |
| <a id="objective-constraints"></a>`objective.constraints` | `[]` | no | Limits on a solution, as text. Shown to the writers; not enforced by code. |
| <a id="objective-success_threshold"></a>`objective.success_threshold` | `null` | no | A score at which the search stops designing and ends. |

## run

Explained in [which search](which-search.md).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="run-type"></a>`run.type` **asked** | `null` | yes | The named bundle of settings to start from. See the run types. |
| <a id="run-description"></a>`run.description` | `""` | yes | Your own description of the search. Kept as the first note the agents read. |
| <a id="run-skill"></a>`run.skill` | `null` | yes | What kind of optimization this is: a built-in skill (see the skills) or the path of a skill folder of your own. It sets what suits the task and gives the agents guidance for it; independent of the run type. |

## space

Explained in [setting up](setting-up.md#1-mark-the-editable-code).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="space-preset"></a>`space.preset` | `"open_architecture"` | yes | Which marked blocks are open. See the search spaces. Accepts: `settings_only`, `module`, `template`, `open_architecture`, `architecture_and_recipe`, `custom`. |
| <a id="space-modules"></a>`space.modules` | `[]` | yes | With preset `module`: the roles or block names that are open. |
| <a id="space-roles"></a>`space.roles` | `{}` | yes | Per role (or block name): open, settings or fixed. Overrides the preset for that role. |
| <a id="space-settings"></a>`space.settings` | `"open"` | yes | The params blocks: open, fixed, or a list of block names that may move. |
| <a id="space-recipe_roles"></a>`space.recipe_roles` | `["loss", "optimizer", "schedule", "augmentation", "training", "recipe"]` | yes | The roles that make up the training recipe; other structure blocks make up the model. |
| <a id="space-forbidden"></a>`space.forbidden` | `[]` | yes | What must not be done, as text. Shown to the writers; not checked by code. |
| <a id="space-must_keep"></a>`space.must_keep` | `[]` | yes | What must be kept, as text. Shown to the writers; not checked by code. |
| <a id="space-forbidden_terms"></a>`space.forbidden_terms` | `[]` | yes | Strings a block may not contain. Enforced by code: a design that has one is not run. |
| <a id="space-ranges"></a>`space.ranges` | `{}` | yes | Bounds for the settings estimator (`variation.settings_by: tpe`): {"block.key": [low, high]}. Without one a setting may move a hundredfold either way. |

## strategy

Explained in [parents](parents.md).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="strategy-mechanism"></a>`strategy.mechanism` | `"lineage"` | yes | How parents are chosen and what stays in the population. See the strategies. Accepts: `lineage`, `archive`, `tournament`, `pareto`, `greedy`. |
| <a id="strategy-islands"></a>`strategy.islands` | `1` | yes | Separate populations of the strategy; 1 for none. |
| <a id="strategy-migrate_every"></a>`strategy.migrate_every` | `12` | yes | With islands: scored runs of an island between migrations into it. |
| <a id="strategy-tournament_size"></a>`strategy.tournament_size` | `3` | yes | With `tournament`: how many are drawn for each parent. |
| <a id="strategy-window"></a>`strategy.window` | `24` | yes | With `tournament`: how many of the most recent designs make up the population. |
| <a id="strategy-descriptors"></a>`strategy.descriptors` | `["family", "size"]` | yes | With `archive`: what makes a cell: `family`, `size`, `behaviour` (designs whose errors fall alike, from the `signature` the runs report), or the name of a metric the runs report. |
| <a id="strategy-reset_every"></a>`strategy.reset_every` | `0` | yes | With islands: scored runs of the whole search between resets of the weaker half of the islands; 0 for never. |
| <a id="strategy-second_metric"></a>`strategy.second_metric` | `null` | yes | With `pareto`: the second figure to do well on: `parameters`, `examples_per_s`, `training_minutes`, or a metric the runs report. |
| <a id="strategy-second_direction"></a>`strategy.second_direction` | `"minimize"` | yes | With `pareto`: whether less (minimize) or more (maximize) of the second figure is better. Accepts: `maximize`, `minimize`. |
| <a id="strategy-behaviour_similarity"></a>`strategy.behaviour_similarity` | `0.9` | yes | How alike (correlation, 0 to 1) the errors of two designs must fall for them to count as the same behaviour. |

## schedule

Explained in [schedule](schedule.md).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="schedule-phases"></a>`schedule.phases` | `[{"until": 0.6, "new": 0.65, "cross": 0.1, "local": 0.25}, {"until": 1.0, "new": 0.15, "cross": 0.25, "local": 0.6}]` | yes | The shares of new designs, crossover and local moves, by phase: each phase holds until that share of the budget is spent. |
| <a id="schedule-novel_share"></a>`schedule.novel_share` | `0.33` | yes | The part of the `new` share that goes to `novel` slots. |
| <a id="schedule-novelty"></a>`schedule.novelty` | `0.3` | yes | 0 to 1. How much a design far from everything tried is favoured: in the choice among several proposals, and in the archive's draw of a parent. |
| <a id="schedule-novelty_measure"></a>`schedule.novelty_measure` | `"auto"` | yes | What a novel slot counts as different: `code` (rarely built on), `behaviour` (errors fall unlike the leader's), or `auto` (behaviour where the runs report a signature). Accepts: `auto`, `code`, `behaviour`. |
| <a id="schedule-adaptive"></a>`schedule.adaptive` | `0.0` | yes | 0 to 1. 0 follows the phases exactly; above 0 blends in what each mode has returned. |
| <a id="schedule-floor"></a>`schedule.floor` | `0.05` | yes | With an adaptive schedule: the least share any mode keeps. |
| <a id="schedule-founder_credit"></a>`schedule.founder_credit` | `0.5` | yes | With an adaptive schedule: the part of each gain credited to the slot that founded the lineage, rather than to the move that made the gain. |
| <a id="schedule-local_mix"></a>`schedule.local_mix` | `{"edit": 0.5, "settings": 0.35, "ablation": 0.15}` | yes | The shares of the local moves: edit, settings, ablation. |

## population

Explained in [parents](parents.md#lineage).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="population-lineages"></a>`population.lineages` | `8` | yes | With `lineage`: how many lineages are active at once. |
| <a id="population-quota"></a>`population.quota` | `0.4` | yes | With `lineage`: the largest share of the local slots one lineage may take. |
| <a id="population-trial_runs"></a>`population.trial_runs` | `2` | yes | With `lineage`: runs a new lineage gets before it is compared with others. |
| <a id="population-retire_after"></a>`population.retire_after` | `6` | yes | With `lineage`: local moves in a row without a gain after which a lineage retires. |
| <a id="population-tie_margin"></a>`population.tie_margin` | `1.0` | yes | Candidates within this many noise floors of a lineage's best count as tied for parent. |
| <a id="population-specialist_rate"></a>`population.specialist_rate` | `0.15` | yes | How often the parent is the candidate best on one of `evaluation.speciality_metrics`. |

## crossover

Explained in [moves](moves.md#crossover).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="crossover-kinds"></a>`crossover.kinds` | `["block_swap", "graft", "hybrid"]` | yes | The kinds of crossover that may be used. Only these are used. |

## variation

Explained in [moves](moves.md).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="variation-proposals_per_slot"></a>`variation.proposals_per_slot` | `2` | yes | How many proposals the writer returns for a slot; one is chosen and trained. |
| <a id="variation-step_adaptation"></a>`variation.step_adaptation` | `true` | yes | Ask for bolder local edits when a lineage's recent ones gain often, smaller when rarely. |
| <a id="variation-settings_by"></a>`variation.settings_by` | `"agent"` | yes | Who makes a settings move: an `agent`; a `sampler` in code that nudges one value (no call); or `tpe`, a Bayesian estimator in code that draws every setting from what the best designs used (no call). Accepts: `agent`, `sampler`, `tpe`. |
| <a id="variation-edit_format"></a>`variation.edit_format` | `"full"` | yes | How a writer returns a change to part of a block: `full` (the whole block) or `diff` (find-and-replace edits, fewer tokens on large blocks; an edit that does not apply exactly once is refused). Accepts: `full`, `diff`. |
| <a id="variation-approaches"></a>`variation.approaches` | `"off"` | yes | Ways of working handed to the writers, one per slot, kept or dropped by how their designs did: `off`, `fixed` (only yours) or `evolve` (the analyst adds to them). Accepts: `off`, `fixed`, `evolve`. |
| <a id="variation-approach_pool"></a>`variation.approach_pool` | `6` | yes | With `evolve`: the most approaches kept at once; past it the worst proven one is retired. |
| <a id="variation-approach_seeds"></a>`variation.approach_seeds` | `[]` | yes | Your own approaches: a list of short instructions on how to go about designing. Never retired. |

## harness

Explained in [agents](agents.md).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="harness-autonomy"></a>`harness.autonomy` | `null` | yes | How much of the search the agents decide: harnessed, guided or agentic. Sets the fields below it. Accepts: `harnessed`, `guided`, `agentic`. |
| <a id="harness-level"></a>`harness.level` | `"full"` | yes | How much oversight runs beside the writer. See the harness levels. Accepts: `minimal`, `standard`, `full`. |
| <a id="harness-coordinator"></a>`harness.coordinator` | `"code"` | yes | Who picks each slot: code or an agent. Accepts: `code`, `agent`. |
| <a id="harness-analyst_every"></a>`harness.analyst_every` | `8` | yes | Finished runs between two analyses. |
| <a id="harness-conductor"></a>`harness.conductor` | `"code"` | yes | Who runs the search as a whole: code (the schedule, deterministic) or an agent you talk to with `evoloop chat`. Accepts: `code`, `agent`. |

## strategist

Explained in [strategist](strategist.md).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="strategist-mode"></a>`strategist.mode` | `"off"` | yes | Whether an agent reviews the search as a whole and may change its course. See the strategist. Accepts: `off`, `advise`, `act`. |
| <a id="strategist-every"></a>`strategist.every` | `15` | yes | Scored designs between two meetings of the strategist. |
| <a id="strategist-plateau"></a>`strategist.plateau` | `12` | yes | Designs with no rise in the best score after which the strategist meets at once. |
| <a id="strategist-horizon"></a>`strategist.horizon` | `15` | yes | Designs after a decision at which what followed it is scored. |
| <a id="strategist-min_new_share"></a>`strategist.min_new_share` | `0.1` | yes | The least share of new designs the strategist may set: exploration is protected. |
| <a id="strategist-max_share_shift"></a>`strategist.max_share_shift` | `0.15` | yes | How far a share may stand from where you last left it without your yes. |
| <a id="strategist-force_max"></a>`strategist.force_max` | `5` | yes | The most slots the strategist may have on order at once. |
| <a id="strategist-ask_first"></a>`strategist.ask_first` | `["strategy"]` | yes | The actions that always wait for your yes, whatever the mode. |

## evaluation

Explained in [comparable](comparable.md).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="evaluation-allowance"></a>`evaluation.allowance` **asked** | `null` | yes, and a new period begins | The length of one training run, in the project's own unit. Passed to every job. |
| <a id="evaluation-allowance_unit"></a>`evaluation.allowance_unit` | `"steps"` | yes, and a new period begins | The name of that unit (steps, epochs, seconds), for the records. |
| <a id="evaluation-seed"></a>`evaluation.seed` | `0` | yes, and a new period begins | The seed of every design's first fit. |
| <a id="evaluation-noise"></a>`evaluation.noise` **asked** | `null` | no | How much the score differs between two fits of one model. A smaller difference is no difference. |
| <a id="evaluation-screen_fraction"></a>`evaluation.screen_fraction` | `0.5` | yes | The point of a new design's first run at which it is compared with earlier new designs. |
| <a id="evaluation-screen_keep"></a>`evaluation.screen_keep` | `0.5` | yes | The share of new designs that goes on past that point; 1 switches screening off. |
| <a id="evaluation-screen_min_pool"></a>`evaluation.screen_min_pool` | `4` | yes | Earlier designs needed at a point before any is stopped there (the screen and every rung of the ladder). |
| <a id="evaluation-recheck_every"></a>`evaluation.recheck_every` | `0` | yes | Designs between two fits of the leader on a new seed; 0 leaves it to the harness level. |
| <a id="evaluation-speciality_metrics"></a>`evaluation.speciality_metrics` | `{}` | yes | Metrics a run reports, with their direction, by which a specialist parent is chosen. |
| <a id="evaluation-metrics"></a>`evaluation.metrics` | `{}` | yes | The validation metrics to track, each with how it is computed: {name: definition}. The names are those your evaluator reports under diagnostics. Shown to the agents, recorded in the study file, and listed on the leaderboard. The report warns when one is missing from the results. |
| <a id="evaluation-test_metrics"></a>`evaluation.test_metrics` | `{}` | yes | The held-out evaluations to run on every design, in the same form: {name: definition}, or {name: {definition, dataset}} for an evaluation on other data. The names are those your evaluator reports under diagnostics.hidden. Never shown to an agent or used for selection. Recorded in the study file and listed on the leaderboard. |
| <a id="evaluation-ladder"></a>`evaluation.ladder` | `[]` | yes | A promotion ladder: a list of rungs {at: share of a run, keep: share that goes on}. At each rung the weaker designs stop and are charged that share, so the budget covers more designs. Empty for the single screen. |
| <a id="evaluation-ladder_applies"></a>`evaluation.ladder_applies` | `"all"` | yes | With a ladder: `all` designs are subject to it, or only `new` ones (the first run of a new design). Accepts: `new`, `all`. |
| <a id="evaluation-schedule_depends_on_length"></a>`evaluation.schedule_depends_on_length` | `true` | no | Whether the learning-rate schedule depends on the run's length. If not, a longer run can continue a checkpoint. |
| <a id="evaluation-keep_checkpoints"></a>`evaluation.keep_checkpoints` | `false` | no | Whether the adapter keeps checkpoints that a later run can continue. |
| <a id="evaluation-on_length_change"></a>`evaluation.on_length_change` | `"auto"` | yes | When the run length changes: auto, continue, rerun, or compare_anyway. Accepts: `auto`, `continue`, `rerun`, `compare_anyway`. |
| <a id="evaluation-leaders_refit"></a>`evaluation.leaders_refit` | `4` | yes | When a new period begins: how many lineages' leaders are fitted again. |
| <a id="evaluation-test_set"></a>`evaluation.test_set` | `"held_out"` | no | `held_out` when test scores are kept from the search. Recorded in the study file. |
| <a id="evaluation-quick_check"></a>`evaluation.quick_check` | `null` | no | A command that tests a design in seconds. A design that fails it is not trained. |
| <a id="evaluation-inherit_weights"></a>`evaluation.inherit_weights` | `false` | yes, and a new period begins | A child is handed its parent's checkpoint folder (EVO_PARENT_CHECKPOINT_DIR) so the adapter can start from the weights that fit. Changing it begins a new period. |
| <a id="evaluation-variables"></a>`evaluation.variables` | `{}` | yes, and a new period begins | Environment variables passed to every job, e.g. {PATIENCE: 5}: the adapter's own knobs. A change begins a new period. |

## budget

Explained in [cost](cost.md).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="budget-evaluations"></a>`budget.evaluations` **asked** | `null` | yes | How many models may be trained in all. |
| <a id="budget-model_dollars"></a>`budget.model_dollars` **asked** | `null` | yes | The most the agents may cost. No call is made once it is reached. |
| <a id="budget-model_calls"></a>`budget.model_calls` | `null` | yes | The most agent calls, as a second cap. |
| <a id="budget-wall_clock_hours"></a>`budget.wall_clock_hours` | `null` | yes | After this long the search starts nothing more and ends when its jobs do. |
| <a id="budget-max_uncounted_failures"></a>`budget.max_uncounted_failures` | `10` | yes | Failed or invalid designs that are not charged; beyond it each is charged. |
| <a id="budget-max_uncounted_rejections"></a>`budget.max_uncounted_rejections` | `50` | yes | Designs rejected for a limit that are not charged; beyond it each is charged. |
| <a id="budget-spend_policy"></a>`budget.spend_policy` | `"pace"` | yes | pace (make the run cheaper when it is heading past the spend cap) or none. Accepts: `none`, `pace`. |
| <a id="budget-reserve_share"></a>`budget.reserve_share` | `0.15` | yes | The last part of the spend cap, kept for writing designs. |

## baseline

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="baseline-mode"></a>`baseline.mode` **asked** | `null` | no | train (fitted inside the search), import (a finished fit) or skip. Accepts: `train`, `import`, `skip`. |
| <a id="baseline-import_from"></a>`baseline.import_from` | `null` | no | With import: the folder holding the fit's result.json. |

## compute

Explained in [servers](servers.md).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="compute-gpus"></a>`compute.gpus` **asked** | `null` | yes | How many training jobs run at once. |
| <a id="compute-scheduler"></a>`compute.scheduler` | `"local"` | no | local (processes on this machine, each given its own GPU) or slurm. Accepts: `local`, `slurm`. |
| <a id="compute-allocation"></a>`compute.allocation` | `"per_design"` | no | On Slurm: per_design (each design its own job, submitted as GPUs come free) or block (one job holds every GPU and the designs run inside it; started with `evoloop controller`). Accepts: `per_design`, `block`. |
| <a id="compute-partition"></a>`compute.partition` | `null` | yes | Slurm partition. |
| <a id="compute-qos"></a>`compute.qos` | `null` | yes | Slurm QoS: one name, or a list in order of preference, [{name: a, max_jobs: 8}, {name: b}]. |
| <a id="compute-gpu_type"></a>`compute.gpu_type` | `null` | yes | Slurm gres type, e.g. a100; empty for any free GPU. |
| <a id="compute-larger_gpu_type"></a>`compute.larger_gpu_type` | `null` | yes | Slurm gres type for designs too large for the GPU they got: the adapter exits 76 (it is told EVO_LARGER_GPU) and the run is submitted again on this type, uncharged. Empty for none. |
| <a id="compute-gpus_per_job"></a>`compute.gpus_per_job` | `1` | yes | GPUs each job asks for; 0 for a CPU job. |
| <a id="compute-cpus_per_job"></a>`compute.cpus_per_job` | `4` | no | Processors each job asks for. |
| <a id="compute-mem_gb"></a>`compute.mem_gb` | `32` | no | Memory each job asks for. |
| <a id="compute-time_limit"></a>`compute.time_limit` | `"2-00:00:00"` | yes | Slurm time limit, per start of a job. A run that reaches it is submitted again and continues from its checkpoint, so a short limit, which starts sooner, is enough when the evaluator resumes. |
| <a id="compute-setup"></a>`compute.setup` | `[]` | no | Shell lines run first in each job, e.g. activating an environment. |
| <a id="compute-extra_sbatch"></a>`compute.extra_sbatch` | `[]` | no | Further sbatch options. |
| <a id="compute-infrastructure_retries"></a>`compute.infrastructure_retries` | `3` | no | How often in a row a run ended by the machine (time limit, preemption, failed node) is started again without having got further. A start that got further than the last is always followed by another. |
| <a id="compute-max_running"></a>`compute.max_running` | `null` | yes | A cap on jobs at once, below `compute.gpus`, that can be moved during a run. |
| <a id="compute-max_waiting"></a>`compute.max_waiting` | `1` | yes | On Slurm: no new design is written while this many jobs await their first start on the usual GPU type. |

## run_command

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="run_command"></a>`run_command` | `"python adapter/run.py"` | no | The command that trains one design, started in its working copy. |

## audit

Explained in [auditing](auditing.md).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="audit-reviews"></a>`audit.reviews` | `"halfway"` | yes | When the assessor reviews the agents. See the review schedules, or give a list of shares. |
| <a id="audit-review_roles"></a>`audit.review_roles` | `"all"` | yes | `all`, or the list of roles to review. |

## agents

Explained in [models](models.md).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="agents-backend"></a>`agents.backend` **asked** | `null` | no | stub (no cost), anthropic_api, or claude_code. Accepts: `stub`, `anthropic_api`, `claude_code`. |
| <a id="agents-stub_module"></a>`agents.stub_module` | `null` | no | With stub: a Python file with respond(role, context); empty for the built-in stub. |
| <a id="agents-default_model"></a>`agents.default_model` | `"claude-opus-5-5"` | yes | The model every role uses unless `agents.models` names another. See the models. |
| <a id="agents-models"></a>`agents.models` | `{}` | yes | A model per role: {writer: ..., analyst: ...}. |
| <a id="agents-effort"></a>`agents.effort` | `"medium"` | yes | How hard the model reasons, for every role: low, medium, high, xhigh, max, or model_default. Accepts: `low`, `medium`, `high`, `xhigh`, `max`, `model_default`. |
| <a id="agents-writer_mix"></a>`agents.writer_mix` | `[]` | yes | Several models for the writers, by share of the calls: [{model: a, share: 0.8}, {model: b, share: 0.2}], each with an effort if wanted. The report compares their designs. |
| <a id="agents-efforts"></a>`agents.efforts` | `{"writer": "high"}` | yes | An effort per role, over `agents.effort`: {writer: high, analyst: low}. |
| <a id="agents-fallbacks"></a>`agents.fallbacks` | `"default"` | yes | default: where the model supports it, a request it declines is answered by another model in the same call. off: it is lost. Accepts: `default`, `off`. |
| <a id="agents-max_tokens"></a>`agents.max_tokens` | `64000` | no | The longest reply (anthropic_api only). |
| <a id="agents-call_timeout_seconds"></a>`agents.call_timeout_seconds` | `900` | no | How long one call may take. |
| <a id="agents-max_concurrent_calls"></a>`agents.max_concurrent_calls` | `4` | no | How many calls run side by side. |
| <a id="agents-max_retries"></a>`agents.max_retries` | `2` | no | Retries of a call that failed for a passing reason; a refusal for the account's limit is never retried. |
| <a id="agents-prices"></a>`agents.prices` | `{}` | yes | Dollars per million tokens, {model: {input: x, output: y}}, over the built-in list. Needed for a model the list does not have: without a price the spend cap cannot count its calls. |

## data

Explained in [study](study.md).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="data-name"></a>`data.name` | `null` | no | The dataset's name. |
| <a id="data-accession"></a>`data.accession` | `null` | no | The dataset's DOI, accession or link. The study file earns no star without it. |
| <a id="data-input"></a>`data.input` | `null` | no | What an input is. |
| <a id="data-output"></a>`data.output` | `null` | no | What an output is. |
| <a id="data-examples"></a>`data.examples` | `null` | no | Counts: {train: n, valid: n, test: n}. |
| <a id="data-preprocessing"></a>`data.preprocessing` | `null` | no | How the data was prepared. |
| <a id="data-splits"></a>`data.splits` | `null` | no | How the split was made, with its code or files. |
| <a id="data-fraction"></a>`data.fraction` | `1.0` | yes, and a new period begins | The share of the training data a run uses. Passed to jobs as EVO_DATA_FRACTION. |

## depositor

Explained in [study](study.md).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="depositor-name"></a>`depositor.name` | `null` | no | Who deposits the study. |
| <a id="depositor-orcid"></a>`depositor.orcid` | `null` | no | Their ORCID. |
| <a id="depositor-lab"></a>`depositor.lab` | `null` | no | Their lab. |
| <a id="depositor-institution"></a>`depositor.institution` | `null` | no | Their institution. |

## license

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="license"></a>`license` | `"MIT"` | no | The licence of the study file. |

## report

Explained in [steering](steering.md#monitoring).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="report-columns"></a>`report.columns` | `[]` | yes | Further leaderboard columns: valid.<metric>, test.<metric>, speed, best_epoch, epochs_run. |
| <a id="report-top"></a>`report.top` | `15` | yes | How many designs the leaderboard shows; the baseline and reference rows are always shown. |

## limits

Explained in [early stopping](early-stopping.md#limits).

| Field | Default | Changes in a search | What it is |
|---|---|---|---|
| <a id="limits"></a>`limits` | `{}` | yes | Hard limits on a design, enforced by code: {metric: {max: x}} or {min: x}, on any figure a result reports, `parameters` or `examples_per_s`. |
