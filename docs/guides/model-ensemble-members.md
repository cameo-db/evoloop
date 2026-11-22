# Find models that fail differently, for an ensemble

Skill `model-ensemble-members`. Find models that are each good and that make different errors from one another, so that averaging them gains more than averaging copies of the best one.

File: [`evoloop/skills/model-ensemble-members/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-ensemble-members/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-ensemble-members/skill.yaml)). A search copies this file to `mysearch/skills/model-ensemble-members/skill.yaml` when you choose the skill, and reads that copy. [Edit it during setup](../skills.md).

## When to use

You will average several models (as a final predictor, or as the teacher for model-distillation) and want members that add to each other. Not for a single best model.

## Usage

[Use this skill in setup](../setting-up.md#3-answer-the-setup-questions) · [Combine it with another skill](../skills.md#combining-skills) · <a href="../../which-search/?goal=model-ensemble-members&run=survey#preview-a-search">Preview the resulting search</a>

In setup, name it at the skill question. Or put these lines in `brief.yaml`; the budget and any limits or ranges are placeholders.

```yaml
run:
  skill: model-ensemble-members
  type: survey
budget:
  evaluations: 150
```

## Settings

A skill's settings override the run type's and the autonomy level's. Settings in your brief override the skill's.

| Setting | Value |
|---|---|
| [`schedule.novelty`](../fields.md#schedule-novelty) | `0.6` |
| [`schedule.novelty_measure`](../fields.md#schedule-novelty_measure) | `behaviour` |
| [`schedule.phases`](../fields.md#schedule-phases) | `[{cross: 0.1, local: 0.3, new: 0.6, until: 0.6}, {cross: 0.15, local: 0.6, new: 0.25, until: 1.0}]` |
| [`strategy.descriptors`](../fields.md#strategy-descriptors) | `[behaviour]` |
| [`strategy.mechanism`](../fields.md#strategy-mechanism) | `archive` |

## Agent guidance

This text is added to every call to the role named. It is taken from the skill's file.

=== "Every role"

    The result of this search is a set of models to be averaged. An ensemble gains only as far as its members are
    wrong in different places, so a design that scores a little below the leader and fails on different examples
    is worth more here than a near-copy of the leader. Designs are grouped by where their errors fall, and the
    best of each group is kept.

=== "Writer"

    Aim for a good model that reaches its answers a different way. Sources of real difference, roughly from
    strongest to weakest:

    - a different inductive bias: convolution against attention against recurrence, local against global, a
      different representation of the input;
    - a different view of the data: resolution, context length, features, augmentation;
    - a different objective or loss weighting;
    - a different size or depth.

    A different seed or a small change of settings gives little: do not spend a slot on it.
    In `hypothesis`, say on which kind of example you expect this design to differ from the leader.

=== "Analyst"

    Report which groups of designs fail together and which fail apart, and which kinds of change produced a design
    in a new group. Note any design that is weak alone but unlike all the others.

=== "Strategist"

    When new designs keep landing in groups that already exist, raise the share of novel slots or change the
    search space; more local moves will not add diversity.

The writer and the analyst are also given these rules:

| If the results show | Then |
|---|---|
| new designs keep falling in the same behaviour group as the leader | the changes are too small to change behaviour: change the inductive bias or the view of the data |
| a design is in a group of its own but scores far below the others | improve it within its lineage before discarding it; a member too weak drags an average down |
| all designs fail on the same examples | those examples may be mislabelled or outside what the data can teach: no member will fix them |
| there are many groups with one design each | the similarity threshold is too strict for this task's noise: lower strategy.behaviour_similarity |

And the writer is told, in the first half of the budget: "Found as many different families as possible, each trained well enough to judge." In the second half: "Raise the score of the best design in each group without making it behave like the others."

## Evaluator requirements

- report `signature` in result.json: a list of numbers saying where the model's errors fall (per class, per range of the target, or per held-out example); the groups are made from it
- after the search, score the average of the best design of each group yourself; evoloop does not train or score ensembles

[Write the evaluator](../evaluator.md) · [Evaluator interface](../project-contract.md)

## Reading the results

Read the population table: each row is the best design of one behaviour group. Those are the candidate members. evoloop does not score the ensemble itself: average the best of each group yourself and check the average against the best single model.

## Rationale

An ensemble gains only as far as its members are wrong in different places. So designs are grouped by where their errors fall and the best of each group is kept, which keeps a design that is slightly worse but different in play.

## Related skills

| If | Use |
|---|---|
| you want one best model | [`model-performance`](model-performance.md) |

Can be combined with [`model-distillation`](model-distillation.md): `run.skill: [model-ensemble-members, model-distillation]`.

## Skill file

[`evoloop/skills/model-ensemble-members/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-ensemble-members/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-ensemble-members/skill.yaml))

