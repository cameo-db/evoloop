# Improve a model's score

Raise the validation score by whatever the open blocks allow. Size and speed are not weighed unless you set limits.

## What a good result looks like

Read the leaderboard for the best design and its family, then "What each mode returned" to see whether new designs or local work produced the gains. A leader with a single fit is a candidate, not a result: fit it again on new seeds, and on the held-out set, before reporting it.

## Start here

```yaml
run:
  type: explore_then_exploit
  skill: model-performance
budget:
  evaluations: 100
```

These lines go in `brief.yaml`. The budget, and any limits or ranges, are placeholders for your own. <a href="../../which-search/?goal=model-performance&run=explore_then_exploit#preview-your-search">Preview this search</a> to see what it will do, or [set up this search](../setting-up.md) on your project. The goal is the skill `model-performance`, shown in full in the [skill library](../skill-library.md#model-performance).

## Why this set-up

With the architecture open and one number to raise, the search should spend its first evaluations finding out which kinds of design work, then concentrate on the best. That is the explore-then-exploit schedule, with families of designs kept alive side by side so that an early leader does not crowd out a slower starter.

The skill sets nothing itself: the run type and the defaults decide the search, and the skill supplies the guidance.

## What your evaluator must report

Only the score. Nothing else is required.

[Write the evaluator](../evaluator.md) shows how to report these; [Evaluator interface](../project-contract.md) is the reference.

## Choose something else when

| If | Use |
|---|---|
| the model must also be smaller or faster | [`model-efficiency`](model-efficiency.md) |
| the architecture must stay as it is | [`model-training-recipe`](model-training-recipe.md) |
| only numbers (learning rate, widths) should change | [`settings-tuning`](settings-tuning.md) |

It combines well with [`model-training-recipe`](model-training-recipe.md) (`run.skill: [model-performance, ...]`).

## Where to look

`evoloop leaderboard` for the ranking, `evoloop show` for one design, and the report for everything ([Files of a run](../records.md)). To change course while it runs: [Watch and steer a run](../steering.md).

## What the agents are told

??? note "Every role"
    The aim is the best validation score. Size, speed and simplicity count only where the person's notes or the
    limits say so.

??? note "The writer"
    Before adding to the leader, work out what limits it. There are three usual limits, and each calls for a
    different kind of change:
    - capacity: it cannot fit the training data. More width, depth, or a mechanism it lacks (a longer range, a
      different pooling, an interaction between parts).
    - optimization: it could fit but trains slowly or unstably. Normalisation, skip connections, initialisation,
      the learning-rate schedule, the batch size.
    - generalisation: it fits training data and not validation data. Regularisation, augmentation, less capacity,
      weight sharing, an inductive bias that matches the data.
    Make one change with one stated cause. A change that helped in one lineage is worth trying in another; a change
    that failed in two different lineages is not worth a third try without a new reason.
    Do not spend a slot on a change smaller than the noise floor can show.

??? note "The analyst"
    Say which kinds of change are still paying and which have stopped. Separate gains that repeat across lineages
    from single results within the noise. Name the limit (capacity, optimization, generalisation) the leader seems
    to be at, with the runs that show it.

??? note "The strategist"
    A plateau with many near-identical designs calls for more new designs. A plateau with scattered designs and
    one clear leader calls for local work on the leader.

| If the results show | Then |
|---|---|
| training and validation scores are both poor and still improving at the end of the run | the run is too short or the optimization is slow: fix the schedule or normalisation before judging the architecture |
| training score is good, validation score is clearly worse | regularize, augment, or reduce capacity; do not add capacity |
| both scores stop improving early and stay poor | the model lacks capacity or a mechanism: widen, deepen, or add the missing range or interaction |
| the same design gives very different scores on a re-check | the gain is within the noise: treat it as no gain, and prefer changes that reduce variance |
| many designs fail the quick check or crash | the changes are too large for the frozen code around them: make smaller edits and keep shapes compatible |

Early in the budget: Cover different families of design; a rough version of each idea is enough to learn whether it has promise.

Late in the budget: Work on the two or three best families. Combine what each does well, and remove what ablations show is dead weight.

You can change any of this: the search gets its own copy of the skill in `skills/model-performance/skill.yaml` ([Skills](../skills.md)).
