# Improve a model's score

Skill `model-performance`. Raise the validation score by whatever the open blocks allow. Size and speed are not weighed unless you set limits.

File: [`evoloop/skills/model-performance/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-performance/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-performance/skill.yaml)). A search copies this file to `mysearch/skills/model-performance/skill.yaml` when you choose the skill, and reads that copy. [Edit it during setup](../skills.md).

## When to use it

The default for model development. Choose something more specific when the goal is a smaller model (model-efficiency), a family across sizes (model-size-frontier), a student of a teacher (model-distillation), or when only the training recipe or the settings may change.

## Use it

[Use this skill in setup](../setting-up.md#3-answer-the-questions) · [Combine it with another skill](../skills.md#combining-skills) · <a href="../../which-search/?goal=model-performance&run=explore_then_exploit#preview-a-search">Preview the resulting search</a>

In setup, name it at the skill question. Or put these lines in `brief.yaml`; the budget and any limits or ranges are placeholders.

```yaml
run:
  skill: model-performance
  type: explore_then_exploit
budget:
  evaluations: 100
```

## What it sets

Nothing. This skill only supplies instructions; the run type and the defaults set the search.

## What it tells the agents

This text is added to every call to the role named. It is taken from the skill's file.

=== "Every role"

    The aim is the best validation score. Size, speed and simplicity count only where the person's notes or the
    limits say so.

=== "Writer"

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

=== "Analyst"

    Say which kinds of change are still paying and which have stopped. Separate gains that repeat across lineages
    from single results within the noise. Name the limit (capacity, optimization, generalisation) the leader seems
    to be at, with the runs that show it.

=== "Strategist"

    A plateau with many near-identical designs calls for more new designs. A plateau with scattered designs and
    one clear leader calls for local work on the leader.

The writer and the analyst are also given these rules:

| If the results show | Then |
|---|---|
| training and validation scores are both poor and still improving at the end of the run | the run is too short or the optimization is slow: fix the schedule or normalisation before judging the architecture |
| training score is good, validation score is clearly worse | regularize, augment, or reduce capacity; do not add capacity |
| both scores stop improving early and stay poor | the model lacks capacity or a mechanism: widen, deepen, or add the missing range or interaction |
| the same design gives very different scores on a re-check | the gain is within the noise: treat it as no gain, and prefer changes that reduce variance |
| many designs fail the quick check or crash | the changes are too large for the frozen code around them: make smaller edits and keep shapes compatible |

And the writer is told, in the first half of the budget: "Cover different families of design; a rough version of each idea is enough to learn whether it has promise." In the second half: "Work on the two or three best families. Combine what each does well, and remove what ablations show is dead weight."

## What your evaluator must report

The score only.

[Write the evaluator](../evaluator.md) · [Evaluator interface](../project-contract.md)

## Reading the results

Read the leaderboard for the best design and its family, then "What each mode returned" to see whether new designs or local work produced the gains. A leader with a single fit is a candidate, not a result: fit it again on new seeds, and on the held-out set, before reporting it.

## Why these settings

With the architecture open and one number to raise, the search should spend its first evaluations finding out which kinds of design work, then concentrate on the best. That is the explore-then-exploit schedule, with families of designs kept alive side by side so that an early leader does not crowd out a slower starter.

## Related skills

| If | Use |
|---|---|
| the model must also be smaller or faster | [`model-efficiency`](model-efficiency.md) |
| the architecture must stay as it is | [`model-training-recipe`](model-training-recipe.md) |
| only numbers (learning rate, widths) should change | [`settings-tuning`](settings-tuning.md) |

Can be combined with [`model-training-recipe`](model-training-recipe.md): `run.skill: [model-performance, model-training-recipe]`.

## The file

[`evoloop/skills/model-performance/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-performance/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-performance/skill.yaml))

```yaml
name: model-performance
title: Raise a model's score
summary: Raise the validation score by whatever the open blocks allow. Size and speed are not weighed unless you set limits.
domain: model
objective: the best score, nothing else weighed
tags: [accuracy, performance, architecture, general]
version: 2
authors: [evoloop]
when: >
  The default for model development. Choose something more specific when the goal is a smaller model
  (model-efficiency), a family across sizes (model-size-frontier), a student of a teacher (model-distillation),
  or when only the training recipe or the settings may change.
settings: {}
guidance:
  all: |
    The aim is the best validation score. Size, speed and simplicity count only where the person's notes or the
    limits say so.
  writer: |
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
  analyst: |
    Say which kinds of change are still paying and which have stopped. Separate gains that repeat across lineages
    from single results within the noise. Name the limit (capacity, optimization, generalisation) the leader seems
    to be at, with the runs that show it.
  strategist: |
    A plateau with many near-identical designs calls for more new designs. A plateau with scattered designs and
    one clear leader calls for local work on the leader.
diagnose:
  - see: "training and validation scores are both poor and still improving at the end of the run"
    do: "the run is too short or the optimization is slow: fix the schedule or normalisation before judging the architecture"
  - see: "training score is good, validation score is clearly worse"
    do: "regularize, augment, or reduce capacity; do not add capacity"
  - see: "both scores stop improving early and stay poor"
    do: "the model lacks capacity or a mechanism: widen, deepen, or add the missing range or interaction"
  - see: "the same design gives very different scores on a re-check"
    do: "the gain is within the noise: treat it as no gain, and prefer changes that reduce variance"
  - see: "many designs fail the quick check or crash"
    do: "the changes are too large for the frozen code around them: make smaller edits and keep shapes compatible"
stages:
  early: "Cover different families of design; a rough version of each idea is enough to learn whether it has promise."
  late: "Work on the two or three best families. Combine what each does well, and remove what ablations show is dead weight."
needs:
  adapter: []
  figures: []
  references: []
combines: [model-training-recipe]
conflicts: [settings-tuning]
goal: Improve a model's score
start:
  run_type: explore_then_exploit
  evaluations: 100
why: >
  With the architecture open and one number to raise, the search should spend its first evaluations finding out
  which kinds of design work, then concentrate on the best. That is the explore-then-exploit schedule, with
  families of designs kept alive side by side so that an early leader does not crowd out a slower starter.
reading: >
  Read the leaderboard for the best design and its family, then "What each mode returned" to see whether new
  designs or local work produced the gains. A leader with a single fit is a candidate, not a result: fit it
  again on new seeds, and on the held-out set, before reporting it.
instead:
  - if: the model must also be smaller or faster
    use: model-efficiency
  - if: the architecture must stay as it is
    use: model-training-recipe
  - if: only numbers (learning rate, widths) should change
    use: settings-tuning
```
