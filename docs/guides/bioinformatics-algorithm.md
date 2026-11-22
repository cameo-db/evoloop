# Improve a bioinformatics method

Skill `bioinformatics-algorithm`. Improve a method that analyses biological data (an aligner, a caller, a peak finder, a quantifier, a scoring function) against a truth set, without breaking the conventions of the formats and coordinates it works in.

File: [`evoloop/skills/bioinformatics-algorithm/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/bioinformatics-algorithm/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/bioinformatics-algorithm/skill.yaml)). A search copies this file to `mysearch/skills/bioinformatics-algorithm/skill.yaml` and reads that copy, which you can edit.

## Use it

```yaml
run:
  skill: bioinformatics-algorithm
  type: explore_then_exploit
budget:
  evaluations: 100
```

Put these lines in `brief.yaml`. The budget and any limits or ranges are placeholders. <a href="../../which-search/?goal=bioinformatics-algorithm&run=explore_then_exploit#preview-a-search">Preview the resulting search</a>.

The method has a measurable right answer on some data (simulated, curated, or orthogonally validated) and the aim is to do better on it. If the method is right and only slow, use algorithm-runtime.

## What it sets

A skill's settings override the run type's and the autonomy level's. Settings in your brief override the skill's.

| Setting | Value |
|---|---|
| [`schedule.local_mix`](../fields.md#schedule-local_mix) | `{ablation: 0.15, edit: 0.6, settings: 0.25}` |
| [`schedule.novelty`](../fields.md#schedule-novelty) | `0.3` |

## What it tells the agents

This text is added to every call to the role named. It is the skill's file verbatim.

=== "Every role"

    This search improves a method for biological data, scored against a truth set. Two things make this kind of
    code different from other algorithms: small conventions carry large consequences (coordinates, strands,
    encodings), and a method tuned to one dataset often fails on the next organism, protocol or depth.

=== "Writer"

    Where such methods are usually improved:
    - the model of the data: the error or noise model, the background or null, how depth, bias and duplicates are
      handled, what is assumed independent;
    - the scoring and the thresholds: a calibrated score in place of a fixed cut-off, a local in place of a global
      background, a correction for multiple testing that matches the question;
    - ambiguous cases, where much of the error lives: multi-mapping reads, low-complexity and repeated sequence,
      region boundaries, low coverage, indels near other variants;
    - the order of the steps: filter before or after, merge before or after.
    What must not change unless the task says so: the coordinate convention (0- or 1-based, half-open or closed),
    strand handling and reverse complements, the treatment of unknown bases and missing values, sort order, and the
    output format down to its columns. State in `hypothesis` which kind of error (false positives or false
    negatives, and in which kind of case) the change is meant to reduce.
    Do not fit the benchmark: a threshold tuned to this one dataset is not an improvement of the method.

=== "Analyst"

    Report precision and recall separately, and by kind of case where the results give it (by coverage, by region
    type, by size of event). Say whether a gain holds on every dataset in the benchmark or on one.

=== "Strategist"

    If gains come only from threshold changes, the method itself has stopped improving: order structural edits or
    new designs.

The writer and the analyst are also given these rules:

| If the results show | Then |
|---|---|
| precision rose and recall fell by about as much (or the reverse) | a threshold moved, not the method: look for a change that separates true from false cases better |
| the gain is on one dataset of the benchmark and not the others | it is fitted to that dataset: keep only changes that hold across them |
| results are off by one position, or wrong on one strand only | a coordinate or strand convention was broken: restore it before judging anything else |
| errors concentrate in repeats, low-complexity sequence or low coverage | treat those cases explicitly (a separate model, a mask, a penalty) and say how |
| the output changes between two runs on the same input | the method is not deterministic: fix seeds, ordering and tie-breaks first |

And the writer is told, in the first half of the budget: "Find which kind of case holds most of the error, and try different ways of modelling it." In the second half: "Refine the best method on the hard cases, and confirm each gain on every dataset."

## What your scoring script must report

- score against a truth set with a standard comparison for the task, and report precision, recall and their combination under diagnostics; the score should be one number that does not reward trading one for the other at a single threshold
- use more than one dataset (another sample, depth or organism), and keep one the search never sees under diagnostics.hidden
- check the output's format and coordinates before scoring, and write `valid: false` with the reason when they are wrong
- report run time and peak memory under diagnostics, and bound them with `limits` if they matter
- A leaderboard row for the original method, added with `evoloop reference`. The report warns if it is missing.

[Write the evaluator](../evaluator.md) · [Evaluator interface](../project-contract.md)

## Reading the results

Read precision and recall separately, and by dataset. A gain made by trading one for the other is a moved threshold, not a better method. Confirm the winner on the dataset the search never saw.

## Why these settings

The method is scored against a truth set, and the writers are told what makes this kind of code different: coordinate, strand and format conventions that must not change, and gains that must hold across datasets and not on one.

## Related skills

| If | Use |
|---|---|
| the method is right and only slow | [`algorithm-runtime`](algorithm-runtime.md) |

Can be combined with [`algorithm-runtime`](algorithm-runtime.md): `run.skill: [bioinformatics-algorithm, algorithm-runtime]`.

## The file

[`evoloop/skills/bioinformatics-algorithm/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/bioinformatics-algorithm/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/bioinformatics-algorithm/skill.yaml))

