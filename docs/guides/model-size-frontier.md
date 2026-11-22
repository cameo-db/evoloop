# Find the best model at several sizes

Skill `model-size-frontier`. Find the best model at each size (or speed), from very small to large, so that the result is a whole trade-off curve to choose from and not one winner.

File: [`evoloop/skills/model-size-frontier/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-size-frontier/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-size-frontier/skill.yaml)). A search copies this file to `mysearch/skills/model-size-frontier/skill.yaml` when you choose the skill, and reads that copy. [Edit it during setup](../skills.md).

## When to use

You need models for several budgets (a phone, a server, a screen of millions of inputs), or want to know what accuracy each size buys before choosing. For one cheaper model at a fixed score use model-efficiency.

## Usage

[Use this skill in setup](../setting-up.md#3-answer-the-setup-questions) · [Combine it with another skill](../skills.md#combining-skills) · <a href="../../which-search/?goal=model-size-frontier&run=survey#preview-a-search">Preview the resulting search</a>

In setup, name it at the skill question. Or put these lines in `brief.yaml`; the budget and any limits or ranges are placeholders.

```yaml
run:
  skill: model-size-frontier
  type: survey
budget:
  evaluations: 200
limits:
  parameters:
    min: 50000
    max: 50000000
```

## Settings

A skill's settings override the run type's and the autonomy level's. Settings in your brief override the skill's.

| Setting | Value |
|---|---|
| [`report.columns`](../fields.md#report-columns) | `[speed]` |
| [`schedule.novelty`](../fields.md#schedule-novelty) | `0.6` |
| [`schedule.phases`](../fields.md#schedule-phases) | `[{cross: 0.15, local: 0.35, new: 0.5, until: 0.5}, {cross: 0.25, local: 0.55, new: 0.2, until: 1.0}]` |
| [`strategy.descriptors`](../fields.md#strategy-descriptors) | `[size]` |
| [`strategy.mechanism`](../fields.md#strategy-mechanism) | `archive` |

## Agent guidance

This text is added to every call to the role named. It is taken from the skill's file.

=== "Every role"

    The result of this search is a set of models, one for each band of size, each the best found in its band. A
    design is a success if it is the best in its band, even when a larger design scores higher. The bands are
    steps of about fourfold in parameter count.

=== "Writer"

    `thin_cells`, when present, lists the size bands with the fewest designs: aim a new design at one of them and
    say in `predicted_effect` what size you expect it to have.
    Ways to move a design to another band without starting again:

    - scale it as a whole: width, depth and resolution together, in proportion, travel further than any one alone;
    - at the small end, change the kind of layer (separable or grouped convolutions, shared weights, a smaller
      head) before shrinking widths until nothing works;
    - at the large end, add capacity where the errors say it is missing, not evenly.

    What is best at one size is often not best at another: do not assume the largest design's shape, shrunk, is
    the best small one. A local move should stay in its parent's band; say so if you mean to leave it.

=== "Analyst"

    Describe the curve: where a fourfold increase in size still buys score and where it has stopped. Say which
    bands are well covered and which hold only one or two designs. Lessons are most useful in the form "at this
    size, X matters; above it, X does not".

=== "Strategist"

    Order new designs for bands that are empty or thin. When every band has several designs, shift toward local
    moves and crossovers between neighbouring bands.

The writer and the analyst are also given these rules:

| If the results show | Then |
|---|---|
| a band holds no design, or only one | aim new designs at it: scale the nearest good design up or down as a whole |
| a larger band's best design scores no better than the band below it | the larger designs are wasting capacity: move the smaller band's best design up by scaling it, and compare |
| the smallest band's designs all fail or score near chance | that size is below what this approach can do: change the kind of layer, or accept the band above as the floor |
| the curve is flat across the top bands | the data or the recipe is the limit, not size: stop adding large designs and spend the budget lower down |

And the writer is told, in the first half of the budget: "Put at least two designs in every band, by scaling a few good shapes up and down." In the second half: "Improve the best design in each band with local moves, and cross neighbours."

## Evaluator requirements

- report `parameters` in result.json for every design; the bands are made from it
- to band by speed instead, report `inference_speed.examples_per_s` and set strategy.descriptors to the name of that metric under diagnostics
- set `limits` for the smallest and largest size worth having, so that designs outside the range are not trained
- `parameters` in every result. The report warns if no result has it.

[Write the evaluator](../evaluator.md) · [Evaluator interface](../project-contract.md)

## Reading the results

Read the population table band by band: each row is the best design of one size band. Plot score against size to see where a fourfold increase stops paying. Bands with one or two designs are not yet explored; treat their best as provisional.

## Rationale

The deliverable is a curve, not a point: the best design in each band of size. An archive keeps the best of each band, new designs are aimed at bands that are empty, and a design is a success when it leads its band even if a larger one scores higher. This needs more evaluations than a search for one model.

## Related skills

| If | Use |
|---|---|
| one cheaper model at a fixed score is enough | [`model-efficiency`](model-efficiency.md) |
| the sizes should be students of a teacher | add [`model-distillation`](model-distillation.md) to this one |

Can be combined with [`model-distillation`](model-distillation.md): `run.skill: [model-size-frontier, model-distillation]`.

## Skill file

[`evoloop/skills/model-size-frontier/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/model-size-frontier/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/model-size-frontier/skill.yaml))

