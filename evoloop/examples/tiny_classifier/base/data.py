"""The data of the example: two interleaved spirals, one per class, with noisy angles and a few wrong labels.
A straight line cannot separate them, and no model can be right on every point."""
import numpy as np


def load():
    rng = np.random.RandomState(0)          # the data is the same for every design and every seed
    n = 600
    xs, ys = [], []
    for label in (0, 1):
        r = np.linspace(0.12, 1.0, n)
        theta = 4.5 * np.pi * r + label * np.pi + rng.normal(0.0, 0.32, n)
        xs.append(np.stack([r * np.cos(theta), r * np.sin(theta)], axis=1))
        ys.append(np.full(n, float(label)))
    x, y = np.concatenate(xs), np.concatenate(ys)
    wrong = rng.rand(len(y)) < 0.04          # four labels in a hundred are wrong: the best possible score is below 1
    y = np.where(wrong, 1.0 - y, y)
    order = rng.permutation(len(y))
    x, y = x[order], y[order]
    return {"train": (x[:600], y[:600]), "val": (x[600:900], y[600:900]), "test": (x[900:], y[900:])}
