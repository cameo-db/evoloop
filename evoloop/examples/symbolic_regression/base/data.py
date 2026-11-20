"""The dataset."""
import numpy as np


def load():
    rng = np.random.default_rng(20240607)
    x = rng.uniform(-3.0, 3.0, size=(800, 2))
    y = 3.2 * np.sin(1.7 * x[:, 0]) * np.exp(-0.4 * x[:, 1]) + 0.8 * x[:, 1] ** 2
    y = y + rng.normal(0.0, 0.05, size=800)
    return {"train": (x[:400], y[:400]), "val": (x[400:600], y[400:600]), "test": (x[600:], y[600:])}
