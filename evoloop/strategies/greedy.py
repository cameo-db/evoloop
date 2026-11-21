"""Greedy best-first: always build on the current best. The simplest strategy with feedback, and the
right one when the budget is too small for a population."""
from __future__ import annotations

import random
from typing import Any, Dict, List

from ..store import View
from . import Request, complement, inspirations, tied


class Greedy:
    name = "greedy"

    def population(self, view: View, settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{"candidate": c["id"], "score": view.display(c["value"]), "family": c["family"]} for c in view.scored()[:5]]

    def choose(self, view: View, mode: str, settings: Dict[str, Any], rng: random.Random) -> Request:
        scored = [c["id"] for c in view.scored()]
        if mode == "local" and scored:
            parent = tied(view, scored, float(settings["population"]["tie_margin"]), rng)
            return {"mode": "local", "lineage": view.cands[parent]["lineage"], "parents": [parent], "step": "normal",
                    "why": "the current best (or one tied with it within the noise)"}
        if mode == "cross" and len(scored) >= 2:
            second = complement(view, scored[0], scored[1:], rng)
            return {"mode": "cross", "lineage": view.cands[scored[0]]["lineage"], "parents": [scored[0], second],
                    "why": "the best and a complementary design"}
        if mode == "novel":
            return {"mode": "novel", "lineage": None, "parents": [], "inspirations": inspirations(view, scored[:1], 3, rng, settings),
                    "why": "designs that have rarely been built on"}
        return {"mode": "new", "lineage": None, "parents": [], "why": "a family the search has not covered"}
