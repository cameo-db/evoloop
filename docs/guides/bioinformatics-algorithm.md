# Improve a bioinformatics method

Improve a method that analyses biological data (an aligner, a caller, a peak finder, a quantifier, a scoring function) against a truth set, without breaking the conventions of the formats and coordinates it works in.

## What a good result looks like

Read precision and recall separately, and by dataset. A gain made by trading one for the other is a moved threshold, not a better method. Confirm the winner on the dataset the search never saw.

## Start here

```yaml
run:
  type: explore_then_exploit
  skill: bioinformatics-algorithm
budget:
  evaluations: 100
```

These lines go in `brief.yaml`. The budget, and any limits or ranges, are placeholders for your own. <a href="../../which-search/?goal=bioinformatics-algorithm&run=explore_then_exploit#preview-your-search">Preview this search</a> to see what it will do, or [set up this search](../setting-up.md) on your project. The goal is the skill `bioinformatics-algorithm`, shown in full in the [skill library](../skill-library.md#bioinformatics-algorithm).

## Why this set-up

The method is scored against a truth set, and the writers are told what makes this kind of code different: coordinate, strand and format conventions that must not change, and gains that must hold across datasets and not on one.

The skill sets these for you (anything you set in the brief wins):

| Setting | Value |
|---|---|
| [`schedule.local_mix`](../fields.md#schedule-local_mix) | `{ablation: 0.15, edit: 0.6, settings: 0.25}` |
| [`schedule.novelty`](../fields.md#schedule-novelty) | `0.3` |

## What your evaluator must report

- score against a truth set with a standard comparison for the task, and report precision, recall and their combination under diagnostics; the score should be one number that does not reward trading one for the other at a single threshold
- use more than one dataset (another sample, depth or organism), and keep one the search never sees under diagnostics.hidden
- check the output's format and coordinates before scoring, and write `valid: false` with the reason when they are wrong
- report run time and peak memory under diagnostics, and bound them with `limits` if they matter
- Add a row to the leaderboard for the original method, to compare against (`evoloop reference`).

[Write the evaluator](../evaluator.md) shows how to report these; [Evaluator interface](../project-contract.md) is the reference.

## Choose something else when

| If | Use |
|---|---|
| the method is right and only slow | [`algorithm-runtime`](algorithm-runtime.md) |

It combines well with [`algorithm-runtime`](algorithm-runtime.md) (`run.skill: [bioinformatics-algorithm, ...]`).

## Where to look

`evoloop leaderboard` for the ranking, `evoloop show` for one design, and the report for everything ([Files of a run](../records.md)). To change course while it runs: [Watch and steer a run](../steering.md).

## What the agents are told

??? note "Every role"
    This search improves a method for biological data, scored against a truth set. Two things make this kind of
    code different from other algorithms: small conventions carry large consequences (coordinates, strands,
    encodings), and a method tuned to one dataset often fails on the next organism, protocol or depth.

??? note "The writer"
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

??? note "The analyst"
    Report precision and recall separately, and by kind of case where the results give it (by coverage, by region
    type, by size of event). Say whether a gain holds on every dataset in the benchmark or on one.

??? note "The strategist"
    If gains come only from threshold changes, the method itself has stopped improving: order structural edits or
    new designs.

| If the results show | Then |
|---|---|
| precision rose and recall fell by about as much (or the reverse) | a threshold moved, not the method: look for a change that separates true from false cases better |
| the gain is on one dataset of the benchmark and not the others | it is fitted to that dataset: keep only changes that hold across them |
| results are off by one position, or wrong on one strand only | a coordinate or strand convention was broken: restore it before judging anything else |
| errors concentrate in repeats, low-complexity sequence or low coverage | treat those cases explicitly (a separate model, a mask, a penalty) and say how |
| the output changes between two runs on the same input | the method is not deterministic: fix seeds, ordering and tie-breaks first |

Early in the budget: Find which kind of case holds most of the error, and try different ways of modelling it.

Late in the budget: Refine the best method on the hard cases, and confirm each gain on every dataset.

You can change any of this: the search gets its own copy of the skill in `skills/bioinformatics-algorithm/skill.yaml` ([Skills](../skills.md)).
