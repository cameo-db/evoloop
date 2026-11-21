"""Tournament selection with aging (regularized evolution).

The population is the `strategy.window` most recent scored candidates: older ones leave it however good
they were, so one lucky score cannot dominate for long. For a parent, `strategy.tournament_size`
members are drawn at random and the best of them is taken."""
from __future__ import annotations

import random
from typing import Any, Dict, List

from ..store import View
from . import Request, complement, inspirations


class Tournament:
    name = "tournament"

    def members(self, view: View, settings: Dict[str, Any]) -> List[str]:
        recent = sorted(view.scored(), key=lambda c: c["order"])[-int(settings["strategy"]["window"]):]
        return [c["id"] for c in recent]

    def population(self, view: View, settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        return [{"candidate": c, "score": view.display(view.cands[c]["value"]), "family": view.cands[c]["family"]}
                for c in self.members(view, settings)]

    def winner(self, view: View, settings: Dict[str, Any], rng: random.Random) -> str:
        pool = self.members(view, settings)
        drawn = rng.sample(pool, min(len(pool), int(settings["strategy"]["tournament_size"])))
        return max(drawn, key=lambda c: view.cands[c]["value"])

    def choose(self, view: View, mode: str, settings: Dict[str, Any], rng: random.Random) -> Request:
        pool = self.members(view, settings)
        if mode == "local" and pool:
            parent = self.winner(view, settings, rng)
            return {"mode": "local", "lineage": view.cands[parent]["lineage"], "parents": [parent], "step": "normal",
                    "why": "the winner of a tournament among the %d most recent designs" % len(pool)}
        if mode == "cross" and len(pool) >= 2:
            first = self.winner(view, settings, rng)
            second = complement(view, first, pool, rng)
            return {"mode": "cross", "lineage": view.cands[first]["lineage"], "parents": [first, second],
                    "why": "a tournament winner and a complementary recent design"}
        if mode == "novel":
            return {"mode": "novel", "lineage": None, "parents": [], "inspirations": inspirations(view, [], 3, rng, settings),
                    "why": "designs that have rarely been built on"}
        return {"mode": "new", "lineage": None, "parents": [], "why": "a family the search has not covered"}
