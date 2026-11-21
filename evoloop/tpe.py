"""A tree-structured Parzen estimator for settings moves: Bayesian optimization with no agent call.

The settings tried so far are split into the best quarter and the rest. For each setting, one density
is laid over the values of the good ones and one over the others; candidates are drawn from the good
density and the one whose values are most typical of good designs and least typical of the others is
taken (the largest ratio of the two densities). Until `STARTUP` settings have been scored, the draws
come from a wide prior around the values in the code.

Numbers above zero are modelled on a log scale (a learning rate, a width); other numbers on a linear
one; whole numbers stay whole; true/false and text values are drawn by how often each appears among the
good and the others (a true/false setting can always take either value; a text setting only values already
seen). `space.ranges` may bound a setting, {"block.key": [low, high]}, and the first draws then cover the
range evenly; without a range a
setting may move a hundredfold either way from where it has been.

Each setting is treated on its own, as in the usual estimator: an interaction between two settings is
found only through the designs that happened to combine them."""
from __future__ import annotations

import math
import random
from typing import Any, Dict, List, Optional, Tuple

STARTUP = 8          # scored designs before the densities are used
GOOD = 0.25          # the share counted as good
DRAWS = 24           # candidates weighed for each suggestion
WIDE = math.log(10.0) / 2.0      # the prior's spread on a log scale: about threefold either way


def numeric(value: Any) -> bool:
    return isinstance(value, (int, float)) and not isinstance(value, bool)


def scale(values: List[float]) -> str:
    return "log" if all(v > 0 for v in values) else "linear"


def to(value: float, how: str) -> float:
    return math.log(value) if how == "log" else float(value)


def back(value: float, how: str) -> float:
    return math.exp(value) if how == "log" else value


def ranged(key: str, how: str, ranges: Dict[str, Any]) -> Optional[Tuple[float, float]]:
    given = ranges.get(key)
    if isinstance(given, (list, tuple)) and len(given) == 2 and all(numeric(x) for x in given) \
            and (how != "log" or min(given) > 0):
        return to(min(given), how), to(max(given), how)
    return None


def bounds(key: str, start: float, seen: List[float], how: str, ranges: Dict[str, Any]) -> Tuple[float, float]:
    given = ranged(key, how, ranges)
    if given:
        return given
    points = [to(v, how) for v in seen + [start]]
    reach = math.log(100.0) if how == "log" else 10.0 * (max(abs(p) for p in points) or 1.0)
    return min(points) - reach, max(points) + reach


def density(points: List[float], prior: Tuple[float, float], low: float, high: float) -> List[Tuple[float, float]]:
    """A mixture of bells, as (centre, spread) pairs: a wide one on the prior, and one on each point as wide as
    the gap to its farther neighbour, so that the density is broad where few designs have been and narrow
    where many have. No bell is narrower than a hundredth of the range, or wider than the range."""
    marked = sorted([(p, False) for p in points] + [(prior[0], True)])
    least = (high - low) / min(100.0, 1.0 + len(marked))
    out = []
    for index, (centre, is_prior) in enumerate(marked):
        if is_prior:
            out.append(prior)
            continue
        left = centre - (marked[index - 1][0] if index > 0 else low)
        right = (marked[index + 1][0] if index + 1 < len(marked) else high) - centre
        out.append((centre, min(high - low, max(left, right, least, 1e-12))))
    return out


def weight(x: float, mixture: List[Tuple[float, float]]) -> float:
    total = 0.0
    for centre, spread in mixture:
        total += math.exp(-0.5 * ((x - centre) / spread) ** 2) / spread
    return total / len(mixture) + 1e-300


def draw(mixture: List[Tuple[float, float]], low: float, high: float, rng: random.Random) -> float:
    for _ in range(50):
        centre, spread = rng.choice(mixture)
        x = rng.gauss(centre, spread)
        if low <= x <= high:
            return x
    return min(high, max(low, rng.choice(mixture)[0]))


def suggest(start: Dict[str, Any], history: List[Tuple[Dict[str, Any], float]], rng: random.Random,
            ranges: Optional[Dict[str, Any]] = None) -> Tuple[Dict[str, Any], str]:
    """New values for the settings in `start` (key -> present value), given what was tried: a list of
    (settings, score) with higher scores better. Returns the values and a line on how they were drawn."""
    ranges = ranges or {}
    history = [(s, v) for s, v in history if isinstance(v, (int, float)) and v == v]
    ranked = sorted(history, key=lambda item: -item[1])
    cut = max(1, int(math.ceil(GOOD * len(ranked))))
    good, rest = ranked[:cut], ranked[cut:]
    modelled = len(ranked) >= STARTUP and bool(rest)
    out: Dict[str, Any] = {}
    for key, present in start.items():
        seen = [s[key] for s, _ in ranked if key in s]
        if numeric(present):
            values = [float(v) for v in seen if numeric(v)]
            how = scale(values + [float(present)])
            low, high = bounds(key, float(present), values, how, ranges)
            if ranged(key, how, ranges):
                # A range was given: nothing is known inside it yet, so the prior covers it evenly.
                prior = ((low + high) / 2.0, high - low)
            else:
                prior = (to(float(present), how), WIDE if how == "log" else max(abs(float(present)), 1.0))
            if modelled:
                well = density([to(float(s[key]), how) for s, _ in good if numeric(s.get(key))], prior, low, high)
                poor = density([to(float(s[key]), how) for s, _ in rest if numeric(s.get(key))], prior, low, high)
                tries = [draw(well, low, high, rng) for _ in range(DRAWS)]
                x = max(tries, key=lambda t: weight(t, well) / weight(t, poor))
            elif ranged(key, how, ranges):
                x = rng.uniform(low, high)
            else:
                x = draw([prior], low, high, rng)
            value = back(x, how)
            if isinstance(present, int):
                value = int(round(value))
                if how == "log":
                    value = max(1, value)
            else:
                value = float("%.4g" % value)
            out[key] = value
        else:   # true/false or text: by how often each value appears among the good and among the others
            options = [True, False] if isinstance(present, bool) else []
            for v in [present] + seen:
                if v not in options:
                    options.append(v)
            if modelled and len(options) > 1:
                def share(group: List[Tuple[Dict[str, Any], float]], option: Any) -> float:
                    return (1.0 + sum(1 for s, _ in group if s.get(key) == option)) / (len(options) + len(group))
                # Drawn in proportion, not always the likeliest: a value that looked poor in a few early designs
                # (for reasons of the other settings) must still get its turn.
                out[key] = rng.choices(options, weights=[share(good, o) / share(rest, o) for o in options])[0]
            else:
                out[key] = rng.choice(options)
    how_drawn = ("from the densities of the best %d and the other %d designs" % (len(good), len(rest)) if modelled
                 else "from the prior around the present values (%d of %d designs scored before the densities are used)" % (
                     len(ranked), STARTUP))
    return out, how_drawn
