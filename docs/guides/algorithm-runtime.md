# Make an algorithm faster

Skill `algorithm-runtime` · domain: algorithm · [the skill in full](../skill-library.md#algorithm-runtime)

Speed up a piece of code (or cut its memory) while its output stays correct. The score is a measured time; a design whose output is wrong is rejected, not scored.

## Start here

Put this in `brief.yaml` (or give the same answers to `evoloop setup`), then read `evoloop plan` before you confirm.

```yaml
run:
  type: explore_then_exploit
  skill: algorithm-runtime
budget:
  evaluations: 80
objective:
  direction: minimize
```

!!! note "A starting point"
    These settings are a reasoned starting point. They have not been measured against alternatives; see [Status and limits](../status.md). The numbers in the example (the budget, any limits or ranges) are placeholders for yours.

## Why this set-up

The score is a measured time and the output must not change, so the benchmark rejects any design whose output differs. Early stopping is off, because a timing is not a curve. The largest gains come from a different algorithm, so the first half of the budget explores.

The skill sets these for you (anything you set in the brief wins):

| Setting | Value |
|---|---|
| [`evaluation.screen_keep`](../fields.md) | `1.0` |
| [`schedule.local_mix`](../fields.md) | `{ablation: 0.15, edit: 0.75, settings: 0.1}` |
| [`schedule.novelty`](../fields.md) | `0.3` |

## What your evaluator must report

- compare every design's output with a stored reference output and write `valid: false` with `rejected: "output differs"` when it does not match (exactly, or within a stated tolerance)
- time the run several times on a quiet machine with a fixed number of threads, and report the median as the score with objective.direction minimize; set evaluation.noise from the spread of repeats
- keep a second set of inputs the search never sees, and report its timing under diagnostics.hidden
- report peak memory under diagnostics if it matters, and bound it with `limits`
- **A reference row on the leaderboard for:** the original code (`evoloop reference`).

How the adapter reports these: [The project's code](../project-contract.md).

## Choose something else when

| If | Use |
|---|---|
| the method's accuracy, not its speed, is the goal | [`bioinformatics-algorithm`](bioinformatics-algorithm.md) |
| the cost is spread over several steps of a pipeline | [`data-pipeline`](data-pipeline.md) |

It combines well with [`data-pipeline`](data-pipeline.md), [`bioinformatics-algorithm`](bioinformatics-algorithm.md) (`run.skill: [algorithm-runtime, ...]`).

## Reading the result

Read the best design's time against the reference row for the original code, and count the designs rejected for a wrong output. Then run the winner on the inputs the search never saw: a gain that does not hold there was fitted to the benchmark.

Where to look: `evoloop leaderboard`, `evoloop show`, and the report ([Records and the study file](../records.md)). To change course while it runs: [Steering a run](../steering.md).

## What the agents are told

??? note "Every role"
    This search makes code faster (or lighter) without changing what it computes. The score is a measured cost on
    a benchmark. Correctness is not negotiable: the benchmark compares each design's output with a reference, and
    a design that differs is rejected however fast it is.

??? note "The writer"
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

??? note "The analyst"
    Say where the time went in the designs that gained, and which kinds of change have stopped paying. Report
    every design rejected for a wrong output and what kind of change caused it.

??? note "The strategist"
    When local edits stop gaining, order new designs: a different algorithm usually beats further tuning of the
    current one.

| If the results show | Then |
|---|---|
| a design is rejected because its output differs from the reference | find which case differs and keep that case's behaviour; do not relax the check |
| a design is faster on small inputs and slower on large ones (or the reverse) | the complexity changed: decide which size matters from the task, and say which the benchmark weighs |
| timings of one design differ between repeats by as much as the gains | the measurement is the problem: gains below the noise floor are not gains |
| time fell and memory rose sharply | a cache or a table is paying for the speed: check it against the memory limit and say so |
| many small edits each gain a little, then nothing | the current algorithm is at its floor: change the algorithm or the data structure |

Early in the budget: Try different algorithms and data structures; a rough version shows whether the idea is in a better class.

Late in the budget: Tighten the best design: remove repeated work, then improve its layout and inner loops.

You can change any of this: the search gets its own copy of the skill in `skills/algorithm-runtime/skill.yaml` ([Skills](../skills.md)).
