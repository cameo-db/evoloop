# Measure your noise

evoloop asks one number of you that it cannot guess: how much your score varies between two runs of
the same design. It treats any difference smaller than that as no difference, so the number decides
what counts as progress.

## Measure it in ten minutes

Train your baseline five times with different seeds and look at the spread.

```
mkdir noise && cp -r mysearch/base/. noise/ && cp -r mysearch/adapter noise/
cd noise
for seed in 0 1 2 3 4; do
    EVO_OUT_DIR=out$seed EVO_SEED=$seed EVO_ALLOWANCE=30 python adapter/run.py
done
grep -ho '"score": [0-9.e-]*' out*/result.json
```

This runs your evaluator exactly as a search would, in a copy of the code. Suppose the five scores are
0.912, 0.907, 0.915, 0.909 and 0.911. Their standard deviation is about 0.003. Use that:

```
evoloop brief mysearch --answer evaluation.noise=0.003
```

Use the same training length you will use in the search (`EVO_ALLOWANCE`): shorter runs are usually
noisier.

## If you cannot afford five runs

Run two and take the difference between them. It is a rough figure; err on the high side, since a noise
floor that is too low is the more costly mistake.

## What goes wrong at each extreme

Too low, and the search believes in gains that are luck. It keeps building on a design that scored well
once, and the leaderboard's top is whichever designs were luckiest.

Too high, and real gains are ignored. Families are retired for "not gaining" while they are improving
slowly, and many designs are treated as tied.

If your scores turn out noisier than the gains you are looking for, no setting fixes that. Train longer,
evaluate on more data, or average several seeds inside your evaluator and report the mean.

## Is my evaluator's seed doing anything?

If all five scores are identical, the seed is not reaching your training code. Check that the script
reads `EVO_SEED` and uses it for the weight initialisation and the data order. A deterministic
evaluator is fine too: set the noise to a very small number, and expect any difference to count.

[When two scores can be compared](comparable.md) explains what else the noise floor is used for.
