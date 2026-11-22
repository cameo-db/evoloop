# Make an algorithm faster

Skill `algorithm-runtime`. Speed up a piece of code (or cut its memory) while its output stays correct. The score is a measured time; a design whose output is wrong is rejected, not scored.

File: [`evoloop/skills/algorithm-runtime/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/algorithm-runtime/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/algorithm-runtime/skill.yaml)). A search copies this file to `mysearch/skills/algorithm-runtime/skill.yaml` and reads that copy, which you can edit.

## Use it

```yaml
run:
  skill: algorithm-runtime
  type: explore_then_exploit
budget:
  evaluations: 80
objective:
  direction: minimize
```

Put these lines in `brief.yaml`. The budget and any limits or ranges are placeholders. <a href="../../which-search/?goal=algorithm-runtime&run=explore_then_exploit#preview-a-search">Preview the resulting search</a>.

The code is correct and too slow or too hungry. The search needs a benchmark that checks the output and times the run. Not for improving what the algorithm computes (see bioinformatics-algorithm for accuracy against a truth set).

## What it sets

A skill's settings override the run type's and the autonomy level's. Settings in your brief override the skill's.

| Setting | Value |
|---|---|
| [`evaluation.screen_keep`](../fields.md#evaluation-screen_keep) | `1.0` |
| [`schedule.local_mix`](../fields.md#schedule-local_mix) | `{ablation: 0.15, edit: 0.75, settings: 0.1}` |
| [`schedule.novelty`](../fields.md#schedule-novelty) | `0.3` |

## What it tells the agents

This text is added to every call to the role named. It is the skill's file verbatim.

=== "Every role"

    This search makes code faster (or lighter) without changing what it computes. The score is a measured cost on
    a benchmark. Correctness is not negotiable: the benchmark compares each design's output with a reference, and
    a design that differs is rejected however fast it is.

=== "Writer"

    Work from the largest effect down:
    - the algorithm: a better complexity class, an index or a hash in place of a scan, sorting once in place of
      searching many times, pruning work that cannot change the answer, stopping early;
    - repeated work: caching, hoisting out of loops, incremental updates in place of recomputation;
    - the data's layout: contiguous arrays in place of objects, fewer allocations, fewer copies, access in order;
    - the machine: vectorised operations, batches, a compiled inner loop;
    - only then constant factors.
    Do not make the code faster on the benchmark's inputs by recognising them: sizes, seeds and particular values
    must not be special-cased, and a held-out benchmark will show it. Keep behaviour on edge cases (empty input,
    one element, duplicates, extreme values) exactly as it was. Say in `hypothesis` where the time goes now and why
    your change removes it.

=== "Analyst"

    Say where the time went in the designs that gained, and which kinds of change have stopped paying. Report
    every design rejected for a wrong output and what kind of change caused it.

=== "Strategist"

    When local edits stop gaining, order new designs: a different algorithm usually beats further tuning of the
    current one.

The writer and the analyst are also given these rules:

| If the results show | Then |
|---|---|
| a design is rejected because its output differs from the reference | find which case differs and keep that case's behaviour; do not relax the check |
| a design is faster on small inputs and slower on large ones (or the reverse) | the complexity changed: decide which size matters from the task, and say which the benchmark weighs |
| timings of one design differ between repeats by as much as the gains | the measurement is the problem: gains below the noise floor are not gains |
| time fell and memory rose sharply | a cache or a table is paying for the speed: check it against the memory limit and say so |
| many small edits each gain a little, then nothing | the current algorithm is at its floor: change the algorithm or the data structure |

And the writer is told, in the first half of the budget: "Try different algorithms and data structures; a rough version shows whether the idea is in a better class." In the second half: "Tighten the best design: remove repeated work, then improve its layout and inner loops."

## What your scoring script must report

- compare every design's output with a stored reference output and write `valid: false` with `rejected: "output differs"` when it does not match (exactly, or within a stated tolerance)
- time the run several times on a quiet machine with a fixed number of threads, and report the median as the score with objective.direction minimize; set evaluation.noise from the spread of repeats
- keep a second set of inputs the search never sees, and report its timing under diagnostics.hidden
- report peak memory under diagnostics if it matters, and bound it with `limits`
- A leaderboard row for the original code, added with `evoloop reference`. The report warns if it is missing.

[Write the evaluator](../evaluator.md) · [Evaluator interface](../project-contract.md)

## Reading the results

Read the best design's time against the reference row for the original code, and count the designs rejected for a wrong output. Then run the winner on the inputs the search never saw: a gain that does not hold there was fitted to the benchmark.

## Why these settings

The score is a measured time and the output must not change, so the benchmark rejects any design whose output differs. Early stopping is off, because a timing is not a curve. The largest gains come from a different algorithm, so the first half of the budget explores.

## Related skills

| If | Use |
|---|---|
| the method's accuracy, not its speed, is the goal | [`bioinformatics-algorithm`](bioinformatics-algorithm.md) |
| the cost is spread over several steps of a pipeline | [`data-pipeline`](data-pipeline.md) |

Can be combined with [`data-pipeline`](data-pipeline.md), [`bioinformatics-algorithm`](bioinformatics-algorithm.md): `run.skill: [algorithm-runtime, data-pipeline]`.

## The file

[`evoloop/skills/algorithm-runtime/skill.yaml`](https://github.com/cameo-db/evoloop/blob/main/evoloop/skills/algorithm-runtime/skill.yaml) ([raw](https://raw.githubusercontent.com/cameo-db/evoloop/main/evoloop/skills/algorithm-runtime/skill.yaml))

```yaml
name: algorithm-runtime
title: Make an algorithm faster at the same output
summary: Speed up a piece of code (or cut its memory) while its output stays correct. The score is a measured time; a design whose output is wrong is rejected, not scored.
domain: algorithm
objective: the same results in less time or memory
tags: [speed, runtime, performance, optimization, complexity, memory, benchmark]
version: 1
authors: [evoloop]
when: >
  The code is correct and too slow or too hungry. The search needs a benchmark that checks the output and times
  the run. Not for improving what the algorithm computes (see bioinformatics-algorithm for accuracy against a
  truth set).
settings:
  evaluation:
    screen_keep: 1.0
  schedule:
    novelty: 0.3
    local_mix: {edit: 0.75, settings: 0.1, ablation: 0.15}
guidance:
  all: |
    This search makes code faster (or lighter) without changing what it computes. The score is a measured cost on
    a benchmark. Correctness is not negotiable: the benchmark compares each design's output with a reference, and
    a design that differs is rejected however fast it is.
  writer: |
    Work from the largest effect down:
    - the algorithm: a better complexity class, an index or a hash in place of a scan, sorting once in place of
      searching many times, pruning work that cannot change the answer, stopping early;
    - repeated work: caching, hoisting out of loops, incremental updates in place of recomputation;
    - the data's layout: contiguous arrays in place of objects, fewer allocations, fewer copies, access in order;
    - the machine: vectorised operations, batches, a compiled inner loop;
    - only then constant factors.
    Do not make the code faster on the benchmark's inputs by recognising them: sizes, seeds and particular values
    must not be special-cased, and a held-out benchmark will show it. Keep behaviour on edge cases (empty input,
    one element, duplicates, extreme values) exactly as it was. Say in `hypothesis` where the time goes now and why
    your change removes it.
  analyst: |
    Say where the time went in the designs that gained, and which kinds of change have stopped paying. Report
    every design rejected for a wrong output and what kind of change caused it.
  strategist: |
    When local edits stop gaining, order new designs: a different algorithm usually beats further tuning of the
    current one.
diagnose:
  - see: "a design is rejected because its output differs from the reference"
    do: "find which case differs and keep that case's behaviour; do not relax the check"
  - see: "a design is faster on small inputs and slower on large ones (or the reverse)"
    do: "the complexity changed: decide which size matters from the task, and say which the benchmark weighs"
  - see: "timings of one design differ between repeats by as much as the gains"
    do: "the measurement is the problem: gains below the noise floor are not gains"
  - see: "time fell and memory rose sharply"
    do: "a cache or a table is paying for the speed: check it against the memory limit and say so"
  - see: "many small edits each gain a little, then nothing"
    do: "the current algorithm is at its floor: change the algorithm or the data structure"
stages:
  early: "Try different algorithms and data structures; a rough version shows whether the idea is in a better class."
  late: "Tighten the best design: remove repeated work, then improve its layout and inner loops."
needs:
  adapter:
    - "compare every design's output with a stored reference output and write `valid: false` with `rejected: \"output differs\"` when it does not match (exactly, or within a stated tolerance)"
    - "time the run several times on a quiet machine with a fixed number of threads, and report the median as the score with objective.direction minimize; set evaluation.noise from the spread of repeats"
    - "keep a second set of inputs the search never sees, and report its timing under diagnostics.hidden"
    - "report peak memory under diagnostics if it matters, and bound it with `limits`"
  figures: []
  references: ["the original code"]
combines: [data-pipeline, bioinformatics-algorithm]
conflicts: [settings-tuning]
goal: Make an algorithm faster
start:
  run_type: explore_then_exploit
  evaluations: 80
  brief:
    objective: {direction: minimize}
why: >
  The score is a measured time and the output must not change, so the benchmark rejects any design whose output
  differs. Early stopping is off, because a timing is not a curve. The largest gains come from a different
  algorithm, so the first half of the budget explores.
reading: >
  Read the best design's time against the reference row for the original code, and count the designs rejected
  for a wrong output. Then run the winner on the inputs the search never saw: a gain that does not hold there
  was fitted to the benchmark.
instead:
  - if: the method's accuracy, not its speed, is the goal
    use: bioinformatics-algorithm
  - if: the cost is spread over several steps of a pipeline
    use: data-pipeline
```
