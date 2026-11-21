"""Islands: several populations of any strategy, evolving apart.

Each run belongs to one island. A slot goes to the island with the fewest runs, and the inner strategy
then sees that island's results only, so the islands are not pulled toward one shared leader. Every
`strategy.migrate_every` scored runs of an island, its next local slot is a migration: the parent is the
best candidate of another island, and the child joins this one.

Resets (`strategy.reset_every`, off at 0). Every so many scored runs of the whole search, the weaker half
of the islands start again: what they held stays in the record and on the leaderboard, but no longer
counts as their population, and each is founded anew from the best design of an island that was kept.
An island that has gone nowhere stops taking slots for the same ideas, and the best idea gets a fresh
population around it."""
from __future__ import annotations

import random
from typing import Any, Dict, List

from ..store import View
from . import Request

NEVER = float("-inf")


class Islands:
    name = "islands"

    def __init__(self, inner: Any, count: int):
        self.inner, self.count = inner, count

    def island_of(self, run: Dict[str, Any]) -> int:
        return int(run["history"].get("island") or 0)

    def began(self, view: View, settings: Dict[str, Any]) -> Dict[int, float]:
        """For each island, when its present population began (NEVER: it was not reset). Worked out from the
        times the runs ended, which do not change, so the answer for a past reset never changes either."""
        start = {i: NEVER for i in range(self.count)}
        every = int(settings["strategy"].get("reset_every") or 0)
        if every <= 0 or self.count < 2:
            return start
        done = sorted((r for r in view.runs.values() if r.get("purpose") != "baseline" and r.get("ended")
                       and view.own_value(r) is not None), key=lambda r: (r["ended"], r["id"]))
        for k in range(every, len(done) + 1, every):
            best: Dict[int, float] = {}
            for run in done[:k]:
                island = self.island_of(run)
                if island in start and float(run.get("designed") or 0.0) > start[island]:
                    best[island] = max(best.get(island, NEVER), view.own_value(run))
            # Only an island that has results can be reset, and one with results is always kept.
            weakest = sorted(best, key=lambda i: (best[i], -i))[:min(self.count // 2, len(best) - 1)]
            for island in weakest:
                start[island] = float(done[k - 1]["ended"])
        return start

    def present(self, run: Dict[str, Any], start: Dict[int, float]) -> bool:
        return float(run.get("designed") or 0.0) > start.get(self.island_of(run), NEVER)

    def sub(self, view: View, island: int, start: Any = None) -> View:
        start = start or {}
        return view.subset(lambda run: run.get("purpose") == "baseline"
                           or (self.island_of(run) == island and self.present(run, start)))

    def population(self, view: View, settings: Dict[str, Any]) -> List[Dict[str, Any]]:
        out = []
        start = self.began(view, settings)
        for island in range(self.count):
            sub = self.sub(view, island, start)
            best = sub.best()
            row = {"island": island, "runs": len(sub.runs), "best": sub.display(best["value"]) if best else None,
                   "population": self.inner.population(sub, settings)}
            if start[island] != NEVER:
                row["reset"] = True
            out.append(row)
        return out

    def choose(self, view: View, mode: str, settings: Dict[str, Any], rng: random.Random) -> Request:
        making = settings.get("_designing") or []      # designs being written now count toward their island
        counts = [sum(1 for r in view.runs.values() if self.island_of(r) == i and r.get("purpose") != "baseline")
                  + sum(1 for d in making if int(d.get("island") or 0) == i) for i in range(self.count)]
        island = min(range(self.count), key=lambda i: (counts[i], i))
        start = self.began(view, settings)
        sub = self.sub(view, island, start)
        every = int(settings["strategy"]["migrate_every"])
        scored_here = sum(1 for r in sub.runs.values() if sub.own_value(r) is not None and self.island_of(r) == island)
        migrations = sum(1 for r in sub.runs.values() if r["history"].get("migrant") and self.island_of(r) == island) \
            + sum(1 for d in making if d.get("migrant") and int(d.get("island") or 0) == island)
        settings = dict(settings, _designing=[d for d in making if int(d.get("island") or 0) == island])
        # The best of the other islands, counting only what belongs to their present populations.
        others = [c for c in view.scored() if c["island"] is not None and int(c["island"]) != island
                  and self.present(view.run_of(c["id"]), start)]
        # After a reset the first slot of the island, whatever its mode, founds it anew from the best of the others.
        if start[island] != NEVER and migrations == 0 and others:
            parent = others[0]["id"]
            return {"mode": "local", "island": island, "migrant": True, "lineage": None, "parents": [parent],
                    "step": "normal", "why": "island %d was reset: it starts again from the best of island %s" % (
                        island, others[0]["island"])}
        if mode == "local" and every > 0 and scored_here // every > migrations and others:
            parent = others[0]["id"]
            return {"mode": "local", "island": island, "migrant": True, "lineage": None, "parents": [parent],
                    "step": "normal", "why": "migration: the best of island %s is brought to island %d" % (
                        others[0]["island"], island)}
        request = self.inner.choose(sub, mode, settings, rng)
        request["island"] = island
        request["why"] = "island %d: %s" % (island, request.get("why", ""))
        return request
