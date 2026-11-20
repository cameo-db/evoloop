"""Islands: several populations of any strategy, evolving apart.

Each run belongs to one island. A slot goes to the island with the fewest runs, and the inner strategy
then sees that island's results only, so the islands are not pulled toward one shared leader. Every
`strategy.migrate_every` scored runs of an island, its next local slot is a migration: the parent is the
best candidate of another island, and the child joins this one."""
from __future__ import annotations

import random
from typing import Any, Dict, List

from ..store import View
from . import Request


class Islands:
    name = "islands"

    def __init__(self, inner: Any, count: int):
        self.inner, self.count = inner, count

    def island_of(self, run: Dict[str, Any]) -> int:
        return int(run["history"].get("island") or 0)

    def sub(self, view: View, island: int) -> View:
        return view.subset(lambda run: self.island_of(run) == island or run.get("purpose") == "baseline")

    def population(self, view: View, settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        out = []
        for island in range(self.count):
            sub = self.sub(view, island)
            best = sub.best()
            out.append({"island": island, "runs": len(sub.runs), "best": sub.display(best["value"]) if best else None,
                        "population": self.inner.population(sub, settings)})
        return out

    def choose(self, view: View, mode: str, settings: Dict[str, Any], rng: random.Random) -> Request:
        making = settings.get("_designing") or []      # designs being written now count toward their island
        counts = [sum(1 for r in view.runs.values() if self.island_of(r) == i and r.get("purpose") != "baseline")
                  + sum(1 for d in making if int(d.get("island") or 0) == i) for i in range(self.count)]
        island = min(range(self.count), key=lambda i: (counts[i], i))
        sub = self.sub(view, island)
        every = int(settings["strategy"]["migrate_every"])
        scored_here = sum(1 for r in sub.runs.values() if sub.own_value(r) is not None and self.island_of(r) == island)
        migrations = sum(1 for r in sub.runs.values() if r["history"].get("migrant") and self.island_of(r) == island) \
            + sum(1 for d in making if d.get("purpose") == "migrant" and int(d.get("island") or 0) == island)
        settings = dict(settings, _designing=[d for d in making if int(d.get("island") or 0) == island])
        if mode == "local" and every > 0 and scored_here // every > migrations:
            others = [c for c in view.scored() if c["island"] is not None and int(c["island"]) != island]
            if others:
                parent = others[0]["id"]
                return {"mode": "local", "island": island, "migrant": True, "lineage": None, "parents": [parent],
                        "step": "normal", "why": "migration: the best of island %s is brought to island %d" % (
                            others[0]["island"], island)}
        request = self.inner.choose(sub, mode, settings, rng)
        request["island"] = island
        request["why"] = "island %d: %s" % (island, request.get("why", ""))
        return request
