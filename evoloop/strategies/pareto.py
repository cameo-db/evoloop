"""A trade-off front: the designs that are best on the score and on a second figure at once.

`strategy.second_metric` names the second figure (`parameters`, `examples_per_s`, `training_minutes`, or a
metric the runs report) and `strategy.second_direction` says whether less or more of it is better. A design
is on the front when no other design is at least as good on both and better on one. Parents are drawn from
the front, the designs standing alone on it favoured, so the search fills the trade-off in and pushes it
outward instead of climbing the score alone. A crossover pairs designs from different parts of the front.

A design that reports no value for the second figure is treated as worst on it."""
from __future__ import annotations

import random
from typing import Any, Dict, List, Tuple

from ..store import View
from . import Request, complement, inspirations, measure, specialist

Point = Tuple[str, float, float]


def points(view: View, settings: Dict[str, Any]) -> List[Point]:
    """(candidate, score, second figure), both turned so that higher is better."""
    name = settings["strategy"].get("second_metric")
    sign = 1.0 if settings["strategy"].get("second_direction") == "maximize" else -1.0
    out = []
    for cand in view.scored():
        second = measure(view, cand["id"], name) if name else None
        out.append((cand["id"], cand["value"], float("-inf") if second is None else sign * second))
    return out


def fronts(view: View, settings: Dict[str, Any], margin: float = 0.0) -> List[List[Point]]:
    """The designs in layers: the front, then the front of what is left, and so on. A difference in score
    below the noise floor is no difference, so a design is not pushed off the front by chance."""
    left = points(view, settings)
    margin = max(margin, view.noise)
    layers: List[List[Point]] = []
    while left:
        front = [p for p in left if not any(
            q[1] >= p[1] and q[2] >= p[2] and (q[1] > p[1] + margin or q[2] > p[2]) for q in left if q[0] != p[0])]
        if not front:   # cannot happen with a strict order; kept so a tie can never loop
            front = [left[0]]
        layers.append(front)
        chosen = {p[0] for p in front}
        left = [p for p in left if p[0] not in chosen]
    return layers


def spacing(front: List[Point]) -> Dict[str, float]:
    """How alone each design stands on the front, 0 to 1: the gap to its neighbours on both figures, each
    scaled to the front's range. The two ends count as fully alone."""
    if len(front) < 3:
        return {p[0]: 1.0 for p in front}
    out = {p[0]: 0.0 for p in front}
    for axis in (1, 2):
        ranked = sorted(front, key=lambda p: p[axis])
        finite = [p[axis] for p in ranked if p[axis] != float("-inf")]
        span = (max(finite) - min(finite)) if len(finite) >= 2 else 0.0
        out[ranked[0][0]] = out[ranked[-1][0]] = 2.0
        if span <= 0:
            continue
        for before, here, after in zip(ranked, ranked[1:], ranked[2:]):
            if before[axis] != float("-inf"):
                out[here[0]] += (after[axis] - before[axis]) / span / 2.0
    return {key: min(1.0, value / 2.0) for key, value in out.items()}


class Pareto:
    name = "pareto"

    def population(self, view: View, settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        name = settings["strategy"].get("second_metric") or "second"
        out = []
        for index, layer in enumerate(fronts(view, settings)[:2]):
            for cand, value, _ in sorted(layer, key=lambda p: -p[1]):
                out.append({"front": index + 1, "candidate": cand, "score": view.display(value),
                            name: measure(view, cand, settings["strategy"].get("second_metric")),
                            "family": view.cands[cand]["family"]})
        return out

    def pool(self, view: View, settings: Dict[str, Any]) -> List[Point]:
        layers = fronts(view, settings)
        if not layers:
            return []
        return layers[0] if len(layers[0]) >= 2 or len(layers) == 1 else layers[0] + layers[1]

    def draw(self, view: View, settings: Dict[str, Any], rng: random.Random) -> str:
        pool = self.pool(view, settings)
        alone = spacing(pool)
        novelty = float(settings["schedule"]["novelty"])
        # At novelty 0 every design of the front is as likely; at 1 the draw follows how alone a design stands.
        weights = [(1 - novelty) + novelty * (0.1 + alone[p[0]]) for p in pool]
        return rng.choices(pool, weights=weights)[0][0]

    def choose(self, view: View, mode: str, settings: Dict[str, Any], rng: random.Random) -> Request:
        scored = [c["id"] for c in view.scored()]
        pool = self.pool(view, settings)
        if mode == "local" and scored:
            parent = specialist(view, scored, settings, rng) or self.draw(view, settings, rng)
            return {"mode": "local", "lineage": view.cands[parent]["lineage"], "parents": [parent], "step": "normal",
                    "why": "a design on the trade-off front (%d on it)" % len(pool)}
        if mode == "cross" and len(scored) >= 2:
            first = self.draw(view, settings, rng)
            mine = next(p for p in pool if p[0] == first)
            others = [p for p in pool if p[0] != first and p[2] != float("-inf") and mine[2] != float("-inf")]
            if others:   # the design of the front that stands farthest from the first on the second figure
                second = min(others, key=lambda p: (-abs(p[2] - mine[2]), view.cands[p[0]]["order"]))[0]
                why = "two designs from different parts of the trade-off front"
            else:
                second = complement(view, first, scored, rng)
                why = "a design on the trade-off front and a complementary design"
            return {"mode": "cross", "lineage": view.cands[first]["lineage"], "parents": [first, second], "why": why}
        if mode == "novel":
            return {"mode": "novel", "lineage": None, "parents": [],
                    "inspirations": inspirations(view, scored[:1], 3, rng, settings),
                    "why": "designs that have rarely been built on"}
        return {"mode": "new", "lineage": None, "parents": [], "why": "a family the search has not covered"}
