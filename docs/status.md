# Status and limits

Version 0.2. This page says what has been run and what has not, so that nobody takes a feature for
more than it is.

## What has been run

- **Over 150 tests** on the built-in example with stub agents (no model call, no GPU). They cover the brief,
  every strategy, islands, the crossover kinds, steering during a run, changing the strategy, harness
  and search space midway, changing the run length, stopping and continuing, the study file, and one
  regression test for each defect that two independent reviews of the code reproduced.
- **A run on a real Slurm cluster** of the example: seven CPU jobs, each its own job.
- **The controller job script on a real Slurm cluster**: with a four-minute limit it stopped cleanly at the
  signal, put itself back in the queue twice, and went on with the search each time it restarted.

## What has not been run

- **The strategist with a real agent.** Its bounds, its record and the commands to approve or decline are
  tested with a stub that follows a fixed rule. Whether a real model decides well is not known.
- **The spend governor against real prices.** It is tested with a backend that charges a fixed sum per call.
- **The cost estimate against a real bill.** It counts calls from the settings and sizes them from the code; it
  has not been compared with what a real run cost.
- **A real agent.** The prompts have not been read by a model, and the `anthropic_api` and
  `claude_code` backends have not been called from this version.
- **A real training task.** Nothing has been trained on a GPU through this version.
- **Whether any strategy searches better than another.** The strategies are known to work as code.
- **The ladder, the trade-off front, behaviour groups and island resets on a real task.** They are tested on
  the example and on made-up results; whether early progress predicts the final score on your task is not known.
- On Slurm: GPU jobs, a preempted job being requeued, the QoS list, a time limit being hit.
- Continuing a run from a checkpoint after the run length is raised.

## Known limits

- **No limit on what an agent is sent.** With large blocks, several parents and a leaderboard, the
  context, and its cost, can grow large.
- **The results are re-read every turn.** Fine at hundreds of runs; slow at thousands.
- **Working copies and checkpoints are never removed**, and the whole of `base/` is copied per run.
- **A job that hits its time limit is started again**, up to `compute.infrastructure_retries` times,
  from its checkpoint if the adapter keeps one and from scratch otherwise.
- **A design stopped at the screen keeps its part-way score** on the leaderboard beside full-length ones.
- **`objective.constraints`, `space.forbidden` and `space.must_keep` are text for the agents**, not
  rules; only `space.forbidden_terms` and the open blocks are enforced by code.
- **A proposal's distance is measured on the code**; behaviour is known only after training, and only if the
  adapter reports `signature`.
- **One noise figure, given by you.** The loop does not measure it.

## Not built

Things people running searches have needed that are not here yet:

- A rule that stops a run falling clearly behind the baseline's own curve. Only new designs are screened, once.
- Moving a waiting job to a better QoS when room appears there; jobs are placed once, at submission.
- Scoring the test set in separate, low-priority jobs. The adapter reports test results itself.
- Refitting the top N designs at the end (on the full data, or on more seeds) and ensembling them. A change of
  `data.fraction` refits the leader of each lineage, which is close but not the same.
- Choosing the GPU type per design.

- A proxy tier on a different, cheaper task (a smaller dataset or model), with promotion to the real one. The
  ladder stops weak designs early within the real task; it does not swap the task.
- Weight inheritance from a parent.
- Repair of a design that crashed.
- A file of a cluster's own rules.
- Running the CAMEO kit's check on the study file.
