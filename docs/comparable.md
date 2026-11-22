# When two scores can be compared

Train the same model twice with different seeds and the scores differ. A search that ignores this
spends its budget chasing luck. Three mechanisms deal with it.

## The noise floor

When you set up a search you say how much the score varies between two runs of the same design
(`evaluation.noise`; [how to measure it](noise.md)). Suppose it is 0.005.

From then on a difference smaller than 0.005 counts as no difference. A design at 0.912 does not beat
its parent at 0.910. Two designs within 0.005 of each other are tied when a parent is chosen. A family
that goes six local moves without gaining more than 0.005 is retired. A lesson the analyst writes
counts as supported only if the same change gained in two different families.

Set it too low and the search treats noise as progress. Set it too high and real gains are ignored.

## Re-checking the leader

The best of many single runs is partly the luckiest. So at intervals the leader is trained again on a
new seed, and its score becomes the mean of its runs. In the built-in demo, a design reached 0.970, was
trained again, scored 0.967, and dropped to second place.

This happens every 20 designs when the full set of agent roles is on (`harness.level: full`), or at the
interval you set with `evaluation.recheck_every`. A re-check is charged like any evaluation.

## Changing what a score means

Some changes during a search alter what a score measures. If you lengthen training from 30 epochs to
50, a new design at 50 epochs is not comparable with an old one at 30.

So such a change starts a new *period*. The best design of each of the four leading families is run
again under the new setting, and those become the references. Earlier scores stay in the records and
still inform the agents' lessons, but they no longer decide which design is built on.

A new period starts when you change the training length (`evaluation.allowance`), the seed, the share
of the data used (`data.fraction`), the variables passed to your evaluator, or whether children inherit
weights. It also starts if you change the frozen code and say that the change moves scores.

Whether the references are trained again from scratch or continued from their checkpoints is set by
`evaluation.on_length_change`. Continuing is only right when the learning-rate schedule does not depend
on the length of training: a cosine schedule over 30 epochs has decayed to almost nothing by the end,
and 20 more epochs at that rate teach little.

## Stopped designs

A design stopped part way has a score for the part it ran. It is shown as provisional and is not ranked
against full-length runs ([Cheaper evaluations](early-stopping.md#what-happens-to-a-stopped-design)).

## What the test set is for

Your evaluator can report held-out results under `diagnostics.hidden`. They are stored and written to
the study file, and never shown to an agent or used for selection. The search optimizes the validation
score; the held-out score tells you afterwards whether the gain was real.

## Settings on this page

[`evaluation.noise`](fields.md#evaluation-noise), [`evaluation.recheck_every`](fields.md#evaluation-recheck_every), [`evaluation.allowance`](fields.md#evaluation-allowance), [`evaluation.on_length_change`](fields.md#evaluation-on_length_change),
[`evaluation.leaders_refit`](fields.md#evaluation-leaders_refit), [`evaluation.variables`](fields.md#evaluation-variables), [`data.fraction`](fields.md#data-fraction).

