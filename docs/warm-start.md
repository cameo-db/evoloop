# Start from earlier designs

A search does not have to start from your baseline alone. It can take designs from an earlier search of
your own, or from a study file in the [CAMEO](https://cameo-db.github.io) database, which holds models,
their code and their scores from other people's searches. The exchange goes both ways: every evoloop
search writes a `study.json` in the CAMEO format, so what you find can be [deposited](study.md) and used
to start someone else's search.

## What happens to an imported design

It depends on whether its code can run in your project.

| The design comes from | What evoloop does |
|---|---|
| the same project: the same marked blocks, on the same data or on new data | Trains it here as a design of this search. Its old score is kept only as a note, because the earlier search may have trained differently. Later designs can build on it. |
| another project or dataset: its code does not have your marked blocks | Keeps it as an idea. Writers of new designs are shown its code, its score there, the data it was scored on, and that study's findings, and adapt what suits your problem into your blocks. Nothing is trained until a writer produces a design that passes the checks. |

Scores from another study are never compared with scores in yours.

## From a study file

Download a study's JSON from CAMEO, or use the `study.json` of any evoloop search. A link works in
place of a path.

```
evoloop import mysearch --name r1 --from-study downloads/study.json --top 5 --by "Your Name"
evoloop import mysearch --name r1 --from-study downloads/study.json --designs M12 M40 --by "Your Name"
evoloop import mysearch --name r1 --from-study downloads/study.json --top 5 --as-ideas --by "Your Name"
```

`--top N` takes the N best models of the study by its own metric. `--as-ideas` trains none of them and
shows them all to the writers. The command reports which were queued for training and which were kept
as ideas, and the ledger records both.

## From an earlier run of your own

```
evoloop import mysearch --name r2 --from-run mysearch/runs/r1 --top 5 --by "Your Name"
```

The designs are trained again in the new run. Use this to continue from a finished search with a
different budget, strategy or data fraction.

## Starting from trained weights

Importing brings in a design's code, and it is trained from the start. To have each new design begin
from its parent's trained weights instead, set `evaluation.inherit_weights: true`; your evaluator then
receives the parent's checkpoint folder as `EVO_PARENT_CHECKPOINT_DIR`.
[Evaluator interface](project-contract.md).

## Limits

- An import is a request to a run, so the run must exist: start it, then import. Imported designs are
  trained ahead of the schedule's own.
- A study's code is used as it is written in the file. Read what you import, as you would any code you
  did not write.
- Reading a study file has been tested on files evoloop wrote and on a hand-made file from another
  project. It has not been tested on files downloaded from the CAMEO site.