```yaml
name: model-size-frontier
title: A family of models across sizes
summary: Find the best model at each size (or speed), from very small to large, so that the result is a whole trade-off curve to choose from and not one winner.
domain: model
objective: the best model at every size or speed across a broad range
tags: [pareto, frontier, trade-off, size, speed, family, scaling, coverage]
version: 1
authors: [evoloop]
when: >
  You need models for several budgets (a phone, a server, a screen of millions of inputs), or want to know what
  accuracy each size buys before choosing. For one cheaper model at a fixed score use model-efficiency.
settings:
  strategy:
    mechanism: archive
    descriptors: [size]
  schedule:
    novelty: 0.6
    phases: [{until: 0.5, new: 0.5, cross: 0.15, local: 0.35}, {until: 1.0, new: 0.2, cross: 0.25, local: 0.55}]
  report:
    columns: [speed]
guidance:
  all: |
    The result of this search is a set of models, one for each band of size, each the best found in its band. A
    design is a success if it is the best in its band, even when a larger design scores higher. The bands are
    steps of about fourfold in parameter count.
  writer: |
    `thin_cells`, when present, lists the size bands with the fewest designs: aim a new design at one of them and
    say in `predicted_effect` what size you expect it to have.
    Ways to move a design to another band without starting again:
    - scale it as a whole: width, depth and resolution together, in proportion, travel further than any one alone;
    - at the small end, change the kind of layer (separable or grouped convolutions, shared weights, a smaller
      head) before shrinking widths until nothing works;
    - at the large end, add capacity where the errors say it is missing, not evenly.
    What is best at one size is often not best at another: do not assume the largest design's shape, shrunk, is
    the best small one. A local move should stay in its parent's band; say so if you mean to leave it.
  analyst: |
    Describe the curve: where a fourfold increase in size still buys score and where it has stopped. Say which
    bands are well covered and which hold only one or two designs. Lessons are most useful in the form "at this
    size, X matters; above it, X does not".
  strategist: |
    Order new designs for bands that are empty or thin. When every band has several designs, shift toward local
    moves and crossovers between neighbouring bands.
diagnose:
  - see: "a band holds no design, or only one"
    do: "aim new designs at it: scale the nearest good design up or down as a whole"
  - see: "a larger band's best design scores no better than the band below it"
    do: "the larger designs are wasting capacity: move the smaller band's best design up by scaling it, and compare"
  - see: "the smallest band's designs all fail or score near chance"
    do: "that size is below what this approach can do: change the kind of layer, or accept the band above as the floor"
  - see: "the curve is flat across the top bands"
    do: "the data or the recipe is the limit, not size: stop adding large designs and spend the budget lower down"
stages:
  early: "Put at least two designs in every band, by scaling a few good shapes up and down."
  late: "Improve the best design in each band with local moves, and cross neighbours."
needs:
  adapter:
    - "report `parameters` in result.json for every design; the bands are made from it"
    - "to band by speed instead, report `inference_speed.examples_per_s` and set strategy.descriptors to the name of that metric under diagnostics"
    - "set `limits` for the smallest and largest size worth having, so that designs outside the range are not trained"
  figures: [parameters]
  references: []
combines: [model-distillation]
conflicts: [settings-tuning, model-efficiency]
goal: Find the best model at several sizes
start:
  run_type: survey
  evaluations: 200
  brief:
    limits: {parameters: {min: 50000, max: 50000000}}
why: >
  The deliverable is a curve, not a point: the best design in each band of size. An archive keeps the best of
  each band, new designs are aimed at bands that are empty, and a design is a success when it leads its band
  even if a larger one scores higher. This needs more evaluations than a search for one model.
reading: >
  Read the population table band by band: each row is the best design of one size band. Plot score against size
  to see where a fourfold increase stops paying. Bands with one or two designs are not yet explored; treat their
  best as provisional.
instead:
  - if: one cheaper model at a fixed score is enough
    use: model-efficiency
  - if: the sizes should be students of a teacher
    use: "model-distillation, model-size-frontier"
```
