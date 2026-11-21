"""Trains the classifier in model.py on the spirals and scores it. Plain NumPy: a small network, Adam, a few
hundred full-batch steps."""
import time

import numpy as np

import data
import model

# EVOLVE-BLOCK-START name=fit kind=params role=optimizer
FIT = {"lr": 0.02, "weight_decay": 0.0}
# EVOLVE-BLOCK-END


def act(z, kind):
    return np.tanh(z) if kind == "tanh" else np.maximum(z, 0.0)


def slope(a, kind):
    return 1.0 - a ** 2 if kind == "tanh" else (a > 0).astype(float)


def forward(params, given, kind):
    acts = [given]
    for i, (w, b) in enumerate(params):
        z = acts[-1] @ w + b
        acts.append(z if i == len(params) - 1 else act(z, kind))
    return acts


def accuracy(params, given, y, kind):
    return float(((forward(params, given, kind)[-1][:, 0] > 0) == (y > 0.5)).mean())


def fit(steps, seed=0, report=None, every=20):
    sets = data.load()
    given = {k: np.asarray(model.features(x), dtype=float) for k, (x, _) in sets.items()}
    if given["train"].ndim != 2 or len(given["train"]) != len(sets["train"][1]):
        raise ValueError("features(x) must return one row per example")
    mean, spread = given["train"].mean(0), given["train"].std(0) + 1e-8
    given = {k: (v - mean) / spread for k, v in given.items()}
    kind = str(model.ACTIVATION)
    sizes = [given["train"].shape[1]] + [int(h) for h in model.HIDDEN] + [1]
    rng = np.random.RandomState(seed)
    params = [(rng.normal(0.0, 1.0 / np.sqrt(m), (m, n)), np.zeros(n)) for m, n in zip(sizes[:-1], sizes[1:])]
    moment = [[np.zeros_like(w), np.zeros_like(b), np.zeros_like(w), np.zeros_like(b)] for w, b in params]
    lr, decay = float(FIT["lr"]), float(FIT["weight_decay"])
    x, y = given["train"], sets["train"][1]
    best = {"val": -1.0, "step": 0, "params": params}
    done = 0
    for step in range(1, int(steps) + 1):
        acts = forward(params, x, kind)
        grad = ((1.0 / (1.0 + np.exp(-np.clip(acts[-1][:, 0], -30, 30)))) - y)[:, None] / len(y)
        fresh = []
        for i in reversed(range(len(params))):
            w, b = params[i]
            gw, gb = acts[i].T @ grad + decay * w, grad.sum(0)
            if i > 0:
                grad = (grad @ w.T) * slope(acts[i], kind)
            mw, mb, vw, vb = moment[i]
            mw, mb = 0.9 * mw + 0.1 * gw, 0.9 * mb + 0.1 * gb
            vw, vb = 0.999 * vw + 0.001 * gw ** 2, 0.999 * vb + 0.001 * gb ** 2
            moment[i] = [mw, mb, vw, vb]
            fix_m, fix_v = 1.0 - 0.9 ** step, 1.0 - 0.999 ** step
            fresh.append((w - lr * (mw / fix_m) / (np.sqrt(vw / fix_v) + 1e-8), b - lr * (mb / fix_m) / (np.sqrt(vb / fix_v) + 1e-8)))
        params = fresh[::-1]
        done = step
        if step % every == 0 or step == int(steps):
            val = accuracy(params, given["val"], sets["val"][1], kind)
            if val > best["val"]:
                best = {"val": val, "step": step, "params": params}
            if report is not None and not report(step, val, accuracy(params, x, y, kind)):
                break
    params = best["params"]
    radius = np.sqrt((sets["val"][0] ** 2).sum(1))
    wrong = (forward(params, given["val"], kind)[-1][:, 0] > 0) != (sets["val"][1] > 0.5)
    rings = [float(wrong[(radius >= lo) & (radius < hi)].mean()) if ((radius >= lo) & (radius < hi)).any() else 0.0
             for lo, hi in ((0.0, 0.3), (0.3, 0.5), (0.5, 0.7), (0.7, 0.85), (0.85, 9.0))]
    started = time.time()
    for _ in range(20):
        forward(params, given["val"], kind)
    return {"score": best["val"], "best_step": best["step"], "steps": done,
            "train_accuracy": accuracy(params, x, y, kind), "test_accuracy": accuracy(params, given["test"], sets["test"][1], kind),
            "parameters": int(sum(w.size + b.size for w, b in params)), "errors_by_ring": rings,
            "examples_per_s": round(20 * len(given["val"]) / max(time.time() - started, 1e-6), 1)}
