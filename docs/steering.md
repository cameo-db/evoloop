# Monitor and steer a search

A search does not need a restart to change. Every command below leaves a request in the run's folder;
the search reads it within a few seconds, checks it, and records it as applied or refused, with your
name. The same commands work on a search that has stopped.

## I want to…

| I want to | Command |
|---|---|
| see where it stands | `evoloop status mysearch --name r1` |
| see the best designs so far | `evoloop leaderboard mysearch --name r1` |
| look at one design | `evoloop show mysearch C12 --name r1` |
| read everything | `evoloop report mysearch --name r1` |
| give it more budget | `evoloop set mysearch --name r1 budget.evaluations=300 --by "Me"` |
| explore more, or less | `evoloop set mysearch --name r1 schedule.novelty=0.6 --by "Me"` |
| train longer | `evoloop set mysearch --name r1 evaluation.allowance=50 --by "Me"` ([starts a new period](#changing-the-length-of-a-run)) |
| tell the agents something | `evoloop note mysearch --name r1 "No attention layers." --by "Me"` |
| say it in my own words | `evoloop steer mysearch --name r1 "more novelty, keep models small" --by "Me"` |
| order the next few moves | `evoloop force mysearch --name r1 --mode cross --count 3 --by "Me"` |
| cap model size | `evoloop set mysearch --name r1 'limits={"parameters": {"max": 20000000}}' --by "Me"` |
| bring in designs from an earlier search | `evoloop import mysearch --name r2 --from-run mysearch/runs/r1 --top 5 --by "Me"` |
| add a published model to the leaderboard | `evoloop reference mysearch --name r1 --label "paper" --score 0.49 --by "Me"` |
| answer something the strategist proposed | `evoloop approve mysearch --name r1 --id S14 --by "Me"` ([Working with the strategist](strategist.md)) |
| talk to the agent running it | `evoloop chat mysearch --name r1 --by "Me"` |
| stop one design | `evoloop stop mysearch --name r1 --run R12 --by "Me"` |
| stop the search | `evoloop stop mysearch --name r1 --by "Me"` ([stop and resume](#stop-and-resume-a-search)) |
| resume a stopped search | `evoloop run mysearch --name r1` |

The sections below explain each.

## Watching

```
evoloop status mysearch --name r1          # a few lines: budget, best, what is held up, what waits for you
evoloop leaderboard mysearch --name r1     # the best designs, the baseline, the reference rows
evoloop show mysearch C12 --name r1        # one design: where it came from, what it changed, how it ended
evoloop report mysearch --name r1          # everything
```

On the leaderboard, `state` says how a score was reached: `full` for a complete training run, or
`stopped at 10%` for a design stopped early, which is listed last and not ranked. `length` is the
training length. `report.columns` adds columns (`valid.<metric>`, `test.<metric>`, `speed`,
`best_epoch`, `epochs_run`).

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
| the harness and the audit | `harness.level`, `harness.coordinator`, `harness.conductor`, `audit.reviews` |
| the budget | `budget.evaluations`, `budget.model_dollars`, `budget.wall_clock_hours` |
| compute | `compute.max_running`, `compute.time_limit`, `compute.qos`, `compute.gpus` |
| the model behind a role | `agents.models`, `agents.default_model` |
| the run type | `run.type` |

[Brief fields](fields.md) says for every field whether it can change.

**What cannot change** is what defines the problem (the objective, the direction of the score, the
dataset's identity, the frozen code) and a few settings fixed when a run starts (the agent backend, the
scheduler, the run command, the noise floor, the quick check). [Brief fields](fields.md) marks each. Such a
request is refused with the reason, and the run goes on.

**A change that moves other settings.** Changing `budget.evaluations` across a boundary of the
guidance, or changing `run.type`, moves the settings that follow from it. The ledger entry lists every
setting that moved with it.

## Changing the length of a run

`evaluation.allowance` (and `evaluation.seed`, `data.fraction`) change what a score means: a model
trained for 50 epochs is not comparable with one trained for 30. So a new **period** begins:

- The best design of each of the `evaluation.leaders_refit` leading lineages is trained under the new
  setting. These are the references for the new period.
- Earlier scores stay in the record and still feed the agents' lessons. They no longer decide
  selection.

Whether a reference is trained again or continued from its checkpoint is set by
`evaluation.on_length_change`:

| Value | What happens |
|---|---|
| `auto` | continued when `evaluation.schedule_depends_on_length` is false and `evaluation.keep_checkpoints` is true; otherwise trained again |
| `continue` | continued from the checkpoint (the evaluator gets `EVO_CONTINUE_FROM`) |
| `rerun` | trained again from scratch |
| `compare_anyway` | no new period: old and new scores are compared as they are |

Continuing is only right when the learning-rate schedule does not depend on the length of the run. A
cosine schedule over 30 epochs has decayed to nearly nothing by the end; 20 more epochs at that rate
teach little, and the continued model looks worse than a fresh 50-epoch fit of the same design.

## Notes to the agents

```
evoloop note mysearch --name r1 "No attention layers." --roles writer --by "Your Name"
evoloop withdraw mysearch --name r1 --id S4 --by "Your Name"
```

Every agent a note is addressed to reads it on every call from then on, and each call
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

## Stop and resume a search

```
evoloop stop mysearch --name r1 --by "Your Name"            # start nothing more; end when the jobs do
evoloop stop mysearch --name r1 --run R12 --by "Your Name"   # stop one run
```

To resume a stopped search, run the same command that started it: `evoloop run mysearch --name r1`. It picks
up from the files on disk, including jobs that were still training. To give a finished search more budget,
raise it with `evoloop set mysearch --name r1 budget.evaluations=N --by "Your Name"` and resume.

## The evaluator's own knobs

`evaluation.variables` is passed to every job as environment variables. Use it for what your evaluator
reads beside the run length: the patience of its early stopping, a minimum gain, a batch size.

```
evoloop set mysearch --name r1 'evaluation.variables={"PATIENCE": 10, "MIN_GAIN": 0.001}' --by "Your Name"
```

Like the run length, these change what a score means, so a change begins a new period: the leaders are
trained again under the new values and earlier scores stop deciding selection. Every run records the
values it ran with.

## Fixing the evaluator or the frozen code during a run

Everything outside the marked blocks, and `adapter/`, is frozen: a run checks it at every start and once
a minute. If it has changed, nothing new is started (jobs already training go on) and the run comes to
rest as paused, saying so. Either restore the files, or record that the change is meant:

```
evoloop rehash mysearch --name r1 --by "Your Name" --reason "the stop rule read the wrong column"
evoloop rehash mysearch --name r1 --by "Your Name" --reason "new loss scaling" --moves-scores
```

With `--moves-scores` a new period begins, because scores before and after the change are not
comparable. Without it you are saying the change moves no score (a logging fix, a crash fix). The
ledger keeps who said so, why, and the two hashes.

## Limits

`limits` are enforced by code on every design: on any figure the evaluator reports, on `parameters`, and
on `examples_per_s` from its inference speed.

```
evoloop set mysearch --name r1 'limits={"parameters": {"max": 20000000}, "examples_per_s": {"min": 500}}' --by "Your Name"
```

- A limit must be measurable. If a result does not report a figure that a limit names, the design is rejected
  and the run pauses, saying which figure is missing. Make the evaluator report it, or remove the
  limit, and continue the run. A limit is never skipped because its figure is absent. (Progress lines may lack
  it: only the final result must carry it.)
- A design outside a limit is **rejected**: it gets no score and is not charged, up to
  `budget.max_uncounted_rejections` (50); it is not a failure and does not count toward a stall.
- A run whose progress lines already show it outside a limit is stopped there, not trained to the end.
  Put the figure in the first progress line and a design that is too big or too slow costs seconds.
- The evaluator can reject too: a result with `"valid": false, "rejected": "the reason"` is treated the
  same way.
- The writers are shown the limits, and each rejected design with its reason.

## Ordering slots yourself

```
evoloop force mysearch --name r1 --mode cross --kind graft --count 3 --by "Your Name"
evoloop force mysearch --name r1 --mode new --count 2 --by "Your Name" \
    --instruction "FiLM after the norm in every conv block, tanh-scaled, replacing the norm's affine."
```

The next slots go where you say, ahead of the schedule, and the writers of those slots are given your
instruction as an order for that slot. Unlike a note, it is not standing advice: it applies to those
slots and no others.

## Designs from an earlier run, and models to compare with

```
evoloop import mysearch --name r2 --from-run mysearch/runs/r1 --top 5 --by "Your Name"
evoloop import mysearch --name r2 --from-run mysearch/runs/r1 --designs C12 C40 --by "Your Name"
```

The designs are trained in this run as designs of its own, and can then be built on. Their scores in the
earlier run are not carried over, since that run may have trained differently; each import keeps a note
of where it came from and what it scored there. A design whose blocks do not fit this run's code is
refused, with the reason.

A model that is not part of the search (a published baseline, an earlier run's best as it scored then)
goes on the leaderboard as a reference row:

```
evoloop reference mysearch --name r2 --label "published model" --score 0.493 --metric test.profile_r=0.61 --by "Your Name"
evoloop reference mysearch --name r2 --from-run mysearch/runs/r1 --top 3 --by "Your Name"
```

Reference rows are shown and marked as such; they take no part in selection.

## A steered run

A run that was steered is not a clean test of one fixed strategy. The report lists every entry of the
ledger with the number of evaluations at which it took effect, and the study file says how many
steering entries the run had.

## Talking to the agent that runs the search

With `harness.conductor: agent` an agent is in charge of the course of the search, and `evoloop chat`
talks to it: it explains, changes course within its bounds when you ask, and takes your yes or no. With
`harness.conductor: code` (the default) the search is deterministic and you steer with the commands on
this page. See [who runs the search](strategist.md#talking-to-it).
