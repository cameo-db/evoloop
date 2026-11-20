# Steering a run

Nothing needs a restart. A steering command leaves a request in the run's folder; the controller reads
it on its next turn, checks it, and records it in the ledger as applied or refused, with your name, the
old value and the new one. The same commands work on a run that is going and on one that has stopped.

## Changing settings

```
evoloop set mysearch --name r1 schedule.novelty=0.6 budget.evaluations=300 --by "Your Name" --reason "plateau"
```

A change applies to the next design. Jobs already started are untouched.

What can change:

| Can change | Examples |
|---|---|
| the schedule | `schedule.phases`, `schedule.novelty`, `schedule.adaptive`, `schedule.local_mix` |
| the strategy | `strategy.mechanism`, `strategy.islands` |
| the population | `population.lineages`, `population.trial_runs`, `population.quota` |
| crossover and variation | `crossover.kinds`, `variation.proposals_per_slot` |
| the search space | `space.preset`, `space.roles`, `space.forbidden_terms` |
| the harness and the audit | `harness.level`, `harness.coordinator`, `audit.reviews` |
| the budget | `budget.evaluations`, `budget.model_dollars`, `budget.wall_clock_hours` |
| compute | `compute.max_running`, `compute.time_limit`, `compute.qos`, `compute.gpus` |
| the model behind a role | `agents.models`, `agents.default_model` |
| the run type | `run.type` |

[Fields of the brief](fields.md) says for every field whether it can change.

**What cannot change** is what defines the problem: the objective, the direction of the score, the
dataset's identity, the frozen code. Such a request is refused with the reason, and the run goes on.

**A change that moves other settings.** Changing `budget.evaluations` across a boundary of the
guidance, or changing `run.type`, moves the settings that follow from it. The ledger entry lists every
setting that moved with it.

## Changing the length of a run

`evaluation.allowance` (and `evaluation.seed`, `data.fraction`) change what a score means: a model
trained for 50 epochs is not comparable with one trained for 30. So a new **period** begins:

- The best design of each of the `evaluation.leaders_refit` leading lineages is fitted under the new
  setting. These are the references for the new period.
- Earlier scores stay in the record and still feed the agents' lessons. They no longer decide
  selection.

Whether a reference is fitted again or continued from its checkpoint is set by
`evaluation.on_length_change`:

| Value | What happens |
|---|---|
| `auto` | continued when `evaluation.schedule_depends_on_length` is false and `evaluation.keep_checkpoints` is true; otherwise fitted again |
| `continue` | continued from the checkpoint (the adapter gets `EVO_CONTINUE_FROM`) |
| `rerun` | fitted again from scratch |
| `compare_anyway` | no new period: old and new scores are compared as they are |

Continuing is only right when the learning-rate schedule does not depend on the length of the run. A
cosine schedule over 30 epochs has decayed to nearly nothing by the end; 20 more epochs at that rate
teach little, and the continued model looks worse than a fresh 50-epoch fit of the same design.

## Notes to the agents

```
evoloop note mysearch --name r1 "No attention layers." --roles writer --by "Your Name"
evoloop withdraw mysearch --name r1 --id S4 --by "Your Name"
```

A note is advice. Every agent it is addressed to reads it on every call from then on, and each call
records which notes it was shown and which it says it followed. A withdrawn note is no longer shown;
its record stays.

A note is not a rule: an agent can set it aside. What must hold has to be a setting that code enforces,
such as `space.forbidden_terms` or `space.roles`.

## In your own words

```
evoloop steer mysearch --name r1 "more novelty from here, and keep the models small" --by "Your Name"
```

An agent turns your words into setting changes and notes, and the command prints them: each change
with the sentence of yours it came from, and anything it could not express under "not covered".
Nothing is changed. Running the same command again with `--yes` applies exactly what was printed.

## Stopping

```
evoloop stop mysearch --name r1 --by "Your Name"            # start nothing more; end when the jobs do
evoloop stop mysearch --name r1 --run R12 --by "Your Name"   # stop one run
```

A stopped run is continued with `evoloop run mysearch --name r1`. To give an ended run more budget,
`evoloop set ... budget.evaluations=N` and continue it.

## A steered run

A run that was steered is not a clean test of one fixed strategy. The report lists every entry of the
ledger with the number of evaluations at which it took effect, and the study file says how many
steering entries the run had.
