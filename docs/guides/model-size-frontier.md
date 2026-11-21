# Find the best model at several sizes

Skill `model-size-frontier` · domain: model · [the skill in full](../skill-library.md#model-size-frontier)

Find the best model at each size (or speed), from very small to large, so that the result is a whole trade-off curve to choose from and not one winner.

## Start here

Put this in `brief.yaml` (or give the same answers to `evoloop setup`), then read `evoloop plan` before you confirm.

```yaml
run:
  type: survey
  skill: model-size-frontier
budget:
  evaluations: 200
limits:
  parameters:
    min: 50000
    max: 50000000
```

The budget, and any limits or ranges, are placeholders: put in your own.

## Why this set-up

The deliverable is a curve, not a point: the best design in each band of size. An archive keeps the best of each band, new designs are aimed at bands that are empty, and a design is a success when it leads its band even if a larger one scores higher. This needs more evaluations than a search for one model.

The skill sets these for you (anything you set in the brief wins):

| Setting | Value |
|---|---|
| [`report.columns`](../fields.md#report-columns) | `[speed]` |
| [`schedule.novelty`](../fields.md#schedule-novelty) | `0.6` |
| [`schedule.phases`](../fields.md#schedule-phases) | `[{cross: 0.15, local: 0.35, new: 0.5, until: 0.5}, {cross: 0.25, local: 0.55, new: 0.2, until: 1.0}]` |
| [`strategy.descriptors`](../fields.md#strategy-descriptors) | `[size]` |
| [`strategy.mechanism`](../fields.md#strategy-mechanism) | `archive` |

## What your evaluator must report

- report `parameters` in result.json for every design; the bands are made from it
- to band by speed instead, report `inference_speed.examples_per_s` and set strategy.descriptors to the name of that metric under diagnostics
- set `limits` for the smallest and largest size worth having, so that designs outside the range are not trained
- Every result must report `parameters`. If none does, the report says so.

[Write the evaluator](../evaluator.md) shows how to report these; [Evaluator interface](../project-contract.md) is the reference.

## Choose something else when

| If | Use |
|---|---|
| one cheaper model at a fixed score is enough | [`model-efficiency`](model-efficiency.md) |
| the sizes should be students of a teacher | [`model-distillation`](model-distillation.md) with [`model-size-frontier`](model-size-frontier.md) |

It combines well with [`model-distillation`](model-distillation.md) (`run.skill: [model-size-frontier, ...]`).

## Reading the result

Read the population table band by band: each row is the best design of one size band. Plot score against size to see where a fourfold increase stops paying. Bands with one or two designs are not yet explored; treat their best as provisional.

Where to look: `evoloop leaderboard`, `evoloop show`, and the report ([Files of a run](../records.md)). To change course while it runs: [Watch and steer a run](../steering.md).

## What the agents are told

??? note "Every role"
    The result of this search is a set of models, one for each band of size, each the best found in its band. A
    design is a success if it is the best in its band, even when a larger design scores higher. The bands are
    steps of about fourfold in parameter count.

??? note "The writer"
    `thin_cells`, when present, lists the size bands with the fewest designs: aim a new design at one of them and
    say in `predicted_effect` what size you expect it to have.
    Ways to move a design to another band without starting again:
    - scale it as a whole: width, depth and resolution together, in proportion, travel further than any one alone;
    - at the small end, change the kind of layer (separable or grouped convolutions, shared weights, a smaller
      head) before shrinking widths until nothing works;
    - at the large end, add capacity where the errors say it is missing, not evenly.
    What is best at one size is often not best at another: do not assume the largest design's shape, shrunk, is
    the best small one. A local move should stay in its parent's band; say so if you mean to leave it.

??? note "The analyst"
    Describe the curve: where a fourfold increase in size still buys score and where it has stopped. Say which
    bands are well covered and which hold only one or two designs. Lessons are most useful in the form "at this
    size, X matters; above it, X does not".

??? note "The strategist"
    Order new designs for bands that are empty or thin. When every band has several designs, shift toward local
    moves and crossovers between neighbouring bands.

| If the results show | Then |
|---|---|
| a band holds no design, or only one | aim new designs at it: scale the nearest good design up or down as a whole |
| a larger band's best design scores no better than the band below it | the larger designs are wasting capacity: move the smaller band's best design up by scaling it, and compare |
| the smallest band's designs all fail or score near chance | that size is below what this approach can do: change the kind of layer, or accept the band above as the floor |
| the curve is flat across the top bands | the data or the recipe is the limit, not size: stop adding large designs and spend the budget lower down |

Early in the budget: Put at least two designs in every band, by scaling a few good shapes up and down.

Late in the budget: Improve the best design in each band with local moves, and cross neighbours.

You can change any of this: the search gets its own copy of the skill in `skills/model-size-frontier/skill.yaml` ([Skills](../skills.md)).
