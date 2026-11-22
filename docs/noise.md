# Noise floor

Two training runs of the same design give different scores. The noise floor, `evaluation.noise`, is
the difference in score that evoloop treats as no difference. You set it once, when you set up a
search. There are two reasonable ways to choose it: set a small value, or estimate it from a few runs.
An agent setting up a search suggests a value and says why.

## Uses

| Decision | Role of the noise floor |
|---|---|
| Has a lineage gained? | A design raises its lineage's best only by beating it by more than the floor. Six local moves in a row without that retire the lineage. |
| Which design is the parent? | Designs within the floor of their lineage's best are tied, and the parent is drawn among them. |
| Is a new design stopped early? | Only if it is behind at the checkpoint by more than the floor. |
| Is a design on the Pareto front? | A difference in score below the floor does not push a design off the front. |

## Purpose

The floor protects a lineage from one lucky score. A design is usually trained once. If a run comes
out high by chance and is taken at face value, it becomes the bar for its lineage and its only parent.
Its descendants are then compared with a score the design itself would not repeat. They fail to beat
it, the lineage counts six moves without a gain, and it is retired. A lineage that could have improved
never takes off.

With a floor, a design close to the top is tied with the top and can be the parent, and the bar moves
only when a later design clears it by a margin.

The floor does not decide whether an improvement is real. A lineage whose designs keep scoring higher
has improved, even though each design was trained once: several independent runs that point the same
way are evidence in themselves. Small gains also add up. Steps that each gain less than the floor
count as a gain as soon as together they exceed it.

## Small value

If you do not know how much your score varies, set a small value, for example 0.001 for a score you
would report to three decimals:

```
evoloop brief mysearch --answer evaluation.noise=0.001
```

This suits a search in which the gains you expect are large next to the variation between runs. Its
risk is the one described above. If lineages tend to stall straight after a single high score, raise
the value. The leading design is also retrained on a new seed at intervals, and its score becomes the
mean of its runs, which corrects a lucky leader whatever the floor is.
[Comparing scores](comparable.md#leader-re-checks)

## Estimate

To estimate the variation, train your baseline a few times with different seeds, at the training
length the search will use.

```
mkdir noise && cp -r mysearch/base/. noise/ && cp -r mysearch/adapter noise/
cd noise
for seed in 0 1 2 3 4; do
    EVO_OUT_DIR=out$seed EVO_CHECKPOINT_DIR=checkpoints$seed EVO_SEED=$seed EVO_ALLOWANCE=30 python adapter/run.py
done
grep -ho '"score": [0-9.e-]*' out*/result.json
```

This runs your evaluator the way a search would, in a copy of the code. Suppose the five scores are
0.912, 0.907, 0.915, 0.909 and 0.911. Their standard deviation is about 0.003:

```
evoloop brief mysearch --answer evaluation.noise=0.003
```

Two runs give a rough figure and five a better one. Shorter training runs are usually noisier.

## Large values

A floor that is too large fails more slowly. More designs count as tied, so the parent is drawn from a
wider group. A lineage that improves in small steps registers a gain only when the steps add up, and
one that gains less than about a sixth of the floor per move is retired.

If the variation between runs is larger than the gains you are looking for, no value of the floor
fixes that. Train longer, evaluate on more data, or average several seeds inside your evaluator and
report the mean.

## Seeds

If repeated runs give identical scores, either the evaluator is deterministic or the seed is not
reaching your training code. Check that the script reads `EVO_SEED` and uses it for the weight
initialisation and the data order. With a deterministic evaluator, set a very small floor.
