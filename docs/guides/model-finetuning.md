# Adapt a pretrained model to a task

Skill `model-finetuning` · domain: model · [the skill in full](../skill-library.md#model-finetuning)

Start from a pretrained model and search over how to adapt it (what to freeze, what to add, the learning rates by layer, how long to train).

## Start here

Put this in `brief.yaml` (or give the same answers to `evoloop setup`), then read `evoloop plan` before you confirm.

```yaml
run:
  type: refine
  skill: model-finetuning
budget:
  evaluations: 60
```

The budget, and any limits or ranges, are placeholders: put in your own.

## Why this set-up

Most of what the model knows is in its pretrained weights, so the search stays close to a working set-up and spends more of its moves on settings (which layers train, at what rate) than a search from scratch would.

The skill sets these for you (anything you set in the brief wins):

| Setting | Value |
|---|---|
| [`schedule.local_mix`](../fields.md#schedule-local_mix) | `{ablation: 0.15, edit: 0.4, settings: 0.45}` |
| [`schedule.novelty`](../fields.md#schedule-novelty) | `0.25` |

## What your evaluator must report

- load the pretrained weights from a fixed path outside base/ (weights are not copied per design)
- mark as open the head, the choice of what is frozen, and the optimizer settings; leave the backbone's definition closed
- add a reference row for the frozen backbone with a linear head
- Add a row to the leaderboard for frozen backbone, to compare against (`evoloop reference`).

[Write the evaluator](../evaluator.md) shows how to report these; [Evaluator interface](../project-contract.md) is the reference.

## Choose something else when

| If | Use |
|---|---|
| you are training from scratch | [`model-performance`](model-performance.md) |

It combines well with [`model-training-recipe`](model-training-recipe.md) (`run.skill: [model-finetuning, ...]`).

## Reading the result

Compare every design with the reference row for the frozen backbone with a linear head: that is the cheapest baseline, and the gain over it is what adapting was worth. Watch the best epoch; fine-tuning that peaks in the first epochs is overfitting.

Where to look: `evoloop leaderboard`, `evoloop show`, and the report ([Files of a run](../records.md)). To change course while it runs: [Watch and steer a run](../steering.md).

## What the agents are told

??? note "Every role"
    This search adapts a pretrained model. The pretrained weights hold most of what the model knows; the risk is
    losing that while fitting a small dataset. The pretrained backbone's own architecture is not to be redesigned.

??? note "The writer"
    The choices that matter, roughly in order:
    - what is trained: the head alone, the last layers, everything, or small added modules (adapters, low-rank
      updates) with the backbone frozen. Less data argues for training less.
    - the learning rates: a much lower rate for pretrained layers than for new ones, lower still for early
      layers; a short warm-up. Too high a rate destroys the pretrained weights in the first steps.
    - the head: its pooling over the backbone's outputs, its depth, which layer it reads from. The last layer is
      not always the best one to read.
    - how long: fine-tuning overfits quickly; keep the best checkpoint, not the last.
    - the input: match the preprocessing the model was pretrained with before changing anything else.
    Compare every design with the cheapest baseline: the frozen backbone with a linear head.

??? note "The analyst"
    Say how much each design gains over the frozen backbone with a linear head, and whether gains come from the
    head, from unfreezing, or from added modules. Watch for designs that fit training data and forget.

??? note "The strategist"
    Settings moves are worth more here than in a search from scratch; keep their share up while they gain.

| If the results show | Then |
|---|---|
| the score falls below the frozen-backbone baseline when layers are unfrozen | the pretrained weights are being destroyed: lower the backbone's learning rate, add warm-up, or unfreeze fewer layers |
| the training score climbs and the validation score peaks in the first epochs | it is overfitting: train fewer parameters (adapters, last layers), regularize, or stop earlier |
| nothing beats the linear head on the frozen backbone | read from an earlier layer or change the pooling before unfreezing anything |
| results differ widely between seeds | the dataset is small for the number of trained parameters: train fewer, and average seeds before comparing |

Early in the budget: Establish the frozen-backbone baseline, then compare the broad options (head only, adapters, partial and full unfreezing).

Late in the budget: Tune the learning rates and the schedule of the best option, and refine the head.

You can change any of this: the search gets its own copy of the skill in `skills/model-finetuning/skill.yaml` ([Skills](../skills.md)).