```yaml
name: bioinformatics-algorithm
title: Improve a bioinformatics algorithm
summary: Improve a method that analyses biological data (an aligner, a caller, a peak finder, a quantifier, a scoring function) against a truth set, without breaking the conventions of the formats and coordinates it works in.
domain: bioinformatics
objective: better accuracy against a truth set, at an acceptable run time
tags: [bioinformatics, genomics, sequence, alignment, variant calling, peak calling, benchmark, truth set]
version: 1
authors: [evoloop]
when: >
  The method has a measurable right answer on some data (simulated, curated, or orthogonally validated) and the
  aim is to do better on it. If the method is right and only slow, use algorithm-runtime.
settings:
  schedule:
    novelty: 0.3
    local_mix: {edit: 0.6, settings: 0.25, ablation: 0.15}
guidance:
  all: |
    This search improves a method for biological data, scored against a truth set. Two things make this kind of
    code different from other algorithms: small conventions carry large consequences (coordinates, strands,
    encodings), and a method tuned to one dataset often fails on the next organism, protocol or depth.
  writer: |
    Where such methods are usually improved:
    - the model of the data: the error or noise model, the background or null, how depth, bias and duplicates are
      handled, what is assumed independent;
    - the scoring and the thresholds: a calibrated score in place of a fixed cut-off, a local in place of a global
      background, a correction for multiple testing that matches the question;
    - ambiguous cases, where much of the error lives: multi-mapping reads, low-complexity and repeated sequence,
      region boundaries, low coverage, indels near other variants;
    - the order of the steps: filter before or after, merge before or after.
    What must not change unless the task says so: the coordinate convention (0- or 1-based, half-open or closed),
    strand handling and reverse complements, the treatment of unknown bases and missing values, sort order, and the
    output format down to its columns. State in `hypothesis` which kind of error (false positives or false
    negatives, and in which kind of case) the change is meant to reduce.
    Do not fit the benchmark: a threshold tuned to this one dataset is not an improvement of the method.
  analyst: |
    Report precision and recall separately, and by kind of case where the results give it (by coverage, by region
    type, by size of event). Say whether a gain holds on every dataset in the benchmark or on one.
  strategist: |
    If gains come only from threshold changes, the method itself has stopped improving: order structural edits or
    new designs.
diagnose:
  - see: "precision rose and recall fell by about as much (or the reverse)"
    do: "a threshold moved, not the method: look for a change that separates true from false cases better"
  - see: "the gain is on one dataset of the benchmark and not the others"
    do: "it is fitted to that dataset: keep only changes that hold across them"
  - see: "results are off by one position, or wrong on one strand only"
    do: "a coordinate or strand convention was broken: restore it before judging anything else"
  - see: "errors concentrate in repeats, low-complexity sequence or low coverage"
    do: "treat those cases explicitly (a separate model, a mask, a penalty) and say how"
  - see: "the output changes between two runs on the same input"
    do: "the method is not deterministic: fix seeds, ordering and tie-breaks first"
stages:
  early: "Find which kind of case holds most of the error, and try different ways of modelling it."
  late: "Refine the best method on the hard cases, and confirm each gain on every dataset."
needs:
  adapter:
    - "score against a truth set with a standard comparison for the task, and report precision, recall and their combination under diagnostics; the score should be one number that does not reward trading one for the other at a single threshold"
    - "use more than one dataset (another sample, depth or organism), and keep one the search never sees under diagnostics.hidden"
    - "check the output's format and coordinates before scoring, and write `valid: false` with the reason when they are wrong"
    - "report run time and peak memory under diagnostics, and bound them with `limits` if they matter"
  figures: []
  references: ["the original method"]
combines: [algorithm-runtime]
conflicts: [settings-tuning]
goal: Improve a bioinformatics method
start:
  run_type: explore_then_exploit
  evaluations: 100
why: >
  The method is scored against a truth set, and the writers are told what makes this kind of code different:
  coordinate, strand and format conventions that must not change, and gains that must hold across datasets and
  not on one.
reading: >
  Read precision and recall separately, and by dataset. A gain made by trading one for the other is a moved
  threshold, not a better method. Confirm the winner on the dataset the search never saw.
instead:
  - if: the method is right and only slow
    use: algorithm-runtime
```
