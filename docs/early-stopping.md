# Early stopping

Most designs a search tries are not improvements. Stopping the weak ones early leaves more of the
budget for the rest. Both methods here need your evaluator to report progress as it trains
([Evaluator interface](project-contract.md#progress-and-stopping)).

## The default: half of new designs stop halfway

Say a training run is 30 epochs. A new design's score at epoch 15 is ranked against the earlier new
designs at epoch 15. If it is in the bottom half, by more than the noise, it stops there and is charged
half an evaluation.

Nothing is stopped until four designs have reached that point. Only new designs are screened; local
moves and crossovers run to the end.

This kills slow starters. If your models tend to overtake late, move the point later
(`evaluation.screen_fraction: 0.7`) or switch it off (`evaluation.screen_keep: 1`).

## A ladder: every design, at several points

For a search that needs many more designs than it can afford full runs, set a ladder:

```yaml
evaluation:
  ladder: [{at: 0.1, keep: 0.5}, {at: 0.3, keep: 0.5}]
```

At a tenth of a run, the better half of the designs that got there go on and the rest stop, charged a
tenth of an evaluation. At three tenths, half again. A design then costs 0.375 of a run on average, so
100 evaluations cover about 270 designs. This is successive halving, done inside each job.

<div class="evo-widget" id="evo-ladder">The ladder figure needs JavaScript.</div>

Each line is one design's score as it trains; grey lines were stopped. Two of these designs start
slowly and finish among the best. Move the first rung earlier and watch for the point where the design
that would have ended best is stopped. The curves are made up to show the trade-off. Whether early
progress predicts the final score on your task, only your own runs can say: start with a late first
rung and a generous share kept.

More designs also means more agent calls, since each design is written by an agent. `evoloop plan`
counts them in its cost estimate.

## What happens to a stopped design

It keeps the score it had when it stopped, marked as provisional. It is listed at the bottom of the
leaderboard with how far it ran (`stopped at 10%`), is not ranked against full-length runs, and is
never used as a parent.

## Starting from the parent's weights

With `evaluation.inherit_weights: true`, a design that has a parent is given the folder holding the
parent's checkpoint. Your evaluator decides what to load: typically every tensor whose name and shape
still match. A child that changed little then trains from where its parent stopped.

The catch is comparability. A warm-started child has had more training than a design started from
scratch, so its score is not a fair comparison with theirs, and evoloop does not correct for that.
Retrain from scratch any design you mean to report.

## Limits: not training what you could never use

A limit rejects a design that is too large or too slow:

```yaml
limits: {parameters: {max: 20000000}, examples_per_s: {min: 500}}
```

A rejected design gets no score and is not charged. If the evaluator writes the figure in its first
progress line, a design over the limit is stopped within seconds. A limit must be measurable: if a
result does not report a figure that a limit names, the search pauses and says which
([Monitor and steer a search](steering.md#limits)).

## Settings

[`evaluation.screen_fraction`](fields.md#evaluation-screen_fraction), [`evaluation.screen_keep`](fields.md#evaluation-screen_keep), [`evaluation.screen_min_pool`](fields.md#evaluation-screen_min_pool),
[`evaluation.ladder`](fields.md#evaluation-ladder), [`evaluation.ladder_applies`](fields.md#evaluation-ladder_applies), [`evaluation.inherit_weights`](fields.md#evaluation-inherit_weights), [`limits`](fields.md#limits). Each is

