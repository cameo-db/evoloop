# Status and limits

evoloop is at version 0.2. This page says what has been run and what has not, so that nobody takes a
feature for more than it is.

## Version 0.1.0

The previous version, 0.1.0, ran seven searches with `claude-opus-5-5` on real training tasks in
regulatory genomics. All seven are in [CAMEO](https://cameo-db.github.io/#/database) with every model,
training recipe and run: 1,450 training runs of 1,227 models, across six benchmarks.

| Study | Benchmark | Runs | Models |
|---|---|---|---|
| [Gosai MPRA architecture search](https://cameo-db.github.io/#/s/study-search-opus2) | Gosai MPRA activity | 303 | 227 |
| [K562 PRO-cap architecture search](https://cameo-db.github.io/#/s/study-procap_k562-run2) | K562 PRO-cap profiles | 253 | 200 |
| [PARM K562 promoter MPRA architecture search](https://cameo-db.github.io/#/s/study-parm_k562-run2) | PARM promoter MPRA, K562 | 242 | 207 |
| [K562 ATAC-seq Y-net architecture search](https://cameo-db.github.io/#/s/study-capy_search-run3) | K562 ATAC-seq profiles | 215 | 229 |
| [DeepSTARR architecture search](https://cameo-db.github.io/#/s/study-deepstarr_search-opus) | DeepSTARR enhancer activity | 201 | 147 |
| [Bolero cell-state conditioning search](https://cameo-db.github.io/#/s/study-bolero-conditioning-round1) | HumanBrainDev cell-state accessibility | 186 | 170 |
| [K562 ATAC-seq open architecture search](https://cameo-db.github.io/#/s/study-capy_open-open1) | K562 ATAC-seq profiles | 50 | 47 |

These show the approach running end to end with a real LLM at the scale of hundreds of training runs.
They are not a test of the code in this repository. Version 0.2 is a rewrite, and the rest of this page
is about version 0.2.

## Tested

- A search with a real LLM on a real GPU training task, in progress as of 2026-11-22. `claude-opus-5-5`,
  through the Claude Code backend, writes the designs and the lessons, and each design trains as its own
  GPU job on Slurm. 14 designs have been trained and scored so far. The search has not finished, so it
  says nothing yet about how well version 0.2 searches.
- Over 200 tests on the two built-in examples with stub agents (no model call, no GPU). They cover the brief,
  every strategy, islands, the crossover kinds, steering during a run, changing the strategy, harness
  and search space midway, changing the run length, stopping and continuing, the study file, and one
  regression test for each defect that two independent reviews of the code reproduced.
- A run on a real Slurm cluster of the example: seven CPU jobs, each its own job.
- The controller job script on a real Slurm cluster: with a four-minute limit it stopped cleanly at the
  signal, put itself back in the queue twice, and went on with the search each time it restarted.

## Not tested

- A finished search with a real LLM. One is in progress.
- The strategist with a real agent. Its bounds, its record and the commands to approve or decline are
  tested with a stub that follows a fixed rule. Whether a real model decides well is not known.
- The `anthropic_api` backend. The search in progress uses `claude_code`.
- The spend governor against real prices. It is tested with a backend that charges a fixed sum per call.
- The cost estimate against a real bill. It counts calls from the settings and sizes them from the code; it
  has not been compared with what a real run cost.
- Whether any strategy searches better than another. The strategies are known to work as code.
- The skills. Thirteen templates load, merge and reach the agents; whether their guidance makes a real
  model search better is not known. The settings estimator beats random draws on a made-up function; it has
  not tuned a real model.
- Several models writing, find-and-replace edits, approaches and weight inheritance with a real agent or a
  real evaluator. The stub returns whole-block edits and one fixed approach; the example evaluator ignores the
  parent's checkpoint. Whether a real model writes edits that apply, or approaches worth keeping, is not known.
- The ladder, the trade-off front, behaviour groups and island resets on a real task. They are tested on
  the example and on made-up results; whether early progress predicts the final score on your task is not known.
- On Slurm: a preempted job being requeued, the QoS list, a time limit being hit.
- Continuing a run from a checkpoint after the run length is raised.
- Importing a study file downloaded from CAMEO. The import is tested on study files evoloop wrote and on a
  hand-made file from another project.
- Detecting a site file on a real cluster. Detection is tested on made-up scheduler output.

## Known limits

- No limit on what an agent is sent. With large blocks, several parents and a leaderboard, the
  context, and its cost, can grow large.
- The results are re-read every turn. Fine at hundreds of runs; slow at thousands.
- Working copies and checkpoints are never removed, and the whole of `base/` is copied per run.
- A job that hits its time limit is started again, up to `compute.infrastructure_retries` times,
  from its checkpoint if the evaluator keeps one and from scratch otherwise.
- A design stopped part way keeps its part-way score as a provisional row: shown, marked with how far it ran,
  not ranked with full-length fits and never a parent.
- `objective.constraints`, `space.forbidden` and `space.must_keep` are text for the agents, not
  rules; only `space.forbidden_terms`, `limits` and the open blocks are enforced by code.
- A proposal's distance is measured on the code; behaviour is known only after training, and only if the
  evaluator reports `signature`.
- One noise figure, given by you. The loop does not measure it.

## Not implemented

Things people running searches have needed that are not here yet:

- A rule that stops a run falling clearly behind the baseline's own curve. The screen and the ladder compare
  designs with each other, not with the baseline.
- Moving a waiting job to a better QoS when room appears there; jobs are placed once, at submission.
- Scoring the test set in separate, low-priority jobs. The evaluator reports test results itself.
- Refitting the top N designs at the end (on the full data, or on more seeds) and ensembling them. A change of
  `data.fraction` refits the leader of each lineage, which is close but not the same.
- Choosing the GPU type per design in advance. A design that proves too large for its GPU can be moved to
  `compute.larger_gpu_type` (the evaluator exits 76).
- A proxy tier on a different, cheaper task (a smaller dataset or model), with promotion to the real one. The
  ladder stops weak designs early within the real task; it does not swap the task.
- Repair of a design that crashed.
- Running the CAMEO kit's check on the study file.
