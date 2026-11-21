# The task

Classify points of two interleaved spirals. Each point has two coordinates, `x[:, 0]` and `x[:, 1]`, and a
label, 0 or 1. The score is the accuracy on validation data: higher is better, and 0.5 is chance. About four labels
in a hundred are wrong on purpose, so no model can score much above 0.96.

## What you may change

- `model` (structure): `HIDDEN`, the widths of the hidden layers (an empty list is a linear classifier);
  `ACTIVATION`, `"tanh"` or `"relu"`; and `features(x)`, which turns the two coordinates into what the network
  is given. `features` must return one row per example and use NumPy (`np`) only.
- `fit` (settings): `FIT`, the learning rate and the weight decay.

## What is fixed

The data, the training loop (Adam, full batch, a fixed number of steps), and the scoring. A design is trained
once, for the same number of steps as every other.

## What is known

A straight line cannot separate the spirals, so the starting design (no hidden layer, raw coordinates) scores
near chance. The classes differ in angle at a given distance from the centre.
