# Make a data pipeline faster or cheaper

Skill `data-pipeline` · domain: pipeline · [the skill in full](../skill-library.md#data-pipeline)

Speed up a multi-step data pipeline (reading, transforming, joining, writing) or cut its memory and cost, with its output unchanged.

## Start here

Put this in `brief.yaml` (or give the same answers to `evoloop setup`), then read `evoloop plan` before you confirm.

```yaml
run:
  type: explore_then_exploit
  skill: data-pipeline
budget:
  evaluations: 80
objective:
  direction: minimize
```

The budget, and any limits or ranges, are placeholders: put in your own.

## Why this set-up

In a pipeline the cost is usually in moving data, so the writers are told to do less and move data fewer times before optimizing computation. The output is compared with a reference, and a design whose output differs is rejected.

The skill sets these for you (anything you set in the brief wins):

| Setting | Value |
|---|---|
| [`evaluation.screen_keep`](../fields.md#evaluation-screen_keep) | `1.0` |
| [`schedule.local_mix`](../fields.md#schedule-local_mix) | `{ablation: 0.1, edit: 0.7, settings: 0.2}` |
| [`schedule.novelty`](../fields.md#schedule-novelty) | `0.3` |

## What your evaluator must report

- run the pipeline on fixed sample data and compare its output with a stored reference (a checksum of sorted records, or row counts with value checks); write `valid: false` with the reason when it differs
- report the cost as the score with objective.direction minimize: wall time as a median of repeats, or a figure that combines time and memory if both matter
- report time per step and peak memory under diagnostics, so that the agents can see where the cost is
- use sample data large enough that input and output costs resemble the real run, and keep a second sample the search never sees under diagnostics.hidden
- Add a row to the leaderboard for the original pipeline, to compare against (`evoloop reference`).

[Write the evaluator](../evaluator.md) shows how to report these; [Evaluator interface](../project-contract.md) is the reference.

## Choose something else when

| If | Use |
|---|---|
| one function holds the cost | [`algorithm-runtime`](algorithm-runtime.md) |

It combines well with [`algorithm-runtime`](algorithm-runtime.md) (`run.skill: [data-pipeline, ...]`).

## Reading the result

Read the best design's cost against the reference row, and the time per step it reports: that shows where the cost went. Check how the gain grows with input size before relying on it at full scale.

Where to look: `evoloop leaderboard`, `evoloop show`, and the report ([Files of a run](../records.md)). To change course while it runs: [Watch and steer a run](../steering.md).

## What the agents are told

??? note "Every role"
    This search makes a pipeline cheaper to run without changing what it produces. The score is a measured cost
    on sample data; the output is compared with a reference, and a design whose output differs is rejected.

??? note "The writer"
    In a pipeline the time is usually in moving data, not computing on it. From the largest effect down:
    - do less: read only the columns, rows and files that are used; filter as early as possible; drop steps whose
      output nothing reads;
    - move data fewer times: fewer passes over the input, no intermediate files that are written and read once,
      streaming in place of loading whole files, a format that is read by column or by block in place of
      re-parsing text;
    - reorder: filters and cheap reductions before joins, sorts and expensive transforms; sort once;
    - process in batches or vectorised operations in place of row by row;
    - parallelise the steps that are independent, sized to the machine, after the above;
    - memory: process in chunks, avoid copies, use narrower types.
    Keep exactly: the rows and their order where order is part of the output, the treatment of missing and
    malformed records, numeric precision, and the output's format. Say in `hypothesis` which step holds the cost
    now. Do not assume properties of the sample data (its size, that it is sorted, that it has no missing values)
    that the real data may not have.

??? note "The analyst"
    Say which step holds the time and memory in the best designs, and how that has shifted. List the designs
    rejected for a changed output, with the step that changed it.

??? note "The strategist"
    When edits within steps stop gaining, order designs that restructure the pipeline: merging steps, reordering
    them, or changing the intermediate format.

| If the results show | Then |
|---|---|
| a design is rejected because its output differs | find the step that changed it (order, missing values, precision, duplicates) and keep that behaviour |
| run time is dominated by reading or writing | read less and fewer times, or change the format; faster computation will not show |
| adding parallel workers gives no gain, or a loss | the steps contend for disk or memory: reduce what is read first, then parallelise fewer, larger pieces |
| memory peaks at one step | process that step in chunks or streams, or reduce the data before it |
| a design is faster on the sample and its gain depends on the sample's size | say how the cost grows with input size; a gain that vanishes at full size is not one |

Early in the budget: Find which steps hold the cost, and try restructuring: fewer passes, earlier filters, another format.

Late in the budget: Tighten the remaining hot steps, then parallelise what is independent.

You can change any of this: the search gets its own copy of the skill in `skills/data-pipeline/skill.yaml` ([Skills](../skills.md)).
