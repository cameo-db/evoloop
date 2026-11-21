# Train a fixed architecture better

Skill `model-training-recipe` · domain: model · [the skill in full](../skill-library.md#model-training-recipe)

The architecture is fixed; the training recipe is open (the loss, the optimizer, the learning-rate schedule, regularization, augmentation). Between tuning numbers and changing the model.

## Start here

Put this in `brief.yaml` (or give the same answers to `evoloop setup`), then read `evoloop plan` before you confirm.

```yaml
run:
  type: explore_then_exploit
  skill: model-training-recipe
budget:
  evaluations: 80
```

!!! note "A starting point"
    These settings are a reasoned starting point. They have not been measured against alternatives; see [Status and limits](../status.md). The numbers in the example (the budget, any limits or ranges) are placeholders for yours.

## Why this set-up

The model is settled and the question is how well it can be trained, so only the blocks that define the loss, the optimizer, the schedule and the augmentation are open. Unlike tuning, the code of those blocks can change, not only their numbers.

The skill sets these for you (anything you set in the brief wins):

| Setting | Value |
|---|---|
| [`schedule.local_mix`](../fields.md) | `{ablation: 0.1, edit: 0.55, settings: 0.35}` |
| [`space.preset`](../fields.md) | `custom` |
| [`space.roles`](../fields.md) | `{augmentation: open, loss: open, optimizer: open, recipe: open, schedule: open, training: open}` |

## What your evaluator must report

- mark the loss, optimizer, schedule and augmentation as blocks with those roles; the model blocks stay closed
- report the training score beside the validation score under diagnostics, so that fitting and generalising can be told apart
- report `best_epoch` and `epochs_run` in result.json

How the adapter reports these: [The project's code](../project-contract.md).

## Choose something else when

| If | Use |
|---|---|
| only the numbers of the recipe should change | [`settings-tuning`](settings-tuning.md) |
| the model itself may change | [`model-performance`](model-performance.md) |

It combines well with [`model-performance`](model-performance.md), [`model-finetuning`](model-finetuning.md) (`run.skill: [model-training-recipe, ...]`).

## Reading the result

Compare the best recipe with the baseline row: the difference is what training alone was worth. Look at whether the training score or the gap to validation moved, and at the best epoch: a best epoch at the end of the run means the comparison favoured fast recipes and a longer run is needed.

Where to look: `evoloop leaderboard`, `evoloop show`, and the report ([Records and the study file](../records.md)). To change course while it runs: [Steering a run](../steering.md).

## What the agents are told

??? note "Every role"
    The model's architecture does not change in this search. Only how it is trained does: the loss, the optimizer,
    the learning-rate schedule, regularization, augmentation, and the training loop's own choices.

??? note "The writer"
    The parts of a recipe interact, so a change to one usually needs another to be re-set:
    - the loss decides what the model is asked for. Consider what it weighs (classes, ranges of the target,
      noisy examples), whether it matches the metric that is scored, and auxiliary terms.
    - the optimizer and schedule decide whether the model gets there. Warm-up, the peak rate, the decay, the
      batch size and weight decay move together; changing one alone often looks like a failure of the other.
    - regularization and augmentation decide what it generalises to. Augmentations should be changes the answer
      is truly invariant to; ones it is not invariant to teach the wrong thing.
    - the loop: gradient clipping, mixed precision, averaging of weights, which checkpoint is kept.
    One change per design, with the settings it interacts with re-set in the same design and named.

??? note "The analyst"
    Group lessons by part of the recipe (loss, optimizer, schedule, regularization, augmentation). Say whether a
    gain came from fitting better (training score rose) or generalising better (the gap closed).

??? note "The strategist"
    When edits to one part of the recipe stop gaining, move the slots to another part before concluding the recipe
    is done.

| If the results show | Then |
|---|---|
| training is unstable or diverges after a recipe change | lower the peak learning rate or lengthen warm-up for that design before rejecting the change |
| the training score rose and the validation score did not | the change helped fitting, not generalisation: pair it with regularization or augmentation |
| a new augmentation lowers both training and validation scores | the answer is not invariant to it: weaken or drop it |
| the best epoch is the last one | the run is too short for this recipe: the comparison favours fast recipes, so say so and ask for a longer run |
| the best epoch is very early and later epochs are worse | the rate is too high late, or regularization too weak: change the decay or add regularization |

Early in the budget: Try one substantial change in each part of the recipe, to find which part has room.

Late in the budget: Work on the parts that paid, and re-tune the settings they interact with.

You can change any of this: the search gets its own copy of the skill in `skills/model-training-recipe/skill.yaml` ([Skills](../skills.md)).
