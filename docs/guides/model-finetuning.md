# Adapt a pretrained model to a task

Skill `model-finetuning`. Start from a pretrained model and search over how to adapt it (what to freeze, what to add, the learning rates by layer, how long to train).

File: [`evoloop/skills/model-finetuning/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-finetuning/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-finetuning/skill.yaml)). A search copies this file to `mysearch/skills/model-finetuning/skill.yaml` when you choose the skill, and reads that copy. [Edit it during setup](../skills.md).

## Use it

```yaml
run:
  skill: model-finetuning
  type: refine
budget:
  evaluations: 60
```

Put these lines in `brief.yaml`. The budget and any limits or ranges are placeholders. <a href="../../which-search/?goal=model-finetuning&run=refine#preview-a-search">Preview the resulting search</a>.

A pretrained model exists and the task has far less data than the model was trained on. Not for training from scratch.

## What it sets

A skill's settings override the run type's and the autonomy level's. Settings in your brief override the skill's.

| Setting | Value |
|---|---|
| [`schedule.local_mix`](../fields.md#schedule-local_mix) | `{ablation: 0.15, edit: 0.4, settings: 0.45}` |
| [`schedule.novelty`](../fields.md#schedule-novelty) | `0.25` |

## What it tells the agents

This text is added to every call to the role named. It is the skill's file verbatim.

=== "Every role"

    This search adapts a pretrained model. The pretrained weights hold most of what the model knows; the risk is
    losing that while fitting a small dataset. The pretrained backbone's own architecture is not to be redesigned.

=== "Writer"

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

=== "Analyst"

    Say how much each design gains over the frozen backbone with a linear head, and whether gains come from the
    head, from unfreezing, or from added modules. Watch for designs that fit training data and forget.

=== "Strategist"

    Settings moves are worth more here than in a search from scratch; keep their share up while they gain.

The writer and the analyst are also given these rules:

| If the results show | Then |
|---|---|
| the score falls below the frozen-backbone baseline when layers are unfrozen | the pretrained weights are being destroyed: lower the backbone's learning rate, add warm-up, or unfreeze fewer layers |
| the training score climbs and the validation score peaks in the first epochs | it is overfitting: train fewer parameters (adapters, last layers), regularize, or stop earlier |
| nothing beats the linear head on the frozen backbone | read from an earlier layer or change the pooling before unfreezing anything |
| results differ widely between seeds | the dataset is small for the number of trained parameters: train fewer, and average seeds before comparing |

And the writer is told, in the first half of the budget: "Establish the frozen-backbone baseline, then compare the broad options (head only, adapters, partial and full unfreezing)." In the second half: "Tune the learning rates and the schedule of the best option, and refine the head."

## What your scoring script must report

- load the pretrained weights from a fixed path outside base/ (weights are not copied per design)
- mark as open the head, the choice of what is frozen, and the optimizer settings; leave the backbone's definition closed
- add a reference row for the frozen backbone with a linear head
- A leaderboard row for frozen backbone, added with `evoloop reference`. The report warns if it is missing.

[Write the evaluator](../evaluator.md) · [Evaluator interface](../project-contract.md)

## Reading the results

Compare every design with the reference row for the frozen backbone with a linear head: that is the cheapest baseline, and the gain over it is what adapting was worth. Watch the best epoch; fine-tuning that peaks in the first epochs is overfitting.

## Why these settings

Most of what the model knows is in its pretrained weights, so the search stays close to a working set-up and spends more of its moves on settings (which layers train, at what rate) than a search from scratch would.

## Related skills

| If | Use |
|---|---|
| you are training from scratch | [`model-performance`](model-performance.md) |

Can be combined with [`model-training-recipe`](model-training-recipe.md): `run.skill: [model-finetuning, model-training-recipe]`.

## The file

[`evoloop/skills/model-finetuning/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-finetuning/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-finetuning/skill.yaml))

```yaml
name: model-finetuning
title: Adapt a pretrained model to a task
summary: Start from a pretrained model and search over how to adapt it (what to freeze, what to add, the learning rates by layer, how long to train).
domain: model
objective: the best score on a task starting from a pretrained model
tags: [finetuning, pretrained, transfer, adapters, foundation model, freezing]
version: 1
authors: [evoloop]
when: >
  A pretrained model exists and the task has far less data than the model was trained on. Not for training from
  scratch.
settings:
  schedule:
    novelty: 0.25
    local_mix: {edit: 0.4, settings: 0.45, ablation: 0.15}
guidance:
  all: |
    This search adapts a pretrained model. The pretrained weights hold most of what the model knows; the risk is
    losing that while fitting a small dataset. The pretrained backbone's own architecture is not to be redesigned.
  writer: |
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
  analyst: |
    Say how much each design gains over the frozen backbone with a linear head, and whether gains come from the
    head, from unfreezing, or from added modules. Watch for designs that fit training data and forget.
  strategist: |
    Settings moves are worth more here than in a search from scratch; keep their share up while they gain.
diagnose:
  - see: "the score falls below the frozen-backbone baseline when layers are unfrozen"
    do: "the pretrained weights are being destroyed: lower the backbone's learning rate, add warm-up, or unfreeze fewer layers"
  - see: "the training score climbs and the validation score peaks in the first epochs"
    do: "it is overfitting: train fewer parameters (adapters, last layers), regularize, or stop earlier"
  - see: "nothing beats the linear head on the frozen backbone"
    do: "read from an earlier layer or change the pooling before unfreezing anything"
  - see: "results differ widely between seeds"
    do: "the dataset is small for the number of trained parameters: train fewer, and average seeds before comparing"
stages:
  early: "Establish the frozen-backbone baseline, then compare the broad options (head only, adapters, partial and full unfreezing)."
  late: "Tune the learning rates and the schedule of the best option, and refine the head."
needs:
  adapter:
    - "load the pretrained weights from a fixed path outside base/ (weights are not copied per design)"
    - "mark as open the head, the choice of what is frozen, and the optimizer settings; leave the backbone's definition closed"
    - "add a reference row for the frozen backbone with a linear head"
  figures: []
  references: ["frozen backbone"]
combines: [model-training-recipe]
conflicts: [settings-tuning]
goal: Adapt a pretrained model to a task
start:
  run_type: refine
  evaluations: 60
why: >
  Most of what the model knows is in its pretrained weights, so the search stays close to a working set-up and
  spends more of its moves on settings (which layers train, at what rate) than a search from scratch would.
reading: >
  Compare every design with the reference row for the frozen backbone with a linear head: that is the cheapest
  baseline, and the gain over it is what adapting was worth. Watch the best epoch; fine-tuning that peaks in the
  first epochs is overfitting.
instead:
  - if: you are training from scratch
    use: model-performance
```