```yaml
name: model-ensemble-members
title: Find models that fail differently, for an ensemble
summary: Find models that are each good and that make different errors from one another, so that averaging them gains more than averaging copies of the best one.
domain: model
objective: a set of strong models whose errors do not coincide
tags: [ensemble, diversity, behaviour, errors, averaging, teacher]
version: 1
authors: [evoloop]
when: >
  You will average several models (as a final predictor, or as the teacher for model-distillation) and want
  members that add to each other. Not for a single best model.
settings:
  strategy:
    mechanism: archive
    descriptors: [behaviour]
  schedule:
    novelty: 0.6
    novelty_measure: behaviour
    phases: [{until: 0.6, new: 0.6, cross: 0.1, local: 0.3}, {until: 1.0, new: 0.25, cross: 0.15, local: 0.6}]
guidance:
  all: |
    The result of this search is a set of models to be averaged. An ensemble gains only as far as its members are
    wrong in different places, so a design that scores a little below the leader and fails on different examples
    is worth more here than a near-copy of the leader. Designs are grouped by where their errors fall, and the
    best of each group is kept.
  writer: |
    Aim for a good model that reaches its answers a different way. Sources of real difference, roughly from
    strongest to weakest:
    - a different inductive bias: convolution against attention against recurrence, local against global, a
      different representation of the input;
    - a different view of the data: resolution, context length, features, augmentation;
    - a different objective or loss weighting;
    - a different size or depth.
    A different seed or a small change of settings gives little: do not spend a slot on it.
    In `hypothesis`, say on which kind of example you expect this design to differ from the leader.
  analyst: |
    Report which groups of designs fail together and which fail apart, and which kinds of change produced a design
    in a new group. Note any design that is weak alone but unlike all the others.
  strategist: |
    When new designs keep landing in groups that already exist, raise the share of novel slots or change the
    search space; more local moves will not add diversity.
diagnose:
  - see: "new designs keep falling in the same behaviour group as the leader"
    do: "the changes are too small to change behaviour: change the inductive bias or the view of the data"
  - see: "a design is in a group of its own but scores far below the others"
    do: "improve it within its lineage before discarding it; a member too weak drags an average down"
  - see: "all designs fail on the same examples"
    do: "those examples may be mislabelled or outside what the data can teach: no member will fix them"
  - see: "there are many groups with one design each"
    do: "the similarity threshold is too strict for this task's noise: lower strategy.behaviour_similarity"
stages:
  early: "Found as many different families as possible, each trained well enough to judge."
  late: "Raise the score of the best design in each group without making it behave like the others."
needs:
  adapter:
    - "report `signature` in result.json: a list of numbers saying where the model's errors fall (per class, per range of the target, or per held-out example); the groups are made from it"
    - "after the search, score the average of the best design of each group yourself; evoloop does not train or score ensembles"
  figures: []
  references: []
combines: [model-distillation]
conflicts: [settings-tuning, model-efficiency]
goal: Find models that fail differently, for an ensemble
start:
  run_type: survey
  evaluations: 150
why: >
  An ensemble gains only as far as its members are wrong in different places. So designs are grouped by where
  their errors fall and the best of each group is kept, which keeps a design that is slightly worse but
  different in play.
reading: >
  Read the population table: each row is the best design of one behaviour group. Those are the candidate
  members. evoloop does not score the ensemble itself: average the best of each group yourself and check the
  average against the best single model.
instead:
  - if: you want one best model
    use: model-performance
```
