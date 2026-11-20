"""Fits the constants of model.predict to the data and scores the fit.

This is the "original code" of the example: a small program that knows nothing about any search.
Run it by hand with `python train.py`."""
import numpy as np

import model
from data import load

# EVOLVE-BLOCK-START name=fit_params kind=params role=optimizer
PARAMS = {"lr": 0.05, "init_scale": 0.5, "l2": 0.0001, "restarts": 2}
# EVOLVE-BLOCK-END

PENALTY_PER_CONSTANT = 0.002
REPORT_EVERY = 25
EPS = 1e-5


def mse(c, x, y):
    return float(np.mean((model.predict(x, c) - y) ** 2))


def fit(steps=1500, seed=0, report=None, start=None):
    """Fit the constants for `steps` steps of Adam, shared between the restarts, and return what was
    found. `report(step, score, train_mse)`, when given, is called every REPORT_EVERY steps; the fit
    ends early if it returns False. `start` continues from constants found before, without restarts."""
    data = load()
    (xt, yt), (xv, yv), (xs, ys) = data["train"], data["val"], data["test"]
    n = int(model.N_CONSTANTS)
    lr, l2 = float(PARAMS["lr"]), float(PARAMS["l2"])
    rng = np.random.default_rng(seed)
    state = {"step": 0, "stop": False}

    def objective(c):
        return mse(c, xt, yt) + l2 * float(np.sum(c ** 2))

    def score(c):
        return mse(c, xv, yv) + PENALTY_PER_CONSTANT * n

    def descend(c, count):
        m, v = np.zeros(n), np.zeros(n)
        for t in range(1, int(count) + 1):
            if state["stop"]:
                break
            grad = np.zeros(n)
            for i in range(n):
                shift = np.zeros(n)
                shift[i] = EPS
                grad[i] = (objective(c + shift) - objective(c - shift)) / (2 * EPS)
            m = 0.9 * m + 0.1 * grad
            v = 0.999 * v + 0.001 * grad ** 2
            c = c - lr * (m / (1 - 0.9 ** t)) / (np.sqrt(v / (1 - 0.999 ** t)) + 1e-8)
            state["step"] += 1
            if report is not None and state["step"] % REPORT_EVERY == 0:
                state["stop"] = report(state["step"], score(c), mse(c, xt, yt)) is False
        return c

    best_c, best_obj = None, float("inf")
    with np.errstate(all="ignore"):
        if start is not None:
            starts, each = [np.asarray(start, dtype=float)], int(steps)
        else:
            restarts = max(1, int(PARAMS["restarts"]))
            starts = [rng.normal(0.0, float(PARAMS["init_scale"]), size=n) for _ in range(restarts)]
            each = max(1, int(steps) // restarts)
        for c in starts:
            c = descend(c, each)
            value = objective(c)
            if np.isfinite(value) and value < best_obj:
                best_c, best_obj = c, value
        found = {"constants": None, "n_constants": n, "steps": state["step"], "score": None}
        if best_c is not None and np.isfinite(score(best_c)):
            residual = model.predict(xv, best_c) - yv
            by_range = {}
            for axis, name in ((0, "x0"), (1, "x1")):
                for low, high in ((-3, -1), (-1, 1), (1, 3)):
                    mask = (xv[:, axis] >= low) & (xv[:, axis] < high)
                    by_range["%s in [%d, %d)" % (name, low, high)] = {
                        "mean_residual": round(float(np.mean(residual[mask])), 5),
                        "rmse": round(float(np.sqrt(np.mean(residual[mask] ** 2))), 5)}
            found.update(constants=best_c, score=score(best_c), train_mse=mse(best_c, xt, yt), val_mse=mse(best_c, xv, yv),
                         test_mse=mse(best_c, xs, ys), residuals_by_range=by_range)
    return found


if __name__ == "__main__":
    outcome = fit()
    print("validation error %.5f with %d constants" % (outcome["val_mse"], outcome["n_constants"]))
